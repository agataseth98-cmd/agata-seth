#!/usr/bin/env python3
"""Corpo operacional — estado de saúde a partir de uma fotografia.

Estados (matriz de redundância §4): normal · pressionado · degradado · isolado · indisponivel.
Os limiares abaixo são PROVISÓRIOS e declarados na spec; mudá-los é decisão do Humano.
Dado ausente nunca é estimado: vira "não medido" e não conta como normal.

- indisponivel: Ollama (rota local de fundo) sem resposta E OmniRoute sem resposta;
- isolado: só o local responde (sem catálogo/combos remotos);
- degradado: recurso crítico (disco < 5%, memória < 5%, temperatura >= 95 °C) ou
  unidade essencial (omniroute, ollama) fora;
- pressionado: disco < 15%, memória < 15%, carga >= 1,5 por CPU ou temperatura >= 85 °C;
- normal: nada acima e nada essencial sem medida.

Unidade sob demanda inativa (gateway, embeddings, painel — decisão de 29/10, sistema sob
demanda) NÃO rebaixa o estado: inativo não é quebrado.
"""
from __future__ import annotations

import json
import sys

LIMIARES = {"disco_critico": 5, "disco_pressao": 15, "mem_critico": 5, "mem_pressao": 15,
            "carga_pressao": 1.5, "temp_critico": 95, "temp_pressao": 85}
ESSENCIAIS = ("omniroute.service",)


def classificar(foto: dict, lim: dict = LIMIARES) -> dict:
    r = foto.get("recursos") or {}
    erros = (foto.get("modelos") or {}).get("erros") or {}
    serv = foto.get("servicos") or {}
    motivos, nao_medido = [], [k for k, v in r.items() if v is None]
    local_ok = "ollama" not in erros
    remoto_ok = "catalogo" not in erros and "combos" not in erros
    if not local_ok and not remoto_ok:
        return {"estado": "indisponivel", "motivos": ["Ollama e OmniRoute sem resposta"], "nao_medido": nao_medido}
    if local_ok and not remoto_ok:
        return {"estado": "isolado", "motivos": ["só a rota local respondeu"], "nao_medido": nao_medido}

    def abaixo(chave, limite):
        v = r.get(chave)
        return v is not None and v < limite

    def acima(chave, limite):
        v = r.get(chave)
        return v is not None and v >= limite
    if abaixo("disco_livre_pct", lim["disco_critico"]):
        motivos.append("disco crítico")
    if abaixo("memoria_disponivel_pct", lim["mem_critico"]):
        motivos.append("memória crítica")
    if acima("temperatura_max_c", lim["temp_critico"]):
        motivos.append("temperatura crítica")
    for u in ESSENCIAIS:
        if u in serv and not serv[u].startswith("active"):
            motivos.append(f"{u} {serv[u]}")
    if not local_ok:
        motivos.append("Ollama sem resposta")
    if motivos:
        return {"estado": "degradado", "motivos": motivos, "nao_medido": nao_medido}
    if abaixo("disco_livre_pct", lim["disco_pressao"]):
        motivos.append("disco abaixo de 15%")
    if abaixo("memoria_disponivel_pct", lim["mem_pressao"]):
        motivos.append("memória abaixo de 15%")
    if acima("carga_1min_por_cpu", lim["carga_pressao"]):
        motivos.append("carga alta")
    if acima("temperatura_max_c", lim["temp_pressao"]):
        motivos.append("temperatura alta")
    if motivos:
        return {"estado": "pressionado", "motivos": motivos, "nao_medido": nao_medido}
    return {"estado": "normal", "motivos": [], "nao_medido": nao_medido}


if __name__ == "__main__":
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    import fotografar  # noqa: E402
    f = fotografar.ultima() or fotografar.fotografar()
    print(json.dumps({"quando": f["quando"], **classificar(f)}, ensure_ascii=False, indent=1))
