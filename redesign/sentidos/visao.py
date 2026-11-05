"""Visão do Agata (projeto 5 sentidos, lote 5, D4): descrever uma imagem com o lfm3-vl, local.

Só entrada: a imagem vai em base64 no campo `images` do Ollama. Sem serviço novo, sem gravação da imagem.
A chamada é injetada (testes sem rede). Medição: `medir_visao` roda só se PIL existir (fora da CI).
"""
from __future__ import annotations

import base64
import json
import os
import urllib.request

OLLAMA = os.environ.get("AGATA_OLLAMA", "http://127.0.0.1:11434")
MODELO = os.environ.get("AGATA_VISAO_MODELO", "lfm3-vl:2b")


def _chamada_padrao(pergunta: str, imagem: bytes) -> str:
    corpo = {"model": MODELO, "stream": False, "think": False,
             "messages": [{"role": "user", "content": pergunta,
                           "images": [base64.b64encode(imagem).decode()]}]}
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return (json.loads(r.read()).get("message") or {}).get("content", "").strip()


def descrever(imagem: bytes, pergunta: str = "Descreva a imagem em português, em uma frase.", *, chamar=None) -> dict:
    if not isinstance(imagem, (bytes, bytearray)) or not imagem:
        raise ValueError("imagem vazia")
    if len(imagem) > 10 * 1024 * 1024:
        raise ValueError("imagem acima de 10 MB")
    try:
        texto = (chamar or _chamada_padrao)(pergunta, bytes(imagem))
        return {"ok": True, "texto": texto, "modelo": MODELO}
    except Exception as e:  # noqa: BLE001 — falha vira estado, não exceção
        return {"ok": False, "falha": e.__class__.__name__, "modelo": MODELO}
