#!/usr/bin/env python3
"""Testes do lote 4 das conversas (09/11/2026): ramos, feedback, resposta interrompida, continuação e ramificação.

Cada teste usa um diretório temporário no lugar de armazem.CONVERSAS_DIR; nada toca em
~/.cache/agata/painel-conversas. Os de rota sobem o servidor numa porta livre (127.0.0.1).
"""
import http.client
import importlib.util
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import armazem

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("painel_lote4", HERE / "server.py")
panel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(panel)


def id_de(n):
    return f"{n:012x}"


def no(id_, pai, role, content, **extra):
    return {"id": id_, "pai": pai, "role": role, "content": content, **extra}


# Quatro nós: duas perguntas (a1 e a3), a resposta antiga (a2) e a nova (a4). O caminho ativo é a3 -> a4.
ARVORE_COM_RAMO = {"nos": [no("a1", None, "user", "pergunta antiga"),
                           no("a2", "a1", "assistant", "resposta antiga"),
                           no("a3", None, "user", "pergunta nova"),
                           no("a4", "a3", "assistant", "resposta nova")], "folha": "a4"}


class ConversasBase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        patch = mock.patch.object(armazem, "CONVERSAS_DIR", self.dir)
        patch.start()
        self.addCleanup(patch.stop)

    def arquivo(self, n):
        return json.loads((self.dir / (id_de(n) + ".json")).read_text(encoding="utf-8"))


class RamosTests(ConversasBase):
    def test_sem_ramo_grava_no_formato_de_sempre(self):
        salvo = armazem._conversa_gravar({"id": id_de(1), "titulo": "Linear", "mensagens": [
            {"role": "user", "content": "oi"}, {"role": "assistant", "content": "olá"}]})
        self.assertIsNotNone(salvo)
        self.assertEqual(sorted(self.arquivo(1)), ["mensagens", "modelo", "titulo"], "conversa sem ramo não muda de formato")

    def test_arvore_com_ramo_grava_nos_e_le_so_o_caminho(self):
        armazem._conversa_gravar({"id": id_de(2), "titulo": "Com ramo", "arvore": ARVORE_COM_RAMO})
        arq = self.arquivo(2)
        self.assertEqual(arq["mensagens"], [{"role": "user", "content": "pergunta nova"},
                                            {"role": "assistant", "content": "resposta nova"}],
                         "o caminho ativo vai junto, para uma versão anterior abrir a conversa")
        self.assertEqual(len(arq["arvore"]["nos"]), 4)
        lida = armazem._conversa_ler(id_de(2))
        self.assertEqual(lida["mensagens"], [{"role": "user", "content": "pergunta nova"},
                                             {"role": "assistant", "content": "resposta nova"}])
        self.assertEqual(lida["arvore"]["folha"], "a4")
        self.assertEqual(len(lida["arvore"]["nos"]), 4, "a resposta antiga continua na conversa")

    def test_arvore_sem_ramo_volta_a_lista(self):
        armazem._conversa_gravar({"id": id_de(3), "titulo": "Linear", "arvore": {"nos": [
            no("a1", None, "user", "oi"), no("a2", "a1", "assistant", "olá")], "folha": "a2"}})
        self.assertIn("mensagens", self.arquivo(3))
        self.assertNotIn("arvore", self.arquivo(3))

    def test_arvore_invalida_e_recusada(self):
        base = [no("a1", None, "user", "oi")]
        casos = {
            "folha desconhecida": {"nos": base, "folha": "zz"},
            "pai depois do filho": {"nos": [no("a2", "a1", "assistant", "x"), no("a1", None, "user", "oi")], "folha": "a2"},
            "pai inexistente": {"nos": [no("a1", "nao", "user", "oi")], "folha": "a1"},
            "id repetido": {"nos": [no("a1", None, "user", "oi"), no("a1", None, "user", "outro")], "folha": "a1"},
            "id fora do formato": {"nos": [no("a-1", None, "user", "oi")], "folha": "a-1"},
            "papel desconhecido": {"nos": [no("a1", None, "system", "oi")], "folha": "a1"},
            "sem nós": {"nos": [], "folha": "a1"},
            "pai que não é texto": {"nos": [{"id": "a1", "pai": ["x"], "role": "user", "content": "oi"}], "folha": "a1"},
            "árvore que não é objeto": ["a1"],
        }
        for nome, arvore in casos.items():
            with self.subTest(caso=nome):
                self.assertIsNone(armazem._conversa_validar({"titulo": "X", "arvore": arvore}))
                self.assertIsNone(armazem._conversa_gravar({"titulo": "X", "arvore": arvore}))
        self.assertEqual(list(self.dir.glob("*.json")), [], "recusa não grava nada")

    def test_arvore_com_caminho_longo_demais_e_recusada(self):
        nos = [no(f"n{i}", f"n{i - 1}" if i else None, "user" if i % 2 == 0 else "assistant", "x") for i in range(201)]
        self.assertIsNone(armazem._conversa_validar({"titulo": "Longa", "arvore": {"nos": nos, "folha": "n200"}}))
        self.assertEqual(armazem.motivo_conversa_recusada({"arvore": {"nos": nos, "folha": "n200"}}), "mais de 200 mensagens")

    def test_arvore_com_nos_demais_tem_motivo_proprio(self):
        nos = [no(f"n{i}", None, "user", "x") for i in range(401)]
        self.assertEqual(armazem.motivo_conversa_recusada({"arvore": {"nos": nos, "folha": "n0"}}),
                         "mais de 400 mensagens contando as versões")

    def test_arvore_ilegivel_na_leitura_cai_no_caminho_mensagens(self):
        (self.dir / (id_de(4) + ".json")).write_text(json.dumps({"titulo": "X", "arvore": {"nos": "lixo"},
                                                                  "mensagens": [{"role": "user", "content": "oi"}]}), encoding="utf-8")
        lida = armazem._conversa_ler(id_de(4))
        self.assertEqual(lida["mensagens"], [{"role": "user", "content": "oi"}])
        self.assertNotIn("arvore", lida)

    def test_conversa_antiga_sem_campos_novos_le_igual(self):
        (self.dir / (id_de(5) + ".json")).write_text(json.dumps({"titulo": "Antiga", "modelo": "seth-livre", "mensagens": [
            {"role": "user", "content": "oi"}, {"role": "assistant", "content": "olá", "modelo": "seth-public"}]}), encoding="utf-8")
        self.assertEqual(armazem._conversa_ler(id_de(5)), {"schema_version": 1, "id": id_de(5), "titulo": "Antiga",
                                                           "modelo": "seth-livre", "mensagens": [
                                                               {"role": "user", "content": "oi"},
                                                               {"role": "assistant", "content": "olá", "modelo": "seth-public"}]})


class MarcasTests(ConversasBase):
    def test_feedback_interrompida_e_cortes_sobrevivem_ao_reabrir(self):
        mensagens = [{"role": "user", "content": "pergunta"},
                     {"role": "assistant", "content": "parte um e parte dois", "interrompida": True,
                      "feedback": {"nota": "ruim", "motivo": "  resposta   vaga  "}, "cortes": [9]}]
        armazem._conversa_gravar({"id": id_de(6), "titulo": "Marcas", "mensagens": mensagens})
        lida = armazem._conversa_ler(id_de(6))
        self.assertEqual(lida["mensagens"][1], {"role": "assistant", "content": "parte um e parte dois", "interrompida": True,
                                                "feedback": {"nota": "ruim", "motivo": "resposta vaga"}, "cortes": [9]})

    def test_marcas_fora_do_formato_saem_sem_recusar_a_conversa(self):
        mensagens = [{"role": "assistant", "content": "abc", "feedback": {"nota": "talvez"}, "cortes": [99], "interrompida": "sim"}]
        self.assertIsNotNone(armazem._conversa_gravar({"id": id_de(7), "mensagens": mensagens}))
        self.assertEqual(armazem._conversa_ler(id_de(7))["mensagens"][0], {"role": "assistant", "content": "abc"})

    def test_motivo_do_feedback_e_cortado_em_200(self):
        salvo = armazem._conversa_validar({"mensagens": [{"role": "assistant", "content": "x", "feedback": {"nota": "bom", "motivo": "m" * 300}}]})
        self.assertEqual(len(salvo["mensagens"][0]["feedback"]["motivo"]), armazem.FEEDBACK_MOTIVO_LIMITE)

    def test_interrompida_e_feedback_so_valem_para_resposta(self):
        salvo = armazem._conversa_validar({"mensagens": [{"role": "user", "content": "x", "interrompida": True,
                                                          "feedback": {"nota": "bom"}}]})
        self.assertEqual(salvo["mensagens"][0], {"role": "user", "content": "x"})

    def test_cortes_validos_entram_em_ordem_sem_repetir(self):
        salvo = armazem._conversa_validar({"mensagens": [{"role": "assistant", "content": "abcdef", "cortes": [4, 2, 4]}]})
        self.assertEqual(salvo["mensagens"][0]["cortes"], [2, 4])


class RamificadaTests(ConversasBase):
    def test_origem_da_ramificacao_grava_e_le(self):
        armazem._conversa_gravar({"id": id_de(8), "titulo": "Filha", "mensagens": [{"role": "user", "content": "oi"}],
                                  "ramificada_de": {"id": id_de(1), "mensagem": 1}})
        self.assertEqual(armazem._conversa_ler(id_de(8))["ramificada_de"], {"id": id_de(1), "mensagem": 1})

    def test_origem_fora_do_formato_sai_sem_recusar(self):
        ruins = [{"id": "../x", "mensagem": 1}, {"id": id_de(1), "mensagem": -1}, {"id": id_de(1), "mensagem": True},
                 {"id": id_de(1)}, "x"]
        for i, ruim in enumerate(ruins):
            with self.subTest(origem=ruim):
                n = 20 + i
                self.assertIsNotNone(armazem._conversa_gravar({"id": id_de(n), "mensagens": [{"role": "user", "content": "oi"}],
                                                               "ramificada_de": ruim}))
                self.assertNotIn("ramificada_de", armazem._conversa_ler(id_de(n)))


class ExportarImportarTests(ConversasBase):
    def gravar_com_ramo(self, n=9):
        armazem._conversa_gravar({"id": id_de(n), "titulo": "Com ramo", "arvore": ARVORE_COM_RAMO,
                                  "ramificada_de": {"id": id_de(1), "mensagem": 0}})

    def test_json_leva_os_ramos_e_a_origem_da_ramificacao(self):
        self.gravar_com_ramo()
        corpo, nome, tipo = armazem._conversa_exportar(id_de(9), "json")
        payload = json.loads(corpo)
        self.assertEqual(nome, f"agata-conversa-{id_de(9)}.json")
        self.assertEqual(len(payload["arvore"]["nos"]), 4)
        self.assertEqual(payload["ramificada_de"], {"id": id_de(1), "mensagem": 0})
        self.assertEqual(payload["origem_id"], id_de(9), "a origem de importação é a própria conversa, não a da ramificação")

    def test_markdown_so_traz_o_caminho_e_avisa(self):
        self.gravar_com_ramo()
        texto = armazem._conversa_exportar(id_de(9), "md")[0].decode("utf-8")
        self.assertIn("Este arquivo traz só o caminho escolhido", texto)
        self.assertIn("pergunta nova", texto)
        self.assertNotIn("pergunta antiga", texto)

    def test_importar_json_com_ramos_preserva_a_arvore(self):
        self.gravar_com_ramo()
        exportado = json.loads(armazem._conversa_exportar(id_de(9), "json")[0])
        # Proteção: apagar leva à lixeira, e item da lixeira conta como existente na importação. Para importar de volta,
        # a conversa precisa sair da lixeira (purga, pedida à mão).
        nome = armazem._conversa_apagar(id_de(9))
        self.assertIsNotNone(nome)
        armazem._lixeira_purgar(nome)
        resultado = armazem._conversa_importar(exportado)
        self.assertEqual(resultado["estado"], "importada")
        lida = armazem._conversa_ler(resultado["id"])
        self.assertEqual(len(lida["arvore"]["nos"]), 4)
        self.assertEqual(lida["mensagens"][-1]["content"], "resposta nova")
        self.assertEqual(lida["ramificada_de"], {"id": id_de(1), "mensagem": 0})

    def test_importar_de_novo_nao_duplica(self):
        self.gravar_com_ramo()
        exportado = json.loads(armazem._conversa_exportar(id_de(9), "json")[0])
        self.assertEqual(armazem._conversa_importar(exportado)["estado"], "ja_existe")


class BuscaListaTests(ConversasBase):
    def test_busca_ve_so_o_caminho_ativo(self):
        self.assertIsNotNone(armazem._conversa_gravar({"id": id_de(10), "titulo": "Busca", "arvore": {"nos": [
            no("a1", None, "user", "pergunta girassol"), no("a2", "a1", "assistant", "resposta"),
            no("a3", None, "user", "pergunta nova"), no("a4", "a3", "assistant", "resposta nova")], "folha": "a4"}}))
        self.assertEqual(armazem._conversas_buscar("girassol")["total"], 0, "o texto só existe numa versão que não está ativa")
        self.assertEqual(armazem._conversas_buscar("pergunta nova")["total"], 1)

    def test_lista_conta_o_caminho_ativo(self):
        armazem._conversa_gravar({"id": id_de(11), "titulo": "Lista", "arvore": ARVORE_COM_RAMO})
        item = armazem._conversas_listar()["items"][0]
        self.assertEqual(item["mensagens"], 2)


class LixeiraComRamoTests(ConversasBase):
    """Proteção + ramos: a árvore vai para a lixeira junto com a conversa e volta no restaurar."""

    def test_apagar_leva_a_arvore_para_a_lixeira_e_restaurar_devolve(self):
        armazem._conversa_gravar({"id": id_de(13), "titulo": "Com ramo", "arvore": ARVORE_COM_RAMO})
        nome = armazem._conversa_apagar(id_de(13))
        self.assertIsNotNone(nome)
        self.assertFalse((self.dir / (id_de(13) + ".json")).exists())
        item = armazem._lixeira_listar()["items"][0]
        self.assertEqual((item["id"], item["mensagens"], item["titulo"]), (id_de(13), 2, "Com ramo"))
        guardado = json.loads((self.dir / armazem.LIXEIRA_PASTA / (nome + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(len(guardado["arvore"]["nos"]), 4, "a lixeira guarda os bytes da conversa, com as versões")
        armazem._lixeira_restaurar(nome)
        lida = armazem._conversa_ler(id_de(13))
        self.assertEqual(len(lida["arvore"]["nos"]), 4)
        self.assertEqual(lida["arvore"]["folha"], "a4")
        self.assertEqual(lida["mensagens"][-1]["content"], "resposta nova")


class RotasTests(unittest.TestCase):
    """Rotas reais (POST /api/seth/conversa, GET, exportação) num servidor de teste, com as mesmas regras de origem."""

    @classmethod
    def setUpClass(cls):
        cls.old_port, cls.old_origin = panel.PORT, panel.ALLOWED_ORIGIN
        cls.server = panel.ThreadingHTTPServer(("127.0.0.1", 0), panel.Handler)
        cls.server.daemon_threads = True
        panel.PORT = cls.server.server_address[1]
        panel.ALLOWED_ORIGIN = f"http://127.0.0.1:{panel.PORT}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        panel.PORT, panel.ALLOWED_ORIGIN = cls.old_port, cls.old_origin

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patch = mock.patch.object(armazem, "CONVERSAS_DIR", Path(tmp.name))
        patch.start()
        self.addCleanup(patch.stop)

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=3)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            conn.close()

    def cabecalhos(self):
        return {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json"}

    def test_post_com_ramo_e_get_devolve_a_arvore(self):
        corpo = json.dumps({"titulo": "Ramo", "modelo": "seth-livre", "arvore": ARVORE_COM_RAMO}).encode("utf-8")
        status, resposta, _ = self.request("POST", "/api/seth/conversa", corpo, self.cabecalhos())
        self.assertEqual(status, 200, resposta)
        conversa_id = json.loads(resposta)["id"]
        status, resposta, _ = self.request("GET", f"/api/seth/conversa?id={conversa_id}")
        self.assertEqual(status, 200)
        dados = json.loads(resposta)
        self.assertEqual(dados["arvore"]["folha"], "a4")
        self.assertEqual([m["content"] for m in dados["mensagens"]], ["pergunta nova", "resposta nova"])

    def test_post_com_arvore_invalida_recusa_com_400(self):
        corpo = json.dumps({"titulo": "Ruim", "arvore": {"nos": [], "folha": "x"}}).encode("utf-8")
        status, _, _ = self.request("POST", "/api/seth/conversa", corpo, self.cabecalhos())
        self.assertEqual(status, 400)

    def test_origem_cruzada_recusada(self):
        corpo = json.dumps({"titulo": "X", "mensagens": [{"role": "user", "content": "oi"}]}).encode("utf-8")
        cabecalhos = {**self.cabecalhos(), "Origin": "http://evil.example", "Sec-Fetch-Site": "cross-site"}
        status, _, _ = self.request("POST", "/api/seth/conversa", corpo, cabecalhos)
        self.assertEqual(status, 403)

    def test_exportacao_pela_rota_leva_os_ramos(self):
        corpo = json.dumps({"id": id_de(12), "titulo": "Export", "arvore": ARVORE_COM_RAMO}).encode("utf-8")
        self.assertEqual(self.request("POST", "/api/seth/conversa", corpo, self.cabecalhos())[0], 200)
        status, resposta, cab = self.request("GET", f"/api/seth/conversa/exportar?id={id_de(12)}&formato=json")
        self.assertEqual(status, 200)
        self.assertIn("attachment", cab.get("Content-Disposition", ""))
        self.assertEqual(len(json.loads(resposta)["arvore"]["nos"]), 4)


if __name__ == "__main__":
    unittest.main()
