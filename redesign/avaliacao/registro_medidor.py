"""Adaptador do registro comum para os medidores antigos (lote 5, A5).

`teste_portugues`, `medir_contexto_efetivo` e `seth_autodev` ganham a flag `--registro`, que chama
`gravar(...)`. Sem a flag, nada muda. O CI roda os selftests desses scripts com `python3 -I`, e por isso
o caminho do pacote é inserido aqui, dentro da função, e não no topo do script.
"""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def gravar(medidor: str, split: str, itens: list[dict], resumo: dict) -> str:
    """itens: dicts com task_id, condition, model_id, outcome e, opcionalmente, failure_stage, latency_ms, usage."""
    sys.path.insert(0, str(AQUI))
    import registro  # noqa: E402
    conj = [{"task_id": i["task_id"], "condicao": i["condition"]} for i in itens]
    run = registro.abrir(medidor, split, registro.hash_conjunto(conj), extra={"medidor_resumo": resumo})
    for i in itens:
        registro.linha(run, task_id=str(i["task_id"]), condition=str(i["condition"]), model_id=i.get("model_id"),
                       outcome=i.get("outcome", "falhou"), failure_stage=i.get("failure_stage"),
                       latency_ms=i.get("latency_ms"), usage=i.get("usage"))
    registro.fechar(run, resumo)
    return run["run_id"]
