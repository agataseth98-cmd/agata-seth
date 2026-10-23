#!/usr/bin/env python3
"""aplicar.py <nome>... [--registro <arquivo-entrada.txt>] [--onde <arquivo-paragrafo.txt>] [--coautor "Nome <email>"]
Aplica propostas P-8 JÁ ASSINADAS pelo Humano: worktree nova de origin/main, copia o APROVADO-, p8_verificar.sh (tem de dar
PODE APLICAR), git apply, move o par para aplicadas/, insere a entrada de MEMÓRIAS (número = topo+1, o texto traz {N}),
commit (pre-commit real), push, PR, espera CI, junta, pull. Nunca assina; não faz nada se faltar a assinatura."""
import argparse, os, re, subprocess, sys, shutil, time
R = os.path.expanduser("~/agata")
def sh(cwd, *a, ok=True, **k):
    p = subprocess.run(a, cwd=cwd, text=True, capture_output=True, **k)
    if ok and p.returncode:
        sys.exit(f"ERRO: {' '.join(a)}\n{p.stdout[-1500:]}{p.stderr[-1500:]}")
    return p
def proximo_numero(texto):
    """Próximo número livre de MEMÓRIAS. Aceita QUALQUER palavra após o número (inclusive acentuada: DIÁRIO, CORREÇÃO);
    o padrão antigo [A-ZÇÃÕ]+ não reconhecia 'Á' e deu (729) a 14 entradas em 16/10/2026."""
    nums = [int(x) for x in re.findall(r"^\((\d+)\) \S+ — ", texto, re.M)]
    if not nums:
        raise ValueError("nenhuma entrada numerada encontrada em MEMÓRIAS.md")
    return max(nums) + 1


def main():
  ap = argparse.ArgumentParser(); ap.add_argument("nomes", nargs="+"); ap.add_argument("--registro", default=None, help="entrada de MEMÓRIAS; NÃO usar se o .diff já mexe em MEMÓRIAS.md")
  ap.add_argument("--onde")
  ap.add_argument("--coautor", default=None, help="linha Co-Authored-By; padrão: Claude Haiku 5.5 para claude, nenhuma para codex")
  ap.add_argument("--agente", default=os.environ.get("DUPLA_AGENTE", "claude"), choices=("claude", "codex"),
                  help="quem aplica: dá o nome da worktree (.<agente>/worktrees) e da autoria")
  ap.add_argument("--sem-pull", action="store_true", help="não atualiza o checkout compartilhado (para trabalhar só em worktree própria)")
  a = ap.parse_args()
  coautor = a.coautor if a.coautor is not None else ("Claude Haiku 5.5 <noreply@anthropic.com>" if a.agente == "claude" else "")
  if not a.sem_pull:
      sh(R, "git", "pull", "-q", "--ff-only")
  for n in a.nomes:
      if not os.path.exists(f"{R}/propostas/APROVADO-{n}"): sys.exit(f"SEM ASSINATURA: {n} (nada aplicado)")
      dp = f"{R}/propostas/{n}.diff"
      if a.registro and os.path.exists(dp) and re.search(r"^\+\+\+ b/MEMÓRIAS\.md$", open(dp, encoding="utf-8").read(), re.M):
          sys.exit(f"{n} mexe em MEMÓRIAS.md: a entrada já vem no .diff; --registro duplicaria (rode sem --registro)")
  tag = "-".join(a.nomes)[:60]; wt = f"{R}/.{a.agente}/worktrees/aplica-{a.agente}-{int(time.time())}"; br = f"aplica/{tag}"
  sh(R, "git", "fetch", "-q"); sh(R, "git", "worktree", "add", "-q", "-b", br, wt, "origin/main")
  for n in a.nomes:
      shutil.copy(f"{R}/propostas/APROVADO-{n}", f"{wt}/propostas/")
  # Verificador CONFIÁVEL = o da base, congelado ANTES de qualquer apply (um diff do lote não pode trocar o verificador do próximo).
  confiavel = f"{wt}/../.verificador-confiavel-{int(time.time())}.sh"
  shutil.copy(f"{wt}/scripts/p8_verificar.sh", confiavel)
  for n in a.nomes:  # TODOS os pares conferidos antes de aplicar o primeiro
      v = sh(wt, "bash", confiavel, n, ok=False)
      linhas = [l for l in v.stdout.splitlines() if l.strip()]
      if v.returncode != 0 or not linhas or linhas[-1].strip() != f"PODE APLICAR: {n}":
          sys.exit(f"FALHA no verificador ({n}) rc={v.returncode}:\n{v.stdout}{v.stderr}")
  os.remove(confiavel)
  for n in a.nomes:
      sh(wt, "git", "apply", f"propostas/{n}.diff"); os.makedirs(f"{wt}/propostas/aplicadas", exist_ok=True)
      sh(wt, "git", "mv", f"propostas/{n}.diff", "propostas/aplicadas/"); os.rename(f"{wt}/propostas/APROVADO-{n}", f"{wt}/propostas/aplicadas/APROVADO-{n}")
  if a.registro:
    t = open(f"{wt}/MEMÓRIAS.md", encoding="utf-8").read()
    ult = proximo_numero(t) - 1; m = re.search(r"^<!-- ENTRADAS-NOVAS:AQUI.*-->\n", t, re.M)
    e = open(a.registro, encoding="utf-8").read().replace("{N}", str(ult + 1)).rstrip("\n") + "\n\n"
    open(f"{wt}/MEMÓRIAS.md", "w", encoding="utf-8").write(t[:m.end()] + e + t[m.end():])
  if a.onde:
      o = open(f"{wt}/ONDE_ESTAMOS.md", encoding="utf-8").read(); i = o.index("## Hoje")
      open(f"{wt}/ONDE_ESTAMOS.md", "w", encoding="utf-8").write(o[:i] + open(a.onde, encoding="utf-8").read().rstrip("\n") + "\n\n" + o[i:])
  sh(wt, "git", "add", "-A")
  msg = f"Aplica {', '.join(a.nomes)} (assinado pelo Humano)" + (" e registra" if a.registro else "") + (f"\n\nCo-Authored-By: {coautor}" if coautor else "")
  sh(wt, "git", "commit", "-qm", msg)
  sh(wt, "git", "push", "-q", "-u", "origin", br)
  pr = sh(wt, "gh", "pr", "create", "--repo", "agataseth98-cmd/agata-seth", "--base", "main", "--head", br, "--title", f"Aplica {', '.join(a.nomes)} (assinado)",
          "--body", "Aplicação do(s) diff(s) assinado(s) pelo Humano; par movido para propostas/aplicadas/; entrada de MEMÓRIAS no mesmo commit.\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)").stdout.strip()
  num = pr.rsplit("/", 1)[-1]; print("PR", pr, flush=True)
  import json
  EXIGIDOS = ("fiscal-p8", "suite-adversarial", "CodeQL")  # CodeQL entrou em 21/10/2026: alerta alto não pode passar pela aplicação
  def ci():
      """Espera e devolve True só se os TRÊS checks exigidos, pelo nome, passaram no HEAD atual da branch."""
      time.sleep(20); limite = time.time() + 1500  # 25 min: check ausente ou API ruim não prende para sempre
      while True:
          if time.time() > limite: return False, {"erro": "timeout esperando os checks"}
          j = sh(wt, "gh", "pr", "checks", num, "--repo", "agataseth98-cmd/agata-seth", "--json", "name,bucket", ok=False).stdout
          try: cs = {c["name"]: c["bucket"] for c in json.loads(j)}
          except Exception: cs = {}
          if all(n in cs and cs[n] not in ("pending",) for n in EXIGIDOS): return all(cs[n] == "pass" for n in EXIGIDOS), cs
          time.sleep(10)
  def head_oid():
      return json.loads(sh(wt, "gh", "pr", "view", num, "--repo", "agataseth98-cmd/agata-seth", "--json", "headRefOid").stdout)["headRefOid"]
  def ci_pinado():
      """Lê o head ANTES e DEPOIS dos checks; só vale se for o mesmo (senão repete, até 3 vezes)."""
      for _ in range(3):
          antes = head_oid(); ok, cs = ci(); depois = head_oid()
          if antes == depois: return ok, cs, depois
      return False, {"erro": "head mudou durante os checks"}, None
  ok, cs, HEAD = ci_pinado(); print(cs)  # o merge só vale para ESSE head (--match-head-commit)
  if not ok: sys.exit(f"CI não passou ({cs}); não juntei")
  for _ in range(4):  # main com proteção "strict": se andou, atualiza a branch e espera o CI de novo
      m = sh(wt, "gh", "pr", "merge", num, "--repo", "agataseth98-cmd/agata-seth", "--merge", "--match-head-commit", HEAD, ok=False)
      if m.returncode == 0: break
      if not any(t in (m.stdout + m.stderr) for t in ("not up to date", "status checks are expected", "BEHIND")): sys.exit(f"merge falhou:\n{m.stdout}{m.stderr}")
      sh(wt, "gh", "pr", "update-branch", num, "--repo", "agataseth98-cmd/agata-seth")
      ok, cs, HEAD = ci_pinado()
      if not ok: sys.exit(f"CI não passou após atualizar ({cs}); não juntei")
  else:
      sys.exit("não consegui juntar após 4 tentativas")
  if not a.sem_pull:
      sh(R, "git", "pull", "-q", "--ff-only")
  for n in a.nomes:
      try: os.remove(f"{R}/propostas/APROVADO-{n}")
      except FileNotFoundError: pass
  print("APLICADO E JUNTADO:", ", ".join(a.nomes))


if __name__ == "__main__":
    main()
