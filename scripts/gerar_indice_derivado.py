#!/usr/bin/env python3
"""Gera o índice derivado do canon público, para consulta externa (NotebookLM).

Lê REGRAS.md, PROJETO.md e as camadas de MEMÓRIAS -- quente (MEMÓRIAS.md),
morno (MEMORIAS-MORNO.md, se existir) e frio (MEMORIAS-FRIO-*.md, chunks
selados -- Fase 4, MEMÓRIAS (357)) --, todas no topo do repositório. NUNCA lê
de memoria/missoes/ -- nem a esfera pessoal (segunda-camada), nem a de
projeto (agata-sistema). A garantia é o conjunto de entrada fixo abaixo
(FONTES + camadas extra de memória) e a reconstrução byte a byte no fim.

Escreve em memoria/missoes/agata-sistema/derivado/ (dentro de agata-sistema/
para o subir_esfera_projeto.py conseguir subir; memoria/missoes/ é gitignorado
do repo principal):
  - indice.md    -- Opção A de MEMÓRIAS (296)/(298):
                    Parte 1: REGRAS.md na íntegra
                    Parte 2: PROJETO.md na íntegra
                    Parte 3: só as linhas de título das entradas de MEMÓRIAS --
                             quente + morno + frio (Fase 4) -- (nº + tipo +
                             data + título), mais recente primeiro (camada por
                             camada), sem corpo de entrada.
  - manifesto.md -- sha256 de REGRAS/PROJETO + de cada camada de memória lida
                    + do indice.md, no commit de referência.

Determinístico: carimbo de commit (git), não relógio de parede. Override por
AGATA_CANON_SHA / AGATA_CANON_DATA no ambiente (para rodar sobre um extract
sem .git, mesmo padrão de gerar_obsidian.py).

Verificação embutida antes de escrever (aborta, nada é gravado):
  1. as fontes são exatamente REGRAS/PROJETO + as camadas de memória achadas
     no disco, cada uma filha direta da raiz do repo;
  2. REGRAS.md e PROJETO.md aparecem no indice.md como bloco verbatim contíguo;
  3. cada linha de título da Parte 3 é uma linha verbatim de alguma camada de
     memória lida (quente, morno ou um chunk frio);
  4. indice.md == HEADER + REGRAS + SEP + PROJETO + SEP + títulos  (byte a byte)
     -- prova de que não há nada além do boilerplate fixo e do canon.
"""
import hashlib
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTES = ("REGRAS.md", "PROJETO.md", "MEMÓRIAS.md")
SAIDA_DIR = os.path.join(REPO, "memoria", "missoes", "agata-sistema", "derivado")
PROIBIDO = os.path.join("memoria", "missoes")

MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI"
FIM_MODERNO = re.compile(r"^## Migrado de DIÁRIO\.md", re.M)
CAB_ENTRADA = re.compile(
    r"^\((\d+)\)\s+([A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ]+(?:\s+[A-Za-zÁÂÃÀÉÊÍÓÔÕÚÜÇçãõ0-9.\-]+)?)\s+[—-]\s+.*$"
)
FRIO_NOME = re.compile(
    r"^MEMORIAS-FRIO-(\d{4}-\d{2}-\d{2})(?:-(\d+))?(-com-migrado)?\.md$"
)

SEP = "\n\n" + "=" * 64 + "\n"


def camadas_frio_recente_primeiro():
    """Nomes dos chunks MEMORIAS-FRIO-*.md na raiz do repo, do mais pro menos
    recente. Mesma regra de ordem do .githooks/gerar-hidratacao.sh (Fase 4,
    MEMÓRIAS (357)): cada passada de scripts/migrar_periodo.py congela o
    trecho mais ANTIGO de morno -- "-com-migrado" é sempre a primeira passada
    de um dia (carrega o bloco migrado, se sobrar naquele momento), o chunk
    SEM sufixo numérico é a segunda, "-2"/"-3"/... crescem na ordem em que
    foram congelados. Mais recente primeiro = maior sufixo primeiro, depois
    sem sufixo, depois "-com-migrado"; entre dias distintos, data mais
    recente primeiro. Verificado contra o conteúdo real dos 11 chunks
    existentes em 06/09/2026 (primeira/última entrada de cada um), não só
    deduzido do código."""
    achados = []
    for nome in os.listdir(REPO):
        m = FRIO_NOME.match(nome)
        if not m:
            continue
        data, seq_str, com_migrado = m.groups()
        seq = 0 if com_migrado else int(seq_str or 1)
        achados.append((data, seq, nome))
    achados.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [nome for _, _, nome in achados]


def abortar(msg):
    print(f"ABORTADO: {msg}", file=sys.stderr)
    sys.exit(1)


def carimbo():
    sha = os.environ.get("AGATA_CANON_SHA")
    data = os.environ.get("AGATA_CANON_DATA")
    if not sha:
        sha = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
    if not data:
        data = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%cI"],
                              capture_output=True, text=True).stdout.strip()
    if not sha:
        abortar("sem AGATA_CANON_SHA e sem git -- não dá pra carimbar.")
    return sha, (data or "(data indisponível)")


def linhas_titulo_camada_moderna(texto, exige_marcador):
    """As linhas de título das entradas modernas de UMA camada, na ordem do
    arquivo (mais recente primeiro, desde MEMÓRIAS (271)). Quente/morno
    exigem o marcador ENTRADAS-NOVAS e cortam no bloco migrado -- lá esse
    heading marca sempre o FIM físico do corpo moderno, com o bloco antigo
    depois dele.

    Um chunk frio não tem marcador (é congelado, já veio pronto da
    migração) -- e NÃO corta em FIM_MODERNO: achado testando de verdade,
    `MEMORIAS-FRIO-*-com-migrado.md` tem esse mesmo heading perto do TOPO do
    arquivo (ele rotula o bloco migrado que fica logo depois), com entradas
    numeradas modernas espalhadas ANTES E DEPOIS dele -- cortar ali
    descartaria quase todo o conteúdo moderno do chunk. Lido inteiro, o
    CAB_ENTRADA simplesmente não bate nas linhas do formato antigo ("### data
    (n)") do bloco migrado, que ficam de fora sem precisar de corte
    explícito."""
    if exige_marcador:
        ini = texto.find(MARCADOR)
        if ini == -1:
            abortar("marcador ENTRADAS-NOVAS não achado numa camada quente/morno.")
        corpo = texto[texto.find("\n", ini) + 1:]
        m = FIM_MODERNO.search(corpo)
        if m:
            corpo = corpo[:m.start()]
    else:
        corpo = texto
    return [ln for ln in corpo.split("\n") if CAB_ENTRADA.match(ln)]


def main():
    # 1. conjunto de entrada fixo: REGRAS/PROJETO + quente, cada um filha
    # direta da raiz do repo -- mais as camadas extra de memória (morno, se
    # existir, e todo chunk frio achado no disco), sob a mesma checagem.
    def validar_filha_direta(nome, p):
        if os.path.dirname(os.path.realpath(p)) != os.path.realpath(REPO):
            abortar(f"fonte {nome} não é filha direta da raiz do repo.")
        if PROIBIDO in os.path.realpath(p):
            abortar(f"fonte {nome} resolve para dentro de {PROIBIDO}/ -- proibido.")

    caminhos = {}
    for nome in FONTES:
        p = os.path.join(REPO, nome)
        validar_filha_direta(nome, p)
        if not os.path.isfile(p):
            abortar(f"fonte ausente: {p}")
        caminhos[nome] = p

    regras = open(caminhos["REGRAS.md"], encoding="utf-8").read()
    projeto = open(caminhos["PROJETO.md"], encoding="utf-8").read()
    mem_txt = open(caminhos["MEMÓRIAS.md"], encoding="utf-8").read()

    # Camadas extra de memória (Fase 4, MEMÓRIAS (357)): morno + frio, mais
    # recente primeiro. Ausência de morno é normal logo após uma migração
    # (pode nascer vazio) -- não é erro, só não entra.
    camadas_extra_nomes = []
    if os.path.isfile(os.path.join(REPO, "MEMORIAS-MORNO.md")):
        camadas_extra_nomes.append("MEMORIAS-MORNO.md")
    camadas_extra_nomes.extend(camadas_frio_recente_primeiro())

    camadas_extra_txt = {}
    for nome in camadas_extra_nomes:
        p = os.path.join(REPO, nome)
        validar_filha_direta(nome, p)
        camadas_extra_txt[nome] = open(p, encoding="utf-8").read()

    sha, data = carimbo()
    titulos = linhas_titulo_camada_moderna(mem_txt, exige_marcador=True)
    for nome in camadas_extra_nomes:
        exige = (nome == "MEMORIAS-MORNO.md")
        titulos += linhas_titulo_camada_moderna(camadas_extra_txt[nome], exige_marcador=exige)

    fontes_citadas = ", ".join(("REGRAS.md", "PROJETO.md", "MEMÓRIAS.md") + tuple(camadas_extra_nomes))
    header = (
        "---\n"
        f"gerado-de: canon público do sistema Agata ({fontes_citadas})\n"
        f"canon: {sha}\n"
        f"data: {data}\n"
        "nota: camada de leitura derivada, só-leitura. Não é canon. "
        "Correção é entrada nova em MEMÓRIAS, nunca edição aqui.\n"
        "---\n\n"
        "# Índice derivado — canon público do Agata\n\n"
        "Mapa para consulta externa. Três partes: as regras na íntegra, o estado\n"
        "atual na íntegra, e a linha do tempo das entradas de memória -- quente +\n"
        "morno + frio (Fase 4) -- (só os\n"
        f"títulos). Gerado do commit `{sha}` ({data}). Hashes em `manifesto.md`.\n"
    )
    parte3_cab = (
        "## PARTE 3 — MEMÓRIAS (linha do tempo, quente+morno+frio, só títulos, mais recente primeiro)\n"
        f"{len(titulos)} entradas.\n\n"
    )
    indice = (
        header
        + SEP + "## PARTE 1 — REGRAS.md (íntegra)\n\n" + regras
        + SEP + "## PARTE 2 — PROJETO.md (íntegra)\n\n" + projeto
        + SEP + parte3_cab + "\n".join(titulos) + "\n"
    )

    # --- verificação antes de gravar
    if regras not in indice:
        abortar("REGRAS.md não aparece verbatim no índice.")
    if projeto not in indice:
        abortar("PROJETO.md não aparece verbatim no índice.")
    linhas_mem = set(mem_txt.split("\n"))
    for txt_extra in camadas_extra_txt.values():
        linhas_mem |= set(txt_extra.split("\n"))
    for t in titulos:
        if t not in linhas_mem:
            abortar(f"linha de título não é verbatim de nenhuma camada de memória lida: {t[:60]}")
    reconstruido = (
        header
        + SEP + "## PARTE 1 — REGRAS.md (íntegra)\n\n" + regras
        + SEP + "## PARTE 2 — PROJETO.md (íntegra)\n\n" + projeto
        + SEP + parte3_cab + "\n".join(titulos) + "\n"
    )
    if indice != reconstruido:
        abortar("reconstrução byte a byte falhou -- há conteúdo fora de HEADER+canon.")

    def h(s):
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    linhas_fontes = [f"  REGRAS.md    {h(regras)}\n", f"  PROJETO.md   {h(projeto)}\n",
                     f"  MEMÓRIAS.md  {h(mem_txt)}\n"]
    for nome in camadas_extra_nomes:
        linhas_fontes.append(f"  {nome}  {h(camadas_extra_txt[nome])}\n")
    manifesto = (
        "---\n"
        "tipo: manifesto do índice derivado\n"
        f"canon: {sha}\n"
        f"data: {data}\n"
        "---\n\n"
        "# Manifesto — índice derivado do canon público\n\n"
        f"Fontes (sha256, no commit {sha}):\n"
        + "".join(linhas_fontes) + "\n"
        "Saída:\n"
        f"  indice.md    {h(indice)}   (Parte 3: {len(titulos)} linhas de título)\n\n"
        "Regenerar: python3 scripts/gerar_indice_derivado.py\n"
        "Conferir : sha256sum das fontes acima bate com os valores acima.\n"
    )

    os.makedirs(SAIDA_DIR, exist_ok=True)
    with open(os.path.join(SAIDA_DIR, "indice.md"), "w", encoding="utf-8") as f:
        f.write(indice)
    with open(os.path.join(SAIDA_DIR, "manifesto.md"), "w", encoding="utf-8") as f:
        f.write(manifesto)

    print(f"OK: indice.md ({len(indice)} B, {len(titulos)} títulos) + manifesto.md")
    print(f"    em {SAIDA_DIR}")
    print(f"    canon {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
