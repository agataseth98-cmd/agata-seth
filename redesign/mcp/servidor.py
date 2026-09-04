#!/usr/bin/env python3
"""Servidor FastMCP das ferramentas de Máquina do Agata (P0-02, branch redesign).

Expõe as verificações determinísticas READ-ONLY do sistema como tools MCP, para
que qualquer executor — sessão Claude, Codex, Qwen Coder, Goose, humano — dirija a
camada de verificação de forma idêntica. É a cola do handoff.

Invariantes (ver redesign/README.md e extras/arquivo-redesign/tasks/P0-02-*.md):
- NENHUMA tool escreve no workspace nem no canon. "read-only" aqui = sem escrita em
  arquivo rastreado / MEMÓRIAS / índice, NÃO "zero escrita no filesystem": git_sync
  faz `git fetch`, que atualiza metadados em .git/ (refs de rastreio, FETCH_HEAD,
  objetos); check_citation escreve um temp e o apaga. Nenhuma toca a árvore de trabalho.
- Sem commit_entry nesta fase (foi para a Fase 4).
- Cada tool é wrapper fino de um script existente em ~/agata/scripts/, chamado com
  cwd=~/agata. Retorno é sempre dado estruturado, nunca texto livre "achando" verdade.
- query_canon rejeita qualquer flag (barra --rebuild, que regenera o índice). LÊ o
  índice derivado em memoria/missoes/agata-sistema/derivado/ — não escreve lá.
- check_citation não é passthrough de stdin: escreve um temp privado, chama o
  script (que recebe caminho), captura o resumo e apaga o temp.
- _run nunca levanta: timeout -> returncode 124; binário ausente/não-executável -> 127.

Uso:
    redesign/mcp/.venv/bin/python redesign/mcp/servidor.py
        # sobe o servidor MCP em stdio (default local)

    redesign/mcp/.venv/bin/python redesign/mcp/servidor.py --selftest <tool> [args...]
        # roda uma tool direto e imprime o JSON do retorno; exit espelha o script
        # ex.: --selftest run_perimetro
        #      --selftest lint_header  (lê o cabeçalho por stdin)
        #      --selftest check_citation  (lê o texto por stdin)
        #      --selftest query_canon hidratação âncora
        #      --selftest git_sync
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

from fastmcp import FastMCP

REPO = os.path.expanduser("~/agata")

mcp = FastMCP("agata-maquina")


_TIMEOUT_PADRAO = 120


def _run(
    cmd: list[str], stdin: str | None = None, timeout: int = _TIMEOUT_PADRAO
) -> subprocess.CompletedProcess:
    """subprocess.run fixo em cwd=~/agata, sem shell, texto. NUNCA levanta:
    timeout -> returncode 124; binário ausente/não-executável -> 127."""
    try:
        return subprocess.run(
            cmd,
            cwd=REPO,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(
            cmd, 124, e.stdout or "", (e.stderr or "") + f"\n[timeout após {timeout}s]"
        )
    except OSError as e:
        return subprocess.CompletedProcess(
            cmd, 127, "", f"[falha ao executar {cmd!r}: {e}]"
        )


# --------------------------------------------------------------------------- #
# git_sync                                                                     #
# --------------------------------------------------------------------------- #
@mcp.tool
def git_sync() -> dict:
    """Estado de sincronização com o remoto, em dois eixos separados:
    (a) o canon local (`main`) vs `origin/main` — é o que alimenta o `sync:` do cabeçalho;
    (b) a branch atual vs o seu upstream.

    Faz `git fetch`, que ATUALIZA metadados em .git/ (refs de rastreio, FETCH_HEAD,
    objetos); nunca toca a árvore de trabalho, o índice, nem empurra nada.

    Retorna: canon_local, canon_remote, canon_em_dia · branch, branch_head,
    branch_upstream, branch_upstream_head, branch_em_dia · fetch_exit_code, fetch_error
    (0/None quando o fetch foi ok; != 0 quando houve erro de transporte — nesse caso
    canon_remote pode vir de um ls-remote que também falhou, então cheque fetch_error).
    """
    fetch = _run(["git", "fetch", "--quiet", "origin"], timeout=180)

    main_local = _run(["git", "rev-parse", "main"]).stdout.strip() or None
    ls = _run(["git", "ls-remote", "origin", "refs/heads/main"])
    ls_out = (ls.stdout or "").strip()
    main_remote = ls_out.split()[0] if ls_out else None

    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip() or None
    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip() or None
    up = _run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"]
    )
    upstream = up.stdout.strip() if up.returncode == 0 else None
    upstream_head = (
        (_run(["git", "rev-parse", upstream]).stdout.strip() or None)
        if upstream
        else None
    )

    return {
        "canon_local": main_local,
        "canon_remote": main_remote,
        "canon_em_dia": bool(
            main_local and main_remote and main_local == main_remote
        ),
        "branch": branch,
        "branch_head": head,
        "branch_upstream": upstream,
        "branch_upstream_head": upstream_head,
        "branch_em_dia": bool(
            head and upstream_head and head == upstream_head
        ),
        "fetch_exit_code": fetch.returncode,
        "fetch_error": (fetch.stderr or "").strip() or None,
    }


# --------------------------------------------------------------------------- #
# run_perimetro                                                                #
# --------------------------------------------------------------------------- #
def _run_perimetro() -> dict:
    r = _run(["bash", "scripts/perimetro.sh"])
    saida = (r.stdout or "") + (r.stderr or "")
    linhas = saida.splitlines()
    resumo = next(
        (ln for ln in linhas if "RESULTADO GERAL" in ln),
        linhas[-1] if linhas else "",
    )
    return {"exit_code": r.returncode, "resumo": resumo.strip(), "linhas": linhas}


@mcp.tool
def run_perimetro() -> dict:
    """Roda `bash scripts/perimetro.sh` (read-only, ACHA E PARA).

    Retorna {exit_code, resumo, linhas}. `resumo` é a linha "RESULTADO GERAL".
    exit_code 0 = perímetro verde.
    """
    return _run_perimetro()


# --------------------------------------------------------------------------- #
# check_citation                                                               #
# --------------------------------------------------------------------------- #
_SUSPEITO_RE = re.compile(r"^SUSPEITO \(P-7\):\s*(.+)$", re.MULTILINE)
_RESUMO_P7_RE = re.compile(
    r"__RESUMO_P7__ total_citacoes=(\d+) suspeitos=(\d+) pulados_exemplo=(\d+)"
)


def _parse_citacao(stdout: str) -> list[str]:
    return [m.group(1).strip() for m in _SUSPEITO_RE.finditer(stdout)]


def _check_citation(texto: str) -> dict:
    fd, path = tempfile.mkstemp(prefix="mcp_cit_", suffix=".txt")
    try:
        # os.fdopen assume a posse do fd e o fecha na saída do with, mesmo em
        # erro de escrita — sem fd vazado se o write falhar (ENOSPC etc.).
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(texto)
        r = _run(["scripts/checar_citacao.sh", path])
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    stdout = r.stdout or ""
    contagem = _RESUMO_P7_RE.search(stdout)
    return {
        "exit_code": r.returncode,
        "resumo": (contagem.group(0) if contagem else stdout.strip()),
        "suspeitos": _parse_citacao(stdout),
    }


@mcp.tool
def check_citation(texto: str) -> dict:
    """Checa as citações `(n - síntese)` de um texto contra o corpo real de MEMÓRIAS.md (P-7).

    Adaptador de temp: o script recebe um caminho de arquivo, não stdin. O wrapper
    escreve um temp privado, chama o script e apaga o temp.
    Retorna {exit_code, resumo, suspeitos}. exit_code 1 = há citação suspeita.
    """
    return _check_citation(texto)


# --------------------------------------------------------------------------- #
# lint_header                                                                  #
# --------------------------------------------------------------------------- #
def _lint_header(cabecalho: str) -> dict:
    r = _run(["python3", "scripts/verificar_cabecalho.py"], stdin=cabecalho)
    motivo = (r.stdout or "").strip() or (r.stderr or "").strip()
    return {"ok": r.returncode == 0, "motivo": motivo}


@mcp.tool
def lint_header(cabecalho: str) -> dict:
    """Verifica se um cabeçalho cumpre o formato da Regra 1 (scripts/verificar_cabecalho.py).

    O script lê o cabeçalho por stdin. Retorna {ok, motivo}: ok=True e motivo="OK"
    quando passa; ok=False e motivo com uma linha por falha quando não.
    """
    return _lint_header(cabecalho)


# --------------------------------------------------------------------------- #
# query_canon                                                                  #
# --------------------------------------------------------------------------- #
_TERMO_RE = re.compile(r"^[\wÀ-ÿ][\wÀ-ÿ\- ]*$")


class TermoInvalido(ValueError):
    pass


def _validar_termos(termos: list[str]) -> list[str]:
    if not termos:
        raise TermoInvalido("query_canon exige pelo menos um termo de consulta")
    for t in termos:
        if t.startswith("-"):
            raise TermoInvalido(
                f"termo rejeitado: {t!r} começa com '-' — flags não são aceitas "
                f"(barra --rebuild, que regenera o índice)"
            )
        if not _TERMO_RE.match(t):
            raise TermoInvalido(
                f"termo rejeitado: {t!r} — só letras/dígitos/hífen/espaço "
                f"(padrão ^[\\wÀ-ÿ][\\wÀ-ÿ\\- ]*$)"
            )
    return termos


def _query_canon(termos: list[str]) -> dict:
    _validar_termos(termos)
    r = _run(["python3", "scripts/consultar_indice.py", *termos])
    return {
        "exit_code": r.returncode,
        "trechos": (r.stdout or "").strip(),
        "erro": (r.stderr or "").strip() or None,
    }


@mcp.tool
def query_canon(termos: list[str]) -> dict:
    """Consulta dirigida ao índice derivado do canon (scripts/consultar_indice.py).

    READ-ONLY: rejeita qualquer termo começando com '-' (barra --rebuild) e qualquer
    termo fora de ^[\\wÀ-ÿ][\\wÀ-ÿ\\- ]*$. Nunca regenera o índice. LÊ o índice em
    memoria/missoes/agata-sistema/derivado/indice.md — não escreve nessa área. Se o
    índice estiver ausente/corrompido, isso continua sendo erro de leitura (o script
    orienta a rodar o gerador), nunca reconstrução automática. Retorna {exit_code,
    trechos, erro}.

    Nota de defesa: a garantia contra --rebuild vem de subprocess sem shell + args em
    lista (um termo como "x --rebuild" chega como UM argumento de texto, não como flag);
    o regex é a segunda linha, não a primeira.
    """
    return _query_canon(termos)


# --------------------------------------------------------------------------- #
# selftest / entrypoint                                                        #
# --------------------------------------------------------------------------- #
_SELFTEST = {
    "git_sync": lambda argv: git_sync(),
    "run_perimetro": lambda argv: _run_perimetro(),
    "check_citation": lambda argv: _check_citation(sys.stdin.read()),
    "lint_header": lambda argv: _lint_header(sys.stdin.read()),
    "query_canon": lambda argv: _query_canon(argv),
}


def _selftest(argv: list[str]) -> int:
    if not argv or argv[0] not in _SELFTEST:
        print(
            "uso: servidor.py --selftest <tool> [args...]\n"
            f"tools: {', '.join(_SELFTEST)}",
            file=sys.stderr,
        )
        return 2
    nome, resto = argv[0], argv[1:]
    try:
        resultado = _SELFTEST[nome](resto)
    except TermoInvalido as e:
        print(json.dumps({"erro_validacao": str(e)}, ensure_ascii=False, indent=2))
        return 3
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if "exit_code" in resultado:
        return int(resultado["exit_code"] or 0)
    # tools sem exit_code no retorno (lint_header): espelha o veredito
    return 1 if resultado.get("ok") is False else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        raise SystemExit(_selftest(sys.argv[2:]))
    mcp.run()
