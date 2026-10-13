#!/usr/bin/env python3
"""Vault Obsidian derivado — representação canônica de TODO o sistema Agata.

MEMÓRIAS.md e os canônicos continuam a fonte da verdade. Isto gera
memoria/obsidian/ : uma nota por entrada de MEMÓRIAS, uma por regra, por
seção de PROJETO, por script, por controle do perímetro, por proposta
aplicada — tudo ligado por wikilinks, com MOCs e um painel de estado.
Serve a visualização do Humano E a leitura da Seth (nota plana, sem
depender de plugin pra extrair informação).

Nunca editado à mão. Regenerado por este script (e pelo post-commit).
Determinístico e idempotente. Desde (670) escreve NO LUGAR: grava só o arquivo
cujo conteúdo mudou e remove só o que deixou de existir -- apagar a pasta inteira
a cada commit deixava o índice do Obsidian (e a listagem de diretório) para trás.

Uso: python3 scripts/gerar_obsidian.py
"""
import os
import re
import json
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
MORNO = os.path.join(REPO, "MEMORIAS-MORNO.md")
FRIO_DIR = os.path.join(REPO, "memoria", "frio")
MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI"
FIM_MODERNO = re.compile(r"^## Migrado de DIÁRIO\.md", re.M)
CAB_ENTRADA = re.compile(
    r"^\((\d+)\)\s+([A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ]+(?:\+[A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ]+)*(?:\s+[A-Za-zÁÂÃÀÉÊÍÓÔÕÚÜÇçãõ0-9.\-]+)?)\s+[—-]\s+(.*)$"
)
FRIO_NOME = re.compile(
    r"^MEMORIAS-FRIO-(\d{4}-\d{2}-\d{2})(?:-(\d+))?(-com-migrado)?\.md$"
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


def wikilink_arquivo(caminho_relativo_ao_repo, rotulo):
    """Wikilink de verdade pra um arquivo REAL do repositório (fora de
    memoria/obsidian/) -- caminho relativo à RAIZ DO VAULT (== raiz do repo),
    não ao arquivo atual. Entra no grafo/backlinks do Obsidian de verdade,
    diferente de um link markdown [texto](../../caminho) -- que abre, mas o
    Obsidian não conta como aresta."""
    return f"[[{caminho_relativo_ao_repo}|{rotulo}]]"


ESCRITOS = set()  # caminhos gerados neste run -- o resto de SAIDA é removido no fim


def escrever(rel, linhas, cru=None):
    """Grava só se o conteúdo mudou (670): o Obsidian não reindexa à toa e a
    listagem de diretório não fica para trás."""
    p = os.path.join(SAIDA, rel)
    ESCRITOS.add(os.path.normpath(p))
    novo = cru if cru is not None else "\n".join(linhas).rstrip() + "\n"
    try:
        with open(p, encoding="utf-8") as f:
            if f.read() == novo:
                return
    except OSError:
        pass
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp-gerador"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(novo)
    os.replace(tmp, p)


def _limpar_obsoletos():
    """Remove de SAIDA o que este run não gerou (nota que deixou de existir)."""
    for raiz, dirs, arquivos in os.walk(SAIDA, topdown=False):
        for a in arquivos:
            c = os.path.normpath(os.path.join(raiz, a))
            if c not in ESCRITOS:
                os.remove(c)
        if raiz != SAIDA and not os.listdir(raiz):
            os.rmdir(raiz)


# ------------------------------------------------------------------ cérebro (670)
# Região anatômica de cada nota (propriedade `brain_region`, lida pelo plugin
# Brain Atlas) e `kind` (escolhe a cor dentro da paleta do plugin mais próxima
# da identidade da Agata). Fonte única: config/agata-identidade.json.
def _identidade():
    try:
        with open(os.path.join(REPO, "config", "agata-identidade.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"escuro": {}, "regioes": {}}


IDENT = _identidade()
_REGIAO_POR_NOTA = {"regra": "frontal", "projeto": "frontal", "referencia": "frontal",
                    "canon": "frontal", "proposta": "frontal", "script": "parietal",
                    "controle": "parietal", "moc": "stem", "estado": "stem",
                    "timeline": "stem", "inicio": "stem"}


def regiao_entrada(categoria):
    c = categoria.upper()
    if "CORRE" in c or "FALHA" in c or "INCIDENTE" in c:
        return "cerebellum"
    if "DECIS" in c or "CONSELHO" in c:
        return "frontal"
    return "temporal"


def _cerebro(campos):
    tipo = str(campos.get("tipo-nota", ""))
    if tipo == "entrada":
        r = regiao_entrada(str(campos.get("categoria", "")).strip('"'))
    else:
        r = _REGIAO_POR_NOTA.get(tipo)
    if not r:
        return {}
    kind = IDENT.get("regioes", {}).get(r, {}).get("kind")
    return {"brain_region": r, **({"kind": kind} if kind else {})}


def _semantica(entradas):
    """Vizinhos por sentido, só LENDO o índice de scripts/busca_semantica.py
    (nunca embeda aqui). Sem índice/numpy: dicionários vazios -- a nota sai
    sem a seção, do mesmo jeito no P-10. Devolve (parecidas, trechos, afinidade,
    n_entradas_com_vetor, n_blocos_com_vetor)."""
    try:
        import numpy as np
        sys.path.insert(0, os.path.join(REPO, "scripts"))
        import busca_semantica as bs
        vetores = bs.carregar_indice()
    except Exception:
        return {}, {}, {}, 0, 0
    if not vetores:
        return {}, {}, {}, 0, 0
    nums, mat = [], []
    bl_dono, bl_n, bl_mat = [], [], []
    for e in entradas:
        v = bs.vetor(vetores, bs.texto_entrada(e))
        if v is not None:
            nums.append(e["num"])
            mat.append(v)
        for bn, t in bs.textos_blocos(e):
            vb = bs.vetor(vetores, t)
            if vb is not None:
                bl_dono.append(e["num"])
                bl_n.append(bn)
                bl_mat.append(vb)
    parecidas, trechos, afinidade = {}, {}, {}
    if len(nums) > 1:
        M = np.vstack(mat).astype("float64")
        S = M @ M.T
        for i, n in enumerate(nums):
            ordem = sorted((j for j in range(len(nums)) if j != i),
                           key=lambda j: (-round(float(S[i, j]), 6), nums[j]))[:5]
            parecidas[n] = [(nums[j], round(float(S[i, j]), 3)) for j in ordem]
            afinidade[n] = round(sum(x for _, x in parecidas[n]) / len(parecidas[n]), 2)
    if len(bl_mat) > 1:
        B = np.vstack(bl_mat).astype("float64")
        SB = B @ B.T
        dono = np.array(bl_dono)
        por_entrada = {}
        for i, n in enumerate(bl_dono):
            por_entrada.setdefault(n, []).append(i)
        for n, idxs in por_entrada.items():
            pares = []
            for i in idxs:
                outros = np.where(dono != n)[0]
                if not len(outros):
                    continue
                j = int(outros[np.argmax(SB[i, outros])])
                pares.append((-round(float(SB[i, j]), 6), bl_n[i], bl_dono[j], bl_n[j]))
            pares.sort()
            vistos, out = set(), []
            for sc, meu, outro, seu in pares:
                if outro in vistos:
                    continue
                vistos.add(outro)
                out.append((meu, outro, seu, round(-sc, 3)))
                if len(out) == 3:
                    break
            trechos[n] = out
    return parecidas, trechos, afinidade, len(nums), len(bl_mat)


def fm(campos):
    out = ["---"]
    campos = {**campos, **_cerebro(campos)}
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


def camadas_frio_recente_primeiro():
    """Nomes dos chunks MEMORIAS-FRIO-*.md em memoria/frio/, do mais pro menos
    recente -- mesma regra usada em scripts/gerar_indice_derivado.py e
    .githooks/gerar-hidratacao.sh (Fase 4, MEMÓRIAS (357)): maior sufixo
    primeiro, depois sem sufixo, depois "-com-migrado"; datas mais recentes
    primeiro entre dias distintos. Verificado contra o conteúdo real dos 11
    chunks existentes em 06/09/2026 (primeira/última entrada de cada um).
    Moradia mudou de raiz do repo para memoria/frio/ em 25/09/2026 (risco
    assumido por escrito pelo Humano, ver a entrada de MEMÓRIAS junto do
    commit que fez a mudança); nomes continuam MEMORIAS-FRIO-*.md."""
    if not os.path.isdir(FRIO_DIR):
        return []
    achados = []
    for nome in os.listdir(FRIO_DIR):
        m = FRIO_NOME.match(nome)
        if not m:
            continue
        data, seq_str, com_migrado = m.groups()
        seq = 0 if com_migrado else int(seq_str or 1)
        achados.append((data, seq, nome))
    achados.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [nome for _, _, nome in achados]


def camadas_fisicas_com_faixa():
    """(nome_arquivo, primeira_n, ultima_n, qtd) para MEMORIAS-MORNO.md e cada
    MEMORIAS-FRIO-*.md, na ordem em que a hidratação as lê (morno, depois frio
    recente->antigo). O MOC de memória usa isto pra listar cada arquivo físico
    com a faixa de entradas que ele guarda -- sem isto os chunks ficam órfãos
    no grafo do Obsidian (achado na sanitização de 08/09, MEMÓRIAS (368))."""
    out = []
    if os.path.isfile(MORNO):
        es = parse_entradas_morno(ler(MORNO))
        if es:
            ns = [e["num"] for e in es]
            out.append(("MEMORIAS-MORNO.md", min(ns), max(ns), len(ns)))
    for nome in camadas_frio_recente_primeiro():
        es = parse_entradas_frio(ler(os.path.join(FRIO_DIR, nome)))
        if es:
            ns = [e["num"] for e in es]
            out.append((nome, min(ns), max(ns), len(ns)))
    return out


def parse_entradas_morno(texto):
    """Camada morna (MEMORIAS-MORNO.md) -- mesma disciplina de quente
    (marcador ENTRADAS-NOVAS obrigatório, mesmo corte no bloco migrado)."""
    return parse_entradas(texto)


def parse_entradas_frio(texto):
    """Um chunk frio não tem marcador (já vem congelado) e NÃO corta em
    FIM_MODERNO: achado testando de verdade (mesmo achado de
    gerar_indice_derivado.py) -- MEMORIAS-FRIO-*-com-migrado.md tem o
    heading "## Migrado de DIÁRIO.md" perto do TOPO do arquivo, com entradas
    modernas espalhadas antes e depois dele; cortar ali descartaria quase
    todo o conteúdo moderno do chunk. Lido inteiro, CAB_ENTRADA não bate no
    formato antigo ("### data (n)") do bloco migrado, que fica de fora sem
    corte explícito."""
    entradas, atual = [], None
    for ln in texto.split("\n"):
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


def todas_entradas_todas_camadas():
    """Quente + morno (se existir) + frio (mais recente primeiro) -- mesma
    ordem/regra de gerar_indice_derivado.py e gerar-hidratacao.sh (Fase 4,
    MEMÓRIAS (357)). Uma nota por entrada em memoria/obsidian/entradas/,
    independente de qual arquivo físico a guarda hoje."""
    entradas = list(parse_entradas(ler(MEMORIAS)))
    if os.path.isfile(MORNO):
        entradas += parse_entradas_morno(ler(MORNO))
    for nome in camadas_frio_recente_primeiro():
        entradas += parse_entradas_frio(ler(os.path.join(FRIO_DIR, nome)))
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


def resumo_readme(path):
    """Título (H1) + primeiro parágrafo de prosa de um README -- pula linhas
    de metadado isoladas (`**Não é canon.**`, `**Tarefa:** ...`) que não
    formam frase por si, pra pegar o parágrafo que explica o "o quê"."""
    t = ler(path) or ""
    linhas = t.split("\n")
    titulo = next((ln[2:].strip() for ln in linhas if ln.startswith("# ")), os.path.basename(path))
    titulo = re.sub(r"^redesign/\S*\s*—\s*", "", titulo)
    par, colhendo = [], False
    for ln in linhas:
        s = ln.strip()
        if s.startswith("# "):
            continue
        if not s:
            if colhendo:
                break
            continue
        if s.startswith("##"):
            break
        so_negrito_curto = re.fullmatch(r"\*\*[^*]+\*\*[.:]?", s) and len(s) < 40
        if so_negrito_curto and not colhendo:
            continue
        par.append(s)
        colhendo = True
    resumo = " ".join(par).strip()
    if len(resumo) > 280:
        resumo = resumo[:277].rstrip() + "…"
    return titulo, resumo


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

def _controles_do_perimetro():
    """(P-N, descrição) lidos de scripts/perimetro.sh -- a fonte da verdade.

    O perímetro declara cada controle com `cabecalho "P-N" "<descrição>" "<fonte>"`.
    Ler dali significa que o vault nunca fica atrás do que o sistema realmente
    roda: controle novo aparece sozinho, controle removido some sozinho.

    FALHA ALTO se não achar nada. Devolver lista vazia em silêncio recriaria,
    de outro jeito, exatamente o problema que esta função existe pra matar --
    um vault que descreve menos controles do que existem, sem avisar.
    """
    caminho = os.path.join(REPO, "scripts", "perimetro.sh")
    try:
        with open(caminho, encoding="utf-8") as fh:
            texto = fh.read()
    except OSError as e:
        raise SystemExit(f"gerar_obsidian: nao consegui ler {caminho} ({e}) -- "
                         "os controles do vault saem dali; abortado sem escrever nada.")
    achados = re.findall(r'^\s*cabecalho\s+"(P-\d+)"\s+"([^"]*)"', texto, re.MULTILINE)
    if not achados:
        raise SystemExit("gerar_obsidian: nenhum controle casou o padrao "
                         "'cabecalho \"P-N\" \"descricao\"' em scripts/perimetro.sh. "
                         "Ou o formato mudou, ou o arquivo esta errado -- abortado "
                         "sem escrever nada, em vez de gerar um vault sem controles.")
    desc = {}
    for c, d in achados:
        desc.setdefault(c, d.strip())
    ordenados = sorted(desc, key=lambda c: int(c.split("-")[1]))
    return ordenados, desc


def main():
    os.makedirs(SAIDA, exist_ok=True)
    ESCRITOS.clear()

    # Lista de .md rastreados capturada AGORA, com memoria/obsidian/ ainda vazio --
    # antes de qualquer nota deste run existir no disco (ver "documentos soltos").
    try:
        todos_md = sorted(subprocess.run(
            ["git", "-c", "core.quotepath=false", "-C", REPO, "ls-files", "*.md"],
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
    # Fase 2 (plano de replicabilidade, 25/09/2026, "opção C"): {{NOME_SISTEMA}} em
    # REGRAS.md resolve pro campo "Nome do sistema:" de PROJETO.md, nunca "Agata"
    # hardcoded -- sem o campo (clone antes da Fase 3), cai em "Agata".
    _m_nome = re.search(r"^Nome do sistema:\s*(.+)$", proj_txt or "", re.MULTILINE)
    _nome_sistema = _m_nome.group(1).strip() if _m_nome else "Agata"
    if reg_txt:
        reg_txt = reg_txt.replace("{{NOME_SISTEMA}}", _nome_sistema)
    entradas = todas_entradas_todas_camadas()
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

    # propostas/aplicadas/ pode não existir ainda -- esqueleto de gênese
    # recém-nascido, antes da primeira proposta aplicada (achado real em
    # (567)/(571): sem esta guarda, o P-10 vira FALHA, não SKIP, a partir do
    # 2º commit de um clone novo, assim que memoria/obsidian/ passa a
    # existir). Lista vazia é o estado correto pra "nenhuma proposta ainda".
    prop_dir = os.path.join(REPO, "propostas", "aplicadas")
    props = sorted(
        n[:-5] for n in (os.listdir(prop_dir) if os.path.isdir(prop_dir) else [])
        if n.endswith(".diff")
    )
    prop_base = {p: slug(p, "prop-") for p in props}
    NOTAS.update(prop_base.values())

    # Os controles vêm do PRÓPRIO perimetro.sh, não de lista fixa aqui.
    # Motivo medido em 10/09/2026: esta lista estava congelada em P-1..P-10
    # enquanto o perímetro já tinha 17. Sete controles -- entre eles o P-11
    # (silo, segurança), o P-14 (selos, história) e os dois criados na
    # véspera -- simplesmente NÃO EXISTIAM no vault. Quem consultasse o vault
    # para saber o que protege o sistema receberia um retrato de meses atrás,
    # sem nenhum aviso de que estava incompleto.
    # Acrescentar os sete à mão seria conserto; ficaria para trás no P-18.
    # Derivar da fonte é mecanismo: controle novo aparece no vault sozinho.
    controles, CTRL_DESC = _controles_do_perimetro()
    ctrl_base = {c: c.lower() for c in controles}
    NOTAS.update(ctrl_base.values())

    for b in ["INICIO", "estado", "timeline", "_LEIA",
              "moc-memoria", "moc-regras", "moc-projeto", "moc-scripts",
              "moc-controles", "moc-propostas", "moc-esferas",
              "moc-documentos", "moc-readmes", "memorias.base",
              "mapa-do-sistema.canvas", "cerebro"]:
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

    parecidas, trechos, afinidade, n_vet, n_blv = _semantica(entradas)
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import agata_blocos

    def _iso(d):
        m = re.match(r"(\d{2})/(\d{2})/(\d{4})$", d or "")
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else "null"

    for e in entradas:
        corpo = "\n".join(agata_blocos.marcar(e["linhas"])).strip("\n")
        par = parecidas.get(e["num"], [])
        campos = {
            "tipo-nota": "entrada",
            "entrada": e["num"],
            "categoria": yq(e["tipo"]),
            "data": e["data"] or "null",
            "titulo": yq(e["titulo"]),
            "cita": ylist(e["cita"]),
            "citada_por": ylist(sorted(citada_por[e["num"]])),
            "dia": _iso(e["data"]),
            "parecidas": "[" + ", ".join(f'"[[{ent_base[n]}]]"' for n, _ in par) + "]",
            "afinidade": afinidade.get(e["num"], "null"),
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
            linhas.append("")
        if par:
            linhas.append("## Parecidas (por sentido)")
            linhas += [f"- {link(ent_base[n])} — {sc:.2f}" for n, sc in par]
            linhas.append("")
        if trechos.get(e["num"]):
            linhas.append("## Trechos parecidos")
            linhas += [f"- este [[#^b{meu}|parágrafo {meu}]] ↔ [[{ent_base[outro]}#^b{seu}|({outro}), parágrafo {seu}]] — {sc:.2f}"
                       for meu, outro, seu, sc in trechos[e["num"]]]
            linhas.append("")
        linhas += ["---", f"< {link('moc-memoria','MOC memória')} · {link('timeline')} · {link('INICIO')} · {link('cerebro','Cérebro')} >"]
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
        # PROMPT_CARREGAMENTO.md carrega {{NOME_SISTEMA}} (Fase 2); os outros 3
        # desta lista não têm o token -- replace() sem ocorrência é no-op.
        txt = txt.replace("{{NOME_SISTEMA}}", _nome_sistema)
        b = slug(arq, "canon-")
        NOTAS.add(b)
        linhas = fm({"tipo-nota": "canon", "arquivo": arq, "resumo": yq(desc),
                     "tags": "[canon/arquivo]"})
        linhas += [f"# {arq} — {desc}", "",
                   "> [!info] Espelho de leitura. Fonte: " + wikilink_arquivo(arq, arq) +
                   ". Não editar aqui.",
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

    # -------- controles do perímetro (lista e descrições vêm de _controles_do_perimetro)
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
    # Camadas morna/fria: têm lugar próprio no moc-memoria.md (abaixo), não
    # entram na lista genérica de "documentos soltos" (MEMÓRIAS (368)).
    JA_COBERTOS |= {p for p in todos_md
                    if os.path.basename(p) == "MEMORIAS-MORNO.md"
                    or FRIO_NOME.match(os.path.basename(p))}
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

    # -------- MOC dedicado: todo README.md do repositório, com título +
    # resumo extraídos do próprio arquivo (hub-of-hubs -- cada README já é
    # o hub do seu subsistema; este é o hub deles).
    GRUPO_README = [
        ("Espinha em produção (redesign/)", (
            "redesign/README.md", "redesign/router/README.md",
            "redesign/grafo/README.md", "redesign/grafo/evals/README.md",
            "redesign/grafo/flows/README.md", "redesign/mcp/README.md",
            "redesign/librechat/README.md", "redesign/obsidian/README.md",
            "redesign/igpu/README.md", "redesign/systemd/README.md",
        )),
        ("Processo e quarentena", (
            "propostas/README.md", "redesign/propostas/README.md",
        )),
        ("Arquivo histórico (extras/)", (
            "extras/arquivo-hermes/README.md", "extras/arquivo-redesign/README.md",
        )),
    ]
    readmes_vistos = {p for _, ps in GRUPO_README for p in ps}
    extras_achados = sorted(p for p in todos_md
                             if os.path.basename(p) == "README.md" and p not in readmes_vistos)

    # -------- MOCs
    por_tipo = {}
    for e in entradas:
        por_tipo.setdefault(e["tipo"], []).append(e["num"])
    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    L += [f"# MOC — memória ({len(entradas)} entradas, ({min(nums)})–({max(nums)}))", "",
          f"Fonte: {wikilink_arquivo('MEMÓRIAS.md', 'MEMÓRIAS.md')}.", ""]
    for tp in sorted(por_tipo):
        L.append(f"## {tp} ({len(por_tipo[tp])})")
        L.append(" · ".join(link(ent_base[n]) for n in sorted(por_tipo[tp], reverse=True)))
        L.append("")
    fisicas = camadas_fisicas_com_faixa()
    if fisicas:
        L += ["## Camadas físicas (Fase 4)", "",
              "> [!info] O grafo tem uma nota por entrada em `entradas/`, seja qual for o "
              "arquivo que a guarda hoje. Estes são os arquivos físicos das camadas morna e "
              "fria — congelados (morno: append-only pelo topo; frio: selado, imutável, P-14). "
              "Listados aqui pra não ficarem soltos no grafo.", ""]
        for nome, a, b, q in fisicas:
            caminho = f"memoria/frio/{nome}" if FRIO_NOME.match(nome) else nome
            L.append(f"- {wikilink_arquivo(caminho, nome)} — ({a})–({b}), {q} entradas")
        L.append("")
    escrever("moc-memoria.md", L)

    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    L += ["# MOC — regras", "", f"Fonte: {wikilink_arquivo('REGRAS.md', 'REGRAS.md')}.", ""]
    L += [f"- {link(b, t)}" for t, b in regra_base.items()]
    escrever("moc-regras.md", L)

    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    L += ["# MOC — projeto e referência", "",
          f"## {wikilink_arquivo('PROJETO.md', 'PROJETO.md')}"]
    L += [f"- {link(b, t)}" for t, b in proj_base.items()]
    L += ["", f"## {wikilink_arquivo('PROJETO_REFERENCIA.md', 'PROJETO_REFERENCIA.md')}"]
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
            L.append(f"- {wikilink_arquivo(p, p)}")
        L.append("")
    escrever("moc-documentos.md", L)  # (369): era "moc-redesign.md" -- nome não batia com o H1

    L = fm({"tipo-nota": "moc", "tags": "[moc]"})
    n_readmes = sum(len(ps) for _, ps in GRUPO_README) + len(extras_achados)
    L += [f"# MOC — READMEs do sistema ({n_readmes})", "",
          "> [!info] Hub dos hubs. Cada README já é a porta de entrada do seu "
          "subsistema (a maioria começa com `## Estado`, uma tabela de tarefas "
          "✅/⏳); esta página só ajuda a achar qual ler primeiro. Título e resumo "
          "vêm do próprio arquivo — não editar aqui, corrigir na fonte.", ""]
    for titulo_grupo, caminhos in GRUPO_README:
        L.append(f"## {titulo_grupo} ({len(caminhos)})")
        L.append("")
        for p in caminhos:
            titulo, resumo = resumo_readme(os.path.join(REPO, p))
            L.append(f"**{wikilink_arquivo(p, titulo)}** — `{p}`")
            if resumo:
                L.append(f"> {resumo}")
            L.append("")
        L.append("")
    if extras_achados:
        L.append(f"## Não classificado ({len(extras_achados)})")
        L.append("> [!warning] README novo desde a última curadoria deste MOC — "
                  "achado por varredura, não posicionado num grupo ainda.")
        L.append("")
        for p in extras_achados:
            titulo, resumo = resumo_readme(os.path.join(REPO, p))
            L.append(f"**{wikilink_arquivo(p, titulo)}** — `{p}`")
            if resumo:
                L.append(f"> {resumo}")
            L.append("")
    escrever("moc-readmes.md", L)

    # -------- moc-missoes.md -- Humano pediu "juntar tudo no grafo" (04/09/2026).
    # memoria/missoes/ é um repositório git PRÓPRIO, sem remote -- git ls-files
    # do repo principal nunca o vê; por isso os arquivos daqui ficavam órfãos
    # no grafo do Obsidian mesmo com o resto do vault linkado. Descoberto via
    # `git -C memoria/missoes ls-files`, não `os.walk` -- mesma disciplina do
    # resto do gerador (fonte é o git, não o disco cru).
    # EXCEÇÃO deliberada: `segunda-camada/` fica de fora -- é a esfera PESSOAL
    # (mais estrita que a esfera do projeto), e PROJETO.md diz "modelos em
    # nuvem não veem". Linkar no grafo principal reduziria essa fronteira
    # justamente pro tipo de sessão (nuvem) que ela existe pra excluir.
    # AGATA_MISSOES_MD_FILE (opcional): caminho de um arquivo com a lista,
    # uma por linha -- mesmo padrão de AGATA_CANON_SHA/DATA. Necessário
    # porque memoria/missoes/ é gitignorado do repo principal: um
    # `git archive HEAD` (a sandbox do P-10) nunca o contém, então o
    # `os.path.isdir` abaixo dá falso nesse ambiente e o P-10 acusaria
    # SUSPEITO pra sempre, mesmo com tudo certo -- achado testando isto, não
    # hipotético. perimetro.sh calcula a lista no repo real (que o tem) e
    # repassa pra sandbox por ARQUIVO, não variável de ambiente: uma missão
    # com milhares de .md rastreados estoura MAX_ARG_STRLEN do kernel
    # (131072 bytes por variável), achado em 15/09/2026 (MEMÓRIAS (429)) —
    # arquivo não tem esse teto, e nenhum outro chamador desta função usava
    # a forma por variável, então não existe interface antiga pra manter.
    MISSOES_DIR = os.path.join(REPO, "memoria", "missoes")
    missoes_md = []
    if os.environ.get("AGATA_MISSOES_MD_FILE"):
        with open(os.environ["AGATA_MISSOES_MD_FILE"], "r", encoding="utf-8") as f:
            missoes_md = sorted(
                p for p in f.read().splitlines()
                if p and not p.startswith("segunda-camada/"))
    elif os.path.isdir(MISSOES_DIR):
        try:
            saida_git = subprocess.run(
                ["git", "-c", "core.quotepath=false", "-C", MISSOES_DIR, "ls-files", "*.md"],
                capture_output=True, text=True, check=True).stdout
            missoes_md = sorted(
                p for p in saida_git.splitlines()
                if not p.startswith("segunda-camada/"))
        except Exception:
            missoes_md = []
    if missoes_md:
        grupos_missoes = {}
        for p in missoes_md:
            partes = p.split("/")
            chave = partes[0] if len(partes) > 1 else "(raiz de missoes/)"
            grupos_missoes.setdefault(chave, []).append(p)
        L = fm({"tipo-nota": "moc", "tags": "[moc]"})
        L += [f"# MOC — missões ({len(missoes_md)})", "",
              "> [!warning] `memoria/missoes/` é git próprio, sem remote, "
              "**gitignorado do repo principal por desenho** (MEMÓRIAS 91/92) "
              "— nunca sobe pro GitHub público. Linkado aqui por pedido do "
              "Humano (04/09/2026); continua fora da hidratação automática "
              "(`.hidrata.md`) — achável, não empurrado. `segunda-camada/` "
              "(esfera pessoal, mais estrita) fica de fora de propósito: "
              "PROJETO.md, \"modelos em nuvem não veem\".", ""]
        for chave in sorted(grupos_missoes):
            L.append(f"## {chave} ({len(grupos_missoes[chave])})")
            for p in sorted(grupos_missoes[chave]):
                caminho_vault = f"memoria/missoes/{p}"
                L.append(f"- {wikilink_arquivo(caminho_vault, p)}")
            L.append("")
        escrever("moc-missoes.md", L)
        NOTAS.add("moc-missoes")

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
          f"scripts: {len(scripts)}  ·  propostas aplicadas: {len(props)}",
          f"- Índice por sentido: {n_vet} de {len(entradas)} entradas e {n_blv} parágrafos com vetor"
          + ("" if n_vet == len(entradas) else
             " — **atrasado**: rode `python3 scripts/busca_semantica.py --atualizar`"), "",
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

    # -------- memorias.base (Obsidian Bases -- nativo, sem plugin, sem vetor)
    # Tabela/cards filtrável e ordenável sobre as entradas, a partir do MESMO
    # frontmatter que as notas de entradas/ já carregam. Escopo por PASTA
    # (file.inFolder), não por `tipo-nota` -- propriedade com hífen quebra o
    # parser de expressão de Bases (não documentado, não arriscado à toa).
    escrever("memorias.base", [
        'filters: file.inFolder("memoria/obsidian/entradas")',
        "",
        "formulas:",
        "  citacoes: 'citada_por.length'",
        "  sem_citacao: 'citada_por.length == 0'",
        "",
        "properties:",
        "  entrada:",
        '    displayName: "#"',
        "  categoria:",
        '    displayName: "Tipo"',
        "  data:",
        '    displayName: "Data"',
        "  titulo:",
        '    displayName: "Título"',
        "  brain_region:",
        '    displayName: "Região"',
        "  afinidade:",
        '    displayName: "Afinidade (sentido)"',
        "  parecidas:",
        '    displayName: "Parecidas"',
        "  formula.citacoes:",
        '    displayName: "Citada por"',
        "",
        "views:",
        "  - type: table",
        '    name: "Todas as entradas"',
        "    sort:",
        "      - property: entrada",
        "        direction: DESC",
        "    order:",
        "      - entrada",
        "      - categoria",
        "      - data",
        "      - titulo",
        "      - brain_region",
        "      - formula.citacoes",
        "  - type: table",
        '    name: "Últimas 2 semanas"',
        "    filters:",
        "      and:",
        "        - 'dia'",
        "        - 'date(dia) >= today() - \"14d\"'",
        "    sort:",
        "      - property: entrada",
        "        direction: DESC",
        "    order:",
        "      - entrada",
        "      - categoria",
        "      - titulo",
        "  - type: cards",
        '    name: "Por região do cérebro"',
        "    groupBy:",
        "      property: brain_region",
        "      direction: ASC",
        "    order:",
        "      - entrada",
        "      - titulo",
        "      - data",
        "  - type: table",
        '    name: "Decisões e Conselho"',
        "    filters: 'brain_region == \"frontal\"'",
        "    sort:",
        "      - property: entrada",
        "        direction: DESC",
        "    order:",
        "      - entrada",
        "      - categoria",
        "      - data",
        "      - titulo",
        "  - type: table",
        '    name: "Correções (cerebelo)"',
        "    filters: 'brain_region == \"cerebellum\"'",
        "    sort:",
        "      - property: entrada",
        "        direction: DESC",
        "    order:",
        "      - entrada",
        "      - data",
        "      - titulo",
        "  - type: table",
        '    name: "Mais citadas"',
        "    limit: 40",
        "    sort:",
        "      - property: formula.citacoes",
        "        direction: DESC",
        "    order:",
        "      - entrada",
        "      - titulo",
        "      - formula.citacoes",
        "  - type: table",
        '    name: "Mais conectadas por sentido"',
        "    limit: 40",
        "    sort:",
        "      - property: afinidade",
        "        direction: DESC",
        "    order:",
        "      - entrada",
        "      - titulo",
        "      - afinidade",
        "      - parecidas",
        "  - type: table",
        '    name: "Órfãs (ninguém cita)"',
        "    filters: 'citada_por.length == 0'",
        "    sort:",
        "      - property: entrada",
        "        direction: DESC",
        "    order:",
        "      - entrada",
        "      - data",
        "      - titulo",
        "      - parecidas",
    ])

    # -------- mapa-do-sistema.canvas (670) -- o cérebro em 2D, para o Humano:
    # uma região por grupo, com as cores da identidade da Agata.
    cores = IDENT.get("escuro", {})
    reg = IDENT.get("regioes", {})
    def _cor(r):
        return cores.get(reg.get(r, {}).get("cor", ""), "#52c7ff")
    import hashlib as _hl
    def _id(txt):
        return _hl.sha256(txt.encode("utf-8")).hexdigest()[:16]
    ultimas = [e["num"] for e in entradas[:6]]
    grupos_canvas = [
        ("frontal", "Frontal — decisão e planejamento", -900, -700,
         [("file", "REGRAS.md"), ("file", "PROTOCOLOS.md"), ("file", "PROJETO.md"),
          ("file", "memoria/obsidian/moc-propostas.md")]),
        ("temporal", "Temporal — memória", 100, -700,
         [("file", "MEMÓRIAS.md"), ("file", "memoria/obsidian/timeline.md")]
         + [("file", f"memoria/obsidian/entradas/{n:04d}.md") for n in ultimas[:4]]),
        ("parietal", "Parietal — ferramentas", -900, 100,
         [("file", "memoria/obsidian/moc-scripts.md"), ("file", "memoria/obsidian/moc-controles.md")]),
        ("cerebellum", "Cerebelo — correção de erro", 100, 100,
         [("file", "FALHAS.md"), ("base", "memoria/obsidian/memorias.base")]),
        ("occipital", "Occipital — o que vem de fora", 1100, 100,
         [("file", "memoria/obsidian/moc-documentos.md"), ("file", "memoria/obsidian/moc-readmes.md")]),
        ("stem", "Tronco — roteamento", 1100, -700,
         [("file", "memoria/obsidian/INICIO.md"), ("file", "memoria/obsidian/estado.md"),
          ("file", "memoria/obsidian/cerebro.md")]),
    ]
    nos, arestas = [], []
    for r, rotulo, gx, gy, itens in grupos_canvas:
        alturas = 260
        cols = 2
        linhas_g = (len(itens) + cols - 1) // cols
        gw, gh = 40 + cols * 420, 80 + linhas_g * (alturas + 40)
        nos.append({"id": _id("g" + r), "type": "group", "x": gx, "y": gy, "width": gw,
                    "height": gh, "label": rotulo, "color": _cor(r)})
        for k, (_tp, caminho) in enumerate(itens):
            nos.append({"id": _id(r + caminho), "type": "file", "file": caminho,
                        "x": gx + 20 + (k % cols) * 420, "y": gy + 60 + (k // cols) * (alturas + 40),
                        "width": 400, "height": alturas, "color": _cor(r)})
    for a, b, rot in [("temporal", "frontal", "memória vira decisão"),
                      ("cerebellum", "frontal", "falha vira regra"),
                      ("parietal", "temporal", "a Máquina registra"),
                      ("stem", "temporal", "hidratação"),
                      ("occipital", "stem", "entra pelo roteamento")]:
        arestas.append({"id": _id(a + b), "fromNode": _id("g" + a), "toNode": _id("g" + b),
                        "toEnd": "arrow", "label": rot, "color": _cor(a)})
    escrever("mapa-do-sistema.canvas", None,
             cru=json.dumps({"nodes": nos, "edges": arestas}, ensure_ascii=False, indent=1) + "\n")

    # -------- cerebro.md (670) -- porta de entrada do segundo cérebro
    cont_reg = {}
    for e in entradas:
        r = regiao_entrada(e["tipo"])
        cont_reg[r] = cont_reg.get(r, 0) + 1
    L = fm({"tipo-nota": "moc", "tags": "[moc, cerebro]"})
    L += ["# 🧠 O cérebro da Agata", "",
          "> [!tip] Abra a paleta de comandos (Ctrl+P) → **Brain Atlas: Open** — o vault inteiro "
          "vira um cérebro 3D girando. Clique num neurônio para abrir a nota; arraste para fixá-lo. "
          "Os botões FRO · PAR · TEM · OCC · CER · STM acendem e apagam cada lobo.", "",
          "## As regiões", "",
          "| Região | O que guarda | Entradas |", "|---|---|---|"]
    for r in ["frontal", "temporal", "parietal", "cerebellum", "occipital", "stem"]:
        L.append(f"| **{r}** | {reg.get(r, {}).get('o_que', '')} | {cont_reg.get(r, '—')} |")
    L += ["", "As cores seguem a identidade da Agata (azul memória, violeta decisão, turquesa "
          "ferramenta, rosa correção, âmbar o que vem de fora). As ligações são as citações "
          "`(N)` e, desde (670), as **sinapses por sentido** (`parecidas`, embedding local).", "",
          "## Por onde explorar",
          f"- {link('mapa-do-sistema.canvas', 'Mapa do sistema (Canvas)')} — as regiões em 2D, com as notas abertas.",
          f"- {link('memorias.base', 'Tabela de MEMÓRIAS (Base)')} — visões: últimas 2 semanas, por região, "
          "decisões, correções, mais citadas, **mais conectadas por sentido**, **órfãs**.",
          f"- {link('timeline', 'Linha do tempo')} · {link('estado', 'Estado')} · {link('INICIO', 'Início')}", "",
          "## Insight do dia",
          "As **órfãs** (nenhuma entrada as cita) com **afinidade alta** são ideias que o sistema "
          "esqueceu de ligar: abra a visão “Órfãs” da Base e olhe a coluna Parecidas.", "",
          "## Busca por sentido no terminal",
          "`bash scripts/agata_busca.sh \"frase\"` · `--abrir N` abre no Obsidian · "
          "`--contexto \"tema\"` gera um pacote para colar noutra IA."]
    escrever("cerebro.md", L)

    # -------- INICIO + _LEIA
    escrever("INICIO.md", fm({"tipo-nota": "inicio", "canon": yq(CANON), "data": yq(DATA)}) + [
        "# Agata — vault", "",
        "> [!tip] Comece aqui. Tudo abaixo é **gerado** de `MEMÓRIAS.md` + canon; "
        "para corrigir, entrada nova na história, nunca edite aqui.", "",
        "## 🧠 Cérebro",
        f"- {link('cerebro','O cérebro da Agata')} — gráfico 3D (Brain Atlas), mapa em Canvas, visões da Base.", "",
        "## Painéis",
        f"- {link('estado','Estado do sistema')}  ·  {link('timeline','Linha do tempo')}  ·  "
        f"{link('memorias.base','Tabela de MEMÓRIAS (Base)')}",
        "## Mapas",
        f"- {link('moc-memoria','Memória')}  ·  {link('moc-regras','Regras')}  ·  "
        f"{link('moc-projeto','Projeto')}",
        f"- {link('moc-scripts','Scripts')}  ·  {link('moc-controles', f'Controles {controles[0]}..{controles[-1]}')}  ·  "
        f"{link('moc-propostas','Propostas')}  ·  {link('moc-esferas','Duas esferas')}",
        f"- {link('moc-readmes','READMEs do sistema')}  ·  "
        f"{link('moc-documentos','Documentos do repositório')}  ·  "
        f"{link('moc-missoes','Missões (memoria/missoes/)')}  ·  "
        f"{link('_LEIA','_LEIA — pasta gerada')}", "",
        "## Como ler o grafo",
        "Cada entrada de MEMÓRIAS é um nó; `(n)` no texto virou aresta. Regras, "
        "scripts, controles e propostas também são nós, ligados pelas entradas que os "
        "citam. Os MOCs são os hubs — comece por eles, não pelo grafo cru.", "",
        "## Fonte da verdade",
        f"{wikilink_arquivo('REGRAS.md', 'REGRAS.md')} · "
        f"{wikilink_arquivo('PROJETO.md', 'PROJETO.md')} · "
        f"{wikilink_arquivo('MEMÓRIAS.md', 'MEMÓRIAS.md')} · "
        f"{wikilink_arquivo('ONDE_ESTAMOS.md', 'ONDE_ESTAMOS.md')}",
    ])
    escrever("_LEIA.md", [
        "# _LEIA — pasta gerada", "",
        "`scripts/gerar_obsidian.py` reconstrói tudo aqui a partir de `MEMÓRIAS.md` "
        "e dos canônicos. Roda também no `post-commit`.", "",
        "- **Não edite nada aqui** — a próxima geração reescreve o que mudou e remove o que não existe mais.",
        "- Corrija a história pelo caminho normal: entrada nova em `MEMÓRIAS.md`.",
        "- Abrir a **raiz do repo** (`~/agata`) como vault; começar por `obsidian/INICIO.md`.",
        "- Reconstruir à mão: `python3 scripts/gerar_obsidian.py`.",
    ])

    _limpar_obsoletos()
    n_notas = sum(len(f) for _, _, f in os.walk(SAIDA))
    print(f"vault gerado: {n_notas} notas em memoria/obsidian/ "
          f"({len(entradas)} entradas, {len(regra_base)} regras, {len(scripts)} scripts, "
          f"{len(props)} propostas, {len(controles)} controles)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
