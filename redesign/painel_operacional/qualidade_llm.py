#!/usr/bin/env python3
"""Indicadores de qualidade de LLM do Agata: só leitura, sem rede, sem modelo.

Cada indicador diz o que mediu e como; o que ainda não tem medição sai como `unknown`
("não medido"), nunca como número inventado. Fonte do mapa: skill agata-llm-fundamentos.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ".agents/skills"
LIMITE_NOME, LIMITE_DESC, LIMITE_LINHAS = 64, 1024, 500
RESERVADAS = ("anthropic", "claude")
ORCAMENTO_HIDRATACAO = 25_000
FAMILIAS_FALHAS = ("FAB", "MED", "IDF", "ART", "CIT", "SIN", "INT")
NAO_MEDIDOS = (
    ("cache_prompt", "Cache de prompt (acerto e custo)", "nenhum uso de cache encontrado na busca de 03/11/2026"),
    ("esforco", "Esforço de raciocínio por tarefa", "sem tabela por tipo de tarefa"),
)


def frontmatter(texto: str) -> tuple[dict, int]:
    """(campos, linhas do corpo). Aceita `chave: valor` e blocos `>-` ou `|`."""
    linhas = texto.splitlines()
    if not linhas or linhas[0].strip() != "---":
        return {}, len(linhas)
    campos, chave, fim = {}, None, None
    for i, linha in enumerate(linhas[1:], 1):
        if linha.strip() == "---":
            fim = i
            break
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", linha)
        if m and not linha.startswith(" "):
            chave, valor = m.group(1), m.group(2).strip()
            campos[chave] = "" if valor in (">", ">-", "|", "|-") else valor.strip("\"'")
        elif chave and linha.startswith(" "):
            campos[chave] = (campos[chave] + " " + linha.strip()).strip()
    return campos, len(linhas) - (fim + 1 if fim else 0)


def _caminhos(corpo: str) -> list[str]:
    achados = re.findall(r"`([^`\s]+)`", corpo)
    return [c for c in achados if "/" in c and not re.search(r"[<>*{}$:~]|^https?|^\.\.", c) and re.search(r"\.\w+$|/$", c)]


def lint_skills(raiz: Path = ROOT) -> list[dict]:
    resultado = []
    for pasta in sorted((raiz / SKILLS).glob("*/")):
        arq = pasta / "SKILL.md"
        if not arq.exists():
            continue
        campos, linhas = frontmatter(arq.read_text(encoding="utf-8", errors="replace"))
        nome, desc = campos.get("name", ""), campos.get("description", "")
        problemas, avisos = [], []
        if nome != pasta.name:
            problemas.append("name difere do nome da pasta")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", nome) or len(nome) > LIMITE_NOME:
            problemas.append(f"name inválido ou acima de {LIMITE_NOME} caracteres")
        if any(r in nome for r in RESERVADAS):
            problemas.append("name usa palavra reservada")
        if not desc:
            problemas.append("description vazia")
        if len(desc) > LIMITE_DESC:
            problemas.append(f"description acima de {LIMITE_DESC} caracteres")
        if re.search(r"</?[a-z]+>", desc):
            problemas.append("description com tag XML")
        if linhas > LIMITE_LINHAS:
            avisos.append(f"{linhas} linhas, acima da recomendação de {LIMITE_LINHAS}")
        if pasta.name.startswith("agata-"):
            corpo = arq.read_text(encoding="utf-8", errors="replace")
            faltam = [c for c in _caminhos(corpo) if not (raiz / c).exists() and not (pasta / c).exists()]
            if faltam:
                avisos.append("caminho citado inexistente: " + ", ".join(faltam[:3]) + ("…" if len(faltam) > 3 else ""))
        resultado.append({"skill": pasta.name, "linhas": linhas, "name_chars": len(nome), "desc_chars": len(desc),
                          "problemas": problemas, "avisos": avisos})
    return resultado


def golden(raiz: Path = ROOT) -> dict | None:
    arq = raiz / "extras" / "seth-golden" / "casos.jsonl"
    try:
        casos = [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines() if l.strip()]
    except (OSError, ValueError):
        return None
    return {"total": len(casos), "com_abstencao": sum(1 for c in casos if c.get("aceita_abstencao"))}


def falhas(raiz: Path = ROOT) -> dict | None:
    try:
        texto = (raiz / "FALHAS.md").read_text(encoding="utf-8")
    except OSError:
        return None
    return {f: len(re.findall(rf"^\| {f}-\d+ ", texto, flags=re.M)) for f in FAMILIAS_FALHAS}


def hidratacao(raiz: Path = ROOT) -> dict | None:
    try:
        quente = len((raiz / "MEMÓRIAS.md").read_text(encoding="utf-8"))
    except OSError:
        return None
    arq = raiz / ".hidrata.md"
    return {"memorias_chars": quente, "orcamento": ORCAMENTO_HIDRATACAO,
            "hidrata_bytes": arq.stat().st_size if arq.exists() else None}


def _ind(id_, titulo, estado, valor, evidencia, fonte):
    return {"id": id_, "titulo": titulo, "estado": estado, "valor": valor, "evidencia": evidencia, "fonte": fonte}


def _medicoes() -> list[dict]:
    """Indicadores que dependem de medição pesada salva pelo painel; sem arquivo, saem como não medidos."""
    pasta = Path(os.environ.get("AGATA_MEDICOES_DIR", Path.home() / ".cache" / "agata" / "painel" / "medicoes"))
    def ler(arq):
        try:
            return json.loads(arq.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
    rec = ler(pasta / "recuperacao.json")
    if rec and isinstance(rec.get("recall"), dict):
        r5 = rec["recall"].get("5", 0)
        a = _ind("recall_busca", "Recuperação: recall@k da busca por texto", "ok" if r5 >= 0.9 else "warning",
                 f"recall@1 {rec['recall'].get('1', 0):.0%} · @5 {r5:.0%} · MRR {rec.get('mrr', 0):.2f} (n={rec.get('n', '?')})",
                 f"Medido em {rec.get('medido_em', '?')} só para busca léxica por conteúdo; paráfrase e busca semântica: não medido.",
                 "scripts/medir_recuperacao.py")
    else:
        a = _ind("recall_busca", "Recuperação: recall@k da busca por texto", "unknown", "não medido",
                 "rode a medição na aba Qualidade de LLM (leitura do vault; sem modelo)", "scripts/medir_recuperacao.py")
    modelos = [d for d in (ler(x) for x in sorted(pasta.glob("contexto-*.json"))) if d and "linhas" in d]
    if modelos:
        partes = [f"{d.get('modelo', '?')}: " + (f"≥{d['efetivo_tokens']} tokens" if d.get("efetivo_tokens") else "abaixo do menor comprimento") for d in modelos]
        pior = min((d.get("efetivo_tokens") or 0) for d in modelos)
        b = _ind("contexto_efetivo", "Comprimento efetivo de contexto dos modelos locais", "warning" if pior < 16384 else "ok",
                 " · ".join(partes), "Teste de agulha em 3 profundidades; mede só recuperação simples, não o RULER completo.",
                 "scripts/medir_contexto_efetivo.py")
    else:
        b = _ind("contexto_efetivo", "Comprimento efetivo de contexto dos modelos locais", "unknown", "não medido",
                 "escolha um modelo local na aba Qualidade de LLM e rode a medição (gasta GPU e minutos)", "scripts/medir_contexto_efetivo.py")
    return [a, b]


def indicadores(raiz: Path = ROOT) -> list[dict]:
    saida = []
    skills = lint_skills(raiz)
    com_problema = [s for s in skills if s["problemas"]]
    com_aviso = [s for s in skills if s["avisos"]]
    saida.append(_ind("skills", "Skills dentro dos limites oficiais",
                      "warning" if com_problema or com_aviso else "ok",
                      f"{len(skills) - len(com_problema)}/{len(skills)} sem problema; {len(com_aviso)} com aviso",
                      "; ".join(f"{s['skill']}: " + ", ".join(s["problemas"] + s["avisos"]) for s in com_problema + [x for x in com_aviso if x not in com_problema][:6]) or "nenhum desvio",
                      ".agents/skills/*/SKILL.md; limites: name 64, description 1024, corpo 500 linhas"))
    g = golden(raiz)
    saida.append(_ind("golden", "Conjunto de ouro da Seth e abstenção",
                      "unknown" if g is None else ("warning" if g["com_abstencao"] < max(1, g["total"] // 3) else "ok"),
                      "sem leitura" if g is None else f"{g['total']} casos; {g['com_abstencao']} aceitam abstenção",
                      "Abstenção calibrada premiada é a mitigação do paper de 2025 (arXiv 2509.04664); falta pontuação graduada.",
                      "extras/seth-golden/casos.jsonl"))
    f = falhas(raiz)
    saida.append(_ind("falhas", "Catálogo de falhas por causa raiz",
                      "unknown" if f is None else "ok",
                      "sem leitura" if f is None else ", ".join(f"{k} {v}" for k, v in f.items()),
                      "Entradas do catálogo por família; uma falha nova entra como linha de tabela.", "FALHAS.md"))
    h = hidratacao(raiz)
    saida.append(_ind("hidratacao", "Memória quente contra o orçamento de hidratação",
                      "unknown" if h is None else ("warning" if h["memorias_chars"] > h["orcamento"] else "ok"),
                      "sem leitura" if h is None else f"{h['memorias_chars']} caracteres; orçamento {h['orcamento']}",
                      "Contexto longo degrada (Chroma 2025; RULER 2024); P-24 avisa e a escalada para FALHA ainda não existe.",
                      "MEMÓRIAS.md; scripts/gerar_mapa_projeto.py (LIMITE_CHARS)"))
    saida += _medicoes()
    for id_, titulo, motivo in NAO_MEDIDOS:
        saida.append(_ind(id_, titulo, "unknown", "não medido", motivo, "mapa.md da skill agata-llm-fundamentos"))
    return saida


def snapshot(raiz: Path = ROOT) -> dict:
    return {"schema_version": 1, "state": "ok", "items": indicadores(raiz), "skills": lint_skills(raiz)}


def _selftest() -> int:
    import tempfile
    os.environ["AGATA_MEDICOES_DIR"] = tempfile.mkdtemp()
    falhou = 0
    def conferir(nome, cond):
        nonlocal falhou
        print(("PASS " if cond else "FALHA ") + nome); falhou += 0 if cond else 1
    with tempfile.TemporaryDirectory() as t:
        r = Path(t)
        (r / SKILLS / "agata-boa").mkdir(parents=True); (r / SKILLS / "ruim").mkdir(parents=True)
        (r / "ref.md").write_text("x", encoding="utf-8")
        (r / SKILLS / "agata-boa" / "SKILL.md").write_text(
            "---\nname: agata-boa\ndescription: >-\n  Faz algo.\n  Use quando preciso.\n---\ncorpo `ref.md` e `nao/existe.md`\n", encoding="utf-8")
        (r / SKILLS / "ruim" / "SKILL.md").write_text(
            "---\nname: claude-ruim\ndescription: <b>x</b>\n---\n" + "l\n" * 600, encoding="utf-8")
        res = {s["skill"]: s for s in lint_skills(r)}
        conferir("bloco >- vira description única", res["agata-boa"]["desc_chars"] == len("Faz algo. Use quando preciso."))
        conferir("caminho inexistente vira aviso, existente não", any("nao/existe.md" in a for a in res["agata-boa"]["avisos"]) and not any("ref.md" in a for a in res["agata-boa"]["avisos"]))
        conferir("skill ruim: nome reservado, nome≠pasta e tag XML", len(res["ruim"]["problemas"]) >= 3)
        conferir("corpo acima de 500 linhas é aviso", any("acima da recomendação" in a for a in res["ruim"]["avisos"]))
        (r / "extras" / "seth-golden").mkdir(parents=True)
        (r / "extras" / "seth-golden" / "casos.jsonl").write_text('{"id":1}\n{"id":2,"aceita_abstencao":true}\n', encoding="utf-8")
        (r / "FALHAS.md").write_text("| FAB-1 | a |\n| FAB-2 | b |\n| SIN-1 | c |\n", encoding="utf-8")
        (r / "MEMÓRIAS.md").write_text("x" * 30_000, encoding="utf-8")
        ind = {i["id"]: i for i in indicadores(r)}
        conferir("golden conta casos e abstenções", ind["golden"]["valor"].startswith("2 casos; 1 aceitam"))
        conferir("falhas contam por família", "FAB 2" in ind["falhas"]["valor"] and "SIN 1" in ind["falhas"]["valor"])
        conferir("memória acima do orçamento é warning", ind["hidratacao"]["estado"] == "warning")
        conferir("o que não tem medição sai unknown", all(ind[k]["estado"] == "unknown" and ind[k]["valor"] == "não medido" for k in ("recall_busca", "contexto_efetivo", "cache_prompt", "esforco")))
        conferir("repositório vazio não quebra", indicadores(Path(t) / "vazio") is not None)
    return 1 if falhou else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
