#!/usr/bin/env python3
"""Teste de preservação (A2) — roda ANTES de qualquer compressão.

Falha (exit != 0) se algum invariante do ÍNDICE ou do PROJETO cair.
Roda contra os artefatos gerados (INDICE_MEMORIAS.md / PROJETO.md), não
contra o texto original em si -- mas usa MEMÓRIAS.md como fonte de
verdade para checar ponteiros e contagens.

Uso:
  python3 scripts/testar_preservacao.py --alvo indice [--indice PATH] [--memorias PATH]
  python3 scripts/testar_preservacao.py --alvo projeto [--projeto PATH] [--memorias PATH]
  python3 scripts/testar_preservacao.py --alvo indice --projeto ... (roda os dois)

Sem --indice/--projeto: usa os arquivos reais do repo (~/agata/INDICE_MEMORIAS.md,
~/agata/PROJETO.md). Passe caminhos alternativos para testar artefatos
temporários (obrigatório antes de habilitar qualquer gerador novo, ver
ORIENTAÇÃO AO EXECUTOR 14/08/2026, "Salvaguarda obrigatória").
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

PAT_OLD = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2} \([0-9]+\)')
PAT_NEW = re.compile(r'^\([0-9]+\) (DIÁRIO|CONSELHO|MOD[^—]*|CORREÇÃO) — [0-9]{2}/[0-9]{2}/[0-9]{4}')
PAT_MEM_OLD = re.compile(r'^### ([0-9]{4}-[0-9]{2}-[0-9]{2}) \(([0-9]+)\)')
# Padrão ESTREITO: exatamente o que o gerador (.githooks/gerar-hermes-md.sh,
# gerar_indice()) reconhece hoje -- usado só pra testar fidelidade do índice
# ao gerador (item 4 abaixo). Precisa ser mantido em sincronia manual com os
# três `grep`/`awk` do gerador sempre que um rótulo novo for reconhecido lá
# -- é assim que a divergência de (161) foi achada, e é a mesma classe de
# lacuna se este padrão ficar pra trás de novo.
PAT_MEM_NEW = re.compile(r'^\(([0-9]+)\) (DIÁRIO|CONSELHO|MOD[^—]*|CORREÇÃO) — ([0-9]{2}/[0-9]{2}/[0-9]{4})')
# Padrão LARGO: qualquer rótulo maiúsculo (DIÁRIO, CONSELHO, MOD..., CORREÇÃO,
# ou um futuro ainda não usado) seguido de travessão e data -- é a verdade
# fundamental de "esta entrada existe em MEMÓRIAS.md", independente de o
# gerador reconhecer o rótulo ou não. Ver achado real: (134) CORREÇÃO fica
# de fora do padrão estreito e por isso nunca chegou ao índice.
PAT_MEM_NEW_LARGO = re.compile(r'^\(([0-9]+)\) ([^—\n]+?) — ([0-9]{2}/[0-9]{2}/[0-9]{4})')


def falha(msgs, texto):
    msgs.append(f"FALHA: {texto}")


def ok(msgs, texto):
    msgs.append(f"ok: {texto}")


def entradas_memorias(memorias_text: str, largo: bool = False):
    """Retorna lista de (numero:int, data:str, linha_original:str) na ordem do arquivo.

    largo=False (default): exatamente os padrões que o gerador reconhece hoje
      (usado para testar fidelidade índice<->gerador).
    largo=True: padrão largo de rótulo, verdade fundamental de "a entrada existe"
      (usado para checar completude do índice e validade de ponteiros)."""
    pat_new = PAT_MEM_NEW_LARGO if largo else PAT_MEM_NEW
    entradas = []
    for line in memorias_text.split("\n"):
        m = PAT_MEM_OLD.match(line)
        if m:
            entradas.append((int(m.group(2)), m.group(1), line))
            continue
        m = pat_new.match(line)
        if m:
            entradas.append((int(m.group(1)), m.group(3), line))
    return entradas


def testar_indice(indice_path: Path, memorias_path: Path) -> tuple[bool, list[str]]:
    msgs = []
    passou = True
    indice_text = indice_path.read_text(encoding="utf-8")
    memorias_text = memorias_path.read_text(encoding="utf-8")

    linhas_indice = [l for l in indice_text.split("\n") if l.strip()]
    # descarta cabeçalho: comentário GERADO, título, linha em branco, linha de explicação
    linhas_entrada = [l for l in linhas_indice if PAT_OLD.match(l) or PAT_NEW.match(l)]

    # Verdade fundamental: padrão LARGO (qualquer rótulo maiúsculo), não o
    # padrão estreito que o próprio gerador usa -- testar contra o padrão do
    # gerador seria usar a implementação como seu próprio oráculo, cego a
    # bugs do gerador por desenho.
    entradas_mem = entradas_memorias(memorias_text, largo=True)
    entradas_mem_estreito = entradas_memorias(memorias_text, largo=False)

    # 0. o padrão estreito do gerador reconhece todo rótulo real usado em MEMÓRIAS.md?
    numeros_largo = {n for n, _, _ in entradas_mem}
    numeros_estreito = {n for n, _, _ in entradas_mem_estreito}
    so_no_largo = numeros_largo - numeros_estreito
    if so_no_largo:
        passou = False
        rotulos = []
        for n, data, linha in entradas_mem:
            if n in so_no_largo:
                rotulo = linha.split("—")[0].split(")", 1)[1].strip()
                rotulos.append(f"({n}) rótulo '{rotulo}'")
        falha(msgs, f"gerador (.githooks/gerar-hermes-md.sh, gerar_indice()) usa um padrão "
                     f"estreito (DIÁRIO|CONSELHO|MOD) que NÃO reconhece {len(so_no_largo)} "
                     f"entrada(s) real(is) de MEMÓRIAS.md, por isso elas nunca chegam ao "
                     f"índice: {', '.join(sorted(rotulos))}. Achado real, pré-existente a "
                     f"esta rodada -- não é falha de calibração do teste.")
    else:
        ok(msgs, "padrão de reconhecimento do gerador cobre todo rótulo real usado em MEMÓRIAS.md")

    # 1. nenhuma entrada desaparecida: contagem bate (contra a verdade fundamental)
    if len(linhas_entrada) != len(entradas_mem):
        passou = False
        falha(msgs, f"contagem diverge: índice tem {len(linhas_entrada)} linhas de entrada, "
                     f"MEMÓRIAS.md tem {len(entradas_mem)} entrada(s) real(is) "
                     f"(contando pelo padrão largo, verdade fundamental)")
    else:
        ok(msgs, f"contagem bate: {len(linhas_entrada)} entradas em ambos")

    # 2. todo número de entrada presente + toda data presente
    numeros_indice_old = set()
    for l in linhas_indice:
        m = PAT_OLD.match(l)
        if m:
            numeros_indice_old.add((l[:10], re.search(r'\(([0-9]+)\)', l).group(1)))
    numeros_indice_new = set()
    for l in linhas_indice:
        m = PAT_NEW.match(l)
        if m:
            n = re.match(r'^\(([0-9]+)\)', l).group(1)
            data = re.search(r'— ([0-9]{2}/[0-9]{2}/[0-9]{4})', l).group(1)
            numeros_indice_new.add((n, data))

    faltando = []
    for numero, data, linha_orig in entradas_mem:
        if PAT_MEM_OLD.match(linha_orig):
            chave = (data, str(numero))
            if chave not in numeros_indice_old:
                faltando.append(f"formato antigo {data} ({numero})")
        else:
            # data em MEMÓRIAS pattern novo já vem DD/MM/YYYY
            chave = (str(numero), data)
            if chave not in numeros_indice_new:
                faltando.append(f"formato novo ({numero}) {data}")
    if faltando:
        passou = False
        falha(msgs, f"{len(faltando)} entrada(s) de MEMÓRIAS sem linha correspondente no índice: "
                     + "; ".join(faltando[:10]) + (" ..." if len(faltando) > 10 else ""))
    else:
        ok(msgs, "todo número de entrada + toda data de MEMÓRIAS.md está presente no índice")

    # 3. toda linha compactada aponta para a fonte completa (o número é a âncora buscável)
    sem_numero = [l for l in linhas_entrada if not re.search(r'\([0-9]+\)', l)]
    if sem_numero:
        passou = False
        falha(msgs, f"{len(sem_numero)} linha(s) do índice sem número de entrada buscável")
    else:
        ok(msgs, "toda linha do índice carrega um número de entrada buscável")

    # 4. o gerador continua sendo a fonte exclusiva -- regenera e diffa
    gerador = REPO / ".githooks" / "gerar-hermes-md.sh"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # roda gerar_indice() isolado, reimplementando a extração aqui seria duplicação
        # arriscada; em vez disso chama o script real com OUT/INDICE redirecionados
        # via cópia do repo inteiro é caro -- usa symlinks pros arquivos-fonte fixos e
        # escreve o índice gerado em tmp, comparando só o índice.
        script_text = gerador.read_text(encoding="utf-8")
        # extrai só a função gerar_indice + chamada, rodando num subshell com INDICE
        # apontando pro tmp e cwd = repo (mesma leitura de MEMÓRIAS.md)
        sh = f'''
set -euo pipefail
cd "{REPO}"
INDICE="{tmp}/indice_regenerado.md"
{script_text[script_text.index('gerar_indice() {'):script_text.index('janela_memorias()')]}
gerar_indice
'''
        proc = subprocess.run(["bash", "-c", sh], capture_output=True, text=True)
        if proc.returncode != 0:
            passou = False
            falha(msgs, f"não foi possível regenerar o índice pra comparação: {proc.stderr.strip()}")
        else:
            regenerado = (tmp / "indice_regenerado.md").read_text(encoding="utf-8")
            if regenerado != indice_text:
                passou = False
                falha(msgs, "índice atual DIVERGE do que o gerador produziria agora -- "
                             "ou houve edição manual, ou MEMÓRIAS.md mudou sem regenerar")
            else:
                ok(msgs, "índice atual é byte-a-byte igual ao que o gerador produz agora "
                          "(gerador confirmado como fonte exclusiva)")

    return passou, msgs


def entradas_validas_memorias(memorias_text: str) -> set[int]:
    # largo=True: "esta entrada existe" não depende do gerador reconhecer o
    # rótulo (ver achado (134) CORREÇÃO em testar_indice).
    return {n for n, _, _ in entradas_memorias(memorias_text, largo=True)}


def numeros_de_lista_enumerada(linha: str) -> set[int]:
    """Marcadores tipo '(1) X, ou (2) Y' não são ponteiros de MEMÓRIAS --
    são listas enumeradas inline. Heurística: sequência (1)(2)[(3)...] na
    mesma linha, começando em 1, cada um incrementando exatamente +1."""
    nums = [int(n) for n in re.findall(r'\(([0-9]+)\)', linha)]
    if not nums or nums[0] != 1:
        return set()
    seq = [1]
    for n in nums[1:]:
        if n == seq[-1] + 1:
            seq.append(n)
        elif n in seq:
            continue  # repetição do mesmo marcador na linha, ignora
        else:
            break
    return set(seq) if len(seq) >= 2 else set()


def testar_projeto(projeto_path: Path, memorias_path: Path) -> tuple[bool, list[str]]:
    msgs = []
    passou = True
    texto = projeto_path.read_text(encoding="utf-8")
    memorias_text = memorias_path.read_text(encoding="utf-8")
    validos = entradas_validas_memorias(memorias_text)
    max_valido = max(validos) if validos else 0

    # 1. toda fase identificável
    m = re.search(r'^## Plano vigente.*$', texto, re.MULTILINE)
    fases = re.findall(r'\*\*Fase (\d+)', texto)
    if not m or not fases:
        passou = False
        falha(msgs, "seção de fases não encontrada ou sem nenhuma 'Fase N' identificável")
    else:
        ok(msgs, f"{len(fases)} fase(s) identificável(is) em '## Plano vigente'")

    # 2. estado atual identificável
    secoes_estado = ["## Estado de publicação", "## Estado dos bugs e dos testes", "## Diagnóstico"]
    achadas = [s for s in secoes_estado if s in texto]
    if not achadas:
        passou = False
        falha(msgs, "nenhuma seção de estado atual encontrada (Estado de publicação / "
                     "Estado dos bugs e dos testes / Diagnóstico)")
    else:
        ok(msgs, f"estado atual identificável via: {', '.join(achadas)}")

    # 3. todo ponteiro histórico válido
    # captura grupos tipo (n), (n)-(m), (n)/(m), (n)-(m)-(o) etc: um grupo com mais de
    # um número (faixa/lista de MEMÓRIAS) é considerado ancorado se PELO MENOS UM dos
    # números resolve pra entrada real -- faixas como "(1)-(62)" citam um marco
    # fundacional/histórico (ver PROJETO.md "Âncora de integridade"); o extremo baixo
    # pode não ter cabeçalho próprio sem que a citação esteja quebrada.
    PAT_GRUPO = re.compile(r'\([0-9]+\)(?:[-/]\([0-9]+\))*')
    invalidos_reais = []
    fora_de_faixa_suspeitos = []
    listas_descartadas = []
    for linha in texto.split("\n"):
        marcadores_lista = numeros_de_lista_enumerada(linha)
        if marcadores_lista:
            listas_descartadas.append((linha.strip()[:60], sorted(marcadores_lista)))
        for grupo in PAT_GRUPO.findall(linha):
            nums = [int(x) for x in re.findall(r'[0-9]+', grupo)]
            nums = [n for n in nums if n not in marcadores_lista]
            if not nums:
                continue
            if any(n in validos for n in nums):
                continue  # grupo ancorado por pelo menos um número real
            # nenhum número do grupo resolve -- heurística: número muito maior que o
            # topo do canon não é ponteiro de MEMÓRIAS (ex.: "porta 8642").
            suspeitos = [n for n in nums if n > max_valido + 5]
            reais = [n for n in nums if n <= max_valido + 5]
            fora_de_faixa_suspeitos.extend(suspeitos)
            invalidos_reais.extend(reais)
    if listas_descartadas:
        ok(msgs, f"(informativo) {len(listas_descartadas)} lista(s) enumerada(s) inline "
                  f"descartada(s) do check de ponteiro (ex: {listas_descartadas[0][0]!r})")
    if invalidos_reais:
        passou = False
        falha(msgs, f"ponteiro(s) para MEMÓRIAS que não existem (dentro da faixa plausível "
                     f"1..{max_valido}): {sorted(set(invalidos_reais))}")
    else:
        ok(msgs, f"todo ponteiro histórico dentro da faixa 1..{max_valido} existe em MEMÓRIAS.md")
    if fora_de_faixa_suspeitos:
        ok(msgs, f"(informativo, não é falha) número(s) entre parênteses fora da faixa de "
                  f"entradas — provavelmente não são ponteiros de MEMÓRIAS (ex: porta de rede): "
                  f"{sorted(set(fora_de_faixa_suspeitos))}")

    # 4. todo item fechado mantém o veredito, não só o tema
    # heurística: parágrafo com palavra de fechamento + ponteiro de MEMÓRIAS deve ter
    # prosa substantiva ao redor, não só a tag.
    palavras_fechamento = r'(fechad[oa]|resolvid[oa]|conclu[íi]d[oa]|corrigid[oa]|testado e verificado)'
    paragrafos = re.split(r'\n\s*\n', texto)
    rasos = []
    total_fechados = 0
    for p in paragrafos:
        if re.search(palavras_fechamento, p, re.IGNORECASE) and re.search(r'\([0-9]+\)', p):
            total_fechados += 1
            if len(p.strip()) < 60:
                rasos.append(p.strip()[:80])
    if rasos:
        passou = False
        falha(msgs, f"{len(rasos)} item(ns) fechado(s) sem veredito substantivo (só tag curta): "
                     + "; ".join(rasos))
    else:
        ok(msgs, f"{total_fechados} parágrafo(s) fechado(s) com veredito substantivo preservado")

    return passou, msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alvo", choices=["indice", "projeto", "ambos"], default="ambos")
    ap.add_argument("--indice", default=str(REPO / "INDICE_MEMORIAS.md"))
    ap.add_argument("--projeto", default=str(REPO / "PROJETO.md"))
    ap.add_argument("--memorias", default=str(REPO / "MEMÓRIAS.md"))
    args = ap.parse_args()

    memorias_path = Path(args.memorias)
    tudo_ok = True

    if args.alvo in ("indice", "ambos"):
        print("=== ÍNDICE ===")
        passou, msgs = testar_indice(Path(args.indice), memorias_path)
        for m in msgs:
            print(" ", m)
        print("RESULTADO ÍNDICE:", "PASSOU" if passou else "FALHOU")
        tudo_ok = tudo_ok and passou

    if args.alvo in ("projeto", "ambos"):
        print("=== PROJETO ===")
        passou, msgs = testar_projeto(Path(args.projeto), memorias_path)
        for m in msgs:
            print(" ", m)
        print("RESULTADO PROJETO:", "PASSOU" if passou else "FALHOU")
        tudo_ok = tudo_ok and passou

    sys.exit(0 if tudo_ok else 1)


if __name__ == "__main__":
    main()
