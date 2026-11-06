"""Testes da falha segura da voz (falha_segura.py)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from falha_segura import AVISO_SEM_VOZ, resposta_ao_usuario, transcricao_segura  # noqa: E402


class TestRespostaAoUsuario(unittest.TestCase):

    def test_modo_voz(self):
        r = resposta_ao_usuario("Olá, tudo bem?", True, None)
        self.assertEqual(r, {"modo": "voz", "texto": "Olá, tudo bem?", "falou": True})

    def test_modo_texto(self):
        r = resposta_ao_usuario("Olá, tudo bem?", False, "piper fora do ar")
        self.assertEqual(
            r,
            {
                "modo": "texto",
                "texto": "Olá, tudo bem?",
                "falou": False,
                "aviso": "A voz não respondeu; segue por texto.",
            },
        )
        self.assertEqual(r["aviso"], AVISO_SEM_VOZ)

    def test_falou_e_false_no_modo_texto(self):
        r = resposta_ao_usuario("Resposta", False, None)
        self.assertIs(r["falou"], False)
        self.assertEqual(r["modo"], "texto")

    def test_audio_nao_booleano_nao_conta_como_falou(self):
        # Fail-safe: so audio_ok is True libera o modo voz.
        r = resposta_ao_usuario("Resposta", 1, None)
        self.assertEqual(r["modo"], "texto")
        self.assertIs(r["falou"], False)

    def test_texto_vazio_recusado(self):
        with self.assertRaises(ValueError):
            resposta_ao_usuario("", True, None)

    def test_texto_so_espacos_recusado(self):
        with self.assertRaises(ValueError):
            resposta_ao_usuario("   \n", False, "motivo")


class TestTranscricaoSegura(unittest.TestCase):

    def test_none(self):
        self.assertEqual(
            transcricao_segura(None),
            {"ok": False, "motivo": "transcrição vazia ou ausente", "texto": None},
        )

    def test_sem_campo_texto(self):
        self.assertEqual(
            transcricao_segura({"idioma": "pt"}),
            {"ok": False, "motivo": "transcrição vazia ou ausente", "texto": None},
        )

    def test_texto_vazio_ou_so_espacos(self):
        for resultado in ({"texto": ""}, {"texto": "   "}, {"texto": None}):
            with self.subTest(resultado=resultado):
                self.assertEqual(
                    transcricao_segura(resultado),
                    {"ok": False, "motivo": "transcrição vazia ou ausente", "texto": None},
                )

    def test_transcricao_ok(self):
        self.assertEqual(
            transcricao_segura({"texto": "bom dia"}),
            {"ok": True, "texto": "bom dia", "motivo": None},
        )


if __name__ == "__main__":
    unittest.main()
