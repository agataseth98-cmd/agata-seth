import json
import unittest

from chat_stream import (
    MAX_CARACTERES_MENSAGEM,
    MAX_MENSAGENS,
    codificar_sse,
    eventos_do_stream,
    montar_pedido,
)


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


if __name__ == "__main__":
    unittest.main()
