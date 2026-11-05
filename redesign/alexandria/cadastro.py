"""Cadastro de objetos externos da Alexandria (lote 5, pacote C1).

Um arquivo JSON por objeto, em `<dados>/alexandria/cadastro/ext:<sha256>.json` (0600). É a fonte de verdade do
que é externo: origem (sem query nem credenciais), direitos, acesso, estado editorial e verificação. O índice
derivado (`acervo.indexar`) é projetado daqui. Cada mudança vira evento no ledger, com a chave idempotente
`alex:<sha>:<estado>`, e o ledger não recebe o conteúdo nem a URI completa.

Regras:
- automático (pipeline, ator "maquina") só faz: recebido -> quarentena, e quarentena -> catalogado|restrito|rejeitado;
- todo o resto exige ator "humano" (promoção a `revisado`, contestar, arquivar, rejeitar, decidir direitos);
- `revisado` com direitos `desconhecido` guarda só a referência: o texto não é indexado.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[0] / "nova_versao"))
import caminhos  # noqa: E402
import eventos  # noqa: E402

ESTADOS = ("recebido", "quarentena", "catalogado", "revisado", "contestado", "restrito", "arquivado", "rejeitado")
TRANSICOES = {
    "recebido": {"quarentena"},
    "quarentena": {"catalogado", "restrito", "rejeitado"},
    "catalogado": {"revisado", "contestado", "restrito", "arquivado", "rejeitado"},
    "revisado": {"contestado", "restrito", "arquivado"},
    "contestado": {"revisado", "arquivado", "rejeitado"},
    "restrito": {"catalogado", "arquivado"},
    "arquivado": set(),
    "rejeitado": set(),
}
AUTOMATICAS = {("recebido", "quarentena"), ("quarentena", "catalogado"), ("quarentena", "restrito"), ("quarentena", "rejeitado")}
DIREITOS = ("pendente", "livre", "permitido_pelo_humano", "desconhecido")
RE_SHA = re.compile(r"[0-9a-f]{64}")


def pasta() -> Path:
    p = eventos.dados() / "alexandria" / "cadastro"
    p.mkdir(parents=True, exist_ok=True)
    os.chmod(p, 0o700)
    return p


def object_id(sha: str) -> str:
    return "ext:" + caminhos.id_seguro(sha, RE_SHA)


def _arquivo(sha: str) -> Path:
    return caminhos.dentro(pasta(), object_id(sha) + ".json")


def sanear_uri(url: str | None) -> str | None:
    """Só esquema http(s), host e caminho: sem usuário, senha, query nem fragmento (não vazam token)."""
    if not url:
        return None
    p = urllib.parse.urlsplit(url.strip())
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ValueError("URI sem esquema http(s) ou sem host")
    host = p.hostname + (f":{p.port}" if p.port else "")
    return urllib.parse.urlunsplit((p.scheme, host, p.path or "/", "", ""))


def _gravar(obj: dict) -> None:
    dest = _arquivo(obj["sha256"])
    fd, tmp = tempfile.mkstemp(dir=pasta(), prefix=".cad.", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.chmod(tmp, 0o600)
    os.replace(tmp, dest)


def ler(sha: str) -> dict | None:
    arq = _arquivo(sha)
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None


def listar() -> list[dict]:
    out = []
    for arq in sorted(pasta().glob("ext:*.json")):
        try:
            out.append(json.loads(arq.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return out


def criar(sha256: str, extensao: str, rotulo: str, *, origem_uri: str | None = None, tamanho: int = 0,
          origem_tipo: str = "arquivo") -> dict:
    """Entrada nova em `recebido`. Idempotente: o mesmo sha devolve o cadastro já existente."""
    existente = ler(sha256)
    if existente:
        return existente
    if extensao not in ("md", "txt", "html", "pdf"):
        raise ValueError("extensão fora da lista")
    agora = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    obj = {"schema_version": 1, "object_id": object_id(sha256), "sha256": sha256, "extensao": extensao,
           "rotulo": " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", rotulo or "")[:120].split()), "tamanho": int(tamanho),
           "origem_tipo": origem_tipo,
           "origem_uri": sanear_uri(origem_uri), "editorial_status": "recebido",
           "direitos": {"status": "pendente", "evidencia": None, "decidido_por": None},
           "acesso": {"classification": "project"},
           "verificacao": {"identidade": "not_checked", "integridade": "sha256", "suporte": "not_checked"},
           "relacoes": [], "adquirido_em": agora, "historico": []}
    _gravar(obj)
    eventos.registrar("observation", "recebido", f"alex:{sha256}", componente="alexandria",
                      classification="project", chave=f"alex:{sha256}:recebido", tamanho=int(tamanho), extensao=extensao)
    return obj


def transicionar(sha: str, para: str, ator: str, motivo: str) -> dict:
    obj = ler(sha)
    if obj is None:
        raise ValueError("objeto não cadastrado")
    atual = obj["editorial_status"]
    if para not in ESTADOS or para not in TRANSICOES.get(atual, set()):
        raise ValueError(f"transição {atual} -> {para} não permitida")
    if ator not in ("maquina", "humano"):
        raise ValueError("ator inválido")
    if ator == "maquina" and (atual, para) not in AUTOMATICAS:
        raise ValueError("só o Humano faz essa transição")
    if para == "revisado" and obj["direitos"]["status"] == "pendente":
        raise ValueError("defina os direitos antes de revisar")
    obj["editorial_status"] = para
    obj["historico"].append({"de": atual, "para": para, "ator": ator, "motivo": (motivo or "")[:200],
                             "em": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    _gravar(obj)
    eventos.registrar("decision" if ator == "humano" else "verification", para, f"alex:{sha}", actor=ator,
                      componente="alexandria", classification="project", chave=f"alex:{sha}:{para}:{len(obj['historico'])}",
                      de=atual)
    return obj


def definir_direitos(sha: str, status: str, evidencia: str, ator: str) -> dict:
    """Decisão de direitos: só o Humano. Sem evidência escrita, não há decisão."""
    if ator != "humano":
        raise ValueError("direitos só o Humano decide")
    if status not in DIREITOS or status == "pendente":
        raise ValueError("status de direitos inválido")
    obj = ler(sha)
    if obj is None:
        raise ValueError("objeto não cadastrado")
    if not (evidencia or "").strip():
        raise ValueError("a decisão de direitos precisa de evidência escrita")
    obj["direitos"] = {"status": status, "evidencia": evidencia.strip()[:300], "decidido_por": "humano",
                       "em": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    _gravar(obj)
    eventos.registrar("decision", status, f"alex:{sha}", actor="humano", componente="alexandria",
                      classification="project", chave=f"alex:{sha}:direitos:{status}:{obj['direitos']['em']}")
    return obj


def anotar(sha: str, **campos) -> dict:
    """Anotações da máquina (parse, sinais de quarentena). Não muda o estado editorial."""
    obj = ler(sha)
    if obj is None:
        raise ValueError("objeto não cadastrado")
    obj.setdefault("analise", {}).update(campos)
    _gravar(obj)
    return obj


def texto_path(sha: str) -> Path:
    return caminhos.dentro(eventos.dados() / "alexandria" / "texto", f"{caminhos.id_seguro(sha, RE_SHA)}.txt")
