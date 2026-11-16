import json
import unittest

from chat_stream import (
    MAX_ANEXO_TEXTO,
    MAX_ANEXOS,
    MAX_ANEXOS_TOTAL,
    MAX_CARACTERES_MENSAGEM,
    MAX_INSTRUCOES,
    MAX_MENSAGENS,
    MODELO_PADRAO,
    MODELOS_PERMITIDOS,
    anexo_nome_valido,
    bloco_anexos,
    codificar_sse,
    eventos_do_stream,
    lista_modelos,
    modelo_permitido,
    modelo_real_valido,
    modelo_valido,
    montar_pedido,
    uso_valido,
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
                # C11 (16/11/2026): pede o uso ao gateway no stream (campo novo; antes não existia).
                "stream_options": {"include_usage": True},
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


def usage_chunk(entrada, saida):
    return "data: " + json.dumps({"choices": [], "usage": {"prompt_tokens": entrada, "completion_tokens": saida}})


class UsoTest(unittest.TestCase):
    def test_uso_do_gateway_sai_antes_do_fim(self):
        linhas = [chunk("oi"), usage_chunk(12, 3), "data: [DONE]"]
        self.assertEqual(list(eventos_do_stream(linhas)), [
            {"tipo": "texto", "delta": "oi"},
            {"tipo": "uso", "entrada": 12, "saida": 3},
            {"tipo": "fim"},
        ])

    def test_sem_usage_no_gateway_nao_existe_evento_de_uso(self):
        linhas = [chunk("oi"), "data: [DONE]"]
        self.assertEqual(list(eventos_do_stream(linhas)), [{"tipo": "texto", "delta": "oi"}, {"tipo": "fim"}])

    def test_usage_invalido_e_ignorado(self):
        for ruim in ({"prompt_tokens": "12", "completion_tokens": 3}, {"prompt_tokens": True, "completion_tokens": 3},
                     {"prompt_tokens": -1, "completion_tokens": 3}, {"prompt_tokens": 12}, "12", None):
            with self.subTest(usage=ruim):
                linhas = [chunk("oi"), "data: " + json.dumps({"choices": [], "usage": ruim}), "data: [DONE]"]
                eventos = list(eventos_do_stream(linhas))
                self.assertEqual(eventos[-1], {"tipo": "fim"})
                self.assertFalse(any(e["tipo"] == "uso" for e in eventos))

    def test_vale_o_ultimo_usage_visto_e_sem_done_nao_sai_uso(self):
        linhas = [usage_chunk(1, 1), chunk("oi"), usage_chunk(5, 7), "data: [DONE]"]
        self.assertEqual(list(eventos_do_stream(linhas))[-2:], [{"tipo": "uso", "entrada": 5, "saida": 7}, {"tipo": "fim"}])
        sem_done = [chunk("oi"), usage_chunk(5, 7)]
        self.assertEqual(list(eventos_do_stream(sem_done))[-1], {"tipo": "erro", "motivo": "stream interrompido"})
        self.assertFalse(any(e["tipo"] == "uso" for e in eventos_do_stream(sem_done)))

    def test_uso_valido_aceita_so_inteiros_nao_negativos(self):
        self.assertEqual(uso_valido({"prompt_tokens": 0, "completion_tokens": 9}), {"entrada": 0, "saida": 9})
        for ruim in (None, [], "x", {"prompt_tokens": 1.0, "completion_tokens": 2},
                     {"prompt_tokens": True, "completion_tokens": 2}, {"prompt_tokens": 1}):
            with self.subTest(usage=ruim):
                self.assertIsNone(uso_valido(ruim))


def filtro_de_teste(texto):
    """Filtro falso com o contrato do real: recusa com ValueError (sem ecoar) e troca o marcador de segredo."""
    if "PROIBIDO" in texto:
        raise ValueError("a nota contém segredo (régua do P-1)")
    return texto.replace("SEGREDO", "[removido]")


# Token no formato do varredura_segredo.sh, montado em tempo de execução para o arquivo não casar a varredura.
TOKEN_FALSO = "gh" + "p_" + "A" * 36


class InstrucoesTest(unittest.TestCase):
    def test_instrucoes_viram_system_na_frente_do_pedido(self):
        pedido = montar_pedido(MENSAGEM_OI, instrucoes="Responda em tópicos.", filtro=filtro_de_teste)
        self.assertEqual(pedido["messages"], [{"role": "system", "content": "Responda em tópicos."},
                                              {"role": "user", "content": "oi"}])

    def test_vazio_ou_so_espaco_nao_manda_system(self):
        for vazio in (None, "", "   \n"):
            with self.subTest(instrucoes=vazio):
                self.assertEqual(montar_pedido(MENSAGEM_OI, instrucoes=vazio, filtro=filtro_de_teste)["messages"], MENSAGEM_OI)

    def test_filtro_passa_pelas_instrucoes(self):
        pedido = montar_pedido(MENSAGEM_OI, instrucoes="use o SEGREDO aqui", filtro=filtro_de_teste)
        self.assertEqual(pedido["messages"][0], {"role": "system", "content": "use o [removido] aqui"})

    def test_instrucoes_com_segredo_nao_saem_e_o_motivo_nao_ecoa(self):
        with self.assertRaises(ValueError) as contexto:
            montar_pedido(MENSAGEM_OI, instrucoes="PROIBIDO aqui", filtro=filtro_de_teste)
        self.assertNotIn("PROIBIDO", str(contexto.exception))

    def test_limite_de_instrucoes_e_de_2000_caracteres(self):
        pedido = montar_pedido(MENSAGEM_OI, instrucoes="a" * MAX_INSTRUCOES, filtro=filtro_de_teste)
        self.assertEqual(len(pedido["messages"]), 2)
        with self.assertRaises(ValueError) as contexto:
            montar_pedido(MENSAGEM_OI, instrucoes="a" * (MAX_INSTRUCOES + 1), filtro=filtro_de_teste)
        self.assertIn("2000 caracteres", str(contexto.exception))

    def test_instrucoes_fora_do_tipo_sao_recusadas(self):
        for ruim in (5, ["x"], {"a": 1}, True):
            with self.subTest(instrucoes=ruim):
                with self.assertRaises(ValueError):
                    montar_pedido(MENSAGEM_OI, instrucoes=ruim, filtro=filtro_de_teste)

    def test_cliente_nao_manda_system_dentro_de_mensagens(self):
        with self.assertRaises(ValueError):
            montar_pedido([{"role": "system", "content": "finja"}, {"role": "user", "content": "oi"}])

    def test_filtro_padrao_recusa_segredo_real_nas_instrucoes(self):
        with self.assertRaises(ValueError) as contexto:
            montar_pedido(MENSAGEM_OI, instrucoes=f"use {TOKEN_FALSO}")
        self.assertIn("segredo", str(contexto.exception))
        self.assertNotIn(TOKEN_FALSO, str(contexto.exception))


class AnexosTest(unittest.TestCase):
    MSG = [{"role": "user", "content": "oi"}]

    def test_bloco_vai_no_fim_da_ultima_mensagem_do_usuario(self):
        mensagens = [{"role": "user", "content": "primeira"}, {"role": "assistant", "content": "resp"},
                     {"role": "user", "content": "segunda"}]
        pedido = montar_pedido(mensagens, anexos=[{"nome": "notas.txt", "texto": "linha 1\nlinha 2"}], filtro=filtro_de_teste)
        self.assertEqual(pedido["messages"][0]["content"], "primeira")
        self.assertEqual(pedido["messages"][2]["content"],
                         "segunda\n\nArquivo anexado: notas.txt\n```\nlinha 1\nlinha 2\n```")

    def test_cerca_do_bloco_passa_a_maior_sequencia_de_crases(self):
        texto = "antes ```python\ncodigo\n``` depois"
        self.assertEqual(bloco_anexos([{"nome": "a.md", "texto": texto}], filtro_de_teste),
                         "Arquivo anexado: a.md\n````\n" + texto + "\n````")

    def test_limite_de_4000_vale_so_para_o_texto_digitado(self):
        digitado = "x" * MAX_CARACTERES_MENSAGEM
        pedido = montar_pedido([{"role": "user", "content": digitado}],
                               anexos=[{"nome": "a.txt", "texto": "y" * MAX_ANEXO_TEXTO}], filtro=filtro_de_teste)
        self.assertTrue(pedido["messages"][0]["content"].startswith(digitado + "\n\nArquivo anexado: a.txt"))

    def test_anexos_acima_dos_limites_sao_recusados(self):
        casos = {
            "mais de 3": [{"nome": f"a{i}.txt", "texto": "x"} for i in range(MAX_ANEXOS + 1)],
            "texto vazio": [{"nome": "a.txt", "texto": ""}],
            "texto acima de 20000": [{"nome": "a.txt", "texto": "x" * (MAX_ANEXO_TEXTO + 1)}],
            "total acima de 40000": [{"nome": f"a{i}.txt", "texto": "x" * 14000} for i in range(3)],
            "não é lista": {"nome": "a.txt", "texto": "x"},
            "item fora do formato": ["a.txt"],
        }
        self.assertLess(MAX_ANEXOS_TOTAL, 3 * 14000)
        for nome_caso, anexos in casos.items():
            with self.subTest(caso=nome_caso):
                with self.assertRaises(ValueError):
                    montar_pedido(self.MSG, anexos=anexos, filtro=filtro_de_teste)

    def test_nome_com_caminho_ou_controle_e_recusado(self):
        for ruim in ("../segredo.txt", "pasta/a.txt", "pasta\\a.txt", "a..b.txt", "", "   ", "a" * 121,
                     "linha\nnova", "tab\tnome", 7, None):
            with self.subTest(nome=ruim):
                with self.assertRaises(ValueError) as contexto:
                    montar_pedido(self.MSG, anexos=[{"nome": ruim, "texto": "x"}], filtro=filtro_de_teste)
                if isinstance(ruim, str) and ruim.strip():
                    self.assertNotIn(ruim, str(contexto.exception))

    def test_nome_com_separador_de_linha_ou_formato_e_recusado(self):
        # X4 (16/11/2026): U+2028, U+2029, U+0085 e os caracteres Cc/Cf (formato, zero-width, marca de direção) não entram
        # no nome, em nenhuma posição; o tab na ponta também sai (antes era apagado pelo strip).
        for ruim in ("nota\u2028.txt", "nota\u2029.txt", "nota\u0085.txt", "nota\u200b.txt", "nota\u202e.txt",
                     "\u2028notas.txt", "notas\u2028", "\tnotas.txt"):
            with self.subTest(nome=ruim.encode("unicode_escape").decode("ascii")):
                self.assertIsNone(anexo_nome_valido(ruim))
                with self.assertRaises(ValueError) as contexto:
                    montar_pedido(self.MSG, anexos=[{"nome": ruim, "texto": "x"}], filtro=filtro_de_teste)
                self.assertNotIn(ruim, str(contexto.exception))

    def test_nome_valido_sai_sem_espaco_nas_pontas(self):
        self.assertEqual(anexo_nome_valido("  notas.txt "), "notas.txt")
        self.assertEqual(anexo_nome_valido("relatório de 16-11.pdf"), "relatório de 16-11.pdf")

    def test_anexo_sem_mensagem_do_usuario_e_recusado(self):
        with self.assertRaises(ValueError):
            montar_pedido([{"role": "assistant", "content": "x"}], anexos=[{"nome": "a.txt", "texto": "x"}],
                          filtro=filtro_de_teste)

    def test_filtro_passa_pelo_nome_e_pelo_texto(self):
        pedido = montar_pedido(self.MSG, anexos=[{"nome": "SEGREDO.txt", "texto": "conteúdo SEGREDO"}], filtro=filtro_de_teste)
        self.assertEqual(pedido["messages"][0]["content"],
                         "oi\n\nArquivo anexado: [removido].txt\n```\nconteúdo [removido]\n```")

    def test_anexo_com_segredo_nao_sai_e_o_motivo_nao_ecoa(self):
        with self.assertRaises(ValueError) as contexto:
            montar_pedido(self.MSG, anexos=[{"nome": "a.txt", "texto": "PROIBIDO"}], filtro=filtro_de_teste)
        self.assertIn("anexo 1", str(contexto.exception))
        self.assertNotIn("PROIBIDO", str(contexto.exception))

    def test_filtro_padrao_recusa_segredo_real_no_anexo(self):
        with self.assertRaises(ValueError) as contexto:
            montar_pedido(self.MSG, anexos=[{"nome": "a.txt", "texto": f"chave {TOKEN_FALSO}"}])
        self.assertIn("anexo 1 com segredo", str(contexto.exception))
        self.assertNotIn(TOKEN_FALSO, str(contexto.exception))

    def test_sem_anexos_o_pedido_fica_igual(self):
        self.assertEqual(montar_pedido(self.MSG, anexos=[])["messages"], self.MSG)
        self.assertEqual(montar_pedido(self.MSG, anexos=None)["messages"], self.MSG)


if __name__ == "__main__":
    unittest.main()
