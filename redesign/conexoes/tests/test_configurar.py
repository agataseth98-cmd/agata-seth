"""Testes de configurar.py: listar, adicionar, id repetido, segredo inline, argumento desconhecido,
host e porta, tarifa pela CLI, trava e portas de chamada sem rede. Nenhuma rede real: o transporte
e urlopen são substituídos e contados."""
import contextlib
import fcntl
import importlib
import io
import json
import os
import stat
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(AQUI.parents[1] / "nova_versao"))
import adaptadores  # noqa: E402
import configurar  # noqa: E402
import eventos  # noqa: E402
import orcamento  # noqa: E402
import segredos  # noqa: E402

CATALOGO_REPO = AQUI.parent / "provedores.json"
CHAVE_CRUA = "sk-proj-" + "Ab3dEf7hIj9kLm2nOp4qRs6tUv8w"        # chave colada no lugar do NOME
SEGREDO_AMBIENTE = "valor-secreto-nao-pode-sair-9f8e7d6c"
SEGREDO_ARG = "SEGREDO-ARG-FICTICIO-4471"                        # argumento desconhecido com segredo
CHAVE_COFRE = "sk-" + "Q" * 30
TARIFA = {"entrada_usd_mtok": 1.0, "saida_usd_mtok": 2.0, "cambio_brl": 5.5,
          "fonte": "https://exemplo/precos", "data": "2026-11-17"}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.cat = t / "provedores.json"
        self.cat.write_text(CATALOGO_REPO.read_text(encoding="utf-8"), encoding="utf-8")
        self.cofre = t / "cofre"
        self.modo_antes = stat.S_IMODE(self.cat.stat().st_mode)
        self.pilha = contextlib.ExitStack()
        self.pilha.enter_context(mock.patch.dict(os.environ, {"AGATA_CONEXOES_DIR": str(self.cofre),
                                                              "AGATA_NV_DIR": str(t / "dados")}))
        # catálogo de ensaio: o da CLI e o que adaptadores lê (ajustar/estado) apontam para a cópia
        self.pilha.enter_context(mock.patch.object(configurar, "CATALOGO", self.cat))
        self.pilha.enter_context(mock.patch.object(adaptadores, "AQUI", t))
        for v in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENAI_X_KEY"):
            os.environ.pop(v, None)

    def tearDown(self):
        self.pilha.close()
        self.tmp.cleanup()

    def texto(self) -> str:
        return self.cat.read_text(encoding="utf-8")

    def ledger(self) -> str:
        p = Path(os.environ["AGATA_NV_DIR"]) / "eventos" / "ledger.jsonl"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def rodar(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = configurar.main(argv)
        return rc, out.getvalue(), err.getvalue()


class ListarTests(Base):
    def test_lista_provedores_e_chave_so_pelo_nome(self):
        os.environ["ANTHROPIC_API_KEY"] = SEGREDO_AMBIENTE
        itens = {i["id"]: i for i in configurar.listar()}
        self.assertIn("claude", itens)
        self.assertIn("chatgpt", itens)
        self.assertEqual(itens["claude"]["chave"], {"no_cofre": False, "no_ambiente": True})
        self.assertEqual(itens["claude"]["chave_env"], "ANTHROPIC_API_KEY")
        self.assertEqual(itens["claude"]["endpoint"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(itens["chatgpt"]["chave"], {"no_cofre": False, "no_ambiente": False})
        self.assertNotIn(SEGREDO_AMBIENTE, json.dumps(list(itens.values())))

    def test_cli_listar_texto_e_json_nao_imprimem_valor(self):
        os.environ["ANTHROPIC_API_KEY"] = SEGREDO_AMBIENTE
        segredos.gravar("chatgpt", CHAVE_COFRE, "sk-")
        rc, out, _ = self.rodar(["listar"])
        self.assertEqual(rc, 0)
        self.assertIn("variável ANTHROPIC_API_KEY", out)
        self.assertIn("no cofre", out)
        self.assertNotIn(SEGREDO_AMBIENTE, out)
        self.assertNotIn("QQQQQ", out)
        rc, out_json, _ = self.rodar(["listar", "--json"])
        self.assertEqual(rc, 0)
        self.assertNotIn(SEGREDO_AMBIENTE, out_json)
        self.assertNotIn("QQQQQ", out_json)


class AdicionarTests(Base):
    def test_pago_openai_em_um_comando_so_api(self):
        bloco = configurar.adicionar("meu-openai", "https://api.openai.com/v1", "OPENAI_X_KEY", "modelo-a,modelo-b")
        self.assertEqual(bloco["api"]["url"], "https://api.openai.com/v1/chat/completions")
        doc = json.loads(self.texto())
        novo = doc["provedores"][-1]
        self.assertEqual(novo["id"], "meu-openai")
        self.assertEqual(novo["api"]["env"], "OPENAI_X_KEY")
        self.assertEqual(novo["api"]["modelo"], "modelo-a")
        self.assertEqual(novo["api"]["modelos"], ["modelo-a", "modelo-b"])
        self.assertEqual(novo["categoria_orcamento"], {"api": "pago"})
        self.assertNotIn("cli", novo)
        self.assertNotIn("navegador", novo)
        antes = json.loads(CATALOGO_REPO.read_text(encoding="utf-8"))["provedores"]
        self.assertEqual(doc["provedores"][:-1], antes)
        self.assertEqual(stat.S_IMODE(self.cat.stat().st_mode), self.modo_antes)
        self.assertIn("provedor_adicionado", self.ledger())

    def test_anthropic_com_formato_e_sufixo_nao_duplicado(self):
        b = configurar.adicionar("anthropic-x", "https://api.anthropic.com/v1", "ANTHROPIC_X_KEY", "m1",
                                 formato="anthropic")
        self.assertEqual(b["api"]["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(b["api"]["formato"], "anthropic")
        b2 = configurar.adicionar("gw-local", "http://127.0.0.1:20127/v1/chat/completions", "GW_KEY", "m1")
        self.assertEqual(b2["api"]["url"], "http://127.0.0.1:20127/v1/chat/completions")

    def test_adicionado_passa_pelas_mesmas_portas_de_chamada_sem_rede(self):
        configurar.adicionar("meu-openai", "https://api.openai.com/v1", "OPENAI_X_KEY", "modelo-a")
        sanitizar = importlib.import_module("sanitizar")   # a régua de privacidade real, não substituída
        resposta = {"model": "modelo-a", "choices": [{"message": {"content": "pronto"}}],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 1}}
        transporte = mock.Mock(return_value=resposta)
        rede = mock.Mock(side_effect=AssertionError("chamada de rede antes do portão"))
        with mock.patch.object(adaptadores, "_post", transporte), \
                mock.patch("urllib.request.urlopen", rede), \
                mock.patch("subprocess.run", rede), \
                mock.patch.object(sanitizar, "_nomes_projeto", return_value=[]):
            # 1) pago desligado: o orçamento barra antes de qualquer envio
            self.assertEqual(adaptadores.chamar("meu-openai", "api", "oi")["falha_etapa"], "orcamento")
            o = orcamento.ler(); o["provedores"]["pago"] = True; o["teto_reais"] = 1.0; orcamento.salvar(o)
            # 2) ligado, sem tarifa datada: o custo barra
            self.assertEqual(adaptadores.chamar("meu-openai", "api", "oi")["falha_etapa"], "custo")
            adaptadores.ajustar("meu-openai", tarifa=TARIFA)
            # 3) com tarifa, sem chave no cofre nem no ambiente: a configuração barra
            self.assertEqual(adaptadores.chamar("meu-openai", "api", "oi")["falha_etapa"], "configuracao")
            transporte.assert_not_called()
            rede.assert_not_called()
            # 4) controle positivo: com a chave no ambiente, o transporte é chamado uma vez
            os.environ["OPENAI_X_KEY"] = SEGREDO_AMBIENTE
            r = adaptadores.chamar("meu-openai", "api", "oi")
            self.assertTrue(r["ok"], r)
            transporte.assert_called_once()
            self.assertEqual(transporte.call_args[0][0], "https://api.openai.com/v1/chat/completions")
            rede.assert_not_called()

    def test_tarifa_pela_cli_grava_no_formato_do_painel(self):
        rc, out, err = self.rodar(["adicionar", "--id", "meu-openai", "--base-url", "https://api.openai.com/v1",
                                   "--chave-env", "OPENAI_X_KEY", "--modelos", "m1",
                                   "--tarifa-entrada", "0,15", "--tarifa-saida", "0.60", "--cambio", "5.5",
                                   "--tarifa-fonte", "https://exemplo/precos", "--tarifa-data", "2026-11-17"])
        self.assertEqual(rc, 0, err)
        esperado = {"entrada_usd_mtok": 0.15, "saida_usd_mtok": 0.6, "cambio_brl": 5.5,
                    "fonte": "https://exemplo/precos", "data": "2026-11-17"}
        ajustes = json.loads((self.cofre / "ajustes.local.json").read_text(encoding="utf-8"))
        self.assertEqual(ajustes["meu-openai"], {"tarifa": esperado})
        self.assertEqual(adaptadores.provedor("meu-openai")["tarifa"], esperado)
        self.assertIn('"ajuste"', self.ledger())
        self.assertIn("tarifa gravada", out)

    def test_tarifa_incompleta_ou_invalida_e_recusada_antes_de_gravar(self):
        antes = self.texto()
        base = {"tarifa_entrada": "1", "tarifa_saida": "2", "cambio": "5.5",
                "tarifa_fonte": "https://exemplo/precos", "tarifa_data": "2026-11-17"}
        casos = [
            {"tarifa_entrada": "1"},                                       # incompleta
            {**base, "tarifa_entrada": "-1"},
            {**base, "tarifa_entrada": "abc"},
            {**base, "tarifa_entrada": "1001"},
            {**base, "tarifa_entrada": "nan"},
            {**base, "cambio": "0"},
            {**base, "cambio": "101"},
            {**base, "tarifa_data": "17/11/2026"},
            {**base, "tarifa_data": "2026-02-30"},
            {**base, "tarifa_fonte": "   "},
            {**base, "tarifa_fonte": "x" * 201},
        ]
        for extra in casos:
            with self.subTest(caso=sorted(extra)):
                with self.assertRaises(ValueError):
                    configurar.adicionar("novo-x", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1", **extra)
        self.assertEqual(self.texto(), antes)
        self.assertFalse((self.cofre / "ajustes.local.json").exists())

    def test_id_repetido_no_catalogo_e_no_local_e_recusado(self):
        antes = self.texto()
        with self.assertRaisesRegex(ValueError, "já existe"):
            configurar.adicionar("claude", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1")
        self.assertEqual(self.texto(), antes)
        local = self.cofre / "provedores.local.json"
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps([{"id": "local-x", "nome": "L", "categoria_orcamento": {"api": "pago"},
                                      "api": {"formato": "openai", "url": "https://a.b/v1/chat/completions",
                                              "env": None, "prefixo_chave": None, "modelo": "m"}}]), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "já existe"):
            configurar.adicionar("local-x", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1")
        self.assertEqual(self.texto(), antes)

    def test_id_repetido_cli_recusa_com_codigo_2(self):
        antes = self.texto()
        rc, out, err = self.rodar(["adicionar", "--id", "chatgpt", "--base-url", "https://api.openai.com/v1",
                                   "--chave-env", "OPENAI_X_KEY", "--modelos", "m1"])
        self.assertEqual(rc, 2)
        self.assertIn("recusado", err)
        self.assertEqual(self.texto(), antes)

    def test_chave_inline_e_recusada_sem_ecoar_o_valor(self):
        antes = self.texto()
        ruins = [CHAVE_CRUA, "sk-ant-" + "x" * 40, "minha_chave_secreta", "OPENAI KEY",
                 "AbCdEf1234567890GhIjKlMnOpQr", "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", "", "OPENAI_API_KEY=abc"]
        for ruim in ruins:
            with self.subTest(valor=ruim[:6]):
                with self.assertRaises(ValueError) as cm:
                    configurar.adicionar("novo-x", "https://api.exemplo.com/v1", ruim, "m1")
                if ruim:
                    self.assertNotIn(ruim, str(cm.exception))
        self.assertEqual(self.texto(), antes)
        rc, out, err = self.rodar(["adicionar", "--id", "novo-x", "--base-url", "https://api.openai.com/v1",
                                   "--chave-env", CHAVE_CRUA, "--modelos", "m1"])
        self.assertEqual(rc, 2)
        self.assertNotIn(CHAVE_CRUA, out + err)
        self.assertEqual(self.texto(), antes)

    def test_argumento_desconhecido_com_segredo_nao_ecoa(self):
        antes = self.texto()
        base = ["adicionar", "--id", "novo-x", "--base-url", "https://api.exemplo.com/v1",
                "--chave-env", "EXEMPLO_KEY", "--modelos", "m1"]
        casos = [base + [SEGREDO_ARG], base + [f"--sem-nome={SEGREDO_ARG}"], base + ["--formato", SEGREDO_ARG],
                 ["listar", SEGREDO_ARG], ["adicionar", "--id", SEGREDO_ARG]]
        for argv in casos:
            with self.subTest(argv=argv[-1][:12]):
                rc, out, err = self.rodar(argv)
                self.assertEqual(rc, 2)
                self.assertIn("erro", err)
                self.assertNotIn(SEGREDO_ARG, out + err)
        self.assertEqual(self.texto(), antes)

    def test_nome_de_variavel_valido_e_aceito(self):
        for nome in ("OPENAI_X_KEY", "MISTRAL_API_KEY", "GW_KEY"):
            with self.subTest(nome=nome):
                b = configurar.adicionar(f"p-{nome.lower().replace('_', '-')}", "https://api.exemplo.com/v1",
                                         nome, "m1")
                self.assertEqual(b["api"]["env"], nome)

    def test_base_url_fora_do_permitido_e_recusada_sem_eco(self):
        antes = self.texto()
        ruins = ["http://api.exemplo.com/v1", "https://user:SEGREDO-URL-123@api.exemplo.com/v1",
                 "https://api.exemplo.com/v1?key=SEGREDO-URL-123", "https://api.exemplo.com/v1#frag",
                 "http://127.0.0.1:9999/v1", "ftp://api.exemplo.com/v1", "http://localhost:20128/v1"]
        for ruim in ruins:
            with self.subTest(url=ruim):
                with self.assertRaises(ValueError) as cm:
                    configurar.adicionar("novo-x", ruim, "EXEMPLO_KEY", "m1")
                self.assertNotIn("SEGREDO-URL-123", str(cm.exception))
        self.assertEqual(self.texto(), antes)
        self.assertEqual(configurar.endereco("http://127.0.0.1:20128/v1", "openai"),
                         "http://127.0.0.1:20128/v1/chat/completions")

    def test_host_e_porta_validados_antes_de_gravar(self):
        antes = self.texto()
        ruins = ["https://./v1", "https://api..exemplo.com/v1", "https://-api.exemplo.com/v1",
                 "https://api-.exemplo.com/v1", "https://" + "a" * 64 + ".exemplo.com/v1",
                 "https://api_x.exemplo.com/v1", "https://api.exemplo.com:99999/v1",
                 "https://api.exemplo.com:0/v1", "https://api.exemplo.com:/v1"]
        for ruim in ruins:
            with self.subTest(url=ruim[:40]):
                with self.assertRaises(ValueError):
                    configurar.adicionar("novo-x", ruim, "EXEMPLO_KEY", "m1")
        self.assertEqual(self.texto(), antes)
        for ok in ("https://api.exemplo.com:443/v1", "https://api.exemplo.com:65535/v1"):
            with self.subTest(url=ok):
                self.assertTrue(configurar.endereco(ok, "openai").startswith(ok))
        b = configurar.adicionar("porta-443", "https://api.exemplo.com:443/v1", "EXEMPLO_KEY", "m1")
        self.assertEqual(b["api"]["url"], "https://api.exemplo.com:443/v1/chat/completions")

    def test_modelos_e_formato_invalidos_sao_recusados(self):
        antes = self.texto()
        for modelos in ("", " , ", "a,a", "modelo com espaço"):
            with self.subTest(modelos=modelos):
                with self.assertRaises(ValueError):
                    configurar.adicionar("novo-x", "https://api.exemplo.com/v1", "EXEMPLO_KEY", modelos)
        with self.assertRaises(ValueError):
            configurar.adicionar("novo-x", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1", formato="gemini")
        self.assertEqual(self.texto(), antes)

    def test_cli_adiciona_e_resume_sem_valor(self):
        os.environ["OPENAI_X_KEY"] = SEGREDO_AMBIENTE
        rc, out, err = self.rodar(["adicionar", "--id", "meu-openai", "--base-url", "https://api.openai.com/v1",
                                   "--chave-env", "OPENAI_X_KEY", "--modelos", "m1,m2"])
        self.assertEqual(rc, 0, err)
        self.assertIn("adicionado: meu-openai", out)
        self.assertIn("variável OPENAI_X_KEY presente", out)
        self.assertIn("sem tarifa", out)
        self.assertIn("aba Conexões do painel", out)
        self.assertNotIn("repetir", out)
        self.assertNotIn(SEGREDO_AMBIENTE, out + self.texto())

    def test_trava_cobre_leitura_checagem_e_gravacao(self):
        lock = self.cofre / "provedores.lock"
        checado = []

        def sob_trava_ou_falha(etapa):
            fd = os.open(lock, os.O_RDWR)
            try:
                with self.assertRaises(BlockingIOError):   # outro descritor não consegue a trava
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                checado.append(etapa)
            finally:
                os.close(fd)

        ler_original, gravar_original = configurar.ler, configurar._gravar

        def ler_checando(caminho=None):
            sob_trava_ou_falha("leitura")
            return ler_original(caminho)

        def gravar_checando(caminho, dado):
            sob_trava_ou_falha("gravacao")
            return gravar_original(caminho, dado)

        with mock.patch.object(configurar, "ler", ler_checando), mock.patch.object(configurar, "_gravar", gravar_checando):
            configurar.adicionar("primeiro", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1")
        self.assertEqual(checado, ["leitura", "gravacao"])
        self.assertIn("primeiro", [p["id"] for p in json.loads(self.texto())["provedores"]])

    def test_duas_adicoes_sequenciais_persistem(self):
        configurar.adicionar("primeiro", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1")
        configurar.adicionar("segundo", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1")
        ids = [p["id"] for p in json.loads(self.texto())["provedores"]]
        self.assertEqual(ids[-2:], ["primeiro", "segundo"])

    def test_adicoes_concorrentes_nao_perdem_entrada(self):
        pids = ["conc-a", "conc-b", "conc-c", "conc-d"]
        barreira = threading.Barrier(len(pids))
        erros = []

        def adicionar(pid):
            try:
                barreira.wait(timeout=10)
                configurar.adicionar(pid, "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1")
            except Exception as e:  # noqa: BLE001 — o teste quer ver qualquer falha
                erros.append(e)

        ths = [threading.Thread(target=adicionar, args=(p,)) for p in pids]
        for t in ths:
            t.start()
        for t in ths:
            t.join(timeout=30)
        self.assertEqual(erros, [])
        ids = [p["id"] for p in json.loads(self.texto())["provedores"]]
        for pid in pids:
            self.assertIn(pid, ids)


    def test_adicoes_concorrentes_com_tarifa_persistem_todas(self):
        pids = ["tar-a", "tar-b", "tar-c", "tar-d"]
        barreira = threading.Barrier(len(pids))
        erros = []

        def adicionar(i, pid):
            try:
                barreira.wait(timeout=10)
                configurar.adicionar(pid, "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1",
                                     tarifa_entrada=str(1 + i), tarifa_saida="2", cambio="5.5",
                                     tarifa_fonte="https://exemplo/precos", tarifa_data="2026-11-17")
            except Exception as e:  # noqa: BLE001 — o teste quer ver qualquer falha
                erros.append(e)

        ths = [threading.Thread(target=adicionar, args=(i, p)) for i, p in enumerate(pids)]
        for t in ths:
            t.start()
        for t in ths:
            t.join(timeout=30)
        self.assertEqual(erros, [])
        ids = [p["id"] for p in json.loads(self.texto())["provedores"]]
        ajustes = json.loads((self.cofre / "ajustes.local.json").read_text(encoding="utf-8"))
        for i, pid in enumerate(pids):
            self.assertIn(pid, ids)
            self.assertEqual(ajustes[pid]["tarifa"]["entrada_usd_mtok"], 1.0 + i)

    def test_tarifa_gravada_sob_a_mesma_trava(self):
        lock = self.cofre / "provedores.lock"
        visto = []
        ajustar_original = adaptadores.ajustar

        def ajustar_checando(pid, **kw):
            fd = os.open(lock, os.O_RDWR)
            try:
                with self.assertRaises(BlockingIOError):   # a trava está segurada durante a tarifa
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                visto.append(pid)
            finally:
                os.close(fd)
            return ajustar_original(pid, **kw)

        with mock.patch.object(adaptadores, "ajustar", ajustar_checando):
            configurar.adicionar("trava-tar", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1",
                                 tarifa_entrada="1", tarifa_saida="2", cambio="5.5",
                                 tarifa_fonte="https://exemplo/precos", tarifa_data="2026-11-17")
        self.assertEqual(visto, ["trava-tar"])

    def test_falha_na_tarifa_desfaz_o_provedor(self):
        antes = self.texto()
        tarifa = {"tarifa_entrada": "1", "tarifa_saida": "2", "cambio": "5.5",
                  "tarifa_fonte": "https://exemplo/precos", "tarifa_data": "2026-11-17"}
        with mock.patch.object(adaptadores, "ajustar", side_effect=OSError("falha simulada na gravação")):
            with self.assertRaises(OSError):
                configurar.adicionar("tar-falha", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1", **tarifa)
        self.assertEqual(self.texto(), antes)
        # o id ficou livre: a mesma adição, agora sem a falha, passa
        configurar.adicionar("tar-falha", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1", **tarifa)
        self.assertIn("tar-falha", [p["id"] for p in json.loads(self.texto())["provedores"]])

    def _falha_so_no_registro_do_provedor(self):
        original = eventos.registrar

        def registrar(kind, status, source, *a, **kw):
            if status == "provedor_adicionado":
                raise OSError("falha simulada no registro do evento")
            return original(kind, status, source, *a, **kw)
        return mock.patch.object(eventos, "registrar", registrar)

    def test_falha_no_registro_depois_da_tarifa_restaura_catalogo_e_ajustes(self):
        self.cofre.mkdir(parents=True, exist_ok=True)
        ajustes = self.cofre / "ajustes.local.json"
        outra = {"entrada_usd_mtok": 3.0, "saida_usd_mtok": 4.0, "cambio_brl": 5.0,
                 "fonte": "https://exemplo/outra", "data": "2026-11-01"}
        ajustes.write_text(json.dumps({"chatgpt": {"tarifa": outra}}, ensure_ascii=False), encoding="utf-8")
        os.chmod(ajustes, 0o640)
        antes_cat = self.texto()
        modo_antes = stat.S_IMODE(ajustes.stat().st_mode)
        gravou = []
        ajustar_original = adaptadores.ajustar

        def ajustar_gravando(pid, **kw):
            r = ajustar_original(pid, **kw)
            gravou.append(pid)               # a tarifa já está no arquivo quando o registro falha
            return r

        with mock.patch.object(adaptadores, "ajustar", ajustar_gravando), self._falha_so_no_registro_do_provedor():
            with self.assertRaises(OSError):
                configurar.adicionar("tar-ledger", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1",
                                     tarifa_entrada="1", tarifa_saida="2", cambio="5.5",
                                     tarifa_fonte="https://exemplo/precos", tarifa_data="2026-11-17")
        self.assertEqual(gravou, ["tar-ledger"])
        self.assertEqual(self.texto(), antes_cat)
        self.assertEqual(json.loads(ajustes.read_text(encoding="utf-8")), {"chatgpt": {"tarifa": outra}})
        self.assertEqual(stat.S_IMODE(ajustes.stat().st_mode), modo_antes)
        # sem a falha, a mesma adição passa e convive com a tarifa antiga
        configurar.adicionar("tar-ledger", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1",
                             tarifa_entrada="1", tarifa_saida="2", cambio="5.5",
                             tarifa_fonte="https://exemplo/precos", tarifa_data="2026-11-17")
        self.assertEqual(set(json.loads(ajustes.read_text(encoding="utf-8"))), {"chatgpt", "tar-ledger"})

    def test_falha_no_registro_sem_ajustes_previos_nao_deixa_arquivo(self):
        antes_cat = self.texto()
        with self._falha_so_no_registro_do_provedor():
            with self.assertRaises(OSError):
                configurar.adicionar("tar-ledger", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1",
                                     tarifa_entrada="1", tarifa_saida="2", cambio="5.5",
                                     tarifa_fonte="https://exemplo/precos", tarifa_data="2026-11-17")
        self.assertEqual(self.texto(), antes_cat)
        self.assertFalse((self.cofre / "ajustes.local.json").exists())


    def test_gravacao_do_painel_entre_a_tarifa_e_a_falha_sobrevive(self):
        self.cofre.mkdir(parents=True, exist_ok=True)
        ajustes = self.cofre / "ajustes.local.json"
        outra = {"entrada_usd_mtok": 3.0, "saida_usd_mtok": 4.0, "cambio_brl": 5.0,
                 "fonte": "https://exemplo/outra", "data": "2026-11-01"}
        ajustes.write_text(json.dumps({"chatgpt": {"tarifa": outra}}, ensure_ascii=False), encoding="utf-8")
        antes_cat = self.texto()
        painel = {"entrada_usd_mtok": 9.0, "saida_usd_mtok": 8.0, "cambio_brl": 5.2,
                  "fonte": "https://exemplo/painel", "data": "2026-11-16"}
        ajustar_original = adaptadores.ajustar

        def ajustar_com_painel(pid, **kw):
            r = ajustar_original(pid, **kw)               # tarifa do id novo gravada
            ajustar_original("claude", tarifa=painel)      # o painel grava outro id no meio, sem trava
            return r

        with mock.patch.object(adaptadores, "ajustar", ajustar_com_painel), self._falha_so_no_registro_do_provedor():
            with self.assertRaises(OSError):
                configurar.adicionar("tar-painel", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1",
                                     tarifa_entrada="1", tarifa_saida="2", cambio="5.5",
                                     tarifa_fonte="https://exemplo/precos", tarifa_data="2026-11-17")
        aj = json.loads(ajustes.read_text(encoding="utf-8"))
        self.assertEqual(aj["claude"], {"tarifa": painel})   # a gravação do painel sobreviveu
        self.assertEqual(aj["chatgpt"], {"tarifa": outra})   # e o que já havia continua igual
        self.assertNotIn("tar-painel", aj)                   # a tarifa do id novo sumiu
        self.assertEqual(self.texto(), antes_cat)

    def test_gravacao_do_painel_sem_ajustes_previos_mantem_o_arquivo(self):
        antes_cat = self.texto()
        painel = {"entrada_usd_mtok": 9.0, "saida_usd_mtok": 8.0, "cambio_brl": 5.2,
                  "fonte": "https://exemplo/painel", "data": "2026-11-16"}
        ajustar_original = adaptadores.ajustar

        def ajustar_com_painel(pid, **kw):
            r = ajustar_original(pid, **kw)
            ajustar_original("claude", tarifa=painel)
            return r

        with mock.patch.object(adaptadores, "ajustar", ajustar_com_painel), self._falha_so_no_registro_do_provedor():
            with self.assertRaises(OSError):
                configurar.adicionar("tar-painel", "https://api.exemplo.com/v1", "EXEMPLO_KEY", "m1",
                                     tarifa_entrada="1", tarifa_saida="2", cambio="5.5",
                                     tarifa_fonte="https://exemplo/precos", tarifa_data="2026-11-17")
        # o arquivo não existia antes, mas agora tem a gravação do painel: não é removido
        self.assertEqual(json.loads((self.cofre / "ajustes.local.json").read_text(encoding="utf-8")),
                         {"claude": {"tarifa": painel}})
        self.assertEqual(self.texto(), antes_cat)


class SchemaTests(Base):
    def test_catalogo_versionado_passa_no_schema_e_formatacao_estavel(self):
        t = CATALOGO_REPO.read_text(encoding="utf-8")
        self.assertEqual(configurar.ler(CATALOGO_REPO)["schema_version"], 1)
        self.assertEqual(json.dumps(json.loads(t), ensure_ascii=False, indent=2) + "\n", t)

    def test_schema_recusa_api_remota_em_http_e_id_repetido(self):
        d = json.loads(CATALOGO_REPO.read_text(encoding="utf-8"))
        d["provedores"][0]["api"]["url"] = "http://api.exemplo.com/v1/messages"
        with self.assertRaises(ValueError):
            configurar.validar_catalogo(d)
        d = json.loads(CATALOGO_REPO.read_text(encoding="utf-8"))
        d["provedores"].append(dict(d["provedores"][0]))
        with self.assertRaisesRegex(ValueError, "repetido"):
            configurar.validar_catalogo(d)
        with self.assertRaises(ValueError):
            configurar.validar_catalogo({"provedores": []})


if __name__ == "__main__":
    unittest.main()
