#!/usr/bin/env python3
"""Busca semântica sobre MEMÓRIAS — complementar ao grep/índice-primeiro, nunca
substituto. Usa o endpoint local de embeddings (:20134, multilingual-e5-small
na iGPU Intel, já em produção desde a Fase 2) — zero nuvem, zero custo, zero
dado saindo desta Máquina.

**Por que existe apesar da recusa de (115)/(293):** aquela recusa foi sobre
vetor como CAMADA PRIMÁRIA de memória (o que veio a ser a hidratação por
janela + grep + query_canon, e continua sendo). Isto aqui é diferente: uma
ferramenta SECUNDÁRIA, sob demanda, nunca injetada em hidratação nenhuma,
pra achar entradas parecidas em SENTIDO quando a palavra exata não bate —
caso que grep estruturalmente não cobre. Autorizado pelo Humano em
04/09/2026 ("Eu assumo o risco por escrito, implemente") depois de pergunta
direta sobre o porquê da recusa original — ver MEMÓRIAS (324)/(327).

**Achado relevante, não escondido:** o spike RLM (P5-01, arquivado em
extras/arquivo-redesign/rlm/ na sanitização de (368), originalmente
redesign/rlm/, 02/09/2026) testou embedding como FALLBACK de busca dentro do loop de
consulta e mediu resultado pior que grep puro (3/13 limpo vs 9/14 da
injeção) — mas aquele teste usava embedding DENTRO do loop de raciocínio do
modelo, tentando substituir grep. Este script é outra forma: um ranking
oferecido ao HUMANO ou a um modelo que já decidiu buscar por tema, não uma
sub-chamada dentro do laço de decisão do modelo. Formas diferentes, uma
mediu mal, a outra ainda não foi medida — declarado, não inferido.

**Índice nunca fica obsoleto sem avisar** (o segundo motivo de (115)):
grava o hash de MEMÓRIAS.md junto do índice; se o canon mudou desde o
último `--reindex`, toda busca imprime um aviso antes do resultado.

Índice fica em ~/.cache/agata/busca_semantica/ — fora do repo, fora do
vault, nunca commitado, regenerado sob demanda (não a cada commit; indexar
~275 entradas na iGPU custa segundos reais, não cabe no hot path do hook).

Desde (670): índice v2, INCREMENTAL, por entrada e por parágrafo (`indice-v2.json`,
vetor guardado pela sha256 do texto) -- só o texto novo vai ao embedding. O
post-commit roda `--atualizar` antes de gerar o vault; a busca se atualiza sozinha.
O `memorias.json` antigo fica sem uso.

Uso:
  scripts/busca_semantica.py --atualizar          # embeda só o que falta
  scripts/busca_semantica.py --reindex            # idem + poda o que não existe mais
  scripts/busca_semantica.py "frase ou termo"     # top 10 entradas e trechos por sentido
  scripts/busca_semantica.py "termo" --json       # para ferramentas (seth_verificador)
  scripts/busca_semantica.py "tema" --contexto ARQ.md   # pacote p/ colar noutra IA
  scripts/busca_semantica.py "termo" -n 5         # top 5
  scripts/busca_semantica.py --selftest           # autoteste, sem tocar o índice real
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORIAS = os.path.join(REPO, "MEMÓRIAS.md")
MORNO = os.path.join(REPO, "MEMORIAS-MORNO.md")
FRIO_DIR = os.path.join(REPO, "memoria", "frio")
EMBED_URL = os.environ.get("AGATA_EMBED_URL", "http://127.0.0.1:20134/embed")
CACHE_DIR = os.environ.get(
    "AGATA_BUSCA_CACHE", os.path.expanduser("~/.cache/agata/busca_semantica")
)
VETORES_PATH = os.path.join(CACHE_DIR, "memorias.json")
MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI"
FIM_MODERNO = re.compile(r"^## Migrado de DIÁRIO\.md", re.M)
CAB_ENTRADA = re.compile(
    r"^\((\d+)\)\s+([A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ]+(?:\+[A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ]+)*(?:\s+[A-Za-zÁÂÃÀÉÊÍÓÔÕÚÜÇçãõ0-9.\-]+)?)\s+[—-]\s+(.*)$"
)
FRIO_NOME = re.compile(
    r"^MEMORIAS-FRIO-(\d{4}-\d{2}-\d{2})(?:-(\d+))?(-com-migrado)?\.md$"
)


def _camadas_frio_recente_primeiro():
    """Mesma regra de ordem de scripts/gerar_indice_derivado.py e
    .githooks/gerar-hidratacao.sh (Fase 4, MEMÓRIAS (357)): mais recente
    primeiro é maior sufixo primeiro, depois sem sufixo, depois
    "-com-migrado"; datas mais recentes primeiro entre dias distintos.
    Moradia mudou de raiz do repo para memoria/frio/ em 25/09/2026."""
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
    return [os.path.join(FRIO_DIR, nome) for _, _, nome in achados]


def _parse_entradas_bloco(corpo):
    """Quebra um corpo de texto (já recortado pra ficar só no formato
    moderno) em entradas -- núcleo compartilhado por camada com/sem marcador."""
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


def _parse_entradas(texto):
    """Camada quente (MEMÓRIAS.md) -- exige o marcador, corta no bloco
    migrado, se ainda estiver ali."""
    ini = texto.find(MARCADOR)
    if ini == -1:
        sys.exit("ERRO: marcador ENTRADAS-NOVAS não achado em MEMÓRIAS.md.")
    corpo = texto[texto.find("\n", ini) + 1:]
    m = FIM_MODERNO.search(corpo)
    if m:
        corpo = corpo[:m.start()]
    return _parse_entradas_bloco(corpo)


def _parse_entradas_morno(texto):
    """Camada morna (MEMORIAS-MORNO.md) -- mesma disciplina de quente."""
    ini = texto.find(MARCADOR)
    if ini == -1:
        sys.exit("ERRO: marcador ENTRADAS-NOVAS não achado em MEMORIAS-MORNO.md.")
    corpo = texto[texto.find("\n", ini) + 1:]
    m = FIM_MODERNO.search(corpo)
    if m:
        corpo = corpo[:m.start()]
    return _parse_entradas_bloco(corpo)


def _parse_entradas_frio(texto):
    """Um chunk frio não tem marcador (já vem congelado) e NÃO corta em
    FIM_MODERNO: achado testando de verdade (mesmo achado registrado em
    gerar_indice_derivado.py) -- MEMORIAS-FRIO-*-com-migrado.md tem o
    heading "## Migrado de DIÁRIO.md" perto do TOPO do arquivo, com entradas
    modernas espalhadas antes e depois dele; cortar ali descartaria quase
    todo o conteúdo moderno do chunk. Lido inteiro, CAB_ENTRADA não bate no
    formato antigo ("### data (n)") do bloco migrado."""
    return _parse_entradas_bloco(texto)


def _todas_entradas_todas_camadas():
    """Quente + morno (se existir) + frio (mais recente primeiro), mesma
    ordem/regra de gerar_indice_derivado.py e gerar-hidratacao.sh (Fase 4,
    MEMÓRIAS (357)). Devolve (entradas, {caminho: texto})."""
    textos = {MEMORIAS: open(MEMORIAS, encoding="utf-8").read()}
    entradas = list(_parse_entradas(textos[MEMORIAS]))
    if os.path.isfile(MORNO):
        textos[MORNO] = open(MORNO, encoding="utf-8").read()
        entradas += _parse_entradas_morno(textos[MORNO])
    for caminho in _camadas_frio_recente_primeiro():
        textos[caminho] = open(caminho, encoding="utf-8").read()
        entradas += _parse_entradas_frio(textos[caminho])
    return entradas, textos


def _hash_camadas(textos):
    """Hash combinado, independente da ordem de iteração, das camadas de
    memória lidas -- detecta índice desatualizado sem depender só de
    MEMÓRIAS.md (Fase 4: mudança em morno/frio também invalida o índice)."""
    h = hashlib.sha256()
    for caminho in sorted(textos):
        h.update(os.path.basename(caminho).encode("utf-8"))
        h.update(textos[caminho].encode("utf-8"))
    return h.hexdigest()


def _embed(textos, input_type):
    payload = json.dumps({"input": textos, "input_type": input_type}).encode()
    req = urllib.request.Request(
        EMBED_URL, data=payload, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())
    except urllib.error.URLError as e:
        sys.exit(
            f"ERRO: não consegui falar com o servidor de embeddings ({EMBED_URL}): {e}\n"
            "O que fazer: 'systemctl --user status openvino-embeddings.service' — "
            "serviço sob demanda (agata.target), sobe com 'agata up' ou 'systemctl --user start'."
        )
    return [d["embedding"] for d in sorted(body["data"], key=lambda d: d["index"])]


# ---------------------------------------------------------------- índice v2
# (670): índice incremental, por ENTRADA e por BLOCO (parágrafo, mesma
# segmentação de scripts/agata_blocos.py que o vault usa pra marcar `^bN`).
# Cada vetor é guardado pela sha256 do texto que o gerou -- texto que já tem
# vetor nunca vai de novo ao embedding; só o novo ou alterado. Sem timer: a
# reindexação roda no post-commit (antes do vault) e, se estiver atrasada, na
# própria busca. O vault (gerar_obsidian.py) só LÊ este índice.
INDICE_V2 = os.path.join(CACHE_DIR, "indice-v2.json")
MODELO = "multilingual-e5-small"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agata_blocos  # noqa: E402


def texto_entrada(e):
    return f"{e['titulo']}\n\n" + "\n".join(e["linhas"]).strip()[:2000]


def textos_blocos(e):
    """[(n, texto)] -- n é o mesmo `^bN` que o vault escreve na nota."""
    return [(n, t[:1500]) for n, _i, _f, t in agata_blocos.blocos(e["linhas"])]


def _h(texto):
    return hashlib.sha256(("passage\0" + texto).encode("utf-8")).hexdigest()


def _b64(vetor):
    import base64
    import numpy as np
    return base64.b64encode(np.asarray(vetor, dtype="<f4").tobytes()).decode()


def carregar_indice():
    """{sha: base64-float32}, ou {} se não houver índice v2."""
    try:
        with open(INDICE_V2, encoding="utf-8") as f:
            d = json.load(f)
        return d.get("vetores", {}) if d.get("versao") == 2 else {}
    except (OSError, ValueError):
        return {}


def vetor(vetores, texto):
    """numpy float32 do texto, ou None se ainda não indexado."""
    v = vetores.get(_h(texto))
    if v is None:
        return None
    import base64
    import numpy as np
    return np.frombuffer(base64.b64decode(v), dtype="<f4")


def _itens(entradas):
    """[(sha, texto)] de todas as entradas e blocos, sem repetição."""
    vistos, out = set(), []
    for e in entradas:
        for t in [texto_entrada(e)] + [t for _n, t in textos_blocos(e)]:
            h = _h(t)
            if h not in vistos:
                vistos.add(h)
                out.append((h, t))
    return out


def _embed_seguro(textos):
    try:
        return _embed(textos, "passage")
    except SystemExit:
        return None


def atualizar(podar=False, silencioso=False):
    """Embeda só o que falta. Devolve (novos, total, ok). `podar` remove
    vetores de texto que não existe mais (só no --reindex explícito: a busca
    não poda, pra nunca tirar o vetor de uma entrada do HEAD que o vault usa)."""
    entradas, _ = _todas_entradas_todas_camadas()
    vetores = carregar_indice()
    itens = _itens(entradas)
    faltam = [(h, t) for h, t in itens if h not in vetores]
    ok = True
    LOTE = 32
    for i in range(0, len(faltam), LOTE):
        lote = faltam[i:i + LOTE]
        vs = _embed_seguro([t for _h2, t in lote])
        if vs is None:
            ok = False
            print("AVISO: embedding (:20134) fora do ar -- índice parcial; a busca usa o que já tem.",
                  file=sys.stderr)
            break
        for (h, _t), v in zip(lote, vs):
            vetores[h] = _b64(v)
        if not silencioso and len(faltam) > LOTE:
            print(f"  {min(i + LOTE, len(faltam))}/{len(faltam)}", file=sys.stderr)
    if podar:
        validos = {h for h, _t in itens}
        vetores = {h: v for h, v in vetores.items() if h in validos}
    novos = sum(1 for h, _t in faltam if h in vetores)
    if novos or podar:
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp = INDICE_V2 + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"versao": 2, "modelo": MODELO, "vetores": vetores}, f)
        os.replace(tmp, INDICE_V2)
    if not silencioso:
        print(f"índice: {novos} texto(s) novo(s) embedado(s); {len(itens)} no total "
              f"({len(entradas)} entradas + blocos)", file=sys.stderr)
    return novos, len(itens), ok


def buscar_dados(query, n=10, blocos=True):
    """[{tipo, num, bloco, score, titulo, data, trecho}] -- entradas e trechos."""
    import numpy as np
    atualizar(silencioso=True)
    entradas, _ = _todas_entradas_todas_camadas()
    vetores = carregar_indice()
    q = np.asarray(_embed([query], "query")[0], dtype="<f4")
    res = []
    for e in entradas:
        v = vetor(vetores, texto_entrada(e))
        if v is not None:
            res.append({"tipo": "entrada", "num": e["num"], "bloco": None,
                        "score": float(v @ q), "titulo": e["titulo"], "data": e["data"],
                        "trecho": ""})
        if blocos:
            for bn, t in textos_blocos(e):
                v = vetor(vetores, t)
                if v is not None:
                    res.append({"tipo": "trecho", "num": e["num"], "bloco": bn,
                                "score": float(v @ q), "titulo": e["titulo"], "data": e["data"],
                                "trecho": t[:280]})
    res.sort(key=lambda r: r["score"], reverse=True)
    # no máximo um trecho por entrada, pra não encher o topo com a mesma entrada
    out, vistos = [], set()
    for r in res:
        chave = (r["tipo"], r["num"])
        if chave in vistos:
            continue
        vistos.add(chave)
        out.append(r)
        if len(out) >= n:
            break
    return out


def buscar(query, n, como_json=False):
    rs = buscar_dados(query, n)
    if como_json:
        print(json.dumps(rs, ensure_ascii=False))
        return
    for r in rs:
        if r["tipo"] == "entrada":
            print(f"{r['score']:.3f}  ({r['num']}) — {r['titulo'][:140]}")
        else:
            print(f"{r['score']:.3f}  ({r['num']}) ^b{r['bloco']} — {r['trecho'][:140]}")


def contexto(query, n, destino):
    """Pacote markdown com as entradas mais relevantes, para colar noutra IA
    (equivalente ao "Smart Context")."""
    rs = buscar_dados(query, n)
    entradas = {e["num"]: e for e in _todas_entradas_todas_camadas()[0]}
    nums = []
    for r in rs:
        if r["num"] not in nums:
            nums.append(r["num"])
    linhas = [f"# Contexto Agata — \"{query}\"", "",
              "Entradas de MEMÓRIAS escolhidas por sentido (busca local, embedding na iGPU). "
              "A fonte da verdade é o canon; isto é recorte.", ""]
    for num in nums:
        e = entradas[num]
        linhas += [f"## ({num}) {e['tipo']} — {e['data']} · {e['titulo']}", "",
                   "\n".join(e["linhas"]).strip()[:4000], ""]
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(destino)


def _cos(a, b):
    return sum(x * y for x, y in zip(a, b))


def selftest():
    pares = [
        "a âncora de sha detecta uma versão velha do canon",
        "o detector de defasagem compara o commit local com o remoto",
        "o gato dorme no sofá da sala o dia inteiro",
    ]
    vs = _embed(pares, "query")
    prox, dist = _cos(vs[0], vs[1]), _cos(vs[0], vs[2])
    print(f"cos(próximas)={prox:.4f}  cos(distante)={dist:.4f}")
    ok = prox > dist
    # incremental: o mesmo texto dá a mesma chave; texto novo dá chave nova
    e = {"titulo": "t", "linhas": ["x" * 90, "", "y" * 90]}
    ok = ok and _h(texto_entrada(e)) == _h(texto_entrada(dict(e))) and len(textos_blocos(e)) == 2
    print("OK" if ok else "FALHA", "-- sentido + chaves do índice incremental")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?", help="termo ou frase pra buscar por sentido")
    ap.add_argument("--reindex", action="store_true",
                    help="embeda o que falta e poda o que não existe mais (incremental)")
    ap.add_argument("--atualizar", action="store_true",
                    help="só embeda o que falta, sem podar (o post-commit usa este)")
    ap.add_argument("--selftest", action="store_true", help="autoteste, não toca o índice real")
    ap.add_argument("--json", action="store_true", help="saída em JSON (para ferramentas)")
    ap.add_argument("--contexto", metavar="ARQUIVO",
                    help="grava um pacote markdown com as entradas mais relevantes")
    ap.add_argument("-n", type=int, default=10, help="quantos resultados (default 10)")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if args.reindex or args.atualizar:
        _n, _t, ok = atualizar(podar=args.reindex)
        sys.exit(0 if ok else 1)
    if not args.query:
        ap.error("passe uma busca, ou --reindex/--atualizar, ou --selftest")
    n = max(1, min(args.n, 50))
    if args.contexto:
        contexto(args.query, n, args.contexto)
    else:
        buscar(args.query, n, como_json=args.json)


if __name__ == "__main__":
    main()
