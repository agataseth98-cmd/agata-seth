#!/usr/bin/env python3
"""
Tools do loop da Fase 4 (P4-02). Funcoes Python tipadas que wrappam os scripts
deterministicos de ~/agata/scripts/. O grafo chama estas -- nao re-implementa a logica.

Herda o desenho do P0-02 (redesign/mcp/servidor.py):
- `_run` NUNCA levanta: timeout -> 124; binario ausente -> 127.
- retorno sempre estruturado, nunca texto livre "achando" verdade.
- query_canon rejeita qualquer termo com '-' inicial (barra --rebuild) + regex;
  a defesa real e' subprocess sem shell + args em lista.
- check_citation escreve um temp privado (o script recebe caminho), chama, apaga.

Novo nesta fase: `commit_entry` (saiu da Fase 0 -- P0-00; escreve canon, nao e' wrapper fino).
APPEND-ONLY: nunca reescreve/trunca; so acrescenta. Idempotente pela idem key (P4-00).
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

AGATA = Path(os.path.expanduser("~/agata"))
SCRIPTS = AGATA / "scripts"


def _run(cmd, cwd=None, stdin=None, timeout=120) -> dict:
    try:
        r = subprocess.run(cmd, cwd=str(cwd or AGATA), input=stdin,
                           capture_output=True, text=True, timeout=timeout)
        return {"exit_code": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
    except subprocess.TimeoutExpired as e:
        return {"exit_code": 124, "stdout": e.stdout or "", "stderr": (e.stderr or "") + f"\n[timeout {timeout}s]"}
    except OSError as e:
        return {"exit_code": 127, "stdout": "", "stderr": f"[falha ao executar {cmd!r}: {e}]"}


# --------------------------------------------------------------------------- read-only
def git_sync(repo=None) -> dict:
    """Sync com o remoto em 2 eixos (canon local vs origin/main; branch vs upstream)."""
    repo = repo or AGATA
    fetch = _run(["git", "fetch", "--quiet", "origin"], cwd=repo, timeout=180)
    main_local = _run(["git", "rev-parse", "main"], cwd=repo)["stdout"].strip() or None
    ls = _run(["git", "ls-remote", "origin", "refs/heads/main"], cwd=repo)["stdout"].strip()
    main_remote = ls.split()[0] if ls else None
    head = _run(["git", "rev-parse", "HEAD"], cwd=repo)["stdout"].strip() or None
    up = _run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], cwd=repo)
    upstream = up["stdout"].strip() if up["exit_code"] == 0 else None
    up_head = _run(["git", "rev-parse", upstream], cwd=repo)["stdout"].strip() if upstream else None
    return {
        "canon_local": main_local, "canon_remote": main_remote,
        "canon_em_dia": bool(main_local and main_remote and main_local == main_remote),
        "branch_head": head, "branch_upstream": upstream, "branch_upstream_head": up_head or None,
        "branch_em_dia": bool(head and up_head and head == up_head),
        "fetch_exit_code": fetch["exit_code"], "fetch_error": (fetch["stderr"] or "").strip() or None,
    }


def run_perimetro(repo=None) -> dict:
    r = _run(["bash", "scripts/perimetro.sh"], cwd=repo)
    linhas = ((r["stdout"] or "") + (r["stderr"] or "")).splitlines()
    resumo = next((l for l in linhas if "RESULTADO GERAL" in l), linhas[-1] if linhas else "")
    return {"exit_code": r["exit_code"], "resumo": resumo.strip(), "linhas": linhas}


_SUSPEITO_RE = re.compile(r"^SUSPEITO \(P-7\):\s*(.+)$", re.MULTILINE)
_RESUMO_P7_RE = re.compile(r"__RESUMO_P7__ total_citacoes=(\d+) suspeitos=(\d+) pulados_exemplo=(\d+)")


def check_citation(texto: str, repo=None) -> dict:
    fd, path = tempfile.mkstemp(prefix="grafo_cit_", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(texto)
        r = _run(["bash", "scripts/checar_citacao.sh", path], cwd=repo)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    out = r["stdout"] or ""
    m = _RESUMO_P7_RE.search(out)
    return {"exit_code": r["exit_code"], "resumo": (m.group(0) if m else out.strip()),
            "suspeitos": [x.group(1).strip() for x in _SUSPEITO_RE.finditer(out)]}


def lint_header(cabecalho: str, repo=None) -> dict:
    r = _run(["python3", "scripts/verificar_cabecalho.py"], cwd=repo, stdin=cabecalho)
    return {"ok": r["exit_code"] == 0, "motivo": (r["stdout"] or "").strip() or (r["stderr"] or "").strip()}


_TERMO_RE = re.compile(r"^[\wÀ-ÿ][\wÀ-ÿ\- ]*$")


class TermoInvalido(ValueError):
    pass


def query_canon(termos: list[str], repo=None) -> dict:
    if not termos:
        raise TermoInvalido("query_canon exige pelo menos um termo")
    for t in termos:
        if t.startswith("-"):
            raise TermoInvalido(f"termo rejeitado: {t!r} comeca com '-' (barra --rebuild)")
        if not _TERMO_RE.match(t):
            raise TermoInvalido(f"termo rejeitado: {t!r} -- fora de ^[\\wÀ-ÿ][\\wÀ-ÿ\\- ]*$")
    r = _run(["python3", "scripts/consultar_indice.py", *termos], cwd=repo)
    return {"exit_code": r["exit_code"], "trechos": (r["stdout"] or "").strip(),
            "erro": (r["stderr"] or "").strip() or None}


# --------------------------------------------------------------------------- commit_entry (escreve canon)
_MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI"


def commit_entry(repo: str, alvo: str, entrada: str, idem: str, *,
                 posicao: str = "fim", validar_cabecalho: bool = True) -> dict:
    """
    Acrescenta `entrada` a `<repo>/<alvo>` (APPEND-ONLY) e faz `git commit`.

    - `posicao="fim"`: acrescenta no fim fisico (LOG.md).
    - `posicao="apos-marcador"`: insere logo APOS a linha do marcador `ENTRADAS-NOVAS:AQUI`
      (MEMORIAS.md -- mais recente primeiro). Nunca move/edita nada acima do marcador.
    - Valida o cabecalho da Regra 1 (`verificar_cabecalho.py`) e as citacoes
      (`checar_citacao.sh`) ANTES de escrever; invalido -> {ok: False}, nada tocado.
    - Idempotente: se `git log --grep=idem:<idem>` ja acha, nao escreve nem commita.
    - Garante que o arquivo SO CRESCEU (assert de tamanho).
    """
    repo_p = Path(repo)
    alvo_p = repo_p / alvo
    # idempotencia
    g = subprocess.run(["git", "-C", repo, "log", "--grep", f"idem:{idem}", "--oneline"],
                       capture_output=True, text=True)
    if g.stdout.strip():
        sha = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
        return {"ok": True, "estado": "pulado(idempotente)", "commit_sha": sha, "idem": idem}
    # validacao
    problemas = []
    if validar_cabecalho:
        lh = lint_header(entrada, repo=repo)
        if not lh["ok"]:
            problemas.append(f"cabecalho: {lh['motivo']}")
    cc = check_citation(entrada, repo=repo)
    if cc["suspeitos"]:
        problemas.append(f"citacoes suspeitas: {cc['suspeitos']}")
    if problemas:
        return {"ok": False, "motivo": "; ".join(problemas), "idem": idem}
    if not alvo_p.exists():
        return {"ok": False, "motivo": f"alvo inexistente: {alvo_p}", "idem": idem}
    # escrita APPEND-ONLY
    original = alvo_p.read_text(encoding="utf-8")
    bloco = ("\n" if not entrada.startswith("\n") else "") + entrada.rstrip() + "\n"
    if posicao == "apos-marcador":
        linhas = original.splitlines(keepends=True)
        i = next((k for k, l in enumerate(linhas) if _MARCADOR in l), None)
        if i is None:
            return {"ok": False, "motivo": f"marcador {_MARCADOR!r} ausente em {alvo}", "idem": idem}
        novo = "".join(linhas[: i + 1]) + bloco + "".join(linhas[i + 1:])
    elif posicao == "fim":
        novo = original + bloco
    else:
        return {"ok": False, "motivo": f"posicao invalida: {posicao!r}", "idem": idem}
    if len(novo) <= len(original) or original not in novo:
        return {"ok": False, "motivo": "escrita nao e' append-only (arquivo nao cresceu / conteudo antigo sumiu)", "idem": idem}
    with open(alvo_p, "w", encoding="utf-8") as f:
        f.write(novo)
        f.flush()
        os.fsync(f.fileno())
    subprocess.run(["git", "-C", repo, "add", alvo], check=True)
    r = subprocess.run(["git", "-C", repo, "commit", "-q", "-m",
                        f"entrada em {alvo} ({posicao})\n\nidem:{idem}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return {"ok": False, "motivo": f"git commit falhou: {r.stderr.strip()}", "idem": idem}
    sha = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    return {"ok": True, "estado": "novo", "commit_sha": sha, "idem": idem,
            "bytes_antes": len(original), "bytes_depois": len(novo)}


TOOLS = {
    "git_sync": git_sync, "run_perimetro": run_perimetro, "check_citation": check_citation,
    "lint_header": lint_header, "query_canon": query_canon, "commit_entry": commit_entry,
}


if __name__ == "__main__":
    import json
    import sys
    a = sys.argv[1:]
    if not a or a[0] not in TOOLS:
        print("uso: tools.py <tool> [args]\n  " + " ".join(TOOLS), file=sys.stderr)
        sys.exit(2)
    name = a[0]
    if name in ("check_citation", "lint_header"):
        print(json.dumps(TOOLS[name](sys.stdin.read()), ensure_ascii=False, indent=2))
    elif name == "query_canon":
        print(json.dumps(query_canon(a[1:]), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(TOOLS[name](), ensure_ascii=False, indent=2))
