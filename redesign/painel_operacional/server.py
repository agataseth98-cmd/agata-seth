#!/usr/bin/env python3
"""Painel operacional local da Agata. HTTP de leitura, preso a loopback."""
from __future__ import annotations

import argparse
import getpass
import hashlib
import http.client
import importlib.util
import collections
import json
import os
import socket
import re
import secrets
import select
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import urllib.error
import urllib.request
from urllib.parse import parse_qs, quote, unquote, urlparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
WEB = Path(__file__).resolve().parent
if str(WEB) not in sys.path:
    sys.path.insert(0, str(WEB))
import armazem  # noqa: E402
import qualidade_llm  # noqa: E402
import medicoes_painel  # noqa: E402
import sdd_painel  # noqa: E402
import nova_versao_painel  # noqa: E402
import chat_stream  # noqa: E402
import ferramentas_seth  # noqa: E402  (20/11/2026): ferramentas de leitura da Seth no seth-livre
import historia_painel  # noqa: E402
import modelos_painel  # noqa: E402
import importantes  # noqa: E402
import seth_voz  # noqa: E402
import seth_ditado  # noqa: E402
import relay_catalog  # noqa: E402  (17/11/2026, D7): fonte única dos provedores do Conselho
from relogio import FRESH_SECONDS, _now, _reading_window, _stamp  # noqa: E402
from armazem import (  # noqa: E402
    CONVERSA_LIMITE_BYTES, IMPORTACAO_LIMITE_BYTES, VAULT_ITENS, ErroConversa, _conversa_apagar, _conversa_caminho,
    _conversa_exportar, _conversa_gravar, _conversa_importar, _conversa_ler, _conversa_organizar, _conversas_buscar,
    _conversas_listar, _lixeira_listar, _lixeira_purgar, _lixeira_restaurar, _pasta_mudar, _registro_escrever,
    _vault_caminho, _vault_item)
BIND = "127.0.0.1"
PORT = 20146
VERIFIER_URL = "http://127.0.0.1:20141/verificar"
REFRESH_SECONDS = 60
CACHE_SECONDS = 3
WIKI_LIBERADA = True
LIMITE_RESPOSTA_VERIFICADOR = 262144
ALLOWED_ORIGIN = f"http://{BIND}:{PORT}"
GATEWAY_CHAT_URL = "http://127.0.0.1:20126/v1/chat/completions"  # constante: os testes trocam por servidor falso
CHAT_STREAM_LIMITE_BYTES = 262_144  # 16/11/2026 (C10): 20 mensagens com acentos mais anexos passavam de 131072
CHAT_STREAM_TIMEOUT_S = 120
# Organização das conversas (lote 3, 09/11/2026): pedidos pequenos de fixar, pasta, marcador, pasta e nome.
SETH_ORGANIZACAO_LIMITE_BYTES = 4096
# Importantes (11/11/2026): pedido de criar, mudar estado, editar ou trazer do Conselho; corpo até 4096 bytes.
IMPORTANTES_LIMITE_BYTES = 4096
IMPORTANTES_ROTAS = ("/api/importantes", "/api/importantes/estado", "/api/importantes/editar", "/api/importantes/trazer")
WIKI_RESULT_MAX = 12000
# Memória compartilhada do Conselho (aba Conselho > Memória compartilhada): leitura do cache, n de 1 a 200.
MEMORIA_CONSELHO_PADRAO = 40
MEMORIA_CONSELHO_MAX = 200
MEMORIA_CONSELHO_RECUSADO = "[conteúdo recusado: contém segredo (régua do P-1)]"

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
# Diário de eventos do sistema (escrito pela vigia da Equipe). Só leitura; o cliente não escolhe o caminho.
EVENTOS_DIARIO = Path.home() / ".cache/agata/sincronia/eventos.log"


def _eventos_recentes(limite: int = 60) -> bytes:
    """Últimas linhas do diário de eventos, em texto simples. Sem diário, diz que ainda não há eventos."""
    try:
        linhas = EVENTOS_DIARIO.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        linhas = []
    if not linhas:
        return b"(sem eventos ainda)\n"
    return ("\n".join(linhas[-limite:]) + "\n").encode("utf-8")
INTEGRATION_ALLOWLIST = (
    "piper-tts.service", "openvino-whisper.service", "openvino-embeddings.service",
    "obsidian-ro-proxy.service", "discord-mcp.service", "navegador-mcp.service",
    "laya-roteador.service", "seth-escriba.service",
    "painel-operacional.service", "agata-vigia@claude.service",
)
# Rótulos legíveis de unidades da allowlist que o front ainda não nomeia (S5, 16/11/2026).
INTEGRATION_ROTULOS = {"painel-operacional.service": "Painel operacional", "agata-vigia@claude.service": "Vigia do Claude"}
# Estado "ausente" (LoadState not-found): a unidade não existe no escopo do usuário (systemctl --user). Distinto de inactive e de unknown.
TEXTO_UNIDADE_AUSENTE = "unidade não existe no escopo do usuário desta Máquina"
# Cache curto de /api/capacidades e /api/lacunas (S6): não roda systemctl a cada chamada.
CACHE_CURTO_SECONDS = 10
_CACHE_CURTO: dict = {}
# Um lock por nome de cache (C6, 16/11/2026): uma rota lenta não segura a outra. O mestre só protege o dicionário de locks.
_CACHE_CURTO_LOCKS: dict = {}
_CACHE_CURTO_MESTRE = threading.Lock()
# Gateway da Seth (S1): a conversa do painel é o gateway em 127.0.0.1:20126; o chat antigo saiu do sistema em 07/11/2026.
GATEWAY_SETH_BASE = ("127.0.0.1", 20126)
_STATUS_LOCK = threading.Lock()
_WIKI_LOCK = threading.BoundedSemaphore(1)
_RELAY_LOCK = threading.BoundedSemaphore(1)
_RELAY_RATE_LOCK = threading.Lock()
_RELAY_REQUESTS: collections.deque[float] = collections.deque()
_RELAY_RATE_WINDOW_SECONDS = 60
_RELAY_RATE_LIMIT = 60
_SEM_CONVERSA_EM_CURSO = threading.BoundedSemaphore(1)
_PROPOSAL_LOCK = threading.BoundedSemaphore(1)
_SDD_LOCK = threading.Lock()
_UPLOAD_LOCK = threading.Lock()   # lote 5: um upload de fonte por vez
_DETAILS_LOCK = threading.Lock()
_DETAILS_CACHE: dict | None = None
_DETAILS_CACHE_AT: float | None = None

_ASSETS = {
    "/prototipo": ("prototipo.html", "text/html; charset=utf-8"),
    "/prototipo.css": ("prototipo.css", "text/css; charset=utf-8"),
    "/prototipo.js": ("prototipo.js", "text/javascript; charset=utf-8"),
    "/abrir.js": ("abrir.js", "text/javascript; charset=utf-8"),
    "/nova_versao.js": ("nova_versao.js", "text/javascript; charset=utf-8"),
    "/operator_console/app.js": ("operator_console/app.js", "text/javascript; charset=utf-8"),
    "/conselho-rede/app.js": ("conselho-rede/app.js", "text/javascript; charset=utf-8"),
    "/assets/agata-portrait.png": ("assets/agata-portrait.png", "image/png"),
    "/historia.js": ("historia.js", "text/javascript; charset=utf-8"),
    "/modelos.js": ("modelos.js", "text/javascript; charset=utf-8"),
}
# Telas antigas (painel unificado, spec 07/11/2026): link antigo cai na seção certa do /prototipo.
_REDIRECTS = {
    "/": "/prototipo#panorama",
    "/index.html": "/prototipo#panorama",
    "/frentes": "/prototipo#panorama",
    "/operator_console": "/prototipo#qualidade",
    "/operator_console/": "/prototipo#qualidade",
    "/conselho-rede": "/prototipo#conselho",
    "/conselho-rede/": "/prototipo#conselho",
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


def _same_origin_request(fetch_site: str | None, origin: str | None) -> bool:
    if fetch_site and fetch_site not in {"same-origin", "none"}:
        return False
    return not origin or origin == ALLOWED_ORIGIN


def _escrita_permitida(fetch_site: str | None, origin: str | None) -> bool:
    """Escrita de conversa (salvar, apagar, organizar, pastas, importar, restaurar, purgar) (09/11/2026): precisa de
    Origin igual ao do painel ou Sec-Fetch-Site same-origin. Sem cabeçalho nenhum, 403. Cabeçalho que diz outra
    origem (cross-site, Origin de outro site) também é 403, mesmo que o outro cabeçalho bata."""
    if fetch_site not in (None, "same-origin") or (origin is not None and origin != ALLOWED_ORIGIN):
        return False
    return fetch_site == "same-origin" or origin == ALLOWED_ORIGIN


def _linhas_do_gateway(resposta):
    """Linhas de texto do stream do gateway. Queda de conexão encerra o stream; quem chama emite 'stream interrompido'."""
    try:
        for linha in resposta:
            yield linha.decode("utf-8", errors="replace")
    except (OSError, http.client.HTTPException):
        return


def _abrir_gateway(pedido: dict):
    """Abre o pedido de chat no gateway e devolve (resposta, socket). Status 4xx/5xx vira OSError, como antes
    (urllib), e a UI recebe 'gateway indisponível'. O socket é pego ANTES de getresponse: sem Content-Length
    (HTTP/1.0), o http.client solta conexao.sock e o passa à resposta. Quem fecha a resposta fecha o socket."""
    destino = urlparse(GATEWAY_CHAT_URL)
    conexao = http.client.HTTPConnection(destino.hostname, destino.port, timeout=CHAT_STREAM_TIMEOUT_S)
    resposta = None
    try:
        conexao.request("POST", destino.path or "/", body=json.dumps(pedido).encode("utf-8"),
                        headers={"Content-Type": "application/json", "Accept": "text/event-stream"})
        sock = conexao.sock
        resposta = conexao.getresponse()
        if resposta.status >= 400:
            raise OSError(f"gateway respondeu {resposta.status}")
    except Exception:
        if resposta is not None:
            resposta.close()
        conexao.close()
        raise
    return resposta, sock


def _derrubar_gateway(sock) -> None:
    """Corta a conexão com o gateway a partir de outra thread. shutdown acorda a leitura bloqueada; close sozinho não acorda."""
    if sock is not None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass


class _SocketAtual:
    """Aponta para o socket da resposta do gateway em curso: o laço de ferramentas abre uma resposta por rodada,
    e a vigia do navegador precisa derrubar a que estiver aberta."""
    def __init__(self, sock=None):
        self.sock = sock

    def shutdown(self, como):
        if self.sock is not None:
            self.sock.shutdown(como)


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


def _memoria_conselho_modulo():
    """Módulo do cache do Conselho, usado só para ler. A gravação fica com o CLI e com a Seth."""
    path = str(ROOT / "redesign/router")
    if path not in sys.path:
        sys.path.insert(0, path)
    import cache_conselho
    return cache_conselho


def _memoria_entrada(cache, reg: dict) -> dict:
    """Uma entrada para a tela. Aplica ao lido o mesmo filtro da gravação (cache_conselho.filtrar):
    dado pessoal vira marca e texto com segredo não sai."""
    def limpo(valor) -> str:
        try:
            return cache.filtrar(str(valor))
        except ValueError:
            return MEMORIA_CONSELHO_RECUSADO
    ts = str(reg.get("ts", ""))
    try:
        data_hora = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").strftime("%d/%m/%Y %H:%M")
    except ValueError:
        data_hora = limpo(ts)
    return {"n": reg.get("n"), "data_hora": data_hora, "autor": limpo(reg.get("autor", "")),
            "tipo": limpo(reg.get("tipo", "")), "texto": limpo(reg.get("texto", ""))}


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
    expected_mode = {"browser_tab_only": "browser_tab", "manual_only": "manual"}.get(
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
    if load == "not-found":
        return {
            "unit": unit, "state": "ausente", "load_state": load, "active_state": active,
            "sub_state": values["SubState"], "source": "seth-verificador", "source_ref": "unidade:" + unit,
            "observed_at": observed_at, "fresh_until": fresh_until, "error": TEXTO_UNIDADE_AUSENTE,
        }
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
    # "ausente" conta como warning: antes desta mudança, unidade não encontrada já caía em warning.
    if any(state in ("warning", "ausente") for state in states):
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
        if len(proc.stdout) > 8192:
            raise ValueError("consulta ao timer indisponível")
        values = _parse_pairs(proc.stdout)
        if values.get("LoadState") == "not-found":
            result.update({"state": "ausente", "error": TEXTO_UNIDADE_AUSENTE})
        else:
            if proc.returncode != 0:
                raise ValueError("consulta ao timer indisponível")
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
        if values.get("LoadState") == "not-found":
            execution.update({"state": "ausente", "error": TEXTO_UNIDADE_AUSENTE})
        else:
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
    """Conversa com a Seth: GET na raiz do gateway (127.0.0.1:20126). Só mede que responde; não prova a conversa inteira."""
    host, porta = GATEWAY_SETH_BASE
    result = {"state": "unknown", "source": "seth-gateway", "source_ref": f"{host}:{porta}/"}
    connection = http.client.HTTPConnection(host, porta, timeout=3)
    try:
        connection.request("GET", "/")
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
    "conversar": {"units": ["seth-gateway.service"], "http": ["http://127.0.0.1:20126/"],
                  "fonte": "seth-gateway · 127.0.0.1:20126"},
    "ouvir": {"units": ["piper-tts.service"], "http": []},
    "buscar": {"units": ["seth-verificador.service"], "http": []},
    "verificar": {"units": ["seth-verificador.service"], "http": ["http://127.0.0.1:20141/"]},
    "navegar": {"units": ["navegador-mcp.service", "discord-mcp.service"], "http": []},
    "rota": {"units": ["seth-gateway.service"], "http": []},
    "manutencao": {"units": ["agata-manutencao.timer"], "http": []},
    "acrescentar": {"units": ["seth-escriba.service"], "http": []},
}


def _estado_systemd(unit: str, sistema: bool = False) -> str | None:
    """'ativa' ou 'inativa' se a unidade existe; 'ausente' se o systemd diz not-found; None se não deu para ler.
    `sistema=True` consulta a unidade de sistema (sem --user)."""
    comando = ["/usr/bin/systemctl"] + ([] if sistema else ["--user"])
    try:
        proc = subprocess.run(comando + ["show", "--no-pager", "--property=ActiveState,LoadState", "--", unit],
                              capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    valores = _parse_pairs(proc.stdout)
    if valores.get("LoadState") == "not-found":
        return "ausente"
    if valores.get("LoadState") != "loaded":
        return None
    return "ativa" if valores.get("ActiveState") == "active" else "inativa"


def _unidade_ativa(unit: str) -> bool | None:
    estado = _estado_systemd(unit)
    return None if estado in (None, "ausente") else estado == "ativa"


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
        itens.append({"id": nome, "state": estado, "source": sondas.get("fonte", "systemctl --user show; HTTP local"),
                      "source_ref": ", ".join(sondas["units"] + sondas["http"]),
                      "evidencia": "Medido agora (" + observed_at + "): " + "; ".join(partes) + ".",
                      "observed_at": observed_at, "fresh_until": fresh_until})
    return {"schema_version": 1, "state": "ok", "observed_at": observed_at, "fresh_until": fresh_until, "items": itens}


def _porta_responde(porta: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", porta), timeout=1):
            return True
    except OSError:
        return False


def _tipo_unidade_usuario(unit: str) -> str | None:
    """Type da unidade de usuário (`oneshot`, `simple`...), para a mesma regra do P-9: oneshot não é lacuna."""
    try:
        proc = subprocess.run(["/usr/bin/systemctl", "--user", "show", "--no-pager", "--property=Type", "--", unit],
                              capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return _parse_pairs(proc.stdout).get("Type")


def _lacunas_snapshot() -> dict:
    """Lacunas declaradas no canon (ESTADO.md, Serviços (boot); gerado de config/servicos-agata.txt), conferidas agora:
    - unidade systemd citada (`nome.service` / `nome.timer`): sem leitura ou inativa vira lacuna; oneshot não;
    - item com porta declarada (`:NNNN`) que não responde em 127.0.0.1 vira lacuna."""
    observed_at, fresh_until = _reading_window()
    try:
        texto = (ROOT / "ESTADO.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"schema_version": 1, "state": "unknown", "observed_at": observed_at, "fresh_until": fresh_until,
                "total_declaradas": 0, "items": [{"nome": "ESTADO.md", "motivo": "fonte do estado indisponível", "fonte": "ESTADO.md"}]}
    inicio = texto.find("## Serviços (boot)")
    fim = texto.find("\n## ", inicio + 1) if inicio >= 0 else -1
    secao = (texto[inicio:fim] if fim > inicio else texto[inicio:]) if inicio >= 0 else ""
    itens = []
    if not secao:
        itens.append({"nome": "seção Serviços (boot)", "motivo": "seção não encontrada em ESTADO.md", "fonte": "ESTADO.md"})
    vistas = set(); declaradas = 0
    for linha in secao.splitlines():
        for unit in re.findall(r"`([a-z0-9@._-]+\.(?:service|timer))`", linha):
            if unit in vistas: continue
            vistas.add(unit); declaradas += 1
            if _tipo_unidade_usuario(unit) == "oneshot":
                continue
            estado = _estado_systemd(unit)
            if estado in (None, "ausente"):
                estado = _estado_systemd(unit, sistema=True)
            if estado == "ausente":
                itens.append({"nome": unit, "state": "ausente", "motivo": TEXTO_UNIDADE_AUSENTE, "fonte": "ESTADO.md · Serviços (boot)"})
            elif estado is None:
                itens.append({"nome": unit, "motivo": "sem leitura do systemd agora (não consultada)", "fonte": "ESTADO.md · Serviços (boot)"})
            elif estado == "inativa":
                itens.append({"nome": unit, "motivo": "declarada no boot e inativa agora", "fonte": "ESTADO.md · Serviços (boot)"})
        if not linha.lstrip().startswith("- "):
            continue
        m = re.search(r"`([a-z][a-z0-9-]+)`.{0,40}?:(\d{4,5})\b", linha)
        if m and not re.search(r"\.(service|timer)$", m.group(1)):
            declaradas += 1
            if not _porta_responde(int(m.group(2))):
                itens.append({"nome": m.group(1) + " :" + m.group(2), "motivo": "porta declarada não responde em 127.0.0.1", "fonte": "ESTADO.md · Serviços (boot)"})
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
    for item in integrations:
        if item["unit"] in INTEGRATION_ROTULOS:
            item["rotulo"] = INTEGRATION_ROTULOS[item["unit"]]
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


def _fontes_sem_leitura(services: list, timers: list, git: dict, chat: dict,
                        maintenance: dict, proposals: dict, models: dict) -> list[str]:
    """Nomes legíveis das fontes que não foram lidas (state unknown). Lista vazia = todas lidas.
    'ausente' (unidade que não existe nesta Máquina) NÃO entra: já aparece como ausente, separado (17/11/2026, D9)."""
    fontes = [(item["unit"], item) for item in services]
    fontes += [(item["unit"], item) for item in timers]
    fontes += [("Git local", git), ("Conversa com a Seth (gateway)", chat), ("Tarefas de manutenção", maintenance),
               ("Propostas", proposals), ("Modelos (registro de capacidades)", models)]
    return [nome for nome, leitura in fontes if leitura.get("state") == "unknown"]


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
    maintenance = _maintenance_tasks()
    proposals = _proposal_snapshot()
    models = _model_snapshot()
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
        "maintenance": maintenance,
        "proposals": proposals,
        "models": models,
        "sem_leitura": _fontes_sem_leitura(services, timers, git, chat, maintenance, proposals, models),
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


def _lock_do_cache_curto(nome: str):
    """Lock próprio de cada nome de cache (C6): criado sob o lock mestre, na primeira vez que o nome aparece."""
    with _CACHE_CURTO_MESTRE:
        lock = _CACHE_CURTO_LOCKS.get(nome)
        if lock is None:
            lock = _CACHE_CURTO_LOCKS[nome] = threading.Lock()
        return lock


def _cached_curto(nome: str, produzir) -> dict:
    """Mesmo padrão de _cached_status, por nome, com CACHE_CURTO_SECONDS (S6): não roda systemctl a cada GET."""
    with _lock_do_cache_curto(nome):
        agora = time.monotonic()
        salvo = _CACHE_CURTO.get(nome)
        if salvo is not None and agora - salvo[0] < CACHE_CURTO_SECONDS:
            return salvo[1]
        valor = produzir()
        _CACHE_CURTO[nome] = (time.monotonic(), valor)
        return valor


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


# Botões "Abrir" do painel. Lista FIXA: o painel só pede um destino pelo nome; nunca um comando ou caminho.
# Derivada do catálogo de provedores do Conselho (17/11/2026, D7). omniroute é o roteador local: não é provedor do catálogo.
ABRIR_PROVEDORES = {provedor["id"]: provedor["site"] for provedor in relay_catalog.PROVIDERS}
ABRIR_PROVEDORES["omniroute"] = "http://127.0.0.1:20128/"
# ---------------------------------------------------------------------------------------------------------------
# Leituras da Equipe, do backup, do egress, do perímetro, do CI e dos provedores (17/11/2026, lote 2b).
# Todas: GET, sem parâmetro do cliente, caminho fixo no código (a pasta pode vir de variável de ambiente do
# serviço, nunca da requisição), leitura com teto de tamanho, cache curto (_cached_curto) e campos state,
# source, observed_at, fresh_until. Ausência de dado = state sem_leitura com motivo, nunca lista vazia muda.
# Nenhuma delas executa o perímetro, o CI, o restic, cargo nem equipe.py: só lê o que os outros deixaram.
# ---------------------------------------------------------------------------------------------------------------
LIMITE_LEITURA_JSON = 262_144
EQUIPE_AGENTE_RE = re.compile(r"[a-z][a-z0-9-]{0,30}")          # mesmo formato de equipe.py (MEMBRO)
EQUIPE_ESTADO_RE = re.compile(r"[a-z_]{1,30}")
EQUIPE_UNIT_RE = re.compile(r"agata-vigia@[a-z][a-z0-9-]{0,30}\.service")
EQUIPE_AUSENTES_CONFIG = ROOT / "config/equipe-ausentes.txt"
DIARIO_LINHAS = 20
REGUA_BACKUP_DIAS = 14                                           # mesma régua do P-12 (scripts/perimetro.sh, P12_N_DIAS)
BACKUP_RECURSO_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,120}")
BACKUP_SNAPSHOT_RE = re.compile(r"[A-Za-z0-9._:-]{1,80}")
EGRESS_CRATE_REL = "redesign/rust/egress"
EGRESS_REGRA_ARQ = ROOT / "scripts/egress_em_dia.py"   # a regra de "em dia" é a do script, lida daqui (não da raiz do crate)
EGRESS_UNIT = "navegador-mcp.service"
CONTROLE_RE = re.compile(r"P-[A-Z0-9][A-Z0-9-]{0,30}")
VEREDITOS = ("OK", "SKIP", "PARCIAL", "FALHA")
HEAD_RE = re.compile(r"[0-9a-f]{4,40}")
RESULTADO_VELHO_HORAS = 24  # R1 (17/11/2026): resultado gravado há mais de 24 h não sai "ok"
_SP = ZoneInfo("America/Sao_Paulo")


def _leitura_segura(produzir) -> dict:
    """Erro inesperado numa leitura nova não derruba a rota: vira sem_leitura, sem o texto do erro."""
    try:
        return produzir()
    except Exception:  # noqa: BLE001 — a rota responde; o motivo não traz detalhe interno
        observed_at, fresh_until = _reading_window()
        return {"state": "sem_leitura", "motivo": "leitura indisponível agora", "observed_at": observed_at,
                "fresh_until": fresh_until}


def _ler_json_limitado(arq: Path) -> dict:
    """Objeto JSON de arquivo local, com teto de tamanho. Erro de leitura ou de formato sobe como OSError/ValueError."""
    if arq.stat().st_size > LIMITE_LEITURA_JSON:
        raise ValueError("arquivo acima do limite")
    dados = json.loads(arq.read_text(encoding="utf-8"))
    if not isinstance(dados, dict):
        raise ValueError("formato inesperado")
    return dados


def _texto_curto(valor, limite: int = 80) -> str | None:
    """Campo de arquivo local: só texto, sem caractere de controle, com teto. Qualquer outro tipo vira None."""
    if not isinstance(valor, str):
        return None
    limpo = re.sub(r"[\x00-\x1f\x7f]", "", valor)[:limite]
    return limpo or None


def _arquivos(pasta: Path, padrao: str) -> list[Path]:
    try:
        return sorted(pasta.glob(padrao))
    except OSError:
        return []


def _iso_de_tempo(ts: float) -> str:
    return datetime.fromtimestamp(ts, _SP).isoformat(timespec="seconds")


# --- Equipe (D1): só lê sessao.json, estado-*.json, ausencia-*.json, config/equipe-ausentes.txt e o diário ---
def _equipe_pasta() -> Path:
    return Path(os.environ.get("AGATA_EQUIPE_DIR", Path.home() / ".cache/agata/sincronia/equipe"))


def _equipe_diario() -> Path:
    return Path(os.environ.get("AGATA_EQUIPE_DIARIO", EVENTOS_DIARIO))


def _ausentes_config() -> tuple[set | None, str | None]:
    """Agentes listados como ausentes no config (um por linha, # comenta). (None, motivo) se não der para ler."""
    try:
        if EQUIPE_AUSENTES_CONFIG.stat().st_size > 65_536:
            raise ValueError("acima do limite")
        texto = EQUIPE_AUSENTES_CONFIG.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None, "config/equipe-ausentes.txt indisponível"
    nomes = set()
    for linha in texto.splitlines():
        nome = linha.split("#", 1)[0].strip()
        if not nome:
            continue
        if not EQUIPE_AGENTE_RE.fullmatch(nome):
            return None, "linha inválida em config/equipe-ausentes.txt"
        nomes.add(nome)
    return nomes, None


def _diario_recente(arq: Path, n: int = DIARIO_LINHAS, limite_bytes: int = 65_536) -> dict:
    """Últimas linhas do diário de eventos (uma linha por evento). Lê só a cauda. Nunca abre o canal de mensagens."""
    try:
        tamanho = arq.stat().st_size
        with arq.open("rb") as arquivo:
            if tamanho > limite_bytes:
                arquivo.seek(tamanho - limite_bytes)
            cauda = arquivo.read(limite_bytes)
    except OSError:
        return {"state": "sem_leitura", "motivo": "diário de eventos ausente", "linhas": []}
    linhas = cauda.decode("utf-8", errors="replace").splitlines()
    if tamanho > limite_bytes and linhas:
        linhas = linhas[1:]  # a primeira linha da cauda pode ter sido cortada
    linhas = [limpa for limpa in (_texto_curto(linha, 300) for linha in linhas) if limpa][-n:]
    if not linhas:
        return {"state": "ok", "motivo": "diário sem eventos", "linhas": []}
    return {"state": "ok", "linhas": linhas}


def _equipe_snapshot() -> dict:
    observed_at, fresh_until = _reading_window()
    pasta = _equipe_pasta()
    sessao, motivo_sessao = None, None
    try:
        sessao = _ler_json_limitado(pasta / "sessao.json")
    except (OSError, ValueError):
        motivo_sessao = "sessao.json ausente ou ilegível: nenhuma partida registrada nesta Máquina"
    presentes, esperados = [], []
    if sessao is not None:
        bruto = sessao.get("presentes") if isinstance(sessao.get("presentes"), dict) else {}
        for agente in sorted(bruto)[:50]:
            info = bruto[agente]
            if EQUIPE_AGENTE_RE.fullmatch(agente):
                presentes.append({"agente": agente,
                                  "desde": _texto_curto(info.get("chegou_em") if isinstance(info, dict) else None, 40)})
        lista = sessao.get("esperados") if isinstance(sessao.get("esperados"), list) else []
        esperados = [a for a in lista[:50] if isinstance(a, str) and EQUIPE_AGENTE_RE.fullmatch(a)]
        estado = _texto_curto(sessao.get("estado"), 30)
        base = sessao.get("base") if isinstance(sessao.get("base"), str) and HEAD_RE.fullmatch(sessao["base"]) else None
        bloco_sessao = {"state": "warning" if estado == "divergente" else "ok", "estado": estado,
                        "base": base[:12] if base else None, "presentes": presentes, "esperados": esperados}
    else:
        bloco_sessao = {"state": "sem_leitura", "motivo": motivo_sessao, "estado": None, "base": None,
                        "presentes": [], "esperados": []}
    presentes_nomes = {p["agente"] for p in presentes}

    config, motivo_config = _ausentes_config()
    declarados = {}
    for arq in _arquivos(pasta, "ausencia-*.json")[:50]:
        agente = arq.name[len("ausencia-"):-len(".json")]
        if not EQUIPE_AGENTE_RE.fullmatch(agente):
            continue
        try:
            info = _ler_json_limitado(arq)
            declarados[agente] = {"desde": _texto_curto(info.get("desde"), 40),
                                  "motivo": _texto_curto(info.get("motivo"), 200), "ate": _texto_curto(info.get("ate"), 40)}
        except (OSError, ValueError):
            declarados[agente] = {"desde": None, "motivo": "arquivo de ausência ilegível", "ate": None}
    itens_ausentes = []
    for agente in sorted(set(config or ()) | set(declarados)):
        origem = (["config"] if config and agente in config else []) + (["ausencia"] if agente in declarados else [])
        info = declarados.get(agente, {})
        itens_ausentes.append({"agente": agente, "origem": origem, "desde": info.get("desde"),
                               "motivo": info.get("motivo"), "ate": info.get("ate")})
    bloco_ausentes = {"state": "ok" if config is not None else "sem_leitura", "itens": itens_ausentes}
    if config is None:
        bloco_ausentes["motivo"] = motivo_config

    divergencias, divergencias_motivo = [], None
    if sessao is None:
        divergencias_motivo = "sessão indisponível: não dá para comparar com os presentes"
    else:
        for agente in sorted(config or ()):
            if agente in presentes_nomes:
                divergencias.append(f"{agente}: ausente no config e presente na sessão")
        for agente in sorted(declarados):
            if agente in presentes_nomes:
                divergencias.append(f"{agente}: ausência declarada (ausencia-{agente}.json) e presente na sessão")
            if config is not None and agente not in config:
                divergencias.append(f"{agente}: ausência declarada na sessão e fora do config")

    agentes_itens = []
    for arq in _arquivos(pasta, "estado-*.json")[:50]:
        agente = arq.name[len("estado-"):-len(".json")]
        if not EQUIPE_AGENTE_RE.fullmatch(agente):
            continue
        try:
            brutos = _ler_json_limitado(arq).get("itens")
            if not isinstance(brutos, dict):
                raise ValueError("itens fora do formato")
            por_estado: dict = {}
            for valor in brutos.values():
                estado = valor.get("estado") if isinstance(valor, dict) else None
                chave = estado if isinstance(estado, str) and EQUIPE_ESTADO_RE.fullmatch(estado) else "sem_estado"
                por_estado[chave] = por_estado.get(chave, 0) + 1
            agentes_itens.append({"agente": agente, "state": "ok", "total": len(brutos),
                                  "por_estado": dict(sorted(por_estado.items()))})
        except (OSError, ValueError):
            agentes_itens.append({"agente": agente, "state": "sem_leitura", "motivo": "estado do agente ilegível"})
    if agentes_itens:
        bloco_itens = {"state": "ok", "agentes": agentes_itens}
    else:
        bloco_itens = {"state": "sem_leitura", "motivo": "nenhum estado-<agente>.json nesta Máquina", "agentes": []}

    if not esperados:
        bloco_vigias = {"state": "sem_leitura", "itens": [],
                        "motivo": "a sessão não declara agentes esperados (campo esperados)" if sessao is not None else motivo_sessao}
    else:
        unidades = [f"agata-vigia@{agente}.service" for agente in esperados]
        unidades = [u for u in unidades if EQUIPE_UNIT_RE.fullmatch(u)]
        with ThreadPoolExecutor(max_workers=3) as pool:
            leituras = list(pool.map(_service_snapshot, unidades))
        vigias = [{"agente": u[len("agata-vigia@"):-len(".service")], "unit": u,
                   "state": "sem_leitura" if leitura["state"] == "unknown" else leitura["state"],
                   "active_state": leitura.get("active_state")} for u, leitura in zip(unidades, leituras)]
        bloco_vigias = {"state": "ok", "itens": vigias}

    if sessao is None:
        estado_geral = "sem_leitura"
    else:
        alerta_vigia = any(v["agente"] in presentes_nomes and v["state"] != "ok" for v in bloco_vigias["itens"])
        estado_geral = "warning" if (divergencias or bloco_sessao["state"] == "warning" or alerta_vigia) else "ok"
    value = {"schema_version": 1, "state": estado_geral,
             "source": "sincronia/equipe (sessao.json, estado-*.json, ausencia-*.json); config/equipe-ausentes.txt; "
                       "systemctl --user (vigias); diário eventos.log (só a cauda)",
             "observed_at": observed_at, "fresh_until": fresh_until, "sessao": bloco_sessao, "ausentes": bloco_ausentes,
             "divergencias": divergencias, "divergencias_motivo": divergencias_motivo, "itens": bloco_itens,
             "vigias": bloco_vigias, "eventos": _diario_recente(_equipe_diario())}
    if sessao is None:
        value["motivo"] = motivo_sessao
    return value


# --- Backup (D2): só lê o cache do P-12, os marcadores e a 1ª linha de ~/.config/agata/hd-backup. Não roda restic. ---
def _backup_pasta() -> Path:
    return Path(os.environ.get("AGATA_BACKUP_STAGING_DIR", Path.home() / ".agata-backup-staging"))


def _hd_backup() -> dict:
    """HD de backup como o perímetro: 1ª linha de hd-backup; sem o arquivo, a pasta AgataBkup01 em /run/media.
    O caminho não sai na resposta; só presente e repositório_presente."""
    arq = Path(os.environ.get("AGATA_HD_BACKUP_CONFIG", Path.home() / ".config/agata/hd-backup"))
    linha = ""
    try:
        if arq.stat().st_size <= 4096:
            linha = arq.read_text(encoding="utf-8").splitlines()[0].strip()
    except (OSError, ValueError, IndexError):
        linha = ""
    try:
        hd = Path(linha) if linha else Path("/run/media") / getpass.getuser() / "AgataBkup01"
        presente = hd.is_dir()
        repo = Path(os.environ["AGATA_RESTIC_REPO"]) if os.environ.get("AGATA_RESTIC_REPO") else hd / "restic-agata-local"
        repositorio = presente and repo.is_dir()
    except (OSError, KeyError, ValueError):
        return {"presente": None, "repositorio_presente": None, "motivo": "HD não pôde ser consultado agora"}
    return {"presente": presente, "repositorio_presente": bool(repositorio),
            "motivo": None if presente else "pasta do HD ausente (disco desmontado ou desconectado)"}


def _backup_snapshot() -> dict:
    observed_at, fresh_until = _reading_window()
    pasta = _backup_pasta()
    agora = _now()
    try:
        pendentes = sum(1 for p in pasta.glob("PENDENTE-HD-DESCONECTADO*") if p.is_file())
    except OSError:
        pendentes = None
    base = {"schema_version": 1,
            "source": "p12-cobertura.json (cache do P-12), marcadores PENDENTE-HD-DESCONECTADO*, HD pela configuração "
                      "local; restic não é executado",
            "observed_at": observed_at, "fresh_until": fresh_until, "hd": _hd_backup(), "pendentes_hd": pendentes,
            "regua_dias": REGUA_BACKUP_DIAS}
    try:
        cache = _ler_json_limitado(pasta / "p12-cobertura.json")
    except (OSError, ValueError):
        return {**base, "state": "sem_leitura", "motivo": "cache de cobertura (p12-cobertura.json) ausente ou ilegível",
                "recursos": []}
    recursos, ignorados = [], 0
    for nome in sorted(cache)[:200]:
        if not BACKUP_RECURSO_RE.fullmatch(nome):
            ignorados += 1
            continue
        valor = cache[nome]
        try:
            verificado = datetime.fromisoformat(valor["verificado_em"])
            if verificado.tzinfo is None:
                raise ValueError("sem fuso")
        except (KeyError, TypeError, ValueError):
            recursos.append({"recurso": nome, "state": "sem_leitura", "motivo": "registro sem data com fuso",
                             "dentro_da_regua": None})
            continue
        idade = (agora - verificado).total_seconds() / 86400
        snap = valor.get("snapshot")
        recursos.append({"recurso": nome, "state": "ok", "verificado_em": verificado.isoformat(timespec="seconds"),
                         "idade_dias": round(idade, 2),
                         "snapshot": snap if isinstance(snap, str) and BACKUP_SNAPSHOT_RE.fullmatch(snap) else None,
                         "dentro_da_regua": idade <= REGUA_BACKUP_DIAS})
    if not recursos:
        return {**base, "state": "sem_leitura", "motivo": "cache sem nenhum recurso com nome válido", "recursos": []}
    fora = any(r["state"] != "ok" or r["dentro_da_regua"] is False for r in recursos)
    value = {**base, "state": "warning" if fora else "ok", "recursos": recursos}
    if ignorados:
        value["ignorados"] = ignorados
    return value


# --- Egress (D3): mesma regra de em dia de scripts/egress_em_dia.py (importada, sem subprocess) ---
def _egress_em_dia_modulo():
    spec = importlib.util.spec_from_file_location("egress_em_dia_painel", EGRESS_REGRA_ARQ)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _navegador_usa_rust() -> bool | None:
    """True se a unidade do navegador tem AGATA_EGRESS_RUST com valor. Só essa chave é lida; o valor não sai."""
    try:
        proc = subprocess.run(["/usr/bin/systemctl", "--user", "show", "--no-pager",
                               "--property=LoadState,Environment", "--", EGRESS_UNIT],
                              capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0 or len(proc.stdout) > 65_536:
        return None
    valores = _parse_pairs(proc.stdout)
    if valores.get("LoadState") != "loaded" or "Environment" not in valores:
        return None
    for token in valores["Environment"].split():
        if token.startswith("AGATA_EGRESS_RUST="):
            return bool(token[len("AGATA_EGRESS_RUST="):])
    return False


def _egress_snapshot() -> dict:
    observed_at, fresh_until = _reading_window()
    crate = ROOT / EGRESS_CRATE_REL
    base = {"schema_version": 1,
            "source": "redesign/rust/egress/target/release (mtime; regra de scripts/egress_em_dia.py) · systemctl --user "
                      "show navegador-mcp.service",
            "observed_at": observed_at, "fresh_until": fresh_until, "paridade": "sem registro"}
    try:
        modulo = _egress_em_dia_modulo()
        if not (crate / "src").is_dir():
            return {**base, "state": "sem_leitura", "motivo": "crate redesign/rust/egress sem src/ nesta árvore",
                    "binarios": [], "navegador_usa_rust": _navegador_usa_rust()}
        fontes = modulo.fontes(crate)
        mais_nova = max((f.stat().st_mtime for f in fontes), default=0.0)
        binarios = []
        for caminho in modulo.binarios(crate):
            presente = caminho.is_file()
            mtime = caminho.stat().st_mtime if presente else None
            binarios.append({"nome": caminho.name, "presente": presente,
                             "mtime": _iso_de_tempo(mtime) if mtime is not None else None,
                             "em_dia": bool(presente and mtime > mais_nova)})
        motivo = modulo.motivo(crate)
    except (OSError, ValueError, ImportError, SyntaxError):
        return {**base, "state": "sem_leitura", "motivo": "regra de em dia indisponível agora", "binarios": [],
                "navegador_usa_rust": None}
    value = {**base, "state": "ok" if all(b["em_dia"] for b in binarios) else "warning", "binarios": binarios,
             "fonte_mais_nova": _iso_de_tempo(mais_nova) if fontes else None,
             "navegador_usa_rust": _navegador_usa_rust()}
    if motivo:
        value["motivo"] = motivo
    return value


# --- Perímetro e CI (D4/D5/D6): só leem o ultimo.json que cada um grava ao terminar. Nunca executam nada. ---
def _perimetro_pasta() -> Path:
    return Path(os.environ.get("AGATA_PERIMETRO_DIR", Path.home() / ".cache/agata/perimetro"))


def _ci_pasta() -> Path:
    return Path(os.environ.get("AGATA_CI_DIR", Path.home() / ".cache/agata/ci"))


def _data_com_fuso(valor) -> datetime | None:
    if not isinstance(valor, str) or len(valor) > 40:
        return None
    try:
        dt = datetime.fromisoformat(valor)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else None


def _inteiro_pequeno(valor) -> bool:
    return type(valor) is int and 0 <= valor <= 100_000


def _envelhece(state: str, idade_horas: float) -> tuple[str, dict]:
    """R1 (17/11/2026): resultado gravado há mais de RESULTADO_VELHO_HORAS não sai "ok" (vira "warning") e a resposta diz por quê."""
    if idade_horas <= RESULTADO_VELHO_HORAS:
        return state, {"envelhecido": False}
    return ("warning" if state == "ok" else state), {"envelhecido": True, "motivo": f"resultado gravado há {int(idade_horas)} h"}


def _perimetro_snapshot() -> dict:
    observed_at, fresh_until = _reading_window()
    base = {"schema_version": 1, "source": "scripts/perimetro.sh → ultimo.json (gravado ao fim de cada execução)",
            "observed_at": observed_at, "fresh_until": fresh_until}
    arq = _perimetro_pasta() / "ultimo.json"
    if not arq.is_file():
        return {**base, "state": "sem_leitura", "motivo": "o perímetro ainda não gravou resultado nesta Máquina"}
    try:
        dados = _ler_json_limitado(arq)
    except (OSError, ValueError):
        return {**base, "state": "sem_leitura", "motivo": "ultimo.json do perímetro ilegível ou acima do limite"}
    gerado = _data_com_fuso(dados.get("gerado_em"))
    geral = dados.get("resultado_geral")
    contagens_brutas = dados.get("contagens") if isinstance(dados.get("contagens"), dict) else {}
    chaves = ("ok", "skip", "parcial", "falha")
    if gerado is None or geral not in ("OK", "FALHA") or not all(_inteiro_pequeno(contagens_brutas.get(k)) for k in chaves):
        return {**base, "state": "sem_leitura", "motivo": "ultimo.json do perímetro com campos inválidos"}
    controles = []
    for item in (dados.get("controles") if isinstance(dados.get("controles"), list) else [])[:200]:
        if (isinstance(item, dict) and isinstance(item.get("id"), str) and CONTROLE_RE.fullmatch(item["id"])
                and item.get("veredito") in VEREDITOS):
            controles.append({"id": item["id"], "veredito": item["veredito"]})
    if not controles:
        return {**base, "state": "sem_leitura", "motivo": "ultimo.json do perímetro sem nenhum controle válido"}
    contagens = {k: contagens_brutas[k] for k in chaves}
    head = dados.get("head") if isinstance(dados.get("head"), str) and HEAD_RE.fullmatch(dados["head"]) else None
    if geral == "FALHA":
        state = "falha"
    else:
        state = "warning" if (contagens["skip"] or contagens["parcial"]) else "ok"
    idade = round((_now() - gerado).total_seconds() / 3600, 2)
    state, velho = _envelhece(state, idade)
    return {**base, "state": state, "gerado_em": gerado.isoformat(timespec="seconds"),
            "idade_horas": idade, "head": head,
            "resultado_geral": geral, "contagens": contagens, "controles": controles, **velho}


def _ci_snapshot() -> dict:
    observed_at, fresh_until = _reading_window()
    base = {"schema_version": 1, "source": "scripts/ci_sdd_local.sh → ultimo.json (gravado ao fim de cada execução)",
            "observed_at": observed_at, "fresh_until": fresh_until}
    arq = _ci_pasta() / "ultimo.json"
    if not arq.is_file():
        return {**base, "state": "sem_leitura", "motivo": "o CI local ainda não gravou resultado nesta Máquina"}
    try:
        dados = _ler_json_limitado(arq)
    except (OSError, ValueError):
        return {**base, "state": "sem_leitura", "motivo": "ultimo.json do CI ilegível ou acima do limite"}
    gerado = _data_com_fuso(dados.get("gerado_em"))
    if gerado is None or not _inteiro_pequeno(dados.get("ok")) or not _inteiro_pequeno(dados.get("falha")):
        return {**base, "state": "sem_leitura", "motivo": "ultimo.json do CI com campos inválidos"}
    passos = []
    for item in (dados.get("passos") if isinstance(dados.get("passos"), list) else [])[:300]:
        nome = _texto_curto(item.get("nome") if isinstance(item, dict) else None, 200)
        if nome and isinstance(item.get("ok"), bool):
            passos.append({"nome": nome, "ok": item["ok"]})
    if not passos:
        return {**base, "state": "sem_leitura", "motivo": "ultimo.json do CI sem nenhum passo válido"}
    head = dados.get("head") if isinstance(dados.get("head"), str) and HEAD_RE.fullmatch(dados["head"]) else None
    idade = round((_now() - gerado).total_seconds() / 3600, 2)
    state, velho = _envelhece("falha" if dados["falha"] > 0 else "ok", idade)
    return {**base, "state": state, "gerado_em": gerado.isoformat(timespec="seconds"),
            "idade_horas": idade, "head": head, "ok": dados["ok"],
            "falha": dados["falha"], "linha_final": _texto_curto(dados.get("linha_final"), 200), "passos": passos, **velho}


# --- Provedores (D7): catálogo estático; não constrói o Council nem abre state.sqlite3 ---
def _provedores_snapshot() -> dict:
    observed_at, fresh_until = _reading_window()
    itens = [{"id": p["id"], "nome": p["name"], "tipo": p["kind"], "acesso": p["access_mode"]}
             for p in relay_catalog.PROVIDERS]
    return {"schema_version": 1, "state": "ok", "source": "redesign/painel_operacional/relay_catalog.py (PROVIDERS)",
            "observed_at": observed_at, "fresh_until": fresh_until, "total": len(itens), "items": itens}


# Rotas de leitura curta (GET): nome do cache, produtor. Lambdas: a função é resolvida na chamada (testes trocam).
LEITURAS_CURTAS = {
    "/api/provedores": ("provedores", lambda: _leitura_segura(_provedores_snapshot)),
    "/api/equipe": ("equipe", lambda: _leitura_segura(_equipe_snapshot)),
    "/api/backup": ("backup", lambda: _leitura_segura(_backup_snapshot)),
    "/api/egress": ("egress", lambda: _leitura_segura(_egress_snapshot)),
    "/api/perimetro": ("perimetro", lambda: _leitura_segura(_perimetro_snapshot)),
    "/api/ci": ("ci", lambda: _leitura_segura(_ci_snapshot)),
}

# Fila própria de pedidos de foco/abertura de abas (lida pela extensão; separada da fila de envios).
FOCOS_PENDENTES = []
FOCOS_MAX = 20
_FOCO_LOCK = threading.Lock()
_OBSIDIAN_ULTIMA = [0.0]
OBSIDIAN_INTERVALO_S = 5.0
# Rotas lidas pela extensão: não passam pela checagem de origem do navegador (usam o cabeçalho do executor).
ROTAS_DA_EXTENSAO = {"/api/relay-council/focos", "/api/relay-council/tasks"}
CONSELHEIROS = ("deepseek", "gemini", "zai", "chatgpt", "claude", "grok", "qwen", "mistral", "kimi")
CONSELHO_REPETE_S = 20.0  # não reenfileira o mesmo conselheiro enquanto o inventário da extensão alcança
_CONSELHO_ULTIMA: dict = {}
ABRIR_OBSIDIAN = ("flatpak", "run", "md.obsidian.Obsidian")


class _RespostaUpload(Exception):
    """Resposta de erro do upload, levantada dentro do try para que a limpeza rode antes de responder."""

    def __init__(self, codigo: int, corpo: bytes):
        super().__init__(codigo)
        self.codigo, self.corpo = codigo, corpo


class Handler(BaseHTTPRequestHandler):
    def _abrir_programa(self) -> None:
        if (self.headers.get("Origin") != ALLOWED_ORIGIN
                or self.headers.get("Sec-Fetch-Site") not in {"same-origin", "none"}
                or self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json"):
            return self._send(403, "text/plain; charset=utf-8", b"same-origin JSON required")
        tamanho = self.headers.get("Content-Length", "")
        if not tamanho.isdecimal() or int(tamanho) > 512:
            return self._send(400, "text/plain; charset=utf-8", b"invalid body size")
        try:
            pedido = json.loads(self.rfile.read(int(tamanho)) or b"{}")
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            return self._send(400, "text/plain; charset=utf-8", b"invalid JSON")
        alvo = pedido.get("alvo") if isinstance(pedido, dict) else None
        if alvo == "obsidian":
            # Obsidian é um programa próprio: sobe como processo separado (no máximo um pedido a cada poucos segundos).
            agora = time.monotonic()
            with _FOCO_LOCK:
                if agora - _OBSIDIAN_ULTIMA[0] < OBSIDIAN_INTERVALO_S:
                    return self._send(429, "text/plain; charset=utf-8", b"aguarde alguns segundos")
                _OBSIDIAN_ULTIMA[0] = agora
            subprocess.Popen(list(ABRIR_OBSIDIAN), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
        elif alvo == "conselho":
            # Entrar na aba Conselho confere os nove conselheiros: só pede abertura dos que a extensão não vê.
            abertos = set(_council_state().available_providers())
            agora = time.monotonic()
            with _FOCO_LOCK:
                na_fila = {p["site"] for p in FOCOS_PENDENTES}
                faltando = [c for c in CONSELHEIROS if c not in abertos]
                for site in faltando:
                    if site in na_fila or agora - _CONSELHO_ULTIMA.get(site, -CONSELHO_REPETE_S) < CONSELHO_REPETE_S:
                        continue
                    _CONSELHO_ULTIMA[site] = agora
                    FOCOS_PENDENTES.append({"id": uuid.uuid4().hex, "site": site, "url": ABRIR_PROVEDORES[site], "janela": False})
                del FOCOS_PENDENTES[:-FOCOS_MAX]
            return self._send(202, "application/json; charset=utf-8",
                              json.dumps({"ok": True, "alvo": alvo, "abertos": len(abertos), "faltando": faltando}).encode("utf-8"))
        elif alvo in ABRIR_PROVEDORES:
            # Foco pela extensão, no mesmo canal do Conselho: o pedido fica numa fila própria (não entra na fila de envios).
            with _FOCO_LOCK:
                FOCOS_PENDENTES.append({"id": uuid.uuid4().hex, "site": alvo, "url": ABRIR_PROVEDORES[alvo], "janela": True})
                del FOCOS_PENDENTES[:-FOCOS_MAX]
        else:
            return self._send(400, "text/plain; charset=utf-8", b"destino fora da lista")
        return self._send(202, "application/json; charset=utf-8", json.dumps({"ok": True, "alvo": alvo}).encode("utf-8"))

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
        frame_ancestors = "'self'" if self.path.startswith("/operator_console") else "'none'"
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; frame-src 'self'; "
            "connect-src 'self'; img-src 'self'; base-uri 'none'; "
            f"frame-ancestors {frame_ancestors}",
        )
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.headers.get("Host") != f"{BIND}:{PORT}":
            return self._send(421, "text/plain; charset=utf-8", b"invalid host")
        if (self.path.startswith("/api/") and self.path.split("?", 1)[0] not in ROTAS_DA_EXTENSAO
                and not _same_origin_request(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin"))):
            return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
        # Painel unificado: as telas antigas redirecionam para a seção certa do /prototipo (tabela _REDIRECTS).
        destino = _REDIRECTS.get(self.path)
        if destino is not None:
            return self._send(302, "text/plain; charset=utf-8", b"", (("Location", destino),))
        if self.path.startswith("/api/grafo"):
            return self._grafo()
        if self.path == "/api/seth/ouvir":
            return self._send(200, "application/json; charset=utf-8", json.dumps(seth_voz.estado(), ensure_ascii=False).encode("utf-8"))
        if self.path == "/api/seth/modelos":
            return self._send(200, "application/json; charset=utf-8", json.dumps(chat_stream.lista_modelos(), ensure_ascii=False).encode("utf-8"))
        if self.path == "/api/seth/conversas":
            return self._send(200, "application/json; charset=utf-8", json.dumps(_conversas_listar(), ensure_ascii=False).encode("utf-8"))
        if self.path == "/api/seth/lixeira":
            return self._send(200, "application/json; charset=utf-8", json.dumps(_lixeira_listar(), ensure_ascii=False).encode("utf-8"))
        if self.path.startswith("/api/seth/conversas/busca?"):
            return self._seth_busca()
        if self.path.startswith("/api/seth/conversa/exportar?"):
            return self._seth_exportar()
        if self.path.startswith("/api/seth/conversa?"):
            dados = _conversa_ler((parse_qs(urlparse(self.path).query).get("id") or [""])[0])
            if dados is None:
                return self._send(404, "text/plain; charset=utf-8", b"conversa indisponivel")
            return self._send(200, "application/json; charset=utf-8", json.dumps(dados, ensure_ascii=False).encode("utf-8"))
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
        if self.path.split("?", 1)[0] == "/api/historia":
            return self._historia_listar()
        if self.path.split("?", 1)[0] == "/api/modelos":
            return self._modelos_listar()
        if self.path.startswith("/api/historia/texto?"):
            return self._historia_texto()
        if self.path == "/api/frentes":
            # Somente leitura: caminho fixo a partir da raiz do repositório; o cliente não escolhe arquivo.
            try:
                dados_frentes = json.loads((ROOT / "config/frentes.json").read_bytes())
            except (OSError, ValueError):
                return self._send(500, "text/plain; charset=utf-8", b"frentes indisponiveis")
            body = json.dumps(dados_frentes, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/lacunas":
            body = json.dumps(_cached_curto("lacunas", _lacunas_snapshot), ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/capacidades":
            body = json.dumps(_cached_curto("capacidades", _capacidades_snapshot), ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/medicoes/estado":
            observed_at, fresh_until = _reading_window()
            body = json.dumps({**medicoes_painel.estado(), "observed_at": observed_at, "fresh_until": fresh_until}, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/nova-versao/estado":
            observed_at, fresh_until = _reading_window()
            body = json.dumps({**nova_versao_painel.estado(), "observed_at": observed_at, "fresh_until": fresh_until}, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/sdd/estado":
            observed_at, fresh_until = _reading_window()
            body = json.dumps({**sdd_painel.estado(ROOT), "observed_at": observed_at, "fresh_until": fresh_until}, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/qualidade-llm":
            observed_at, fresh_until = _reading_window()
            dados = {**qualidade_llm.snapshot(ROOT), "observed_at": observed_at, "fresh_until": fresh_until}
            body = json.dumps(dados, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/relay-council/focos":
            if self.headers.get("X-Relay-Client") != RELAY_CLIENT_ID:
                return self._send(403, "application/json; charset=utf-8", b'{"error":"executor not authorized"}')
            with _FOCO_LOCK:
                pedidos = list(FOCOS_PENDENTES)
                FOCOS_PENDENTES.clear()
            return self._send(200, "application/json; charset=utf-8", json.dumps(pedidos).encode("utf-8"))
        if self.path.split("?", 1)[0] == "/api/conselho/memoria":
            return self._conselho_memoria()
        if self.path == "/api/importantes":
            return self._importantes_listar()
        if self.path == "/api/eventos":
            return self._send(200, "text/plain; charset=utf-8", _eventos_recentes())
        if self.path in LEITURAS_CURTAS:
            nome_cache, produzir = LEITURAS_CURTAS[self.path]
            body = json.dumps(_cached_curto(nome_cache, produzir), ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/relay-council/catalog":
            _cache, catalog, _contract, _sanitizer = _relay_modules()
            council = _council_state()
            body = json.dumps(
                {"schema_version": 1, "providers": catalog.snapshot(council.available_providers())},
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
            raw_providers = self.headers.get("X-Relay-Providers", "")
            providers = raw_providers.split(",") if raw_providers else []
            try:
                _council_state().set_active_providers(providers)
            except ValueError:
                return self._send(400, "application/json; charset=utf-8", b'{"error":"invalid tab inventory"}')
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
        if self.path == "/api/abrir":
            return self._abrir_programa()
        if self.path == "/api/historia/ouvir":
            return self._historia_ouvir()
        if self.path == "/api/modelos/decisao":
            return self._modelos_decisao()
        if self.path == "/api/seth/ouvir":
            return self._seth_ouvir()
        if self.path == "/api/seth/ouvir/parar":
            return self._seth_ouvir_parar()
        if self.path == "/api/seth/ditado":
            return self._seth_ditado()
        if self.path in {"/api/relay-council/actions", "/api/relay-council/groups",
                         "/api/relay-council/decision"}:
            return self._relay_council_human_post()
        if self.path == "/api/relay-council/result":
            return self._relay_council_result()
        if self.path == "/api/relay-council/evaluations":
            return self._relay_evaluation()
        if self.path == "/api/seth/chat":
            return self._seth_chat()
        if self.path == "/api/seth/chat/stream":
            return self._seth_chat_stream()
        if self.path in ("/api/seth/conversa", "/api/seth/conversa/apagar"):
            return self._seth_conversa(self.path.endswith("/apagar"))
        if self.path in ("/api/seth/conversa/organizar", "/api/seth/pastas", "/api/seth/conversa/importar"):
            return self._seth_organizacao(self.path)
        if self.path in ("/api/seth/lixeira/restaurar", "/api/seth/lixeira/purgar"):
            return self._seth_lixeira(self.path.endswith("/restaurar"))
        if self.path in IMPORTANTES_ROTAS:
            return self._importantes_escrita(self.path)
        if self.path == "/api/nova-versao/upload":
            return self._nova_versao_upload()
        if self.path not in {"/api/wiki/search", "/api/proposals/verify", "/api/sdd/executar", "/api/medicoes/executar", "/api/nova-versao/executar"} or (self.path == "/api/wiki/search" and not WIKI_LIBERADA):
            return self._send(405, "text/plain; charset=utf-8", b"read only", (("Allow", "GET, POST"),))
        if self.headers.get("Origin") != ALLOWED_ORIGIN or not _same_origin_request(
            self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")
        ):
            return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            return self._send(415, "text/plain; charset=utf-8", b"JSON required")
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > 65_536:
            return self._send(413, "text/plain; charset=utf-8", b"request too large")
        try:
            payload = json.loads(self.rfile.read(int(raw_length)))
        except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
            return self._send(400, "text/plain; charset=utf-8", b"invalid JSON")
        if not isinstance(payload, dict):
            return self._send(400, "text/plain; charset=utf-8", b"invalid search")
        if self.path == "/api/medicoes/executar":
            try:
                resultado = medicoes_painel.executar(payload.get("acao"), payload.get("modelo"), tarefa=payload.get("tarefa"), raciocinio=payload.get("raciocinio"))
            except ValueError:
                return self._send(400, "text/plain; charset=utf-8", b"invalid measurement")
            except RuntimeError as exc:  # D8 (17/11/2026): só motivo fixo vai no corpo
                return self._send(429, "text/plain; charset=utf-8", f"measurement busy: {medicoes_painel.motivo_ocupado(exc)}".encode("utf-8"))
            body = json.dumps({"schema_version": 1, **resultado}, ensure_ascii=False).encode("utf-8")
            return self._send(202, "application/json; charset=utf-8", body)
        if self.path == "/api/nova-versao/executar":
            try:
                resultado = nova_versao_painel.executar(payload.get("acao"), payload)
            except ValueError:
                return self._send(400, "text/plain; charset=utf-8", b"invalid nova-versao action")
            except RuntimeError as exc:  # D8 (17/11/2026): só motivo fixo vai no corpo
                return self._send(429, "text/plain; charset=utf-8", f"nova-versao busy: {medicoes_painel.motivo_ocupado(exc)}".encode("utf-8"))
            except FileNotFoundError:
                return self._send(409, "text/plain; charset=utf-8", b"nova-versao index missing")
            except PermissionError:
                return self._send(403, "text/plain; charset=utf-8", b"nova-versao action not allowed yet")
            body = json.dumps({"schema_version": 1, **resultado}, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
        if self.path == "/api/sdd/executar":
            if not _SDD_LOCK.acquire(blocking=False):
                return self._send(429, "text/plain; charset=utf-8", b"sdd busy")
            try:
                try:
                    resultado = sdd_painel.executar(payload.get("acao"), payload.get("componente"), ROOT)
                except ValueError:
                    return self._send(400, "text/plain; charset=utf-8", b"invalid sdd action")
            finally:
                _SDD_LOCK.release()
            body = json.dumps({"schema_version": 1, **resultado}, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body)
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

    def _relay_council_result(self) -> None:
        if self.headers.get("X-Relay-Client") != RELAY_CLIENT_ID:
            return self._send(403, "application/json; charset=utf-8", b'{"error":"executor not authorized"}')
        payload = self._relay_council_body(65_536)
        if payload is None:
            return
        task_id, lease, site = payload.get("task_id"), payload.get("lease"), payload.get("site")
        result = {"ok": payload.get("ok"), "text": payload.get("text", ""),
                  "error": payload.get("error", "")}
        if not all(isinstance(value, str) for value in (task_id, lease, site)):
            return self._send(400, "application/json; charset=utf-8", b'{"error":"invalid task"}')
        try:
            recorded = _council_state().finish_browser(task_id, lease, site, result)
        except _COUNCIL_CONFLICT:
            return self._send(409, "application/json; charset=utf-8", b'{"error":"task lease mismatch"}')
        except (ValueError, TypeError, KeyError):
            return self._send(400, "application/json; charset=utf-8", b'{"error":"invalid task"}')
        return self._send(200, "application/json; charset=utf-8",
                          json.dumps(recorded).encode("utf-8"))

    def _nova_versao_upload(self) -> None:
        """Upload de fonte externa (lote 5, C4): corpo binário, em blocos, para o temporário da pasta de entrada.
        Mesmas checagens de origem das outras rotas; sem JSON; um por vez; prazo total e timeout por leitura.
        A limpeza do temporário acontece ANTES da resposta: o cliente nunca vê a pasta com resto de upload."""
        if self.headers.get("Origin") != ALLOWED_ORIGIN or not _same_origin_request(
            self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")
        ):
            return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/octet-stream":
            return self._send(415, "text/plain; charset=utf-8", b"octet-stream required")
        if self.headers.get("Transfer-Encoding"):
            return self._send(411, "text/plain; charset=utf-8", b"content-length required")
        import aquisicao  # noqa: E402  (alexandria já está no sys.path via nova_versao_painel)
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > aquisicao.MAX_BYTES:
            return self._send(413, "text/plain; charset=utf-8", b"request too large")
        extensao = (self.headers.get("X-Extensao") or "").strip().lower()
        if extensao not in aquisicao.EXTENSOES:
            return self._send(422, "text/plain; charset=utf-8", b"extension not accepted")
        nome = unquote(self.headers.get("X-Nome") or "upload")[:200]   # o navegador envia encodeURIComponent (cabeçalho é latin-1)
        if not _UPLOAD_LOCK.acquire(blocking=False):
            return self._send(429, "text/plain; charset=utf-8", b"upload busy")
        tmp_path = None
        resposta = None
        try:
            fd, tmp_path = tempfile.mkstemp(dir=aquisicao.entrada(), prefix=".up-")
            restante = int(raw_length)
            prazo = time.monotonic() + 60
            self.connection.settimeout(10)
            with os.fdopen(fd, "wb") as f:
                while restante > 0:
                    if time.monotonic() > prazo:
                        raise _RespostaUpload(408, b"upload timeout")
                    bloco = self.rfile.read(min(65536, restante))
                    if not bloco:
                        break
                    f.write(bloco)
                    restante -= len(bloco)
            if restante:
                raise _RespostaUpload(400, b"incomplete body")
            r = aquisicao.guardar_arquivo(Path(tmp_path), extensao, nome, origem_tipo="upload")
            tmp_path = None
            c = r["cadastro"]
            body = json.dumps({"schema_version": 1, "sha256": c["sha256"], "duplicado": r["duplicado"],
                               "editorial_status": c["editorial_status"], "extensao": c["extensao"],
                               "tamanho": c["tamanho"]}, ensure_ascii=False).encode("utf-8")
            resposta = (201 if not r["duplicado"] else 200, body)
        except _RespostaUpload as r:
            resposta = (r.codigo, r.corpo)
        except socket.timeout:
            resposta = (408, b"upload timeout")
        except ValueError as e:
            resposta = (422, str(e).encode("utf-8")[:200])
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            _UPLOAD_LOCK.release()
        codigo, corpo = resposta
        ctype = "application/json; charset=utf-8" if codigo in (200, 201) else "text/plain; charset=utf-8"
        return self._send(codigo, ctype, corpo)

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


    def _seth_chat_stream(self) -> None:
        """Chat da Seth em streaming (SSE) pelo gateway local. Seth pública: só texto. seth-livre (20/11/2026): ferramentas de
        leitura (ferramentas_seth) e anotar no cache do Conselho, em laço de até 5 rodadas. Não grava conteúdo em log."""
        if self.headers.get("Origin") != ALLOWED_ORIGIN or not _same_origin_request(
            self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")
        ):
            return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            return self._send(415, "text/plain; charset=utf-8", b"JSON required")
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > CHAT_STREAM_LIMITE_BYTES:
            return self._send(413, "text/plain; charset=utf-8", f"pedido acima de {CHAT_STREAM_LIMITE_BYTES} bytes".encode("utf-8"))
        try:
            corpo = json.loads(self.rfile.read(int(raw_length)))
        except (ValueError, RecursionError):
            return self._send(400, "text/plain; charset=utf-8", "pedido em JSON inválido".encode("utf-8"))
        try:
            pedido = chat_stream.montar_pedido(corpo.get("mensagens") if isinstance(corpo, dict) else None,
                                               corpo.get("modelo") if isinstance(corpo, dict) else None,
                                               corpo.get("instrucoes") if isinstance(corpo, dict) else None,
                                               corpo.get("anexos") if isinstance(corpo, dict) else None)
        except ValueError as erro:
            # A mensagem de montar_pedido traz só posição e regra (ex.: "mensagem 3 acima de 4000 caracteres"), nunca o texto.
            return self._send(400, "text/plain; charset=utf-8", str(erro).encode("utf-8"))
        if not _SEM_CONVERSA_EM_CURSO.acquire(blocking=False):
            return self._send(429, "text/plain; charset=utf-8", b"busy")
        resposta, fim = None, threading.Event()
        sock_gateway = _SocketAtual()
        proximas = []  # respostas abertas pelo laço de ferramentas, fechadas ao fim

        modelos_rodadas = []  # (23/11/2026) X-Modelo-Real de cada rodada de ferramenta, na ordem

        def abrir_proxima(pedido_seguinte):
            nova, sock = _abrir_gateway(pedido_seguinte)
            proximas.append(nova)
            modelos_rodadas.append(chat_stream.modelo_real_valido(nova.headers.get("X-Modelo-Real")) or "")
            sock_gateway.sock = sock
            return _linhas_do_gateway(nova)
        try:
            if pedido["model"] == ferramentas_seth.MODELO_COM_FERRAMENTAS:
                ferramentas = ferramentas_seth.esquemas()  # nunca na Seth pública
                if ferramentas:
                    pedido["tools"] = ferramentas
            try:
                resposta, sock_gateway.sock = _abrir_gateway(pedido)
            except (OSError, http.client.HTTPException):
                return self._stream_sse([{"tipo": "erro", "motivo": "gateway indisponível"}])
            # Vigia: se o navegador sair no meio do stream, a conexão com o gateway cai já, sem esperar o próximo pedaço.
            threading.Thread(target=self._vigiar_cliente, args=(sock_gateway, fim), daemon=True).start()
            with resposta:
                # Modelo real (X-Modelo-Real, fato da Máquina) segue no cabeçalho da resposta; sem ele, a UI mostra o escolhido.
                real = chat_stream.modelo_real_valido(resposta.headers.get("X-Modelo-Real"))
                modelos_rodadas.append(real or "")
                if "tools" in pedido:
                    eventos = ferramentas_seth.laco(abrir_proxima, _linhas_do_gateway(resposta), pedido,
                                                    modelos=modelos_rodadas)
                else:
                    eventos = chat_stream.eventos_do_stream(_linhas_do_gateway(resposta))
                self._stream_sse(eventos, (("X-Modelo-Real", real),) if real else ())
        finally:
            fim.set()
            if resposta is not None:
                resposta.close()  # fecha o socket do gateway, mesmo se o cliente saiu no meio
            for extra in proximas:
                extra.close()
            _SEM_CONVERSA_EM_CURSO.release()

    def _vigiar_cliente(self, sock_gateway, fim: threading.Event) -> None:
        """Thread do stream: espera o navegador (leitura do socket do cliente). Se ele fechar a conexão enquanto
        o gateway ainda responde, derruba a conexão com o gateway. Para quando o stream termina (fim) ou o cliente sai."""
        cliente = self.connection
        saiu = False
        while not fim.is_set():
            try:
                pronto, _, _ = select.select([cliente], [], [], 0.5)
                if pronto and cliente.recv(1024) == b"":
                    saiu = True
                    break
            except OSError:
                saiu = True
                break
        if saiu:
            _derrubar_gateway(sock_gateway)

    def _stream_sse(self, eventos, cabecalhos_extra=()) -> None:
        """Repassa eventos como SSE. Sem Content-Length: a conexão fecha ao fim (HTTP/1.0).
        Se o navegador sair (BrokenPipeError, ConnectionResetError ou outro OSError na escrita), para de escrever
        e fecha o gerador, que solta a leitura do gateway."""
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            for nome, valor in cabecalhos_extra:
                self.send_header(nome, valor)
            self.end_headers()
            for evento in eventos:
                self.wfile.write(chat_stream.codificar_sse(evento))
                self.wfile.flush()
        except OSError:
            pass  # o navegador saiu no meio do stream (BrokenPipeError e ConnectionResetError caem aqui)
        finally:
            fechar = getattr(eventos, "close", None)
            if fechar is not None:
                fechar()

    def _responder_escrita(self, rota: str, identificador, status: int, corpo: bytes,
                           tipo: str = "text/plain; charset=utf-8") -> None:
        """Toda resposta de escrita de conversa passa aqui: grava a linha do registro (sem conteúdo) e responde."""
        _registro_escrever(rota, identificador, status)
        return self._send(status, tipo, corpo)

    def _seth_conversa(self, apagar: bool) -> None:
        """Histórico de conversas da Seth, em ~/.cache (fora do canon). Só valida e grava o que o próprio painel envia.
        Apagar move a conversa para a lixeira (09/11/2026); nada é apagado de vez aqui."""
        rota = self.path
        if not _escrita_permitida(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")):
            return self._responder_escrita(rota, None, 403, b"cross-origin request denied")
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > CONVERSA_LIMITE_BYTES:
            return self._responder_escrita(rota, None, 413, f"conversa acima de {CONVERSA_LIMITE_BYTES} bytes".encode("utf-8"))
        try:
            dados = json.loads(self.rfile.read(int(raw_length)).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._responder_escrita(rota, None, 400, "conversa com JSON inválido".encode("utf-8"))
        pedido_id = dados.get("id") if isinstance(dados, dict) else None
        if apagar:
            try:
                nome = _conversa_apagar(pedido_id if isinstance(pedido_id, str) else "")
            except ErroConversa as erro:
                return self._responder_escrita(rota, pedido_id, erro.status, erro.motivo.encode("utf-8"))
            if nome is None:
                return self._responder_escrita(rota, pedido_id, 404, json.dumps({"apagada": False}).encode("utf-8"),
                                               "application/json; charset=utf-8")
            corpo = {"apagada": True, "lixeira": nome}
            return self._responder_escrita(rota, pedido_id, 200, json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
                                           "application/json; charset=utf-8")
        salvo = _conversa_gravar(dados)
        if salvo is None:
            return self._responder_escrita(rota, pedido_id, 400, armazem.motivo_conversa_recusada(dados).encode("utf-8"))
        return self._responder_escrita(rota, salvo["id"], 200, json.dumps(salvo, ensure_ascii=False).encode("utf-8"),
                                       "application/json; charset=utf-8")

    def _seth_lixeira(self, restaurar: bool) -> None:
        """Lixeira de conversas (09/11/2026): restaurar devolve a conversa; purgar apaga de vez (só manual, com confirmação na tela)."""
        rota = self.path
        if not _escrita_permitida(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")):
            return self._responder_escrita(rota, None, 403, b"cross-origin request denied")
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > SETH_ORGANIZACAO_LIMITE_BYTES:
            return self._responder_escrita(rota, None, 413, f"pedido acima de {SETH_ORGANIZACAO_LIMITE_BYTES} bytes".encode("utf-8"))
        try:
            dados = json.loads(self.rfile.read(int(raw_length)).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._responder_escrita(rota, None, 400, "pedido com JSON inválido".encode("utf-8"))
        nome = dados.get("nome") if isinstance(dados, dict) else None
        try:
            resultado = _lixeira_restaurar(nome) if restaurar else _lixeira_purgar(nome)
        except ErroConversa as erro:
            return self._responder_escrita(rota, nome, erro.status, erro.motivo.encode("utf-8"))
        return self._responder_escrita(rota, nome, 200, json.dumps(resultado, ensure_ascii=False).encode("utf-8"),
                                       "application/json; charset=utf-8")

    def _seth_busca(self) -> None:
        """Busca por texto nas conversas salvas (títulos e mensagens), só leitura e local."""
        termo = (parse_qs(urlparse(self.path).query).get("q") or [""])[0]
        try:
            dados = _conversas_buscar(termo)
        except ErroConversa as erro:
            return self._send(erro.status, "text/plain; charset=utf-8", erro.motivo.encode("utf-8"))
        return self._send(200, "application/json; charset=utf-8", json.dumps(dados, ensure_ascii=False).encode("utf-8"))

    def _seth_exportar(self) -> None:
        """Download de uma conversa salva, em JSON ou Markdown. O nome do arquivo leva só o id."""
        query = parse_qs(urlparse(self.path).query)
        try:
            corpo, nome, tipo = _conversa_exportar((query.get("id") or [""])[0], (query.get("formato") or [""])[0])
        except ErroConversa as erro:
            return self._send(erro.status, "text/plain; charset=utf-8", erro.motivo.encode("utf-8"))
        return self._send(200, tipo, corpo, (("Content-Disposition", f'attachment; filename="{nome}"'),))

    def _seth_organizacao(self, rota: str) -> None:
        """Fixar, arquivar, marcadores, pastas e importação das conversas (lote 3). Só valida e grava o que o painel envia."""
        if not _escrita_permitida(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")):
            return self._responder_escrita(rota, None, 403, b"cross-origin request denied")
        importando = rota.endswith("/importar")
        limite = IMPORTACAO_LIMITE_BYTES if importando else SETH_ORGANIZACAO_LIMITE_BYTES
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > limite:
            aviso = f"arquivo acima de {limite} bytes" if importando else f"pedido acima de {limite} bytes"
            return self._responder_escrita(rota, None, 413, aviso.encode("utf-8"))
        try:
            dados = json.loads(self.rfile.read(int(raw_length)).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._responder_escrita(rota, None, 400, "pedido com JSON inválido".encode("utf-8"))
        identificador = dados.get("id") if isinstance(dados, dict) and not importando else None
        try:
            if importando:
                resultado = _conversa_importar(dados)
                identificador = resultado["id"]
            elif not isinstance(dados, dict):
                raise ErroConversa(400, "pedido precisa ser um objeto JSON")
            elif rota == "/api/seth/pastas":
                resultado = _pasta_mudar(dados.get("acao"), dados.get("id"), dados.get("nome"))
                identificador = resultado.get("id", identificador)
            else:
                resultado = _conversa_organizar(dados.get("id"), {k: v for k, v in dados.items() if k != "id"})
        except ErroConversa as erro:
            return self._responder_escrita(rota, identificador, erro.status, erro.motivo.encode("utf-8"))
        return self._responder_escrita(rota, identificador, 200, json.dumps(resultado, ensure_ascii=False).encode("utf-8"),
                                       "application/json; charset=utf-8")

    def _seth_chat(self) -> None:
        """Conversa com a Seth pelo gateway local, só texto, sem ferramentas e sem escrita. Modelo: lista fixa (chat_stream).
        Mesmo teto de pedido do stream (CHAT_STREAM_LIMITE_BYTES): a janela que a UI manda cabe nos dois caminhos."""
        if not _same_origin_request(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")):
            return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > CHAT_STREAM_LIMITE_BYTES:
            return self._send(413, "text/plain; charset=utf-8", f"pedido acima de {CHAT_STREAM_LIMITE_BYTES} bytes".encode("utf-8"))
        try:
            corpo = json.loads(self.rfile.read(int(raw_length)))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._send(400, "text/plain; charset=utf-8", "pedido em JSON inválido".encode("utf-8"))
        mensagens = corpo.get("messages") if isinstance(corpo, dict) else None
        if not isinstance(mensagens, list) or not mensagens or len(mensagens) > chat_stream.MAX_MENSAGENS:
            return self._send(400, "text/plain; charset=utf-8", f"a janela precisa ter de 1 a {chat_stream.MAX_MENSAGENS} mensagens".encode("utf-8"))
        limpas = []
        for m in mensagens:
            if not isinstance(m, dict) or m.get("role") not in ("user", "assistant"):
                return self._send(400, "text/plain; charset=utf-8", "mensagem com papel inválido".encode("utf-8"))
            conteudo = m.get("content")
            if not isinstance(conteudo, str) or not conteudo.strip() or len(conteudo) > chat_stream.MAX_CARACTERES_MENSAGEM:
                return self._send(400, "text/plain; charset=utf-8",
                                  f"mensagem vazia ou acima de {chat_stream.MAX_CARACTERES_MENSAGEM} caracteres".encode("utf-8"))
            limpas.append({"role": m["role"], "content": conteudo})
        try:
            modelo = chat_stream.modelo_valido(corpo.get("modelo") if isinstance(corpo, dict) else None)
        except ValueError:
            return self._send(400, "text/plain; charset=utf-8", b"modelo fora da lista")
        try:
            # Instruções da conversa (system, filtradas) e anexos (no fim da última mensagem do usuário), pelo mesmo montador do stream.
            limpas = chat_stream.montar_mensagens(limpas, corpo.get("instrucoes") if isinstance(corpo, dict) else None,
                                                  corpo.get("anexos") if isinstance(corpo, dict) else None)
        except ValueError as erro:
            return self._send(400, "text/plain; charset=utf-8", str(erro).encode("utf-8"))
        if not _SEM_CONVERSA_EM_CURSO.acquire(blocking=False):
            return self._send(429, "text/plain; charset=utf-8", b"busy")
        try:
            pedido = {"model": modelo, "stream": False, "messages": limpas, "max_tokens": 1024}
            req = urllib.request.Request(GATEWAY_CHAT_URL, data=json.dumps(pedido).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=120) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
                real = chat_stream.modelo_real_valido(resposta.headers.get("X-Modelo-Real"))
            texto = dados["choices"][0]["message"].get("content") or ""
            saida = {"schema_version": 1, "content": texto, "model": dados.get("model")}
            uso = chat_stream.uso_valido(dados.get("usage"))  # só quando o gateway devolve a contagem; sem ela, o campo não existe
            if uso is not None:
                saida["uso"] = uso
            body = json.dumps(saida, ensure_ascii=False).encode("utf-8")
            return self._send(200, "application/json; charset=utf-8", body, (("X-Modelo-Real", real),) if real else ())
        except (OSError, KeyError, IndexError, ValueError):
            return self._send(502, "text/plain; charset=utf-8", b"gateway indisponivel")
        finally:
            _SEM_CONVERSA_EM_CURSO.release()


    def _conselho_memoria(self) -> None:
        """Memória compartilhada do Conselho, só leitura: as últimas n entradas, mais recentes primeiro.
        A checagem de origem já rodou em do_GET. Não aceita caminho e não escreve no cache.
        n é inteiro de 1 a 200: acima do limite corta; vazio, zero ou não numérico recusa com 400."""
        bruto = (parse_qs(urlparse(self.path).query).get("n") or [str(MEMORIA_CONSELHO_PADRAO)])[0]
        if not re.fullmatch(r"[0-9]{1,4}", bruto) or int(bruto) < 1:
            return self._send(400, "text/plain; charset=utf-8", b"n invalido")
        n = min(int(bruto), MEMORIA_CONSELHO_MAX)
        observed_at, fresh_until = _reading_window()
        try:
            cache = _memoria_conselho_modulo()
            entradas = [_memoria_entrada(cache, reg) for reg in reversed(cache.ler(n))]
        except (OSError, ValueError, ImportError):
            return self._send(500, "text/plain; charset=utf-8", b"memoria indisponivel")
        dados = {"estado": "ok" if entradas else "vazio", "n": n, "entradas": entradas,
                 "observed_at": observed_at, "fresh_until": fresh_until}
        return self._send(200, "application/json; charset=utf-8", json.dumps(dados, ensure_ascii=False).encode("utf-8"))

    def _importantes_listar(self) -> None:
        """Importantes (11/11/2026): leitura da lista local. A checagem de origem já rodou em do_GET."""
        corpo = json.dumps(importantes.listar(), ensure_ascii=False).encode("utf-8")
        return self._send(200, "application/json; charset=utf-8", corpo)

    def _responder_importante(self, rota: str, identificador, status: int, corpo: bytes,
                              tipo: str = "text/plain; charset=utf-8") -> None:
        """Toda resposta de escrita de importantes passa aqui: grava a linha do registro (sem conteúdo) e responde."""
        importantes.registro_escrever(rota, identificador, status)
        return self._send(status, tipo, corpo)

    def _importantes_escrita(self, rota: str) -> None:
        """Importantes (11/11/2026): criar, marcar, editar e trazer do cache do Conselho. Escrita exige origem do
        painel (_escrita_permitida, como as conversas). Cada pedido, inclusive o recusado, gera uma linha no registro."""
        if not _escrita_permitida(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")):
            return self._responder_importante(rota, None, 403, b"cross-origin request denied")
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdecimal() or int(raw_length) > IMPORTANTES_LIMITE_BYTES:
            return self._responder_importante(rota, None, 413, f"pedido acima de {IMPORTANTES_LIMITE_BYTES} bytes".encode("utf-8"))
        try:
            dados = json.loads(self.rfile.read(int(raw_length)).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._responder_importante(rota, None, 400, "pedido com JSON inválido".encode("utf-8"))
        identificador = dados.get("id") if isinstance(dados, dict) else None
        try:
            if rota == "/api/importantes":
                resultado = importantes.criar(dados)
            elif rota == "/api/importantes/estado":
                resultado = importantes.mudar_estado(dados)
            elif rota == "/api/importantes/editar":
                resultado = importantes.editar(dados)
            else:
                try:
                    cache = _memoria_conselho_modulo()
                except ImportError as erro:
                    raise importantes.ErroImportantes(500, "cache do Conselho indisponível; nada foi trazido") from erro
                resultado = importantes.trazer_do_conselho(cache)
                identificador = None
        except importantes.ErroImportantes as erro:
            return self._responder_importante(rota, identificador, erro.status, erro.motivo.encode("utf-8"))
        except OSError:
            return self._responder_importante(rota, identificador, 500, "gravacao indisponivel; nada foi alterado".encode("utf-8"))
        if rota != "/api/importantes/trazer":
            identificador = resultado["id"]
        return self._responder_importante(rota, identificador, 200, json.dumps(resultado, ensure_ascii=False).encode("utf-8"),
                                          "application/json; charset=utf-8")

    def _modelos_listar(self) -> None:
        """Catálogo de modelos (18/11/2026): só leitura do JSON do catálogo e do arquivo de decisões."""
        try:
            dados = modelos_painel.listar()
        except modelos_painel.ErroModelos as erro:
            return self._send(erro.status, "text/plain; charset=utf-8", erro.motivo.encode("utf-8"))
        return self._send(200, "application/json; charset=utf-8", json.dumps(dados, ensure_ascii=False).encode("utf-8"))

    def _modelos_decisao(self) -> None:
        """Liberar para rota ou voltar ao standby: só registra a decisão (append-only). Escrita, então só da origem do painel."""
        if not _escrita_permitida(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")):
            return self._send(403, "text/plain; charset=utf-8", b"cross-origin request denied")
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            return self._send(415, "text/plain; charset=utf-8", b"JSON required")
        tamanho = self.headers.get("Content-Length", "")
        if not tamanho.isdecimal() or int(tamanho) > 2048:
            return self._send(413, "text/plain; charset=utf-8", b"pedido acima de 2048 bytes")
        try:
            pedido = json.loads(self.rfile.read(int(tamanho)).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._send(400, "text/plain; charset=utf-8", b"invalid JSON")
        try:
            dados = modelos_painel.decidir(pedido)
        except modelos_painel.ErroModelos as erro:
            return self._send(erro.status, "text/plain; charset=utf-8", erro.motivo.encode("utf-8"))
        return self._send(200, "application/json; charset=utf-8", json.dumps(dados, ensure_ascii=False).encode("utf-8"))

    def _historia_listar(self) -> None:
        """Seção História (11/11/2026): tomos e textos de historia/, só leitura. A checagem de origem já rodou em do_GET."""
        try:
            dados = historia_painel.listar()
        except historia_painel.ErroHistoria as erro:
            return self._send(erro.status, "text/plain; charset=utf-8", erro.motivo.encode("utf-8"))
        return self._send(200, "application/json; charset=utf-8", json.dumps(dados, ensure_ascii=False).encode("utf-8"))

    def _historia_texto(self) -> None:
        """Um texto da História. tomo e texto vêm na query e têm formato fixo (historia_painel.ler)."""
        query = parse_qs(urlparse(self.path).query)
        try:
            dados = historia_painel.ler((query.get("tomo") or [""])[0], (query.get("texto") or [""])[0])
        except historia_painel.ErroHistoria as erro:
            return self._send(erro.status, "text/plain; charset=utf-8", erro.motivo.encode("utf-8"))
        return self._send(200, "application/json; charset=utf-8", json.dumps(dados, ensure_ascii=False).encode("utf-8"))

    def _historia_ouvir(self) -> None:
        """Botão Ouvir da História: POST JSON {tomo, texto}, só da própria origem. Responde falou ou não falou."""
        if (self.headers.get("Origin") != ALLOWED_ORIGIN
                or self.headers.get("Sec-Fetch-Site") not in {"same-origin", "none"}
                or self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json"):
            return self._send(403, "text/plain; charset=utf-8", b"same-origin JSON required")
        tamanho = self.headers.get("Content-Length", "")
        if not tamanho.isdecimal() or int(tamanho) > 512:
            return self._send(400, "text/plain; charset=utf-8", b"invalid body size")
        try:
            pedido = json.loads(self.rfile.read(int(tamanho)) or b"{}")
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            return self._send(400, "text/plain; charset=utf-8", b"invalid JSON")
        if not isinstance(pedido, dict):
            return self._send(400, "text/plain; charset=utf-8", b"invalid request")
        try:
            dados = historia_painel.ouvir(pedido.get("tomo"), pedido.get("texto"))
        except historia_painel.ErroHistoria as erro:
            return self._send(erro.status, "text/plain; charset=utf-8", erro.motivo.encode("utf-8"))
        return self._send(200, "application/json; charset=utf-8", json.dumps(dados, ensure_ascii=False).encode("utf-8"))

    def _json_voz(self, status: int, obj: dict) -> None:
        """Resposta JSON das rotas de voz (fala e ditado). Sucesso e erro saem no mesmo formato: {falou, motivo} ou {erro}."""
        self._send(status, "application/json; charset=utf-8", json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _seth_ouvir(self) -> None:
        """Ler em voz alta (11/11/2026). Faz falar na Máquina, então é escrita: só da origem do painel.
        Responde se falou ou NÃO falou. Demora o tempo da leitura: o Parar chega em outra conexão."""
        if not _escrita_permitida(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")):
            return self._json_voz(403, {"erro": "pedido de outra origem recusado"})
        tamanho = self.headers.get("Content-Length", "")
        if not tamanho.isdecimal():
            return self._json_voz(411, {"erro": "pedido sem tamanho (Content-Length)"})
        if int(tamanho) > seth_voz.LIMITE_CORPO_BYTES:
            return self._json_voz(413, {"erro": f"pedido acima de {seth_voz.LIMITE_CORPO_BYTES} bytes"})
        try:
            pedido = json.loads(self.rfile.read(int(tamanho)).decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return self._json_voz(400, {"erro": "pedido com JSON inválido"})
        texto = pedido.get("texto") if isinstance(pedido, dict) else None
        try:
            dados = seth_voz.iniciar(texto)
        except seth_voz.ErroVoz as erro:
            return self._json_voz(erro.status, {"erro": erro.motivo})
        return self._json_voz(200, dados)

    def _seth_ouvir_parar(self) -> None:
        """Pede a parada da leitura. Vale entre trechos. Sem corpo; se não estiver lendo, diz isso."""
        if not _escrita_permitida(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")):
            return self._json_voz(403, {"erro": "pedido de outra origem recusado"})
        return self._json_voz(200, seth_voz.parar())

    def _seth_ditado(self) -> None:
        """Ditado (11/11/2026): o áudio do microfone, em corpo cru, repassado ao ouvido local. Escrita: só da origem do painel.
        O texto volta para o campo; nada é enviado à Seth daqui."""
        if not _escrita_permitida(self.headers.get("Sec-Fetch-Site"), self.headers.get("Origin")):
            return self._json_voz(403, {"erro": "pedido de outra origem recusado"})
        tamanho = self.headers.get("Content-Length", "")
        if not tamanho.isdecimal():
            return self._json_voz(411, {"erro": "pedido sem tamanho (Content-Length)"})
        if int(tamanho) > seth_ditado.LIMITE_AUDIO_BYTES:
            return self._json_voz(413, {"erro": "gravação grande demais: o limite é 2 MB, cerca de 60 segundos. Grave menos."})
        corpo = self.rfile.read(int(tamanho))
        try:
            dados = seth_ditado.transcrever(corpo, self.headers.get("Content-Type", ""))
        except seth_ditado.ErroDitado as erro:
            return self._json_voz(erro.status, {"erro": erro.motivo})
        return self._json_voz(200, dados)

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
    _chat_snapshot = lambda: {"state": "unknown", "source": "seth-gateway", "source_ref": "127.0.0.1:20126/"}
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
    assert snapshot["chat"]["source"] == "seth-gateway" and "127.0.0.1:20126" in snapshot["chat"]["source_ref"]
    assert "Conversa com a Seth (gateway)" in snapshot["sem_leitura"]
    assert _overall_state(["ok", "ausente"]) == "warning"
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
