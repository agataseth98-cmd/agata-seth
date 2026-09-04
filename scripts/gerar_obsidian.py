#!/usr/bin/env python3
"""Vault Obsidian derivado — representação canônica de TODO o sistema Agata.

MEMÓRIAS.md e os canônicos continuam a fonte da verdade. Isto gera
memoria/obsidian/ : uma nota por entrada de MEMÓRIAS, uma por regra, por
seção de PROJETO, por script, por controle do perímetro, por proposta
aplicada — tudo ligado por wikilinks, com MOCs e um painel de estado.
Serve a visualização do Humano E a leitura da Seth (nota plana, sem
depender de plugin pra extrair informação).

Nunca editado à mão. Regenerado por este script (e pelo post-commit).
Determinístico e idempotente: apaga memoria/obsidian/ e reconstrói.

Uso: python3 scripts/gerar_obsidian.py
"""
import os
import re
import shutil
import subprocess
import sys
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(REPO, "memoria", "obsidian")


def _canon():
    """Proveniência determinística: o commit de que o vault foi gerado, não o
    relógio. AGATA_CANON_SHA/DATA no ambiente vencem (o controle P-10 os passa
    ao rodar num extract sem .git); senão, git. Árvore suja sufixa o SHA."""
    sha = os.environ.get("AGATA_CANON_SHA")
    data = os.environ.get("AGATA_CANON_DATA")
    if sha and data:
        return sha, data
    try:
        g = lambda *a: subprocess.run(["git", "-C", REPO, *a], capture_output=True,
                                      text=True, check=True).stdout.strip()
        sha = g("rev-parse", "HEAD")
        data = g("log", "-1", "--format=%cI")
        # árvore suja = arquivos RASTREADOS diferentes de HEAD. Arquivo não
        # rastreado (canvas/nota que o Obsidian larga na raiz) não muda o que o
        # gerador lê e não pode sujar o carimbo -- senão o P-10 reprova sozinho.
        suja = subprocess.run(["git", "-C", REPO, "diff", "--quiet", "HEAD"],
                              capture_output=True).returncode != 0
        if suja:
            sha += "-arvore-suja"
        return sha, data
    except Exception:
        return "desconhecido", "desconhecido"


CANON, DATA = _canon()

MEMORIAS = os.path.join(REPO, "MEMÓRIAS.md")
MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI"
FIM_MODERNO = re.compile(r"^## Migrado de DIÁRIO\.md", re.M)
CAB_ENTRADA = re.compile(
    r"^\((\d+)\)\s+([A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ]+(?:\s+[A-Za-zÁÂÃÀÉÊÍÓÔÕÚÜÇçãõ0-9.\-]+)?)\s+[—-]\s+(.*)$"
)
REF_ENTRADA = re.compile(r"\((\d{1,3})\)")
REF_REGRA = re.compile(r"\bRegra\s+(\d+(?:\.\d+)?)\b")
REF_CONTROLE = re.compile(r"\bP-([1-9])\b")
REF_SCRIPT = re.compile(r"\b((?:scripts/|\.githooks/)?[\w\-]+\.(?:py|sh))\b")

CANON_INTEIROS = [
    ("ONDE_ESTAMOS.md", "estado para o Humano"),
    ("PROMPT_CARREGAMENTO.md", "prompt de inicialização de sessão em nuvem"),
    ("CHAVES.md", "inventário de credenciais e consumidores"),
    ("PROCEDIMENTO_LOGIN.md", "procedimento do bug de login s2idle"),
]

# ------------------------------------------------------------------ utilidades

_slugs = set()


def slug(txt, prefixo=""):
    s = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    s = s.replace(".", "-")
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[\s_-]+", "-", s)[:60].strip("-") or "x"
    s = f"{prefixo}{s}" if prefixo else s
    base, n = s, 2
    while s in _slugs:
        s = f"{base}-{n}"
        n += 1
    _slugs.add(s)
    return s


def yq(txt):
    """string YAML segura numa linha."""
    t = str(txt).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return f'"{t}"'


def ylist(xs):
    return "[" + ", ".join(str(x) for x in xs) + "]"


NOTAS = set()  # todo basename gerado, para só linkar o que existe


def link(base, rotulo=None):
    if base in NOTAS:
        return f"[[{base}|{rotulo}]]" if rotulo else f"[[{base}]]"
    return rotulo or base


def escrever(rel, linhas):
    p = os.path.join(SAIDA, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas).rstrip() + "\n")


def fm(campos):
    out = ["---"]
    for k, v in campos.items():
        out.append(f"{k}: {v}")
    out += ["---", ""]
    return out


# ------------------------------------------------------------------ parse

def ler(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def parse_entradas(texto):
    ini = texto.find(MARCADOR)
    if ini == -1:
        sys.exit("ERRO: marcador ENTRADAS-NOVAS não achado.")
    corpo = texto[texto.find("\n", ini) + 1:]
    m = FIM_MODERNO.search(corpo)
    if m:
        corpo = corpo[:m.start()]
    entradas, atual = [], None
    for ln in corpo.split("\n"):
        mm = CAB_ENTRADA.match(ln)
        if mm:
            if atual:
                entradas.append(atual)
            num, tipo, resto = int(mm.group(1)), mm.group(2).strip(), mm.group(3).strip()
            data, titulo = "", resto
            pm = re.match(r"(\d{2}/\d{2}/\d{4})\s*(?:·\s*(.*))?$", resto)
            if pm:
                data, titulo = pm.group(1), (pm.group(2) or "").strip()
            atual = {"num": num, "tipo": tipo, "data": data, "titulo": titulo, "linhas": []}
        elif atual is not None:
            atual["linhas"].append(ln)
    if atual:
        entradas.append(atual)
    return entradas


def secoes(texto):
    """divide um markdown em (titulo, corpo) por heading ^## ."""
    out = []
    cur_t, cur_b = None, []
    for ln in (texto or "").split("\n"):
        if ln.startswith("## "):
            if cur_t is not None:
                out.append((cur_t, "\n".join(cur_b).strip()))
            cur_t, cur_b = ln[3:].strip(), []
        elif cur_t is not None:
            cur_b.append(ln)
    if cur_t is not None:
        out.append((cur_t, "\n".join(cur_b).strip()))
    return out


def cabecalho_arquivo(path):
    """primeira frase útil de um script: docstring ou 1ª linha de comentário."""
    t = ler(path) or ""
    m = re.search(r'"""(.*?)"""', t, re.S)
    if m:
        return " ".join(m.group(1).strip().split("\n")[0:2]).strip()
    for ln in t.split("\n"):
        s = ln.strip().lstrip("#").strip()
        if s and not s.startswith("!") and len(s) > 8:
            return s
    return "(sem descrição no arquivo)"


# ------------------------------------------------------------------ geração

def main():
    if os.path.isdir(SAIDA):
        shutil.rmtree(SAIDA)
    os.makedirs(SAIDA)

    # Lista de .md rastreados capturada AGORA, com memoria/obsidian/ ainda vazio --
    # antes de qualquer nota deste run existir no disco (ver "documentos soltos").
    try:
        todos_md = sorted(subprocess.run(
            ["git", "-C", REPO, "ls-files", "*.md"],
            capture_output=True, text=True, check=True).stdout.splitlines())
    except Exception:
        # Sem .git -- só acontece na sandbox do P-10 (checkout de `git archive`,
        # sem metadado; roda o gerador de novo pra conferir contra o disco real).
        # os.walk sem filtro é seguro aqui: `git archive` por definição só extrai
        # arquivo rastreado, e memoria/obsidian/ (gitignorado) nunca é extraído --
        # exclui mesmo assim, de propósito, caso essa premissa mude um dia.
        achados = []
        for raiz, dirs, arquivos in os.walk(REPO):
            dirs[:] = [d for d in dirs
                       if d != "__pycache__" and os.path.join(raiz, d) != SAIDA]
            for a in arquivos:
                if a.endswith(".md"):
                    rel = os.path.relpath(os.path.join(raiz, a), REPO)
                    achados.append(rel.replace(os.sep, "/"))
        todos_md = sorted(achados)

    reg_txt = ler(os.path.join(REPO, "REGRAS.md"))
    proj_txt = ler(os.path.join(REPO, "PROJETO.md"))
    ref_txt = ler(os.path.join(REPO, "PROJETO_REFERENCIA.md"))
    mem_txt = ler(MEMORIAS)
    entradas = parse_entradas(mem_txt)
    nums = {e["num"] for e in entradas}

    # -------- registrar basenames (para linkar só o que existe)
    ent_base = {e["num"]: f"{e['num']:04d}" for e in entradas}
    NOTAS.update(ent_base.values())

    regra_base = {}   # "1", "1.1", "8" -> basename
    regsec = secoes(reg_txt)
    for t, _ in regsec:
        mr = re.match(r"Regra\s+(\d+(?:\.\d+)?)", t)
        if mr:
            b = f"regra-{mr.group(1).replace('.', '-')}"
        else:
            b = slug(t, "reg-")
        regra_base[t] = b
        NOTAS.add(b)
    # "As 7 regras" cobre 1..7 — aponta os números soltos pra ela
    sete = next((b for (t, b) in regra_base.items() if "7 regras" in t), None)

    proj_base = {t: slug(t, "proj-") for t, _ in secoes(proj_txt)}
    NOTAS.update(proj_base.values())
    ref_base = {t: slug(t, "ref-") for t, _ in secoes(ref_txt)}
    NOTAS.update(ref_base.values())

    scripts = sorted(
        [("scripts/" + n, n) for n in os.listdir(os.path.join(REPO, "scripts"))
         if n.endswith((".py", ".sh")) and n != "__pycache__"]
        + [(".githooks/" + n, n) for n in os.listdir(os.path.join(REPO, ".githooks"))]
    )
    script_base = {}
    for rel, nome in scripts:
        b = slug(nome, "script-")
        script_base[nome] = b
        script_base[rel] = b
        NOTAS.add(b)

    prop_dir = os.path.join(REPO, "propostas", "aplicadas")
    props = sorted(n[:-5] for n in os.listdir(prop_dir) if n.endswith(".diff"))
    prop_base = {p: slug(p, "prop-") for p in props}
    NOTAS.update(prop_base.values())

    controles = ["P-1", "P-2", "P-3", "P-4", "P-5", "P-6", "P-7", "P-8", "P-9", "P-10"]
    ctrl_base = {c: c.lower() for c in controles}
    NOTAS.update(ctrl_base.values())

    for b in ["INICIO", "estado", "timeline", "_LEIA",
              "moc-memoria", "moc-regras", "moc-projeto", "moc-scripts",
              "moc-controles", "moc-propostas", "moc-esferas"]:
        NOTAS.add(b)

    # -------- religação de um corpo de texto
    def religar(corpo, eu=None):
        def _ent(m):
            n = int(m.group(1))
            return f"[[{ent_base[n]}]]" if n in ent_base and n != eu else m.group(0)
        def _reg(m):
            v = m.group(1)
            b = f"regra-{v.replace('.', '-')}"
            if b in NOTAS:
                return f"[[{b}|Regra {v}]]"
            if "." not in v and sete:
                return f"[[{sete}|Regra {v}]]"
            return m.group(0)
        def _ctrl(m):
            b = f"p-{m.group(1)}"
            return f"[[{b}|P-{m.group(1)}]]" if b in NOTAS else m.group(0)
        def _scr(m):
            nome = m.group(1)
            b = script_base.get(nome) or script_base.get(nome.split("/")[-1])
            return f"[[{b}|{nome}]]" if b else m.group(0)
        corpo = REF_ENTRADA.sub(_ent, corpo)
        corpo = REF_REGRA.sub(_reg, corpo)
        corpo = REF_CONTROLE.sub(_ctrl, corpo)
        corpo = REF_SCRIPT.sub(_scr, corpo)
        return corpo

    # -------- entradas + índice reverso
    citada_por = {e["num"]: set() for e in entradas}
    for e in entradas:
        corpo = "\n".join(e["linhas"])
        e["cita"] = sorted(n for n in {int(x) for x in REF_ENTRADA.findall(corpo)}
                           if n in nums and n != e["num"])
        for a in e["cita"]:
            citada_por[a].add(e["num"])

    for e in entradas:
        corpo = "\n".join(e["linhas"]).strip("\n")
        campos = {
            "tipo-nota": "entrada",
            "entrada": e["num"],
            "categoria": yq(e["tipo"]),
            "data": e["data"] or "null",
            "titulo": yq(e["titulo"]),
            "cita": ylist(e["cita"]),
            "citada_por": ylist(sorted(citada_por[e["num"]])),
            "tags": "[memoria/entrada]",
        }
        linhas = fm(campos)
        linhas.append(f"# ({e['num']}) {e['tipo']} — {e['data']} · {e['titulo']}")
        linhas.append("")
        linhas.append(religar(corpo, eu=e["num"]))
        linhas.append("")
        if citada_por[e["num"]]:
            linhas.append("## Citada por")
            linhas += [f"- {link(ent_base[n])}" for n in sorted(citada_por[e["num"]])]
        linhas += ["", "---", f"< {link('moc-memoria','MOC memória')} · {link('timeline')} · {link('INICIO')} >"]
        escrever(f"entradas/{e['num']:04d}.md", linhas)

    # -------- regras (seções de REGRAS.md)
    for t, corpo in regsec:
        b = regra_base[t]
        linhas = fm({"tipo-nota": "regra", "secao": yq(t), "fonte": "REGRAS.md",
                     "tags": "[canon/regra]"})
        linhas += [f"# {t}", "", religar(corpo), "",
                   "---", f"< {link('moc-regras','MOC regras')} · fonte: `../../REGRAS.md` >"]
        escrever(f"regras/{b}.md", linhas)

    # -------- projeto + referência
    for t, corpo in secoes(proj_txt):
        b = proj_base[t]
        linhas = fm({"tipo-nota": "projeto", "secao": yq(t), "fonte": "PROJETO.md",
                     "tags": "[canon/projeto]"})
        linhas += [f"# {t}", "", religar(corpo), "",
                   "---", f"< {link('moc-projeto','MOC projeto')} · fonte: `../../PROJETO.md` >"]
        escrever(f"projeto/{b}.md", linhas)
    for t, corpo in secoes(ref_txt):
        b = ref_base[t]
        linhas = fm({"tipo-nota": "referencia", "secao": yq(t),
                     "fonte": "PROJETO_REFERENCIA.md", "tags": "[canon/referencia]"})
        linhas += [f"# {t}", "", religar(corpo), "",
                   "---", f"< {link('moc-projeto','MOC projeto')} · fonte: `../../PROJETO_REFERENCIA.md` >"]
        escrever(f"projeto/{b}.md", linhas)

    # -------- canônicos inteiros
    for arq, desc in CANON_INTEIROS:
        txt = ler(os.path.join(REPO, arq))
        if txt is None:
            continue
        b = slug(arq, "canon-")
        NOTAS.add(b)
        linhas = fm({"tipo-nota": "canon", "arquivo": arq, "resumo": yq(desc),
                     "tags": "[canon/arquivo]"})
        linhas += [f"# {arq} — {desc}", "",
                   "> [!info] Espelho de leitura. Fonte: `../../" + arq + "`. Não editar aqui.",
                   "", religar(txt)]
        escrever(f"canon/{b}.md", linhas)

    # -------- scripts e hooks
    entradas_por_script = {}
    for e in entradas:
        corpo = "\n".join(e["linhas"])
        for m in REF_SCRIPT.finditer(corpo):
            nome = m.group(1).split("/")[-1]
            entradas_por_script.setdefault(nome, set()).add(e["num"])
    for rel, nome in scripts:
        b = script_base[nome]
        ents = sorted(entradas_por_script.get(nome, []))
        linhas = fm({"tipo-nota": "script", "arquivo": rel,
                     "tags": "[sistema/script]"})
        linhas += [f"# `{rel}`", "", "> [!abstract] O que faz",
                   "> " + cabecalho_arquivo(os.path.join(REPO, rel)), ""]
        if ents:
            linhas.append("## Entradas de MEMÓRIAS que citam este arquivo")
            linhas += [f"- {link(ent_base[n])}" for n in ents]
            linhas.append("")
        linhas += ["---", f"< {link('moc-scripts','MOC scripts')} · fonte: `../../{rel}` >"]
        escrever(f"scripts/{b}.md", linhas)

    # -------- propostas aplicadas
    for p in props:
        b = prop_base[p]
        mnum = re.search(r"memorias?-(\d{2,3})", p)
        linhas = fm({"tipo-nota": "proposta", "nome": yq(p), "estado": "aplicada",
                     "tags": "[sistema/proposta]"})
        linhas += [f"# proposta `{p}` — aplicada", ""]
        if mnum and int(mnum.group(1)) in ent_base:
            linhas += [f"Entrada relacionada: {link(ent_base[int(mnum.group(1))])}", ""]
        linhas += ["Diff congelado + `APROVADO-` em `../../propostas/aplicadas/`.", "",
                   "---", f"< {link('moc-propostas','MOC propostas')} >"]
        escrever(f"propostas/{b}.md", linhas)

    # -------- controles do perímetro
    CTRL_DESC = {
        "P-1": "Segredos só em ~/.config/agata/.env, fora do repo",
        "P-2": "O executor pausa e pede sudo ao Humano",
        "P-3": "Publicação é decisão deliberada; consentimento por trecho",
        "P-4": "api_server contido; Ollama só em 127.0.0.1",
        "P-5": "Regra 4 mecânica: MEMÓRIAS.md append-only (sufixo não-encolhido)",
        "P-6": "Cópia da história fora da máquina (bundle + HD)",
        "P-7": "Citação de MEMÓRIAS aponta pra entrada real, não fabricada",
        "P-8": "Quarentena: mudança de comportamento exige proposta + APROVADO-",
        "P-9": "Serviço declarado em PROJETO.md não pode morrer em silêncio",
        "P-10": "Vault derivado confere byte a byte com a regeneração do HEAD",
    }
    for c in controles:
        ents = sorted(e["num"] for e in entradas
                      if re.search(rf"\b{c}\b", "\n".join(e["linhas"])))
        linhas = fm({"tipo-nota": "controle", "controle": c,
                     "tags": "[sistema/perimetro]"})
        linhas += [f"# {c} — {CTRL_DESC[c]}", "",
                   "Implementado em `../../scripts/perimetro.sh`. "
                   f"Ver {link('script-perimetro-sh','perimetro.sh')}.", ""]
        if ents:
            linhas.append("## Entradas que mencionam " + c)
            linhas += [f"- {link(ent_base[n])}" for n in ents]
            linhas.append("")
        linhas += ["---", f"< {link('moc-controles','MOC controles')} >"]
        escrever(f"controles/{c.lower()}.md", linhas)

    # -------- documentos soltos do repositório (fora do que já virou nota estruturada)
    # `todos_md` já foi capturado no topo de main(), antes de qualquer escrita.
    JA_COBERTOS = {"REGRAS.md", "PROJETO.md", "PROJETO_REFERENCIA.md", "MEMÓRIAS.md"}
    JA_COBERTOS |= {arq for arq, _ in CANON_INTEIROS}
    soltos = [p for p in todos_md if p not in JA_COBERTOS]
    grupos = {}
    for p in soltos:
        partes = p.split("/")
        if len(partes) == 1:
            chave = "(raiz)"
        elif partes[0] == "redesign" and len(partes) > 2:
            chave = f"redesign/{partes[1]}"
        else:
            chave = partes[0]
        grupos.setdefault(chave, []).append(p)

    # -------- MOCs
    por_tipo = {}
    for e in entradas:
        por_tipo.setdefault(e["tipo"], []).append(e["num"])
    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    L += [f"# MOC — memória ({len(entradas)} entradas, ({min(nums)})–({max(nums)}))", ""]
    for tp in sorted(por_tipo):
        L.append(f"## {tp} ({len(por_tipo[tp])})")
        L.append(" · ".join(link(ent_base[n]) for n in sorted(por_tipo[tp], reverse=True)))
        L.append("")
    escrever("moc-memoria.md", L)

    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    L += ["# MOC — regras", "", "Fonte: `../REGRAS.md`.", ""]
    L += [f"- {link(b, t)}" for t, b in regra_base.items()]
    escrever("moc-regras.md", L)

    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    L += ["# MOC — projeto e referência", "", "## PROJETO.md"]
    L += [f"- {link(b, t)}" for t, b in proj_base.items()]
    L += ["", "## PROJETO_REFERENCIA.md"]
    L += [f"- {link(b, t)}" for t, b in ref_base.items()]
    escrever("moc-projeto.md", L)

    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    L += ["# MOC — scripts e hooks", ""]
    L += [f"- {link(script_base[nome], rel)}" for rel, nome in scripts]
    escrever("moc-scripts.md", L)

    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    L += ["# MOC — controles do perímetro", "",
          f"Rodam em `../scripts/perimetro.sh` a cada commit. Ver {link('script-perimetro-sh','perimetro.sh')}.", ""]
    L += [f"- {link(c.lower(), c)} — {CTRL_DESC[c]}" for c in controles]
    escrever("moc-controles.md", L)

    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    L += [f"# MOC — propostas aplicadas ({len(props)})", "",
          "Cada uma: `.diff` congelado + `APROVADO-` em `../propostas/aplicadas/`.", ""]
    L += [f"- {link(prop_base[p], p)}" for p in props]
    escrever("moc-propostas.md", L)

    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    L += ["# MOC — memória em duas esferas", "",
          "Arquitetura aprovada em " + link("0283") + " (reversão parcial de (223)).", "",
          "- **Esfera pessoal** — `memoria/missoes/segunda-camada/` — local, privada, sem remote.",
          "- **Esfera do projeto** — `memoria/missoes/agata-sistema/` — conta Google dedicada, escopo `drive.file`.",
          f"- Cano: {link('script-subir-esfera-projeto-py','subir_esfera_projeto.py')} ("+link("0286")+").",
          f"- Credencial: `~/.config/agata/google-project/` — ver {link('canon-chaves-md','CHAVES.md')}.",
          "", "Seção canônica: " + link(proj_base.get("Memória em duas camadas", "x"), "PROJETO.md · Memória em duas camadas")]
    escrever("moc-esferas.md", L)

    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    L += [f"# MOC — documentos do repositório ({len(soltos)})", "",
          "> [!info] Todo `.md` versionado que não virou nota estruturada acima "
          "(não é REGRAS/PROJETO/MEMÓRIAS, seção deles, script, controle ou proposta "
          "aplicada). Link direto pro arquivo real — clique abre o original, não uma "
          "cópia. `extras/` é arquivo deliberado (REGRAS, \"Princípios\"), listado "
          "aqui só para achar, não para ler primeiro.", ""]
    for chave in sorted(grupos):
        L.append(f"## {chave} ({len(grupos[chave])})")
        for p in sorted(grupos[chave]):
            L.append(f"- [{p}](../../{p})")
        L.append("")
    escrever("moc-redesign.md", L)

    # -------- painel de estado
    onde = ler(os.path.join(REPO, "ONDE_ESTAMOS.md")) or ""
    m_ult = re.search(r"## Última atualização\n(.+?)(?:\n##|\Z)", onde, re.S)
    ult = entradas[0]
    L = fm({"tipo-nota": "estado",
            "ultima_entrada": ult["num"], "tags": "[painel]"})
    L += ["# Estado do sistema (derivado)", "",
          "> [!warning] Instantâneo da geração. A verdade viva é o canon + `git`.", "",
          f"- Última entrada: {link(ent_base[ult['num']])} — {ult['titulo']}",
          f"- Total de entradas: {len(entradas)}  ·  regras: {len(regra_base)}  ·  "
          f"scripts: {len(scripts)}  ·  propostas aplicadas: {len(props)}", "",
          "## Última atualização (de ONDE_ESTAMOS.md)", "",
          (m_ult.group(1).strip() if m_ult else "(não encontrado)"), "",
          "---", f"< {link('INICIO')} >"]
    escrever("estado.md", L)

    # -------- timeline
    L = fm({"tipo-nota": "timeline", "tags": "[moc]"})
    L += ["# Linha do tempo — mais recente primeiro", ""]
    L += [f"- {link(ent_base[e['num']])} **{e['tipo']}** {e['data']} — {e['titulo']}"
          for e in entradas]
    escrever("timeline.md", L)

    # -------- INICIO + _LEIA
    escrever("INICIO.md", fm({"tipo-nota": "inicio", "canon": yq(CANON), "data": yq(DATA)}) + [
        "# Agata — vault", "",
        "> [!tip] Comece aqui. Tudo abaixo é **gerado** de `MEMÓRIAS.md` + canon; "
        "para corrigir, entrada nova na história, nunca edite aqui.", "",
        "## Painéis",
        f"- {link('estado','Estado do sistema')}  ·  {link('timeline','Linha do tempo')}",
        "## Mapas",
        f"- {link('moc-memoria','Memória')}  ·  {link('moc-regras','Regras')}  ·  "
        f"{link('moc-projeto','Projeto')}",
        f"- {link('moc-scripts','Scripts')}  ·  {link('moc-controles','Controles P-1..P-9')}  ·  "
        f"{link('moc-propostas','Propostas')}  ·  {link('moc-esferas','Duas esferas')}  ·  "
        f"{link('moc-redesign','Documentos do repositório')}", "",
        "## Como ler o grafo",
        "Cada entrada de MEMÓRIAS é um nó; `(n)` no texto virou aresta. Regras, "
        "scripts, controles e propostas também são nós, ligados pelas entradas que os "
        "citam. Os MOCs são os hubs — comece por eles, não pelo grafo cru.", "",
        "## Fonte da verdade",
        "`../REGRAS.md` · `../PROJETO.md` · `../MEMÓRIAS.md` · `../ONDE_ESTAMOS.md`",
    ])
    escrever("_LEIA.md", [
        "# _LEIA — pasta gerada", "",
        "`scripts/gerar_obsidian.py` reconstrói tudo aqui a partir de `MEMÓRIAS.md` "
        "e dos canônicos. Roda também no `post-commit`.", "",
        "- **Não edite nada aqui** — a próxima geração apaga a pasta e reescreve.",
        "- Corrija a história pelo caminho normal: entrada nova em `MEMÓRIAS.md`.",
        "- Abrir a **raiz do repo** (`~/agata`) como vault; começar por `obsidian/INICIO.md`.",
        "- Reconstruir à mão: `python3 scripts/gerar_obsidian.py`.",
    ])

    n_notas = sum(len(f) for _, _, f in os.walk(SAIDA))
    print(f"vault gerado: {n_notas} notas em memoria/obsidian/ "
          f"({len(entradas)} entradas, {len(regra_base)} regras, {len(scripts)} scripts, "
          f"{len(props)} propostas, {len(controles)} controles)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
