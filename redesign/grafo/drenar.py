#!/usr/bin/env python3
"""Dreno do WAL para o ExecStop do agata-drain.service (P7-01).

SO espera os efeitos em curso (intent sem done no eventos.ndjson) terminarem;
se nao terminarem no prazo, registra como pendentes e sai mesmo assim. NAO
para servico nenhum -- o teardown dos servicos e' do systemd (cada unit tem
PartOf=agata.target). Chamar `systemctl stop` daqui deadlocka contra a propria
transacao de stop do systemd (visto no teste P7-01, 2026-09-02).

Sai 0 sempre: travar o teardown do systemd seria pior que a lacuna que um
efeito pendente sinaliza -- o objetivo e' NAO cortar no meio de um commit, e
para isso basta esperar e, no limite, deixar o registro.

Prazo 25s < TimeoutStopSec=45 do agata-drain.service, com folga.
"""
import sys
import time

sys.path.insert(0, "/home/orusoua/agata/redesign/grafo")
from cli import _pendencias_wal  # noqa: E402  -- mesma logica de WAL do `agata down`

PRAZO_S = 25


def main() -> int:
    pend = _pendencias_wal()
    if not pend:
        print("dreno: WAL limpo, nada a esperar.")
        return 0
    print(f"dreno: {len(pend)} efeito(s) em curso -- aguardando ate {PRAZO_S}s...", flush=True)
    for _ in range(PRAZO_S):
        time.sleep(1)
        if not _pendencias_wal():
            print("dreno: efeitos concluidos, WAL limpo.")
            return 0
    resto = _pendencias_wal()
    print(f"dreno: AVISO -- {len(resto)} efeito(s) ainda pendente(s) apos {PRAZO_S}s; "
          "registrados abaixo, NAO cortados:")
    for p in resto:
        print(f"  - thread={p['thread']} node={p['node']} passo={p['passo']} chave={p['chave']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
