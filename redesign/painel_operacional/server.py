#!/usr/bin/env python3
"""Painel operacional local da Agata. HTTP de leitura, preso a loopback."""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
WEB = Path(__file__).resolve().parent
BIND = "127.0.0.1"
PORT = 20146
VERIFIER_URL = "http://127.0.0.1:20141/verificar"
REFRESH_SECONDS = 60
FRESH_SECONDS = 60
CACHE_SECONDS = 3
# Formação em recortes: a Wiki só é liberada depois do contrato de busca (plano reconciliado, dependências 1-6).
WIKI_LIBERADA = False
LIMITE_RESPOSTA_VERIFICADOR = 262144
ALLOWED_ORIGIN = f"http://{BIND}:{PORT}"
WIKI_RESULT_MAX = 12000

# Allowlist de unidades de usuário. A API não aceita nome de unidade do cliente.
SERVICE_ALLOWLIST = (
    "omniroute.service",
    "omniroute-sanitizer.service",
    "seth-gateway.service",
    "seth-verificador.service",
)

_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/prototipo": ("prototipo.html", "text/html; charset=utf-8"),
    "/prototipo.css": ("prototipo.css", "text/css; charset=utf-8"),
    "/prototipo.js": ("prototipo.js", "text/javascript; charset=utf-8"),
}
_STATUS_CACHE: dict | None = None
_STATUS_CACHE_AT: float | None = None


def _now() -> datetime:
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


def _stamp(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _reading_window() -> tuple[str, str]:
    observed = _now()
    return _stamp(observed), _stamp(observed + timedelta(seconds=FRESH_SECONDS))


def _same_origin_request(fetch_site: str | None, origin: str | None) -> bool:
    if fetch_site and fetch_site not in {"same-origin", "none"}:
        return False
    return not origin or origin == ALLOWED_ORIGIN


def _verify(command: str, **arguments: object) -> str:
    """Consulta comandos fixos do verificador; argumentos nunca vêm do navegador."""
    allowed = {"unidade", "git_status", "git_log"}
    if WIKI_LIBERADA:
        allowed |= {"busca_texto", "busca_semantica"}
    if command not in allowed:
        raise ValueError("comando não permitido pelo painel")
    payload = {"comando": command, **arguments}
    request = urllib.request.Request(
        VERIFIER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    timeout = 95 if command == "busca_semantica" else 5
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(LIMITE_RESPOSTA_VERIFICADOR + 1)
        if len(raw) > LIMITE_RESPOSTA_VERIFICADOR:
            raise ValueError("resposta do verificador acima do limite")
        result = json.loads(raw.decode("utf-8"))
    output = result.get("saida")
    if not isinstance(output, str):
        raise ValueError("o verificador não retornou uma saída")
    return output


def _command_body(output: str) -> str:
    if "[CORTADO" in output:
        raise ValueError("a saída do verificador foi cortada")
    _, separator, body = output.partition("\n\n")
    if not separator:
        raise ValueError("a saída do verificador está incompleta")
    return body


def _parse_pairs(text: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            pairs[key] = value
    return pairs


def _parse_git_status(status_text: str, branch: str, head: str) -> dict:
    lines = status_text.splitlines()
    header = lines[0] if lines and lines[0].startswith("## ") else ""
    changed = [line for line in lines[1:] if line.strip()] if header else [
        line for line in lines if line.strip()
    ]
    relation = "no_upstream"
    if "..." in header:
        relation = "tracking_up_to_date"
        if "ahead " in header or "behind " in header:
            relation = "tracking_diverged"

    dirty = len(changed)
    return {
        "branch": branch or "detached",
        "head": head,
        "dirty_count": dirty,
        "working_tree": "dirty" if dirty else "clean",
        "tracking": relation,
        "state": "warning" if dirty or relation == "tracking_diverged" else "ok",
        "source": "git",
        "source_ref": "git status --porcelain=v1 -b; git rev-parse HEAD",
    }


def _git_snapshot() -> dict:
    try:
        status_output = _verify("git_status")
        status_body = _command_body(status_output)
        log_body = _command_body(_verify("git_log", n=1))
    except (OSError, TimeoutError, ValueError, urllib.error.URLError):
        observed_at, fresh_until = _reading_window()
        return {
            "state": "unknown",
            "source": "seth-verificador",
            "source_ref": "git_status + git_log n=1",
            "observed_at": observed_at,
            "fresh_until": fresh_until,
            "error": "leitura local do Git indisponível",
        }

    first = next((line for line in log_body.splitlines() if line.strip()), "")
    head = first.split(maxsplit=1)[0] if first else ""
    if not head or any(char not in "0123456789abcdef" for char in head.lower()):
        observed_at, fresh_until = _reading_window()
        return {
            "state": "unknown",
            "source": "seth-verificador",
            "source_ref": "git_status + git_log n=1",
            "observed_at": observed_at,
            "fresh_until": fresh_until,
            "error": "HEAD não veio na leitura do verificador",
        }

    status_lines = status_body.splitlines()
    header = status_lines[0] if status_lines else ""
    branch = header[3:].partition("...")[0] if header.startswith("## ") else "detached"
    value = _parse_git_status(status_body, branch, head)
    observed_at, fresh_until = _reading_window()
    value.update(
        {
            "observed_at": observed_at,
            "fresh_until": fresh_until,
            "commit": head,
            "source": "seth-verificador",
            "source_ref": "git_status + git_log n=1",
        }
    )
    return value


def _service_snapshot(unit: str) -> dict:
    try:
        output = _verify("unidade", consulta=unit)
        values = _parse_pairs(_command_body(output))
    except (OSError, TimeoutError, ValueError, urllib.error.URLError):
        observed_at, fresh_until = _reading_window()
        values = {}
    else:
        observed_at, fresh_until = _reading_window()

    required = ("LoadState", "ActiveState", "SubState")
    if any(key not in values for key in required):
        return {
            "unit": unit,
            "state": "unknown",
            "source": "seth-verificador",
            "source_ref": "unidade:" + unit,
            "observed_at": observed_at,
            "fresh_until": fresh_until,
            "error": "leitura da unidade indisponível",
        }

    active = values["ActiveState"]
    load = values["LoadState"]
    state = "ok" if load == "loaded" and active == "active" else "warning"
    return {
        "unit": unit,
        "state": state,
        "load_state": load,
        "active_state": active,
        "sub_state": values["SubState"],
        "source": "seth-verificador",
        "source_ref": "unidade:" + unit,
        "observed_at": observed_at,
        "fresh_until": fresh_until,
    }


def _overall_state(states: list[str]) -> str:
    if any(state == "unknown" for state in states):
        return "unknown"
    if any(state == "warning" for state in states):
        return "warning"
    return "ok"


def collect() -> dict:
    services = [_service_snapshot(unit) for unit in SERVICE_ALLOWLIST]
    git = _git_snapshot()
    observed_at, fresh_until = _reading_window()
    overall = _overall_state([item["state"] for item in services])
    return {
        "schema_version": 1,
        "state": overall,
        "scope": "quatro unidades fixas e Git local via seth-verificador",
        "commit": git.get("commit"),
        "observed_at": observed_at,
        "fresh_until": fresh_until,
        "refresh_seconds": REFRESH_SECONDS,
        "services": services,
        "git": git,
    }


def _cached_status() -> dict:
    """Reusa por poucos segundos respostas GET sequenciais do HTTPServer simples."""
    global _STATUS_CACHE, _STATUS_CACHE_AT
    now = time.monotonic()
    if (
        _STATUS_CACHE is not None
        and _STATUS_CACHE_AT is not None
        and now - _STATUS_CACHE_AT < CACHE_SECONDS
    ):
        return _STATUS_CACHE
    _STATUS_CACHE = collect()
    _STATUS_CACHE_AT = time.monotonic()
    return _STATUS_CACHE


def _wiki_search(query: str, mode: str) -> dict:
    """Executa apenas os dois comandos de busca aprovados, com a consulta como dado."""
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError("query must contain 1-200 characters")
    if not isinstance(mode, str) or mode not in {"texto", "sentido", "ambos"}:
        raise ValueError("invalid search mode")
    commands = ("busca_texto", "busca_semantica") if mode == "ambos" else (
        ("busca_texto",) if mode == "texto" else ("busca_semantica",)
    )
    results = []
    for command in commands:
        try:
            output = _verify(command, consulta=query.strip(), **(
                {"n": 8} if command == "busca_semantica" else {}
            ))
            if len(output) > WIKI_RESULT_MAX:
                total = len(output)
                percent = round(WIKI_RESULT_MAX / total * 100)
                output = output[:WIKI_RESULT_MAX] + (
                    f"\n\n[TRUNCADO: mostrando {WIKI_RESULT_MAX} de {total} caracteres "
                    f"(~{percent}%). O restante não foi lido; não conclua nada sobre ele.]"
                )
            results.append({"command": command, "output": output, "error": None})
        except (OSError, TimeoutError, ValueError, urllib.error.URLError) as error:
            results.append({"command": command, "output": "", "error": str(error)})
    return {
        "schema_version": 1,
        "observed_at": _stamp(_now()),
        "source": "seth-verificador",
        "source_ref": "busca_texto/busca_semantica · vault prioritário e extras/",
        "results": results,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "AgataPainel/1"

    def log_message(self, _format: str, *args) -> None:
        # Não grava conteúdo de requisição em log.
        return

    def _send(
        self,
        status: int,
        content_type: str,
        body: bytes,
        extra_headers: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for name, value in extra_headers:
            self.send_header(name, value)
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self'; base-uri 'none'; "
            "frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.headers.get("Host") != f"{BIND}:{PORT}":
            return self._send(421, "text/plain; charset=utf-8", b"invalid host")
        if self.path == "/api/status":
            if not _same_origin_request(
                self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")
            ):
                return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
            body = json.dumps(_cached_status(), ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)

        asset = _ASSETS.get(self.path)
        if asset is None:
            return self._send(404, "text/plain; charset=utf-8", b"not found")
        name, content_type = asset
        try:
            body = (WEB / name).read_bytes()
        except OSError:
            return self._send(500, "text/plain; charset=utf-8", b"asset unavailable")
        self._send(200, content_type, body)

    def do_POST(self) -> None:
        if self.headers.get("Host") != f"{BIND}:{PORT}":
            return self._send(421, "text/plain; charset=utf-8", b"invalid host")
        if self.path != "/api/wiki/search" or not WIKI_LIBERADA:
            return self._send(405, "text/plain; charset=utf-8", b"read only", (("Allow", "GET, POST"),))
        if not _same_origin_request(
            self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")
        ):
            return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > 4096:
            return self._send(413, "text/plain; charset=utf-8", b"request too large")
        try:
            payload = json.loads(self.rfile.read(int(raw_length)))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._send(400, "text/plain; charset=utf-8", b"invalid JSON")
        if not isinstance(payload, dict):
            return self._send(400, "text/plain; charset=utf-8", b"invalid search")
        query = payload.get("query")
        mode = payload.get("mode", "ambos")
        if not isinstance(query, str) or not query.strip() or len(query) > 200:
            return self._send(400, "text/plain; charset=utf-8", b"query must contain 1-200 characters")
        if not isinstance(mode, str) or mode not in {"texto", "sentido", "ambos"}:
            return self._send(400, "text/plain; charset=utf-8", b"invalid search mode")
        try:
            result = _wiki_search(query, mode)
        except ValueError:
            return self._send(400, "text/plain; charset=utf-8", b"invalid search")
        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        return self._send(200, "application/json; charset=utf-8", body)

    def do_PUT(self) -> None:
        return self._send(405, "text/plain; charset=utf-8", b"read only", (("Allow", "GET"),))

    def do_DELETE(self) -> None:
        return self._send(405, "text/plain; charset=utf-8", b"read only", (("Allow", "GET"),))


def _selftest() -> int:
    global _STATUS_CACHE, _STATUS_CACHE_AT, _verify, collect
    sample = "## main...origin/main\n M PROJETO.md\n?? reports/\n"
    git = _parse_git_status(sample, "main", "abc123def456")
    assert git["branch"] == "main"
    assert git["head"] == "abc123def456"
    assert git["dirty_count"] == 2
    assert git["state"] == "warning"
    assert "PROJETO.md" not in json.dumps(git)
    assert git["tracking"] == "tracking_up_to_date"

    diverged = _parse_git_status(
        "## main...origin/main [ahead 1, behind 2]\n", "main", "def456"
    )
    assert diverged["tracking"] == "tracking_diverged"
    assert diverged["state"] == "warning"

    pairs = _parse_pairs("LoadState=loaded\nActiveState=active\nSubState=running\n")
    assert pairs == {
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": "running",
    }
    assert SERVICE_ALLOWLIST == (
        "omniroute.service",
        "omniroute-sanitizer.service",
        "seth-gateway.service",
        "seth-verificador.service",
    )
    assert all(unit.endswith(".service") for unit in SERVICE_ALLOWLIST)
    assert _overall_state(["ok", "ok"]) == "ok"
    assert _overall_state(["ok", "warning"]) == "warning"
    assert _overall_state(["ok", "unknown"]) == "unknown"
    assert _same_origin_request("same-origin", ALLOWED_ORIGIN)
    assert _same_origin_request(None, None)
    assert not _same_origin_request("cross-site", ALLOWED_ORIGIN)
    assert not _same_origin_request("same-origin", "https://example.com")

    original_verify = _verify

    def fake_verify(command: str, **arguments: object) -> str:
        if command == "unidade":
            body = "LoadState=loaded\nActiveState=active\nSubState=running\n"
        elif command == "git_status":
            body = "## main...origin/main\n M README.md\n"
        elif command == "git_log":
            body = "abc123def456 mensagem de exemplo\n"
        elif command == "busca_texto":
            assert arguments == {"consulta": "wiki"}
            body = "resultado textual demonstrativo " + ("x" * (WIKI_RESULT_MAX + 1))
        elif command == "busca_semantica":
            assert arguments == {"consulta": "wiki", "n": 8}
            body = "resultado semântico demonstrativo"
        else:
            raise AssertionError("comando inesperado no selftest")
        return "comando permitido\n\n" + body

    _verify = fake_verify
    try:
        snapshot = collect()
        if WIKI_LIBERADA:
            wiki = _wiki_search("wiki", "ambos")
            assert [item["command"] for item in wiki["results"]] == ["busca_texto", "busca_semantica"]
            assert all(item["error"] is None for item in wiki["results"])
            assert "resultado textual" in wiki["results"][0]["output"]
            total_textual = len("comando permitido\n\nresultado textual demonstrativo " + ("x" * (WIKI_RESULT_MAX + 1)))
            assert f"TRUNCADO: mostrando {WIKI_RESULT_MAX} de {total_textual} caracteres" in wiki["results"][0]["output"]
            assert "resultado semântico" in wiki["results"][1]["output"]
            try:
                _wiki_search("x" * 201, "texto")
            except ValueError:
                pass
            else:
                raise AssertionError("busca acima de 200 caracteres não foi recusada")
            try:
                _wiki_search("wiki", "livre")
            except ValueError:
                pass
            else:
                raise AssertionError("modo de busca arbitrário não foi recusado")
    finally:
        _verify = original_verify

    assert snapshot["state"] == "ok"
    assert snapshot["git"]["state"] == "warning"
    assert snapshot["commit"] == "abc123def456"
    for reading in [*snapshot["services"], snapshot["git"]]:
        observed = datetime.fromisoformat(reading["observed_at"])
        valid_until = datetime.fromisoformat(reading["fresh_until"])
        assert valid_until - observed == timedelta(seconds=FRESH_SECONDS)
        assert reading.get("source_ref")
    assert "README.md" not in json.dumps(snapshot)

    original_collect = collect
    call_count = 0

    def fake_collect() -> dict:
        nonlocal call_count
        call_count += 1
        return {"schema_version": 1}

    collect = fake_collect
    _STATUS_CACHE = None
    _STATUS_CACHE_AT = None
    try:
        cached_first = _cached_status()
        cached_second = _cached_status()
        assert cached_first is cached_second
        assert call_count == 1
    finally:
        collect = original_collect
        _STATUS_CACHE = None
        _STATUS_CACHE_AT = None
    print("painel_operacional selftest: OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return _selftest()

    server = ThreadingHTTPServer((BIND, PORT), Handler)
    server.daemon_threads = True
    print(f"Painel somente leitura: http://{BIND}:{PORT}/")
    print("Parar com Ctrl-C. Nenhuma unidade systemd é instalada ou iniciada.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
