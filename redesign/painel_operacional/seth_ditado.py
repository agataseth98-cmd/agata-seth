"""Ditado da Seth no painel (11/11/2026): o navegador grava o microfone, o painel repassa o áudio ao ouvido local.

O navegador manda o áudio só para o próprio painel (mesma origem). Daí o módulo o repassa ao servidor_ouvido em
127.0.0.1:20137 (redesign/sentidos/servidor_ouvido.py, POST /v1/audio/transcriptions, campo `file`). Nada sai da
Máquina. O texto volta para o campo, e o Humano revisa antes de enviar: este módulo nunca fala com a Seth.
O ouvido não é ligado aqui (decisão de 29/10: sob demanda). Se estiver parado, a resposta diz isso.
"""
from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
import uuid

LIMITE_AUDIO_BYTES = 2 * 1024 * 1024  # cerca de 60 s de opus; o cliente para a gravação antes disso
DURACAO_MAX_S = 60  # limite de gravação no navegador (o servidor não mede duração)
OUVIDO = os.environ.get("AGATA_OUVIDO_URL", "http://127.0.0.1:20137")
TEMPO_S = 120
TEXTO_MAX = 4000  # mesmo teto do campo de mensagem da Seth
EXTENSOES = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "m4a", "audio/wav": "wav", "audio/x-wav": "wav"}
_TRANSCRICAO = threading.Lock()


class ErroDitado(Exception):
    def __init__(self, status: int, motivo: str):
        super().__init__(motivo)
        self.status, self.motivo = status, motivo


def transcrever(corpo: bytes, tipo: str, *, url: str | None = None) -> dict:
    """Áudio cru do navegador -> {texto}. Erros viram ErroDitado com a mensagem para o Humano."""
    if not corpo:
        raise ErroDitado(400, "nada foi gravado: o áudio está vazio")
    if len(corpo) > LIMITE_AUDIO_BYTES:
        raise ErroDitado(413, "gravação grande demais: o limite é 2 MB, cerca de 60 segundos. Grave menos.")
    base = (tipo or "").split(";")[0].strip().lower()
    if not base.startswith("audio/"):
        raise ErroDitado(415, "o navegador mandou um formato que não é áudio")
    if not _TRANSCRICAO.acquire(blocking=False):
        raise ErroDitado(429, "já estou transcrevendo outro áudio; aguarde e tente de novo")
    try:
        texto = _chamar_ouvido(corpo, base, url or OUVIDO)
    finally:
        _TRANSCRICAO.release()
    texto = texto.strip()
    if not texto:
        raise ErroDitado(422, "não ouvi fala nesse áudio: tente de novo, mais perto do microfone")
    return {"schema_version": 1, "texto": texto[:TEXTO_MAX]}


def _multipart(corpo: bytes, tipo: str) -> tuple[bytes, str]:
    fronteira = uuid.uuid4().hex
    ext = EXTENSOES.get(tipo, "bin")
    cabeca = (f"--{fronteira}\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\npt\r\n"
              f"--{fronteira}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"fala.{ext}\"\r\n"
              f"Content-Type: {tipo}\r\n\r\n").encode("utf-8")
    return cabeca + corpo + f"\r\n--{fronteira}--\r\n".encode("utf-8"), fronteira


def _chamar_ouvido(corpo: bytes, tipo: str, base_url: str) -> str:
    dados, fronteira = _multipart(corpo, tipo)
    pedido = urllib.request.Request(base_url.rstrip("/") + "/v1/audio/transcriptions", data=dados, method="POST",
                                    headers={"Content-Type": f"multipart/form-data; boundary={fronteira}"})
    try:
        with urllib.request.urlopen(pedido, timeout=TEMPO_S) as resposta:
            obj = json.loads(resposta.read(TEXTO_MAX * 8))
    except urllib.error.HTTPError as erro:
        if erro.code == 503:
            raise ErroDitado(503, "o ouvido local não tem motor no ar: nada foi transcrito. Ligue o servidor do ouvido e tente de novo.")
        if erro.code == 413:
            raise ErroDitado(413, "gravação grande demais para o ouvido local. Grave menos.")
        raise ErroDitado(422, "não consegui processar esse áudio: tente gravar de novo")
    except (urllib.error.URLError, OSError):
        raise ErroDitado(503, "o ouvido local (127.0.0.1:20137) não respondeu: nada foi transcrito. Ligue o servidor do ouvido e tente de novo.")
    except ValueError:
        raise ErroDitado(502, "o ouvido local respondeu fora do formato esperado")
    texto = obj.get("text") if isinstance(obj, dict) else None
    if not isinstance(texto, str):
        raise ErroDitado(502, "o ouvido local respondeu fora do formato esperado")
    return texto
