#!/usr/bin/env python3
"""aplicar.py <nome>... [--registro <arquivo-entrada.txt>] [--onde <arquivo-paragrafo.txt>] [--coautor "Nome <email>"]
Aplica propostas P-8 JÁ ASSINADAS pelo Humano: worktree nova de origin/main, copia o APROVADO-, p8_verificar.sh (tem de dar
PODE APLICAR), git apply, move o par para aplicadas/, insere a entrada de MEMÓRIAS (número = topo+1, o texto traz {N}),
commit (pre-commit real), push, PR, espera CI, junta, pull. Se o main andou antes do merge (BEHIND/DIRTY), refaz a branch sobre
o origin/main novo (verificador, apply e número de MEMÓRIAS de novo) e empurra com --force-with-lease. Nunca assina; não faz nada se faltar a assinatura."""
import argparse, json, os, re, subprocess, sys, shutil, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diff_limpo, numero_memorias, trava  # mesma pasta: fonte única (12/11/2026)
R = os.path.expanduser("~/agata")
def sh(cwd, *a, ok=True, **k):
    p = subprocess.run(a, cwd=cwd, text=True, capture_output=True, **k)
    if ok and p.returncode:
        sys.exit(f"ERRO: {' '.join(a)}\n{p.stdout[-1500:]}{p.stderr[-1500:]}")
    return p
proximo_numero = numero_memorias.proximo


def precisa_refazer(estado, saida):
    """O merge falhou porque a base andou (BEHIND) ou conflita com ela (DIRTY)? Aí a branch se refaz do zero sobre o
    origin/main novo. `gh pr update-branch` juntava o main na branch e conflitava em MEMÓRIAS.md (mesmo ponto de inserção):
    discord-venv-unica-20261028 ficou DIRTY assim em 28/10/2026."""
    return estado in ("BEHIND", "DIRTY") or any(t in saida for t in ("not up to date", "status checks are expected", "BEHIND", "merge conflict"))


def montar(wt, a, coautor):
    """Sobre o HEAD atual da worktree (= origin/main): verificador congelado, apply, par para aplicadas/, MEMÓRIAS
    (número = topo+1 DESTA base), ONDE_ESTAMOS, commit. Roda de novo, igual, cada vez que a base é refeita."""
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


def main():
  ap = argparse.ArgumentParser(); ap.add_argument("nomes", nargs="+"); ap.add_argument("--registro", default=None, help="entrada de MEMÓRIAS; NÃO usar se o .diff já mexe em MEMÓRIAS.md")
  ap.add_argument("--onde")
  ap.add_argument("--coautor", default=os.environ.get("EQUIPE_COAUTOR"), help="linha Co-Authored-By (nome do modelo REAL, medido; padrão: $EQUIPE_COAUTOR ou nenhuma)")
  ap.add_argument("--agente", default=os.environ.get("EQUIPE_AGENTE") or os.environ.get("DUPLA_AGENTE") or "claude",
                  help="membro da Equipe que aplica (claude, codex, gemini...): dá o nome da worktree (.<membro>/worktrees)")
  ap.add_argument("--sem-pull", action="store_true", help="não atualiza o checkout compartilhado (para trabalhar só em worktree própria)")
  a = ap.parse_args()
  if not re.match(r"^[a-z][a-z0-9-]{0,30}$", a.agente): sys.exit(f"membro inválido: {a.agente!r}")
  coautor = a.coautor or ""  # nunca um nome de modelo fixo no código: o modelo muda de sessão para sessão
  if not a.sem_pull:
      sh(R, "git", "pull", "-q", "--ff-only")
  for n in a.nomes:
      if not os.path.exists(f"{R}/propostas/APROVADO-{n}"): sys.exit(f"SEM ASSINATURA: {n} (nada aplicado)")
      dp = f"{R}/propostas/{n}.diff"
      if a.registro and os.path.exists(dp) and re.search(r"^\+\+\+ b/MEMÓRIAS\.md$", open(dp, encoding="utf-8").read(), re.M):
          sys.exit(f"{n} mexe em MEMÓRIAS.md: a entrada já vem no .diff; --registro duplicaria (rode sem --registro)")
  for n in a.nomes:  # (3a) recusa mecânica: diff com hunk em bloco ANCORA-SHA quebra no commit seguinte
      achados = diff_limpo.hunks_gerados(open(f"{R}/propostas/{n}.diff", encoding="utf-8").read())
      if achados: sys.exit(f"{n}.diff tem hunk em bloco gerado (ANCORA-SHA), nada aplicado: {achados[0][0]} linha {achados[0][1]}")
  if trava.ativos(R): sys.exit(f"outra aplicação em curso nesta cópia: {', '.join(trava.ativos(R))} (nada aplicado)")
  abertas = aplicacoes_remotas()
  if abertas: sys.exit(f"aplicação em curso no GitHub ({', '.join(abertas)}): espere o fim (nada aplicado)")
  tag = "-".join(a.nomes)[:60]; wt = f"{R}/.{a.agente}/worktrees/aplica-{a.agente}-{int(time.time())}"; br = f"aplica/{tag}"
  trava.marcar(R, tag)  # (3b) trava: marcador local com o PID; some no fim, mesmo se a aplicação cair
  try:
      _aplicar(a, coautor, tag, wt, br)
  finally:
      trava.soltar(R, tag)


def aplicacoes_remotas():
  """Heads `aplica/*` das PRs abertas. Falha fechada: sem a lista, não se aplica."""
  p = subprocess.run(["gh", "pr", "list", "--repo", "agataseth98-cmd/agata-seth", "--state", "open", "--json", "headRefName", "--limit", "200"],
                     capture_output=True, text=True)
  if p.returncode: sys.exit(f"não consegui listar as PRs abertas (falha fechada): {p.stderr.strip()[:200]}")
  return trava.aplicacoes_abertas([d.get("headRefName", "") for d in json.loads(p.stdout or "[]")])


def _aplicar(a, coautor, tag, wt, br):
  sh(R, "git", "fetch", "-q"); sh(R, "git", "worktree", "add", "-q", "-b", br, wt, "origin/main")
  montar(wt, a, coautor)
  sh(wt, "git", "push", "-q", "-u", "origin", br)
  pr = sh(wt, "gh", "pr", "create", "--repo", "agataseth98-cmd/agata-seth", "--base", "main", "--head", br, "--title", f"Aplica {', '.join(a.nomes)} (assinado)",
          "--body", "Aplicação do(s) diff(s) assinado(s) pelo Humano; par movido para propostas/aplicadas/; entrada de MEMÓRIAS no mesmo commit.\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)").stdout.strip()
  num = pr.rsplit("/", 1)[-1]; print("PR", pr, flush=True)
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
  for _ in range(4):  # main com proteção "strict": se andou, REFAZ a branch sobre o main novo e espera o CI de novo
      m = sh(wt, "gh", "pr", "merge", num, "--repo", "agataseth98-cmd/agata-seth", "--merge", "--match-head-commit", HEAD, ok=False)
      if m.returncode == 0: break
      estado = json.loads(sh(wt, "gh", "pr", "view", num, "--repo", "agataseth98-cmd/agata-seth", "--json", "mergeStateStatus", ok=False).stdout or "{}").get("mergeStateStatus", "")
      if not precisa_refazer(estado, m.stdout + m.stderr): sys.exit(f"merge falhou ({estado}):\n{m.stdout}{m.stderr}")
      print(f"base andou ({estado}): refazendo a branch sobre o origin/main novo", flush=True)
      sh(wt, "git", "fetch", "-q", "origin"); sh(wt, "git", "reset", "-q", "--hard", "origin/main"); sh(wt, "git", "clean", "-qfd")
      montar(wt, a, coautor)  # verificador da base NOVA, apply de novo, número de MEMÓRIAS recalculado
      sh(wt, "git", "push", "-q", "--force-with-lease", "origin", br)
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
