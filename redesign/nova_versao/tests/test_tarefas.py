import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import tarefas  # noqa: E402


class TarefasTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = self.tmp.name + "/d"
        os.environ["AGATA_NV_CACHE"] = self.tmp.name + "/c"

    def tearDown(self):
        self.tmp.cleanup()

    def test_gpu_em_fila_unica_e_teto_de_chamadas(self):
        ativos, pico, trava = [0], [0], threading.Lock()

        def f(item):
            with trava:
                ativos[0] += 1; pico[0] = max(pico[0], ativos[0])
            time.sleep(0.02)
            with trava:
                ativos[0] -= 1
            return {"ok": True}
        itens = [{"chave": f"g{i}", "recurso": "gpu"} for i in range(4)]
        t = tarefas.criar("x", itens, max_chamadas=3, prazo_s=60)
        t = tarefas.executar(t, f, paralelo=True)
        self.assertEqual(pico[0], 1)
        self.assertEqual(t["chamadas"], 3)
        self.assertEqual(t["resultados"]["g3"]["falha_etapa"], "orcamento")
        self.assertEqual(t["estado"], "concluida")

    def test_cancelar_impede_novos_itens_e_contexto_mudado_vai_para_revisao(self):
        t = tarefas.criar("x", [{"chave": "a"}, {"chave": "b"}], max_chamadas=10, prazo_s=60)
        tarefas.cancelar(t["task_id"])
        r = tarefas.executar(t, lambda i: {"ok": True}, paralelo=False)
        self.assertEqual(r["estado"], "cancelada")
        self.assertTrue(all(v["falha_etapa"] == "cancelada" for v in r["resultados"].values()))
        t2 = tarefas.criar("y", [{"chave": "a"}], max_chamadas=10, prazo_s=60)
        with mock.patch.object(tarefas, "versao_contexto", return_value="outro-commit"):
            r2 = tarefas.executar(t2, lambda i: {"ok": True})
        self.assertTrue(r2["obsoleto"])
        self.assertEqual(r2["estado"], "em_revisao")


if __name__ == "__main__":
    unittest.main()
