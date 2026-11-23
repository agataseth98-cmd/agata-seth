#!/usr/bin/env python3
"""Capivara — registro de capacidades dos modelos (roteamento por capacidade).

V9, seção 35; desenho em "Área de trabalho/DESENHO_roteamento_por_capacidade_rascunho.md",
seções 3 e 8. Fonte única: `config/capivara/capacidades.json` (janela, saída máxima e
capacidades de CADA modelo do OmniRoute e do catalogo.json). `config/capivara/perfis-modelos.json`
é DERIVADO dele (capivara_perfis.py), porque o gateway da Seth lê esse outro arquivo.
Lê fatos, nunca escreve canon.

Cobertura: todo modelo do OmniRoute (`/v1/models`) e do catalogo.json, não só as filas.
Modelo sem dado fica com as camadas vazias e `fonte: nao_medido`, nunca com número inventado.

Camadas, nunca fundidas num "capaz = sim":
- `catalogo`  — inventário: o que o OmniRoute lista (provedor, id resolvido, modalidades) e o que
                o catalogo.json diz (estado, rótulos de capacidade), com a fonte de cada um;
- `declarado` — afirmações de fonte pública, por campo e por origem: `claims[campo]` é uma lista
                de {origem, fonte (URL ou endpoint), data, valor}. Janela, saída máxima e
                capacidades saem de uma precedência fixa; `divergente` lista os campos em que as
                origens discordam (não se escolhe em silêncio). Origens: omniroute (/v1/models),
                openrouter e nvidia (listas públicas, sem chave), documentacao
                (janelas-documentadas.json) e ollama (num_ctx, local);
- `medido`    — ensaios do benchmark (`--incorporar RODADA`), um registro por medição, com
                proveniência completa;
- `observado` — uso real do gateway (`--incorporar-uso`, log uso.jsonl, sem texto): por modelo×tipo
                e pelo roteador Laya (`laya/roteador-atual`, por rota e por quem decidiu), lote a lote,
                com desde/ate.

Ao regenerar, `medido` e `observado` são preservados, e a afirmação de uma fonte que deixou de
responder também fica (com a data antiga, visível). Ids que só existem numa lista pública não entram
aqui: são candidatos do pesquisar_modelos_gratuitos.py, não inventário.

Onde fica o quê: o registro em uso é o do estado (~/.local/share/agata/capivara/, ou AGATA_CAPIVARA_ESTADO)
se ele existir e passar em conferir(); senão, o retrato versionado em config/capivara/. A etapa semanal
e --incorporar-uso gravam só no estado. O build manual grava retrato e estado, e o perfil derivado nos dois.

Uso:
  capivara_capacidades.py                         monta, confere, grava o retrato e o estado, e o perfil derivado
  capivara_capacidades.py --relato                monta e confere em memória, sem gravar
  capivara_capacidades.py --conferir              valida o registro gravado (saída 1 se inválido)
  capivara_capacidades.py --incorporar DIR...     medido: resumo.json de uma rodada do benchmark
  capivara_capacidades.py --incorporar-uso [ARQ]  observado: lê o uso.jsonl (padrão em ~/.local/share/agata/capivara/)
  capivara_capacidades.py --selftest              roda scripts/testar_capivara_capacidades.py
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.request
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REGISTRO = RAIZ / "config" / "capivara" / "capacidades.json"
PERFIS = RAIZ / "config" / "capivara" / "perfis-modelos.json"
DOCUMENTADAS = RAIZ / "config" / "capivara" / "janelas-documentadas.json"
CATALOGO_VIVO = Path.home() / ".local" / "share" / "agata" / "catalogo-modelos" / "catalogo.json"
# Estado operacional, fora do repositório: a etapa semanal e --incorporar-uso gravam aqui.
# config/capivara/* é o retrato versionado, gravado pelo build manual. AGATA_CAPIVARA_ESTADO troca a pasta (testes).
ESTADO_DIR = Path(os.environ.get("AGATA_CAPIVARA_ESTADO") or (Path.home() / ".local" / "share" / "agata" / "capivara"))
ESTADO_REGISTRO = ESTADO_DIR / "capacidades.json"
ESTADO_PERFIL = ESTADO_DIR / "perfis-modelos.json"
USO = ESTADO_DIR / "uso.jsonl"
OLLAMA = "http://127.0.0.1:11434"
FILAS = ("seth-rapido", "seth-livre", "seth-pesado", "seth-codigo")
CAMADAS = ("catalogo", "declarado", "medido", "observado")
# Proveniência mínima de toda medição ou observação (desenho, seção 8).
PROVENIENCIA = ("metrica", "valor", "protocolo", "amostra", "provedor", "endpoint",
                "versao_resolvida", "data")
PROIBIDAS = ("capaz", "capable")  # veredito fundido, sem camada nem prova
LAYA = "laya/roteador-atual"      # o roteador, não um modelo: entra só pelo uso
ROTAS_USO = ("rapido", "livre", "pesado", "codigo")
ROTA_POR = ("laya", "regra")
TIPOS_USO = ("conversa", "codigo", "json", "contexto", "ferramenta")
COMO_USAR = ("Gerado por scripts/capivara_capacidades.py (fonte única). perfis-modelos.json é derivado "
             "deste arquivo (capivara_perfis.py) e é o que o gateway lê. Camadas: catalogo (inventário), "
             "declarado (afirmações por campo, com origem, fonte e data), medido (benchmark), observado "
             "(uso real). Número só com afirmação; sem afirmação, nao_medido. MEMÓRIAS (667).")

# Origem -> fonte padrão (URL ou endpoint). A documentação traz a sua própria.
FONTE_ORIGEM = {
    "omniroute": "omniroute GET /v1/models (127.0.0.1:20128)",
    "openrouter": "https://openrouter.ai/api/v1/models",
    "nvidia": "https://integrate.api.nvidia.com/v1/models",
    "ollama": "ollama GET /api/show (127.0.0.1:11434, num_ctx)",
    "documentacao": "janelas-documentadas.json",
}
# Campo -> origens que podem afirmá-lo, na ordem de precedência (a primeira com valor vence).
# Janela repete a precedência antiga de capivara_perfis (ollama > omniroute > documentação),
# e as listas públicas entram depois: só valem onde ninguém mais diz.
ORDEM = {
    "janela": ("ollama", "omniroute", "documentacao", "openrouter", "nvidia"),
    "saida_max": ("omniroute", "documentacao", "openrouter"),
    "ferramentas": ("omniroute", "openrouter", "nvidia"),
    "raciocinio": ("omniroute", "openrouter", "nvidia"),
    "listado": ("nvidia",),
}
INT_CAMPOS = ("janela", "saida_max")
BOOL_CAMPOS = ("ferramentas", "raciocinio", "listado")
# Texto que o perfil (perfis-modelos.json) mostra como fonte da janela.
TEXTO_FONTE = {"ollama": "ollama num_ctx", "omniroute": "omniroute /v1/models",
               "openrouter": "openrouter /api/v1/models (lista pública)",
               "nvidia": "nvidia /v1/models (lista pública)"}
TIPO_POR_PREFIXO = {"cod": "codigo", "fer": "ferramenta", "json": "json", "longo": "contexto_longo", "conv": "conversa"}
PESO_ROTULO = {"boa": 1.0, "parcial": 0.5, "ruim": 0.0, "ruim_grave": 0.0}


# --- afirmações (puras: recebem o JSON já lido, sem rede) ------------------------------
def _data_iso(texto: str | None) -> str | None:
    """Data da leitura dita no texto da fonte ('... (lido em 13/10/2026)'), em AAAA-MM-DD."""
    m = re.search(r"lido em (\d{2})/(\d{2})/(\d{4})", texto or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def _data_ok(s) -> bool:
    if not isinstance(s, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return False
    try:
        date.fromisoformat(s)
    except ValueError:
        return False
    return True


def _inteiro(v) -> int | None:
    return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else None


def _bool(v) -> bool | None:
    return v if isinstance(v, bool) else None


def _numero(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _claim(origem: str, valor, data: str | None, fonte: str | None = None) -> dict:
    return {"origem": origem, "fonte": fonte or FONTE_ORIGEM[origem], "data": data, "valor": valor}


def _pos(af: dict, mid: str, campo: str, claim: dict) -> None:
    af.setdefault(mid, {}).setdefault(campo, []).append(claim)


def _itens(dados) -> list[dict]:
    if not isinstance(dados, dict) or not isinstance(dados.get("data"), list):
        raise ValueError("forma inesperada: esperava objeto com lista em 'data'")
    return [x for x in dados["data"] if isinstance(x, dict)]


def afirma_omniroute(dados, data: str) -> dict:
    """GET /v1/models do OmniRoute. Só o que vier; campo ausente não vira valor."""
    af: dict = {}
    for it in _itens(dados):
        mid = it.get("id")
        if not isinstance(mid, str) or not mid:
            continue
        cap = it.get("capabilities") if isinstance(it.get("capabilities"), dict) else {}
        valores = {"janela": _inteiro(it.get("context_length")) or _inteiro(it.get("max_input_tokens")),
                   "saida_max": _inteiro(it.get("max_output_tokens")),
                   "ferramentas": _bool(cap.get("tool_calling")),
                   "raciocinio": _bool(cap.get("reasoning"))}
        for campo, v in valores.items():
            if v is not None:
                _pos(af, mid, campo, _claim("omniroute", v, data))
    return af


def afirma_openrouter(dados, data: str) -> dict:
    """GET /api/v1/models do OpenRouter (lista pública). O id do OmniRoute é 'openrouter/' + o id da lista.
    Só afirmação positiva em supported_parameters: a ausência na lista não prova que falta a capacidade."""
    af: dict = {}
    for it in _itens(dados):
        rid = it.get("id")
        if not isinstance(rid, str) or not rid:
            continue
        mid = "openrouter/" + rid
        tp = it.get("top_provider") if isinstance(it.get("top_provider"), dict) else {}
        sp = it.get("supported_parameters") if isinstance(it.get("supported_parameters"), list) else []
        janela = _inteiro(it.get("context_length")) or _inteiro(tp.get("context_length"))
        if janela is not None:
            _pos(af, mid, "janela", _claim("openrouter", janela, data))
        saida = _inteiro(tp.get("max_completion_tokens"))
        if saida is not None:
            _pos(af, mid, "saida_max", _claim("openrouter", saida, data))
        if "tools" in sp:
            _pos(af, mid, "ferramentas", _claim("openrouter", True, data))
        if "reasoning" in sp or "include_reasoning" in sp:
            _pos(af, mid, "raciocinio", _claim("openrouter", True, data))
    return af


def afirma_nvidia(dados, data: str) -> dict:
    """GET /v1/models da NVIDIA (lista pública). O id do OmniRoute é 'nvidia/' + o id da lista.
    A lista traz quase só o id; os campos extras aparecem em poucos itens e valem só onde vierem."""
    af: dict = {}
    for it in _itens(dados):
        rid = it.get("id")
        if not isinstance(rid, str) or not rid:
            continue
        mid = "nvidia/" + rid
        _pos(af, mid, "listado", _claim("nvidia", True, data))
        janela = _inteiro(it.get("context_window"))
        if janela is not None:
            _pos(af, mid, "janela", _claim("nvidia", janela, data))
        ferramentas = _bool(it.get("supports_tools"))
        if ferramentas is not None:
            _pos(af, mid, "ferramentas", _claim("nvidia", ferramentas, data))
        pensa = _bool(it.get("supports_thinking"))
        if pensa is not None:
            _pos(af, mid, "raciocinio", _claim("nvidia", pensa, data))
    return af


def afirma_documentacao(modelos_doc: dict) -> dict:
    """janelas-documentadas.json: só o que o provedor documenta, com a data da leitura no texto da fonte."""
    af: dict = {}
    for mid, d in (modelos_doc or {}).items():
        if not isinstance(mid, str) or not isinstance(d, dict) or not isinstance(d.get("fonte"), str):
            continue
        data = _data_iso(d["fonte"])
        for campo in INT_CAMPOS:
            v = _inteiro(d.get(campo))
            if v is not None:
                _pos(af, mid, campo, _claim("documentacao", v, data, d["fonte"]))
    return af


def afirma_ollama(modelo: str, num_ctx, data: str) -> dict:
    v = _inteiro(num_ctx)
    return {modelo: {"janela": [_claim("ollama", v, data)]}} if v is not None else {}


# --- resolução: afirmações -> campos resolvidos (mesma regra em montar, aplicar e conferir) ------
def _escolher(lista: list, ordem: tuple):
    for origem in ordem:
        for c in lista:
            if c.get("origem") == origem and c.get("valor") is not None:
                return c
    return None


def _texto_fonte(c: dict) -> str:
    if c["origem"] == "documentacao":
        return "documentação oficial: " + c["fonte"]
    return TEXTO_FONTE[c["origem"]]


def recalcular(entrada: dict) -> dict:
    """Recalcula janela, saida_max, fonte e os campos de `declarado` a partir das afirmações.
    Sem afirmação nenhuma: camadas vazias e fonte nao_medido."""
    decl = entrada.get("declarado") if isinstance(entrada.get("declarado"), dict) else {}
    claims = {k: v for k, v in (decl.get("claims") or {}).items() if v}
    if not claims:
        entrada["declarado"] = None
        entrada.update(janela=None, saida_max=None, fonte="nao_medido")
        return entrada
    res = {campo: (_escolher(claims.get(campo, []), ORDEM[campo]) or {}).get("valor") for campo in ORDEM}
    divergente = sorted(c for c, lista in claims.items()
                        if len({repr(x["valor"]) for x in lista if x.get("valor") is not None}) > 1)
    entrada["declarado"] = {**res, "divergente": divergente, "claims": claims}
    jc = _escolher(claims.get("janela", []), ORDEM["janela"])
    entrada["janela"] = res["janela"]
    entrada["saida_max"] = res["saida_max"]
    entrada["fonte"] = _texto_fonte(jc) if jc else "nao_medido"
    return entrada


def aplicar(modelos: dict, afirmacoes: dict) -> dict:
    """Põe afirmações no registro. Uma afirmação substitui a anterior da MESMA origem no MESMO campo;
    a de outra origem fica. Id fora do registro não entra (é candidato, não inventário)."""
    tocados = fora = 0
    for mid, campos in afirmacoes.items():
        if mid not in modelos or not isinstance(modelos[mid], dict):
            fora += 1
            continue
        e = modelos[mid]
        decl = e.get("declarado") if isinstance(e.get("declarado"), dict) else {}
        claims = {k: list(v) for k, v in (decl.get("claims") or {}).items()}
        for campo, novas in campos.items():
            lista = claims.setdefault(campo, [])
            for c in novas:
                lista[:] = [x for x in lista if x.get("origem") != c["origem"]]
                lista.append(c)
        e["declarado"] = {"claims": claims}
        recalcular(e)
        tocados += 1
    return {"aplicadas": tocados, "fora_do_inventario": fora}


def normalizar(reg: dict) -> dict:
    """Recalcula todas as entradas a partir das afirmações (para registro lido de versão anterior)."""
    for e in (reg.get("modelos") or {}).values():
        if isinstance(e, dict):
            recalcular(e)
    return reg


# --- catálogo (inventário) -------------------------------------------------------------
def camada_catalogo(item: dict | None, lido_em: str) -> dict | None:
    if not item:
        return None
    cap = item.get("capabilities") if isinstance(item.get("capabilities"), dict) else {}
    return {"fonte": FONTE_ORIGEM["omniroute"], "lido_em": lido_em,
            "provedor": item.get("owned_by"), "id_resolvido": item.get("root"),
            "janela": item.get("context_length") or item.get("max_input_tokens"),
            "saida_max": item.get("max_output_tokens"),
            "entrada": item.get("input_modalities"), "saida": item.get("output_modalities"),
            "ferramentas": cap.get("tool_calling"), "raciocinio": cap.get("reasoning"),
            "gratis": item.get("free"), "combo": item.get("owned_by") == "combo"}


def camada_candidato(item: dict) -> dict:
    """Um item do catalogo.json. O texto do erro de acesso fica de fora (é texto de terceiro)."""
    acesso = item.get("acesso_verificado")
    if isinstance(acesso, dict):
        acesso = {k: acesso[k] for k in ("status", "data", "latencia_s") if k in acesso}
    caps = item.get("capacidades")
    return {"fonte": item.get("fonte"), "nome": item.get("nome"), "provedor": item.get("provedor"),
            "capacidades": caps if isinstance(caps, list) else None,
            "estado": item.get("estado"), "acesso_verificado": acesso}


def _catalogo(item_omni: dict | None, item_cand: dict | None, lido_em: str) -> dict | None:
    cat = camada_catalogo(item_omni, lido_em)
    if cat is None and item_cand is None:
        return None
    if cat is None:
        acesso = item_cand.get("acesso_verificado")
        cat = {"fonte": "catalogo-modelos/catalogo.json (candidato, fora do OmniRoute)",
               "lido_em": acesso.get("data") if isinstance(acesso, dict) else None,
               "provedor": item_cand.get("provedor"), "id_resolvido": None, "janela": None,
               "saida_max": None, "entrada": None, "saida": None, "ferramentas": None,
               "raciocinio": None, "gratis": None, "combo": False}
    if item_cand is not None:
        cat["catalogo_modelos"] = camada_candidato(item_cand)
    return cat


def _entrada_vazia(fora: bool = True) -> dict:
    e = {"janela": None, "saida_max": None, "fonte": "nao_medido", "catalogo": None,
         "declarado": None, "medido": [], "observado": []}
    if fora:
        e["fora_da_cobertura"] = True
    return e


def _migrar_catalogo_antigo(v: dict, claims: dict) -> None:
    """Registro de antes desta versão guardava a janela, a saída e as capacidades do OmniRoute só em
    `catalogo`, sem origem nem data de afirmação. Se a montagem atual já não as vê, elas viram afirmação
    do OmniRoute com a data da leitura antiga (`catalogo.lido_em`): 'ausência não apaga' vale desde a
    primeira montagem nova. Sem data legível, não migra (não se sabe quando foi lido)."""
    cat = v.get("catalogo") if isinstance(v.get("catalogo"), dict) else None
    if not cat:
        return
    data = str(cat.get("lido_em") or "")[:10]
    if not _data_ok(data):
        return
    for campo, valida in (("janela", _inteiro), ("saida_max", _inteiro),
                          ("ferramentas", _bool), ("raciocinio", _bool)):
        valor = valida(cat.get(campo))
        if valor is not None and not any(c.get("origem") == "omniroute" for c in claims.get(campo, [])):
            claims.setdefault(campo, []).append(_claim("omniroute", valor, data))


def _base(v: dict, mid: str, omni: dict, cand: dict, lido_em: str) -> dict:
    """Entrada nova preservando medido, observado e as afirmações já gravadas."""
    decl = v.get("declarado") if isinstance(v.get("declarado"), dict) else {}
    claims = {k: list(x) for k, x in (decl.get("claims") or {}).items()} \
        if isinstance(decl.get("claims"), dict) else {}
    _migrar_catalogo_antigo(v, claims)
    claims = {k: x for k, x in claims.items() if x}
    e = {"catalogo": _catalogo(omni.get(mid), cand.get(mid), lido_em),
         "declarado": {"claims": claims} if claims else None,
         "medido": list(v.get("medido") or []), "observado": list(v.get("observado") or [])}
    return recalcular(e)


def montar(filas: dict, omni: dict, candidatos: list, documentadas: dict, ollama: dict,
           anterior: dict, lido_em: str) -> dict:
    """Registro novo a partir das fontes lidas. `omni` = {id: item de /v1/models}; `candidatos` = lista
    do catalogo.json; `documentadas` = o mapa `modelos` de janelas-documentadas.json; `ollama` =
    {modelo: num_ctx ou None}; `anterior` = o registro gravado (medido, observado e afirmações de fontes
    que não foram relidas agora são preservados)."""
    data = lido_em[:10]
    velhos = anterior.get("modelos") or {}
    cand = {c["id"]: c for c in candidatos if isinstance(c, dict) and isinstance(c.get("id"), str)}
    cobertura = {m for ordem in filas.values() for m in ordem} | set(omni) | set(cand)
    modelos = {}
    for m in sorted(cobertura):
        v = velhos.get(m) if isinstance(velhos.get(m), dict) else {}
        modelos[m] = _base(v, m, omni, cand, lido_em)
    aplicar(modelos, afirma_omniroute({"data": list(omni.values())}, data))
    aplicar(modelos, afirma_documentacao(documentadas))
    for m, num_ctx in ollama.items():
        if m in modelos:
            aplicar(modelos, afirma_ollama(m, num_ctx, data))
    for m, v in velhos.items():
        if m in modelos or not isinstance(v, dict):
            continue
        if v.get("medido") or v.get("observado"):  # medição não se descarta, mesmo fora da cobertura
            modelos[m] = _base(v, m, {}, {}, lido_em)
            modelos[m]["fora_da_cobertura"] = True
    reg = {"_como_usar": COMO_USAR, "gerado_em": lido_em, "filas": filas, "modelos": modelos}
    if anterior.get("uso_posicao"):
        reg["uso_posicao"] = anterior["uso_posicao"]
    if anterior.get("verificacao"):
        reg["verificacao"] = anterior["verificacao"]
    return reg


# --- conferência ------------------------------------------------------------------------
def _conferir_declarado(m: str, decl) -> list[str]:
    if decl is None:
        return []
    if not isinstance(decl, dict) or not isinstance(decl.get("claims"), dict):
        return [f"{m}.declarado: formato antigo (sem 'claims'); rode a montagem"]
    erros = []
    for campo, lista in decl["claims"].items():
        if campo not in ORDEM or not isinstance(lista, list):
            erros.append(f"{m}.declarado: campo '{campo}' desconhecido ou mal formado")
            continue
        for i, c in enumerate(lista):
            onde = f"{m}.declarado.{campo}[{i}]"
            if not isinstance(c, dict):
                erros.append(f"{onde}: não é objeto")
                continue
            if c.get("origem") not in ORDEM[campo]:
                erros.append(f"{onde}: origem '{c.get('origem')}' não pode afirmar '{campo}'")
                continue
            if not isinstance(c.get("fonte"), str) or not c["fonte"]:
                erros.append(f"{onde}: falta fonte")
                continue
            if not _data_ok(c.get("data")):
                erros.append(f"{onde}: falta data (AAAA-MM-DD)")
                continue
            valor = c.get("valor")
            if (campo in INT_CAMPOS and _inteiro(valor) is None) or (campo in BOOL_CAMPOS and not isinstance(valor, bool)):
                erros.append(f"{onde}: valor inválido para '{campo}'")
    return erros


def _verificacao_valida(v) -> bool:
    if not isinstance(v, dict) or not isinstance(v.get("linhas"), int) or v["linhas"] < 0 \
            or not isinstance(v.get("achados"), dict):
        return False
    for rot, d in v["achados"].items():
        if not (isinstance(rot, str) and ROTULO_ACHADO.fullmatch(rot) and isinstance(d, dict)):
            return False
        oc, rs = d.get("ocorrencias"), d.get("resolvidos_pela_refacao")
        if not (isinstance(oc, int) and isinstance(rs, int) and 0 <= rs <= oc):
            return False
    return True


def _acumular_verificacao(reg: dict, novas: list[dict]) -> None:
    """Soma no bloco global `verificacao` os rótulos achados nas linhas novas. `resolvidos_pela_refacao` conta a
    linha que tinha o rótulo, veio com corrigido true e foi refeita pelo menos uma vez."""
    ver = [x for x in novas if x["achados"] is not None]
    if not ver:
        return
    bloco = reg.get("verificacao") if isinstance(reg.get("verificacao"), dict) else {"linhas": 0, "achados": {}}
    bloco["linhas"] = bloco.get("linhas", 0) + len(ver)
    rotulos = bloco.setdefault("achados", {})
    for x in ver:
        for rot in x["achados"]:
            d = rotulos.setdefault(rot, {"ocorrencias": 0, "resolvidos_pela_refacao": 0})
            d["ocorrencias"] += 1
            if x["corrigido"] is True and (x["refeito"] or 0) >= 1:
                d["resolvidos_pela_refacao"] += 1
    bloco["desde"] = bloco.get("desde") or min(x["ts"] for x in ver).isoformat()
    bloco["ate"] = max(x["ts"] for x in ver).isoformat()
    reg["verificacao"] = bloco


def _posicao_valida(p) -> bool:
    return (isinstance(p, dict) and isinstance(p.get("inode"), int) and isinstance(p.get("offset"), int)
            and p["offset"] >= 0 and isinstance(p.get("janela_sha"), str) and len(p["janela_sha"]) == 64)


def conferir(reg: dict) -> list[str]:
    erros = []
    modelos = reg.get("modelos")
    if not isinstance(modelos, dict) or not modelos:
        return ["registro sem modelos"]
    if "uso_posicao" in reg and not _posicao_valida(reg["uso_posicao"]):
        erros.append("uso_posicao inválida (esperava inode, offset, janela_sha)")
    if "verificacao" in reg and not _verificacao_valida(reg["verificacao"]):
        erros.append("verificacao inválida (esperava linhas e achados por rótulo, com resolvidos <= ocorrencias)")
    for m, v in modelos.items():
        if not isinstance(v, dict):
            erros.append(f"{m}: entrada não é objeto")
            continue
        for k in v:
            if isinstance(k, str) and k.lower() in PROIBIDAS:
                erros.append(f"{m}: campo '{k}' funde as camadas (proibido)")
        faltam = [c for c in CAMADAS + ("janela", "saida_max", "fonte") if c not in v]
        if faltam:
            erros.append(f"{m}: falta {', '.join(faltam)}")
        n0 = len(erros)
        erros += _conferir_declarado(m, v.get("declarado"))
        for c in ("medido", "observado"):
            regs = v.get(c)
            if not isinstance(regs, list):
                erros.append(f"{m}.{c}: deveria ser lista")
                continue
            for i, r in enumerate(regs):
                faltam_p = [p for p in PROVENIENCIA if not isinstance(r, dict) or r.get(p) in (None, "")]
                if faltam_p:
                    erros.append(f"{m}.{c}[{i}]: falta proveniência ({', '.join(faltam_p)})")
                elif not (isinstance(r["amostra"], int) and r["amostra"] >= 1):
                    erros.append(f"{m}.{c}[{i}]: amostra deve ser inteiro >= 1")
        if len(erros) == n0 and not faltam:
            # Número sem afirmação (ou editado à mão) não passa: recalcula e compara.
            esperado = recalcular(json.loads(json.dumps(v)))
            for k in ("janela", "saida_max", "fonte", "declarado"):
                if v.get(k) != esperado.get(k):
                    erros.append(f"{m}: '{k}' não bate com as afirmações declaradas (número sem fonte ou editado à mão)")
                    break
    return erros


# --- medido (benchmark) -----------------------------------------------------------------
def incorporar(reg: dict, rodada: str, resumo: dict, rotulos: list[dict]) -> int:
    """Leva para `medido` as medidas mecânicas do `resumo.json` de uma rodada do benchmark e a qualidade
    por tipo de tarefa tirada dos rótulos daquela rodada (boa=1, parcial=0,5, ruim=0). Só modelos já no
    registro; o que já está (mesmo protocolo e métrica) não duplica."""
    novos = 0
    for modelo, v in (reg.get("modelos") or {}).items():
        r = resumo.get(modelo)
        if not r or not r.get("medido"):
            continue
        base = dict(r["medido"][0])
        registros = [dict(x, protocolo=f"{x['protocolo']} rodada:{rodada}") for x in r["medido"]]
        por_tipo: dict = {}
        for rot in rotulos:
            if rot.get("rodada") == rodada and rot.get("modelo") == modelo and rot.get("rotulo") in PESO_ROTULO:
                tipo = TIPO_POR_PREFIXO.get(rot["item"].split("-")[0])
                if tipo:
                    por_tipo.setdefault(tipo, []).append(PESO_ROTULO[rot["rotulo"]])
        for tipo, ps in sorted(por_tipo.items()):
            registros.append({"protocolo": f"{base['protocolo']} rodada:{rodada} rotulo-humano-ou-criterio",
                              "provedor": base["provedor"], "endpoint": base["endpoint"],
                              "versao_resolvida": base["versao_resolvida"], "data": base["data"],
                              "metrica": f"qualidade_{tipo}", "valor": round(sum(ps) / len(ps), 3), "amostra": len(ps)})
        ja = {(x.get("protocolo"), x.get("metrica")) for x in v.get("medido") or []}
        for x in registros:
            if (x["protocolo"], x["metrica"]) not in ja:
                v.setdefault("medido", []).append(x)
                novos += 1
    return novos


# --- observado (uso real do gateway) ----------------------------------------------------
def _ts(s) -> datetime | None:
    """Data-hora ISO com fuso. Sem fuso não serve: não dá para ordenar lotes com segurança."""
    if not isinstance(s, str) or not s:
        return None
    try:
        t = datetime.fromisoformat(s)
    except ValueError:
        return None
    return t if t.tzinfo is not None else None


# Verificação na 1ª resposta: rótulos curtos (slug). Só o rótulo é guardado, nunca texto.
ROTULO_ACHADO = re.compile(r"[a-z0-9][a-z0-9_.-]{0,39}")


def _achados(o: dict) -> list[str] | None:
    """Rótulos achados na 1ª resposta. Campo ausente = não verificada (None); null = [] (sem achado).
    Só slugs entram: outro valor deixa a linha não verificada."""
    if "achados" not in o:
        return None
    a = o.get("achados")
    if a is None:
        return []
    if isinstance(a, list) and all(isinstance(x, str) and ROTULO_ACHADO.fullmatch(x) for x in a):
        return list(dict.fromkeys(a))
    return None


def _refeito(o: dict) -> int | None:
    r = o.get("refeito")
    return r if isinstance(r, int) and not isinstance(r, bool) and r >= 0 else None


def _corrigido(o: dict) -> bool | None:
    return o["corrigido"] if isinstance(o.get("corrigido"), bool) else None


def _linha_uso(texto: str) -> dict | None:
    """Uma linha do uso.jsonl. Só lê os campos conhecidos: nenhum campo de texto é lido.
    Campos obrigatórios inválidos = linha malformada (None). rota/rota_por/laya_confianca são
    opcionais: inválidos só deixam a linha de fora do perfil Laya."""
    try:
        o = json.loads(texto)
    except ValueError:
        return None
    if not isinstance(o, dict):
        return None
    ts, modelo, tipo = _ts(o.get("ts")), o.get("modelo"), o.get("tipo")
    status, bloqueado, lat = o.get("status"), o.get("bloqueado"), o.get("latencia_ms")
    if ts is None or not isinstance(modelo, str) or not modelo or tipo not in TIPOS_USO:
        return None
    # status null = falha sem resposta (timeout, conexão): conta como falha, não some
    if status is not None and not (isinstance(status, int) and not isinstance(status, bool)):
        return None
    if not isinstance(bloqueado, bool):
        return None
    # latência null = falha sem medida: entra na taxa (como falha) e fica fora da mediana
    if lat is not None and (not _numero(lat) or lat < 0):
        return None
    rota = o.get("rota") if o.get("rota") in ROTAS_USO else None
    rota_por = o.get("rota_por") if o.get("rota_por") in ROTA_POR else None
    conf = o.get("laya_confianca")
    conf = float(conf) if _numero(conf) and 0 <= conf <= 1 else None
    return {"ts": ts, "modelo": modelo, "tipo": tipo, "status": status, "bloqueado": bloqueado,
            "latencia_ms": None if lat is None else float(lat), "rota": rota, "rota_por": rota_por,
            "laya_confianca": conf, "achados": _achados(o), "refeito": _refeito(o), "corrigido": _corrigido(o)}


# Bytes antes do offset que identificam o trecho já lido (detecta reescrita do que já foi incorporado).
JANELA_POSICAO = 512


def _janela_sha(p: Path, offset: int) -> str:
    inicio = max(0, offset - JANELA_POSICAO)
    with p.open("rb") as f:
        f.seek(inicio)
        trecho = f.read(offset - inicio)
    return hashlib.sha256(trecho).hexdigest()


def ler_incremento(caminho: Path, posicao: dict | None = None) -> tuple[list[dict], int, dict | None]:
    """Lê só o que é novo no uso.jsonl desde `posicao` = {inode, offset, janela_sha, tamanho}.
    Recomeça do zero (e incorpora o arquivo inteiro) quando o inode mudou (arquivo trocado), quando o
    arquivo encolheu, ou quando os bytes antes do offset já não batem com `janela_sha` (reescrita).
    Lê só linhas completas (terminadas em \\n): a linha que o gateway ainda está gravando fica para a
    próxima vez. Devolve (linhas válidas, malformadas, posição nova). Arquivo ausente: ([], 0, posicao)."""
    p = Path(caminho)
    if not p.is_file():
        return [], 0, posicao
    st = p.stat()
    inicio = 0
    if (posicao and posicao.get("inode") == st.st_ino and isinstance(posicao.get("offset"), int)
            and 0 <= posicao["offset"] <= st.st_size
            and _janela_sha(p, posicao["offset"]) == posicao.get("janela_sha")):
        inicio = posicao["offset"]
    with p.open("rb") as f:
        f.seek(inicio)
        dados = f.read()
    fim = dados.rfind(b"\n") + 1
    validas, mal = [], 0
    for crua in dados[:fim].split(b"\n"):
        texto = crua.decode("utf-8", errors="replace").strip()
        if not texto:
            continue
        lida = _linha_uso(texto)
        if lida is None:
            mal += 1
        else:
            validas.append(lida)
    nova = inicio + fim
    return validas, mal, {"inode": st.st_ino, "offset": nova, "janela_sha": _janela_sha(p, nova),
                          "tamanho": st.st_size}


def ler_uso(caminho: Path) -> tuple[list[dict], int]:
    """(linhas válidas, malformadas) do arquivo inteiro, sem estado. Arquivo ausente = ([], 0)."""
    validas, mal, _ = ler_incremento(Path(caminho), None)
    return validas, mal


def _resumo_periodo(grupo: list[dict]) -> dict:
    ts = [x["ts"] for x in grupo]
    return {"desde": min(ts).isoformat(), "ate": max(ts).isoformat()}


def _dia(iso: str) -> str:
    return datetime.fromisoformat(iso).date().isoformat()


def _somas_taxa(grupo: list[dict]) -> dict:
    """Contagens e somas de uma rodada (nunca taxas: taxa se recalcula a partir da soma acumulada)."""
    lat = [x["latencia_ms"] for x in grupo if x["latencia_ms"] is not None]
    ok = sum(1 for x in grupo if x["status"] == 200 and not x["bloqueado"])
    return {"amostra": len(grupo), "ok": ok, "falhas": len(grupo) - ok, "lat_n": len(lat),
            "lat_soma_ms": round(sum(lat), 3)}


def _d_taxa(r: dict) -> dict:
    return {"valor": round(r["ok"] / r["amostra"], 4),
            "latencia_media_ms": round(r["lat_soma_ms"] / r["lat_n"], 1) if r["lat_n"] else None,
            "data": _dia(r["ate"])}


def _d_achado(r: dict) -> dict:
    return {"valor": round(r["com_achado"] / r["amostra"], 4), "data": _dia(r["ate"])}


def _d_corrigido(r: dict) -> dict:
    return {"valor": round(r["corrigido_true"] / r["amostra"], 4), "data": _dia(r["ate"])}


def _d_refeito(r: dict) -> dict:
    return {"valor": round(r["refeito_soma"] / r["amostra"], 4), "data": _dia(r["ate"])}


def _d_confianca(r: dict) -> dict:
    return {"valor": round(r["conf_soma"] / r["amostra"], 4), "data": _dia(r["ate"])}


def _registro_acumulado(lista: list[dict], chave: dict) -> dict | None:
    for r in lista:
        if all(r.get(k) == v for k, v in chave.items()):
            return r
    return None


def _acumular(lista: list[dict], chave: dict, base: dict, somas: dict, derivar, periodo: dict) -> dict:
    """Um registro por chave, acumulado. Soma `somas` (contagens e somas) no que já existe, expande o período
    (desde = o menor, ate = o maior) e recalcula `valor` e o que `derivar` devolve. Uma rodada nova nunca
    recria nem zera o registro: só soma o que é novo."""
    r = _registro_acumulado(lista, chave)
    if r is None:
        r = {**chave, **base, **{c: 0 for c in somas}, "desde": periodo["desde"], "ate": periodo["ate"]}
        lista.append(r)
    for c, v in somas.items():
        r[c] = r[c] + v
    if datetime.fromisoformat(periodo["desde"]) < datetime.fromisoformat(r["desde"]):
        r["desde"] = periodo["desde"]
    if datetime.fromisoformat(periodo["ate"]) > datetime.fromisoformat(r["ate"]):
        r["ate"] = periodo["ate"]
    r.update(derivar(r))
    return r


def incorporar_linhas(reg: dict, novas: list[dict]) -> dict:
    """Soma as linhas novas no `observado`, um registro acumulado por chave (nunca um por rodada):
    - por modelo×tipo: taxa_ok (sucesso = status 200 e não bloqueado; cada falha conta 0), taxa_achado,
      taxa_corrigido e refeito_medio (só onde a verificação veio marcada);
    - Laya (`laya/roteador-atual`): taxa_ok por rota e por quem decidiu, e laya_confianca_media por rota.
    As taxas são recalculadas a partir das somas acumuladas. A escolha lê estes registros."""
    st = {"novas": len(novas), "registros": 0, "laya": 0, "ate": None, "verificacao": 0}
    if not novas:
        return st
    _acumular_verificacao(reg, novas)
    modelos = reg.setdefault("modelos", {})
    grupos: dict = {}
    for x in novas:
        grupos.setdefault((x["modelo"], x["tipo"]), []).append(x)
    for (modelo, tipo), g in sorted(grupos.items()):
        e = modelos.setdefault(modelo, _entrada_vazia())
        obs = e.setdefault("observado", [])
        id_res = (e.get("catalogo") or {}).get("id_resolvido") or modelo
        prov = {"provedor": modelo.split("/")[0] if "/" in modelo else modelo, "endpoint": modelo,
                "versao_resolvida": id_res}
        _acumular(obs, {"metrica": "taxa_ok", "tipo": tipo},
                  {**prov, "protocolo": f"uso de producao (uso.jsonl do gateway) tipo:{tipo}"},
                  _somas_taxa(g), _d_taxa, _resumo_periodo(g))
        st["registros"] += 1
        # verificação na 1ª resposta: só as linhas que trouxeram o campo entram nestas medidas
        ver = [x for x in g if x["achados"] is not None]
        com = [x for x in ver if x["achados"]]
        cc = [x for x in com if x["corrigido"] is not None]
        rf = [x for x in g if x["refeito"] is not None]
        if ver:
            _acumular(obs, {"metrica": "taxa_achado", "tipo": tipo},
                      {**prov, "protocolo": f"uso de producao (uso.jsonl) verificacao:taxa_achado tipo:{tipo}"},
                      {"amostra": len(ver), "com_achado": len(com)}, _d_achado, _resumo_periodo(ver))
            st["registros"] += 1
            st["verificacao"] += 1
        if cc:
            _acumular(obs, {"metrica": "taxa_corrigido", "tipo": tipo},
                      {**prov, "protocolo": f"uso de producao (uso.jsonl) verificacao:taxa_corrigido tipo:{tipo}"},
                      {"amostra": len(cc), "corrigido_true": sum(1 for x in cc if x["corrigido"])},
                      _d_corrigido, _resumo_periodo(cc))
            st["registros"] += 1
            st["verificacao"] += 1
        if rf:
            _acumular(obs, {"metrica": "refeito_medio", "tipo": tipo},
                      {**prov, "protocolo": f"uso de producao (uso.jsonl) verificacao:refeito_medio tipo:{tipo}"},
                      {"amostra": len(rf), "refeito_soma": sum(x["refeito"] for x in rf)},
                      _d_refeito, _resumo_periodo(rf))
            st["registros"] += 1
            st["verificacao"] += 1
    laya = [x for x in novas if x["rota"] and x["rota_por"]]
    if laya:
        e = modelos.setdefault(LAYA, _entrada_vazia())
        obs = e.setdefault("observado", [])
        base = {"provedor": "laya", "endpoint": LAYA, "versao_resolvida": "roteador-atual"}
        for rota in ROTAS_USO:
            for por in ROTA_POR:
                g = [x for x in laya if x["rota"] == rota and x["rota_por"] == por]
                if not g:
                    continue
                _acumular(obs, {"metrica": "taxa_ok", "rota": rota, "rota_por": por},
                          {**base, "protocolo": f"uso de producao (uso.jsonl) rota:{rota} por:{por}"},
                          _somas_taxa(g), _d_taxa, _resumo_periodo(g))
                st["laya"] += 1
            cf = [x for x in laya if x["rota"] == rota and x["laya_confianca"] is not None]
            if cf:
                _acumular(obs, {"metrica": "laya_confianca_media", "rota": rota},
                          {**base, "protocolo": f"uso de producao (uso.jsonl) rota:{rota} laya_confianca"},
                          {"amostra": len(cf), "conf_soma": round(sum(x["laya_confianca"] for x in cf), 6)},
                          _d_confianca, _resumo_periodo(cf))
                st["laya"] += 1
    st["registros"] += st["laya"]
    st["ate"] = max(x["ts"] for x in novas).isoformat()
    return st


def incorporar_arquivo(reg: dict, caminho: Path) -> dict:
    """Lê o uso.jsonl desde a posição guardada no registro, incorpora o que é novo e guarda a posição nova.
    Rodar duas vezes sem linha nova não duplica nada (a posição é o que torna isso idempotente)."""
    novas, mal, posicao = ler_incremento(Path(caminho), reg.get("uso_posicao"))
    st = incorporar_linhas(reg, novas)
    st.update(lidas=len(novas), malformadas=mal)
    if posicao is not None:
        reg["uso_posicao"] = posicao
    return st


# --- resumo, gravação e leitura ---------------------------------------------------------
def resumo(reg: dict) -> dict:
    mods = reg.get("modelos") or {}
    por_origem: dict = {}
    divergentes, sem_dado, com_janela, com_saida, fora = [], 0, 0, 0, 0
    camadas = {c: 0 for c in CAMADAS}
    for mid, e in mods.items():
        if e.get("fora_da_cobertura"):
            fora += 1
        for c in CAMADAS:
            if e.get(c):
                camadas[c] += 1
        if e.get("janela") is None:
            sem_dado += 1
        else:
            com_janela += 1
        if e.get("saida_max") is not None:
            com_saida += 1
        d = e.get("declarado") or {}
        if d.get("divergente"):
            divergentes.append(mid)
        cj = _escolher((d.get("claims") or {}).get("janela", []), ORDEM["janela"])
        if cj:
            por_origem[cj["origem"]] = por_origem.get(cj["origem"], 0) + 1
    return {"modelos": len(mods), "fora_da_cobertura": fora, "camadas": camadas, "janela": com_janela,
            "saida_max": com_saida, "sem_dado": sem_dado, "origem_janela": por_origem,
            "divergentes": sorted(divergentes)}


def gravar(reg: dict, caminho: Path = REGISTRO) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.parent / (caminho.name + ".tmp")
    tmp.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, caminho)


def _ler_json(caminho: Path, padrao):
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def registro_valido(caminho: Path) -> bool:
    reg = _ler_json(caminho, None)
    return isinstance(reg, dict) and bool(reg.get("modelos")) and not conferir(reg)


def caminho_registro(retrato: Path | None = None, estado: Path | None = None) -> Path:
    """Registro em uso: o do estado se existir e passar na conferência; senão o retrato do repositório.
    Os padrões são lidos na hora da chamada (não na definição), para que trocá-los no módulo valha."""
    retrato = REGISTRO if retrato is None else retrato
    estado = ESTADO_REGISTRO if estado is None else estado
    return estado if registro_valido(estado) else retrato


def carregar(caminho: Path | None = None) -> dict:
    return _ler_json(caminho or caminho_registro(), {})


def gravar_retrato_e_estado(reg: dict) -> None:
    """Build manual: retrato versionado e estado saem iguais, para o estado mais antigo não esconder o
    retrato recém-gerado (caminho_registro() prefere o estado quando ele é válido)."""
    gravar(reg, REGISTRO)
    gravar(reg, ESTADO_REGISTRO)


# --- leitura local (OmniRoute, catálogo, documentação, Ollama) -------------------------
def _num_ctx_ollama(q, modelo: str) -> int | None:
    req = urllib.request.Request(OLLAMA + "/api/show", json.dumps({"model": modelo.split("/", 1)[1]}).encode(),
                                 {"Content-Type": "application/json"})
    try:
        with q._SEM_PROXY.open(req, timeout=15) as r:
            params = json.load(r).get("parameters", "")
    except (OSError, ValueError):
        return None
    for linha in str(params).splitlines():
        partes = linha.split()
        if len(partes) == 2 and partes[0] == "num_ctx":
            try:
                return _inteiro(int(partes[1]))
            except ValueError:
                return None
    return None


def ler_tudo():
    """Filas, OmniRoute (/v1/models, local, com o token interno), catalogo.json, documentação e num_ctx."""
    sys.path.insert(0, str(RAIZ / "scripts"))
    import queda_por_elo as q  # noqa: E402  (filas, token interno, abridor sem proxy)
    filas = q.ler_filas(quais=FILAS)
    req = urllib.request.Request(q.PROXY + "/v1/models", headers={"X-Agata-Token": q._token_interno()})
    with q._SEM_PROXY.open(req, timeout=30) as r:
        dados = json.load(r)
    omni = {m["id"]: m for m in dados.get("data", []) if isinstance(m, dict) and m.get("id")}
    candidatos = _ler_json(CATALOGO_VIVO, [])
    doc = _ler_json(DOCUMENTADAS, {}).get("modelos", {})
    ids = {m for ordem in filas.values() for m in ordem} | set(omni)
    ids |= {c["id"] for c in candidatos if isinstance(c, dict) and isinstance(c.get("id"), str)}
    ollama = {m: _num_ctx_ollama(q, m) for m in sorted(ids) if m.startswith("ollama-local/")}
    return filas, omni, candidatos, doc, ollama


def _imprimir_resumo(reg: dict) -> None:
    r = resumo(reg)
    print(f"modelos: {r['modelos']} (fora da cobertura do OmniRoute/catálogo: {r['fora_da_cobertura']})")
    print("camadas com dado: " + ", ".join(f"{c}={n}" for c, n in r["camadas"].items()))
    print(f"janela com número: {r['janela']}; sem dado (nao_medido): {r['sem_dado']}; saída máxima com número: {r['saida_max']}")
    print("janela por origem: " + (", ".join(f"{k}={v}" for k, v in sorted(r["origem_janela"].items())) or "nenhuma"))
    div = r["divergentes"]
    print(f"divergentes (origens discordam): {len(div)}" + (": " + ", ".join(div[:8]) if div else ""))
    for m in sorted({x for ordem in reg["filas"].values() for x in ordem}):
        e = reg["modelos"].get(m) or {}
        print(f"  fila  {m:52} janela={str(e.get('janela')):>8} saida={str(e.get('saida_max')):>7}  {str(e.get('fonte'))[:46]}")


def _incorporar_uso_cli(arq: str | None) -> int:
    caminho = Path(arq) if arq else USO
    reg = carregar()
    if not reg.get("modelos"):
        print("registro de capacidades ausente: rode capivara_capacidades.py antes")
        return 1
    if not caminho.is_file():
        print("uso: sem arquivo de uso ainda; nada a incorporar")
        return 0
    antes = json.dumps(reg, sort_keys=True)
    st = incorporar_arquivo(reg, caminho)
    erros = conferir(reg)
    if erros:
        print("INVÁLIDO, nada gravado:\n  " + "\n  ".join(erros))
        return 1
    if json.dumps(reg, sort_keys=True) != antes:
        gravar(reg, ESTADO_REGISTRO)  # uso é operacional: vai para o estado, não para o retrato do repositório
    print(f"uso: linhas válidas {st['lidas']}, malformadas {st['malformadas']}, novas {st['novas']}; "
          f"registros gravados {st['registros']} (laya {st['laya']}); ate={st['ate']}")
    return 0


def _incorporar_medido_cli(dirs: list[str]) -> int:
    reg = carregar()
    total = 0
    for d in dirs:
        pasta = Path(d)
        rotulos_arq = pasta.parent / "rotulos.jsonl"
        rotulos = [json.loads(x) for x in rotulos_arq.read_text(encoding="utf-8").splitlines() if x.strip()] \
            if rotulos_arq.exists() else []
        total += incorporar(reg, pasta.name, json.loads((pasta / "resumo.json").read_text(encoding="utf-8")), rotulos)
    erros = conferir(reg)
    if erros:
        print("INVÁLIDO, nada gravado:\n  " + "\n  ".join(erros))
        return 1
    gravar_retrato_e_estado(reg)
    print(f"incorporadas {total} medidas novas")
    return 0


def _selftest() -> int:
    import unittest
    aqui = str(Path(__file__).resolve().parent)
    if aqui not in sys.path:
        sys.path.insert(0, aqui)
    import testar_capivara_capacidades as t  # noqa: E402
    suite = unittest.defaultTestLoader.loadTestsFromModule(t)
    res = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
    print("SELFTEST OK" if res.wasSuccessful() else "SELFTEST: FALHA(S)")
    return 0 if res.wasSuccessful() else 1


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    if argv == ["--conferir"]:
        erros = conferir(carregar())
        print("OK: registro válido" if not erros else "INVÁLIDO:\n  " + "\n  ".join(erros))
        return 1 if erros else 0
    if argv[:1] == ["--incorporar"] and len(argv) >= 2:
        return _incorporar_medido_cli(argv[1:])
    if argv[:1] == ["--incorporar-uso"] and len(argv) <= 2:
        return _incorporar_uso_cli(argv[1] if len(argv) == 2 else None)
    if argv not in ([], ["--relato"]):
        print(__doc__)
        return 2
    filas, omni, candidatos, doc, ollama = ler_tudo()
    reg = montar(filas, omni, candidatos, doc, ollama, carregar(), time.strftime("%Y-%m-%d %H:%M %z"))
    erros = conferir(reg)
    if erros:
        print("INVÁLIDO, nada gravado:\n  " + "\n  ".join(erros))
        return 1
    _imprimir_resumo(reg)
    if argv == ["--relato"]:
        print("relato: nada gravado")
        return 0
    gravar_retrato_e_estado(reg)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import capivara_perfis  # noqa: E402  (o perfil que o gateway lê é derivado deste registro)
    perfil = capivara_perfis.derivar(reg)
    gravar(perfil, PERFIS)            # retrato: é o que o gateway lê por caminho explícito
    gravar(perfil, ESTADO_PERFIL)
    print(f"gravado: retrato {REGISTRO.name} e {PERFIS.name} (derivado); estado em {ESTADO_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
