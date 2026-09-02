#!/usr/bin/env python3
"""Semeia ~/.agata-backup-staging/p12-cobertura.json a partir do repo restic.

Roda SO com o HD montado (le `restic snapshots --json`). Cruza cada recurso do
models/manifest.json (blob_sha256 / ir_sha256_xmlbin) com os snapshots que tem
esse hash como tag, e grava, por recurso coberto:

    { "<name>": { "sha256": "<hash>", "verificado_em": "<ISO-8601 UTC>",
                  "snapshot": "<id-curto>" } }

O P-12 do perimetro.sh (redesign/propostas/p12-backup-verificavel.diff) le esse
arquivo quando o HD NAO esta montado, para reportar PARCIAL com a data de
cobertura mais velha em vez de travar um commit.

Uso:
    export RESTIC_REPOSITORY=/run/media/orusoua/AgataBkup01/restic-agata-local
    export RESTIC_PASSWORD_FILE=$HOME/.config/agata/restic.pass
    python3 redesign/fase7-hd/semear_cache_p12.py [--dry-run]
"""
import datetime
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(REPO_ROOT, "models", "manifest.json")
CACHE = os.path.expanduser("~/.agata-backup-staging/p12-cobertura.json")


def restic_snapshots():
    env = os.environ.copy()
    if "RESTIC_REPOSITORY" not in env:
        sys.exit("RESTIC_REPOSITORY nao setado -- o HD esta montado?")
    try:
        out = subprocess.run(
            ["restic", "snapshots", "--json"],
            check=True, capture_output=True, text=True, env=env, timeout=120,
        ).stdout
    except FileNotFoundError:
        sys.exit("restic nao encontrado no PATH.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"restic snapshots falhou: {e.stderr.strip()}")
    return json.loads(out or "[]")


def main():
    dry = "--dry-run" in sys.argv[1:]
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    snaps = restic_snapshots()
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

    cache = {}
    for x in manifest["modelos"]:
        name = x["name"]
        h = x.get("blob_sha256") or x.get("ir_sha256_xmlbin") or ""
        if not h:
            continue
        hit = None
        for s in snaps:
            tags = s.get("tags") or []
            if h in tags and (name in tags or not name):
                # mais recente vence
                if hit is None or s.get("time", "") > hit.get("time", ""):
                    hit = s
        if hit:
            cache[name] = {
                "sha256": h,
                "verificado_em": now,
                "snapshot": (hit.get("short_id") or hit.get("id", ""))[:8],
            }

    print(json.dumps(cache, indent=2, ensure_ascii=False))
    if dry:
        print("\n(--dry-run: nada gravado)")
        return
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    tmp = CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CACHE)
    print(f"\ngravado: {CACHE} ({len(cache)} recurso(s) coberto(s))")
    faltam = [
        x["name"] for x in manifest["modelos"]
        if (x.get("blob_sha256") or x.get("ir_sha256_xmlbin")) and x["name"] not in cache
    ]
    if faltam:
        print("SEM cobertura (nenhum snapshot com o hash atual): " + ", ".join(faltam))


if __name__ == "__main__":
    main()
