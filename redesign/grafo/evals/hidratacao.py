#!/usr/bin/env python3
"""
Eval de FIDELIDADE DE HIDRATACAO (P4-05).

O grafo hidrata (`estado_para_eco.sh`) e responde. O eval verifica que:
  1. O `hidratar` pega o topo REAL do canon (a ultima entrada de MEMORIAS).
  2. O envelope da resposta (com `--com-envelope`) cita ESSE numero, nao um inventado.
  3. `verificar_cabecalho.py --max-entrada <real>` NAO acusa (numero <= real, plausivel).
  4. Negativo: se a gente MENTE o fato para o modelo (entrada=999), o
     `verificar_cabecalho.py --max-entrada <real>` PEGA (n > real -> "implausivel").

FALHA do eval = o grafo cita um numero != topo real, OU o check nao pega o numero mentido.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
AGATA = os.path.expanduser("~/agata")


def _topo_real():
    r = subprocess.run(["bash", "scripts/estado_para_eco.sh"], cwd=AGATA,
                       capture_output=True, text=True)
    for ln in r.stdout.splitlines():
        if ln.startswith("TOPO-MEMÓRIAS:"):
            m = re.search(r"\((\d+)\)", ln)
            return int(m.group(1)) if m else None
    return None


def _lint(texto, max_entrada):
    r = subprocess.run(["python3", "scripts/verificar_cabecalho.py", "--max-entrada", str(max_entrada)],
                       cwd=AGATA, input=texto, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def run():
    real = _topo_real()
    if real is None:
        print(json.dumps({"erro": "nao consegui ler o topo real"}))
        return 1

    import envelope

    # 1+2+3 -- geracao FIEL: o fato passado e' o real
    fiel = envelope.gerar("Qual e a ultima entrada de MEMORIAS e por que o estado esta coerente?",
                          hash_estado="abc123abc123", entrada=real,
                          sync="PASS · x", seed=42)
    m = re.search(r"última entrada[^(]{0,20}\((\d+)\)|MEMÓRIAS\s*\((\d+)\)|\((\d+)\)\s*DIÁRIO", fiel)
    citado = int(next(g for g in m.groups() if g)) if m else None
    rc_fiel, msg_fiel = _lint(fiel, real)
    fiel_ok = (citado == real and rc_fiel == 0)

    # 4 -- geracao MENTIDA: o fato passado e' 999 (maior que o real)
    mentida = envelope.gerar("Qual e a ultima entrada de MEMORIAS?",
                             hash_estado="abc123abc123", entrada=999,
                             sync="PASS · x", seed=42)
    rc_ment, msg_ment = _lint(mentida, real)
    # o check TEM que pegar (rc != 0 e a mensagem fala de implausivel/maior)
    pegou_mentira = (rc_ment != 0 and ("implausível" in msg_ment or "maior que" in msg_ment))

    out = {
        "topo_real": real,
        "fiel": {"citado": citado, "lint_exit": rc_fiel, "ok": fiel_ok},
        "mentida_999": {"lint_exit": rc_ment, "pegou": pegou_mentira,
                        "msg": msg_ment.splitlines()[0] if msg_ment else ""},
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    allpass = fiel_ok and pegou_mentira
    print("\nVEREDITO hidratacao.py:", "PASS -- cita o topo real; a mentira e' pega"
          if allpass else "FALHA")
    return 0 if allpass else 1


if __name__ == "__main__":
    sys.exit(run())
