#!/usr/bin/env python3
"""Alexandria — índice de skills separado do índice de documentos, e seleção léxica.

Skill é procedimento; documento é conteúdo (Experimento GPT, Alexandria §8–§9, (063)–(065)).
Por isso as skills têm tabela e FTS próprios. Junta os três índices que hoje estão
desconexos, sem alterar nenhum deles:
- `.agents/skills/*/SKILL.md` (próprias; dono em `.agents/skills/INDICE.md`);
- `.claude/skills/*/SKILL.md` (terceiros instaladas);
- `ferramentas/indice.json` (catálogo de fontes externas, com a quarentena de
  `ferramentas/ferramentas.py`: peça em quarentena é listada, nunca sugerida).

Seleção: menção explícita do nome tem prioridade; depois busca léxica por nome e
descrição. Registra `disponivel`/`selecionada` e o sha256 do SKILL.md. NÃO lê o corpo
para executar, NÃO carrega, NÃO instala: escolher não é executar (invariante do briefing).
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
sys.path.insert(0, str(REPO / "ferramentas"))
sys.path.insert(0, str(REPO / "scripts"))
import busca_texto  # noqa: E402

try:
    from ferramentas import QUARENTENA  # noqa: E402
except Exception:  # noqa: BLE001 — sem o catálogo, nada fica fora da quarentena por engano
    QUARENTENA = re.compile(r".*")


def _frontmatter(p: Path) -> dict:
    try:
        texto = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    if not texto.startswith("---"):
        return {}
    fm = {}
    for ln in texto.split("---", 2)[1].splitlines():
        if ":" in ln and not ln.startswith(" "):
            k, v = ln.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm


def _sha(p: Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def varrer(raiz: Path) -> list[dict]:
    out, vistos = [], set()
    for origem, base in (("propria", raiz / ".agents" / "skills"), ("terceiro", raiz / ".claude" / "skills")):
        for p in sorted(base.glob("*/SKILL.md")) if base.exists() else []:
            fm = _frontmatter(p)
            nome = fm.get("name") or p.parent.name
            rel = p.relative_to(raiz).as_posix()
            if (nome, origem) in vistos:
                continue
            vistos.add((nome, origem))
            out.append({"skill_id": f"skill:{origem}:{nome}", "nome": nome, "origem": origem, "caminho": rel,
                        "descricao": fm.get("description", ""), "sha256": _sha(p), "estado": "disponivel",
                        "quarentena": 0})
    try:
        catalogo = json.loads((raiz / "ferramentas" / "indice.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        catalogo = []
    for item in catalogo if isinstance(catalogo, list) else []:
        nome = str(item.get("nome", ""))
        if not nome or item.get("tipo") != "skill" or any(nome == s["nome"] for s in out if s["origem"] == "propria"):
            continue
        q = 1 if QUARENTENA.match(nome) else 0
        out.append({"skill_id": f"skill:{item.get('fonte', 'catalogo')}:{nome}", "nome": nome,
                    "origem": f"catalogo:{item.get('fonte', '?')}", "caminho": item.get("caminho", ""),
                    "descricao": item.get("resumo", ""), "sha256": _sha(raiz / item.get("caminho", "")) if item.get("caminho") else None,
                    "estado": "quarentena" if q else "disponivel", "quarentena": q})
    return out


def popular(con: sqlite3.Connection, raiz: Path) -> int:
    lista = varrer(Path(raiz))
    for s in lista:
        cur = con.execute("INSERT OR IGNORE INTO skills (skill_id, nome, origem, caminho, descricao, sha256, estado,"
                          " quarentena) VALUES (?,?,?,?,?,?,?,?)",
                          (s["skill_id"], s["nome"], s["origem"], s["caminho"], s["descricao"], s["sha256"],
                           s["estado"], s["quarentena"]))
        if cur.rowcount == 0:
            continue
        con.execute("INSERT INTO skills_fts(rowid, nome, descricao) VALUES (?,?,?)",
                    (cur.lastrowid, s["nome"].replace("-", " "), s["descricao"]))
    return con.execute("SELECT count(*) FROM skills").fetchone()[0]


def selecionar(consulta: str, n: int = 3, con: sqlite3.Connection | None = None) -> dict:
    # lote 5 (C5): skill revogada pelo ciclo nunca é sugerida (o histórico continua no ciclo)
    sys.path.insert(0, str(AQUI))
    import ciclo_skills  # noqa: E402
    proibidas = ciclo_skills.revogadas()
    sys.path.insert(0, str(AQUI))
    import acervo  # noqa: E402
    proprio = con is None
    con = con or acervo._con()
    con.row_factory = sqlite3.Row
    try:
        norm = busca_texto._norm(consulta)
        candidatos, vistos = [], set()
        # 1) menção explícita do nome, entre as permitidas (fora da quarentena)
        for row in con.execute("SELECT * FROM skills WHERE quarentena = 0"):
            if re.search(r"(?<![\w-])" + re.escape(row["nome"].lower()) + r"(?![\w-])", norm):
                candidatos.append({**dict(row), "motivo": "mencao_explicita"}); vistos.add(row["skill_id"])
        # 2) léxico por nome e descrição
        ps = busca_texto.palavras(consulta)
        if ps and len(candidatos) < n:
            q = " OR ".join('"' + p + '"*' for p in ps)
            for row in con.execute("SELECT s.*, bm25(skills_fts) AS r FROM skills_fts JOIN skills s ON s.rowid = skills_fts.rowid"
                                   " WHERE skills_fts MATCH ? AND s.quarentena = 0 ORDER BY r LIMIT ?", (q, n * 3)):
                if row["skill_id"] not in vistos:
                    vistos.add(row["skill_id"]); d = dict(row); d.pop("r", None)
                    candidatos.append({**d, "motivo": "lexico"})
                if len(candidatos) >= n:
                    break
    finally:
        if proprio:
            con.close()
    for c in candidatos:
        c["estado"] = "selecionada"   # sugestão: ninguém leu nem aplicou
        c["aplicada"] = False
    return {"schema_version": 1, "candidatos": [c for c in candidatos if c["nome"] not in proibidas][:n],
            "nota": "seleção consultiva: o executor ainda precisa ler o SKILL.md inteiro; nada foi executado"}


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "selecionar":
        print(json.dumps(selecionar(sys.argv[2]), ensure_ascii=False, indent=1))
        sys.exit(0)
    print(__doc__)
    sys.exit(2)


def bloco_skills(consulta: str, *, n: int = 3, teto: int = 500) -> str | None:
    """(lote 5, A2) Sugestão de skills para a hidratação: nome e descrição curta. Nada é carregado.
    Descrição com instrução embutida é omitida (guarda.nota). Revogadas nunca entram (selecionar já filtra)."""
    try:
        cands = selecionar(consulta, n=n)["candidatos"]
    except FileNotFoundError:
        return None
    if not cands:
        return None
    sys.path.insert(0, str(AQUI.parent / "metacognicao"))
    import guarda  # noqa: E402
    linhas = ["SKILLS-SUGERIDAS (sugestão: nada foi carregado; leia o SKILL.md inteiro antes de aplicar):"]
    for c in cands:
        desc = " ".join((c.get("descricao") or "").split())[:90]
        if guarda.nota(desc):
            continue
        linhas.append(f"- {c['nome']}: {desc}")
    if len(linhas) == 1:
        return None
    return "\n".join(linhas)[:teto]
