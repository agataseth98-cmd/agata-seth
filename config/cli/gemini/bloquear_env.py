#!/usr/bin/env python3
"""Gancho BeforeTool do Gemini CLI (exemplo, pacote mecânico, 12/11/2026): nega a ferramenta
cuja entrada aponta para ~/.config/agata/.env.

Doc: https://geminicli.com/docs/hooks/ (bloqueio: exit 2, o stderr vira o motivo) e
https://geminicli.com/docs/hooks/reference/ (BeforeTool recebe tool_name e tool_input).
Não medido: a chave exata do caminho dentro de tool_input na versão instalada. Por isso a
checagem é por substring na entrada inteira ("config/agata/.env"), e não por um nome de campo.
Limite: entrada que não é JSON deixa passar (exit 0); não é um controle de sandbox.
"""
import json
import sys

MARCA = "config/agata/.env"


def main(entrada: str) -> int:
    try:
        dados = json.loads(entrada) if entrada.strip() else {}
    except ValueError:
        return 0
    alvo = dados.get("tool_input", dados) if isinstance(dados, dict) else dados
    if MARCA in json.dumps(alvo, ensure_ascii=False):
        print("Negado: ~/.config/agata/.env é segredo e não é lido (permissões do projeto).",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.stdin.read()))
