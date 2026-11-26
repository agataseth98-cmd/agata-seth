"""Imitação em memória das três CLIs, nos formatos medidos em 26/11/2026 numa HOME descartável.

claude:   `claude mcp add -s user ...` grava mcpServers[nome] = {type, command, args, env} em ~/.claude.json;
          recusa nome existente ("already exists"); `claude mcp remove -s user <nome>`.
codex:    `codex mcp add <nome> --env K=V -- cmd` grava [mcp_servers.<nome>] em config.toml; `codex mcp remove`.
opencode: `opencode mcp add <nome> ...` grava mcp[nome] em opencode.jsonc, preserva comentários, sobrescreve nome;
          não tem remove (L6).
Nenhum processo real é criado: o runner devolve código de retorno e escreve nos arquivos da HOME de teste.
"""
from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "ferramentas"))
import nativos as N  # noqa: E402


def _rc(codigo: int = 0, texto: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=codigo, stdout="", stderr=texto)


def _parse_claude_add(args: list[str]):
    env: dict = {}
    posicionais: list[str] = []
    transporte, cmd = "stdio", None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "-s":
            i += 2
            continue
        if a == "-t":
            transporte = args[i + 1]
            i += 2
            continue
        if a == "-e":
            k, v = args[i + 1].split("=", 1)
            env[k] = v
            i += 2
            continue
        if a == "--":
            cmd = args[i + 1:]
            break
        posicionais.append(a)
        i += 1
    nome = posicionais[0]
    url = posicionais[1] if len(posicionais) > 1 else None
    return nome, transporte, env, url, cmd


def _toml(d: dict, prefixo: tuple = ()) -> str:
    def valor(v) -> str:
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, list):
            return "[" + ", ".join(valor(x) for x in v) + "]"
        return json.dumps(str(v), ensure_ascii=False)

    linhas = []
    if prefixo:
        linhas.append(f"[{'.'.join(prefixo)}]")
    for k, v in d.items():
        if not isinstance(v, dict):
            linhas.append(f"{k} = {valor(v)}")
    texto = "\n".join(linhas) + ("\n" if linhas else "")
    for k, v in d.items():
        if isinstance(v, dict):
            texto += "\n" + _toml(v, prefixo + (k,))
    return texto


class FakeCLIs:
    def __init__(self, home: Path):
        self.home = home
        self.chamadas: list[list[str]] = []
        self.escritas = 0
        self.ao_chamar = None  # gancho: recebe o argv antes de cada chamada
        self.claude_json = home / ".claude.json"
        self.codex_toml = home / ".codex" / "config.toml"
        self.opencode = home / ".config" / "opencode" / "opencode.jsonc"

    def __call__(self, argv: list[str]):
        self.chamadas.append(list(argv))
        if self.ao_chamar:
            self.ao_chamar(list(argv))
        if argv[0] == "claude":
            return self._claude(argv[1:])
        if argv[0] == "codex":
            return self._codex(argv[1:])
        if argv[0] == "opencode":
            return self._opencode(argv[1:])
        return _rc(127, "binário desconhecido")

    def _claude(self, args):
        d = json.loads(self.claude_json.read_text(encoding="utf-8")) if self.claude_json.exists() else {}
        servers = d.setdefault("mcpServers", {})
        # args = ["mcp", "add"|"remove", ...]
        if args[1] == "remove":
            nome = args[-1]
            if nome not in servers:
                return _rc(1, "not found")
            del servers[nome]
        elif args[1] == "add":
            nome, transporte, env, url, cmd = _parse_claude_add(args[2:])
            if nome in servers:
                return _rc(1, "already exists")
            if transporte == "http":
                servers[nome] = {"type": "http", "url": url}
            else:
                servers[nome] = {"type": "stdio", "command": cmd[0], "args": cmd[1:], "env": env}
        self.claude_json.parent.mkdir(parents=True, exist_ok=True)
        self.claude_json.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
        self.escritas += 1
        return _rc(0)

    def _codex(self, args):
        cfg = tomllib.loads(self.codex_toml.read_text(encoding="utf-8")) if self.codex_toml.exists() else {}
        servers = cfg.setdefault("mcp_servers", {})
        # args = ["mcp", "add"|"remove", nome, ...]
        if args[1] == "remove":
            nome = args[2]
            if nome not in servers:
                return _rc(1, "not found")
            del servers[nome]
        else:
            nome, resto = args[2], args[3:]
            if "--url" in resto:
                servers[nome] = {"url": resto[resto.index("--url") + 1]}
            else:
                env: dict = {}
                cmd = []
                i = 0
                while i < len(resto):
                    if resto[i] == "--env":
                        k, v = resto[i + 1].split("=", 1)
                        env[k] = v
                        i += 2
                        continue
                    if resto[i] == "--":
                        cmd = resto[i + 1:]
                        break
                    i += 1
                entrada = {"command": cmd[0], "args": cmd[1:]}
                if env:
                    entrada["env"] = env
                servers[nome] = entrada
        self.codex_toml.parent.mkdir(parents=True, exist_ok=True)
        self.codex_toml.write_text(_toml(cfg), encoding="utf-8")
        self.escritas += 1
        return _rc(0)

    def _opencode(self, args):
        texto = self.opencode.read_text(encoding="utf-8") if self.opencode.exists() else '{"$schema": "x"}'
        cabecalho = "".join(linha for linha in texto.splitlines(True) if linha.startswith("//"))
        d = json.loads(N.sem_comentarios_jsonc(texto))
        mcp = d.setdefault("mcp", {})
        # args = ["mcp", "add", nome, ...]; sobrescreve nome existente, como a CLI medida
        nome, resto = args[2], args[3:]
        if "--url" in resto:
            mcp[nome] = {"type": "remote", "url": resto[resto.index("--url") + 1]}
        else:
            env: dict = {}
            cmd: list = []
            i = 0
            while i < len(resto):
                if resto[i] == "--env":
                    k, v = resto[i + 1].split("=", 1)
                    env[k] = v
                    i += 2
                    continue
                if resto[i] == "--":
                    cmd = resto[i + 1:]
                    break
                i += 1
            entrada = {"type": "local", "command": cmd}
            if env:
                entrada["environment"] = env
            mcp[nome] = entrada
        self.opencode.parent.mkdir(parents=True, exist_ok=True)
        self.opencode.write_text(cabecalho + json.dumps(d, indent=2) + "\n", encoding="utf-8")
        self.escritas += 1
        return _rc(0)
