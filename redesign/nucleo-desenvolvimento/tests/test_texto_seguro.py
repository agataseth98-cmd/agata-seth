"""C7: nas linhas acrescentadas por este lote, nenhum valor de segredo e nenhum caminho de memória restrita.

Régua de segredo: redesign/router/sanitizar.py, função varrer. O escopo são as linhas que este lote acrescenta
(regiões abaixo), não o arquivo inteiro: o resto de AGENTS.md já tinha texto antes deste lote.

Caminho de memória restrita: a lista NÃO é escrita neste repositório (regra do sistema: não se cita esse tipo de
caminho). Ela vem da variável AGATA_CAMINHOS_RESTRITOS, separada por vírgula, configurada por quem roda o teste.
Sem a variável, a parte de caminho restrito fica como pendência (skip com motivo), e a parte de segredo continua.
"""
import os
import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "redesign" / "router"))


def caminhos_restritos():
    return [c.strip() for c in os.environ.get("AGATA_CAMINHOS_RESTRITOS", "").split(",") if c.strip()]


def regioes_acrescentadas():
    """Trechos que este lote acrescenta, lidos dos arquivos. Falha clara se a região sumir."""
    agents = (RAIZ / "AGENTS.md").read_text(encoding="utf-8").splitlines()
    indice = (RAIZ / ".agents/skills/INDICE.md").read_text(encoding="utf-8").splitlines()
    gw = (RAIZ / "redesign/router/seth_gateway.py").read_text(encoding="utf-8")
    fluxo = (RAIZ / ".agents/skills/agata-fluxo/SKILL.md").read_text(encoding="utf-8")
    ponteiro = [l for l in agents if "agata-fluxo/SKILL.md" in l]
    linhas_indice = [l for l in indice if re.search(
        r"agata-fluxo`|agata-processo-lote|agata-time-inovacao|agata-disciplina|agata-engenharia-reversa|elephant-goldfish-sdd", l)]
    m_gw = re.search(r"# \(07/11/2026, núcleo de desenvolvimento, D2\) ponteiro de uma linha.*?(?=\ndef _hidratacao)",
                     gw, re.S)
    m_inj = re.search(r"# \(07/11/2026, núcleo de desenvolvimento, D2\) ponteiro PROCESSO.*?\+ _proc\n", gw, re.S)
    faltam = [n for n, ok in (("ponteiro do AGENTS.md", ponteiro), ("linhas do índice", linhas_indice),
                              ("bloco do gateway", m_gw), ("injeção do gateway", m_inj)) if not ok]
    if faltam:
        raise AssertionError(f"região acrescentada não encontrada: {faltam}")
    return {
        "AGENTS.md (ponteiro)": "\n".join(ponteiro),
        "INDICE.md (linhas novas e do agata-fluxo)": "\n".join(linhas_indice),
        "guia agata-fluxo (inteiro)": fluxo,
        "seth_gateway.py (ponteiro)": m_gw.group(0) + "\n" + m_inj.group(0),
    }


class TextoSeguroTests(unittest.TestCase):
    def test_linhas_novas_sem_segredo_nem_memoria_restrita(self):
        from sanitizar import varrer  # régua oficial de segredo (P-1)

        regioes = regioes_acrescentadas()
        achados = {}
        for nome, texto in regioes.items():
            seg = varrer(texto)
            if seg:
                achados[nome] = [(a["padrao_rotulo"], a["trecho_redigido"]) for a in seg]
        self.assertFalse(achados, f"linhas acrescentadas com valor de segredo: {achados}")

        restritos = caminhos_restritos()
        if not restritos:
            self.skipTest("pendência: caminhos restritos não configurados (AGATA_CAMINHOS_RESTRITOS); "
                          "a parte de segredo passou")
        for nome, texto in regioes.items():
            citados = [c for c in restritos if c in texto]
            self.assertFalse(citados, f"{nome} cita caminho restrito: {citados}")


if __name__ == "__main__":
    unittest.main()
