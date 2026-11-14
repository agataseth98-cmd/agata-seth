"""C1, C2 e C6: a entrada universal aponta para o guia, o índice lista as skills e os caminhos citados existem.

Roda em checkout limpo (CI): não lê arquivo fora do repositório e não depende de arquivo local não versionado.
"""
import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
AGENTS = RAIZ / "AGENTS.md"
FLUXO = RAIZ / ".agents/skills/agata-fluxo/SKILL.md"
INDICE = RAIZ / ".agents/skills/INDICE.md"
PONTEIRO = ".agents/skills/agata-fluxo/SKILL.md"


def pastas_com_skill():
    """Nomes das pastas de .agents/skills que têm SKILL.md. Lê o disco, sem git: vale também num export.
    As cópias de terceiros que não estão no git aparecem na seção "Skills de terceiros" do índice."""
    return sorted(p.parent.name for p in (RAIZ / ".agents/skills").glob("*/SKILL.md"))


def secao_terceiros(texto):
    m = re.search(r"^## Skills de terceiros.*$", texto, re.M)
    if not m:
        return ""
    resto = texto[m.end():]
    prox = re.search(r"^## ", resto, re.M)
    return resto[: prox.start()] if prox else resto


def caminhos_citados(texto):
    """Mesma régua de qualquer skill: token entre crases, sem espaço, com barra, com extensão ou barra final.
    Caminho absoluto, URL, placeholder (<nome>, *, {}, $, ~, :) e '..' ficam fora."""
    texto = re.sub(r"```.*?```", "", texto, flags=re.S)
    achados = re.findall(r"`([^`\s]+)`", texto)
    return sorted({c for c in achados
                   if "/" in c and not re.search(r"[<>*{}$:~]|^https?|^\.\.|^/", c)
                   and re.search(r"\.\w+$|/$", c)})


class EntradaUniversalTests(unittest.TestCase):
    def test_agents_aponta_para_o_fluxo_universal(self):
        # C1: AGENTS.md cita o guia e o caminho existe.
        linhas = [l for l in AGENTS.read_text(encoding="utf-8").splitlines() if PONTEIRO in l]
        self.assertTrue(linhas, f"AGENTS.md não cita {PONTEIRO}")
        self.assertTrue((RAIZ / PONTEIRO).is_file(), f"o caminho {PONTEIRO} não existe")

    def test_indice_lista_toda_pasta_de_skill(self):
        # C2: uma linha de tabela para cada pasta com SKILL.md (cópias de terceiros ficam na seção própria).
        pastas = pastas_com_skill()
        self.assertGreater(len(pastas), 0, "nenhuma pasta com SKILL.md em .agents/skills")
        texto = INDICE.read_text(encoding="utf-8")
        faltam = [p for p in pastas
                  if not re.search(rf"^\| `{re.escape(p)}`", texto, re.M)
                  and f"`{p}`" not in secao_terceiros(texto)]
        self.assertFalse(faltam, f"INDICE.md sem linha para: {faltam}")

    def test_caminhos_citados_existem(self):
        # C6: caminhos relativos do guia, da linha do AGENTS.md e do índice existem.
        linha_agents = [l for l in AGENTS.read_text(encoding="utf-8").splitlines() if PONTEIRO in l]
        fontes = [
            ("guia", FLUXO.read_text(encoding="utf-8")),
            ("AGENTS.md (linha do ponteiro)", "\n".join(linha_agents)),
            ("INDICE.md", INDICE.read_text(encoding="utf-8")),
        ]
        faltam = []
        for nome, texto in fontes:
            for c in caminhos_citados(texto):
                if not (RAIZ / c).exists():
                    faltam.append(f"{nome}: {c}")
        self.assertFalse(faltam, "caminhos citados que não existem: " + "; ".join(faltam))


if __name__ == "__main__":
    unittest.main()
