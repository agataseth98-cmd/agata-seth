#!/usr/bin/env python3
"""Hook PreInvocation do Gemini CLI para injetar o cabeçalho de turno automaticamente.

Lê o payload JSON do stdin (campo conversationId como sessão, lastUserInput como prompt,
modelName como modelo) e devolve um JSON com injectSteps contendo uma systemMessage
com o cabeçalho do turno.

Equivalente ao gancho UserPromptSubmit do Claude Code (scripts/turno.py hook), mas no
formato do Gemini CLI / Antigravity (hooks.json, evento PreInvocation).

Uso: colocar em .agents/hooks.json (ou ~/.gemini/antigravity-cli/hooks.json):
  {"agata-turno": {"PreInvocation": [{"type": "command",
   "command": "python3 scripts/turno_gemini_hook.py", "timeout": 10}]}}
"""
from __future__ import annotations

import json
import sys

import turno


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    sessao = payload.get("conversationId", "")
    if not isinstance(sessao, str) or not sessao:
        print(json.dumps({}))
        return 0

    prompt = payload.get("lastUserInput", "")
    modelo_raw = payload.get("modelName", "")
    modelo = modelo_raw if isinstance(modelo_raw, str) and modelo_raw.strip() else "gemini"

    if turno.e_notificacao(prompt):
        t = turno.atual_da_sessao(sessao)
        if t is None:
            print(json.dumps({}))
            return 0
        cab = turno.linha(modelo, t, turno.BASE_NOTIFICACAO)
        msg = (f"Cabeçalho deste turno: {cab}\n"
               "Esta mensagem é notificação do sistema ou de agente, não do Humano: o t não avança. "
               "Copie a linha como abertura da resposta.\n"
               f"Sessão para turno.py e auditoria_turno.py --verificar --sessao: {sessao}")
    else:
        try:
            t, base, cab = turno._avancar(sessao, modelo)
        except Exception:
            print(json.dumps({}))
            return 0
        if t == 1:
            marca = " Contador reiniciado (arquivo corrompido): t=1." if "reiniciado" in base else ""
            msg = ("Cabeçalho deste turno: 1ª resposta desta sessão. Abra com o bloco de prontidão "
                   "(PROTOCOLOS.md, \"Carregar e formatos\"), sem linha t=." + marca)
        else:
            msg = (f"Cabeçalho deste turno: {cab}\n"
                   "Copie a linha como abertura da resposta (REGRAS.md, Regra 1); não recalcule o t. "
                   f"Subagente: t=<n>.sub com `python3 scripts/turno.py sub --sessao {sessao}`.")
        msg += f"\nSessão para turno.py e auditoria_turno.py --verificar --sessao: {sessao}"

    print(json.dumps({
        "injectSteps": [
            {"systemMessage": {"systemMessage": msg}}
        ]
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
