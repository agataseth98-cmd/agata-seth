#!/usr/bin/env python3
"""Metacognição: o ANTES do turno, determinístico e em sombra.

Origem: Experimento GPT, conclusões (026)–(029), (013), (014) e
`proposta-tecnica-metacognicao-llm.md` §3. Não é uma nova persona e não chama modelo:
classifica o pedido para que a estratégia (memória, skill, modelo, pesquisa externa)
seja escolhida com os fatos à mão. A classificação é sujeita a erro (regex), por isso
só fica em sombra até a avaliação (lote 3) medir a utilidade.

Reaproveita `redesign/router/sombra_capacidade.requisitos` (tokens, ferramentas,
código, JSON, dado pessoal pela régua do `sanitizar.py`) e acrescenta:
- atualidade: pedido volátil (hoje, preço, estado da arte...) pede consulta local E
  externa em paralelo, se permitido (Alexandria §6), nunca espera serial;
- risco: pedido com efeito (apagar, enviar, publicar, instalar...) passa pelo portão
  humano; "apto" depois não autoriza o efeito;
- "problema" polissêmico (014): marca os sentidos a distinguir;
- limite de interação combinado (013): "três perguntas", "no máximo 2" — conta o que
  já foi usado no histórico, para o modelo não perder a conta.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[0] / "router"))

RE_VOLATIL = re.compile(r"\b(hoje|agora|atual(mente|izad[oa])?|[uú]ltim[oa]s?|recente|estado da arte|not[ií]cia|"
                        r"pre[cç]o|cota[cç][aã]o|esta semana|este m[eê]s|lan[cç]amento|vers[aã]o nova|20\d\d)\b", re.I)
RE_EFEITO = re.compile(r"\b(apag|delet|remov|exclu|envi[ae]|mand[ae]|public|commit|push|merge|instal|desinstal|"
                       r"reinici|sudo|pag[ae]r?|compr[ae]|assin[ae]|aplic[ae]|grav[ae])\w*", re.I)
RE_PROBLEMA = re.compile(r"\bproblemas?\b", re.I)
SENTIDOS_PROBLEMA = ("obstáculo", "pergunta", "erro", "risco", "discrepância", "tarefa", "estado pendente", "oportunidade")
NUM = {"uma": 1, "um": 1, "duas": 2, "dois": 2, "três": 3, "tres": 3, "quatro": 4, "cinco": 5}
RE_LIMITE = re.compile(r"\b(?:no m[aá]ximo\s+)?(\d+|uma|um|duas|dois|tr[eê]s|quatro|cinco)\s+perguntas?\b", re.I)
RE_SISTEMA = re.compile(r"\b(mem[oó]ria|entrada|decis[aã]o|regra|proposta|canon|protocolo|falha|hist[oó]ric|"
                        r"o que (foi|ficou) decidido|quando)\b", re.I)


def _texto(c) -> str:
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text")
    return ""


def limite_interacao(msgs: list) -> dict | None:
    """Procura um limite de perguntas declarado e conta as perguntas do Humano depois dele."""
    users = [_texto(m.get("content")) for m in msgs if isinstance(m, dict) and m.get("role") == "user"]
    for i, t in enumerate(users):
        m = RE_LIMITE.search(t)
        if m:
            v = m.group(1).lower()
            total = int(v) if v.isdigit() else NUM.get(v, 0)
            usadas = sum("?" in u for u in users[i + 1:])
            return {"declarado": total, "usadas": usadas, "restantes": max(total - usadas, 0)}
    return None


def classificar(payload: dict, varrer_pessoal=None) -> dict:
    import sombra_capacidade  # noqa: E402  (mesmo diretório do gateway)
    msgs = payload.get("messages") or []
    ultima = next((_texto(m.get("content")) for m in reversed(msgs)
                   if isinstance(m, dict) and m.get("role") == "user"), "")
    req = sombra_capacidade.requisitos(payload, varrer_pessoal)
    volatil = bool(RE_VOLATIL.search(ultima))
    efeito = sorted({m.group(0).lower() for m in RE_EFEITO.finditer(ultima)})[:5]
    estrategia = []
    if RE_SISTEMA.search(ultima):
        estrategia.append("consultar Alexandria (local) antes de afirmar")
    if volatil:
        estrategia.append("local e externa em paralelo, se permitido; egresso minimizado")
    if req["privado"]:
        estrategia.append("dado pessoal: só rota local, nada sai")
    if efeito:
        estrategia.append("efeito pedido: preparar e passar pelo portão do Humano")
    out = {"tipo": req["tipo"], "tokens_est": req["tokens_est"], "ferramentas": req["ferramentas"],
           "privado": req["privado"], "atualidade": "volatil" if volatil else "estavel",
           "risco": "efeito" if efeito else "leitura", "sinais_efeito": efeito,
           "problema_ambiguo": list(SENTIDOS_PROBLEMA) if RE_PROBLEMA.search(ultima) else None,
           "limite_interacao": limite_interacao(msgs), "estrategia": estrategia or ["resposta direta"]}
    return out


if __name__ == "__main__":
    import json
    if len(sys.argv) == 2:
        print(json.dumps(classificar({"messages": [{"role": "user", "content": sys.argv[1]}]}, lambda t: []),
                         ensure_ascii=False, indent=1))
        sys.exit(0)
    print(__doc__)
    sys.exit(2)
