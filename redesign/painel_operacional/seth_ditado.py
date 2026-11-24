"""Ditado da Seth no painel (11/11/2026): o navegador grava o microfone, o painel repassa o áudio ao ouvido local.

O navegador manda o áudio só para o próprio painel (mesma origem). Daí o módulo o repassa ao servidor_ouvido em
127.0.0.1:20137 (redesign/sentidos/servidor_ouvido.py, POST /v1/audio/transcriptions, campo `file`). Nada sai da
Máquina. O texto volta para o campo, e o Humano revisa antes de enviar: este módulo nunca fala com a Seth.
O ouvido e a voz continuam desligados no boot (decisão de 29/10: sob demanda). Se o ouvido estiver parado quando o
Humano dita (conexão recusada ou sem motor), o módulo liga `ouvido-agata.service` e `piper-tts.service` com
`systemctl --user start` (sem enable, então o boot não muda), espera até 20 s a porta 20137 abrir e repete a
transcrição uma vez. Só se falhar de novo a resposta é o 503 com o motivo. Só liga serviço quando o ouvido é local.
"""
from __future__ import annotations

import errno
import json
import os
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

LIMITE_AUDIO_BYTES = 2 * 1024 * 1024  # cerca de 60 s de opus; o cliente para a gravação antes disso
DURACAO_MAX_S = 60  # limite de gravação no navegador (o servidor não mede duração)
OUVIDO = os.environ.get("AGATA_OUVIDO_URL", "http://127.0.0.1:20137")
TEMPO_S = 120
TEXTO_MAX = 4000  # mesmo teto do campo de mensagem da Seth
EXTENSOES = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "m4a", "audio/wav": "wav", "audio/x-wav": "wav"}
SYSTEMCTL = "/usr/bin/systemctl"  # mesmo caminho que o painel usa nas outras chamadas
UNIDADES_OUVIDO = ("ouvido-agata.service", "piper-tts.service")
ESPERA_OUVIDO_S = 20  # tempo máximo para a porta do ouvido abrir depois do start
INTERVALO_OUVIDO_S = 0.5
HOSTS_LOCAIS = ("127.0.0.1", "localhost")
_TRANSCRICAO = threading.Lock()
_PARTIDA = threading.Event()  # verdadeiro enquanto o ouvido está sendo ligado e a porta é esperada
MSG_SUBINDO = "ouvido subindo, tente em alguns segundos"


class ErroDitado(Exception):
    def __init__(self, status: int, motivo: str, partida: bool = False):
        super().__init__(motivo)
        self.status, self.motivo = status, motivo
        self.partida = partida  # True só para recusa de conexão e 503 do motor: os dois casos em que a partida se justifica


def transcrever(corpo: bytes, tipo: str, *, url: str | None = None) -> dict:
    """Áudio cru do navegador -> {texto}. Erros viram ErroDitado com a mensagem para o Humano."""
    if not corpo:
        raise ErroDitado(400, "nada foi gravado: o áudio está vazio")
    if len(corpo) > LIMITE_AUDIO_BYTES:
        raise ErroDitado(413, "gravação grande demais: o limite é 2 MB, cerca de 60 segundos. Grave menos.")
    base = (tipo or "").split(";")[0].strip().lower()
    if not base.startswith("audio/"):
        raise ErroDitado(415, "o navegador mandou um formato que não é áudio")
    if _PARTIDA.is_set():
        raise ErroDitado(503, MSG_SUBINDO)
    if not _TRANSCRICAO.acquire(blocking=False):
        if _PARTIDA.is_set():  # a partida começou entre a checagem e a trava
            raise ErroDitado(503, MSG_SUBINDO)
        raise ErroDitado(429, "já estou transcrevendo outro áudio; aguarde e tente de novo")
    try:
        texto = _transcrever_com_partida(corpo, base, url or OUVIDO)
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
        erro.close()  # solta a resposta já lida: o erro pode ficar guardado enquanto a partida roda
        if erro.code == 503:  # 503 explícito do motor: o ouvido está no ar sem motor
            raise ErroDitado(503, "o ouvido local não tem motor no ar: nada foi transcrito. Ligue o servidor do ouvido e tente de novo.", partida=True)
        if erro.code == 413:
            raise ErroDitado(413, "gravação grande demais para o ouvido local. Grave menos.")
        raise ErroDitado(422, "não consegui processar esse áudio: tente gravar de novo")
    except (urllib.error.URLError, OSError) as erro:
        if _demorou(erro):  # leitura ou conexão que estourou o prazo: erro direto, sem reenviar
            raise ErroDitado(504, "o ouvido local demorou demais para responder: nada foi transcrito. Tente de novo.")
        if _recusou_conexao(erro):  # ouvido parado: a partida liga e repete (só aí)
            raise ErroDitado(503, "o ouvido local (127.0.0.1:20137) não respondeu: nada foi transcrito. Ligue o servidor do ouvido e tente de novo.", partida=True)
        raise ErroDitado(503, "o ouvido local (127.0.0.1:20137) não respondeu: nada foi transcrito. Ligue o servidor do ouvido e tente de novo.")
    except ValueError:
        raise ErroDitado(502, "o ouvido local respondeu fora do formato esperado")
    texto = obj.get("text") if isinstance(obj, dict) else None
    if not isinstance(texto, str):
        raise ErroDitado(502, "o ouvido local respondeu fora do formato esperado")
    return texto


def _recusou_conexao(erro: BaseException) -> bool:
    """Recusa de conexão (ECONNREFUSED ou ConnectionRefusedError), direta ou dentro do URLError."""
    motivo = erro.reason if isinstance(erro, urllib.error.URLError) else erro
    return isinstance(motivo, ConnectionRefusedError) or getattr(motivo, "errno", None) == errno.ECONNREFUSED


def _demorou(erro: BaseException) -> bool:
    """Prazo de conexão ou de leitura estourado."""
    motivo = erro.reason if isinstance(erro, urllib.error.URLError) else erro
    return isinstance(motivo, (TimeoutError, socket.timeout))


def _transcrever_com_partida(corpo: bytes, tipo: str, url: str) -> str:
    """Ouvido parado (recusou a conexão ou tem motor desligado) e local: liga, espera a porta e repete uma vez.
    Timeout, formato ruim ou outro erro: sai direto, sem partida e sem reenvio."""
    try:
        return _chamar_ouvido(corpo, tipo, url)
    except ErroDitado as erro:
        if not erro.partida or not _local(url):
            raise
    _PARTIDA.set()
    try:
        _ligar_ouvido()
        _esperar_porta(url)
    finally:
        _PARTIDA.clear()
    return _chamar_ouvido(corpo, tipo, url)


def _local(url: str) -> bool:
    """Só liga serviço local para o ouvido desta Máquina; URL de outro host não dispara systemctl."""
    return (urllib.parse.urlsplit(url).hostname or "") in HOSTS_LOCAIS


def _ligar_ouvido() -> None:
    """`start` das unidades do ouvido e da voz (sob demanda, 29/10). Falha do comando não para o fluxo:
    quem decide se o ouvido subiu é a espera pela porta."""
    try:
        subprocess.run([SYSTEMCTL, "--user", "start", *UNIDADES_OUVIDO], capture_output=True, timeout=15, check=False)
    except (OSError, subprocess.SubprocessError):
        pass


def _esperar_porta(url: str) -> bool:
    """Espera até ESPERA_OUVIDO_S a porta do ouvido aceitar conexão. True se abriu; False se o prazo acabou."""
    partes = urllib.parse.urlsplit(url)
    endereco = (partes.hostname or "127.0.0.1", partes.port or 80)
    limite = time.monotonic() + ESPERA_OUVIDO_S
    while True:
        try:
            with socket.create_connection(endereco, timeout=1):
                return True
        except OSError:
            pass
        if time.monotonic() >= limite:
            return False
        time.sleep(INTERVALO_OUVIDO_S)
