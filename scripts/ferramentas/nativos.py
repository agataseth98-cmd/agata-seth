#!/usr/bin/env python3
"""Leitura e escrita nativa das três CLIs (lote ferramentas-unificadas-26-11).

Escrita de MCP só pelos comandos nativos (A1), que preservam o que não nomeiam (medido: o opencode
mantém comentários e chaves; o claude recusa nome existente, por isso o sync remove antes):
  claude:   claude mcp add -s user ... / claude mcp remove -s user <nome>   (~/.claude.json, mcpServers)
  codex:    codex mcp add ... / codex mcp remove <nome>                    (config.toml, mcp_servers)
  opencode: opencode mcp add ... (sobrescreve; sem remove: L6)             (opencode.jsonc, mcp)
Leitura só para comparar e hashear. O hash guarda SHA-256 de cada valor de env, nunca o valor.
"""
from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path


class ErroConfig(ValueError):
    """Config nativa não lê. O sync aborta antes da primeira escrita (AC-14)."""


def _h(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def sem_comentarios_jsonc(texto: str) -> str:
    """Remove // e /* */ fora de strings e vírgula final antes de } ou ]."""
    saida: list[str] = []
    i, n, em_texto = 0, len(texto), False
    while i < n:
        c = texto[i]
        if em_texto:
            saida.append(c)
            if c == "\\" and i + 1 < n:
                saida.append(texto[i + 1])
                i += 2
                continue
            if c == '"':
                em_texto = False
            i += 1
            continue
        if c == '"':
            em_texto = True
            saida.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and texto[i + 1] == "/":
            fim = texto.find("\n", i)
            i = n if fim < 0 else fim
            continue
        if c == "/" and i + 1 < n and texto[i + 1] == "*":
            fim = texto.find("*/", i + 2)
            if fim < 0:
                raise ErroConfig("jsonc: comentário de bloco sem fechamento")
            i = fim + 2
            continue
        if c == ",":
            j = i + 1
            while j < n and texto[j] in " \t\r\n":
                j += 1
            if j < n and texto[j] in "}]":
                i += 1
                continue
        saida.append(c)
        i += 1
    return "".join(saida)


def _json(caminho: Path, jsonc: bool = False) -> dict:
    try:
        texto = caminho.read_text(encoding="utf-8")
        if jsonc:
            texto = sem_comentarios_jsonc(texto)
        dados = json.loads(texto) if texto.strip() else {}
    except (OSError, ValueError):
        raise ErroConfig(f"{caminho.name} não lê como {'JSONC' if jsonc else 'JSON'}") from None
    if not isinstance(dados, dict):
        raise ErroConfig(f"{caminho.name}: o topo não é um mapa")
    return dados


def _entrada(transporte: str, comando, args, url, env) -> dict:
    return {
        "transporte": transporte,
        "comando": comando,
        "args": [str(a) for a in (args or [])],
        "url": url,
        "env": {str(k): str(v) for k, v in (env or {}).items()},
    }


def _mapa(bruto, onde: str) -> dict:
    if bruto is None:
        return {}
    if not isinstance(bruto, dict):
        raise ErroConfig(f"{onde}: não é um mapa")
    return bruto


def _ler_claude(p: Path) -> dict:
    if not p.exists():
        return {}
    servidores = _mapa(_json(p).get("mcpServers"), "claude: mcpServers")
    saida = {}
    for nome, s in servidores.items():
        if not isinstance(s, dict):
            raise ErroConfig("claude: uma entrada de mcpServers não é mapa")
        tipo = s.get("type", "stdio")
        if tipo == "stdio":
            saida[nome] = _entrada("stdio", s.get("command"), s.get("args"), None, s.get("env"))
        else:
            saida[nome] = _entrada(str(tipo), None, None, s.get("url"), None)
    return saida


def _ler_codex(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        dados = tomllib.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ErroConfig("codex: config.toml não lê como TOML") from None
    servidores = _mapa(dados.get("mcp_servers"), "codex: mcp_servers")
    saida = {}
    for nome, s in servidores.items():
        if not isinstance(s, dict):
            raise ErroConfig("codex: uma entrada de mcp_servers não é tabela")
        if "url" in s:
            saida[nome] = _entrada("http", None, None, s.get("url"), None)
        else:
            saida[nome] = _entrada("stdio", s.get("command"), s.get("args"), None, s.get("env"))
    return saida


def _ler_opencode(p: Path) -> dict:
    if not p.exists():
        return {}
    servidores = _mapa(_json(p, jsonc=True).get("mcp"), "opencode: mcp")
    saida = {}
    for nome, s in servidores.items():
        if not isinstance(s, dict):
            raise ErroConfig("opencode: uma entrada de mcp não é mapa")
        if s.get("type") == "remote":
            saida[nome] = _entrada("http", None, None, s.get("url"), None)
        else:
            cmd = s.get("command") or []
            if not isinstance(cmd, list):
                raise ErroConfig("opencode: command não é lista")
            saida[nome] = _entrada(
                "stdio", cmd[0] if cmd else None, cmd[1:], None, s.get("environment")
            )
    return saida


def caminho_nativo(cli: str, ctx) -> Path:
    if cli == "claude":
        return ctx.claude_json
    if cli == "codex":
        return ctx.codex_dir / "config.toml"
    if cli == "opencode":
        return ctx.opencode_jsonc
    raise ErroConfig(f"CLI desconhecida: {cli}")


def ler_mcp(cli: str, ctx) -> dict:
    """nome -> {transporte, comando, args, url, env}. O env traz valores: o chamador não os imprime."""
    if cli == "claude":
        return _ler_claude(ctx.claude_json)
    if cli == "codex":
        return _ler_codex(ctx.codex_dir / "config.toml")
    if cli == "opencode":
        return _ler_opencode(ctx.opencode_jsonc)
    raise ErroConfig(f"CLI desconhecida: {cli}")


def hash_entrada(e: dict) -> str:
    """Compara só os campos que o sync controla. Valor de env entra como SHA-256 dele."""
    base = {
        "transporte": e.get("transporte"),
        "comando": e.get("comando"),
        "args": list(e.get("args") or []),
        "url": e.get("url"),
        "env": {k: _h(str(v)) for k, v in sorted((e.get("env") or {}).items())},
    }
    return _h(json.dumps(base, sort_keys=True, ensure_ascii=False))


def argv_adicionar(cli: str, nome: str, e: dict) -> list[str]:
    """`e` = {transporte, comando, args, url, env (valores resolvidos)}."""
    if e["transporte"] == "http":
        if cli == "claude":
            return ["claude", "mcp", "add", "-s", "user", "-t", "http", nome, e["url"]]
        if cli == "codex":
            return ["codex", "mcp", "add", nome, "--url", e["url"]]
        return ["opencode", "mcp", "add", nome, "--url", e["url"], "--pure", "--log-level", "ERROR"]
    cmd = [e["comando"], *e["args"]]
    env_claude = [y for k, v in e.get("env", {}).items() for y in ("-e", f"{k}={v}")]
    env_outro = [y for k, v in e.get("env", {}).items() for y in ("--env", f"{k}={v}")]
    if cli == "claude":
        return ["claude", "mcp", "add", "-s", "user", nome, *env_claude, "--", *cmd]
    if cli == "codex":
        return ["codex", "mcp", "add", nome, *env_outro, "--", *cmd]
    return ["opencode", "mcp", "add", nome, *env_outro, "--pure", "--log-level", "ERROR", "--", *cmd]


def argv_remover(cli: str, nome: str) -> list[str] | None:
    """None quando a CLI não tem remoção medida (opencode: L6)."""
    if cli == "claude":
        return ["claude", "mcp", "remove", "-s", "user", nome]
    if cli == "codex":
        return ["codex", "mcp", "remove", nome]
    return None
