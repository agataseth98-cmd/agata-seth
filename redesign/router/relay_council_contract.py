"""Contrato tipado de resultados do RelayCouncil.

Resultados aceitos vêm de uma aba de chat aprovada ou de entrada manual. A
extensão interage com o DOM da aba já aberta; não lê nem exporta cookies,
tokens ou credenciais. O texto de entrada e de resposta é dado externo não
confiável; antes de persistir ou encaminhar ao cache comum, o consumidor deve
aplicar o sanitizador existente. O histórico local fica fora do repositório.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any, Mapping


CONTRACT_VERSION = "relay-council-evaluation/v4"
ALLOWED_STATES = frozenset({
    "candidate",
    "green",
    "monitoring",
    "provider_busy",
    "excluded",
})
ALLOWED_ACCESS_MODES = frozenset({"browser_tab", "manual"})
ALLOWED_PROVIDERS = frozenset({
    "deepseek", "gemini", "zai", "chatgpt", "claude", "grok", "qwen",
    "mistral", "kimi",
})
MAX_ID_CHARS = 96
MAX_TEXT_CHARS = 60_000
MAX_ERROR_CHARS = 2_000
_FORBIDDEN_WORDS = (
    "authorization", "cookie", "password", "passwd", "secret", "token",
    "credential", "session", "bearer", "api_key", "apikey",
)
_KEY_SEPARATORS = re.compile(r"([a-z0-9])([A-Z])")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,95}\Z")


class RelayCouncilContractError(ValueError):
    """Payload do relay não pode entrar no boundary do sistema."""


def _normalized_key(key: Any) -> str:
    camel_split = _KEY_SEPARATORS.sub(r"\1_\2", str(key))
    return _NON_ALNUM.sub("_", camel_split.lower()).strip("_")


def _has_forbidden_key(value: Any, path: str = "") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = _normalized_key(key)
            words = set(normalized.split("_"))
            if any(word in words or word.replace("_", "") in normalized.replace("_", "")
                   for word in _FORBIDDEN_WORDS):
                return f"campo proibido: {path}{key}"
            found = _has_forbidden_key(child, f"{path}{key}.")
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found = _has_forbidden_key(child, f"{path}{index}.")
            if found:
                return found
    return None


def _required_id(payload: Mapping[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str):
        raise RelayCouncilContractError(f"campo obrigatório inválido: {name}")
    value = value.strip()
    if len(value) > MAX_ID_CHARS or not _ID.fullmatch(value):
        raise RelayCouncilContractError(f"identificador inválido: {name}")
    return value


def _optional_text(value: Any, name: str, limit: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise RelayCouncilContractError(f"{name} deve ser texto")
    value = value.strip()
    if len(value) > limit:
        raise RelayCouncilContractError(f"{name} excede o limite")
    return value or None


def _timestamp(value: Any) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if not isinstance(value, str):
        raise RelayCouncilContractError("timestamp deve ser texto ISO-8601")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RelayCouncilContractError("timestamp inválido") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RelayCouncilContractError("timestamp precisa informar fuso horário")
    return parsed.astimezone(timezone.utc).isoformat()


def normalize_evaluation(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Valida e reduz uma avaliação ao esquema público do Conselho.

    Chaves desconhecidas são descartadas. Campos que aparentam conter
    credenciais, cookies ou sessão são recusados antes de qualquer redução.
    """
    if not isinstance(payload, Mapping):
        raise RelayCouncilContractError("resultado deve ser um objeto")
    forbidden = _has_forbidden_key(payload)
    if forbidden:
        raise RelayCouncilContractError(forbidden)

    task_id = _required_id(payload, "task_id")
    provider = _required_id(payload, "provider")
    if provider not in ALLOWED_PROVIDERS:
        raise RelayCouncilContractError("provider não está no roster do Conselho")
    site = _required_id(payload, "site")
    access_mode = payload.get("access_mode")
    if not isinstance(access_mode, str) or access_mode not in ALLOWED_ACCESS_MODES:
        raise RelayCouncilContractError("access_mode deve ser browser_tab ou manual")
    state = payload.get("state", "candidate")
    if not isinstance(state, str) or state not in ALLOWED_STATES:
        raise RelayCouncilContractError("state inválido")
    ok = payload.get("ok")
    if not isinstance(ok, bool):
        raise RelayCouncilContractError("ok deve ser booleano")

    text = _optional_text(payload.get("text"), "text", MAX_TEXT_CHARS)
    error = _optional_text(payload.get("error"), "error", MAX_ERROR_CHARS)
    if ok and (state not in {"green", "candidate", "monitoring"} or not text):
        raise RelayCouncilContractError("resposta positiva precisa de texto e estado compatível")
    if not ok and state == "green":
        raise RelayCouncilContractError("estado green exige ok=true")

    latency_ms = payload.get("latency_ms")
    if latency_ms is not None:
        if (isinstance(latency_ms, bool) or not isinstance(latency_ms, (int, float))
                or not math.isfinite(latency_ms) or latency_ms < 0):
            raise RelayCouncilContractError("latency_ms inválido")

    return {
        "contract": CONTRACT_VERSION,
        "task_id": task_id,
        "provider": provider,
        "site": site,
        "access_mode": access_mode,
        "state": state,
        "ok": ok,
        "text": text if ok else None,
        "error": error,
        "latency_ms": latency_ms,
        "timestamp": _timestamp(payload.get("timestamp")),
    }
