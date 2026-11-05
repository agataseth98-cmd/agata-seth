import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import conjunto  # noqa: E402
import revisar  # noqa: E402


class RevisarCLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = str(Path(self.tmp.name) / "dados")
        pasta = conjunto.pasta_reservado("teste2")
        pasta.mkdir(parents=True, exist_ok=True)
        t = {"task_id": "rec-01", "grupo": "recuperacao", "split": "teste2", "pedido": "p?", "autor": "Teste",
             "criterios": [{"tipo": "contem", "valor": ["x"]}],
             "documentos": [{"id": "d1", "texto": "x", "origem": "canon", "autoridade": "canon"}]}
        (pasta / conjunto.ARQ_RESERVADO).write_text(json.dumps(t) + "\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_lista_mostra_pedido_documentos_e_criterios(self):
        s = revisar.listar("teste2", id_="rec-01")
        self.assertIn("== rec-01", s)
        self.assertIn("PEDIDO: p?", s)
        self.assertIn("[d1] (canon · canon) x", s)
        self.assertIn("CRITÉRIOS: contem ['x']", s)

    def test_marcar_vale_so_para_o_hash_atual(self):
        self.assertIn("ninguém", revisar.estado("teste2"))
        self.assertEqual(revisar.main(["marcar", "--revisor", "Humano"]), 0)
        self.assertIn("revisado por: Humano", revisar.estado("teste2"))
        # muda o conjunto: a revisão deixa de valer
        p = conjunto.pasta_reservado("teste2") / conjunto.ARQ_RESERVADO
        p.write_text(p.read_text(encoding="utf-8").replace('"pedido": "p?"', '"pedido": "outro?"'), encoding="utf-8")
        self.assertIn("revise de novo", revisar.estado("teste2"))

    def test_marcar_sem_revisor_recusa(self):
        self.assertEqual(revisar.main(["marcar"]), 2)


if __name__ == "__main__":
    unittest.main()
