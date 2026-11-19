#!/usr/bin/env python3
"""Rótulos de ferramenta e nível de confiança por provedor (19/11/2026).

Decisão do Humano (19/11/2026): todo modelo, local ou de nuvem, pode usar ferramentas, escolhido por capacidade; a
segurança é pelo DADO e pelo EFEITO, não pelo lugar do modelo. Cada ferramenta tem um rótulo no arquivo
config/ferramentas-rotulos.json: dado que devolve (publico | pessoal | segredo) e efeito (leitura | escrita). Cada
provedor tem um nível: local e pago_sem_treino levam dado até pessoal; gratuito leva só público. Segredo nunca vai a
ninguém. Escrita continua pelo portão de aprovação do cliente para qualquer modelo (o gateway não aprova nada).

Funções puras e sem rede. O arquivo é lido com cache por mtime. Arquivo ausente ou quebrado = falha fechada: nenhuma
ferramenta conhecida, desconhecida vale pessoal+escrita, e as faixas ficam no nível mais restrito. Quem usa é o
seth_gateway (e o teste).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO_PADRAO = RAIZ / "config" / "ferramentas-rotulos.json"
ORDEM_DADO = {"publico": 0, "pessoal": 1, "segredo": 2}
DESCONHECIDA = {"dado": "pessoal", "efeito": "escrita"}
_CACHE: dict = {"mtime": None, "caminho": None, "dados": None}
_RE_SUFIXO_MCP = re.compile(r"_mcp_[a-z0-9_]+$", re.I)
OMISSAO = "[resultado de {nome} omitido pela Máquina: {motivo}]"


def _restrito() -> dict:
    return {"niveis": {"local": {"dado_maximo": "pessoal"}, "pago_sem_treino": {"dado_maximo": "pessoal"},
                       "gratuito": {"dado_maximo": "publico"}},
            "provedores": {}, "padrao_provedor_desconhecido": "gratuito", "faixas": {},
            "ferramentas": {}, "padrao_ferramenta_desconhecida": dict(DESCONHECIDA)}


def carregar(caminho: Path | str | None = None) -> dict:
    """Os rótulos, com cache por mtime. Ausente ou ilegível: o conjunto restrito (falha fechada)."""
    caminho = Path(caminho or ARQUIVO_PADRAO)
    try:
        mt = caminho.stat().st_mtime
        if _CACHE["mtime"] == mt and _CACHE["caminho"] == str(caminho):
            return _CACHE["dados"]
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        if not isinstance(dados, dict) or not isinstance(dados.get("ferramentas"), dict):
            raise ValueError("estrutura")
    except (OSError, ValueError):
        return _restrito()
    for k, v in _restrito().items():
        dados.setdefault(k, v)
    _CACHE.update(mtime=mt, caminho=str(caminho), dados=dados)
    return dados


def nome_base(nome: str) -> str:
    """`vault_buscar_mcp_canon` -> `vault_buscar` (o LibreChat põe o servidor como sufixo)."""
    return _RE_SUFIXO_MCP.sub("", str(nome or "").strip())


def rotulo(nome: str, caminho=None) -> dict:
    """{dado, efeito} da ferramenta. Nome desconhecido ou rótulo inválido: o mais restrito (pessoal, escrita)."""
    d = carregar(caminho)
    r = d["ferramentas"].get(nome_base(nome))
    if not isinstance(r, dict) or r.get("dado") not in ORDEM_DADO or r.get("efeito") not in ("leitura", "escrita"):
        pad = d.get("padrao_ferramenta_desconhecida")
        return dict(pad) if isinstance(pad, dict) and pad.get("dado") in ORDEM_DADO else dict(DESCONHECIDA)
    return {"dado": r["dado"], "efeito": r["efeito"]}


def _dado_do_nivel(nivel: str, d: dict) -> str:
    """Dado máximo de um nível de provedor ou de uma faixa. Desconhecido: publico (o mais restrito)."""
    if nivel == "pessoal_via_sanitizador":
        return "pessoal"
    n = d["niveis"].get(nivel)
    m = n.get("dado_maximo") if isinstance(n, dict) else None
    return m if m in ("publico", "pessoal") else "publico"  # segredo nunca é máximo de ninguém


def nivel_do_provedor(provedor: str, caminho=None) -> str:
    d = carregar(caminho)
    return d["provedores"].get(str(provedor or "").lower()) or d.get("padrao_provedor_desconhecido") or "gratuito"


def dado_maximo(modelo: str, publica: bool, caminho=None) -> str:
    """O maior dado que pode ir ao modelo deste pedido. Faixa pública: o da faixa (gratuito). Modelo local (prefixo do
    gateway): local. Fila seth-*: o da faixa no arquivo. Outro nome: o provedor antes da barra, ou desconhecido."""
    d = carregar(caminho)
    faixas = d.get("faixas") or {}
    if publica:
        return _dado_do_nivel(faixas.get("publica", "gratuito"), d)
    modelo = str(modelo or "")
    if modelo.startswith(("ollama-local/", "llamacpp-", "llama-cpp/", "local/")):
        return _dado_do_nivel("local", d)
    if modelo in faixas:
        return _dado_do_nivel(faixas[modelo], d)
    prov = modelo.split("/", 1)[0] if "/" in modelo else ""
    return _dado_do_nivel(nivel_do_provedor(prov, caminho), d)


def cabe(dado: str, maximo: str) -> bool:
    """O dado cabe no máximo? Segredo nunca cabe; dado desconhecido não cabe."""
    if dado == "segredo" or dado not in ORDEM_DADO or maximo not in ORDEM_DADO:
        return False
    return ORDEM_DADO[dado] <= ORDEM_DADO[maximo]


def ferramenta_cabe(nome: str, maximo: str, caminho=None) -> bool:
    return cabe(rotulo(nome, caminho)["dado"], maximo)


def _nome_da_def(t) -> str:
    if isinstance(t, dict):
        f = t.get("function") if isinstance(t.get("function"), dict) else t
        n = f.get("name")
        if isinstance(n, str):
            return n
    return ""


def filtrar_ferramentas(payload: dict, maximo: str, caminho=None) -> list[str]:
    """Deixa em payload["tools"] só as ferramentas cujo dado cabe em `maximo`. Devolve os nomes retirados. Definição
    sem nome é retirada. Sem ferramenta sobrando, sai também tool_choice (e os campos antigos)."""
    tools = payload.get("tools")
    retiradas: list[str] = []
    if isinstance(tools, list):
        ficam = []
        for t in tools:
            nome = _nome_da_def(t)
            if nome and ferramenta_cabe(nome, maximo, caminho):
                ficam.append(t)
            else:
                retiradas.append(nome or "?")
        if ficam:
            payload["tools"] = ficam
        else:
            payload.pop("tools", None)
        ficou = {_nome_da_def(t) for t in ficam}
        tc = payload.get("tool_choice")
        if isinstance(tc, dict) and _nome_da_def(tc) and _nome_da_def(tc) not in ficou:
            payload.pop("tool_choice", None)
        if not ficam:
            for campo in ("tool_choice", "functions", "function_call"):
                payload.pop(campo, None)
    elif tools is not None:
        payload.pop("tools", None)
        payload.pop("tool_choice", None)
    return retiradas


def tem_segredo(texto: str) -> bool:
    """Segredo no texto, pela régua do sanitizador, sem a heurística `NOME_KEY=` (texto do canon cita nomes de variável
    e ela recusaria resultado legítimo; o proxy sanitizador ainda aplica a heurística na saída). Régua indisponível:
    trata como segredo (falha fechada)."""
    if not texto:
        return False
    try:
        import sanitizar  # noqa: E402  (mesmo diretório)
        return any(rx.search(texto) for r, _b, rx in sanitizar._regras() if not r.startswith("heuristica"))
    except Exception:  # noqa: BLE001
        return True


def _texto_da_msg(m: dict) -> str:
    c = m.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(p.get("text", "") for p in c if isinstance(p, dict) and isinstance(p.get("text"), str))
    return ""


def _nomes_por_id(msgs: list) -> dict:
    por_id = {}
    for m in msgs:
        if isinstance(m, dict) and m.get("role") == "assistant":
            for tc in m.get("tool_calls") or []:
                if isinstance(tc, dict) and tc.get("id"):
                    por_id[tc["id"]] = str((tc.get("function") or {}).get("name") or tc.get("name") or "")
    return por_id


def _nome_do_resultado(m: dict, por_id: dict) -> str:
    """A ferramenta que gerou o resultado, SÓ pelo tool_call_id ligado a uma chamada do assistente no histórico. O campo
    `name` da mensagem é do cliente e nunca é confiado (um resultado de `vault_buscar` com name="buscar_web" passaria por
    público). Sem vínculo verificável: "" (o rótulo restrito, pessoal)."""
    tid = m.get("tool_call_id")
    return por_id.get(tid, "") if isinstance(tid, str) and tid else ""


def filtrar_historico(msgs: list, maximo: str, so_com_par: bool = False, caminho=None) -> tuple[list, list[str]]:
    """Resultado de ferramenta que devolve dado acima do nível (ou que traz segredo) é trocado por uma omissão ANTES
    de voltar ao modelo. Devolve (mensagens, nomes recusados). Com `so_com_par` (faixa pública), também sai o
    resultado sem chamada pareada, e a chamada de ferramenta que não cabe sai da mensagem do assistente."""
    por_id = _nomes_por_id(msgs)
    recusadas: list[str] = []
    saida: list = []
    ids_ok: set = set()
    for m in msgs:
        if not isinstance(m, dict):
            continue
        papel = m.get("role")
        if papel == "assistant" and m.get("tool_calls"):
            if so_com_par:
                mantidas = [tc for tc in m["tool_calls"] if isinstance(tc, dict)
                            and ferramenta_cabe(str((tc.get("function") or {}).get("name") or tc.get("name") or ""),
                                                maximo, caminho)]
                ids_ok |= {tc.get("id") for tc in mantidas if tc.get("id")}
                novo = {k: v for k, v in m.items() if k != "tool_calls"}
                if mantidas:
                    novo["tool_calls"] = mantidas
                elif not _texto_da_msg(m).strip():
                    continue
                saida.append(novo)
                continue
            saida.append(m)
        elif papel == "tool":
            nome = _nome_do_resultado(m, por_id)
            if so_com_par and (not m.get("tool_call_id") or m.get("tool_call_id") not in ids_ok):
                continue
            motivo = None
            if not ferramenta_cabe(nome, maximo, caminho):  # nome vazio (sem vínculo): rótulo restrito, pessoal
                motivo = f"dado {rotulo(nome, caminho)['dado']} acima do nível deste provedor (máximo: {maximo})"
            elif tem_segredo(_texto_da_msg(m)):
                motivo = "o resultado traz segredo, que não vai a nenhum modelo"
            if motivo:
                recusadas.append(nome_base(nome) or "?")
                novo = dict(m)
                novo["content"] = OMISSAO.format(nome=nome_base(nome) or "ferramenta", motivo=motivo)
                saida.append(novo)
            else:
                saida.append(m)
        else:
            saida.append(m)
    return saida, recusadas


def e_escrita(nome: str, caminho=None) -> bool:
    return rotulo(nome, caminho)["efeito"] == "escrita"


if __name__ == "__main__":
    import sys
    for n in sys.argv[1:]:
        print(n, rotulo(n))
