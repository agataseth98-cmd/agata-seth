#!/usr/bin/env python3
"""Laya no roteador da Seth: pergunta, avaliação e ajuste fino (MEMÓRIAS (718)/(719)).

Roda com o venv FORA do repo, `~/.local/share/agata-laya/.venv` (torch + `laya` 0.4.8 do
PyPI, Apache-2.0) -- o resto do sistema é stdlib e não importa isto.

  avaliar(concorrente, arquivo)  acerto por classe, com o limiar de produção, e tempo
  treinar(entrada, saida)        ajuste fino do laya-multilingual (rótulo em `expected`)

Uso:
  .venv/bin/python redesign/laya/laya_roteador.py avaliar <laya-base|jev|DIR> <teste.jsonl>...
  .venv/bin/python redesign/laya/laya_roteador.py treinar <treino.jsonl> <saida_dir>
"""
from __future__ import annotations

import collections
import json
import sys
import time
import urllib.request

# A MESMA pergunta do gateway (seth_gateway._PERGUNTA_ROTA): treinar com outra seria
# treinar para outro problema.
PERGUNTA = {"rota": {"type": "choice", "instructions": "What kind of AI model does this user request need?",
    "criteria": {"rapido": "a greeting, thanks, confirmation or trivial one-line question",
                 "livre": "normal conversation, everyday explanation or writing help, no hard reasoning",
                 "pesado": "hard reasoning, proof, deep technical analysis or complex planning",
                 "codigo": "writing, fixing or explaining programming code, SQL or a script"}}}
LIMIAR = 0.6


def concorrente(nome: str, device: str = "cpu"):
    if nome == "jev":
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def f(s):
            req = urllib.request.Request("http://127.0.0.1:11435/v1/systemone",
                json.dumps({"model": "winnow:e4b", "state": s, "questions": PERGUNTA}).encode(),
                {"Content-Type": "application/json"})
            with op.open(req, timeout=120) as r:
                return json.load(r)["answers"]["rota"]
        return f
    import laya
    a = laya.load("multilingual" if nome == "laya-base" else nome, device=device)
    return lambda s: a.predict(s, PERGUNTA)["answers"]["rota"]


def avaliar(f, arquivo: str) -> dict:
    itens = [json.loads(l) for l in open(arquivo, encoding="utf-8")]
    ok = okl = cob = 0
    ms, por = [], collections.defaultdict(lambda: [0, 0])
    for x in itens:
        t = time.monotonic()
        r = f(x["state"])
        ms.append((time.monotonic() - t) * 1000)
        acerto = r["choice"] == x["gold"]
        ok += acerto
        por[x["gold"]][0] += acerto
        por[x["gold"]][1] += 1
        if r["confidence"] >= LIMIAR:
            cob += 1
            okl += acerto
    ms.sort()
    return {"n": len(itens), "acerto": ok / max(len(itens), 1), "decide": cob,
            "acerta_quando_decide": okl / max(cob, 1), "ms_p50": ms[len(ms) // 2] if ms else None,
            "por_classe": {g: f"{a}/{b}" for g, (a, b) in sorted(por.items())}}


def treinar(entrada: str, saida: str) -> dict:
    from laya.train import TrainConfig, finetune, resolve_checkpoint_dir
    conv = saida.rstrip("/") + "-dados.jsonl"
    with open(entrada, encoding="utf-8") as f, open(conv, "w", encoding="utf-8") as g:
        for l in f:
            x = json.loads(l)
            g.write(json.dumps({"state": x["state"], "questions": PERGUNTA, "expected": {"rota": x["gold"]}},
                               ensure_ascii=False) + "\n")
    # Medido em 15/10/2026 (v1 941 itens, v2 1.917): 4 épocas, opções embaralhadas contra o
    # viés de posição (#131 do projeto), alguns minutos na RTX 4060 de 8 GB.
    cfg = TrainConfig(epochs=4, micro_batch=8, grad_accum=4, shuffle_options=("choice",), seed=0)
    return finetune(conv, resolve_checkpoint_dir("multilingual"), saida, cfg)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "avaliar":
        f = concorrente(a[1])
        for arq in a[2:]:
            print(arq, json.dumps(avaliar(f, arq), ensure_ascii=False))
    elif len(a) == 3 and a[0] == "treinar":
        print(treinar(a[1], a[2]))
    else:
        sys.exit(__doc__)
