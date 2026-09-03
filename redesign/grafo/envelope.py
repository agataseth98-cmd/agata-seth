#!/usr/bin/env python3
"""
P4-03 -- GBNF so no envelope, em DUAS FASES.

Fase 1: chamada com a gramatica `envelope.gbnf` -> produz so o cabecalho Regra 1 + `sync:`
        + eco (a gramatica termina depois do eco; a geracao para ali).
Fase 2: chamada SEM gramatica e SEM o system prompt do envelope (so a pergunta) -> gera o
        CORPO com zero restricao (anti alignment-tax, PESQUISA C3). Depois: envelope + corpo.

O modelo recebe os fatos REAIS da hidratacao no prompt; a gramatica so garante a forma.

Uso:
    envelope.py --pergunta "..." [--hash <hex12>] [--entrada 309] [--sync "PASS · ..."] [--free] [--seed N]
        --free: uma unica chamada SEM gramatica (baseline p/ comparar o corpo)
"""
import json
import re
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LLAMACPP = os.environ.get("AGATA_LLAMACPP", "http://127.0.0.1:20129")
GBNF = (HERE / "envelope.gbnf").read_text(encoding="utf-8")
MODEL = "qwen3-30b-a3b"


def _sys_msg(hash_estado, entrada, sync):
    return (
        "Voce responde SEMPRE começando por um envelope de 3 linhas, exatamente nesta forma:\n"
        "modelo: <seu nome> · turno: t=<n> (contado no contexto) · última entrada: (<N>)\n"
        "sync: <PASS|FALHA|não verificado> · <detalhe>\n"
        "eco: HASH-ESTADO=<hex de 12> — <uma frase dizendo por que o estado esta coerente>\n"
        "Depois do envelope, uma linha em branco e a resposta em texto livre.\n\n"
        "FATOS DESTA SESSAO (use-os no envelope, nao invente):\n"
        f"- ultima entrada de MEMORIAS: ({entrada})\n"
        f"- HASH-ESTADO: {hash_estado}\n"
        f"- sync: {sync}\n"
        "- seu turno: t=1 (contado no contexto); seu nome: Agata\n"
    )


def _chat(messages, *, grammar=None, max_tokens=500, temperature=0.7, seed=None):
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens,
            "temperature": temperature}
    if grammar:
        body["grammar"] = grammar
    if seed is not None:
        body["seed"] = seed
    req = urllib.request.Request(f"{LLAMACPP}/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"].get("content") or ""


def gerar(pergunta, hash_estado="a1b2c3d4e5f6", entrada=309,
          sync="PASS · REGRAS=deadbeef · MEMÓRIAS=cafef00d · HEAD=abc1234",
          free=False, temperature=0.7, seed=None):
    sysm = _sys_msg(hash_estado, entrada, sync)
    base = [{"role": "system", "content": sysm}, {"role": "user", "content": pergunta}]
    if free:
        return _chat(base, temperature=temperature, seed=seed)
    # fase 1 -- SO o envelope, com gramatica (a gramatica termina depois do eco)
    envelope = _chat(base, grammar=GBNF, max_tokens=200, temperature=temperature, seed=seed).rstrip("\n")
    # fase 2 -- corpo: geracao SEM gramatica e SEM o system prompt do envelope (so a pergunta),
    #           para o corpo nao carregar restricao nenhuma (anti alignment-tax, PESQUISA C3).
    corpo = _chat([{"role": "user", "content": pergunta}],
                  max_tokens=500, temperature=temperature,
                  seed=(seed + 1 if seed is not None else None))
    return envelope + "\n\n" + _so_corpo(corpo)


_ENV_RE = re.compile(r"^\s*(modelo:|sync:|eco:|.{0,40}(turno: t\s*[=≥]|última entrada: \())", re.IGNORECASE)


def _so_corpo(texto):
    """Descarta linhas de envelope que a geracao livre por ventura tenha emitido no inicio."""
    linhas = texto.splitlines()
    i = 0
    while i < len(linhas) and (not linhas[i].strip() or _ENV_RE.match(linhas[i])):
        i += 1
    return "\n".join(linhas[i:]).strip() or texto.strip()


if __name__ == "__main__":
    a = sys.argv[1:]
    g = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    out = gerar(g("--pergunta", "Explique em 3 frases por que a espinha deterministica e o sistema."),
                hash_estado=g("--hash", "a1b2c3d4e5f6"),
                entrada=int(g("--entrada", "309")),
                sync=g("--sync", "PASS · REGRAS=deadbeef · MEMÓRIAS=cafef00d · HEAD=abc1234"),
                free="--free" in a,
                seed=int(g("--seed")) if "--seed" in a else None)
    print(out)
