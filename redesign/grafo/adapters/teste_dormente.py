#!/usr/bin/env python3
"""P4-06 -- confirma que o adapter dsh esta DORMENTE e a interface bate com grafo.py."""
import inspect
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import dsh  # noqa: E402
import grafo  # noqa: E402

falhas = []

# 1. ENABLED e' False
if dsh.ENABLED is not False:
    falhas.append(f"dsh.ENABLED = {dsh.ENABLED!r}, esperado False")

# 2. levanta se chamado
for fn, args in [(dsh.run, ("x", "/r", "t")), (dsh.resume, ("t", "/r"))]:
    try:
        fn(*args)
        falhas.append(f"dsh.{fn.__name__} NAO levantou")
    except NotImplementedError:
        pass

# 3. interface identica a de grafo.py (mesmos nomes de parametro)
for nome in ("run", "resume"):
    p_dsh = list(inspect.signature(getattr(dsh, nome)).parameters)
    p_grafo = list(inspect.signature(getattr(grafo, nome)).parameters)
    if p_dsh != p_grafo:
        falhas.append(f"assinatura {nome}: dsh {p_dsh} != grafo {p_grafo}")

# 4. dsh nao foi importado por grafo.py
if "dsh" in sys.modules and "dsh" in inspect.getsource(grafo):
    falhas.append("grafo.py referencia 'dsh' no codigo")

if falhas:
    print("FALHA:")
    for f in falhas:
        print("  -", f)
    sys.exit(1)
print("PASS -- dsh ENABLED=False, levanta se chamado, interface == grafo.py, nao importado pelo loop")
sys.exit(0)
