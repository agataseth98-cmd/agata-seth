"""Catálogo de modelos no painel (18/11/2026): ver por capacidade e estado, e registrar a decisão do Humano.

Lê um catálogo JSON (lista de modelos; formato de catalogo-modelos-18-11) e mostra o estado efetivo de cada um.
Liberar para rota e voltar ao standby SÓ gravam uma linha em um arquivo de decisões (append-only, com quem e
quando). Este módulo não altera rotas, não toca o OmniRoute e não lê chave nenhuma. `proibido_pela_regra` e
`indisponivel` não podem ser liberados. A decisão mais recente de um id vale como estado efetivo na leitura.

Caminhos (lidos na hora da chamada; os testes trocam os nomes):
  AGATA_CATALOGO_MODELOS  catálogo (padrão ~/.local/share/agata/catalogo-modelos/catalogo.json)
  AGATA_DECISOES_MODELOS  decisões (padrão: decisoes.jsonl ao lado do catálogo)
"""
from __future__ import annotations

import datetime
import fcntl
import json
import os
import re
from pathlib import Path

PASTA_PADRAO = Path.home() / ".local/share/agata/catalogo-modelos"
ESTADOS = ("liberado", "candidato_prova", "standby", "indisponivel", "proibido_pela_regra")
ACOES = {"liberar": "liberado", "standby": "standby"}
# De onde cada ação é permitida (estado efetivo atual).
ORIGENS_PERMITIDAS = {"liberar": {"candidato_prova", "standby"}, "standby": {"liberado", "candidato_prova"}}
LIMITE_CATALOGO_BYTES = 8_000_000
LIMITE_TEXTO = 300
QUEM_RE = re.compile(r"[^\w .@-]", re.U)


class ErroModelos(Exception):
    def __init__(self, status: int, motivo: str):
        super().__init__(motivo)
        self.status, self.motivo = status, motivo


def catalogo_caminho() -> Path:
    return Path(os.environ.get("AGATA_CATALOGO_MODELOS") or PASTA_PADRAO / "catalogo.json")


def decisoes_caminho() -> Path:
    return Path(os.environ.get("AGATA_DECISOES_MODELOS") or catalogo_caminho().with_name("decisoes.jsonl"))


def _texto(valor, limite: int = LIMITE_TEXTO) -> str:
    return valor[:limite] if isinstance(valor, str) else ""


def _ler_catalogo() -> list[dict] | None:
    """Lista de modelos válidos, ou None se o arquivo não existe. Arquivo ilegível levanta 500 (nada é inventado)."""
    caminho = catalogo_caminho()
    if not caminho.is_file():
        return None
    try:
        if caminho.stat().st_size > LIMITE_CATALOGO_BYTES:
            raise ErroModelos(413, "catalogo acima do limite")
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ErroModelos(500, "catalogo ilegivel")
    if not isinstance(dados, list):
        raise ErroModelos(500, "catalogo fora do formato")
    return [m for m in dados if isinstance(m, dict) and isinstance(m.get("id"), str) and m.get("estado") in ESTADOS]


def _ler_decisoes() -> list[dict]:
    caminho = decisoes_caminho()
    if not caminho.is_file():
        return []
    saida = []
    try:
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(linha)
            except ValueError:
                continue  # linha quebrada não derruba a leitura; o arquivo não é reescrito
            if isinstance(d, dict) and isinstance(d.get("id"), str) and d.get("acao") in ACOES:
                saida.append(d)
    except OSError:
        raise ErroModelos(500, "decisoes ilegiveis")
    return saida


def _estado_efetivo(modelo: dict, ultima: dict | None) -> str:
    base = modelo["estado"]
    # Decisão só vale sobre quem pode recebê-la: proibido e indisponível nunca mudam por decisão.
    if ultima and base in ("candidato_prova", "standby", "liberado"):
        return ACOES[ultima["acao"]]
    return base


def _veredito(modelo: dict) -> dict | None:
    """Veredito da prova, se o catálogo trouxer (`veredito`: texto ou {resultado, data, fonte}). Sem campo, None."""
    v = modelo.get("veredito")
    if isinstance(v, str) and v:
        return {"resultado": _texto(v), "data": "", "fonte": ""}
    if isinstance(v, dict) and isinstance(v.get("resultado"), str):
        return {"resultado": _texto(v["resultado"]), "data": _texto(v.get("data"), 40), "fonte": _texto(v.get("fonte"))}
    return None


def _acesso(modelo: dict) -> dict:
    a = modelo.get("acesso_verificado")
    if not isinstance(a, dict):
        return {"verificado": False, "resumo": "não verificado"}
    resumo = f"HTTP {a.get('status')}" if a.get("status") is not None else "sem status"
    if a.get("latencia_s") is not None:
        resumo += f", {a['latencia_s']} s"
    return {"verificado": True, "resumo": resumo, "data": _texto(a.get("data"), 40),
            "nota": _texto(a.get("nota"), 120)}


def _item(modelo: dict, ultima: dict | None) -> dict:
    efetivo = _estado_efetivo(modelo, ultima)
    return {
        "id": _texto(modelo["id"], 200), "nome": _texto(modelo.get("nome")) or _texto(modelo["id"], 200),
        "provedor": _texto(modelo.get("provedor"), 60),
        "capacidades": [_texto(c, 40) for c in modelo.get("capacidades", []) if isinstance(c, str)][:12],
        "contexto": _texto(modelo.get("contexto"), 80), "estado": efetivo, "estado_catalogo": modelo["estado"],
        "acesso": _acesso(modelo), "veredito": _veredito(modelo), "fonte": _texto(modelo.get("fonte")),
        "decisao": ({"acao": ultima["acao"], "quem": _texto(ultima.get("quem"), 80), "quando": _texto(ultima.get("quando"), 40)}
                    if ultima and efetivo != modelo["estado"] else None),
        "pode_liberar": efetivo in ORIGENS_PERMITIDAS["liberar"],
        "pode_standby": efetivo in ORIGENS_PERMITIDAS["standby"],
    }


def listar() -> dict:
    """Catálogo com estado efetivo, contagens e a fonte (caminho e hora do arquivo). Só leitura."""
    catalogo = _ler_catalogo()
    caminho = catalogo_caminho()
    base = {"schema_version": 1, "fonte": str(caminho), "estados": list(ESTADOS)}
    if catalogo is None:
        return {**base, "estado": "sem_catalogo", "modelos": [], "contagens": {}, "capacidades": [], "provedores": []}
    ultima: dict[str, dict] = {}
    for d in _ler_decisoes():
        ultima[d["id"]] = d
    modelos = [_item(m, ultima.get(m["id"])) for m in catalogo]
    contagens = {e: sum(1 for m in modelos if m["estado"] == e) for e in ESTADOS}
    hora = datetime.datetime.fromtimestamp(caminho.stat().st_mtime).astimezone().isoformat(timespec="seconds")
    return {**base, "estado": "ok" if modelos else "vazio", "arquivo_em": hora, "modelos": modelos,
            "contagens": contagens,
            "capacidades": sorted({c for m in modelos for c in m["capacidades"]}),
            "provedores": sorted({m["provedor"] for m in modelos if m["provedor"]})}


def decidir(pedido) -> dict:
    """Registra liberar ou standby. Exige confirmacao == id (confirmação explícita). Só acrescenta ao arquivo de decisões."""
    if not isinstance(pedido, dict):
        raise ErroModelos(400, "pedido invalido")
    ident, acao = pedido.get("id"), pedido.get("acao")
    # Tipos primeiro: lista ou dict em qualquer campo texto é 400, nunca TypeError.
    for campo in ("id", "acao", "confirmacao", "quem", "nota"):
        valor = pedido.get(campo)
        if (valor is not None or campo in ("id", "acao", "confirmacao")) and not isinstance(valor, str):
            raise ErroModelos(400, f"campo {campo} deve ser texto")
    if acao not in ACOES:
        raise ErroModelos(400, "id ou acao invalidos")
    if pedido.get("confirmacao") != ident:
        raise ErroModelos(400, "confirmacao explicita ausente: envie confirmacao igual ao id")
    quem = QUEM_RE.sub("", _texto(pedido.get("quem"), 60)).strip() or "humano"
    caminho = decisoes_caminho()
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with caminho.open("a+", encoding="utf-8") as arq:
            fcntl.flock(arq, fcntl.LOCK_EX)  # leitura do estado, validação e append sob a mesma trava
            modelo = next((m for m in (_ler_catalogo() or []) if m["id"] == ident), None)
            if modelo is None:
                raise ErroModelos(404, "modelo fora do catalogo")
            arq.seek(0)
            anterior = None
            for l in arq.read().splitlines():
                try:
                    d = json.loads(l)
                except ValueError:
                    continue
                if isinstance(d, dict) and d.get("id") == ident and d.get("acao") in ACOES:
                    anterior = d
            atual = _estado_efetivo(modelo, anterior)
            if modelo["estado"] == "proibido_pela_regra":
                raise ErroModelos(409, "proibido pela regra: nao pode ser liberado nem mudar de estado")
            if atual not in ORIGENS_PERMITIDAS[acao]:
                raise ErroModelos(409, f"estado {atual} nao permite {acao}")
            linha = {"quando": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "id": ident,
                     "acao": acao, "de": atual, "para": ACOES[acao], "quem": quem + " (painel)",
                     "nota": _texto(pedido.get("nota"), 200)}
            arq.seek(0, 2)
            arq.write(json.dumps(linha, ensure_ascii=False) + "\n")
            arq.flush()
    except OSError:
        raise ErroModelos(500, "gravacao indisponivel; nada foi registrado")
    return {"schema_version": 1, "registrado": linha,
            "aviso": "decisao registrada; nenhuma rota foi alterada (isso e feito fora do painel)"}
