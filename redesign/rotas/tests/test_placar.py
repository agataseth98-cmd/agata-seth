import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import placar  # noqa: E402


def resp(modelo, tipo, n, s=2.0, ok=True, item="x"):
    return [{"modelo": modelo, "tipo": tipo, "item": item if item.endswith("_mcp_canon") else f"{item}{i}", "estado": "ok" if ok else "erro", "s": s + i,
             "texto": "resposta", "chamadas": [], "checagens": {}} for i in range(n)]


def resumo(modelo, data="2026-11-18", proto="benchmark-roteamento-v1 corpus-sha256:abc"):
    return {modelo: {"feitas": 1, "ok": 1, "medido": [
        {"protocolo": proto, "metrica": "taxa_erro", "valor": 0.0, "amostra": 1, "data": data}]}}


class PlacarTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def run_dir(self, nome, modelos, proto=None):
        d = self.tmp / "fonte" / nome
        d.mkdir(parents=True)
        res, linhas = {}, []
        for m, tipo, n, kw in modelos:
            res.update(resumo(m, **({"proto": proto} if proto else {})))
            linhas += resp(m, tipo, n, **kw)
        (d / "resumo.json").write_text(json.dumps(res))
        (d / "respostas.jsonl").write_text("\n".join(json.dumps(l) for l in linhas))
        return self.tmp / "fonte"

    def gerar(self, fonte, decisoes=None, tarifas=None):
        dec = self.tmp / "dec.jsonl"
        dec.write_text("\n".join(json.dumps(d) for d in (decisoes or [])))
        return placar.gerar([fonte], self.tmp / "out" / "placar.json", dec, tarifas or {})

    def test_agrega_por_modelo_e_tipo_com_n_p50_p95(self):
        f = self.run_dir("a", [("ollama-local/m", "codigo", 10, {}), ("ollama-local/m", "contexto_longo", 6, {})])
        doc = self.gerar(f)
        t = doc["modelos"]["ollama-local/m"]["tipos"]
        self.assertEqual(set(t), {"codigo", "contexto"})
        self.assertEqual(t["codigo"]["n"], 10)
        self.assertEqual(t["codigo"]["nota"], 1.0)
        self.assertEqual(t["codigo"]["p50"], 6.0)
        self.assertEqual(t["codigo"]["p95"], 11.0)

    def test_arquivo_0600(self):
        self.gerar(self.run_dir("a", [("ollama-local/m", "json", 6, {})]))
        modo = (self.tmp / "out" / "placar.json").stat().st_mode & 0o777
        self.assertEqual(modo, 0o600)

    def test_nota_usa_porta_entrada_resposta_vazia_reprova(self):
        f = self.run_dir("a", [("ollama-local/m", "conversa", 6, {})])
        arq = f / "a" / "respostas.jsonl"
        linhas = [json.loads(l) for l in arq.read_text().splitlines()]
        for l in linhas[:3]:
            l["texto"] = ""
        arq.write_text("\n".join(json.dumps(l) for l in linhas))
        self.assertEqual(self.gerar(f)["modelos"]["ollama-local/m"]["tipos"]["conversa"]["nota"], 0.5)

    def test_confianca_e_classe_pessoal_so_local(self):
        f = self.run_dir("a", [("ollama-local/l", "json", 6, {}), ("nvidia/x/y", "json", 6, {})])
        doc = self.gerar(f)
        self.assertEqual(doc["modelos"]["nvidia/x/y"]["confianca"], "gratuito")
        self.assertEqual([x["modelo"] for x in placar.melhores(doc, "json", "pessoal")], ["ollama-local/l"])
        self.assertEqual(len(placar.melhores(doc, "json", "publico")), 2)

    def test_segredo_nenhum(self):
        doc = self.gerar(self.run_dir("a", [("ollama-local/l", "json", 6, {})]))
        self.assertEqual(placar.melhores(doc, "json", "segredo"), [])

    def test_standby_tira_e_ultima_decisao_vence(self):
        f = self.run_dir("a", [("nvidia/x/y", "json", 6, {}), ("nvidia/x/z", "json", 6, {})])
        dec = [{"quando": "2026-11-19T08:00:00", "id": "nvidia/x/y", "para": "liberado"},
               {"quando": "2026-11-19T09:00:00", "id": "nvidia/x/y", "para": "standby"}]
        doc = self.gerar(f, dec)
        self.assertEqual([x["modelo"] for x in placar.melhores(doc, "json", "publico")], ["nvidia/x/z"])
        dec.append({"quando": "2026-11-19T10:00:00", "id": "nvidia/x/y", "para": "liberado"})
        doc = self.gerar(f, dec)
        self.assertEqual(len(placar.melhores(doc, "json", "publico")), 2)

    def test_amostra_pequena_aviso_peso_menor_mas_nao_descartada(self):
        f = self.run_dir("a", [("ollama-local/p", "json", 2, {}), ("ollama-local/g", "json", 10, {})])
        doc = self.gerar(f)
        r = doc["modelos"]["ollama-local/p"]["tipos"]["json"]
        self.assertLess(r["peso"], 1)
        self.assertTrue(any("amostra pequena" in a for a in r["avisos"]))
        lista = placar.melhores(doc, "json", "publico")
        self.assertEqual([x["modelo"] for x in lista], ["ollama-local/g", "ollama-local/p"])

    def test_melhor_em_um_tipo_nunca_some(self):
        f = self.run_dir("a", [("ollama-local/a", "codigo", 1, {}), ("ollama-local/b", "conversa", 6, {})])
        doc = self.gerar(f)
        self.assertEqual([x["modelo"] for x in placar.melhores(doc, "codigo", "publico")], ["ollama-local/a"])

    def test_mais_recente_vence_e_prompt_real(self):
        d1 = self.run_dir("a", [("ollama-local/m", "json", 6, {"ok": False})])
        d2 = self.tmp / "fonte" / "b"
        d2.mkdir()
        (d2 / "resumo.json").write_text(json.dumps(resumo("ollama-local/m", "2026-11-19")))
        (d2 / "respostas.jsonl").write_text("\n".join(json.dumps(l) for l in resp("ollama-local/m", "json", 6, item="j_mcp_canon")))
        r = self.gerar(d1)["modelos"]["ollama-local/m"]["tipos"]["json"]
        self.assertEqual((r["nota"], r["prompt"], r["data"], r["execucoes"]), (1.0, "prompt_real", "2026-11-19", 2))

    def test_custo_pago_por_tarifa(self):
        f = self.run_dir("a", [("claude/haiku", "json", 6, {})])
        tar = {"claude": {"confianca": "pago_sem_treino", "tarifa": {"entrada_usd_mtok": 1, "saida_usd_mtok": 5}}}
        ent = self.gerar(f, tarifas=tar)["modelos"]["claude/haiku"]
        self.assertEqual((ent["confianca"], ent["custo"]["tipo"]), ("pago_sem_treino", "pago"))

    def test_fonte_ausente_e_resumo_quebrado_viram_aviso(self):
        f = self.run_dir("a", [("ollama-local/m", "json", 6, {})])
        (f / "a" / "resumo-x.json").write_text("{nao json")
        dec = self.tmp / "dec.jsonl"
        dec.write_text("")
        doc = placar.gerar([f, self.tmp / "nada"], self.tmp / "o.json", dec, {})
        self.assertEqual(len(doc["avisos"]), 2)
        self.assertIn("ollama-local/m", doc["modelos"])

    def test_cli_gerar_e_melhores(self):
        f = self.run_dir("a", [("ollama-local/m", "json", 6, {})])
        out = self.tmp / "p.json"
        dec = self.tmp / "d.jsonl"
        dec.write_text("")
        self.assertEqual(placar.main(["gerar", "--fontes", str(f), "--saida", str(out), "--decisoes", str(dec)]), 0)
        self.assertEqual(placar.main(["melhores", "--tipo", "json", "--classe", "pessoal", "--placar", str(out)]), 0)
        self.assertEqual(placar.main(["melhores", "--tipo", "zzz", "--classe", "pessoal", "--placar", str(out)]), 2)


if __name__ == "__main__":
    unittest.main()
