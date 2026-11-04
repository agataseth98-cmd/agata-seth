#!/usr/bin/env python3
"""Metacognição: o DEPOIS do turno — estado de saída da resposta.

Origem: `proposta-tecnica-metacognicao-llm.md` §5. Os estados possíveis são
apto · parcial · inconclusivo · bloqueado · aguardando_humano. "Apto" não cria
autorização para efeito protegido.

Não cria verificador novo: o que pode ser decidido por Máquina já está em
`redesign/router/auditoria_turno.verificar_resposta_atual` (Jev sem consulta, P-n,
entrada e caminho inexistentes, citação inventada, ação sem chamada...). Este módulo só
junta esses achados com a classificação do antes (`previo.py`) e devolve o estado.

Uso: `python3 redesign/metacognicao/posterior.py < resposta.txt`  (sai 1 se não for apto)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[0] / "router"))

RE_LACUNA = re.compile(r"\b(n[aã]o medid[oa]|lacuna|n[aã]o encontrad[oa] nesta busca|n[aã]o verificad[oa]|parcial)\b", re.I)
ESTADOS = ("apto", "parcial", "inconclusivo", "bloqueado", "aguardando_humano")


def classificar(texto: str, previo: dict | None = None, *, msgs: list | None = None, rota_remota: bool = False,
                achados: list | None = None) -> dict:
    previo = previo or {}
    if achados is None:
        import auditoria_turno  # noqa: E402
        achados = auditoria_turno.verificar_resposta_atual(texto, msgs or [])
    motivos = []
    if previo.get("privado") and rota_remota:
        estado = "bloqueado"; motivos.append("dado pessoal em rota remota")
    elif achados:
        estado = "inconclusivo"; motivos += [str(a) for a in achados[:5]]
    elif previo.get("risco") == "efeito":
        estado = "aguardando_humano"; motivos.append("efeito pedido: só o Humano autoriza")
    elif RE_LACUNA.search(texto):
        estado = "parcial"; motivos.append("a resposta declara lacuna")
    else:
        estado = "apto"
    return {"estado": estado, "motivos": motivos, "achados_mecanicos": len(achados),
            "nota": "apto não autoriza efeito protegido" if estado == "apto" else None}


if __name__ == "__main__":
    if sys.stdin.isatty():
        print(__doc__)
        sys.exit(2)
    r = classificar(sys.stdin.read())
    print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.exit(0 if r["estado"] == "apto" else 1)
