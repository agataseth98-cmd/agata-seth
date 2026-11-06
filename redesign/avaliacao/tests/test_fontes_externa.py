"""Condição alexandria_externa mantém as fontes da própria tarefa (lote 8)."""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))
import avaliar  # noqa: E402
import externa  # noqa: E402

TAREFA = {"task_id": "rec-teste", "grupo": "recuperacao", "pedido": "Qual a capacidade?",
          "documentos": [{"id": "d1", "texto": "O reservatório tem 840 litros.", "autoridade": "canon",
                          "data": "2025-04-12", "estado": "revisado"}],
          "criterios": [{"tipo": "todos", "valor": ["840"]}]}


def test_externa_sem_fornecedor_mantem_fonte_da_tarefa(monkeypatch):
    monkeypatch.delenv("AGATA_EXTERNA_FORNECEDOR", raising=False)
    fontes, _ = avaliar.fontes(TAREFA, "alexandria_externa")
    ids = [f["id"] for f in fontes]
    assert "d1" in ids                      # a fonte da tarefa não some
    assert not any(str(i).startswith("x") for i in ids)  # sem fornecedor: nenhuma evidência externa


def test_externa_acrescenta_evidencia_externa(monkeypatch):
    monkeypatch.delenv("AGATA_EXTERNA_FORNECEDOR", raising=False)
    monkeypatch.setattr(externa, "pesquisar", lambda p, buscar=None: {
        "resultados": [{"trecho": "trecho externo", "url": "https://exemplo.test/x"}]})
    fontes, _ = avaliar.fontes(TAREFA, "alexandria_externa")
    ids = [f["id"] for f in fontes]
    assert "d1" in ids and "x1" in ids
