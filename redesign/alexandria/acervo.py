#!/usr/bin/env python3
"""Alexandria — acervo, índice léxico e consulta com pacote de evidência (piloto em sombra).

Especificação: `redesign/alexandria/spec/spec.md` (origem: Experimento GPT, proposta
Alexandria §4–§7, decisão do Humano (077) e decisões de 04/11/2026).

O que faz:
- `iniciar`: cria a estrutura de pastas de trabalho em `<dados>/alexandria/` (fluxo
  editorial, skills, contextos) — fora do repo, 0700.
- `snapshot <commit>`: cópia fixa do repositório naquele commit (`git archive`), que é
  o acervo do piloto (decisão 1: só o que já está no repo).
- `indexar`: índice DERIVADO e reconstruível em SQLite/FTS5 (`<cache>/indice.sqlite3`).
  Cada objeto tem `object_id`, caminho, commit, sha256, classificação de acesso, estado
  editorial e verificação — dimensões separadas. Entradas `(N)` viram objetos próprios e
  suas citações `(M)` viram relações. Reindexar compara hashes e registra no ledger os
  objetos que mudaram: contextos que os citam ficam pendentes de revisão.
- `consultar "frase"`: filtra acesso, busca léxica (FTS5, sem acento), segue relações e,
  só quando pedido ou quando o léxico achou pouco, chama a busca semântica SECUNDÁRIA
  (`scripts/busca_semantica.py --json`, (327)), sempre rotulada. Devolve pacote de
  evidência com objeto, trecho, linha, commit e sha. Nunca chama LLM. Sem resultado:
  "não encontrado nesta busca" — nunca "não existe".

Não é camada primária vetorial ((115)); não grava no canon; não lê ~/.config/agata/.env.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
sys.path.insert(0, str(REPO / "redesign" / "nova_versao"))
sys.path.insert(0, str(REPO / "scripts"))
import eventos  # noqa: E402
import busca_texto  # noqa: E402  (mesma normalização da busca por texto, (682)/(716))

ESTRUTURA = {
    "alexandria/acervo/recebido": "entrada bruta, ainda sem verificação",
    "alexandria/acervo/quarentena": "parser isolado; nada aqui é executado nem vira instrução",
    "alexandria/acervo/catalogado": "origem, direitos e hash registrados",
    "alexandria/acervo/revisado": "conferido; elegível para consulta",
    "alexandria/acervo/contestado": "preservado, mas com afirmação contestada",
    "alexandria/acervo/restrito": "acesso limitado por silo ou sensibilidade",
    "alexandria/acervo/arquivado": "fora de circulação, história preservada",
    "alexandria/acervo/rejeitado": "não entra; motivo no ledger",
    "alexandria/acervo/snapshots": "cópia fixa do repo por commit (acervo do piloto)",
    "alexandria/skills/rascunho": "skill candidata, sem revisão",
    "alexandria/skills/quarentena": "em revisão de fontes",
    "alexandria/skills/em-teste": "testes reservados",
    "alexandria/skills/elegivel": "elegível para experimento (NÃO instalada; instalar segue P-8)",
    "alexandria/skills/revogada": "versão retirada; uso futuro impedido, registro preservado",
    "alexandria/contextos": "pacotes de evidência entregues a modelos",
    "metacognicao": "sombra do antes/depois do turno, sem o texto do pedido",
    "corpo": "fotografias e saúde datadas da Máquina",
    "redundancia/testes": "testes por rota e capacidade (lote 2)",
    "coordenacao/tarefas": "task_id, versão de contexto e estado (lote 2)",
    "avaliacao/dev": "casos de desenvolvimento (lote 3)",
    "avaliacao/calibracao": "casos de calibração (lote 3)",
    "avaliacao/teste-reservado": "gabarito fora da visão do executor (lote 3)",
    "avaliacao/execucoes": "registro por execução (lote 3)",
    "eventos": "ledger único, encadeado por hash",
    "config": "orcamento.json (editado pelo painel)",
}

CANON = ("REGRAS.md", "PROTOCOLOS.md", "FALHAS.md", "PROJETO.md", "PROJETO_REFERENCIA.md", "MEMÓRIAS.md",
         "MEMORIAS-MORNO.md", "AGENTS.md", "PROMPT_CARREGAMENTO.md")
# INDICE_MEMORIAS*.md é derivado: não é fonte. MEMORIAS-MORNO.md é a camada morna de MEMÓRIAS (entradas
# como (670) e (692) só existem lá); faltava no lote 1 e a avaliação (lote 3) achou a lacuna.
GLOBS = ("memoria/**/*.md", "extras/**/*.md", "propostas/*.md", "redesign/*/README.md", "redesign/*/spec/spec.md")
# acesso por caminho; o que não casar é "public" (tudo aqui está no repo público)
PRIVADO = re.compile(r"(^|/)(privado|private|mod-[^/]+)/", re.I)
RE_ENTRADA = re.compile(r"^\((\d{1,4})\)\s")
RE_CITA = re.compile(r"(?<![\w(])\((\d{1,4})\)")
NAO_ENCONTRADO = "não encontrado nesta busca"
# a mesma entrada pode existir em cópia (extras/arquivo): a fonte viva vem primeiro
PRIORIDADE = "CASE origem WHEN 'canon' THEN 0 WHEN 'memoria' THEN 1 ELSE 2 END, caminho"


def cache() -> Path:
    return Path(os.environ.get("AGATA_NV_CACHE", Path.home() / ".cache" / "agata" / "nova-versao"))


def indice_path() -> Path:
    return cache() / "indice.sqlite3"


def iniciar() -> Path:
    base = eventos.dados()
    base.mkdir(parents=True, exist_ok=True)
    os.chmod(base, 0o700)
    for rel in ESTRUTURA:
        (base / rel).mkdir(parents=True, exist_ok=True)
    linhas = ["# Nova versão do Agata — pastas de trabalho", "",
              "Gerado por `redesign/alexandria/acervo.py iniciar`. Fora do repo. Não editar à mão.", ""]
    linhas += [f"- `{rel}/` — {desc}" for rel, desc in ESTRUTURA.items()]
    (base / "LEIA-ME.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    eventos.registrar("execution", "ok", "estrutura", componente="alexandria", chave="iniciar:v1")
    return base


def snapshot(commit: str = "HEAD", repo: Path = REPO) -> Path:
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", commit + "^{commit}"],
                         capture_output=True, text=True, check=True).stdout.strip()
    destino = eventos.dados() / "alexandria" / "acervo" / "snapshots" / sha[:12]
    if (destino / ".completo").exists():
        return destino
    bruto = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", sha],
                           capture_output=True, check=True).stdout
    tmp = Path(tempfile.mkdtemp(dir=destino.parent if destino.parent.exists() else None, prefix=".snap-"))
    with tarfile.open(fileobj=io.BytesIO(bruto)) as tar:
        tar.extractall(tmp, filter="data")  # sem link absoluto, sem sair da pasta
    (tmp / ".commit").write_text(sha + "\n", encoding="utf-8")
    (tmp / ".completo").write_text("", encoding="utf-8")
    destino.parent.mkdir(parents=True, exist_ok=True)
    os.replace(tmp, destino)
    eventos.registrar("observation", "ok", f"snapshot:{sha[:12]}", componente="alexandria", chave=f"snapshot:{sha}",
                      commit=sha)
    return destino


def _fontes(raiz: Path):
    vistos = set()
    for nome in CANON:
        p = raiz / nome
        if p.is_file():
            vistos.add(p); yield p, "canon"
    for g in GLOBS:
        for p in sorted(raiz.glob(g)):
            if p.is_file() and p not in vistos and not any(x.startswith(".") for x in p.relative_to(raiz).parts):
                vistos.add(p)
                yield p, ("memoria" if g.startswith("memoria") else g.split("/")[0])


def _blocos(linhas: list[str]):
    """Parágrafos (linhas não vazias seguidas), com a linha inicial (1-based)."""
    ini, buf = None, []
    for i, ln in enumerate(linhas, 1):
        if ln.strip():
            if ini is None:
                ini = i
            buf.append(ln)
        elif buf:
            yield ini, "\n".join(buf); ini, buf = None, []
    if buf:
        yield ini, "\n".join(buf)


def _objetos(raiz: Path, commit: str):
    """Gera (objeto, [trechos]) — arquivos inteiros e, dentro deles, entradas (N)."""
    for p, origem in _fontes(raiz):
        rel = p.relative_to(raiz).as_posix()
        texto = p.read_text(encoding="utf-8", errors="replace")
        linhas = texto.splitlines()
        acesso = "private" if PRIVADO.search(rel) else "public"
        editorial = "revisado" if origem in ("canon", "memoria") else "catalogado"
        entradas = [(i, int(m.group(1))) for i, ln in enumerate(linhas, 1) if (m := RE_ENTRADA.match(ln))]
        if entradas:
            limites = [i for i, _ in entradas] + [len(linhas) + 1]
            for (i, n), fim in zip(entradas, limites[1:]):
                corpo = "\n".join(linhas[i - 1:fim - 1])
                obj = {"object_id": f"alex:entrada:{n}@{rel}", "tipo": "entrada", "entrada": n, "caminho": rel,
                       "linha": i, "commit": commit, "sha256": hashlib.sha256(corpo.encode()).hexdigest(),
                       "classification": acesso, "editorial_status": editorial, "origem": origem,
                       "cita": sorted({int(c) for c in RE_CITA.findall(corpo)} - {n})}
                yield obj, [(i + off - 1, b) for off, b in _blocos(linhas[i - 1:fim - 1])]
            cabeca = linhas[:entradas[0][0] - 1]
        else:
            cabeca = linhas
        obj = {"object_id": f"alex:arquivo:{rel}", "tipo": "arquivo", "entrada": None, "caminho": rel, "linha": 1,
               "commit": commit, "sha256": hashlib.sha256(texto.encode()).hexdigest(), "classification": acesso,
               "editorial_status": editorial, "origem": origem, "cita": []}
        yield obj, list(_blocos(cabeca))


ESQUEMA = """
CREATE TABLE meta(chave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE objects(object_id TEXT PRIMARY KEY, tipo TEXT, entrada INTEGER, caminho TEXT, linha INTEGER,
  commit_ TEXT, sha256 TEXT, classification TEXT, editorial_status TEXT, origem TEXT,
  v_identidade TEXT, v_integridade TEXT, v_suporte TEXT);
CREATE TABLE relations(src TEXT, dst_entrada INTEGER, tipo TEXT);
CREATE TABLE trechos(rowid INTEGER PRIMARY KEY, object_id TEXT, linha INTEGER, texto TEXT);
CREATE VIRTUAL TABLE trechos_fts USING fts5(texto, content='trechos', content_rowid='rowid',
  tokenize='unicode61 remove_diacritics 2');
CREATE TABLE skills(skill_id TEXT PRIMARY KEY, nome TEXT, origem TEXT, caminho TEXT, descricao TEXT,
  sha256 TEXT, estado TEXT, quarentena INTEGER);
CREATE VIRTUAL TABLE skills_fts USING fts5(nome, descricao, content='skills', tokenize='unicode61 remove_diacritics 2');
"""


def _anteriores() -> dict:
    try:
        con = sqlite3.connect(f"file:{indice_path()}?mode=ro", uri=True)
        try:
            return dict(con.execute("SELECT object_id, sha256 FROM objects"))
        finally:
            con.close()
    except sqlite3.Error:
        return {}


def indexar(raiz: Path | None = None, skills: bool = True) -> dict:
    """Reconstrói o índice inteiro a partir do snapshot (determinístico; troca atômica)."""
    raiz = Path(raiz) if raiz else snapshot("HEAD")
    commit = (raiz / ".commit").read_text().strip() if (raiz / ".commit").exists() else "sem-commit"
    antes = _anteriores()
    cache().mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=cache(), prefix=".indice.", suffix=".sqlite3")
    os.close(fd)
    con = sqlite3.connect(tmp)
    try:
        con.executescript(ESQUEMA)
        n_obj = n_tr = 0
        for obj, trechos in _objetos(raiz, commit):
            con.execute("INSERT OR REPLACE INTO objects VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (obj["object_id"], obj["tipo"], obj["entrada"], obj["caminho"], obj["linha"], commit,
                         obj["sha256"], obj["classification"], obj["editorial_status"], obj["origem"],
                         f"git:{commit[:12]}", "sha256", "not_checked"))
            con.executemany("INSERT INTO relations VALUES (?,?, 'cita')", [(obj["object_id"], c) for c in obj["cita"]])
            for linha, texto in trechos:
                cur = con.execute("INSERT INTO trechos(object_id, linha, texto) VALUES (?,?,?)",
                                  (obj["object_id"], linha, texto[:4000]))
                con.execute("INSERT INTO trechos_fts(rowid, texto) VALUES (?,?)", (cur.lastrowid, texto[:4000]))
                n_tr += 1
            n_obj += 1
        n_sk = 0
        if skills:
            sys.path.insert(0, str(AQUI))
            import skills as _sk  # noqa: E402
            n_sk = _sk.popular(con, raiz)
        con.executemany("INSERT INTO meta VALUES (?,?)", [("commit", commit), ("raiz", str(raiz)),
                        ("gerado_em", time.strftime("%Y-%m-%dT%H:%M:%S%z")), ("objetos", str(n_obj)),
                        ("trechos", str(n_tr)), ("skills", str(n_sk)), ("schema", "1")])
        novos = dict(con.execute("SELECT object_id, sha256 FROM objects"))
        con.commit()
    finally:
        con.close()
    os.replace(tmp, indice_path())
    mudou = sorted(k for k, v in novos.items() if k in antes and antes[k] != v)
    saiu = sorted(set(antes) - set(novos))
    if mudou or saiu:
        eventos.registrar("drift", "derivados_pendentes", "indice", componente="alexandria", commit=commit,
                          mudaram=mudou[:200], sairam=saiu[:200], n_mudaram=len(mudou), n_sairam=len(saiu))
    eventos.registrar("execution", "ok", "indexar", componente="alexandria", commit=commit, objetos=n_obj,
                      trechos=n_tr, skills=n_sk)
    return {"commit": commit, "objetos": n_obj, "trechos": n_tr, "skills": n_sk, "mudaram": len(mudou), "sairam": len(saiu)}


def _con() -> sqlite3.Connection:
    if not indice_path().exists():
        raise FileNotFoundError("índice ausente: rode `acervo.py indexar`")
    con = sqlite3.connect(f"file:{indice_path()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def meta() -> dict:
    try:
        con = _con()
    except FileNotFoundError:
        return {}
    try:
        return dict(con.execute("SELECT chave, valor FROM meta").fetchall())
    finally:
        con.close()


def _alvo(con, entrada: int, permitidos: tuple):
    # só fonte viva (canon e memória); cópia em extras/arquivo não é alvo de citação
    sql = ("SELECT * FROM objects WHERE entrada = ? AND origem IN ('canon', 'memoria') AND classification IN (%s)"
           " ORDER BY %s LIMIT 1"
           % (",".join("?" * len(permitidos)), PRIORIDADE))
    return con.execute(sql, (entrada, *permitidos)).fetchone()


def _fts_query(ps: list[str]) -> str:
    return " OR ".join('"' + p.replace('"', "") + '"*' for p in ps)


def _semantica_padrao(consulta: str, n: int) -> list[dict]:
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "busca_semantica.py"), "--json", "-n", str(n), consulta],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip().splitlines()[-1:] or ["falhou"])
    d = json.loads(r.stdout)
    return d if isinstance(d, list) else d.get("resultados", [])


def consultar(consulta: str, *, acesso: str = "public", n: int = 8, semantica: str = "auto",
              buscar_semantica=None, salvar: bool = False) -> dict:
    """Pacote de evidência. `semantica`: nunca | auto (só se o léxico achar < 3) | sempre."""
    if acesso not in ("public", "project", "private"):
        raise ValueError("acesso fora da lista")
    permitidos = {"public": ("public",), "project": ("public", "project"), "private": ("public", "project", "private")}[acesso]
    ps = busca_texto.palavras(consulta)
    avisos, resultados, metodos = [], [], []
    m = meta()
    con = _con()
    try:
        if ps:
            linhas = con.execute(
                "SELECT t.object_id, t.linha, t.texto, o.caminho, o.commit_, o.sha256, o.entrada, o.classification,"
                " o.editorial_status, bm25(trechos_fts) AS r FROM trechos_fts JOIN trechos t ON t.rowid = trechos_fts.rowid"
                " JOIN objects o ON o.object_id = t.object_id WHERE trechos_fts MATCH ? AND o.classification IN (%s)"
                " ORDER BY r LIMIT 400" % ",".join("?" * len(permitidos)), (_fts_query(ps), *permitidos)).fetchall()
            inteiras = [re.compile(r"(?<![a-z0-9])" + re.escape(p) + r"(?![a-z0-9])") for p in ps]

            def chave(row):
                norm = busca_texto._norm(row["texto"])
                return (-sum(p in norm for p in ps), -sum(bool(x.search(norm)) for x in inteiras), row["r"])
            vistos = set()
            for row in sorted(linhas, key=chave):
                if row["object_id"] in vistos:
                    continue
                vistos.add(row["object_id"])
                norm = busca_texto._norm(row["texto"])
                resultados.append({"object_id": row["object_id"], "caminho": row["caminho"], "linha": row["linha"],
                                   "entrada": row["entrada"], "trecho": row["texto"][:300], "commit": row["commit_"],
                                   "sha256": row["sha256"], "classification": row["classification"],
                                   "editorial_status": row["editorial_status"], "metodo": "lexico",
                                   "palavras": f"{sum(p in norm for p in ps)}/{len(ps)}"})
                if len(resultados) >= n:
                    break
            if resultados:
                metodos.append("lexico")
            # relações: entradas citadas pelos dois primeiros resultados (cita), rotuladas
            ja = {r["entrada"] for r in resultados if r["entrada"] is not None}
            for r in resultados[:2]:
                for (dst,) in con.execute("SELECT dst_entrada FROM relations WHERE src = ? LIMIT 3", (r["object_id"],)):
                    if dst in ja:
                        continue
                    alvo = _alvo(con, dst, permitidos)
                    if alvo:
                        ja.add(dst)
                        resultados.append({"object_id": alvo["object_id"], "caminho": alvo["caminho"], "linha": alvo["linha"],
                                           "entrada": dst, "trecho": None, "commit": alvo["commit_"], "sha256": alvo["sha256"],
                                           "classification": alvo["classification"],
                                           "editorial_status": alvo["editorial_status"], "metodo": "relacao",
                                           "via": r["object_id"]})
                        if "relacao" not in metodos:
                            metodos.append("relacao")
        n_lex = sum(r["metodo"] == "lexico" for r in resultados)
        if semantica == "sempre" or (semantica == "auto" and n_lex < 3):
            try:
                achados = (buscar_semantica or _semantica_padrao)(consulta, n)
                ja = {r["entrada"] for r in resultados if r["entrada"] is not None}
                for a in achados:
                    num = a.get("num")
                    alvo = _alvo(con, num, permitidos) if num else None
                    if not alvo or num in ja:
                        continue
                    ja.add(num)
                    resultados.append({"object_id": alvo["object_id"], "caminho": alvo["caminho"], "linha": alvo["linha"],
                                       "entrada": num, "trecho": (a.get("trecho") or "")[:300], "commit": alvo["commit_"],
                                       "sha256": alvo["sha256"], "classification": alvo["classification"],
                                       "editorial_status": alvo["editorial_status"], "metodo": "semantica",
                                       "score": a.get("score")})
                if any(r["metodo"] == "semantica" for r in resultados):
                    metodos.append("semantica")
            except Exception as e:  # noqa: BLE001 — endpoint fora: degrada para léxico, com aviso
                avisos.append(f"busca semântica indisponível ({e.__class__.__name__}); resultado só léxico")
    finally:
        con.close()
    pacote = {"schema_version": 1, "consulta_sha256": hashlib.sha256(consulta.encode()).hexdigest(),
              "commit": m.get("commit"), "indice_gerado_em": m.get("gerado_em"), "acesso": acesso,
              "gerado_em": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "metodos": metodos, "avisos": avisos,
              "estado": "encontrado" if resultados else NAO_ENCONTRADO, "palavras": ps, "resultados": resultados}
    pacote["context_id"] = "ctx:" + hashlib.sha256(json.dumps([pacote["consulta_sha256"], m.get("commit"),
                                                              [r["object_id"] for r in resultados]]).encode()).hexdigest()[:16]
    if salvar:
        destino = eventos.dados() / "alexandria" / "contextos" / (pacote["context_id"].split(":")[1] + ".json")
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(pacote, ensure_ascii=False, indent=1), encoding="utf-8")
    return pacote


def contexto_valido(pacote: dict) -> dict:
    """Um pacote antigo ainda vale? Compara o sha de cada objeto com o índice atual."""
    con = _con()
    try:
        pend = []
        for r in pacote.get("resultados", []):
            row = con.execute("SELECT sha256 FROM objects WHERE object_id = ?", (r["object_id"],)).fetchone()
            if row is None or row["sha256"] != r["sha256"]:
                pend.append(r["object_id"])
    finally:
        con.close()
    return {"valido": not pend, "pendentes": pend}


def estado() -> dict:
    base = eventos.dados()
    contagem = {}
    for rel in ESTRUTURA:
        if rel.startswith("alexandria/acervo/") and not rel.endswith("snapshots"):
            p = base / rel
            contagem[rel.rsplit("/", 1)[1]] = sum(1 for _ in p.iterdir()) if p.exists() else None
    m = meta()
    snaps = sorted(p.name for p in (base / "alexandria/acervo/snapshots").glob("*")) if (base / "alexandria/acervo/snapshots").exists() else []
    return {"iniciado": (base / "LEIA-ME.md").exists(), "indice": m or None, "snapshots": snaps, "editorial": contagem}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("iniciar")
    s = sub.add_parser("snapshot"); s.add_argument("commit", nargs="?", default="HEAD")
    i = sub.add_parser("indexar"); i.add_argument("--raiz", type=Path)
    c = sub.add_parser("consultar"); c.add_argument("consulta"); c.add_argument("-n", type=int, default=8)
    c.add_argument("--acesso", default="public"); c.add_argument("--semantica", default="auto", choices=("nunca", "auto", "sempre"))
    c.add_argument("--salvar", action="store_true")
    sub.add_parser("estado")
    a = ap.parse_args(argv)
    if a.cmd == "iniciar":
        print(iniciar())
    elif a.cmd == "snapshot":
        print(snapshot(a.commit))
    elif a.cmd == "indexar":
        print(json.dumps(indexar(a.raiz), ensure_ascii=False))
    elif a.cmd == "consultar":
        p = consultar(a.consulta, acesso=a.acesso, n=a.n, semantica=a.semantica, salvar=a.salvar)
        print(json.dumps(p, ensure_ascii=False, indent=1))
        return 0 if p["resultados"] else 1
    else:
        print(json.dumps(estado(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
