import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import medir_ouvido  # noqa: E402
import ouvido  # noqa: E402
import servidor_ouvido  # noqa: E402

TEM_FFMPEG = bool(shutil.which("ffmpeg"))


def wav(pasta: Path, nome="a.wav") -> Path:
    p = pasta / nome
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=440:d=1", str(p)], check=True)
    return p


class OuvidoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        os.environ["AGATA_NV_DIR"] = str(self.t / "dados")

    def tearDown(self):
        self.tmp.cleanup()

    def test_lfm3_recebe_instrucao_no_sistema_e_audio_em_images(self):
        visto = {}

        def post(url, corpo, timeout):
            visto.update(url=url, corpo=corpo)
            return {"message": {"content": " olá "}}
        a = self.t / "x.wav"
        a.write_bytes(b"RIFF0000WAVE")
        self.assertEqual(ouvido.lfm3(a, post=post), "olá")
        msgs = visto["corpo"]["messages"]
        self.assertEqual(msgs[0], {"role": "system", "content": "Perform ASR in Portuguese."})
        self.assertEqual(msgs[1]["content"], "")
        self.assertEqual(len(msgs[1]["images"]), 1)          # o campo `audio` dá 500 no Ollama 0.40.14
        self.assertTrue(visto["url"].endswith("/api/chat"))

    @unittest.skipUnless(TEM_FFMPEG, "sem ffmpeg")
    def test_reserva_so_se_o_whisper_ja_estiver_no_ar_e_nunca_liga_servico(self):
        a = wav(self.t)

        def cai(w, i):
            raise ConnectionError("ollama fora")
        r = ouvido.transcrever(a, chamar_lfm3=cai, chamar_whisper=lambda w: "reserva", whisper_ativo=lambda: True)
        self.assertEqual((r["text"], r["motor"]), ("reserva", "whisper"))
        r = ouvido.transcrever(a, chamar_lfm3=cai, chamar_whisper=lambda w: self.fail("não deveria chamar"),
                               whisper_ativo=lambda: False)
        self.assertIsNone(r["text"])
        self.assertEqual(r["falha_etapa"], "indisponivel")
        self.assertEqual([x["falha_etapa"] for x in r["tentativas"]], ["transporte", "indisponivel"])
        with self.assertRaises(ValueError):
            ouvido.transcrever(a, motor="nuvem")
        with self.assertRaises(ValueError):
            ouvido.transcrever(self.t / "nao-existe.wav")

    def test_wer_sem_acento_pontuacao_e_caixa(self):
        self.assertEqual(medir_ouvido.wer("Olá, Seth!", "ola seth"), 0)
        self.assertAlmostEqual(medir_ouvido.wer("abra o painel", "abro o painel"), 1 / 3)
        self.assertEqual(medir_ouvido.wer("a b", ""), 1)

    @unittest.skipUnless(TEM_FFMPEG, "sem ffmpeg")
    def test_medicao_grava_registro_comum_com_referencia_e_wer(self):
        def falar(texto, tocar=True, salvar=None, manter=False):
            self.assertFalse(tocar)                          # a medição nunca toca no alto-falante
            wav(salvar, "fala-01.wav")
            return 0
        frases = medir_ouvido.FRASES.read_text(encoding="utf-8").splitlines()

        def transcrever(arq, motor="auto"):
            if motor == "whisper":
                return {"text": None, "falha_etapa": "indisponivel", "erro": "fora", "proc_s": None}
            i = int(Path(arq).stem[-2:])
            return {"text": frases[i - 1], "motor": "lfm3-audio:2b", "proc_s": 0.1, "falha_etapa": None, "erro": None}
        r = medir_ouvido.medir(("lfm3", "whisper"), falar=falar, transcrever=transcrever)
        pm = r["resumo"]["por_motor"]
        self.assertEqual(pm["lfm3|limpo"]["wer"], 0)
        self.assertEqual(pm["lfm3|limpo"]["perfeitas"], 20)
        self.assertIsNone(pm["whisper|limpo"]["wer"])       # sem o serviço: não medido, nunca zero
        self.assertEqual(pm["whisper|limpo"]["nao_rodou"], 20)
        import registro
        ls = registro.linhas(r["run_id"])
        self.assertEqual(len(ls), 80)
        self.assertTrue({"referencia", "transcricao", "wer"} <= set(next(x for x in ls if x["outcome"] == "passou")))


class ServidorTests(unittest.TestCase):
    def test_multipart_openai_idioma_e_recusas(self):
        b = "XyZ"
        corpo = (f"--{b}\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\npt\r\n"
                 f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.webm\"\r\n"
                 f"Content-Type: audio/webm\r\n\r\n").encode() + b"\x00\x01" + f"\r\n--{b}--\r\n".encode()
        dados, campos = servidor_ouvido.ler_multipart(f"multipart/form-data; boundary={b}", corpo)
        self.assertEqual(dados, b"\x00\x01")
        self.assertEqual(servidor_ouvido.idioma(campos), "Portuguese")
        self.assertEqual(servidor_ouvido.idioma({"language": "en"}), "English")
        self.assertEqual(servidor_ouvido.idioma({"language": "klingon"}), "Portuguese")
        with self.assertRaises(ValueError):
            servidor_ouvido.ler_multipart("application/json", b"{}")
        self.assertEqual(servidor_ouvido.HOST, "127.0.0.1")       # só loopback; a bridge chega pelo relé
        self.assertEqual(servidor_ouvido._selftest(), 0)

    def test_porta_declarada_no_rele_no_yaml_e_na_lista_juntos(self):
        raiz = AQUI.parents[2]
        self.assertIn("20137|ouvido-agata|127.0.0.1,172.29.7.1", (raiz / "config/portas-agata.txt").read_text())
        self.assertIn(" 20137 ", (raiz / "redesign/librechat/docker-compose.yml").read_text())
        y = (raiz / "redesign/librechat/librechat.yaml").read_text()
        self.assertIn('url: "http://172.29.7.1:20137/v1/audio/transcriptions"', y)
        self.assertIn('allowedAddresses: ["172.29.7.1:20137"]', y)
        self.assertIn("ExecStart=/usr/bin/python3 %h/agata/redesign/sentidos/servidor_ouvido.py",
                      (raiz / "redesign/systemd/ouvido-agata.service").read_text())


if __name__ == "__main__":
    unittest.main()
