import json
import unittest

from chat_stream import (
    MAX_CARACTERES_MENSAGEM,
    MAX_MENSAGENS,
    MODELO_PADRAO,
    MODELOS_PERMITIDOS,
    codificar_sse,
    eventos_do_stream,
    lista_modelos,
    modelo_permitido,
    modelo_real_valido,
    modelo_valido,
    montar_pedido,
)

MENSAGEM_OI = [{"role": "user", "content": "oi"}]
# Nomes do librechat.yaml que o gateway não aceita sem classificação pública, e nomes de fila do Seth.
NOMES_FORA_DA_LISTA = ("seth-zai", "seth-gemini", "seth-hf", "seth-mistral", "seth-auto",
                       "seth-rapido", "seth-pesado", "seth-codigo")


def chunk(conteudo):
    return "data: " + json.dumps(
        {"choices": [{"delta": {"content": conteudo}}]}, ensure_ascii=False
    )


class EventosDoStreamTest(unittest.TestCase):
    def test_deltas_normais_terminam_em_fim(self):
        linhas = [
            chunk("Olá"),
            "",
            chunk(", mundo"),
            "",
            "data: [DONE]",
            "",
        ]
        self.assertEqual(
            list(eventos_do_stream(linhas)),
            [
                {"tipo": "texto", "delta": "Olá"},
                {"tipo": "texto", "delta": ", mundo"},
                {"tipo": "fim"},
            ],
        )

    def test_done_sem_delta_vira_erro(self):
        linhas = [
            'data: {"choices": [{"delta": {"role": "assistant"}}]}',
            "",
            "data: [DONE]",
        ]
        self.assertEqual(
            list(eventos_do_stream(linhas)),
            [{"tipo": "erro", "motivo": "resposta vazia"}],
        )

    def test_json_invalido_vira_erro_e_para(self):
        linhas = [chunk("a"), "data: {isto não é json", chunk("b"), "data: [DONE]"]
        self.assertEqual(
            list(eventos_do_stream(linhas)),
            [
                {"tipo": "texto", "delta": "a"},
                {"tipo": "erro", "motivo": "linha de dados inválida"},
            ],
        )

    def test_stream_sem_done_vira_erro(self):
        self.assertEqual(
            list(eventos_do_stream([chunk("a")])),
            [
                {"tipo": "texto", "delta": "a"},
                {"tipo": "erro", "motivo": "stream interrompido"},
            ],
        )

    def test_comentarios_e_deltas_vazios_nao_contam(self):
        linhas = [
            ": keep-alive",
            'data: {"choices": [{"delta": {"content": ""}}]}',
            "data: [DONE]",
        ]
        self.assertEqual(
            list(eventos_do_stream(linhas)),
            [{"tipo": "erro", "motivo": "resposta vazia"}],
        )


class CodificarSseTest(unittest.TestCase):
    def test_preserva_acentos_e_separador_em_branco(self):
        dados = codificar_sse({"tipo": "texto", "delta": "ação à vista"})
        self.assertIsInstance(dados, bytes)
        self.assertEqual(
            dados.decode("utf-8"),
            'data: {"tipo": "texto", "delta": "ação à vista"}\n\n',
        )
        self.assertTrue(dados.endswith(b"\n\n"))


class MontarPedidoTest(unittest.TestCase):
    def test_monta_pedido_com_stream_true(self):
        pedido = montar_pedido([{"role": "user", "content": "oi"}])
        self.assertEqual(
            pedido,
            {
                "model": "seth-livre",
                "messages": [{"role": "user", "content": "oi"}],
                "stream": True,
            },
        )

    def test_aceita_limites_exatos(self):
        mensagens = [
            {"role": "user", "content": "x" * MAX_CARACTERES_MENSAGEM}
            for _ in range(MAX_MENSAGENS)
        ]
        self.assertEqual(len(montar_pedido(mensagens)["messages"]), MAX_MENSAGENS)

    def test_recusa_mais_de_20_mensagens(self):
        mensagens = [{"role": "user", "content": "oi"}] * (MAX_MENSAGENS + 1)
        with self.assertRaises(ValueError):
            montar_pedido(mensagens)

    def test_recusa_papel_invalido(self):
        with self.assertRaises(ValueError):
            montar_pedido([{"role": "tool", "content": "oi"}])

    def test_recusa_conteudo_nao_texto(self):
        with self.assertRaises(ValueError):
            montar_pedido([{"role": "user", "content": None}])

    def test_recusa_mensagem_longa(self):
        with self.assertRaises(ValueError):
            montar_pedido(
                [{"role": "user", "content": "x" * (MAX_CARACTERES_MENSAGEM + 1)}]
            )

    def test_recusa_lista_vazia(self):
        with self.assertRaises(ValueError):
            montar_pedido([])

    def test_erro_de_mensagem_longa_diz_o_limite_sem_ecoar_o_texto(self):
        # O servidor devolve esta frase no 400 e a UI a mostra: precisa dizer o limite e não trazer o texto do usuário.
        with self.assertRaises(ValueError) as contexto:
            montar_pedido([{"role": "user", "content": "SEGREDO" + "x" * MAX_CARACTERES_MENSAGEM}])
        motivo = str(contexto.exception)
        self.assertIn(f"{MAX_CARACTERES_MENSAGEM} caracteres", motivo)
        self.assertNotIn("SEGREDO", motivo)


class ModelosDoChatTest(unittest.TestCase):
    """Allowlist de modelos do chat: lista fixa, padrão, recusa e o modelo que vai ao pedido."""

    def test_lista_fixa_so_com_os_dois_nomes_aceitos_pelo_gateway(self):
        self.assertEqual(MODELOS_PERMITIDOS, frozenset({"seth-livre", "seth-public"}))

    def test_padrao_e_seth_livre(self):
        self.assertEqual(MODELO_PADRAO, "seth-livre")
        self.assertEqual(modelo_valido(None), "seth-livre")
        self.assertEqual(montar_pedido(MENSAGEM_OI)["model"], "seth-livre")
        self.assertEqual(montar_pedido(MENSAGEM_OI, None)["model"], "seth-livre")

    def test_modelo_escolhido_vai_ao_pedido(self):
        self.assertEqual(montar_pedido(MENSAGEM_OI, "seth-public")["model"], "seth-public")
        self.assertEqual(montar_pedido(MENSAGEM_OI, "seth-livre")["model"], "seth-livre")

    def test_lista_para_o_seletor_traz_padrao_rotulo_e_descricao(self):
        dados = lista_modelos()
        self.assertEqual(dados["schema_version"], 1)
        self.assertEqual(dados["padrao"], "seth-livre")
        self.assertEqual([m["id"] for m in dados["modelos"]], ["seth-livre", "seth-public"])
        for modelo in dados["modelos"]:
            self.assertTrue(modelo["rotulo"].strip(), modelo)
            self.assertTrue(modelo["descricao"].strip(), modelo)

    def test_lista_devolvida_nao_altera_a_lista_interna(self):
        lista_modelos()["modelos"].append({"id": "seth-zai", "rotulo": "x", "descricao": "x"})
        self.assertEqual([m["id"] for m in lista_modelos()["modelos"]], ["seth-livre", "seth-public"])

    def test_recusa_nomes_fora_da_lista(self):
        for ruim in NOMES_FORA_DA_LISTA + ("", "SETH-LIVRE", " seth-livre", "seth-livre ", "seth-livre-longo"):
            with self.subTest(modelo=ruim):
                self.assertFalse(modelo_permitido(ruim))
                with self.assertRaises(ValueError):
                    modelo_valido(ruim)
                with self.assertRaises(ValueError):
                    montar_pedido(MENSAGEM_OI, ruim)

    def test_recusa_tipos_que_nao_sao_texto(self):
        for ruim in (["seth-livre"], {"id": "seth-livre"}, 1, True, 0.5):
            with self.subTest(modelo=ruim):
                self.assertFalse(modelo_permitido(ruim))
                with self.assertRaises(ValueError):
                    montar_pedido(MENSAGEM_OI, ruim)

    def test_erro_de_modelo_nao_ecoa_o_valor_recusado(self):
        with self.assertRaises(ValueError) as contexto:
            montar_pedido(MENSAGEM_OI, "seth-zai-segredo-xyz")
        self.assertNotIn("segredo-xyz", str(contexto.exception))


class ModeloRealTest(unittest.TestCase):
    """Nome do modelo que respondeu (cabeçalho X-Modelo-Real do gateway): só passa texto curto e limpo."""

    def test_aceita_nome_de_modelo_com_barra_e_versao(self):
        for bom in ("openai/gpt-oss-120b", "seth-livre", "a.b_c:d+e-f/g", "x" * 120):
            with self.subTest(modelo=bom):
                self.assertEqual(modelo_real_valido(bom), bom)

    def test_recusa_vazio_espaco_controle_inicio_invalido_e_tipo_errado(self):
        for ruim in (None, "", " openai", "openai ", "lixo com espaço", "a\nb", "<script>", "x" * 121, "-inicio", 3, ["openai/x"]):
            with self.subTest(modelo=ruim):
                self.assertIsNone(modelo_real_valido(ruim))


if __name__ == "__main__":
    unittest.main()
