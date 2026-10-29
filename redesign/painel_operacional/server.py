#!/usr/bin/env python3
"""Painel operacional local da Agata. HTTP de leitura, preso a loopback."""
from __future__ import annotations

import argparse
import hashlib
import http.client
import collections
import json
import os
import socket
import re
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlparse
from concurrent.futures import ThreadPoolExecutor
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
WIKI_LIBERADA = True
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

# Só unidades fixas; a interface nunca escolhe argumentos do systemctl.
TIMER_ALLOWLIST = ("agata-manutencao.timer", "agata-vault-inbox.timer")
TIMER_SERVICES = {"agata-manutencao.timer": "agata-manutencao.service",
                  "agata-vault-inbox.timer": "agata-vault-inbox.service"}
MAINTENANCE_STATE = Path.home() / ".cache/agata/janela/state.json"
INTEGRATION_ALLOWLIST = (
    "piper-tts.service", "openvino-whisper.service", "openvino-embeddings.service",
    "obsidian-ro-proxy.service", "discord-mcp.service", "navegador-mcp.service",
    "laya-roteador.service", "seth-escriba.service",
)
_STATUS_LOCK = threading.Lock()
_WIKI_LOCK = threading.BoundedSemaphore(1)
_RELAY_LOCK = threading.BoundedSemaphore(1)
_RELAY_RATE_LOCK = threading.Lock()
_RELAY_REQUESTS: collections.deque[float] = collections.deque()
_RELAY_RATE_WINDOW_SECONDS = 60
_RELAY_RATE_LIMIT = 60
_SEM_CONVERSA_EM_CURSO = threading.BoundedSemaphore(1)
_PROPOSAL_LOCK = threading.BoundedSemaphore(1)
_DETAILS_LOCK = threading.Lock()
_DETAILS_CACHE: dict | None = None
_DETAILS_CACHE_AT: float | None = None

_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/prototipo": ("prototipo.html", "text/html; charset=utf-8"),
    "/prototipo.css": ("prototipo.css", "text/css; charset=utf-8"),
    "/prototipo.js": ("prototipo.js", "text/javascript; charset=utf-8"),
    "/conselho-rede": ("conselho-rede/index.html", "text/html; charset=utf-8"),
    "/conselho-rede/": ("conselho-rede/index.html", "text/html; charset=utf-8"),
    "/conselho-rede/style.css": ("conselho-rede/style.css", "text/css; charset=utf-8"),
    "/conselho-rede/app.js": ("conselho-rede/app.js", "text/javascript; charset=utf-8"),
    "/assets/agata-portrait.png": ("assets/agata-portrait.png", "image/png"),
}
_STATUS_CACHE: dict | None = None
_STATUS_CACHE_AT: float | None = None
RELAY_CLIENT_ID = "agata-relay-v2"
_COUNCIL_LOCK = threading.Lock()
_COUNCIL = None
_COUNCIL_CONFLICT = ValueError
_COUNCIL_DATA_DIR = Path(os.environ.get(
    "AGATA_RELAY_COUNCIL_DATA_DIR",
    str(Path.home() / ".local/share/agata/painel-conselho/official"),
))
_COUNCIL_LEGACY_HISTORY = Path.home() / ".local/share/agata/painel-conselho/history.jsonl"


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


def _relay_modules():
    """Carrega contrato e persistência locais; nenhum módulo faz chamada externa."""
    for directory in (ROOT / "redesign/router", WEB):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    import cache_conselho
    import relay_catalog
    import relay_council_contract
    import sanitizar
    return cache_conselho, relay_catalog, relay_council_contract, sanitizar


def _relay_rate_limited() -> bool:
    now = time.monotonic()
    with _RELAY_RATE_LOCK:
        while (_RELAY_REQUESTS
               and now - _RELAY_REQUESTS[0] >= _RELAY_RATE_WINDOW_SECONDS):
            _RELAY_REQUESTS.popleft()
        if len(_RELAY_REQUESTS) >= _RELAY_RATE_LIMIT:
            return True
        _RELAY_REQUESTS.append(now)
        return False


class RelayEvaluationTooLarge(ValueError):
    """Avaliação excede o limite de uma entrada do cache compartilhado."""


class RelayDailyQuotaExceeded(ValueError):
    """Cache comum atingiu a quota diária de escrita."""


class RelayIdempotencyConflict(ValueError):
    """Uma reentrega reutilizou a chave com conteúdo diferente."""


def _relay_store(payload: dict) -> dict:
    cache, _catalog, contract, sanitizer = _relay_modules()
    if "timestamp" not in payload:
        raise ValueError("timestamp is required for idempotent result delivery")
    try:
        normalized = contract.normalize_evaluation(payload)
    except RecursionError as exc:
        raise ValueError("evaluation nesting limit exceeded") from exc
    provider = _catalog.PROVIDER_BY_ID[normalized["provider"]]
    expected_mode = {"official_api_only": "official_api", "manual_only": "manual"}.get(
        provider["access_mode"]
    )
    if normalized["access_mode"] != expected_mode:
        raise ValueError("access mode does not match provider catalog")
    try:
        sanitizer.sanitizar_payload(normalized)
    except sanitizer.SegredoNoPayload as exc:
        raise ValueError("sensitive content rejected") from exc
    task_key = hashlib.sha256(
        f"{normalized['provider']}:{normalized['task_id']}:{normalized['timestamp']}".encode("utf-8")
    ).hexdigest()
    persisted = {**normalized, "task_id": task_key}
    record = json.dumps(persisted, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(record) > cache.MAX_TEXTO:
        raise RelayEvaluationTooLarge("evaluation exceeds shared-cache entry limit")
    try:
        return cache.anotar(
            autor=f"relay:{normalized['provider']}",
            texto=record,
            tipo="nota",
            fonte="RelayCouncil",
            idempotency_key=f"relay-{task_key}",
        )
    except cache.LimiteDiarioAtingido as exc:
        raise RelayDailyQuotaExceeded from exc
    except cache.ConflitoIdempotencia as exc:
        raise RelayIdempotencyConflict from exc


def _council_clean(text: str) -> str:
    cache, _catalog, _contract, _sanitizer = _relay_modules()
    return cache.filtrar(text)


def _council_execute(tool: str, args: dict, text: str) -> str:
    """Executa apenas ferramentas locais de leitura, depois da aprovação humana."""
    cache, _catalog, _contract, _sanitizer = _relay_modules()
    if tool == "SEARCH":
        result = _wiki_search(args["canon"], "ambos")
    elif tool == "STATE":
        result = collect()
    elif tool == "CACHE":
        result = cache.ler(args["ler"])
    elif tool == "AUDIT":
        completed = subprocess.run(
            [sys.executable, str(ROOT / "redesign/router/auditoria_turno.py"), "--verificar"],
            input=text, text=True, capture_output=True, timeout=10, cwd=ROOT,
            check=False,
        )
        result = {"returncode": completed.returncode, "stdout": completed.stdout,
                  "stderr": completed.stderr}
    elif tool == "DELIVER":
        result = {"state": "requires_human_review", "text": text,
                  "message": "O painel não executa código nem aplica alterações."}
    else:
        raise ValueError("ferramenta não permitida")
    return json.dumps(result, ensure_ascii=False, default=str)


def _council_state():
    global _COUNCIL, _COUNCIL_CONFLICT
    if _COUNCIL is None:
        with _COUNCIL_LOCK:
            if _COUNCIL is None:
                for directory in (WEB, ROOT / "redesign/router"):
                    path = str(directory)
                    if path not in sys.path:
                        sys.path.insert(0, path)
                import conselho_rede
                _COUNCIL_CONFLICT = conselho_rede.Conflict
                _COUNCIL = conselho_rede.Council(
                    _COUNCIL_DATA_DIR, _council_clean, _council_execute,
                    legacy=_COUNCIL_LEGACY_HISTORY,
                )
    return _COUNCIL


def _verify(command: str, **arguments: object) -> str:
    """Consulta comandos fixos do verificador; parâmetros externos são validados."""
    allowed = {"unidade", "git_status", "git_log", "p8_verificar"}
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
    timeout = 95 if command == "busca_semantica" else 65 if command == "p8_verificar" else 5
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


def _timer_snapshot(unit: str) -> dict:
    observed_at, fresh_until = _reading_window()
    result = {
        "unit": unit, "state": "unknown", "source": "systemctl --user show",
        "source_ref": unit, "observed_at": observed_at, "fresh_until": fresh_until,
    }
    if unit not in TIMER_ALLOWLIST:
        raise ValueError("timer não permitido")
    try:
        proc = subprocess.run(
            ["/usr/bin/systemctl", "--user", "show", "--no-pager",
             "--property=Id,LoadState,ActiveState,SubState,NextElapseUSecRealtime,LastTriggerUSec",
             "--", unit], capture_output=True, text=True, timeout=5, check=False,
        )
        if proc.returncode != 0 or len(proc.stdout) > 8192:
            raise ValueError("consulta ao timer indisponível")
        values = _parse_pairs(proc.stdout)
        if values.get("Id") != unit or values.get("LoadState") != "loaded" or not values.get("ActiveState"):
            raise ValueError("timer ausente ou resposta incompleta")
        result.update({
            "state": "ok" if values["ActiveState"] == "active" else "warning",
            "active_state": values["ActiveState"], "sub_state": values.get("SubState", ""),
            "next_trigger": values.get("NextElapseUSecRealtime") or None,
            "last_trigger": values.get("LastTriggerUSec") or None,
        })
    except (OSError, subprocess.TimeoutExpired, ValueError):
        result["error"] = "estado do timer indisponível"
    service = TIMER_SERVICES[unit]
    execution = {"state": "unknown", "source_ref": service}
    try:
        proc = subprocess.run(
            ["/usr/bin/systemctl", "--user", "show", "--no-pager",
             "--property=Id,LoadState,ActiveState,Result,ExecMainStatus,ExecMainExitTimestamp",
             "--", service], capture_output=True, text=True, timeout=5, check=False,
        )
        values = _parse_pairs(proc.stdout)
        if proc.returncode != 0 or len(proc.stdout) > 8192 or values.get("Id") != service or values.get("LoadState") != "loaded":
            raise ValueError("estado da execução indisponível")
        result_code = values.get("Result")
        ended_at = values.get("ExecMainExitTimestamp") or None
        if result_code == "exec-condition":
            execution["state"] = "skipped"
        elif result_code and ended_at:
            execution["state"] = "observed"
        execution.update({"result": result_code or None, "ended_at": ended_at,
                          "active_state": values.get("ActiveState") or None})
    except (OSError, subprocess.TimeoutExpired, ValueError):
        execution["error"] = "resultado da unidade indisponível"
    result["execution"] = execution
    result["observed_at"], result["fresh_until"] = _reading_window()
    return result


def _maintenance_tasks() -> dict:
    observed_at, fresh_until = _reading_window()
    value = {"state": "unknown", "source": "config/janela-tarefas.txt",
             "observed_at": observed_at, "fresh_until": fresh_until, "tasks": []}
    try:
        path = ROOT / "config/janela-tarefas.txt"
        if path.stat().st_size > 65536:
            raise ValueError("configuração acima do limite")
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            fields = line.split("|")
            if len(fields) < 6 or not re.fullmatch(r"[a-z0-9_-]{1,80}", fields[0]) or fields[1] not in {"daily", "weekly"}:
                raise ValueError("configuração de tarefa inválida")
            value["tasks"].append({"id": fields[0], "cadence": fields[1]})
        value["state"] = "ok"
    except (OSError, UnicodeError, ValueError):
        value["tasks"] = []
        value["error"] = "configuração da janela indisponível"
    value["history_state"] = "unknown"
    if value["state"] == "ok":
        try:
            if MAINTENANCE_STATE.stat().st_size > 262144:
                raise ValueError("estado acima do limite")
            history = json.loads(MAINTENANCE_STATE.read_text(encoding="utf-8"))
            if not isinstance(history, dict):
                raise ValueError("estado inválido")
            for task in value["tasks"]:
                record = history.get(task["id"], {})
                if not isinstance(record, dict):
                    continue
                result = record.get("last_result")
                finished = record.get("last_finished")
                if result in {"success", "skipped", "failed"} and isinstance(finished, str) and len(finished) <= 40:
                    datetime.fromisoformat(finished)
                    task.update({"last_result": result, "last_finished": finished})
            value["history_state"] = "ok"
        except (OSError, UnicodeError, ValueError, TypeError):
            value["history_error"] = "resultado das tarefas indisponível"
    value["observed_at"], value["fresh_until"] = _reading_window()
    return value


def _chat_snapshot() -> dict:
    result = {"state": "unknown", "source": "LibreChat /health", "source_ref": "127.0.0.1:3080/health"}
    connection = http.client.HTTPConnection("127.0.0.1", 3080, timeout=3)
    try:
        connection.request("GET", "/health")
        response = connection.getresponse()
        result.update({"state": "ok" if response.status == 200 else "warning", "http_status": response.status})
    except (OSError, TimeoutError, http.client.HTTPException):
        result["error"] = "verificação HTTP indisponível"
    finally:
        connection.close()
    result["observed_at"], result["fresh_until"] = _reading_window()
    return result


def _substituidas(directory: Path) -> dict:
    """Propostas substituídas, lidas de propostas/SUBSTITUIDAS.txt (nome | substituída por | motivo)."""
    arquivo = directory / "SUBSTITUIDAS.txt"
    if not arquivo.is_file() or arquivo.stat().st_size > 16384:
        return {}
    out = {}
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        partes = [p.strip() for p in linha.split("|")]
        if len(partes) >= 2 and re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,80}", partes[0]):
            out[partes[0]] = partes[1][:200]
    return out


# (27/10/2026) Capacidades do painel com leitura real. Só sondas de leitura: estado de unidades e HTTP local.
# Capacidade sem sonda (documento) não tem estado, e não é listada aqui.
CAPACIDADES = {
    "conversar": {"units": ["seth-gateway.service"], "http": ["http://127.0.0.1:3080/"]},
    "ouvir": {"units": ["piper-tts.service"], "http": []},
    "buscar": {"units": ["seth-verificador.service"], "http": []},
    "verificar": {"units": ["seth-verificador.service"], "http": ["http://127.0.0.1:20141/"]},
    "navegar": {"units": ["navegador-mcp.service", "discord-mcp.service"], "http": []},
    "rota": {"units": ["seth-gateway.service"], "http": []},
    "manutencao": {"units": ["agata-manutencao.timer"], "http": []},
    "acrescentar": {"units": ["seth-escriba.service"], "http": []},
}


def _unidade_ativa(unit: str) -> bool | None:
    try:
        proc = subprocess.run(["/usr/bin/systemctl", "--user", "show", "--no-pager", "--property=ActiveState,LoadState", "--", unit],
                              capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    valores = _parse_pairs(proc.stdout)
    if valores.get("LoadState") != "loaded":
        return None
    return valores.get("ActiveState") == "active"


def _http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as resposta:
            return resposta.status == 200
    except (OSError, ValueError):
        return False


def _capacidades_snapshot() -> dict:
    observed_at, fresh_until = _reading_window()
    itens = []
    for nome, sondas in CAPACIDADES.items():
        estados = [_unidade_ativa(u) for u in sondas["units"]] + [_http_ok(h) for h in sondas["http"]]
        if any(e is None for e in estados):
            estado = "unknown"
        elif all(estados):
            estado = "ok"
        else:
            estado = "warning"
        partes = []
        for u, e in zip(sondas["units"], estados[:len(sondas["units"])]):
            partes.append(f"{u} {'ativo' if e else ('inativo ou ausente' if e is False else 'sem leitura')}")
        for h, e in zip(sondas["http"], estados[len(sondas["units"]):]):
            partes.append(f"{h} {'responde 200' if e else 'sem resposta 200'}")
        itens.append({"id": nome, "state": estado, "source": "systemctl --user show; HTTP local",
                      "source_ref": ", ".join(sondas["units"] + sondas["http"]),
                      "evidencia": "Medido agora (" + observed_at + "): " + "; ".join(partes) + ".",
                      "observed_at": observed_at, "fresh_until": fresh_until})
    return {"schema_version": 1, "state": "ok", "observed_at": observed_at, "fresh_until": fresh_until, "items": itens}


def _unidade_de_sistema_ativa(unit: str) -> bool | None:
    """Unidade de sistema (sem --user), para units como ollama.service que o canon declara no boot."""
    try:
        proc = subprocess.run(["/usr/bin/systemctl", "show", "--no-pager", "--property=ActiveState,LoadState", "--", unit],
                              capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    valores = _parse_pairs(proc.stdout)
    if valores.get("LoadState") != "loaded":
        return None
    return valores.get("ActiveState") == "active"


def _porta_responde(porta: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", porta), timeout=1):
            return True
    except OSError:
        return False


VAULT_ITENS = {"inicio": "INICIO.md", "timeline": "timeline.md", "estado": "estado.md",
               "mapa": "mapa-do-sistema.canvas", "memorias": "memorias.base", "moc-projeto": "moc-projeto.md",
               "moc-memoria": "moc-memoria.md", "moc-documentos": "moc-documentos.md", "moc-scripts": "moc-scripts.md"}
VAULT_LIMITE = 65536


def _vault_item(item_id: str) -> dict:
    """Um item do vault, só leitura, de uma lista fechada. Texto cru; canvas também vira lista de nós."""
    observed_at, fresh_until = _reading_window()
    nome = VAULT_ITENS[item_id]
    arq = ROOT / "memoria/obsidian" / nome
    base = {"schema_version": 1, "id": item_id, "fonte": "memoria/obsidian/" + nome,
            "observed_at": observed_at, "fresh_until": fresh_until}
    if not arq.is_file():
        return {**base, "state": "unknown", "titulo": nome, "motivo": "arquivo ausente no vault"}
    st = arq.stat()
    with arq.open("rb") as f:
        bruto = f.read(VAULT_LIMITE)
    texto = bruto.decode("utf-8", errors="replace")
    titulo = next((l[2:].strip() for l in texto.splitlines() if l.startswith("# ")), nome)
    out = {**base, "state": "ok", "titulo": titulo, "texto": texto, "tamanho": st.st_size,
           "truncado": st.st_size > VAULT_LIMITE,
           "modificado": datetime.fromtimestamp(st.st_mtime, ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds")}
    if nome.endswith(".canvas") and not out["truncado"]:
        try:
            dados = json.loads(texto)
            out["canvas"] = {"nos": [{"tipo": n.get("type", ""), "texto": str(n.get("text") or n.get("file") or "")[:200]}
                                     for n in dados.get("nodes", [])[:200]],
                             "arestas": len(dados.get("edges", []))}
        except ValueError:
            out["canvas"] = None
    return out


def _vault_caminho(caminho: str) -> dict | None:
    """Nota .md do vault pelo caminho relativo, só leitura. Recusa tudo que sair de memoria/obsidian."""
    if not re.fullmatch(r"[^\x00-\x1f\\]{1,200}\.md", caminho) or caminho.startswith("/") or ".." in caminho.split("/"):
        return None
    raiz = (ROOT / "memoria/obsidian").resolve()
    arq = (raiz / caminho).resolve()
    if raiz not in arq.parents or not arq.is_file():
        return None
    observed_at, fresh_until = _reading_window()
    st = arq.stat()
    with arq.open("rb") as f:
        texto = f.read(VAULT_LIMITE).decode("utf-8", errors="replace")
    titulo = next((l[2:].strip() for l in texto.splitlines() if l.startswith("# ")), arq.stem)
    return {"schema_version": 1, "id": caminho, "fonte": "memoria/obsidian/" + caminho, "state": "ok",
            "titulo": titulo, "texto": texto, "tamanho": st.st_size, "truncado": st.st_size > VAULT_LIMITE,
            "modificado": datetime.fromtimestamp(st.st_mtime, ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds"),
            "observed_at": observed_at, "fresh_until": fresh_until}


CONVERSAS_DIR = Path.home() / ".cache/agata/painel-conversas"
CONVERSA_ID = re.compile(r"[0-9a-f]{12}")
CONVERSA_LIMITE_BYTES = 262144


def _conversa_caminho(conversa_id: str) -> Path | None:
    if not isinstance(conversa_id, str) or not CONVERSA_ID.fullmatch(conversa_id):
        return None
    return CONVERSAS_DIR / (conversa_id + ".json")


def _conversas_listar() -> dict:
    itens = []
    if CONVERSAS_DIR.is_dir():
        for arq in sorted(CONVERSAS_DIR.glob("*.json"), key=lambda a: a.stat().st_mtime, reverse=True)[:200]:
            if not CONVERSA_ID.fullmatch(arq.stem):
                continue
            try:
                dados = json.loads(arq.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            itens.append({"id": arq.stem, "titulo": dados.get("titulo", "Sem título"),
                          "atualizada": datetime.fromtimestamp(arq.stat().st_mtime, ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds"),
                          "mensagens": len(dados.get("mensagens", []))})
    return {"schema_version": 1, "state": "ok", "items": itens}


def _conversa_validar(dados: dict) -> dict | None:
    if not isinstance(dados, dict):
        return None
    titulo = str(dados.get("titulo") or "").strip()[:80] or "Sem título"
    mensagens = dados.get("mensagens")
    if not isinstance(mensagens, list) or len(mensagens) > 200:
        return None
    limpas = []
    for m in mensagens:
        if not isinstance(m, dict) or m.get("role") not in ("user", "assistant") or not isinstance(m.get("content"), str):
            return None
        if len(m["content"]) > 8000:
            return None
        limpas.append({"role": m["role"], "content": m["content"]})
    return {"titulo": titulo, "mensagens": limpas}


def _conversa_gravar(dados: dict) -> dict | None:
    limpo = _conversa_validar(dados)
    if limpo is None:
        return None
    conversa_id = dados.get("id") or os.urandom(6).hex()
    arq = _conversa_caminho(conversa_id)
    if arq is None:
        return None
    CONVERSAS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps(limpo, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, arq)
    return {"id": conversa_id, **limpo}


def _conversa_apagar(conversa_id: str) -> bool:
    arq = _conversa_caminho(conversa_id)
    if arq is None or not arq.is_file():
        return False
    arq.unlink()
    return True


def _lacunas_snapshot() -> dict:
    """Lacunas declaradas no canon (PROJETO.md, Serviços (boot)), conferidas agora:
    - unidade systemd citada (`nome.service` / `nome.timer`): sem leitura ou inativa vira lacuna;
    - item com porta declarada (`:NNNN`) que não responde em 127.0.0.1 vira lacuna."""
    observed_at, fresh_until = _reading_window()
    try:
        texto = (ROOT / "PROJETO.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"schema_version": 1, "state": "unknown", "observed_at": observed_at, "fresh_until": fresh_until,
                "total_declaradas": 0, "items": [{"nome": "PROJETO.md", "motivo": "fonte do canon indisponível", "fonte": "PROJETO.md"}]}
    inicio = texto.find("## Serviços (boot)")
    fim = texto.find("**Não recriar", inicio)
    secao = texto[inicio:fim] if (inicio >= 0 and fim > inicio) else ""
    itens = []
    if not secao:
        itens.append({"nome": "seção Serviços (boot)", "motivo": "seção não encontrada em PROJETO.md", "fonte": "PROJETO.md"})
    vistas = set(); declaradas = 0
    for linha in secao.splitlines():
        if linha.startswith("**Manuais") or linha.startswith("**Consolidação") or linha.startswith("**Não recriar"):
            continue
        for unit in re.findall(r"`([a-z0-9@._-]+\.(?:service|timer))`", linha):
            if unit in vistas: continue
            vistas.add(unit); declaradas += 1
            ativo = _unidade_ativa(unit)
            if ativo is None:
                ativo = _unidade_de_sistema_ativa(unit)
            if ativo is None:
                itens.append({"nome": unit, "motivo": "sem leitura do systemd agora (ausente ou não consultada)", "fonte": "PROJETO.md · Serviços (boot)"})
            elif ativo is False:
                itens.append({"nome": unit, "motivo": "declarada no boot e inativa agora", "fonte": "PROJETO.md · Serviços (boot)"})
        if not linha.lstrip().startswith("- "):
            continue
        m = re.search(r"`([a-z][a-z0-9-]+)`.{0,40}?:(\d{4,5})\b", linha)
        if m and not re.search(r"\.(service|timer)$", m.group(1)):
            declaradas += 1
            if not _porta_responde(int(m.group(2))):
                itens.append({"nome": m.group(1) + " :" + m.group(2), "motivo": "porta declarada não responde em 127.0.0.1", "fonte": "PROJETO.md · Serviços (boot)"})
    return {"schema_version": 1, "state": "ok", "observed_at": observed_at, "fresh_until": fresh_until,
            "total_declaradas": declaradas, "items": itens}


def _propostas_versionadas() -> set | None:
    """Nomes de propostas/*.diff que estão no git (fonte do canon). None se o git não responder."""
    try:
        proc = subprocess.run(["/usr/bin/git", "-C", str(ROOT), "ls-files", "propostas"], capture_output=True,
                              text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return {Path(l).stem for l in proc.stdout.splitlines() if l.endswith(".diff")}


def _proposal_snapshot() -> dict:
    observed_at, fresh_until = _reading_window()
    value = {"state": "unknown", "source": "propostas/ local", "observed_at": observed_at,
             "fresh_until": fresh_until, "items": []}
    try:
        directory = ROOT / "propostas"
        if not directory.is_dir():
            raise OSError("diretório indisponível")
        paths = sorted(directory.glob("*.diff"))
        versionadas = _propostas_versionadas()
        for path in paths[:100]:
            if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,80}", path.stem):
                continue
            item = {"name": path.stem, "marker_present": (directory / ("APROVADO-" + path.stem)).is_file(),
                    "versionada": path.stem in versionadas if versionadas is not None else None}
            if path.stem in _substituidas(directory):
                item["substituida_por"] = _substituidas(directory)[path.stem]
            value["items"].append(item)
        value.update({"state": "ok", "total": len(paths), "truncated": len(paths) > 100})
    except OSError:
        value["error"] = "lista local de propostas indisponível"
    value["observed_at"], value["fresh_until"] = _reading_window()
    return value


def _proposal_check(name: str) -> dict:
    if (not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,80}", name)
            or name.endswith((".", ".diff"))):
        raise ValueError("nome inválido")
    directory = ROOT / "propostas"
    if not (directory / (name + ".diff")).is_file():
        raise ValueError("proposta indisponível")
    observed_at, fresh_until = _reading_window()
    result = {"name": name, "state": "unknown", "source": "seth-verificador: p8_verificar",
              "observed_at": observed_at, "fresh_until": fresh_until}
    if not (directory / ("APROVADO-" + name)).is_file():
        result["state"] = "unsigned"
        return result
    try:
        paths = (directory / (name + ".diff"), directory / ("APROVADO-" + name))
        def digest(path: Path) -> str:
            if path.is_symlink() or path.stat().st_size > 8 * 1024 * 1024:
                raise ValueError("arquivo de proposta inválido")
            with path.open("rb") as stream:
                return hashlib.file_digest(stream, "sha256").hexdigest()
        before = tuple(digest(path) for path in paths)
        body = _command_body(_verify("p8_verificar", nome=name))
        if before != tuple(digest(path) for path in paths):
            raise ValueError("proposta alterada durante a verificação")
        result["diff_sha256"] = before[0]
        if re.search(r"(?m)^PODE APLICAR:", body):
            result["state"] = "applicable"
        else:
            failure = re.search(r"(?m)^FALHA ([1-4]):", body)
            if failure:
                result.update({"state": "blocked", "failed_check": int(failure.group(1))})
    except (OSError, TimeoutError, ValueError, urllib.error.URLError):
        result["error"] = "verificação indisponível"
    result["observed_at"], result["fresh_until"] = _reading_window()
    return result


def _model_snapshot() -> dict:
    observed_at, fresh_until = _reading_window()
    value = {"state": "unknown", "source": "config/capivara/capacidades.json",
             "observed_at": observed_at, "fresh_until": fresh_until, "models": []}
    try:
        path = ROOT / "config/capivara/capacidades.json"
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("registro acima do limite")
        data = json.loads(path.read_text(encoding="utf-8"))
        models = data["modelos"]
        if not isinstance(models, dict) or len(models) > 100:
            raise ValueError("registro de modelos inválido")
        for name, model in sorted(models.items()):
            if not isinstance(name, str) or len(name) > 200 or not isinstance(model, dict):
                raise ValueError("modelo inválido")
            catalog = model.get("catalogo") or {}
            if not isinstance(catalog, dict):
                raise ValueError("catálogo inválido")
            measured = model.get("medido") or []
            observed = model.get("observado") or []
            if not isinstance(measured, list) or not isinstance(observed, list):
                raise ValueError("medições inválidas")
            metrics = [{key: row.get(key) for key in ("metrica", "valor", "data", "amostra", "protocolo")}
                       for row in measured[-12:] if isinstance(row, dict)]
            value["models"].append({"name": name, "window": catalog.get("janela"),
                                    "max_output": catalog.get("saida_max"), "source": catalog.get("fonte"),
                                    "read_at": catalog.get("lido_em"), "metrics": metrics,
                                    "metrics_truncated": len(measured) > 12,
                                    "observed": [{key: row.get(key) for key in ("metrica", "valor", "data", "amostra", "protocolo")}
                                                 for row in observed[-12:] if isinstance(row, dict)],
                                    "observed_truncated": len(observed) > 12})
        value.update({"state": "ok", "recorded_at": data.get("gerado_em")})
    except (OSError, UnicodeError, ValueError, TypeError, KeyError):
        value["models"] = []
        value["error"] = "registro de modelos indisponível"
    value["observed_at"], value["fresh_until"] = _reading_window()
    return value


def _details_snapshot() -> dict:
    """Dados menos frequentes, coletados apenas quando uma tela os solicita."""
    with ThreadPoolExecutor(max_workers=3) as pool:
        integrations = list(pool.map(_service_snapshot, INTEGRATION_ALLOWLIST))
    observed_at, fresh_until = _reading_window()
    memory = {"state": "unknown", "source": "memoria/obsidian/",
              "observed_at": observed_at, "fresh_until": fresh_until}
    try:
        vault = ROOT / "memoria/obsidian"
        entries = vault / "entradas"
        if not vault.is_dir() or not entries.is_dir():
            raise OSError("vault indisponível")
        count = sum(1 for path in entries.iterdir() if path.is_file() and path.suffix == ".md")
        memory.update({"state": "ok", "entry_count": count})
    except OSError:
        memory["error"] = "vault derivado indisponível"
    return {"schema_version": 1, "observed_at": observed_at,
            "integrations": integrations, "memory": memory}


def _cached_details() -> dict:
    global _DETAILS_CACHE, _DETAILS_CACHE_AT
    with _DETAILS_LOCK:
        now = time.monotonic()
        if _DETAILS_CACHE is not None and _DETAILS_CACHE_AT is not None and now - _DETAILS_CACHE_AT < 60:
            return _DETAILS_CACHE
        _DETAILS_CACHE = _details_snapshot()
        _DETAILS_CACHE_AT = time.monotonic()
        return _DETAILS_CACHE


def collect() -> dict:
    # Consultas fixas e limitadas em paralelo; uma fonte lenta não serializa as demais.
    with ThreadPoolExecutor(max_workers=3) as pool:
        unit_futures = [pool.submit(_service_snapshot, unit) for unit in SERVICE_ALLOWLIST]
        git_future = pool.submit(_git_snapshot)
        timer_futures = [pool.submit(_timer_snapshot, unit) for unit in TIMER_ALLOWLIST]
        chat_future = pool.submit(_chat_snapshot)
        services = [future.result() for future in unit_futures]
        git = git_future.result()
        timers = [future.result() for future in timer_futures]
        chat = chat_future.result()
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
        "timers": timers,
        "chat": chat,
        "maintenance": _maintenance_tasks(),
        "proposals": _proposal_snapshot(),
        "models": _model_snapshot(),
    }


def _cached_status() -> dict:
    """Reusa por poucos segundos respostas GET sequenciais do HTTPServer simples."""
    global _STATUS_CACHE, _STATUS_CACHE_AT
    with _STATUS_LOCK:
        now = time.monotonic()
        if (_STATUS_CACHE is not None and _STATUS_CACHE_AT is not None
                and now - _STATUS_CACHE_AT < CACHE_SECONDS):
            return _STATUS_CACHE
        _STATUS_CACHE = collect()
        _STATUS_CACHE_AT = time.monotonic()
        return _STATUS_CACHE


def _wiki_search(query: str, mode: str) -> dict:
    """Executa apenas os dois comandos de busca aprovados, com a consulta como dado."""
    if (not isinstance(query, str) or not query.strip() or len(query) > 200
            or any(char in query for char in "\r\n\x00")):
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
            first = output.splitlines()[0] if output else ""
            match = re.search(r"\(exit=(\d+)\)", first)
            if not match or int(match.group(1)) not in ({0, 1} if command == "busca_texto" else {0}):
                raise ValueError("a busca não retornou uma leitura válida")
            if command == "busca_semantica" and "índice semântico ausente, vazio ou inválido" in output:
                raise ValueError("índice semântico indisponível")
            partial = command == "busca_semantica" and "índice parcial" in output
            if len(output) > WIKI_RESULT_MAX:
                total = len(output)
                percent = round(WIKI_RESULT_MAX / total * 100)
                output = output[:WIKI_RESULT_MAX] + (
                    f"\n\n[TRUNCADO: mostrando {WIKI_RESULT_MAX} de {total} caracteres "
                    f"(~{percent}%). O restante não foi lido; não conclua nada sobre ele.]"
                )
            results.append({"command": command, "output": output, "error": None, "partial": partial})
        except (OSError, TimeoutError, ValueError, urllib.error.URLError):
            results.append({"command": command, "output": "", "error": "fonte indisponível"})
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
        if self.path.startswith("/api/grafo"):
            return self._grafo()
        if self.path == "/api/seth/conversas":
            return self._send(200, "application/json; charset=utf-8", json.dumps(_conversas_listar(), ensure_ascii=False).encode("utf-8"))
        if self.path.startswith("/api/seth/conversa?"):
            arq = _conversa_caminho((parse_qs(urlparse(self.path).query).get("id") or [""])[0])
            if arq is None or not arq.is_file():
                return self._send(404, "text/plain; charset=utf-8", b"conversa indisponivel")
            return self._send(200, "application/json; charset=utf-8", arq.read_bytes())
        if self.path.startswith("/api/vault/item"):
            q = parse_qs(urlparse(self.path).query)
            if q.get("caminho"):
                dados = _vault_caminho(q["caminho"][0])
                if dados is None:
                    return self._send(400, "text/plain; charset=utf-8", b"caminho fora do vault")
            else:
                item_id = (q.get("id") or [""])[0]
                if item_id not in VAULT_ITENS:
                    return self._send(400, "text/plain; charset=utf-8", b"item fora da lista")
                dados = _vault_item(item_id)
            body = json.dumps(dados, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/lacunas":
            body = json.dumps(_lacunas_snapshot(), ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/capacidades":
            body = json.dumps(_capacidades_snapshot(), ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/relay-council/catalog":
            _cache, catalog, _contract, _sanitizer = _relay_modules()
            body = json.dumps(
                {"schema_version": 1, "providers": catalog.snapshot()},
                ensure_ascii=False,
            ).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/relay-council/state":
            council = _council_state()
            data = council.snapshot()
            data["csrf"] = council.csrf
            data["legacy_history"] = council.history(legacy=True)
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path.startswith("/api/relay-council/history?"):
            query = parse_qs(urlparse(self.path).query)
            try:
                offset = int((query.get("offset") or ["0"])[0])
                data = _council_state().history(offset)
            except (ValueError, TypeError):
                return self._send(400, "text/plain; charset=utf-8", b"invalid history offset")
            return self._send(200, "application/json; charset=utf-8",
                              json.dumps(data, ensure_ascii=False).encode("utf-8"))
        if self.path == "/api/relay-council/tasks":
            if self.headers.get("X-Relay-Client") != RELAY_CLIENT_ID:
                return self._send(403, "application/json; charset=utf-8", b'{"error":"executor not authorized"}')
            tasks = _council_state().claim()
            return self._send(200, "application/json; charset=utf-8",
                              json.dumps(tasks, ensure_ascii=False).encode("utf-8"))
        if self.path in {"/api/status", "/api/details"}:
            if not _same_origin_request(
                self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")
            ):
                return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
            data = _cached_status() if self.path == "/api/status" else _cached_details()
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
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
        if self.path in {"/api/relay-council/actions", "/api/relay-council/groups",
                         "/api/relay-council/decision"}:
            return self._relay_council_human_post()
        if self.path == "/api/relay-council/execute":
            return self._relay_council_execute()
        if self.path == "/api/relay-council/evaluations":
            return self._relay_evaluation()
        if self.path == "/api/seth/chat":
            return self._seth_chat()
        if self.path in ("/api/seth/conversa", "/api/seth/conversa/apagar"):
            return self._seth_conversa(self.path.endswith("/apagar"))
        if self.path not in {"/api/wiki/search", "/api/proposals/verify"} or (self.path == "/api/wiki/search" and not WIKI_LIBERADA):
            return self._send(405, "text/plain; charset=utf-8", b"read only", (("Allow", "GET, POST"),))
        if self.headers.get("Origin") != ALLOWED_ORIGIN or not _same_origin_request(
            self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")
        ):
            return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            return self._send(415, "text/plain; charset=utf-8", b"JSON required")
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > 4096:
            return self._send(413, "text/plain; charset=utf-8", b"request too large")
        try:
            payload = json.loads(self.rfile.read(int(raw_length)))
        except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
            return self._send(400, "text/plain; charset=utf-8", b"invalid JSON")
        if not isinstance(payload, dict):
            return self._send(400, "text/plain; charset=utf-8", b"invalid search")
        if self.path == "/api/proposals/verify":
            name = payload.get("name")
            if not _PROPOSAL_LOCK.acquire(blocking=False):
                return self._send(429, "text/plain; charset=utf-8", b"verification busy")
            try:
                try:
                    result = _proposal_check(name)
                except ValueError:
                    return self._send(400, "text/plain; charset=utf-8", b"invalid proposal")
            finally:
                _PROPOSAL_LOCK.release()
            body = json.dumps({"schema_version": 1, **result}, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        query = payload.get("query")
        mode = payload.get("mode", "ambos")
        if (not isinstance(query, str) or not query.strip() or len(query) > 200
                or any(char in query for char in "\r\n\x00")):
            return self._send(400, "text/plain; charset=utf-8", b"query must contain 1-200 characters")
        if not isinstance(mode, str) or mode not in {"texto", "sentido", "ambos"}:
            return self._send(400, "text/plain; charset=utf-8", b"invalid search mode")
        if not _WIKI_LOCK.acquire(blocking=False):
            return self._send(429, "text/plain; charset=utf-8", b"search busy")
        try:
            result = _wiki_search(query, mode)
        finally:
            _WIKI_LOCK.release()
        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        return self._send(200, "application/json; charset=utf-8", body)

    def _relay_council_body(self, max_bytes: int = 65_536) -> dict | None:
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            self._send(415, "text/plain; charset=utf-8", b"JSON required")
            return None
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > max_bytes:
            self._send(413, "text/plain; charset=utf-8", b"request too large")
            return None
        try:
            payload = json.loads(self.rfile.read(int(raw_length)).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
            self._send(400, "text/plain; charset=utf-8", b"invalid JSON")
            return None
        if not isinstance(payload, dict):
            self._send(400, "text/plain; charset=utf-8", b"JSON object required")
            return None
        return payload

    def _relay_council_human_post(self) -> None:
        if (self.headers.get("Origin") != ALLOWED_ORIGIN
                or self.headers.get("Sec-Fetch-Site") not in {"same-origin", "none"}):
            return self._send(403, "text/plain; charset=utf-8", b"same-origin request required")
        payload = self._relay_council_body()
        if payload is None:
            return
        council = _council_state()
        if not isinstance(payload.get("csrf"), str) or not secrets.compare_digest(payload["csrf"], council.csrf):
            return self._send(403, "text/plain; charset=utf-8", b"invalid CSRF token")
        try:
            if self.path.endswith("/actions"):
                action = council.create(payload.get("kind"), payload.get("payload"))
                result = council._row(action)
            elif self.path.endswith("/groups"):
                group = council.group(payload.get("kind"), payload.get("prompt"),
                                      payload.get("sites"), payload.get("repetitions", 1))
                result = {"group_id": group, "state": "pending-human-approval"}
            else:
                result = council.decide(payload.get("id"), payload.get("hash"), payload.get("approve"))
            result.pop("lease", None)
            body = json.dumps(result, ensure_ascii=False, default=str).encode("utf-8")
        except _COUNCIL_CONFLICT:
            return self._send(409, "text/plain; charset=utf-8", b"action changed; refresh and review")
        except (ValueError, TypeError, KeyError, AttributeError):
            return self._send(400, "text/plain; charset=utf-8", b"invalid council action")
        return self._send(201, "application/json; charset=utf-8", body)

    def _relay_council_execute(self) -> None:
        if self.headers.get("X-Relay-Client") != RELAY_CLIENT_ID:
            return self._send(403, "application/json; charset=utf-8", b'{"error":"executor not authorized"}')
        payload = self._relay_council_body(4096)
        if payload is None:
            return
        task_id, lease = payload.get("task_id"), payload.get("lease")
        if not isinstance(task_id, str) or not isinstance(lease, str):
            return self._send(400, "application/json; charset=utf-8", b'{"error":"invalid task"}')
        try:
            import relay_executor
            result = _council_state().execute_api(task_id, lease, relay_executor.send)
        except _COUNCIL_CONFLICT:
            return self._send(409, "application/json; charset=utf-8", b'{"error":"task lease mismatch"}')
        except (ValueError, TypeError, KeyError):
            return self._send(400, "application/json; charset=utf-8", b'{"error":"invalid task"}')
        return self._send(200, "application/json; charset=utf-8",
                          json.dumps(result).encode("utf-8"))

    def _relay_evaluation(self) -> None:
        if (self.headers.get("Origin") != ALLOWED_ORIGIN
                or self.headers.get("Sec-Fetch-Site") not in {"same-origin", "none"}):
            return self._send(403, "text/plain; charset=utf-8", b"same-origin request required")
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            return self._send(415, "text/plain; charset=utf-8", b"JSON required")
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > 65_536:
            return self._send(413, "text/plain; charset=utf-8", b"request too large")
        try:
            payload = json.loads(self.rfile.read(int(raw_length)).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
            return self._send(400, "text/plain; charset=utf-8", b"invalid JSON")
        if not isinstance(payload, dict):
            return self._send(400, "text/plain; charset=utf-8", b"evaluation must be an object")
        if not _RELAY_LOCK.acquire(blocking=False):
            return self._send(429, "text/plain; charset=utf-8", b"relay busy")
        try:
            if _relay_rate_limited():
                return self._send(429, "text/plain; charset=utf-8", b"relay rate limit reached",
                                  (("Retry-After", str(_RELAY_RATE_WINDOW_SECONDS)),))
            try:
                receipt = _relay_store(payload)
            except RelayDailyQuotaExceeded:
                return self._send(429, "text/plain; charset=utf-8", b"local council daily quota reached")
            except RelayIdempotencyConflict:
                return self._send(409, "text/plain; charset=utf-8", b"task result conflicts with stored result")
            except RelayEvaluationTooLarge:
                return self._send(413, "text/plain; charset=utf-8", b"evaluation too large for local council cache")
            except ValueError:
                return self._send(400, "text/plain; charset=utf-8", b"invalid evaluation")
            except OSError:
                return self._send(503, "text/plain; charset=utf-8", b"local council cache unavailable")
        finally:
            _RELAY_LOCK.release()
        body = json.dumps({
            "schema_version": 1,
            "stored": True,
            "entry": receipt["n"],
            "hash": receipt["h"],
            "duplicate": receipt.get("duplicate", False),
        }).encode("utf-8")
        return self._send(200 if receipt.get("duplicate") else 201, "application/json; charset=utf-8", body)


    def _seth_conversa(self, apagar: bool) -> None:
        """Histórico de conversas da Seth, em ~/.cache (fora do canon). Só valida e grava o que o próprio painel envia."""
        if not _same_origin_request(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")):
            return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > CONVERSA_LIMITE_BYTES:
            return self._send(413, "text/plain; charset=utf-8", b"request too large")
        try:
            dados = json.loads(self.rfile.read(int(raw_length)).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._send(400, "text/plain; charset=utf-8", b"invalid json")
        if apagar:
            ok = _conversa_apagar(dados.get("id") if isinstance(dados, dict) else "")
            return self._send(200 if ok else 404, "application/json; charset=utf-8", json.dumps({"apagada": ok}).encode("utf-8"))
        salvo = _conversa_gravar(dados)
        if salvo is None:
            return self._send(400, "text/plain; charset=utf-8", b"conversa invalida")
        return self._send(200, "application/json; charset=utf-8", json.dumps(salvo, ensure_ascii=False).encode("utf-8"))

    def _seth_chat(self) -> None:
        """Conversa com a Seth pelo gateway local (seth-livre), só texto, sem ferramentas e sem escrita."""
        if not _same_origin_request(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")):
            return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > 16384:
            return self._send(413, "text/plain; charset=utf-8", b"request too large")
        try:
            corpo = json.loads(self.rfile.read(int(raw_length)))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._send(400, "text/plain; charset=utf-8", b"invalid JSON")
        mensagens = corpo.get("messages") if isinstance(corpo, dict) else None
        if not isinstance(mensagens, list) or not mensagens or len(mensagens) > 20:
            return self._send(400, "text/plain; charset=utf-8", b"messages must be 1-20 items")
        limpas = []
        for m in mensagens:
            if not isinstance(m, dict) or m.get("role") not in ("user", "assistant"):
                return self._send(400, "text/plain; charset=utf-8", b"invalid message")
            conteudo = m.get("content")
            if not isinstance(conteudo, str) or not conteudo.strip() or len(conteudo) > 4000:
                return self._send(400, "text/plain; charset=utf-8", b"content must be 1-4000 characters")
            limpas.append({"role": m["role"], "content": conteudo})
        if not _SEM_CONVERSA_EM_CURSO.acquire(blocking=False):
            return self._send(429, "text/plain; charset=utf-8", b"busy")
        try:
            pedido = {"model": "seth-livre", "stream": False, "messages": limpas, "max_tokens": 1024}
            req = urllib.request.Request("http://127.0.0.1:20126/v1/chat/completions", data=json.dumps(pedido).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=120) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
            texto = dados["choices"][0]["message"].get("content") or ""
            body = json.dumps({"schema_version": 1, "content": texto, "model": dados.get("model")}, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        except (OSError, KeyError, IndexError, ValueError):
            return self._send(502, "text/plain; charset=utf-8", b"gateway indisponivel")
        finally:
            _SEM_CONVERSA_EM_CURSO.release()


    def _grafo(self) -> None:
        """Grafo do vault derivado, só leitura: modo 'citacoes' (cita/citada_por de uma entrada) ou 'regioes' (tags regiao/)."""
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(self.path).query)
        entrada = (q.get("entrada") or ["0850"])[0]
        modo = (q.get("modo") or ["citacoes"])[0]
        if modo == "atlas":
            return self._atlas()
        if not re.fullmatch(r"\d{4}", entrada) or modo not in ("citacoes", "regioes"):
            return self._send(400, "text/plain; charset=utf-8", b"entrada ou modo invalido")
        pasta = ROOT / "memoria/obsidian/entradas"
        arq = pasta / (entrada + ".md")
        if not arq.is_file() or arq.stat().st_size > 65536:
            return self._send(404, "text/plain; charset=utf-8", b"entrada indisponivel")
        def ler_campo(texto: str, campo: str) -> str:
            m = re.search(r"^" + campo + r":\s*(.*)$", texto, re.M)
            return m.group(1) if m else ""
        def ids(valor: str) -> list:
            return re.findall(r"\[\[(\d{4})\]\]", valor)
        def titulo_de(num: str) -> str:
            f = pasta / (num + ".md")
            if not f.is_file() or f.stat().st_size > 65536: return num
            m = re.search(r'^titulo:\s*"?(.*?)"?$', f.read_text(encoding="utf-8", errors="replace"), re.M)
            if not m: return num
            limpo = re.sub(r"\*\*|`", "", m.group(1)).strip()
            return limpo[:60] or num
        corpo = arq.read_text(encoding="utf-8", errors="replace")
        nos = {entrada: {"id": entrada, "label": entrada + " · " + titulo_de(entrada)[:40], "kind": "centro"}}
        arestas = []
        if modo == "citacoes":
            citas = [c for c in ids(ler_campo(corpo, "cita")) if c != entrada][:12]
            cits = [c for c in ids(ler_campo(corpo, "citada_por")) if c != entrada][:12]
            parec = [c for c in ids(ler_campo(corpo, "parecidas")) if c != entrada][:8]
            for c in citas:
                nos[c] = {"id": c, "label": c + " · " + titulo_de(c)[:40], "kind": "cita"}; arestas.append([entrada, c])
            for c in cits:
                nos[c] = {"id": c, "label": c + " · " + titulo_de(c)[:40], "kind": "citada_por"}; arestas.append([c, entrada])
            for c in parec:
                nos[c] = {"id": c, "label": c + " · " + titulo_de(c)[:40], "kind": "parecida"}; arestas.append([entrada, c])
        else:
            regioes = re.findall(r"regiao/[\w-]+", corpo)[:3]
            for r in dict.fromkeys(regioes):
                nos[r] = {"id": r, "label": r, "kind": "regiao"}; arestas.append([entrada, r])
                alvos = []
                for f in sorted(pasta.glob("*.md")):
                    if f.stem == entrada: continue
                    if f.stat().st_size > 65536: continue
                    if r in f.read_text(encoding="utf-8", errors="replace"):
                        alvos.append(f.stem)
                    if len(alvos) >= 8: break
                for a in alvos:
                    nos[a] = {"id": a, "label": a + " · " + titulo_de(a)[:40], "kind": "entrada"}; arestas.append([r, a])
        body = json.dumps({"schema_version": 1, "modo": modo, "centro": entrada, "nodes": list(nos.values()), "edges": arestas},
                          ensure_ascii=False).encode("utf-8")
        return self._send(200, "application/json; charset=utf-8", body)


    def _atlas(self) -> None:
        """Brain Atlas: contagem de notas por região, medida agora no vault (só leitura, só o cabeçalho de cada nota)."""
        vault = ROOT / "memoria/obsidian"
        contagem = collections.Counter(); total = 0
        if not vault.is_dir():
            return self._send(503, "text/plain; charset=utf-8", b"vault indisponivel")
        for arq in vault.rglob("*.md"):
            if any(parte.startswith(".") for parte in arq.relative_to(vault).parts):
                continue
            total += 1
            try:
                with arq.open("rb") as f:
                    bruto = f.read(8192).decode("utf-8", errors="replace")
            except OSError:
                continue
            partes = bruto.split("---", 2)
            cabeca = partes[1] if bruto.startswith("---") and len(partes) >= 3 else ""
            regioes = set(r for r in re.findall(r"regiao/([\w-]{3,})", cabeca))
            for r in regioes: contagem[r] += 1
        nos = [{"id": "cerebro", "label": "Brain Atlas · " + str(total) + " notas", "kind": "centro"}]
        arestas = []
        for r, n in sorted(contagem.items(), key=lambda kv: -kv[1]):
            nos.append({"id": "regiao/" + r, "label": r + " · " + str(n) + " notas", "kind": "regiao"})
            arestas.append(["cerebro", "regiao/" + r])
        body = json.dumps({"schema_version": 1, "modo": "atlas", "centro": "cerebro", "total": total,
                           "nodes": nos, "edges": arestas}, ensure_ascii=False).encode("utf-8")
        return self._send(200, "application/json; charset=utf-8", body)

    def do_PUT(self) -> None:
        return self._send(405, "text/plain; charset=utf-8", b"read only", (("Allow", "GET"),))

    def do_DELETE(self) -> None:
        return self._send(405, "text/plain; charset=utf-8", b"read only", (("Allow", "GET"),))


def _selftest() -> int:
    global _STATUS_CACHE, _STATUS_CACHE_AT, _verify, collect, _chat_snapshot, _timer_snapshot
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

    original_verify, original_chat, original_timer = _verify, _chat_snapshot, _timer_snapshot

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
        return f"$ {command} (exit=0)\n\n" + body

    _verify = fake_verify
    _chat_snapshot = lambda: {"state": "unknown"}
    _timer_snapshot = lambda unit: {"unit": unit, "state": "unknown"}
    try:
        snapshot = collect()
        if WIKI_LIBERADA:
            wiki = _wiki_search("wiki", "ambos")
            assert [item["command"] for item in wiki["results"]] == ["busca_texto", "busca_semantica"]
            assert all(item["error"] is None for item in wiki["results"])
            assert "resultado textual" in wiki["results"][0]["output"]
            total_textual = len("$ busca_texto (exit=0)\n\nresultado textual demonstrativo " + ("x" * (WIKI_RESULT_MAX + 1)))
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
        _chat_snapshot = original_chat
        _timer_snapshot = original_timer

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
