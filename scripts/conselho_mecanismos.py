#!/usr/bin/env python3
"""Verificador de mecanismos do Conselho (pacote mecânico, 12/11/2026).

Decisão do Humano (cache do Conselho, 12/11/2026): o que o Agata desenvolve vale para todos os modelos
do Conselho de forma mecânica, por mecanismo da Máquina, não por instrução. Este verificador lê SÓ o
repositório (nada fora dele, nem ~/.codex, ~/.gemini, ~/.config) e diz, por modelo:

  - ponto de entrada: cada CLI lê AGENTS.md (direto ou por ponteiro). Falha se o ponteiro se perdeu.
  - decisões: a cadeia AGENTS.md -> PROMPT_CARREGAMENTO.md -> canon, e o cache do Conselho.
  - contador de turno (scripts/turno.py) e auditoria de fim de turno (scripts/auditoria_stop.py).
  - negação de leitura de ~/.config/agata/.env.
  - subagentes com o pacote mínimo.

Estados (cada linha diz qual é):
  ok-mecanico   verificado nesta Máquina pelo próprio arquivo do repo.
  ok-doc        depende de comportamento nativo da CLI, segundo a doc pública (não rodado aqui).
  passo-humano  existe como exemplo em config/cli/; o Humano copia para fora do repo.
  disciplina    depende de o modelo cumprir a instrução.
  nao-medido    a doc pública não confirma, ou falta medir na CLI instalada.
  FALHA         o que o sistema afirma não bate com o arquivo. Faz a saída ser 1.

Uso: python3 scripts/conselho_mecanismos.py --verificar [--raiz CAMINHO]
Saída: uma linha por controle: `modelo | controle | estado | evidência`. Código 0 sem FALHA; 1 com FALHA.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ_PADRAO = Path(__file__).resolve().parents[1]
LIMITE_CODEX_BYTES = 32 * 1024  # project_doc_max_bytes, padrão da doc do Codex
LIMITE_PONTEIRO_BYTES = 500     # CLAUDE.md e GEMINI.md são ponteiros, não cópia
CANON_ENCADEADO = ("REGRAS.md", "PROTOCOLOS.md", "FALHAS.md", "MEMÓRIAS.md", "PROJETO.md")

DOC = {
    "claude": "https://code.claude.com/docs/en/memory",
    "claude_hooks": "https://code.claude.com/docs/en/hooks",
    "claude_perm": "https://code.claude.com/docs/en/permissions",
    "claude_agents": "https://code.claude.com/docs/en/sub-agents",
    "codex_agents": "https://learn.chatgpt.com/docs/agent-configuration/agents-md",
    "codex_hooks": "https://learn.chatgpt.com/docs/hooks",
    "codex_config": "https://learn.chatgpt.com/docs/config-file/config-reference",
    "gemini_md": "https://geminicli.com/docs/cli/gemini-md/",
    "gemini_hooks": "https://geminicli.com/docs/hooks/reference/",
    "opencode_rules": "https://opencode.ai/docs/rules/",
    "opencode_perm": "https://opencode.ai/docs/permissions/",
}


@dataclass(frozen=True)
class Achado:
    modelo: str
    controle: str
    estado: str
    evidencia: str


def _ler(raiz: Path, rel: str) -> str | None:
    try:
        return (raiz / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _json(raiz: Path, rel: str):
    texto = _ler(raiz, rel)
    if texto is None:
        return None
    try:
        return json.loads(texto)
    except ValueError:
        return None


def _tem_import_agents(texto: str | None) -> bool:
    return texto is not None and any(ln.strip() == "@AGENTS.md" for ln in texto.splitlines())


def _ponteiro_ok(raiz: Path, rel: str) -> bool:
    texto = _ler(raiz, rel)
    return _tem_import_agents(texto) and len(texto.encode("utf-8")) <= LIMITE_PONTEIRO_BYTES


def _toml(raiz: Path, rel: str):
    try:
        import tomllib  # biblioteca padrão a partir do Python 3.11
    except ImportError:
        return "sem-tomllib"
    texto = _ler(raiz, rel)
    if texto is None:
        return None
    try:
        return tomllib.loads(texto)
    except ValueError:
        return None


def verificar(raiz: Path = RAIZ_PADRAO) -> list[Achado]:
    raiz = Path(raiz)
    out: list[Achado] = []

    def add(modelo: str, controle: str, estado: str, evidencia: str) -> None:
        out.append(Achado(modelo, controle, estado, evidencia))

    agents = _ler(raiz, "AGENTS.md")
    tam_agents = len(agents.encode("utf-8")) if agents is not None else 0

    # 1. Ponto de entrada: cada CLI lê AGENTS.md, direto ou por ponteiro.
    ok = _ponteiro_ok(raiz, "CLAUDE.md")
    add("Claude Code", "entrada -> AGENTS.md", "ok-mecanico" if ok else "FALHA",
        "CLAUDE.md só importa @AGENTS.md" if ok else "CLAUDE.md sem a linha @AGENTS.md ou com regra própria")
    ok = agents is not None and tam_agents <= LIMITE_CODEX_BYTES and not (raiz / "AGENTS.override.md").exists()
    add("Codex", "entrada -> AGENTS.md", "ok-mecanico" if ok else "FALHA",
        f"AGENTS.md com {tam_agents} B (limite {LIMITE_CODEX_BYTES} B) e sem AGENTS.override.md na raiz; "
        f"a leitura é nativa ({DOC['codex_agents']})" if ok else
        "AGENTS.md ausente, acima do limite do Codex ou com AGENTS.override.md na raiz")
    ok = _ponteiro_ok(raiz, "GEMINI.md")
    add("Gemini CLI", "entrada -> AGENTS.md", "ok-mecanico" if ok else "FALHA",
        "GEMINI.md só importa @AGENTS.md" if ok else "GEMINI.md sem a linha @AGENTS.md ou com regra própria")
    add("OpenCode", "entrada -> AGENTS.md", "ok-doc" if agents is not None else "FALHA",
        f"AGENTS.md na raiz, lido pelo OpenCode segundo {DOC['opencode_rules']}; "
        "não rodado aqui" if agents is not None else "AGENTS.md ausente")
    gw = _ler(raiz, "redesign/router/seth_gateway.py") or ""
    ok = '_diretrizes_agents()' in gw and '/ "AGENTS.md"' in gw
    add("Seth", "entrada -> AGENTS.md (hidratação do gateway)", "ok-mecanico" if ok else "FALHA",
        "seth_gateway.py inclui AGENTS.md na hidratação compacta" if ok else
        "seth_gateway.py não lê AGENTS.md na hidratação")
    add("Seth", "cópia da doutrina no código", "disciplina" if "_DOUTRINA_FIXA" in gw else "ok-mecanico",
        "seth_gateway.py mantém a constante _DOUTRINA_FIXA: cópia de regras, não comparada com AGENTS.md "
        "(pendência do Humano)" if "_DOUTRINA_FIXA" in gw else "sem constante de doutrina no gateway")

    # 2. Decisões: AGENTS.md aponta para o canon e para o cache do Conselho; o verificador confere os ponteiros.
    prompt = _ler(raiz, "PROMPT_CARREGAMENTO.md") or ""
    canon_ok = "PROMPT_CARREGAMENTO.md" in (agents or "") and all(c in prompt for c in CANON_ENCADEADO)
    cache_ok = "cache_conselho.py ler" in (agents or "") and (raiz / "redesign/router/cache_conselho.py").exists()
    contador_ok = "scripts/turno.py proximo" in (agents or "")
    for modelo in ("Claude Code", "Codex", "Gemini CLI", "OpenCode"):
        add(modelo, "decisões: AGENTS.md -> PROMPT_CARREGAMENTO.md -> canon",
            "ok-mecanico" if canon_ok else "FALHA",
            "a cadeia de ponteiros existe; ler o canon é disciplina do modelo" if canon_ok else
            "AGENTS.md ou PROMPT_CARREGAMENTO.md não encadeiam o canon")
        add(modelo, "decisões: cache do Conselho", "ok-mecanico" if cache_ok else "FALHA",
            "AGENTS.md manda ler cache_conselho.py e o arquivo existe; ler é disciplina do modelo"
            if cache_ok else "AGENTS.md não manda ler o cache do Conselho, ou o arquivo sumiu")
    add("Seth", "decisões: canon e cache na hidratação e nas ferramentas",
        "ok-mecanico" if ("resumo_hidratacao" in gw and "query_canon" in gw) else "FALHA",
        "gateway injeta o resumo do cache do Conselho e expõe query_canon" if
        ("resumo_hidratacao" in gw and "query_canon" in gw) else "gateway sem o resumo do cache ou sem query_canon")

    # 3. Contador de turno e auditoria de fim de turno.
    settings = _json(raiz, ".claude/settings.json") or {}
    hooks = settings.get("hooks", {}) if isinstance(settings, dict) else {}
    ups = json.dumps(hooks.get("UserPromptSubmit", []), ensure_ascii=False)
    stop = json.dumps(hooks.get("Stop", []), ensure_ascii=False)
    deny = (settings.get("permissions", {}) or {}).get("deny", []) if isinstance(settings, dict) else []
    add("Claude Code", "contador de turno (gancho UserPromptSubmit)",
        "ok-mecanico" if "turno.py" in ups else "FALHA",
        f"hook de turno em .claude/settings.json ({DOC['claude_hooks']})")
    add("Claude Code", "auditoria de fim de turno (gancho Stop, só aviso)",
        "ok-mecanico" if "auditoria_stop.py" in stop else "FALHA",
        f"hook Stop em .claude/settings.json, saída systemMessage ({DOC['claude_hooks']})")
    add("Claude Code", "negação de leitura de ~/.config/agata/.env",
        "ok-mecanico" if "Read(~/.config/agata/.env)" in deny else "FALHA",
        f"permissions.deny em .claude/settings.json ({DOC['claude_perm']}); cobre também cat, head e tail")
    add("Codex", "contador de turno", "disciplina" if contador_ok else "FALHA",
        "AGENTS.md manda rodar `turno.py proximo` no início de cada resposta: sem gancho, depende do modelo")
    codex = _toml(raiz, "config/cli/codex/config.toml.exemplo")
    codex_ok = isinstance(codex, dict) and "Stop" in codex.get("hooks", {}) and \
        codex.get("permissions", {}).get("agata", {}).get("filesystem", {}).get("~/.config/agata/.env") == "deny"
    add("Codex", "auditoria de fim de turno e negação do .env",
        "passo-humano" if codex_ok else ("nao-medido" if codex == "sem-tomllib" else "FALHA"),
        f"config/cli/codex/config.toml.exemplo: copiar para ~/.codex/config.toml, rodar /hooks para confiar "
        f"({DOC['codex_hooks']}; chave de deny em {DOC['codex_config']})")
    gem = _json(raiz, "config/cli/gemini/settings.json.exemplo")
    gem_hooks = (gem or {}).get("hooks", {}) if isinstance(gem, dict) else {}
    gem_ok = "AfterAgent" in gem_hooks and "BeforeTool" in gem_hooks
    add("Gemini CLI", "auditoria de fim de turno (AfterAgent) e negação do .env (BeforeTool)",
        "passo-humano" if gem_ok else "FALHA",
        f"config/cli/gemini/settings.json.exemplo, copiar para ~/.gemini/settings.json ({DOC['gemini_hooks']}); "
        "o nome do campo do caminho em tool_input não está confirmado: a checagem é por substring")
    add("Gemini CLI", "contador de turno", "disciplina" if contador_ok else "FALHA",
        "sem gancho de início de turno: depende de o modelo rodar `turno.py proximo`")
    oc = _json(raiz, "config/cli/opencode/opencode.json.exemplo")
    oc_ok = isinstance(oc, dict) and {"action": "read", "resource": "*.env", "effect": "deny"} in oc.get("permissions", [])
    add("OpenCode", "negação de leitura de .env", "passo-humano" if oc_ok else "FALHA",
        f"config/cli/opencode/opencode.json.exemplo (sintaxe V2 da doc: {DOC['opencode_perm']}); "
        "não medido: a regra de *.env cobre ~/.config/agata/.env na versão instalada?")
    add("OpenCode", "auditoria de fim de turno", "nao-medido",
        "a doc pública consultada não confirma evento de fim de turno com o texto da resposta; "
        "sem gancho, fica como disciplina")
    add("OpenCode", "contador de turno", "disciplina" if contador_ok else "FALHA",
        "sem gancho de início de turno: depende de o modelo rodar `turno.py proximo`")

    # 4. Subagentes: modelo barato, limite de turnos e pacote mínimo.
    agentes_dir = raiz / ".claude" / "agents"
    arquivos = sorted(agentes_dir.glob("*.md")) if agentes_dir.is_dir() else []
    falhas_ag = []
    for arq in arquivos:
        t = arq.read_text(encoding="utf-8")
        if "model: haiku" not in t or "maxTurns:" not in t or "omitClaudeMd: true" in t or "## Pacote mínimo" not in t:
            falhas_ag.append(arq.name)
    add("Claude Code", "subagentes: haiku, maxTurns e pacote mínimo",
        "ok-mecanico" if arquivos and not falhas_ag else "FALHA",
        f"{len(arquivos)} agentes em .claude/agents/" + (f"; faltam campos em: {', '.join(falhas_ag)}" if falhas_ag else ""))
    skill = _ler(raiz, ".agents/skills/agata-equipe/SKILL.md") or ""
    add("Todos (subagentes)", "pacote mínimo na skill de equipe",
        "disciplina" if "## 9. Pacote mínimo para subagente" in skill else "FALHA",
        "a regra está na skill agata-equipe; cumprir é disciplina fora do Claude Code")
    return out


def _main(argv: list[str]) -> int:
    raiz = RAIZ_PADRAO
    if "--raiz" in argv:
        raiz = Path(argv[argv.index("--raiz") + 1])
    if "--verificar" not in argv:
        print(__doc__)
        return 2
    achados = verificar(raiz)
    for a in achados:
        print(f"{a.modelo} | {a.controle} | {a.estado} | {a.evidencia}")
    falhas = [a for a in achados if a.estado == "FALHA"]
    mec = sum(a.estado == "ok-mecanico" for a in achados)
    dis = sum(a.estado == "disciplina" for a in achados)
    print(f"resumo: {len(achados)} controles; ok-mecanico {mec}; disciplina {dis}; FALHA {len(falhas)}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
