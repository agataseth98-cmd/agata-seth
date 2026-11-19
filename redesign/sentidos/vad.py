#!/usr/bin/env python3
"""VAD por energia (canal de voz, fase 1): Python puro (array/math; numpy não está no venv do CI), sem modelo, sem rede.

Quadros de 30 ms, PCM s16le mono 16 kHz. Piso de ruído adaptativo (desce rápido, sobe devagar fora da fala), limiar
= max(RMS_MIN, piso * RAZAO). Histerese: abre após ABRE_QUADROS seguidos de fala e fecha após HANGOVER_MS de
silêncio. Teto de trecho: MAX_TRECHO_MS fecha à força. Trecho menor que MIN_TRECHO_MS é descartado.
Não usa zero-crossing na fase 1 (menor mecanismo; entra se a medição com voz real pedir).
"""
from __future__ import annotations

import array
import math
import sys

QUADRO_MS = 30
TAXA = 16000
BYTES_QUADRO = TAXA * QUADRO_MS // 1000 * 2   # 960
RMS_MIN = 300.0
RAZAO = 3.0
MARGEM_MAX = 3000.0      # com piso alto, o limiar é piso + margem (piso*3 passaria do teto de 16 bits)
CALIBRA_QUADROS = 10     # 300 ms
ABRE_QUADROS = 3
HANGOVER_MS = 2000      # Humano 18/11 19:51: "espere dois segundos e responda"
PRE_ROLL_QUADROS = 5
MAX_TRECHO_MS = 15000
MIN_TRECHO_MS = 300


def rms(quadro: bytes) -> float:
    a = array.array("h")
    a.frombytes(quadro)
    if sys.byteorder == "big":
        a.byteswap()
    return math.sqrt(sum(x * x for x in a) / len(a)) if a else 0.0


class Vad:
    def __init__(self):
        self.piso: float | None = None
        self._calib: list[float] = []
        self.n = 0                     # quadros vistos
        self.pre: list[bytes] = []
        self.dentro = False
        self.seguidos = 0
        self.silencio = 0
        self.buf: list[bytes] = []
        self.ini = 0
        self.ultimo_fala = 0

    def _fala(self, r: float) -> bool:
        # Calibra o piso com a mediana dos primeiros CALIBRA_QUADROS (um quadro silencioso isolado não derruba o piso),
        # e o piso acompanha devagar o ruído SEMPRE (inclusive dentro da fala): ruído alto e constante (medido em
        # 18/11: RMS ~19 mil no microfone da Máquina) não pode prender o trecho aberto até o teto.
        if self.n <= CALIBRA_QUADROS:
            self._calib.append(r)
            self.piso = sorted(self._calib)[len(self._calib) // 2]
        limiar = max(RMS_MIN, min(self.piso * RAZAO, self.piso + MARGEM_MAX))
        fala = r > limiar
        if r < self.piso:
            self.piso += 0.2 * (r - self.piso)
        else:
            self.piso += (0.0005 if fala else 0.02) * (r - self.piso)
        return fala

    def alimentar(self, quadro: bytes) -> dict | None:
        """Devolve {pcm, ini_ms, fim_ms, motivo} quando um trecho fecha; senão None."""
        if len(quadro) != BYTES_QUADRO:
            return None
        i = self.n
        self.n += 1
        fala = self._fala(rms(quadro))
        if not self.dentro:
            self.pre.append(quadro)
            self.pre = self.pre[-(PRE_ROLL_QUADROS + ABRE_QUADROS):]
            self.seguidos = self.seguidos + 1 if fala else 0
            if self.seguidos >= ABRE_QUADROS:
                self.dentro = True
                self.buf = list(self.pre)
                self.ini = i - ABRE_QUADROS + 1
                self.ultimo_fala = i
                self.silencio = 0
            return None
        self.buf.append(quadro)
        if fala:
            self.ultimo_fala = i
            self.silencio = 0
        else:
            self.silencio += 1
        dur = (i - self.ini + 1) * QUADRO_MS
        if self.silencio * QUADRO_MS >= HANGOVER_MS:
            return self._fechar("silencio")
        if dur >= MAX_TRECHO_MS:
            return self._fechar("teto")
        return None

    def _fechar(self, motivo: str) -> dict | None:
        fim = self.ultimo_fala + 1
        ini_ms, fim_ms = self.ini * QUADRO_MS, fim * QUADRO_MS
        pcm = b"".join(self.buf)
        self.dentro, self.buf, self.pre, self.seguidos, self.silencio = False, [], [], 0, 0
        if fim_ms - ini_ms < MIN_TRECHO_MS:
            return None
        return {"pcm": pcm, "ini_ms": ini_ms, "fim_ms": fim_ms, "motivo": motivo}
