import os
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import fotografar  # noqa: E402
import saude  # noqa: E402

SHOW = {"ok": True, "saida": "Id=omniroute.service\nActiveState=active\nSubState=running\n\n"
                              "Id=seth-gateway.service\nActiveState=inactive\nSubState=dead\n"}
SS = {"ok": True, "saida": "LISTEN 0 128 127.0.0.1:20128 0.0.0.0:*\nLISTEN 0 128 [::1]:11434 [::]:*\n"}
REC = {"disco_livre_pct": 40.0, "memoria_disponivel_pct": 60.0, "carga_1min_por_cpu": 0.2, "temperatura_max_c": 60.0}


def foto(**kw):
    base = {"servicos": {"omniroute.service": "active/running", "seth-gateway.service": "inactive/dead"},
            "recursos": dict(REC), "modelos": {"erros": {}}}
    base.update(kw)
    return base


class FotografiaTests(unittest.TestCase):
    def test_so_le_com_get_e_separa_campos(self):
        metodos = []

        class Resp:
            def __init__(self, corpo): self.corpo = corpo
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return self.corpo

        def urlopen(req, timeout=None):
            metodos.append(req.get_method())
            if req.full_url.endswith("/api/tags"):
                return Resp(b'{"models":[{"name":"qwen3:4b"}]}')
            if req.full_url.endswith("/api/models"):
                return Resp(b'{"models":[{"fullModel":"g/x","available":true}]}')
            return Resp(b'{"combos":[{"name":"seth-livre","models":[{"model":"g/x"}]}]}')
        with tempfile.TemporaryDirectory() as t, mock.patch.object(urllib.request, "urlopen", urlopen):
            os.environ["AGATA_NV_DIR"] = t
            f = fotografar.fotografar(show=lambda *a: SHOW, ss=lambda *a: SS, recursos=REC)
            self.assertTrue((Path(t) / "corpo" / "fotografias.jsonl").exists())
        self.assertEqual(set(metodos), {"GET"})
        tab = f["modelos"]["tabela"]
        self.assertTrue(tab["ollama-local/qwen3:4b"]["instalado"])
        self.assertEqual(tab["g/x"]["em_fila"], ["seth-livre"])
        self.assertIsNone(tab["g/x"]["testado"])   # testado só vem de medição própria
        self.assertEqual(f["servicos"]["seth-gateway.service"], "inactive/dead")
        self.assertEqual(f["portas"], [11434, 20128])


class SaudeTests(unittest.TestCase):
    def test_cinco_estados_e_sob_demanda_nao_rebaixa(self):
        self.assertEqual(saude.classificar(foto())["estado"], "normal")
        self.assertEqual(saude.classificar(foto(recursos={**REC, "disco_livre_pct": 10}))["estado"], "pressionado")
        self.assertEqual(saude.classificar(foto(recursos={**REC, "memoria_disponivel_pct": 2}))["estado"], "degradado")
        self.assertEqual(saude.classificar(foto(modelos={"erros": {"catalogo": "x", "combos": "x"}}))["estado"], "isolado")
        self.assertEqual(saude.classificar(foto(modelos={"erros": {"ollama": "x", "catalogo": "x", "combos": "x"}}))["estado"],
                         "indisponivel")
        sem = saude.classificar(foto(recursos={**REC, "temperatura_max_c": None}))
        self.assertEqual(sem["nao_medido"], ["temperatura_max_c"])


if __name__ == "__main__":
    unittest.main()
