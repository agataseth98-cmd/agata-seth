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

**Achado relevante, não escondido:** o spike RLM (P5-01, redesign/rlm/,
02/09/2026) testou embedding como FALLBACK de busca dentro do loop de
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

Uso:
  scripts/busca_semantica.py --reindex            # (re)constrói o índice
  scripts/busca_semantica.py "frase ou termo"     # top 10 entradas por sentido
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
EMBED_URL = os.environ.get("AGATA_EMBED_URL", "http://127.0.0.1:20134/embed")
CACHE_DIR = os.environ.get(
    "AGATA_BUSCA_CACHE", os.path.expanduser("~/.cache/agata/busca_semantica")
)
VETORES_PATH = os.path.join(CACHE_DIR, "memorias.json")
MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI"
FIM_MODERNO = re.compile(r"^## Migrado de DIÁRIO\.md", re.M)
CAB_ENTRADA = re.compile(
    r"^\((\d+)\)\s+([A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ]+(?:\s+[A-Za-zÁÂÃÀÉÊÍÓÔÕÚÜÇçãõ0-9.\-]+)?)\s+[—-]\s+(.*)$"
)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_entradas(texto):
    ini = texto.find(MARCADOR)
    if ini == -1:
        sys.exit("ERRO: marcador ENTRADAS-NOVAS não achado em MEMÓRIAS.md.")
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


def _cos(a, b):
    return sum(x * y for x, y in zip(a, b))


def reindex():
    if not os.path.isfile(MEMORIAS):
        sys.exit("ERRO: MEMÓRIAS.md não encontrado — rode a partir da raiz do repositório.")
    texto = open(MEMORIAS, encoding="utf-8").read()
    entradas = _parse_entradas(texto)
    if not entradas:
        sys.exit("ERRO: nenhuma entrada achada — MEMÓRIAS.md vazio ou marcador quebrado?")
    textos = [
        f"{e['titulo']}\n\n" + "\n".join(e["linhas"]).strip()[:2000]
        for e in entradas
    ]
    print(f"Indexando {len(entradas)} entradas via {EMBED_URL} (iGPU) ...", file=sys.stderr)
    vetores = []
    LOTE = 16
    for i in range(0, len(textos), LOTE):
        vetores.extend(_embed(textos[i:i + LOTE], "passage"))
        print(f"  {min(i + LOTE, len(textos))}/{len(textos)}", file=sys.stderr)
    os.makedirs(CACHE_DIR, exist_ok=True)
    payload = {
        "memorias_sha256": _sha256(MEMORIAS),
        "modelo": "multilingual-e5-small",
        "dim": len(vetores[0]) if vetores else 0,
        "entradas": [
            {"num": e["num"], "tipo": e["tipo"], "data": e["data"], "titulo": e["titulo"],
             "vetor": v}
            for e, v in zip(entradas, vetores)
        ],
    }
    with open(VETORES_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"Índice gravado: {VETORES_PATH} ({len(entradas)} entradas, dim {payload['dim']})",
          file=sys.stderr)


def buscar(query, n):
    if not os.path.isfile(VETORES_PATH):
        sys.exit(f"ERRO: índice não existe ainda — rode '{sys.argv[0]} --reindex' primeiro.")
    idx = json.load(open(VETORES_PATH, encoding="utf-8"))
    if os.path.isfile(MEMORIAS) and idx.get("memorias_sha256") != _sha256(MEMORIAS):
        print("AVISO: MEMÓRIAS.md mudou desde o último --reindex — resultado pode estar "
              "desatualizado. Rode --reindex pra atualizar.", file=sys.stderr)
    qvec = _embed([query], "query")[0]
    ranking = sorted(
        idx["entradas"],
        key=lambda e: _cos(qvec, e["vetor"]),
        reverse=True,
    )[:n]
    for e in ranking:
        score = _cos(qvec, e["vetor"])
        print(f"{score:.3f}  ({e['num']}) {e['tipo']} — {e['titulo']}")


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
    print("OK" if ok else "FALHA", "-- frases relacionadas mais parecidas que a não relacionada")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?", help="termo ou frase pra buscar por sentido")
    ap.add_argument("--reindex", action="store_true", help="(re)constrói o índice de MEMÓRIAS")
    ap.add_argument("--selftest", action="store_true", help="autoteste, não toca o índice real")
    ap.add_argument("-n", type=int, default=10, help="quantos resultados (default 10)")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if args.reindex:
        reindex()
        return
    if not args.query:
        ap.error("passe uma busca, ou --reindex, ou --selftest")
    buscar(args.query, args.n)


if __name__ == "__main__":
    main()
