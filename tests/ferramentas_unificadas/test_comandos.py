"""AC-11 (instalar), AC-12 (promover), AC-13 (segredo fora de yml e log), AC-15 (listar)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from ferr_helpers import REPO, entrada_teste, escrever_overlay, montar_ctx

import estado as E
import instalar as I
import listar as LI
import nativos as N
import promover as P
import sincronizar as SYNC

PARES = ["transporte=stdio", "comando=echo", "args=ola", "env=AGATA_TESTE_VAR", "clis=claude,codex,opencode"]


def _arvore(raiz: Path) -> dict:
    return {str(p.relative_to(raiz)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(raiz.rglob("*")) if p.is_file()}


def _silencio(*_a, **_k):
    return None


def test_instalar_nao_toca_canon_nem_repo(ctx, fake):
    antes = _arvore(ctx.raiz)
    rc = I.instalar(ctx, "mcp", "agata-teste", PARES, pedir=lambda _: "sim", imprimir=_silencio)
    assert rc == 0
    assert _arvore(ctx.raiz) == antes, "instalar mexeu na raiz (config/, propostas/ ou outro arquivo)"
    assert ctx.overlay.is_file()
    assert "agata-teste" in ctx.overlay.read_text(encoding="utf-8")


def test_instalar_sem_sim_nao_grava(ctx, fake):
    antes = _arvore(ctx.raiz)
    rc = I.instalar(ctx, "mcp", "agata-teste", PARES, pedir=lambda _: "nao", imprimir=_silencio)
    assert rc == 3
    assert not ctx.overlay.exists()
    assert fake.chamadas == []
    assert _arvore(ctx.raiz) == antes


def test_promover_gera_diff_sem_aplicar(ctx, fake):
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})
    canonico = ctx.raiz / "config" / "ferramentas" / "mcp.yml"
    canon_antes = canonico.read_bytes()
    overlay_antes = ctx.overlay.read_bytes()
    saida: list[str] = []
    rc = P.promover(ctx, "agata-teste", imprimir=saida.append)
    assert rc == 0, saida
    assert canonico.read_bytes() == canon_antes, "promover aplicou a mudança na fonte canônica"
    assert ctx.overlay.read_bytes() == overlay_antes, "promover mexeu no overlay"
    diffs = sorted((ctx.raiz / "propostas").glob("*-promover-agata-teste.diff"))
    assert len(diffs) == 1
    texto = diffs[0].read_text(encoding="utf-8")
    assert texto.startswith("diff --git a/config/ferramentas/mcp.yml b/config/ferramentas/mcp.yml\n")
    assert "+  - nome: agata-teste" in texto
    assert "valor-de-teste" not in texto
    if shutil.which("git"):
        # o diff tem de ser aplicável (checagem, sem aplicar): formato que o P-8 confere
        verifica = subprocess.run(["git", "apply", "--check", str(diffs[0])], cwd=ctx.raiz,
                                  capture_output=True, text=True, timeout=30)
        assert verifica.returncode == 0, verifica.stderr


def test_sem_valor_de_segredo_em_yml_nem_log(ctx, fake, monkeypatch):
    segredo = "segredo-de-teste-9f8e7d6c"
    monkeypatch.setenv("AGATA_TESTE_VAR", segredo)
    saida: list[str] = []
    assert I.instalar(ctx, "mcp", "agata-teste", PARES, pedir=lambda _: "sim", imprimir=saida.append) == 0
    linhas, _ = LI.linhas(ctx)
    saida += [" ".join(map(str, linha)) for linha in linhas]
    # tentar gravar o valor pela própria CLI: recusado, e o valor não ecoa
    rc = I.instalar(ctx, "mcp", "outro-teste", ["transporte=stdio", "comando=echo", f"env=CHAVE={segredo}",
                                                "clis=claude"], pedir=lambda _: "sim", imprimir=saida.append)
    assert rc == 2
    assert segredo not in "\n".join(saida)
    arquivos = [ctx.overlay, ctx.raiz / "config" / "ferramentas" / "mcp.yml",
                ctx.base / "gerenciado.json", ctx.base / "log.jsonl"]
    for arq in arquivos:
        assert arq.exists(), arq
        assert segredo.encode() not in arq.read_bytes(), arq.name


def test_listar_categoria_cli_origem(ctx, fake):
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})
    assert SYNC.sincronizar(ctx, imprimir=_silencio) == 0
    linhas, indice = LI.linhas(ctx)
    chaves = {(cat, nome, cli, origem): estado for cat, nome, cli, origem, estado in linhas}
    for cli in ("claude", "codex", "opencode"):
        assert chaves[("mcp", "agata-teste", cli, "overlay")] == "gerenciado"
    assert ("mcp", "github-pat", "claude", "canonico") in chaves
    assert chaves[("skill", "agata-arranque", "claude", "canonico")] == "ponteiro ok"
    assert ("agente", "agata-dev", "claude", "canonico") in chaves
    assert indice == ".agents/skills/INDICE.md"
    assert "valor-de-teste" not in "\n".join(" ".join(map(str, linha)) for linha in linhas)
    # o nativo que não está na fonte aparece como nativo, sem valor
    ctx.claude_json.write_text('{"mcpServers": {"intrusa": {"type": "stdio", "command": "x", "args": []}}}')
    linhas2, _ = LI.linhas(ctx)
    assert ("mcp", "intrusa", "claude", "nativo") in {(c, n, cl, o) for c, n, cl, o, _e in linhas2}


def test_instalar_recusa_sem_tty(tmp_path):
    """Alto 1 (revisão independente): entrada pipeada não passa como "sim" do Humano. Nada é gravado."""
    home = tmp_path / "home"
    home.mkdir()
    env = {k: v for k, v in os.environ.items() if k not in ("XDG_CONFIG_HOME", "CODEX_HOME")}
    env["HOME"] = str(home)  # contexto_padrao usa HOME: o teste não toca o home real
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "ferramentas" / "instalar.py"), "mcp", "agata-teste",
         "--params", "transporte=stdio", "--params", "comando=echo", "--params", "clis=claude"],
        input="sim\n", capture_output=True, text=True, timeout=60, env=env)
    assert proc.returncode != 0
    assert "terminal" in proc.stdout
    assert not (home / "agata-local" / "ferramentas.yml").exists()
    assert not (home / ".local").exists(), "instalar criou pasta antes da recusa"


@pytest.mark.slow
def test_opencode_mcp_add_real(tmp_path):
    """AC-04 com CLI real (Alto 3): o comando que nativos.py monta grava no opencode de verdade o formato que
    fakes.py imita. Medido em 26/11/2026 numa HOME descartável; só configuração, nenhum modelo."""
    if shutil.which("opencode") is None:
        pytest.skip("opencode não está no PATH")
    xdg = tmp_path / "xdg"
    env = {**os.environ, "HOME": str(tmp_path / "home"), "XDG_CONFIG_HOME": str(xdg / "config"),
           "XDG_DATA_HOME": str(xdg / "data"), "XDG_CACHE_HOME": str(xdg / "cache"),
           "XDG_STATE_HOME": str(xdg / "state")}
    ctx = montar_ctx(tmp_path, "opencode-real")
    cfg = xdg / "config" / "opencode" / "opencode.jsonc"
    ctx.opencode_jsonc = cfg

    def real(argv):
        return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60, env=env)

    e = {"transporte": "stdio", "comando": "echo", "args": ["ola"], "url": None,
         "env": {"CHAVE_FICTICIA": "valor-ficticio-123"}}
    r = real(N.argv_adicionar("opencode", "agata-ficticio", e))
    assert r.returncode == 0, r.stderr[-300:]
    assert N.ler_mcp("opencode", ctx) == {"agata-ficticio": e}
    # formato real: mcp.<nome> = {type: local, command: [cmd, args...], environment: {...}}, igual ao que fakes.py grava
    bruto = json.loads(N.sem_comentarios_jsonc(cfg.read_text(encoding="utf-8")))
    assert bruto["mcp"]["agata-ficticio"] == {"type": "local", "command": ["echo", "ola"],
                                              "environment": {"CHAVE_FICTICIA": "valor-ficticio-123"}}
    # nome existente é sobrescrito (medido): a segunda rodada troca os argumentos
    assert real(N.argv_adicionar("opencode", "agata-ficticio", {**e, "args": ["outro"]})).returncode == 0
    assert N.ler_mcp("opencode", ctx)["agata-ficticio"]["args"] == ["outro"]
    # sem remove medido no opencode (L6): o sync não tenta remover por comando
    assert N.argv_remover("opencode", "agata-ficticio") is None
