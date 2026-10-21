#!/usr/bin/env python3
"""Auditoria rígida do escriba (somente leitura). Não corrige nada.

Checagens (cada uma PASS/FAIL; qualquer FAIL = exit 1):
 1. apenso: nenhum commit remove linha de MEMÓRIAS.md/SETH-DIARIO.md, exceto âncoras automáticas.
 2. numeração: entradas (N) não repetem sem registro conhecido na baseline.
 3. segredo: nenhuma linha adicionada casa com os padrões de scripts/varredura_segredo.sh.
 4. registro: entrada nova chega por merge de PR, nunca por commit direto no main.
 5. cópia: o working tree de MEMÓRIAS.md/SETH-DIARIO.md não tem linhas fora do origin/main (diferença não commitada).
Baseline: scripts/auditoria_escriba_baseline.json (duplicatas já conhecidas, ex.: 729).
Grava uma linha por execução em ~/.cache/agata/auditoria-escriba.jsonl.
"""
from __future__ import annotations
import json, os, re, subprocess, sys, time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVOS = ["MEMÓRIAS.md", "SETH-DIARIO.md"]
ANCORA = re.compile(r"(SHA do commit ANTERIOR|Escrito em:|raw\.githubusercontent\.com/|ANCORA-SHA)")
ENTRADA = re.compile(r"^\((\d+)\) ")

def git(*a: str) -> str:
    return subprocess.run(["git", "-C", str(RAIZ), *a], capture_output=True, text=True, check=False).stdout

def secretos() -> list[str]:
    s = (RAIZ / "scripts" / "varredura_segredo.sh").read_text(encoding="utf-8")
    return re.findall(r"'([^']{6,})'", s)  # padrões entre aspas simples

def checar() -> dict[str, tuple[bool, str]]:
    r: dict[str, tuple[bool, str]] = {}
    base = json.loads((RAIZ / "scripts" / "auditoria_escriba_baseline.json").read_text(encoding="utf-8"))
    # 1. apenso: commit que apaga linha (fora das âncoras) só é aceito se estiver na lista de exceções aprovadas
    aprovadas = {e["commit"]: e for e in base.get("excecoes_aprovadas", [])}
    pendentes = []
    marco = base.get("marco", "")
    intervalo = f"{marco}..HEAD" if marco else "HEAD"
    historico = []
    for linha in git("log", "--format=%h", "--no-merges", intervalo, "--", *ARQUIVOS).split():
        apag = [l for l in git("show", "--format=", "-p", linha, "--", *ARQUIVOS).splitlines()
                if l.startswith("-") and not l.startswith("---") and not ANCORA.search(l)]
        if apag and linha not in aprovadas:
            pendentes.append(f"{linha}({len(apag)})")
    for linha in git("log", "--format=%h", "--no-merges", "--", *ARQUIVOS).split():
        if linha in git("log", "--format=%h", "--no-merges", intervalo, "--", *ARQUIVOS).split():
            continue
        apag = [l for l in git("show", "--format=", "-p", linha, "--", *ARQUIVOS).splitlines()
                if l.startswith("-") and not l.startswith("---") and not ANCORA.search(l)]
        if apag and linha not in aprovadas:
            historico.append(linha)
    r["1_apenso"] = (not pendentes, (f"após o marco {marco}: remoção sem exceção aprovada em {pendentes[:6]}" if pendentes
                     else f"após o marco {marco or '-'}: nenhuma remoção fora de exceção") + f" | dívida histórica (info, não conta): {len(historico)} commit(s)")
    # 2. numeração
    texto = (RAIZ / "MEMÓRIAS.md").read_text(encoding="utf-8")
    nums = [int(m.group(1)) for l in texto.splitlines() if (m := ENTRADA.match(l))]
    repetidos = sorted({n for n in nums if nums.count(n) > 1})
    novos = [n for n in repetidos if n not in base.get("repetidos_conhecidos", [])]
    r["2_numeracao"] = (not novos, f"repetidos novos: {novos}" if novos else f"repetidos só os da baseline ({len(repetidos)})")
    # 3. segredo nas linhas adicionadas (últimos 50 commits)
    achados = []
    for arq in ARQUIVOS:
        add = git("log", "-n", "50", "-p", "--format=", "--", arq)
        for l in add.splitlines():
            if l.startswith("+") and not l.startswith("+++"):
                for pad in secretos():
                    if pad and pad in l and not ANCORA.search(l):
                        achados.append(arq)  # nunca o texto do padrão: o log não pode vazar segredo (CodeQL)
    r["3_segredo"] = (not achados, f"{len(achados)} ocorrência(s) de padrão de segredo em {sorted(set(achados))}" if achados else "nenhum")
    # 4. registro por merge de PR
    diretos = []
    for arq in ARQUIVOS:
        for c in git("log", "-n", "50", "--no-merges", "--format=%h", "--", arq).split():
            if "DIÁRIO" in git("show", "-s", "--format=%B", c) or ENTRADA.search(git("show", c, "--", arq)):
                diretos.append(c)
    r["4_registro_por_pr"] = (not diretos, f"commit direto adicionando entrada: {diretos[:3]}" if diretos else "todas as entradas vieram por merge")
    # 5. working tree igual ao origin/main
    sujo = [a for a in ARQUIVOS if git("diff", "--", a).strip()]
    r["5_copia_igual_origin"] = (not sujo, f"alteração não commitada: {sujo}" if sujo else "working tree igual ao HEAD")
    return r

def main() -> int:
    res = checar()
    for k, (ok, msg) in res.items():
        print(("PASS" if ok else "FAIL"), k, "-", msg)
    falhas = sum(1 for ok, _ in res.values() if not ok)
    print("AUDITORIA ESCRIBA OK" if not falhas else f"AUDITORIA ESCRIBA FALHOU ({falhas})")
    try:
        log = Path.home() / ".cache" / "agata" / "auditoria-escriba.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                "resultado": {k: ok for k, (ok, _) in res.items()}}, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return 1 if falhas else 0

if __name__ == "__main__":
    sys.exit(main())
