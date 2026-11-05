"""Revisão de suporte (lote 5, pacote D3): a afirmação está sustentada pelo trecho citado?

Dois níveis:
1) mecânico (sempre): citação que não existe entre as fontes; número da resposta que não aparece em nenhuma fonte;
2) revisor (proporcional ao risco, Regra 8): um ou três passes de um modelo de OUTRA família, que vê só o par
   (afirmação, trecho), nunca a conversa. Divergência entre passes vira `inconclusivo`.
"""
from __future__ import annotations

import re
from collections import Counter

RE_COLCHETE = re.compile(r"\[([a-z0-9]+)\]")
RE_PAREN = re.compile(r"(?<![\w(])\((\d{1,4})\)")
RE_NUM = re.compile(r"(?<![\w.])\d{2,}(?:[.,]\d+)?(?![\w])")


def mecanico(resposta: str, fontes: list[dict]) -> dict:
    ids = {str(f["id"]) for f in fontes}
    textos = " ".join(str(f.get("texto") or "") for f in fontes)
    citados = RE_COLCHETE.findall(resposta or "") + RE_PAREN.findall(resposta or "")
    inexistentes = sorted({c for c in citados if c not in ids})
    sem_suporte = sorted({n for n in RE_NUM.findall(resposta or "") if n not in textos})
    estado = "inconsistente" if inexistentes else ("revisar" if sem_suporte else "ok")
    return {"estado": estado, "citacoes_inexistentes": inexistentes, "numeros_sem_suporte": sem_suporte}


def plano(*, risco: str = "leitura", remoto: bool = False, citacao: bool = False, nao_verificavel: bool = False) -> dict:
    """Quantos revisores: decisão não verificável = 3 passes locais; efeito, remoto ou citação = 1; leitura = 0."""
    if nao_verificavel:
        return {"revisores": 3, "motivo": "decisão não verificável (Regra 8): três passes"}
    if risco == "efeito" or remoto or citacao:
        return {"revisores": 1, "motivo": "efeito, rota remota ou citação: um revisor"}
    return {"revisores": 0, "motivo": "leitura sem citação: só o mecânico"}


def revisar(afirmacao: str, trecho: str, revisor, passes: int = 1) -> dict:
    """`revisor(prompt) -> texto`. O prompt traz só o par (afirmação, trecho). Resposta esperada: SUSTENTA ou NAO_SUSTENTA."""
    prompt = ("Responda somente SUSTENTA ou NAO_SUSTENTA: o trecho sustenta a afirmação?\n"
              f"AFIRMAÇÃO: {afirmacao}\nTRECHO: {trecho}")
    votos = []
    for _ in range(passes):
        t = (revisor(prompt) or "").upper()
        votos.append("sustenta" if "NAO_SUSTENTA" not in t and "SUSTENTA" in t else "nao_sustenta" if "NAO_SUSTENTA" in t else "indeterminado")
    if not votos:
        return {"veredito": "inconclusivo", "votos": []}
    cont = Counter(votos)
    if len(cont) == 1 and passes >= 1 and votos[0] != "indeterminado":
        return {"veredito": votos[0], "votos": votos}
    return {"veredito": "inconclusivo", "votos": votos}
