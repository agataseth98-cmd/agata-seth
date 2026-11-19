#!/usr/bin/env python3
"""Captura do canal de voz: pw-record sob demanda, quadros de 30 ms por stdout, nada em disco.

O microfone só fica aberto entre `abrir()` e `fechar()`. `descartar_pendente(ms)` esvazia o que já está no cano
(meia-duplex: o que o microfone ouviu enquanto o sistema falava) e mais `ms` de áudio novo.
"""
from __future__ import annotations

import os
import select
import shutil
import subprocess
import time

from vad import BYTES_QUADRO, QUADRO_MS


class CapturaErro(RuntimeError):
    pass


class Captura:
    def __init__(self, comando: list[str] | None = None):
        # --raw: sem ele, pw-record no stdout escreve contêiner Sun AU (big-endian) e o PCM vira chiado (medido 18/11: RMS 19 mil vs 644 real).
        self.comando = comando or ["pw-record", "--raw", "--rate", "16000", "--channels", "1", "--format", "s16", "-"]
        self.proc: subprocess.Popen | None = None
        self._buf = b""

    def abrir(self) -> None:
        if not shutil.which(self.comando[0]):
            raise CapturaErro(f"{self.comando[0]} ausente")
        # bufsize=0: stdout cru, para misturar select e os.read sem o buffer escondendo dados do select
        self.proc = subprocess.Popen(self.comando, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     stdin=subprocess.DEVNULL, bufsize=0)
        self._buf = b""

    def vivo(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def _ler(self, espera: float) -> bytes | None:
        """Até uma espera de `espera` s; b"" = o processo fechou o cano; None = nada ainda (a leitura nunca bloqueia)."""
        fd = self.proc.stdout.fileno()  # type: ignore[union-attr]
        if not select.select([fd], [], [], espera)[0]:
            return None
        return os.read(fd, 65536)

    def quadros(self):
        """Gera quadros de 960 bytes; termina quando o processo morre (o chamador trata como erro de captura).
        A leitura é por select com 0,5 s de espera: um sinal ou `fechar()` nunca ficam presos num read bloqueado."""
        assert self.proc and self.proc.stdout
        while self.proc is not None:
            while len(self._buf) >= BYTES_QUADRO:
                q, self._buf = self._buf[:BYTES_QUADRO], self._buf[BYTES_QUADRO:]
                yield q
            dado = self._ler(0.5)
            if dado is None:
                if not self.vivo():
                    return
                continue
            if not dado:
                return
            self._buf += dado

    def descartar_pendente(self, ms: int) -> None:
        if not self.vivo():
            return
        self._buf = b""
        while self._ler(0):                 # esvazia o que já está no cano
            pass
        fim = time.monotonic() + ms / 1000
        while time.monotonic() < fim:
            if self._ler(max(0.0, min(0.1, fim - time.monotonic()))) == b"":
                break

    def fechar(self) -> None:
        p, self.proc = self.proc, None
        if p is None:
            return
        p.terminate()
        try:
            p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait(timeout=3)
        if p.stdout:
            p.stdout.close()
