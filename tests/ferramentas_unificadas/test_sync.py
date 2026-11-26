"""AC-03 a AC-08 e AC-14: sincronização (idempotência, merge, adoção, ponteiro, backup, config inválida)."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess

import pytest
from ferr_helpers import entrada_teste, escrever_overlay, montar_ctx

import estado as E
import nativos as N
import sincronizar as SYNC


def _estado_nativo(ctx) -> dict:
    return {cli: N.ler_mcp(cli, ctx) for cli in ("claude", "codex", "opencode")}


def _sha_nativos(ctx) -> dict:
    arquivos = {"claude": ctx.claude_json, "codex": ctx.codex_dir / "config.toml", "opencode": ctx.opencode_jsonc}
    return {k: (hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None) for k, p in arquivos.items()}


def _sync(ctx, **kw) -> tuple[int, list[str]]:
    saida: list[str] = []
    rc = SYNC.sincronizar(ctx, imprimir=saida.append, **kw)
    return rc, saida


def test_sync_duas_rodadas_zero_diff(ctx, fake):
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})
    rc, _ = _sync(ctx)
    assert rc == 0
    antes = _sha_nativos(ctx)
    escritas_antes = fake.escritas
    rc, saida = _sync(ctx)
    assert rc == 0
    assert fake.escritas == escritas_antes, "segunda rodada chamou comando nativo de escrita"
    assert _sha_nativos(ctx) == antes, "segunda rodada alterou arquivo nativo"
    assert any("0 mudança(s)" in linha for linha in saida)


def test_mcp_overlay_aparece_nos_tres_nativos(ctx, fake):
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})
    rc, _ = _sync(ctx)
    assert rc == 0
    estado = _estado_nativo(ctx)
    for cli in ("claude", "codex", "opencode"):
        assert "agata-teste" in estado[cli], cli
        entrada = estado[cli]["agata-teste"]
        assert entrada["comando"] == "echo" and entrada["args"] == ["ola"], cli
        # o valor da variável foi ao nativo, pelo ambiente; não veio da fonte
        assert entrada["env"] == {"AGATA_TESTE_VAR": "valor-de-teste-nao-vai-a-fonte"}, cli
    assert "valor-de-teste" not in (ctx.raiz / "config" / "ferramentas" / "mcp.yml").read_text()


def test_sync_preserva_entrada_nao_gerenciada(ctx, fake):
    # entradas que o Humano já tinha nas três CLIs, fora da fonte e do manifest
    ctx.claude_json.write_text(json.dumps({"mcpServers": {"intrusa": {"type": "stdio", "command": "x", "args": []}}}))
    ctx.codex_dir.mkdir(parents=True, exist_ok=True)
    ctx.codex_dir.joinpath("config.toml").write_text('[mcp_servers.intrusa-codex]\ncommand = "y"\nargs = []\n')
    ctx.opencode_jsonc.parent.mkdir(parents=True, exist_ok=True)
    ctx.opencode_jsonc.write_text('// meu comentário\n{"mcp": {"intrusa-oc": {"type": "remote", "url": "http://127.0.0.1:9/mcp"}}}\n')
    antes = _estado_nativo(ctx)
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})
    rc, _ = _sync(ctx)
    assert rc == 0
    depois = _estado_nativo(ctx)
    assert depois["claude"]["intrusa"] == antes["claude"]["intrusa"]
    assert depois["codex"]["intrusa-codex"] == antes["codex"]["intrusa-codex"]
    assert depois["opencode"]["intrusa-oc"] == antes["opencode"]["intrusa-oc"]
    assert "// meu comentário" in ctx.opencode_jsonc.read_text(), "comentário do opencode.jsonc se perdeu"


def test_sync_nao_adota_sem_flag(ctx, fake):
    # o nativo já tem agata-teste com outro comando, e nada no manifest diz que é nosso
    ctx.claude_json.write_text(json.dumps({"mcpServers": {"agata-teste": {"type": "stdio", "command": "outro", "args": []}}}))
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})
    rc, saida = _sync(ctx)
    assert rc == 0
    assert _estado_nativo(ctx)["claude"]["agata-teste"]["comando"] == "outro", "sync adotou sem adotar: true"
    assert "claude|mcp|agata-teste" not in E.ler_manifest(ctx)["entradas"]
    assert any("nao_adotado" in linha for linha in saida)
    # com adotar: true, a mesma entrada passa a ser gerenciada
    escrever_overlay(ctx, {"mcp": [entrada_teste(adotar=True)]})
    rc, _ = _sync(ctx)
    assert rc == 0
    assert _estado_nativo(ctx)["claude"]["agata-teste"]["comando"] == "echo"
    assert "claude|mcp|agata-teste" in json.loads((ctx.base / "gerenciado.json").read_text())["entradas"]


def test_skill_arranque_ponteiro_claude_codex(ctx, fake):
    rc, _ = _sync(ctx)
    assert rc == 0
    alvo = (ctx.checkout / ".agents" / "skills" / "agata-arranque").resolve()
    for pasta in (ctx.claude_skills, ctx.codex_skills):
        link = pasta / "agata-arranque"
        assert link.is_symlink(), pasta
        assert os.path.realpath(link) == str(alvo), pasta
        texto = (link / "SKILL.md").read_text(encoding="utf-8")
        assert texto.startswith("---\nname: agata-arranque\n"), pasta
    assert fake.chamadas == [], "skill é ponteiro: nenhum comando nativo de MCP deveria rodar"


def test_sync_backup_600_antes_de_escrever(ctx, fake):
    ctx.claude_json.write_text(json.dumps({"mcpServers": {}}))
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})
    visto = {}

    def ao_chamar(argv):
        if "backup" in visto:
            return
        raiz = ctx.base / "backup"
        visto["backup"] = sorted(p.name for p in raiz.iterdir()) if raiz.exists() else []
        if raiz.exists():
            pasta = next(raiz.iterdir())
            copia = pasta / "claude.json"
            visto["copia_modo"] = stat.S_IMODE(copia.stat().st_mode) if copia.exists() else None
            visto["pasta_modo"] = stat.S_IMODE(pasta.stat().st_mode)

    fake.ao_chamar = ao_chamar
    rc, _ = _sync(ctx)
    assert rc == 0
    assert visto["backup"], "nenhum backup existia quando a primeira escrita nativa começou"
    assert visto["copia_modo"] == 0o600
    assert visto["pasta_modo"] == 0o700


def test_sync_aborta_config_invalida_sem_escrita(ctx, fake):
    ctx.claude_json.write_text("{ isto nao e json")
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})
    conteudo = ctx.claude_json.read_bytes()
    rc, saida = _sync(ctx)
    assert rc == 2
    assert fake.chamadas == [], "comando nativo foi chamado com config inválida"
    assert ctx.claude_json.read_bytes() == conteudo
    assert not (ctx.base / "backup").exists(), "backup criado mesmo sem escrita"
    assert any("ERRO" in linha and "claude.json" in linha for linha in saida)


def test_timeout_nao_vaza_segredo(tmp_path, monkeypatch):
    """Alto 4 (revisão independente): TimeoutExpired carrega o argv, e o argv leva K=valor de env.
    Nada disso pode sair na saída do sync nem na mensagem da exceção."""
    segredo = "segredo-timeout-5a4b3c2d"
    monkeypatch.setenv("AGATA_TESTE_VAR", segredo)
    ctx = montar_ctx(tmp_path, "timeout")
    ctx.runner = E.executar_cli  # o runner de verdade; só o subprocess é trocado
    escrever_overlay(ctx, {"mcp": [entrada_teste()]})

    def estoura_prazo(argv, **kw):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=120)

    monkeypatch.setattr(E.subprocess, "run", estoura_prazo)
    argv_com_segredo = ["claude", "mcp", "add", "-s", "user", "agata-teste", "-e", f"AGATA_TESTE_VAR={segredo}",
                        "--", "echo"]
    with pytest.raises(E.ErroComando) as erro:
        E.executar_cli(argv_com_segredo)
    assert segredo not in str(erro.value)
    saida: list[str] = []
    rc = SYNC.sincronizar(ctx, imprimir=saida.append)
    texto = "\n".join(saida)
    assert rc == 2
    assert "ERRO" in texto and "sem resposta no prazo" in texto
    assert segredo not in texto
    assert "AGATA_TESTE_VAR=" not in texto
