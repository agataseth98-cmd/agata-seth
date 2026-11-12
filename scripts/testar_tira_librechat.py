#!/usr/bin/env python3
"""Contraprova da proposta tira-librechat-07-11 (07/11/2026).

O LibreChat foi excluído pelo Humano hoje (contêineres e volumes). Enquanto o atalho `seth`
tiver `docker compose` do LibreChat ou copiar arquivos para ~/librechat, ele recria o LibreChat
vazio ao rodar. Este teste falha se isso voltar, e falha se o P-9 voltar a conferir os
contêineres do LibreChat. Só LÊ os arquivos: não roda os atalhos (eles subiriam serviços).
"""
import re
import subprocess
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SETH = RAIZ / "redesign/systemd/seth"
SETH_PARAR = RAIZ / "redesign/systemd/seth-parar"
PERIMETRO = RAIZ / "scripts/perimetro.sh"

# Padrões que não podem aparecer em linha de código (comentário não conta).
PROIBIDOS = [
    (re.compile(r"\bdocker\s+(compose|restart|start|stop|up|run)\b"), "docker compose/restart/start/stop/up/run"),
    (re.compile(r"librechat", re.IGNORECASE), "palavra LibreChat em código"),
    (re.compile(r"\bLC="), "variável LC (compose do LibreChat)"),
    (re.compile(r"~/librechat|\$HOME/librechat"), "caminho ~/librechat"),
    (re.compile(r"docker-compose\.yml"), "docker-compose.yml"),
    (re.compile(r"\b3080\b"), "porta 3080 (saúde do LibreChat)"),
]


def codigo(caminho):
    """Linhas de código, sem comentário de linha inteira nem comentário no fim da linha."""
    saida = []
    for n, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
        if linha.lstrip().startswith("#"):
            continue
        saida.append((n, re.sub(r"\s#.*$", "", linha)))
    return saida


def achados(caminho):
    out = []
    for n, linha in codigo(caminho):
        for padrao, nome in PROIBIDOS:
            if padrao.search(linha):
                out.append(f"{caminho.name}:{n}: {nome}: {linha.strip()}")
    return out


def tem(caminho, trecho):
    return any(trecho in linha for _, linha in codigo(caminho))


class TiraLibrechatDosAtalhos(unittest.TestCase):
    def test_seth_nao_sobe_nem_copia_librechat(self):
        self.assertEqual([], achados(SETH), "seth ainda mexe no LibreChat")

    def test_seth_parar_nao_para_librechat(self):
        self.assertEqual([], achados(SETH_PARAR), "seth-parar ainda mexe no LibreChat")

    def test_gateway_modelos_e_target_continuam(self):
        self.assertTrue(tem(SETH, "systemctl --user start agata.target"))
        self.assertTrue(tem(SETH, "seth-gateway.service"))
        self.assertTrue(tem(SETH, "piper-tts.service"))
        self.assertTrue(tem(SETH_PARAR, "systemctl --user stop agata.target"))
        self.assertTrue(tem(SETH_PARAR, "seth-gateway.service"))
        self.assertTrue(tem(SETH_PARAR, "ollama stop"))

    def test_sintaxe_dos_atalhos(self):
        for caminho in (SETH, SETH_PARAR):
            r = subprocess.run(["bash", "-n", str(caminho)], capture_output=True, text=True)
            self.assertEqual(0, r.returncode, r.stderr)

    def test_p9_nao_confere_containers_do_librechat(self):
        linhas = [l for l in PERIMETRO.read_text(encoding="utf-8").splitlines() if l.startswith("P9_CONTAINERS_DOCKER=")]
        self.assertEqual(1, len(linhas), "P9_CONTAINERS_DOCKER tem de existir, mesmo vazia (set -u)")
        self.assertNotIn("librechat", linhas[0].lower())


if __name__ == "__main__":
    unittest.main()
