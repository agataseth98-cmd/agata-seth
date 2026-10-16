#!/usr/bin/env python3
"""Conta mecanicamente as mensagens do Humano no transcrito da sessão do Claude Code (base 'contador mecânico' do t= da Regra 1).
Heurística: registros `user` que não são tool_result nem avisos de sistema/tarefa. Uso: python3 contar_turnos.py [transcrito.jsonl]"""
import glob, json, os, sys
f = sys.argv[1] if len(sys.argv) > 1 else max(glob.glob(os.path.expanduser("~/.claude/projects/-home-orusoua-agata/*.jsonl")), key=os.path.getmtime)
n = 0
for l in open(f, encoding="utf-8"):
    try:
        d = json.loads(l)
    except ValueError:
        continue
    if d.get("type") != "user":
        continue
    c = d.get("message", {}).get("content")
    if isinstance(c, list) and any(isinstance(x, dict) and x.get("type") == "tool_result" for x in c):
        continue
    txt = c if isinstance(c, str) else "".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text") if isinstance(c, list) else ""
    s = txt.strip()
    if s and not s.startswith(("<system-reminder>", "<task-notification>")) and "[SYSTEM NOTIFICATION" not in s[:200]:
        n += 1
print(n)
