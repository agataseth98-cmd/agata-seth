"""AC-09 e AC-10: reversão pelo registro, com hash guard."""
from __future__ import annotations

import json

from ferr_helpers import entrada_teste, escrever_overlay, montar_ctx

import estado as E
import nativos as N
import reverter as R
import sincronizar as SYNC


def _estado_nativo(ctx) -> dict:
    return {cli: N.ler_mcp(cli, ctx) for cli in ("claude", "codex", "opencode")}


def _rodar(ctx, **kw):
    saida: list[str] = []
    rc = SYNC.sincronizar(ctx, imprimir=saida.append, **kw)
    assert rc == 0, saida
    return saida


def _ts_da_execucao(ctx) -> str:
    execs = R.listar(ctx)
    assert execs, "nenhuma execução registrada"
    return execs[-1]["ts"]


def test_reverter_restaura_estado_pre_sync(tmp_path, monkeypatch):
    monkeypatch.setenv("AGATA_TESTE_VAR", "valor-de-teste-reverter")
    # cenário 1: entrada nova. O nativo tinha uma entrada alheia, que tem de continuar igual.
    ctx = montar_ctx(tmp_path, "novo")
    ctx.claude_json.write_text(json.dumps({"mcpServers": {"intrusa": {"type": "stdio", "command": "x", "args": []}}}))
    # opencode.jsonc que já existia, com comentário: a reversão tem de devolver os bytes exatos (backup)
    ctx.opencode_jsonc.parent.mkdir(parents=True, exist_ok=True)
    ctx.opencode_jsonc.write_text('// meu comentário\n{"mcp": {}}\n', encoding="utf-8")
    antes = _estado_nativo(ctx)
    bytes_opencode_antes = ctx.opencode_jsonc.read_bytes()
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})
    _rodar(ctx)
    assert "agata-teste" in _estado_nativo(ctx)["claude"]
    assert (ctx.claude_skills / "agata-arranque").is_symlink(), "o sync deveria ter criado o ponteiro"
    rc = R.reverter(ctx, _ts_da_execucao(ctx), imprimir=lambda *_: None)
    assert rc == 0
    depois = _estado_nativo(ctx)
    assert depois["claude"] == antes["claude"]
    assert depois["codex"] == antes["codex"]
    assert depois["opencode"] == antes["opencode"]
    assert ctx.opencode_jsonc.read_bytes() == bytes_opencode_antes, "opencode.jsonc não voltou aos bytes de antes"
    assert "claude|mcp|agata-teste" not in E.ler_manifest(ctx)["entradas"]
    # o ponteiro saiu do lugar por mv para ~/agata-arquivo, nunca por rm
    assert not (ctx.claude_skills / "agata-arranque").is_symlink()
    assert list((ctx.home / "agata-arquivo").glob("ferramentas-*/claude-agata-arranque")), "ponteiro não foi arquivado"

    # cenário 2: entrada alheia com o mesmo nome. Com adotar: true, o sync a substitui; reverter devolve o valor anterior.
    # Aqui o opencode.jsonc não existia antes: a reversão tira o arquivo do lugar, sem apagá-lo.
    ctx2 = montar_ctx(tmp_path, "adotado")
    ctx2.claude_json.write_text(json.dumps({"mcpServers": {"agata-teste": {"type": "stdio", "command": "antigo", "args": ["a"]}}}))
    escrever_overlay(ctx2, {"mcp": [entrada_teste(adotar=True)]})
    _rodar(ctx2)
    assert _estado_nativo(ctx2)["claude"]["agata-teste"]["comando"] == "echo"
    rc = R.reverter(ctx2, _ts_da_execucao(ctx2), imprimir=lambda *_: None)
    assert rc == 0
    recuperado = _estado_nativo(ctx2)["claude"]["agata-teste"]
    assert recuperado["comando"] == "antigo" and recuperado["args"] == ["a"]
    assert not ctx2.opencode_jsonc.exists(), "opencode.jsonc que não existia continuou no lugar"
    assert list((ctx2.home / "agata-arquivo").glob("ferramentas-*/opencode.jsonc")), "arquivo não foi movido para o arquivo"


def test_reverter_recusa_arquivo_alterado(tmp_path, monkeypatch):
    monkeypatch.setenv("AGATA_TESTE_VAR", "valor-de-teste-reverter")
    ctx = montar_ctx(tmp_path, "alterado")
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})
    _rodar(ctx)
    ts = _ts_da_execucao(ctx)
    # depois do sync, alguém muda a entrada no nativo do Claude
    dados = json.loads(ctx.claude_json.read_text())
    dados["mcpServers"]["agata-teste"]["command"] = "mudou-depois"
    ctx.claude_json.write_text(json.dumps(dados, indent=2))
    conteudo = ctx.claude_json.read_bytes()
    chamadas_antes = len(ctx.runner.chamadas)
    saida: list[str] = []
    rc = R.reverter(ctx, ts, imprimir=saida.append)
    assert rc == 3
    assert any("mudou depois do sync" in linha for linha in saida)
    assert len(ctx.runner.chamadas) == chamadas_antes, "reverter chamou comando nativo mesmo recusando"
    assert ctx.claude_json.read_bytes() == conteudo
    assert "claude|mcp|agata-teste" in E.ler_manifest(ctx)["entradas"], "manifest mudou numa recusa"
