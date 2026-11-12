#!/usr/bin/env python3
"""Gancho de fim de turno: confere a última resposta com a auditoria e só AVISA. Nunca bloqueia.

Pacote mecânico, 12/11/2026 (decisão do Humano: a verificação vale para todos os modelos, por mecanismo).
Liga-se a: Claude Code (`Stop`, em .claude/settings.json), Codex (`[[hooks.Stop]]`, exemplo em
config/cli/codex/config.toml.exemplo) e Gemini CLI (`AfterAgent`, exemplo em
config/cli/gemini/settings.json.exemplo). Doc pública:
  - Claude Code: https://code.claude.com/docs/en/hooks  (Stop: last_assistant_message; systemMessage com exit 0)
  - Codex: https://learn.chatgpt.com/docs/hooks  (Stop: last_assistant_message; systemMessage com exit 0)
  - Gemini CLI: https://geminicli.com/docs/hooks/reference/  (AfterAgent: prompt_response; systemMessage com exit 0)

Entrada: JSON na stdin. O texto da resposta vem de `last_assistant_message` (Claude, Codex) ou
`prompt_response` (Gemini). Sem texto, sai calado. O id da sessão (`session_id`) liga a conferência
do `t=` ao contador de scripts/turno.py.

Saída: exit 0 sempre. Havendo achado, imprime {"systemMessage": "..."} (aviso ao Humano, sem
decision/continue). Falha de leitura, de subprocesso ou timeout: não imprime nada e sai com 0.

Uso: python3 scripts/auditoria_stop.py < entrada.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
AUDITORIA = RAIZ / "redesign" / "router" / "auditoria_turno.py"
PRAZO = 20  # segundos; o gancho não pode travar o fim do turno


def _texto_da_resposta(dados: dict) -> str:
    for chave in ("last_assistant_message", "prompt_response", "last-assistant-message"):
        valor = dados.get(chave)
        if isinstance(valor, str) and valor.strip():
            return valor
    return ""


def avisos_da_resposta(texto: str, sessao: str) -> list[str]:
    """Linhas de achado da auditoria (`--verificar`). Vazia se não há achado ou se a auditoria falhou."""
    cmd = [sys.executable, str(AUDITORIA), "--verificar"]
    if sessao:
        cmd += ["--sessao", sessao]
    try:
        r = subprocess.run(cmd, input=texto, capture_output=True, text=True, timeout=PRAZO, cwd=str(RAIZ))
    except (OSError, subprocess.SubprocessError) as e:
        print(f"auditoria_stop: auditoria não rodou ({type(e).__name__})", file=sys.stderr)
        return []
    return [ln for ln in r.stdout.splitlines() if ln.startswith("- ")]


def main(entrada: str) -> int:
    try:
        dados = json.loads(entrada) if entrada.strip() else {}
    except ValueError:
        return 0  # entrada inválida: o gancho não age, não derruba o fim do turno
    if not isinstance(dados, dict):
        return 0
    texto = _texto_da_resposta(dados)
    if not texto:
        return 0
    sessao = dados.get("session_id") if isinstance(dados.get("session_id"), str) else ""
    achados = avisos_da_resposta(texto, sessao)
    if achados:
        aviso = "Auditoria do turno (aviso, não bloqueia):\n" + "\n".join(achados)
        print(json.dumps({"systemMessage": aviso}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.stdin.read()))
