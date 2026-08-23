#!/usr/bin/env python3
"""Harness A1, nível 0 — hook pre_api_request do Hermes.

Le o payload JSON do pre_api_request (stdin, protocolo documentado em
agent/shell_hooks.py do hermes-agent) e compara o `system_prompt`
REALMENTE enviado contra o conteúdo REAL de `.hermes.md` no disco
agora -- não contra um valor lembrado ou presumido. Detecta o mesmo
tipo de bug já visto neste projeto (MEMÓRIAS 103-105, 220): o
carregador cortando o arquivo de contexto antes de injetar, em
silêncio.

Nível 0: heurística de contenção + maior prefixo contido (busca
binária, não presume que o conteúdo comece na posição 0 do prompt),
não diff completo.
Observacional só -- nunca bloqueia a chamada (pre_api_request não
suporta decisão de bloqueio no protocolo do Hermes).

Saída: nada em stdout (silent no-op, protocolo do Hermes). Efeito:
uma linha JSONL por chamada em TRACE_PATH.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

TRACE_PATH = Path.home() / "agata" / "memoria" / "harness_a1_trace.jsonl"
CONTEXT_FILE = Path.home() / "agata" / ".hermes.md"


def _hash8(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:8]


def _maior_prefixo_contido(contexto: str, system_prompt: str) -> int:
    """Maior L tal que contexto[:L] aparece (em qualquer posição, não só
    no início) dentro de system_prompt -- busca binária sobre L, já que
    "contido" é monotônico: se um prefixo de tamanho L está contido, todo
    prefixo menor também está. Não presume que o wrapper do Hermes
    injeta o arquivo bem no início do system prompt (achado no teste 2,
    ver PROPOSTA/testes: um wrapper de texto antes do conteúdo derrubava
    a checagem ingênua de prefixo posição-a-posição para 0)."""
    lo, hi = 0, len(contexto)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if contexto[:mid] in system_prompt:
            lo = mid
        else:
            hi = mid - 1
    return lo


def avaliar(system_prompt: str, context_content: str) -> dict:
    context_chars = len(context_content)
    hash_esperado = _hash8(context_content)

    if context_content and context_content in system_prompt:
        return {
            "context_file_chars": context_chars,
            "hash_esperado": hash_esperado,
            "hash_enviado": hash_esperado,
            "enviado_chars": context_chars,
            "truncado": False,
        }

    prefixo = _maior_prefixo_contido(context_content, system_prompt)
    return {
        "context_file_chars": context_chars,
        "hash_esperado": hash_esperado,
        "hash_enviado": _hash8(context_content[:prefixo]) if prefixo else "-",
        "enviado_chars": prefixo,
        "truncado": True,
    }


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        _trace({"erro": f"JSON inválido no stdin: {exc}"})
        return 0  # fail open -- evento observacional, nunca derruba a chamada real

    extra = payload.get("extra") or {}
    system_prompt = extra.get("system_prompt")
    if not isinstance(system_prompt, str):
        _trace({"erro": "extra.system_prompt ausente ou não é string neste payload"})
        return 0

    try:
        context_content = CONTEXT_FILE.read_text(encoding="utf-8")
    except OSError as exc:
        _trace({"erro": f"não consegui ler {CONTEXT_FILE}: {exc}"})
        return 0

    resultado = avaliar(system_prompt, context_content)
    resultado.update(
        {
            "session_id": payload.get("session_id", ""),
            "api_call_count": extra.get("api_call_count"),
            "model": extra.get("model"),
        }
    )
    _trace(resultado)
    return 0


def _trace(campos: dict) -> None:
    linha = {"ts": time.time(), "harness": "A1", "nivel": 0}
    linha.update(campos)
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(linha, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    sys.exit(main())
