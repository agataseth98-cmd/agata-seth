#!/usr/bin/env python3
"""Conta o t= da Regra 1 num transcrito, de forma mecânica. Dois modos:
  --modo humano (PADRÃO): mensagens do Humano (registros `user` que não são tool_result nem aviso de sistema/tarefa).
     É o t= que o Humano acompanha. Sem transcrito informado, usa o JSONL mais recente de ~/.claude/projects/-home-orusoua-agata
     (limite conhecido: com duas sessões abertas pode pegar a outra; informe o transcrito para ser exato).
  --modo respostas: respostas textuais do MODELO (Claude JSONL e Codex response_item), dedup por message.id; exige
     transcrito explícito (argumento ou AGATA_TRANSCRITO); nunca escolhe sessão por mtime.
Uso: contar_turnos.py [--modo humano|respostas] [--proximo] [TRANSCRITO]. --proximo soma 1 (a resposta que será escrita).
"""
import argparse
import glob
import json
import os
from pathlib import Path


def contar_humano(linhas):
    n = 0
    for linha in linhas:
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if not isinstance(d, dict) or d.get("type") != "user":
            continue
        c = (d.get("message") or {}).get("content")
        if isinstance(c, list) and any(isinstance(x, dict) and x.get("type") == "tool_result" for x in c):
            continue
        txt = c if isinstance(c, str) else "".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text") if isinstance(c, list) else ""
        s = txt.strip()
        if s and not s.startswith(("<system-reminder>", "<task-notification>")) and "[SYSTEM NOTIFICATION" not in s[:200]:
            n += 1
    return n


def contar(linhas):
    """Respostas textuais do modelo (modo respostas). JSON truncado é erro explícito."""
    vistos = set()
    total = 0
    for n, linha in enumerate(linhas, 1):
        if not linha.strip():
            continue
        try:
            d = json.loads(linha)
        except ValueError as e:
            raise ValueError(f'linha {n}: JSON incompleto ou inválido') from e
        if not isinstance(d, dict):
            raise ValueError(f'linha {n}: registro não é objeto')
        if d.get('type') == 'assistant':
            m = d.get('message') or {}
            if not isinstance(m, dict):
                raise ValueError(f'linha {n}: mensagem inválida')
        elif d.get('type') == 'response_item':
            m = d.get('payload') or {}
            if not isinstance(m, dict):
                raise ValueError(f'linha {n}: payload inválido')
            if m.get('type') != 'message' or m.get('role') != 'assistant':
                continue
        else:
            continue
        c = m.get('content')
        texto = c if isinstance(c, str) else ''.join(x.get('text', '') for x in c
                if isinstance(x, dict) and x.get('type') in ('text', 'output_text') and isinstance(x.get('text'), str)) if isinstance(c, list) else ''
        if not texto.strip():
            continue
        # Fragmentos com o mesmo message.id não são respostas novas.
        ident = m.get('id')
        if isinstance(ident, str) and ident:
            if ident in vistos:
                continue
            vistos.add(ident)
        total += 1
    return total


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('transcrito', nargs='?', default=os.environ.get('AGATA_TRANSCRITO'))
    ap.add_argument('--modo', choices=('humano', 'respostas'), default='humano')
    ap.add_argument('--proximo', action='store_true')
    a = ap.parse_args(argv)
    fonte = a.transcrito
    if not fonte and a.modo == 'humano':
        achados = glob.glob(os.path.expanduser('~/.claude/projects/-home-orusoua-agata/*.jsonl'))
        fonte = max(achados, key=os.path.getmtime) if achados else None
    if not fonte:
        ap.error('transcrito desta sessão não informado; use contagem no contexto')
    try:
        with Path(fonte).open(encoding='utf-8') as f:
            n = contar_humano(f) if a.modo == 'humano' else contar(f)
    except (OSError, ValueError) as e:
        ap.exit(2, f'contador: {e}\n')
    print(n + int(a.proximo))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
