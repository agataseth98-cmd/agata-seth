import os
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import eventos  # noqa: E402
import nv  # noqa: E402


class SincronizarTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        os.environ["AGATA_NV_DIR"] = str(t / "dados")
        self.repo = t / "repo"
        pro = self.repo / "propostas"
        (pro / "aplicadas").mkdir(parents=True)
        (pro / "x.diff").write_text("a", encoding="utf-8")
        (pro / "y.diff").write_text("b", encoding="utf-8")
        (pro / "APROVADO-y").write_text("assinada", encoding="utf-8")
        (pro / "aplicadas" / "z.diff").write_text("c", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_caminho_nunca_pula_palavra(self):
        self.assertEqual(eventos.caminho_ate(None, "assimilacao"), ["compreensao", "assimilacao"])
        self.assertEqual(eventos.caminho_ate("apresentacao", "transicao"),
                         ["compreensao", "assimilacao", "simbiose", "transicao"])
        self.assertEqual(eventos.caminho_ate("transicao", "transicao"), [])
        with self.assertRaises(ValueError):
            eventos.caminho_ate("apresentacao", "remocao_inexistente")

    def test_propostas_andam_pelos_passos_e_a_segunda_rodada_nao_repete(self):
        r1 = nv.sincronizar(self.repo)
        self.assertEqual(r1["propostas"], 3)              # x, y (com APROVADO-) e z (aplicada): três objetos
        movidas = {m["objeto"]: m for m in r1["movidas"]}
        self.assertEqual(movidas["proposta:x"]["passos"], ["apresentacao"])
        self.assertEqual(movidas["proposta:y"]["passos"], ["apresentacao", "compreensao", "assimilacao"])
        self.assertEqual(movidas["proposta:z"]["passos"],
                         ["apresentacao", "compreensao", "assimilacao", "simbiose", "transicao"])
        self.assertEqual(eventos.ultimo_estado("proposta:z"), "transicao")
        r2 = nv.sincronizar(self.repo)
        self.assertEqual(r2["movidas"], [])                    # nada novo a registrar
        ledger = Path(os.environ["AGATA_NV_DIR"]) / "eventos" / "ledger.jsonl"
        self.assertEqual(sum('"estado_seguinte": "transicao"' in l for l in ledger.read_text().splitlines()), 1)

    def test_remocao_nunca_e_automatica(self):
        nv.sincronizar(self.repo)
        for nome in ("x", "y", "z"):
            self.assertNotEqual(eventos.ultimo_estado(f"proposta:{nome}"), "remocao")


if __name__ == "__main__":
    unittest.main()
