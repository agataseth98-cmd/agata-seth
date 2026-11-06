#!/usr/bin/env python3
"""Ficha de rotas (P7): valida config/rotas-ficha.json contra as decisões D2 e D3.

D2: dado pessoal só entra em rota local. Segredo nunca entra em rota nenhuma.
D3: cota gratuita compartilhada com a Seth é permitida sem teto; o aviso aparece na ficha.
Não chama nenhum provedor. Só lê o arquivo.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CAMPOS = ("id", "provedor", "modelo", "categoria", "classes_permitidas", "treina_com_prompts",
          "cota", "compartilhada_com_seth", "cota_medida", "conferida_em", "fonte")
CATEGORIAS = ("local", "gratuito", "assinatura", "pago")
CLASSES = ("publico", "sintetico", "pessoal", "segredo")
TREINO = ("nao", "sim", "nao_conferido", "nao_aplica")
RAIZ = Path(__file__).resolve().parents[2]
PADRAO = RAIZ / "config" / "rotas-ficha.json"


def verificar(ficha: dict) -> tuple[list[str], list[str]]:
    """Devolve (erros, avisos). Erro bloqueia; aviso é só informação."""
    erros, avisos = [], []
    for r in ficha.get("rotas", []):
        rid = r.get("id", "?")
        faltam = [c for c in CAMPOS if c not in r]
        if faltam:
            erros.append(f"{rid}: campos ausentes {faltam}")
            continue
        if r["categoria"] not in CATEGORIAS:
            erros.append(f"{rid}: categoria inválida {r['categoria']!r}")
        if r["treina_com_prompts"] not in TREINO:
            erros.append(f"{rid}: treina_com_prompts inválido {r['treina_com_prompts']!r}")
        classes = r["classes_permitidas"]
        if any(c not in CLASSES for c in classes):
            erros.append(f"{rid}: classe desconhecida em {classes}")
        if "segredo" in classes:
            erros.append(f"{rid}: segredo nunca pode sair para rota nenhuma (regra de segurança)")
        if "pessoal" in classes and r["categoria"] != "local":
            erros.append(f"{rid}: dado pessoal só em rota local (D2)")
        if r["compartilhada_com_seth"] and r["categoria"] != "local":
            avisos.append(f"{rid}: cota compartilhada com a Seth, sem teto (D3)")
        if not r["cota_medida"]:
            avisos.append(f"{rid}: cota não medida")
        if r["treina_com_prompts"] == "nao_conferido":
            avisos.append(f"{rid}: política de treino não conferida")
    return erros, avisos


def main(argv: list[str]) -> int:
    caminho = Path(argv[0]) if argv else PADRAO
    ficha = json.loads(caminho.read_text(encoding="utf-8"))
    erros, avisos = verificar(ficha)
    for a in avisos:
        print("AVISO:", a)
    for e in erros:
        print("ERRO:", e)
    print("FICHA OK" if not erros else f"FICHA COM {len(erros)} ERRO(S)")
    return 1 if erros else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
