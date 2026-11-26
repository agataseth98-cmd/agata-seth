"""Fixtures do lote ferramentas-unificadas-26-11. Nenhum teste toca o home real nem o repositório.

Os auxiliares ficam em ferr_helpers.py (nome próprio, sem colisão com outros conftest do CI).
"""
from __future__ import annotations

import pytest

# ferr_helpers põe scripts/ferramentas no sys.path antes de importar estado (E) e os fakes
from ferr_helpers import E, entrada_teste, montar_ctx  # noqa: F401  (reexportados para quem quiser)
from fakes import FakeCLIs


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: roda a CLI real (opencode) em HOME descartável; mais lento")


@pytest.fixture
def ctx(tmp_path, monkeypatch) -> E.Contexto:
    monkeypatch.setenv("AGATA_TESTE_VAR", "valor-de-teste-nao-vai-a-fonte")
    return montar_ctx(tmp_path)


@pytest.fixture
def fake(ctx) -> FakeCLIs:
    return ctx.runner
