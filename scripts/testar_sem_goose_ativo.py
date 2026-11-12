#!/usr/bin/env python3
"""Testa que nenhuma referência ATIVA ao Goose sobrou em código e atalhos do repositório.

Escopo (arquivos rastreados pelo git):
  * scripts/, redesign/ e config/ com extensão de código ou configuração (.py .sh .html .json .txt .yaml);
  * redesign/systemd/ sem extensão ou com extensão de unidade/atalho (.service .target .timer .conf .sh).
Fora do escopo, de propósito: documentação (.md), canon (PROJETO, AGENTS, MEMÓRIAS), skills (.agents/),
histórico (extras/, propostas/, redesign/LOG.md), dados (.jsonl) e este próprio teste.

Regra: cada arquivo do escopo com a palavra goose (sem diferenciar maiúscula) precisa estar em EXCECOES,
com a contagem EXATA de linhas e um motivo. Arquivo novo com referência reprova. Exceção que deixou de
casar também reprova: ao tirar uma referência, ajuste a contagem ou tire a entrada na mesma mudança.

Uso: python3 scripts/testar_sem_goose_ativo.py -v
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESTE = os.path.relpath(os.path.abspath(__file__), RAIZ).replace(os.sep, "/")
PADRAO = re.compile(r"goose", re.IGNORECASE)
EXTENSOES_CODIGO = (".py", ".sh", ".html", ".json", ".txt", ".yaml")
EXTENSOES_ATALHO = ("", ".service", ".target", ".timer", ".conf", ".sh")

# Referências que ficam de propósito. Contagem = linhas com a palavra, medida em origin/main (83334fde).
EXCECOES = {
    "scripts/perimetro/p08_quarentena.sh": (7, "perímetro: redesign/goose/* segue na lista enquanto o diretório existir (Passo 4 pendente); comentários são histórico de 24/09"),
    "redesign/router/seth_gateway.py": (16, "detector do payload do Goose (chamada de título, MEMÓRIAS 495); trocar exige medir antes o payload do OpenCode"),
    "redesign/router/auditoria_turno.py": (2, "docstring com a medição do Goose (MEMÓRIAS 662 e 664); OpenCode ainda não medido"),
    "scripts/estado_para_eco.sh": (1, "comentário histórico do incidente da ferramenta write do Goose (MEMÓRIAS 516 e 517)"),
    "redesign/mcp/servidor.py": (1, "lista de executores do MCP; OpenCode ainda não foi medido contra o servidor"),
    "config/portas-de-entrada.txt": (3, "rotas para redesign/goose/AGENTS.md, que fica até a decisão de remoção; lista de ferramentas que leem AGENTS.md"),
    "config/agata-identidade.json": (1, "proveniência histórica da paleta (tema do Goose); texto de origem, não referência ativa"),
    "redesign/painel_operacional/prototipo.html": (1, "palavra de busca do cartão 'Trabalhar com código'; o painel tem spec e âncora próprios, fora desta proposta"),
}


def _no_escopo(rel: str) -> bool:
    if rel == ESTE:
        return False
    if rel.startswith("redesign/systemd/"):
        return os.path.splitext(rel)[1] in EXTENSOES_ATALHO
    if rel.startswith(("scripts/", "redesign/", "config/")):
        return rel.endswith(EXTENSOES_CODIGO)
    return False


def _escopo() -> list[str]:
    saida = subprocess.run(["git", "-C", RAIZ, "ls-files", "-z"], capture_output=True, check=True).stdout
    return sorted(r for r in saida.decode("utf-8").split("\0") if r and _no_escopo(r))


def _contar(rel: str) -> int:
    with open(os.path.join(RAIZ, rel), encoding="utf-8", errors="replace") as f:
        return sum(1 for linha in f if PADRAO.search(linha))


class SemGooseAtivo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.escopo = _escopo()
        cls.contagens = {rel: _contar(rel) for rel in cls.escopo}

    def test_escopo_nao_esta_vazio(self):
        # Sem isto, um git ls-files vazio faria todos os outros testes passarem por nada.
        self.assertGreater(len(self.escopo), 100, "escopo do teste ficou pequeno demais")

    def test_nenhuma_referencia_ativa_fora_das_excecoes(self):
        reprovados = {rel: n for rel, n in self.contagens.items() if n and rel not in EXCECOES}
        self.assertEqual({}, reprovados, "referência ativa ao Goose fora das exceções listadas")

    def test_excecoes_batem_com_a_contagem_atual(self):
        for rel, (esperado, _motivo) in EXCECOES.items():
            with self.subTest(arquivo=rel):
                self.assertIn(rel, self.contagens, "exceção aponta para arquivo que não está no escopo ou não existe")
                self.assertEqual(esperado, self.contagens[rel], "contagem mudou: ajuste a exceção na mesma mudança")

    def test_toda_excecao_tem_motivo(self):
        for rel, (_n, motivo) in EXCECOES.items():
            with self.subTest(arquivo=rel):
                self.assertGreater(len(motivo.strip()), 20)

    def test_atalho_do_terminal_abre_opencode(self):
        caminho = os.path.join(RAIZ, "redesign", "systemd", "seth-agente")
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        self.assertIn("command -v opencode", texto)
        self.assertIn(".opencode/bin/opencode", texto)
        self.assertFalse("goose" in texto.lower(), "o atalho ainda cita o Goose")
        # só checagem de sintaxe: o script de verdade inicia serviços e abre terminal
        sintaxe = subprocess.run(["bash", "-n", caminho], capture_output=True, text=True)
        self.assertEqual(0, sintaxe.returncode, sintaxe.stderr)

    def test_equipe_registra_opencode_e_nao_goose(self):
        caminho = os.path.join(RAIZ, "scripts", "equipe", "equipe.py")
        with open(caminho, encoding="utf-8") as f:
            arvore = ast.parse(f.read())
        nomes = None
        for no in arvore.body:
            if isinstance(no, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "NOMES" for t in no.targets):
                nomes = ast.literal_eval(no.value)
        self.assertIsNotNone(nomes, "NOMES não encontrado em scripts/equipe/equipe.py")
        self.assertEqual("OpenCode", nomes.get("opencode"))
        self.assertNotIn("goose", nomes)


if __name__ == "__main__":
    unittest.main()
