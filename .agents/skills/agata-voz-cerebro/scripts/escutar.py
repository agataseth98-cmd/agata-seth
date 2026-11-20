#!/usr/bin/env python3
"""Ouve UMA fala do Humano (microfone -> VAD -> transcrição local) e imprime o texto. Para o Claude ser o cérebro."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "redesign" / "sentidos"))
from captura import Captura
import vad as vadmod
import canal_voz

limite = float(sys.argv[1]) if len(sys.argv) > 1 else 90
c = Captura(); c.abrir()
v = vadmod.Vad(); t0 = time.time(); seg = None
try:
    for q in c.quadros():
        seg = v.alimentar(q)
        if seg or time.time() - t0 > limite:
            break
finally:
    c.fechar()
print(canal_voz.transcrever_pcm(seg["pcm"]) if seg else "[silêncio: nada ouvido]")
