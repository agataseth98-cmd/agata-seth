import os
import sys
import tempfile
import threading
import unittest
from unittest import mock
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import eventos  # noqa: E402
import nv  # noqa: E402
import orcamento  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()


class EventosTests(Base):
    def test_chave_idempotente_nao_grava_duas_vezes(self):
        a = eventos.registrar("execution", "ok", "x", chave="k1")
        b = eventos.registrar("execution", "ok", "x", chave="k1")
        self.assertEqual(a["id"], b["id"])
        self.assertTrue(b.get("repetido"))
        self.assertEqual(len(eventos.ultimos(100)), 1)

    def test_escritas_concorrentes_preservam_a_cadeia(self):
        ts = [threading.Thread(target=eventos.registrar, args=("observation", "ok", f"t{i}")) for i in range(20)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(len(eventos.ultimos(100)), 20)
        self.assertTrue(eventos.verificar())

    def test_transicao_recusa_salto_e_remocao_sem_autorizacao(self):
        eventos.transicao("obj", None, "apresentacao", "pergunta definida")
        eventos.transicao("obj", "apresentacao", "compreensao", "fontes descritas")
        with self.assertRaises(ValueError):
            eventos.transicao("obj", "compreensao", "transicao", "pulou")
        with self.assertRaises(ValueError):
            eventos.transicao("obj", "transicao", "remocao", "sem ok")
        ev = eventos.transicao("obj", "transicao", "remocao", "alvo exato", autorizacao="Humano 04/11")
        self.assertEqual(ev["estado_seguinte"], "remocao")


class OrcamentoTests(Base):
    def test_padrao_so_local_e_pago_sem_teto_nao_gasta(self):
        o = orcamento.ler()
        self.assertEqual(o["provedores"], {"local": True, "gratuito": False, "assinatura": False, "pago": False})
        self.assertFalse(orcamento.permite("gratuito")[0])
        orcamento.salvar({**o, "provedores": {"local": True, "gratuito": False, "assinatura": False, "pago": True}})
        ok, motivo = orcamento.permite("pago")
        self.assertFalse(ok)
        self.assertIn("teto", motivo)
        self.assertTrue(orcamento.permite("local")[0])
        self.assertFalse(orcamento.permite("local", chamadas_ja=10**6)[0])

    def test_valores_de_fabrica_e_quatro_categorias_da_spec(self):
        o = orcamento.ler()
        self.assertEqual(orcamento.PROVEDORES, ("local", "gratuito", "assinatura", "pago"))
        self.assertEqual(o["provedores"], {"local": True, "gratuito": False, "assinatura": False, "pago": False})
        self.assertEqual((o["max_chamadas"], o["max_tokens"], o["timeout_s"], o["teto_reais"]), (200, 2_000_000, 120, 0.0))
        self.assertEqual([orcamento.permite(p)[0] for p in orcamento.PROVEDORES], [True, False, False, False])


class ReversaoTests(unittest.TestCase):
    """spec, "Migração e reversão": a reversão não apaga AGATA_NV_DIR; só remove o cache."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name).resolve()
        self.home = base / "home"                                   # home falsa: nenhum teste toca o ~/.cache real
        self._home = mock.patch.object(Path, "home", return_value=self.home)
        self._home.start()
        self.dados, self.destino = base / "dados", base / "arquivo"
        self.cache = self.home / ".cache" / "nova-versao-cache"
        self._env = {k: os.environ.get(k) for k in ("AGATA_NV_DIR", "AGATA_NV_CACHE")}
        self._cwd = os.getcwd()
        os.environ["AGATA_NV_DIR"], os.environ["AGATA_NV_CACHE"] = str(self.dados), str(self.cache)
        self.dados.mkdir(parents=True)
        (self.cache / "gpu.lock").parent.mkdir(parents=True)
        (self.cache / "gpu.lock").write_text("x", encoding="utf-8")
        self.nv = nv

    def tearDown(self):
        self._home.stop()
        os.chdir(self._cwd)
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def _recusa(self, destino=None):
        with self.assertRaises(ValueError):
            self.nv.reverter(destino if destino is not None else self.destino)
        self.assertTrue(self.dados.exists())                       # dados intactos
        self.assertTrue((self.cache / "gpu.lock").exists())        # cache sobreviveu à recusa
        self.assertFalse(self.destino.exists())                    # nenhum pacote criado

    def test_reversao_nao_apaga_dados_so_remove_cache(self):
        import tarfile
        eventos.registrar("execution", "ok", "antes da reversão")
        antes = sorted(p.relative_to(self.dados) for p in self.dados.rglob("*"))
        r = self.nv.reverter(self.destino)
        self.assertFalse(self.cache.exists())                       # cache derivado removido
        self.assertTrue(self.dados.exists())                        # dados nunca apagados
        self.assertEqual(sorted(p.relative_to(self.dados) for p in self.dados.rglob("*")), antes)
        self.assertTrue(eventos.verificar())                        # ledger íntegro depois
        pacote = Path(r["pacote"])
        self.assertEqual(r["pacote_estado"], "arquivado")
        self.assertTrue(pacote.exists() and pacote.parent == self.destino)
        with tarfile.open(pacote) as tar:
            self.assertTrue(any(n.startswith("dados/") for n in tar.getnames()))

    def test_recusa_cache_raiz_ou_home(self):
        for alvo in ("/", str(Path.home())):
            os.environ["AGATA_NV_CACHE"] = alvo
            self._recusa()

    def test_recusa_cache_igual_ou_dentro_dos_dados(self):
        for alvo in (self.dados, self.dados / "nova-versao-cache"):
            os.environ["AGATA_NV_CACHE"] = str(alvo)
            self._recusa()

    def test_recusa_cache_fora_de_cache_e_sem_nome(self):
        os.environ["AGATA_NV_CACHE"] = str(self.cache.parent / "qualquer")        # em ~/.cache, sem o nome
        self._recusa()

    def test_recusa_o_proprio_cache_e_cache_agata(self):
        for alvo in (self.home / ".cache", self.home / ".cache" / "agata"):
            os.environ["AGATA_NV_CACHE"] = str(alvo)
            self._recusa()

    def test_recusa_nova_versao_fora_de_cache(self):
        os.environ["AGATA_NV_CACHE"] = str(Path(self.tmp.name) / "x" / "nova-versao")
        self._recusa()

    def test_padrao_e_aceito_e_variavel_vazia_reverte_de_ponta_a_ponta(self):
        padrao = self.home / ".cache" / "agata" / "nova-versao"
        padrao.mkdir(parents=True)
        (padrao / "gpu.lock").write_text("x", encoding="utf-8")
        with mock.patch.object(self.nv, "CACHE_PADRAO", padrao):
            os.environ["AGATA_NV_CACHE"] = ""
            r = self.nv.reverter(self.destino)
        self.assertFalse(padrao.exists())
        self.assertTrue((self.cache / "gpu.lock").exists())         # outro cache não foi tocado
        self.assertTrue(self.dados.exists() and Path(r["pacote"]).exists())

    def test_recusa_cache_que_contem_o_diretorio_atual(self):
        os.chdir(self.cache)
        self._recusa()

    def test_recusa_destino_igual_aos_dados_ou_dentro_do_cache(self):
        self._recusa(self.dados)
        self._recusa(self.cache / "arquivo")
        self.assertTrue((self.cache / "gpu.lock").exists())

    def test_recusa_destino_dentro_do_repositorio(self):
        self._recusa(Path(self.nv.__file__).resolve().parents[2] / "arquivo-de-teste")

    def test_variavel_vazia_conta_como_ausente(self):
        os.environ["AGATA_NV_CACHE"] = ""
        self.assertEqual(self.nv._cache(), self.nv.CACHE_PADRAO)    # nunca o diretório atual
        os.environ["AGATA_NV_CACHE"] = str(self.cache)
        os.environ["AGATA_NV_DIR"] = ""
        with self.assertRaises(ValueError):
            self.nv.reverter(self.destino)
        self.assertTrue((self.cache / "gpu.lock").exists())


if __name__ == "__main__":
    unittest.main()
