#!/usr/bin/env python3
"""Redundância por capacidade — teste funcional mínimo de cada rota (Experimento GPT,
(043)–(047) e `matriz-redundancia-agata-2026-11-04.md`).

Uma rota só conta como redundância para uma capacidade depois de passar num teste
pertinente. Catálogo, flag `available` e instalação não contam. Este script:

- monta as rotas que o orçamento do painel permite: `local` (tags do Ollama),
  `gratuito` (modelos marcados disponíveis no OmniRoute), `assinatura` (CLI dos
  provedores de `provedores.json`) e `pago` (API com chave, modelo e tarifa);
- roda três provas sintéticas e fixas (nada do Humano sai da Máquina): conversa, formato
  JSON e código. Verificação é mecânica (regex ou `json.loads`), não juízo de modelo;
- descreve a independência de cada rota (família, provedor, cota, hardware, rede):
  provedor diferente reduz algumas dependências, não garante verdade;
- coordena pela `tarefas.py` (paralelo para remoto, fila única para a GPU local, teto
  de chamadas do orçamento, cancelamento) e grava em
  `<dados>/redundancia/testes/<run_id>.json`. Não muda fila nenhuma do OmniRoute.

Uso: testar_rotas.py [--categorias local,gratuito,assinatura,pago] [--limite N]
Só roda quando o Humano pede (painel ou terminal): consome inferência.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
for _p in (AQUI, REPO / "redesign" / "nova_versao"):
    sys.path.insert(0, str(_p))
import adaptadores  # noqa: E402
import eventos  # noqa: E402
import orcamento  # noqa: E402
import tarefas  # noqa: E402

OLLAMA = "http://127.0.0.1:11434"
OMNI = "http://127.0.0.1:20128"


def _json_ok(t: str) -> bool:
    m = re.search(r"\{.*\}", t or "", re.S)
    try:
        return bool(m) and json.loads(m.group(0)).get("ok") is True
    except ValueError:
        return False


PROVAS = {
    "conversa": ("Responda apenas com a palavra: pronto", lambda t: bool(re.search(r"\bpronto\b", (t or "").lower()))),
    "formato": ('Responda somente com este JSON, sem mais nada: {"ok": true}', _json_ok),
    "codigo": ("Escreva só a expressão em Python que soma 2 e 3, sem explicação.",
               lambda t: bool(re.search(r"2\s*\+\s*3", t or ""))),
}


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read())


def _post(url, corpo, timeout):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


GRATUITOS = REPO / "config" / "gratuitos_omniroute.json"


def gratuitos_configurados() -> list[str]:
    """Ids de modelos gratuitos ativos, que o OmniRoute aceita por passagem (ex.: openrouter/<id>:free).
    Lista versionada em config/gratuitos_omniroute.json; `ativo: false` deixa de fora (ex.: origem anônima)."""
    try:
        d = json.loads(GRATUITOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [x["id"] for x in d.get("modelos", []) if x.get("ativo") and x.get("id")]


def rotas(categorias: set[str], get=None) -> list[dict]:
    get = get or _get
    o = orcamento.ler()
    out = []
    if "local" in categorias and o["provedores"]["local"]:
        try:
            for m in get(f"{OLLAMA}/api/tags").get("models", []):
                n = m.get("name", "")
                if n and "embed" not in n.lower():
                    out.append({"rota": f"ollama-local/{n}", "categoria": "local", "tipo": "ollama", "modelo": n,
                                "independencia": {"familia": n.split(":")[0], "provedor": "local", "cota": "nenhuma",
                                                  "hardware": "GPU local (fila única)", "rede": "nenhuma"}})
        except Exception:  # noqa: BLE001
            pass
    if "gratuito" in categorias and o["provedores"]["gratuito"]:
        try:
            for m in get(f"{OMNI}/api/models").get("models", []):
                n = m.get("fullModel")
                if n and m.get("available") and not n.endswith("/auto"):
                    out.append({"rota": n, "categoria": "gratuito", "tipo": "omniroute", "modelo": n,
                                "independencia": {"familia": n.split("/")[-1].split("-")[0], "provedor": n.split("/")[0],
                                                  "cota": "gratuita do provedor", "hardware": "remoto", "rede": "internet"}})
        except Exception:  # noqa: BLE001
            pass
    if "gratuito" in categorias and o["provedores"]["gratuito"]:
        ja = {r["rota"] for r in out}
        for n in gratuitos_configurados():
            if n not in ja:
                out.append({"rota": n, "categoria": "gratuito", "tipo": "omniroute", "modelo": n,
                            "independencia": {"familia": n.split("/")[-1].split("-")[0], "provedor": n.split("/")[0],
                                              "cota": "gratuita do provedor (cota pode esgotar: sinalizada)",
                                              "hardware": "remoto", "rede": "internet"}})
    for p in adaptadores.estado():
        for modo in ("cli", "api"):
            info = p["modos"].get(modo)
            if info and info["disponivel"] and info.get("categoria") in categorias and o["provedores"].get(info["categoria"]):
                out.append({"rota": f"{p['id']}:{modo}", "categoria": info["categoria"], "tipo": "conexao", "provedor": p["id"],
                            "modo": modo, "modelo": info.get("modelo"),
                            "independencia": {"familia": p["id"], "provedor": p["id"],
                                              "cota": "assinatura do usuário" if modo == "cli" else "por token",
                                              "hardware": "remoto", "rede": "internet"}})
    return out


def chamar_rota(r: dict, prompt: str, timeout_s: int, *, max_tokens: int = 60, post=None, chamadas_ja: int = 0) -> dict:
    """Uma chamada a uma rota de `rotas()`, dentro do orçamento. Devolve ok, texto, usage, latencia_ms,
    falha_etapa e erro. Reaproveitada pela avaliação (redesign/avaliacao/avaliar.py)."""
    post = post or _post
    t0 = time.monotonic()
    if r["tipo"] == "conexao":
        res = adaptadores.chamar(r["provedor"], r["modo"], prompt, max_tokens=max_tokens, chamadas_ja=chamadas_ja)
    else:
        ok, motivo = orcamento.permite(r["categoria"])
        if not ok:
            return {"ok": False, "falha_etapa": "orcamento", "erro": motivo}
        try:
            if r["tipo"] == "ollama":
                d = post(f"{OLLAMA}/api/chat", {"model": r["modelo"], "stream": False, "think": False,
                                                 "messages": [{"role": "user", "content": prompt}],
                                                 "options": {"temperature": 0, "num_predict": max_tokens}}, timeout_s)
                res = {"ok": True, "texto": (d.get("message") or {}).get("content", ""),
                       "usage": {"input_tokens": d.get("prompt_eval_count"), "output_tokens": d.get("eval_count")}}
            else:
                d = post(f"{OMNI}/v1/chat/completions", {"model": r["modelo"], "max_tokens": max_tokens, "temperature": 0,
                                                         "messages": [{"role": "user", "content": prompt}]}, timeout_s)
                u = d.get("usage") or {}
                res = {"ok": True, "texto": ((d.get("choices") or [{}])[0].get("message") or {}).get("content", ""),
                       "usage": {"input_tokens": u.get("prompt_tokens"), "output_tokens": u.get("completion_tokens")}}
        except Exception as e:  # noqa: BLE001
            # cota esgotada (429, limite, quota) é estado próprio: a rota fica sinalizada, não "quebrada"
            cota = bool(re.search(r"\b429\b|rate.?limit|quota|exhaust|too many requests", str(e), re.I))
            res = {"ok": False, "falha_etapa": "cota_esgotada" if cota else "transporte",
                   "erro": f"{e.__class__.__name__}: {str(e)[:160]}"}
    if res.get("latencia_ms") is None:
        res["latencia_ms"] = round((time.monotonic() - t0) * 1000)
    return res


def _executor(timeout_s: int, post=None):
    def f(item):
        prompt, _ = PROVAS[item["capacidade"]]
        res = chamar_rota(item["rota_info"], prompt, timeout_s, post=post)
        res["passou"] = bool(res.get("ok")) and PROVAS[item["capacidade"]][1](res.get("texto"))
        res.pop("texto", None)   # a resposta não é guardada: só o veredito mecânico
        return res
    return f


def testar(categorias: set[str] | None = None, limite: int | None = None, *, get=None, post=None) -> dict:
    o = orcamento.ler()
    categorias = categorias or {c for c, ligado in o["provedores"].items() if ligado}
    lista = rotas(categorias, get)[: limite or None]
    itens = [{"chave": f"{r['rota']}|{cap}", "capacidade": cap, "rota_info": r,
              "recurso": "gpu" if r["categoria"] == "local" else None} for r in lista for cap in PROVAS]
    t = tarefas.criar("redundancia", itens, max_chamadas=o["max_chamadas"], prazo_s=max(o["timeout_s"] * 3, 300))
    t = tarefas.executar(t, _executor(o["timeout_s"], post), paralelo=True)
    resultados = []
    for i in itens:
        r = t["resultados"].get(i["chave"], {})
        resultados.append({"rota": i["rota_info"]["rota"], "categoria": i["rota_info"]["categoria"], "capacidade": i["capacidade"],
                           "passou": r.get("passou", False), "ok": r.get("ok", False), "falha_etapa": r.get("falha_etapa"),
                           "erro": r.get("erro"), "latencia_ms": r.get("latencia_ms"), "usage": r.get("usage"),
                           "independencia": i["rota_info"]["independencia"]})
    resumo = {cap: sorted({x["rota"] for x in resultados if x["capacidade"] == cap and x["passou"]}) for cap in PROVAS}
    run = {"schema_version": 1, "run_id": t["task_id"], "commit": t["contexto_versao"], "quando": t.get("fim"),
           "estado": t["estado"], "obsoleto": t["obsoleto"], "categorias": sorted(categorias), "chamadas": t["chamadas"],
           "provas": {k: v[0] for k, v in PROVAS.items()}, "resultados": resultados,
           "rotas_que_passaram": resumo,
           "nota": "redundância demonstrada só para a capacidade testada; independência é descrita, não garantida"}
    p = eventos.dados() / "redundancia" / "testes" / f"{t['task_id']}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(run, ensure_ascii=False, indent=1), encoding="utf-8")
    eventos.registrar("verification", t["estado"], f"redundancia:{t['task_id']}", componente="redundancia",
                      rotas=len(lista), passaram={k: len(v) for k, v in resumo.items()})
    return run


def ultimo() -> dict | None:
    pasta = eventos.dados() / "redundancia" / "testes"
    arqs = sorted(pasta.glob("t-*.json")) if pasta.exists() else []
    return json.loads(arqs[-1].read_text(encoding="utf-8")) if arqs else None


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--categorias")
    ap.add_argument("--limite", type=int)
    a = ap.parse_args()
    r = testar(set(a.categorias.split(",")) if a.categorias else None, a.limite)
    print(json.dumps({k: r[k] for k in ("run_id", "estado", "chamadas", "rotas_que_passaram")}, ensure_ascii=False, indent=1))
