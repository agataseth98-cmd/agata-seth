#!/usr/bin/env python3
"""Mede o ouvido (fala → texto) com frases sintéticas da voz do sistema: WER e tempo por motor.

As 20 frases fixas de `frases_ouvido.txt` são faladas pelo piper `pt_BR-agata-last`
(`scripts/agata_falar.py`, sem tocar) e misturadas a ruído rosa leve (ffmpeg). Cada motor transcreve
cada clipe: `lfm3` (Ollama) e `whisper` (iGPU, só se já estiver no ar; senão sai "não medido"). O WER é
calculado sem acento, sem pontuação e em minúsculas. Grava no registro comum da avaliação
(`redesign/avaliacao/registro.py`, medidor `ouvido`), com a frase de referência e a transcrição.

Limite: a voz é sintética, não a do Humano; o ruído é leve. Mede o caso fácil. Só roda a pedido
(painel ou terminal): liga o piper só durante a geração, como o `agata_falar.py` já faz.
Uso: medir_ouvido.py [--motores lfm3,whisper]
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
for _p in (AQUI, REPO / "redesign" / "avaliacao", REPO / "redesign" / "nova_versao", REPO / "scripts"):
    sys.path.insert(0, str(_p))
import ouvido  # noqa: E402
import registro  # noqa: E402

FRASES = AQUI / "frases_ouvido.txt"


def norm(t: str) -> list[str]:
    t = unicodedata.normalize("NFKD", (t or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", t).split()


def wer(ref: str, hip: str) -> float:
    r, h = norm(ref), norm(hip)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (r[i - 1] != h[j - 1]))
    return d[len(h)] / max(len(r), 1)


def gerar(frases: list[str], pasta: Path, falar=None) -> list[tuple[str, Path, Path]]:
    if falar is None:
        import agata_falar
        falar = agata_falar.falar
    out = []
    for i, f in enumerate(frases, 1):
        d = pasta / f"f{i:02d}"
        d.mkdir()
        if falar(f, tocar=False, salvar=d) != 0:
            raise RuntimeError("a voz do sistema não gerou o áudio")
        bruto = sorted(d.glob("fala-*.wav"))[0]
        limpo, ruido = pasta / f"limpo{i:02d}.wav", pasta / f"ruido{i:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(bruto), "-ar", "16000", "-ac", "1", str(limpo)], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(limpo), "-filter_complex",
                        "anoisesrc=d=60:c=pink:a=0.03:r=16000[n];[0][n]amix=inputs=2:duration=first:normalize=0",
                        "-ar", "16000", "-ac", "1", str(ruido)], check=True)
        out.append((f, limpo, ruido))
    return out


def medir(motores=("lfm3", "whisper"), *, falar=None, transcrever=None) -> dict:
    frases = [x for x in FRASES.read_text(encoding="utf-8").splitlines() if x.strip()]
    transcrever = transcrever or ouvido.transcrever
    run = registro.abrir("ouvido", "dev", registro.hash_conjunto([{"task_id": f"f{i:02d}", "frase": f}
                                                                 for i, f in enumerate(frases, 1)]),
                         extra={"motores": list(motores), "voz": "piper pt_BR-agata-last (sintética)"})
    resumo = {}
    with tempfile.TemporaryDirectory(prefix="medir-ouvido-") as t:
        clipes = gerar(frases, Path(t), falar)
        for m in motores:
            for cond in ("limpo", "ruido"):
                ws, ts, nao = [], [], 0
                for i, (ref, limpo, ruido) in enumerate(clipes, 1):
                    r = transcrever(limpo if cond == "limpo" else ruido, motor=m)
                    if not r["text"]:
                        nao += 1
                        registro.linha(run, task_id=f"f{i:02d}", condition=f"{m}|{cond}", model_id=m, outcome="nao_rodou",
                                       failure_stage=r["falha_etapa"], erro=r["erro"])
                        continue
                    w = wer(ref, r["text"])
                    ws.append(w); ts.append(r["proc_s"])
                    registro.linha(run, task_id=f"f{i:02d}", condition=f"{m}|{cond}", model_id=r["motor"],
                                   outcome="passou" if w == 0 else "falhou", latency_ms=round(r["proc_s"] * 1000),
                                   referencia=ref, transcricao=r["text"], wer=round(w, 4))
                resumo[f"{m}|{cond}"] = {"motor": m, "condicao": cond, "n": len(ws), "nao_rodou": nao,
                                         "wer": round(statistics.mean(ws), 4) if ws else None,
                                         "perfeitas": sum(w == 0 for w in ws) if ws else None,
                                         "tempo_mediano_s": round(statistics.median(ts), 3) if ts else None}
    return registro.fechar(run, {"por_motor": resumo, "nota": "voz sintética e ruído leve: mede o caso fácil"})


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--motores", default="lfm3,whisper")
    a = ap.parse_args()
    r = medir(tuple(a.motores.split(",")))
    print(json.dumps({"run_id": r["run_id"], **r["resumo"]}, ensure_ascii=False, indent=1))
