"""Ciclo de vida de skills candidatas da Alexandria (lote 5, pacote C5).

Estados (próprios, separados do editorial de fontes):
  rascunho -> quarentena -> em-teste -> elegivel -> revogada
Regras:
- nada aqui instala skill: `elegivel` só gera um `.diff` rascunho para o fluxo P-8 (propostas/, assinatura do Humano);
- máquina só faz rascunho -> quarentena; todo o resto é decisão do Humano;
- `revogada` é terminal: uso futuro impedido; o histórico fica (ledger);
- uso registra eventos: disponivel, selecionada, lida (com comparação de sha), aplicada, testada.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (AQUI, RAIZ / "redesign" / "nova_versao", RAIZ / "redesign" / "painel_operacional"):
    sys.path.insert(0, str(_p))
import caminhos  # noqa: E402
import eventos  # noqa: E402

ESTADOS = ("rascunho", "quarentena", "em-teste", "elegivel", "revogada")
TRANSICOES = {"rascunho": {"quarentena", "revogada"}, "quarentena": {"em-teste", "revogada"},
              "em-teste": {"elegivel", "revogada"}, "elegivel": {"revogada"}, "revogada": set()}
USOS = ("disponivel", "selecionada", "lida", "aplicada", "testada")
RE_NOME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
LIMITE_NOME, LIMITE_DESC = 64, 1024


def pasta() -> Path:
    p = eventos.dados() / "alexandria" / "skills-ciclo"
    p.mkdir(parents=True, exist_ok=True)
    os.chmod(p, 0o700)
    return p


def _arquivo(nome: str) -> Path:
    if not RE_NOME.fullmatch(nome or "") or len(nome) > LIMITE_NOME:
        raise ValueError("nome de skill inválido")
    return caminhos.dentro(pasta(), nome + ".json")


def ler(nome: str) -> dict | None:
    a = _arquivo(nome)
    return json.loads(a.read_text(encoding="utf-8")) if a.exists() else None


def _gravar(obj: dict) -> None:
    dest = _arquivo(obj["nome"])
    fd, tmp = tempfile.mkstemp(dir=pasta(), prefix=".sk.", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.chmod(tmp, 0o600)
    os.replace(tmp, dest)


def listar() -> list[dict]:
    out = []
    for a in sorted(pasta().glob("*.json")):
        try:
            out.append(json.loads(a.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return out


def revogadas() -> set[str]:
    """Usado por skills.selecionar: uma skill revogada não é sugerida nem usada."""
    return {o["nome"] for o in listar() if o["estado"] == "revogada"}


def _lint(texto: str, nome: str) -> list[str]:
    import qualidade_llm  # noqa: E402
    campos, _linhas = qualidade_llm.frontmatter(texto)
    problemas = []
    if campos.get("name") != nome:
        problemas.append("name difere do nome")
    if not RE_NOME.fullmatch(campos.get("name", "")) or len(campos.get("name", "")) > LIMITE_NOME:
        problemas.append("name inválido")
    desc = campos.get("description", "")
    if not desc:
        problemas.append("description vazia")
    if len(desc) > LIMITE_DESC:
        problemas.append("description acima do limite")
    if re.search(r"</?[a-z]+>", desc):
        problemas.append("description com tag XML")
    return problemas


def rascunhar(nome: str, titulo: str, descricao: str, gatilhos: list[str], fontes: list[str]) -> dict:
    """Esqueleto de SKILL.md em `alexandria/skills/rascunho/<nome>/`. Sem fontes, não há rascunho."""
    if not fontes:
        raise ValueError("uma skill precisa de fontes declaradas")
    if not RE_NOME.fullmatch(nome) or len(nome) > LIMITE_NOME:
        raise ValueError("nome inválido")
    corpo = (f"---\nname: {nome}\ndescription: {' '.join(descricao.split())[:LIMITE_DESC]}\n---\n\n"
             f"# {titulo}\n\n## Quando usar\n" + "".join(f"- {g}\n" for g in gatilhos) +
             "\n## Fontes\n" + "".join(f"- {f}\n" for f in fontes) +
             "\n## Casos de teste\n- (a escrever antes de sair do rascunho)\n")
    problemas = _lint(corpo, nome)
    if problemas:
        raise ValueError("rascunho reprovado: " + ", ".join(problemas))
    d = eventos.dados() / "alexandria" / "skills" / "rascunho" / nome
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(corpo, encoding="utf-8")
    sha = hashlib.sha256(corpo.encode()).hexdigest()
    obj = {"schema_version": 1, "nome": nome, "estado": "rascunho", "sha256": sha, "fontes": list(fontes),
           "historico": [{"de": None, "para": "rascunho", "ator": "maquina", "em": time.strftime("%Y-%m-%dT%H:%M:%S%z")}],
           "testes": None}
    _gravar(obj)
    eventos.registrar("observation", "rascunho", f"skill:{nome}", componente="alexandria", classification="project",
                      chave=f"skill:{nome}:rascunho:{sha[:12]}", sha256=sha)
    return obj


def transicionar(nome: str, para: str, ator: str, motivo: str, *, evidencia: str | None = None) -> dict:
    obj = ler(nome)
    if obj is None:
        raise ValueError("skill desconhecida")
    atual = obj["estado"]
    if para not in TRANSICOES.get(atual, set()):
        raise ValueError(f"transição {atual} -> {para} não permitida")
    if ator not in ("maquina", "humano"):
        raise ValueError("ator inválido")
    if ator == "maquina" and (atual, para) != ("rascunho", "quarentena"):
        raise ValueError("só o Humano faz essa transição")
    if para == "elegivel":
        if not (evidencia or "").strip():
            raise ValueError("elegível exige evidência do teste (resumo escrito)")
        obj["testes"] = {"evidencia": evidencia.strip()[:500], "em": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    obj["estado"] = para
    obj["historico"].append({"de": atual, "para": para, "ator": ator, "motivo": (motivo or "")[:200],
                             "em": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    _gravar(obj)
    eventos.registrar("decision" if ator == "humano" else "verification", para, f"skill:{nome}", actor=ator,
                      componente="alexandria", classification="project",
                      chave=f"skill:{nome}:{para}:{len(obj['historico'])}", de=atual)
    return obj


def registrar_uso(nome: str, uso: str, *, sha_lido: str | None = None) -> dict:
    """Uso de uma skill. `lida` compara o hash lido com o atual: diferença = a skill mudou entre a seleção e a leitura."""
    if uso not in USOS:
        raise ValueError("uso fora da lista")
    obj = ler(nome)
    if obj is None:
        raise ValueError("skill desconhecida")
    if uso == "selecionada" and obj["estado"] == "revogada":
        raise ValueError("skill revogada: uso impedido")
    resultado = {"nome": nome, "uso": uso, "estado": obj["estado"]}
    if uso == "lida" and sha_lido is not None:
        resultado["mudou_desde_o_hash"] = sha_lido != obj["sha256"]
    eventos.registrar("observation", uso, f"skill:{nome}", componente="alexandria", classification="project",
                      chave=f"skill:{nome}:uso:{uso}:{time.monotonic_ns()}", sha256=obj["sha256"])
    return resultado


def gerar_diff_p8(nome: str) -> Path:
    """Só para `elegivel`: um `.diff` que cria `.agents/skills/<nome>/SKILL.md`, para o fluxo P-8 (não instala)."""
    obj = ler(nome)
    if obj is None or obj["estado"] != "elegivel":
        raise ValueError("só uma skill elegível gera o diff para o P-8")
    fonte = eventos.dados() / "alexandria" / "skills" / "rascunho" / nome / "SKILL.md"
    if not fonte.exists():
        raise ValueError("rascunho não encontrado")
    linhas = fonte.read_text(encoding="utf-8").splitlines(keepends=True)
    diff = "".join(difflib.unified_diff([], linhas, fromfile="/dev/null", tofile=f"b/.agents/skills/{nome}/SKILL.md"))
    destino = eventos.dados() / "alexandria" / "skills" / "elegivel"
    destino.mkdir(parents=True, exist_ok=True)
    arq = destino / f"{nome}.diff"
    arq.write_text(f"diff --git a/.agents/skills/{nome}/SKILL.md b/.agents/skills/{nome}/SKILL.md\nnew file mode 100644\n" + diff,
                   encoding="utf-8")
    return arq
