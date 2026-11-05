import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import aquisicao  # noqa: E402
import cadastro  # noqa: E402
import fornecedores  # noqa: E402
import sandbox  # noqa: E402

VENV_PY = Path.home() / ".local" / "share" / "agata" / "nova-versao" / "ferramentas" / "pdf-venv" / "bin" / "python"


def pdf_minimo(texto: str) -> bytes:
    """PDF de uma página com um texto em Helvetica; offsets do xref calculados aqui."""
    stream = f"BT /F1 18 Tf 72 720 Td ({texto}) Tj ET".encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    corpo = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(corpo))
        corpo += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(corpo)
    corpo += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()
    for o in offs:
        corpo += f"{o:010d} 00000 n \n".encode()
    corpo += f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return corpo


class PdfTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = str(Path(self.tmp.name) / "dados")
        self.arq = Path(self.tmp.name) / "horta.pdf"
        self.arq.write_bytes(pdf_minimo("Horta urbana precisa de compostagem"))

    def tearDown(self):
        self.tmp.cleanup()

    @unittest.skipUnless(sandbox.disponivel() and shutil.which("pdftotext"), "precisa de bwrap e pdftotext")
    def test_pdf_com_pdftotext_dentro_do_sandbox(self):
        texto, motivo = aquisicao._texto_de(self.arq, "pdf")
        self.assertIsNone(motivo)
        self.assertIn("compostagem", texto)

    @unittest.skipUnless(sandbox.disponivel() and VENV_PY.exists(), "precisa de bwrap e do venv pypdf")
    def test_pdf_com_venv_pypdf_quando_nao_ha_pdftotext(self):
        original = shutil.which
        try:
            shutil.which = lambda nome, *a, **k: None if nome == "pdftotext" else original(nome, *a, **k)
            venv_dir = Path.home() / ".local" / "share" / "agata" / "nova-versao" / "ferramentas" / "pdf-venv"
            link = Path(os.environ["AGATA_NV_DIR"]) / "alexandria" / "ferramentas"
            link.mkdir(parents=True, exist_ok=True)
            (link / "pdf-venv").symlink_to(venv_dir)
            texto, motivo = aquisicao._texto_de(self.arq, "pdf")
        finally:
            shutil.which = original
        self.assertIsNone(motivo)
        self.assertIn("compostagem", texto)

    def test_sem_parser_nenhum_vira_motivo_claro(self):
        original = shutil.which
        try:
            shutil.which = lambda nome, *a, **k: None
            sandbox_disp = sandbox.disponivel
            sandbox.disponivel = lambda: True
            texto, motivo = aquisicao._texto_de(self.arq, "pdf")
        finally:
            shutil.which = original
            sandbox.disponivel = sandbox_disp
        self.assertIsNone(texto)
        self.assertIn("sem parser de PDF", motivo)


class WikipediaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = str(Path(self.tmp.name) / "dados")

    def tearDown(self):
        self.tmp.cleanup()

    def test_pesquisa_devolve_endereco_limpo_e_trecho_sem_html(self):
        resposta = {"query": {"search": [{"title": "Horta urbana", "snippet": "uma <span>horta</span> &amp; compostagem"}]}}
        r = fornecedores.wikipedia_pesquisar("horta", buscar=lambda url: json.dumps(resposta).encode())
        self.assertEqual(r[0]["url"], "https://pt.wikipedia.org/wiki/Horta_urbana")
        self.assertEqual(r[0]["trecho"], "uma horta & compostagem")

    def test_pesquisa_vazia_nao_chama_a_rede(self):
        chamou = []
        self.assertEqual(fornecedores.wikipedia_pesquisar("   ", buscar=lambda u: chamou.append(u) or b""), [])
        self.assertEqual(chamou, [])

    def test_guardar_extrato_entra_em_quarentena_com_origem(self):
        extrato = {"query": {"pages": [{"title": "Horta urbana", "extract": "Horta urbana é o cultivo em cidades."}]}}
        r = fornecedores.wikipedia_guardar("Horta urbana", buscar=lambda url: json.dumps(extrato).encode())
        c = r["cadastro"]
        self.assertEqual(c["origem_tipo"], "wikipedia")
        self.assertEqual(c["origem_uri"], "https://pt.wikipedia.org/wiki/Horta_urbana")
        self.assertEqual(c["editorial_status"], "recebido")          # não vai direto ao índice
        o = aquisicao.processar(c["sha256"])
        self.assertEqual(o["editorial_status"], "catalogado")         # quarentena concluída, ainda sem revisão do Humano

    def test_artigo_inexistente_e_recusado(self):
        vazio = {"query": {"pages": [{"title": "X", "missing": True}]}}
        with self.assertRaises(ValueError):
            fornecedores.wikipedia_guardar("X", buscar=lambda url: json.dumps(vazio).encode())


if __name__ == "__main__":
    unittest.main()
