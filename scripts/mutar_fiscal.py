#!/usr/bin/env python3
"""K1 -- mutation testing do fiscal de PR. Aplica uma mutação por vez numa CÓPIA de scripts/ e roda testar_p8_verificar_pr.py
sobre a cópia. Mutante MORTO = a suíte falhou (bom). SOBREVIVENTE = a suíte passou mesmo com o fiscal quebrado (lacuna de teste
OU mutante equivalente: M02/M03 são equivalentes porque a assinatura SSH cobre o hash real; M11 é encoberto pelo teste de
ancestralidade enquanto o fiscal passar --ancora-ancestral-de). Só /tmp. Uso: python3 -I scripts/mutar_fiscal.py <repo> <saida.json>"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

repo, saida = sys.argv[1], sys.argv[2]
SH, PY = "scripts/p8_verificar_pr.sh", "scripts/p8_integral.py"
M = [
 ("M01 par já aplicado na base deixa de ser ignorado", SH, 'git cat-file -e "$base:$caminho" 2>/dev/null && continue', ':'),
 ("M02 hash do .diff não conferido", SH, 'grep -qx "diff-sha256: $dsha" "$tmp/$nome.aprovado" ||', 'true ||'),
 ("M03 assinatura ausente aceita", SH, '[ -s "$tmp/$nome.sig" ] ||', 'true ||'),
 ("M04 âncora sem checagem de ancestralidade", SH, 'args+=(--ancora-ancestral-de "$head")', ':'),
 ("M05 sem --incluir-tocados", SH, '--restrict "$tmp/protegidos.z" --incluir-tocados)"', '--restrict "$tmp/protegidos.z")"'),
 ("M06 par em aplicadas/ pode ser symlink/executável", SH, 'e["mode"] != "100644" or e["type"] != "blob"', 'False'),
 ("M07 protegido sem par sempre OK", SH, 'if [ "$n_sem_par" -eq 0 ]; then', 'if true; then'),
 ("M08 arquivo de âncora isento sem verificar o bloco", SH, 'if python3 -I "$tmp/p8_integral.py" --repo . --base "$base" --actual-tree "$(git rev-parse "$head^{tree}")" \\\n             --so-ancora "$f" --ancora-ancestral-de "$head" >/dev/null 2>&1; then continue; fi ;;', 'continue ;;'),
 ("M09 corpo fora do bloco de âncora não comparado", PY, 'if a is None or b is None or a[0] != b[0]:', 'if a is None or b is None:'),
 ("M10 slug do bloco não comparado", PY, 'if b[1]["slug"] != a[1]["slug"]:', 'if False:'),
 ("M11 SHA da âncora não precisa ser commit", PY, 'if _git(repo, "cat-file", "-e", b[1]["sha"] + "^{commit}", check=False).returncode:', 'if False:'),
 ("M12 SHA da âncora não precisa ser ancestral", PY, 'if ancestral_de and _git(repo, "merge-base", "--is-ancestor", b[1]["sha"], ancestral_de, check=False).returncode:', 'if False:'),
 ("M13 modo/tipo do arquivo de âncora ignorado", PY, 'if c in ancoras_b and quer[c][:2] == tem[c][:2] and quer[c][1] == "blob":', 'if c in ancoras_b and quer[c][1] == "blob":'),
 ("M14 so_ancora aceita modo diferente", PY, 'if a is None or b is None or a[:2] != b[:2] or a[1] != "blob":', 'if a is None or b is None:'),
 ("M15 sem raiz de confiança não falha", SH, 'git show "$base:propostas/.allowed_signers" > "$tmp/signers" 2>/dev/null && [ -s "$tmp/signers" ] \\\n  || falha', 'true || falha'),
]
# Erro de infraestrutura ou baseline quebrada não prova que a suíte matou mutante.
baseline = subprocess.run([sys.executable, "-I", os.path.join(repo, "scripts/testar_p8_verificar_pr.py")],
                          capture_output=True, text=True, timeout=900)
conclusao = re.search(r"(?m)^(\d+)/\1 casos conforme o esperado$", baseline.stdout)
if baseline.returncode or not conclusao:
    sys.exit("BASELINE INVALIDA: suite não concluiu verde; nenhuma mutação classificada")
baseline_conclusao = conclusao.group(0)
res = []
for nome, arq, velho, novo in M:
    td = tempfile.mkdtemp(prefix="mut-")
    try:
        shutil.copytree(os.path.join(repo, "scripts"), os.path.join(td, "scripts"))
        p = os.path.join(td, arq)
        t = open(p, encoding="utf-8").read()
        n = t.count(velho)
        if n != 1:
            res.append({"mutante": nome, "resultado": "NAO-APLICADO", "ocorrencias": n}); print(nome, "NAO-APLICADO", n, flush=True); continue
        open(p, "w", encoding="utf-8").write(t.replace(velho, novo))
        t0 = time.time()
        r = subprocess.run(["python3", "-I", os.path.join(td, "scripts/testar_p8_verificar_pr.py")], capture_output=True, text=True, timeout=900)
        falhou = [l for l in r.stdout.splitlines() if l.startswith("FALHOU") or l.startswith("FALHA")]
        v = "MORTO" if r.returncode != 0 and falhou else ("SOBREVIVEU" if r.returncode == 0 and baseline_conclusao in r.stdout else "ERRO-INFRA")
        res.append({"mutante": nome, "resultado": v, "casos_que_pegaram": [l[7:70] for l in falhou][:3], "s": round(time.time() - t0)})
        print(nome, v, "|", (falhou[0][7:60] if falhou else ""), flush=True)
    finally:
        shutil.rmtree(td, ignore_errors=True)
json.dump(res, open(saida, "w"), ensure_ascii=False, indent=1)
mortos = sum(r["resultado"] == "MORTO" for r in res); aplic = sum(r["resultado"] != "NAO-APLICADO" for r in res)
print(f"\nmutantes aplicados: {aplic} · mortos: {mortos} · sobreviventes: {aplic - mortos}")

if any(r["resultado"] in ("ERRO-INFRA", "NAO-APLICADO") for r in res):
    sys.exit(2)
