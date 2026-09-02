#!/usr/bin/env python3
"""
Adapter DeepSeek Harness (`dsh`) -- DORMENTE (P4-06).

`dsh` esta em 0.1.0-rc.5, "THERE WILL BE COMPATIBILITY-BREAKING CHANGES" (PESQUISA). Este
adapter existe so como contrato + mapa (ver adapters/dsh.md). NAO instala o `dsh`,
NAO e' importado por `grafo.py`, e levanta se chamado.

Reabrir: `dsh` com tag estavel + motivo concreto pos-Fase 8 (ver dsh.md "Gatilho de
reavaliacao" e a linha do `dsh` em PESQUISA.md).

A interface abaixo espelha `grafo.py` -- o swap futuro e' mecanico.
"""

ENABLED = False

_MOTIVO = ("dsh preview instavel (0.1.0-rc.5, breaking changes prometidas) -- "
           "ver redesign/grafo/adapters/dsh.md; reavaliar em tag estavel")


def run(entrada, repo, thread_id, tipo="trabalho", com_envelope=False):
    """Espelha grafo.run. Dispara o loop pelo `dsh` (loops/models/tools/sandboxes/UI seams)."""
    raise NotImplementedError(_MOTIVO)


def resume(thread_id, repo, aprovar=True):
    """Espelha grafo.resume. Retoma do checkpoint (session log append-only nativo do dsh)."""
    raise NotImplementedError(_MOTIVO)


# nos do loop -> seams do dsh (resumo; tabela completa em dsh.md)
NO_PARA_SEAM = {
    "hidratar": ["loops", "storage"],
    "rotear": ["models"],
    "trabalhar": ["models", "skills"],
    "verificar": ["tools", "sandboxes"],
    "portao": ["UI", "loops"],
    "registrar_e_commitar": ["tools", "storage", "sessions"],
}


if __name__ == "__main__":
    import sys
    print(f"dsh adapter -- ENABLED={ENABLED}")
    print(f"motivo: {_MOTIVO}")
    print(f"nos mapeados: {list(NO_PARA_SEAM)}")
    sys.exit(0 if ENABLED is False else 1)
