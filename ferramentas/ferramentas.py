#!/usr/bin/env python3
"""Caixa de ferramentas do Agata: skills e agentes por tema, carregados sob demanda.

Só lê arquivos; não executa nada do que está em fontes/.
  ferramentas.py temas                  lista os temas e quantas peças cada um tem
  ferramentas.py tema <tema>            lista as peças do tema (nome, tipo, 1 linha)
  ferramentas.py ver <nome>             imprime o caminho e o texto da peça
  ferramentas.py reindexar              refaz INDICE.md e indice.json
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
REPO = RAIZ.parent
FONTES = {
    "ecc": RAIZ / "fontes" / "ecc",
    "superpowers": RAIZ / "fontes" / "superpowers",
}
PROPRIAS = [REPO / ".agents" / "skills"]

# Peças que mudam o comportamento do sistema por conta própria (memória automática,
# aprendizado, laços autônomos). Só consulta; nunca carregar sem decisão do Humano.
QUARENTENA = re.compile(
    r"^(continuous-learning.*|unified-memory|agentic-os|autonomous-.*|continuous-agent-loop|"
    r"dynamic-workflow-mode|orch-.*|visa-doc-translate|growth-log|ledger.*)$"
)

# Ordem importa: o primeiro tema que casar vence.
TEMAS = [
    ("seguranca", r"secur|vuln|hipaa|defi|owasp|threat|secret|compliance|pentest|sanitiz"),
    ("testes", r"test|tdd|e2e|verif|qa$|eval|coverage|debug|diagnos"),
    ("revisao-e-git", r"review|git|commit|branch|worktree|pull-request|pr-|issue|changelog|merge"),
    ("planejamento-e-agentes", r"plan|brainstorm|architect|adr|decision|subagent|dispatch|execut|orchestr|team|council|harness|loop|agent|workflow|task"),
    ("frontend-e-design", r"frontend|design|ui|ux|a11y|css|react|vue|svelte|angular|nextjs|nuxt|tailwind|motion|slide|video|taste|canvas"),
    ("banco-e-infra", r"postgres|mysql|redis|clickhouse|sql|database|migration|docker|k8s|kube|terraform|network|homelab|deploy|ci-|cloud|aws|gcp|azure"),
    ("pesquisa-e-docs", r"research|search|doc|lookup|onboarding|readme|knowledge|wiki|note|summar"),
    ("linguagens", r"python|typescript|javascript|go-|golang|rust|java|kotlin|swift|cpp|c\+\+|csharp|dart|flutter|php|laravel|django|spring|ruby|rails|scala|elixir|fsharp|node|bash|shell|lua|perl|haskell|zig|nest|fastapi|flask|quarkus"),
    ("negocios-e-nichos", r"."),
]


def frontmatter(caminho: Path) -> dict:
    texto = caminho.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"---\n(.*?)\n---", texto, re.S)
    campos = {}
    if m:
        for linha in m.group(1).splitlines():
            k, _, v = linha.partition(":")
            if k.strip() in ("name", "description") and v.strip():
                campos[k.strip()] = v.strip().strip(">|").strip().strip("\"'")
    return campos


def tema_de(nome: str) -> str:
    if QUARENTENA.match(nome):
        return "quarentena"
    for tema, padrao in TEMAS:
        if re.search(padrao, nome):
            return tema
    return "negocios-e-nichos"


def varrer() -> list:
    pecas = []
    for fonte, base in FONTES.items():
        for skill in sorted((base / "skills").glob("*/SKILL.md")):
            nome = skill.parent.name
            f = frontmatter(skill)
            pecas.append({"nome": nome, "tipo": "skill", "fonte": fonte, "tema": tema_de(nome),
                          "caminho": str(skill.relative_to(REPO)), "resumo": f.get("description", "")[:140]})
        for ag in sorted((base / "agents").glob("*.md")) if (base / "agents").is_dir() else []:
            f = frontmatter(ag)
            pecas.append({"nome": ag.stem, "tipo": "agente", "fonte": fonte, "tema": tema_de(ag.stem),
                          "caminho": str(ag.relative_to(REPO)), "resumo": f.get("description", "")[:140]})
    for base in PROPRIAS:
        for skill in sorted(base.glob("*/SKILL.md")):
            f = frontmatter(skill)
            pecas.append({"nome": skill.parent.name, "tipo": "skill", "fonte": "agata", "tema": "agata",
                          "caminho": str(skill.relative_to(REPO)), "resumo": f.get("description", "")[:140]})
    return pecas


def carregar() -> list:
    return json.loads((RAIZ / "indice.json").read_text(encoding="utf-8"))


def reindexar() -> None:
    pecas = varrer()
    (RAIZ / "indice.json").write_text(json.dumps(pecas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    por_tema = {}
    for p in pecas:
        por_tema.setdefault(p["tema"], []).append(p)
    linhas = ["# Caixa de ferramentas — índice por tema", "",
              "Só este arquivo é lido por padrão. Para abrir um tema: `python3 ferramentas/ferramentas.py tema <tema>`.",
              "Para ler uma peça: `python3 ferramentas/ferramentas.py ver <nome>`. Gerado por `reindexar`; não edite à mão.", "",
              "| Tema | Peças | Observação |", "|---|---|---|"]
    obs = {"quarentena": "só consulta; nada carrega sem decisão do Humano", "agata": "skills próprias do sistema"}
    for tema in sorted(por_tema):
        linhas.append(f"| {tema} | {len(por_tema[tema])} | {obs.get(tema, '')} |")
    linhas += ["", f"Total: {len(pecas)} peças. Fontes presas a commit: `fontes/*/COMMIT`; licenças: `fontes/*/LICENSE`.", ""]
    (RAIZ / "INDICE.md").write_text("\n".join(linhas), encoding="utf-8")
    print(f"{len(pecas)} peças, {len(por_tema)} temas")


def main(argv: list) -> int:
    cmd = argv[1] if len(argv) > 1 else "temas"
    if cmd == "reindexar":
        reindexar()
    elif cmd == "temas":
        cont = {}
        for p in carregar():
            cont[p["tema"]] = cont.get(p["tema"], 0) + 1
        for t, n in sorted(cont.items()):
            print(f"{t}\t{n}")
    elif cmd == "tema" and len(argv) > 2:
        for p in carregar():
            if p["tema"] == argv[2]:
                print(f"{p['nome']}\t{p['tipo']}\t{p['fonte']}\t{p['resumo']}")
    elif cmd == "ver" and len(argv) > 2:
        achadas = [p for p in carregar() if p["nome"] == argv[2]]
        if not achadas:
            print("não encontrado neste índice", file=sys.stderr)
            return 1
        for p in achadas:
            print(f"# {p['caminho']} (tema {p['tema']}, fonte {p['fonte']})")
            if p["tema"] == "quarentena":
                print("# QUARENTENA: só leitura; não aplicar sem decisão do Humano")
            print((REPO / p["caminho"]).read_text(encoding="utf-8", errors="replace"))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
