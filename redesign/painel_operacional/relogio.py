"""Relógio do painel: carimbo de leitura e janela de frescor. Saiu de server.py em 03/11/2026."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

FRESH_SECONDS = 60


def _now() -> datetime:
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


def _stamp(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _reading_window() -> tuple[str, str]:
    observed = _now()
    return _stamp(observed), _stamp(observed + timedelta(seconds=FRESH_SECONDS))
