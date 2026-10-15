#!/usr/bin/env python3
"""Pedidos sintéticos pt-BR para treinar o Laya no roteador da Seth (MEMÓRIAS (718)).

Cada lote pede a um modelo de nuvem 25 mensagens de UMA classe (o rótulo é a classe do
lote), num estilo sorteado. Pelo sanitizador (`:20127`, `X-Agata-Token`), como o resto do
sistema. Os dados de `dados/` foram gerados assim em 15/10/2026 (treino: `ministral-14b` e
`nemotron-3-super`; teste B: `gemini-3.5-flash-lite`; teste A escrito à mão). Só stdlib.

Uso: python3 redesign/laya/gerar_sinteticos.py <modelo> <lotes_por_grupo> <saida.jsonl> [semente] [grupos]
     grupos: rapido,livre,pesado,codigo (padrão) e/ou livre-curto,rapido-puro,pesado-curto
"""
from __future__ import annotations

import json
import random
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import token_interno  # noqa: E402

PROXY = "http://127.0.0.1:20127/v1/chat/completions"
CLASSES = {
    "rapido": "cumprimento, agradecimento, confirmação ou pergunta trivial de uma linha (ex.: 'oi', 'valeu', 'ok, pode seguir', 'que horas são?')",
    "livre": "conversa normal, explicação do dia a dia ou ajuda com texto, SEM raciocínio difícil (ex.: explicar um conceito simples, resumir, revisar um e-mail, dar uma opinião rápida)",
    "pesado": "raciocínio difícil, prova, análise técnica profunda ou planejamento complexo (ex.: comparar arquiteturas com trade-offs, auditar um desenho de sistema, demonstrar algo, plano de migração em etapas) -- SEM pedir para escrever código",
    "codigo": "escrever, corrigir ou explicar código de programação, SQL ou script (ex.: 'esse sed não funciona', 'escreve uma função python que...', 'por que esse SELECT demora')",
}
# v2 (718): reforço onde a v1 errava -- ela tinha aprendido "pedido curto = rápido"
FOCO = {
    "livre-curto": ("livre", "pergunta CURTA, de uma linha, que pede um fato, uma explicação, uma tradução, uma sugestão ou uma opinião (ex.: 'qual a capital da Austrália?', 'me sugere um filme', 'o que é latência?', 'traduz bom dia pro inglês'). NÃO é cumprimento, agradecimento nem confirmação"),
    "rapido-puro": ("rapido", "SÓ cumprimento, agradecimento, despedida, confirmação ou reação curta, sem pedir nada (ex.: 'oi', 'valeu', 'ok', 'beleza, pode seguir', 'assinado', 'show'). NUNCA uma pergunta que peça informação"),
    "pesado-curto": ("pesado", "pedido CURTO (uma ou duas frases) mas que exige raciocínio difícil, análise profunda, prova ou planejamento complexo (ex.: 'audite o desenho de segurança desse fluxo', 'compare essas duas arquiteturas com trade-offs') -- sem pedir código"),
}
ESTILOS = ["informal, com gírias e erros de digitação", "formal e educado", "curto e seco", "longo e detalhado",
           "misturando português e termos técnicos em inglês", "como quem já está no meio de uma conversa",
           "com contexto de Linux, servidores e modelos de IA", "do dia a dia, fora de tecnologia"]
_OP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def pedir(modelo: str, grupo: str, estilo: str, semente: int) -> list:
    rotulo, desc = (grupo, CLASSES[grupo]) if grupo in CLASSES else FOCO[grupo]
    prompt = (f"Gere 25 mensagens DIFERENTES que um usuário brasileiro mandaria a uma assistente de IA chamada Seth. "
              f"Todas da categoria: {desc}. Estilo: {estilo}. Varie tamanho, assunto e forma; "
              f"nada de numeração nem explicação. Responda SÓ com um array JSON de strings. Semente: {semente}.")
    corpo = {"model": modelo, "messages": [{"role": "user", "content": prompt}], "temperature": 1.0, "max_tokens": 4000}
    req = urllib.request.Request(PROXY, json.dumps(corpo).encode(),
                                 {"Content-Type": "application/json", "X-Agata-Token": token_interno.ler()})
    erro = None
    for _ in range(3):
        try:
            with _OP.open(req, timeout=180) as r:
                d = json.load(r)
            m = re.search(r"\[.*\]", d["choices"][0]["message"]["content"], re.S)
            itens = [s.strip() for s in json.loads(m.group(0)) if isinstance(s, str) and s.strip()]
            return [(rotulo, s, d.get("model", modelo)) for s in itens]
        except Exception as e:  # noqa: BLE001
            erro = e
            time.sleep(3)
    print(f"falhou {grupo}/{estilo}: {erro}", file=sys.stderr)
    return []


def main() -> None:
    modelo, lotes, saida = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    random.seed(int(sys.argv[4]) if len(sys.argv) > 4 else 0)
    grupos = sys.argv[5].split(",") if len(sys.argv) > 5 else list(CLASSES)
    tarefas = [(g, random.choice(ESTILOS), random.randint(1, 10**6)) for g in grupos for _ in range(lotes)]
    vistos, n = set(), 0
    with ThreadPoolExecutor(4) as ex, open(saida, "a", encoding="utf-8") as f:
        for res in ex.map(lambda t: pedir(modelo, *t), tarefas):
            for rotulo, s, real in res:
                if s.lower() in vistos:
                    continue
                vistos.add(s.lower())
                n += 1
                f.write(json.dumps({"state": s, "gold": rotulo, "gerador": real}, ensure_ascii=False) + "\n")
    print(f"{modelo}: {n} pedidos em {saida}")


if __name__ == "__main__":
    main()
