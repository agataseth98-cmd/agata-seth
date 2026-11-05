import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import registro  # noqa: E402
import registro_medidor  # noqa: E402


class RegistroMedidorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = str(Path(self.tmp.name) / "dados")

    def tearDown(self):
        self.tmp.cleanup()

    def test_grava_um_run_com_uma_linha_por_item_e_evento_no_ledger(self):
        itens = [{"task_id": "t1", "condition": "tarefa-x", "model_id": "m", "outcome": "passou"},
                 {"task_id": "t2", "condition": "tarefa-x", "model_id": "m", "outcome": "falhou", "failure_stage": "execucao"}]
        run_id = registro_medidor.gravar("teste_portugues", "dev", itens, {"n": 2})
        ls = registro.linhas(run_id)
        self.assertEqual([x["outcome"] for x in ls], ["passou", "falhou"])
        self.assertEqual(ls[0]["split"], "dev")
        resumo = json.loads((registro.pasta() / f"{run_id}.resumo.json").read_text(encoding="utf-8"))
        self.assertEqual(resumo["medidor"], "teste_portugues")


if __name__ == "__main__":
    unittest.main()
