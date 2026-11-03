#!/usr/bin/env python3
"""medir_recuperacao.py -- mede a recuperação da busca por texto do Agata (1 - recall@k, MRR).

Por quê: o vídeo e o estado da arte (Anthropic, Contextual Retrieval, 2024) pedem uma métrica de
recuperação própria; o conjunto de ouro da Seth mede a resposta, não a busca. Aqui o gabarito é
CALCULADO na hora, nunca guardado: para cada nota de `memoria/obsidian/entradas/`, a consulta são as 3
palavras mais raras do corpo (fora do título); o esperado é a própria nota. Isto mede busca por conteúdo
lexical, o caso fácil: paráfrase e busca semântica NÃO estão cobertas (precisam de modelo e do serviço de
embeddings) e saem como "não medido".

Só LÊ o repositório; com --salvar escreve um JSON em AGATA_MEDICOES_DIR (padrão
~/.cache/agata/painel/medicoes). Uso:
  medir_recuperacao.py [--raiz DIR] [--n 40] [--seed 7] [--semantico] [--salvar]     |     --selftest
--semantico mede a busca por sentido (scripts/busca_semantica.py, embeddings locais) com as MESMAS consultas; precisa do
serviço de embeddings no ar, senão sai como não medido. Paráfrase continua não coberta.
Saída: JSON em stdout. Exit 0 = medido; 3 = sem notas para medir.
"""
import json
import os
import random
import re
import sys
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
import busca_texto  # noqa: E402

KS = (1, 5, 10)
CONSULTA_PALAVRAS = 3
MIN_LETRAS = 5
DF_MAX = 5


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _corpo_e_titulo(texto: str) -> tuple[str, str]:
    titulo, corpo = "", texto
    if texto.startswith("---"):
        partes = texto.split("---", 2)
        if len(partes) == 3:
            m = re.search(r"^titulo:\s*(.*)$", partes[1], flags=re.M)
            titulo, corpo = (m.group(1) if m else ""), partes[2]
    corpo = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", corpo)
    return corpo, titulo


def _palavras(t: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", _norm(t)) if len(w) >= MIN_LETRAS and not w.isdigit()}


def casos(raiz: Path, n: int = 40, seed: int = 7) -> list[dict]:
    pasta = raiz / "memoria" / "obsidian" / "entradas"
    notas = sorted(pasta.glob("*.md")) if pasta.is_dir() else []
    docs = {}
    for arq in notas:
        corpo, titulo = _corpo_e_titulo(arq.read_text(encoding="utf-8", errors="replace"))
        docs[arq] = (_palavras(corpo), _palavras(titulo))
    df = {}
    for palavras, _ in docs.values():
        for w in palavras:
            df[w] = df.get(w, 0) + 1
    candidatos = []
    for arq, (palavras, titulo) in docs.items():
        raras = sorted((w for w in palavras - titulo if df[w] <= DF_MAX), key=lambda w: (df[w], w))[:CONSULTA_PALAVRAS]
        if len(raras) == CONSULTA_PALAVRAS:
            candidatos.append({"esperado": arq.relative_to(raiz).as_posix(), "consulta": " ".join(raras)})
    random.Random(seed).shuffle(candidatos)
    return candidatos[:n]


def posicao(consulta: str, esperado: str, raiz: Path) -> int | None:
    achados, _melhor, _ps = busca_texto.buscar(consulta, str(raiz))
    vistos = []
    for _n, rel, _i, _t in achados:
        if rel not in vistos:
            vistos.append(rel)
    return vistos.index(esperado) + 1 if esperado in vistos else None


def posicao_semantica(consulta: str, esperado: str, n: int = 10) -> int | None:
    import busca_semantica
    num = int(Path(esperado).stem)
    vistos = []
    for item in busca_semantica.buscar_dados(consulta, n=n, blocos=False):
        if item.get("tipo") == "entrada" and item.get("num") not in vistos:
            vistos.append(item.get("num"))
    return vistos.index(num) + 1 if num in vistos else None


def _resumo(pos: list, metodo: str, seed: int) -> dict:
    total = len(pos)
    return {"metodo": metodo, "n": total, "seed": seed,
            "recall": {str(k): round(sum(1 for p in pos if p is not None and p <= k) / total, 3) for k in KS},
            "mrr": round(sum(1 / p for p in pos if p) / total, 3),
            "sem_resultado": round(sum(1 for p in pos if p is None) / total, 3),
            "nao_medido": ["consultas por paráfrase"] + ([] if "sentido" in metodo else ["busca por sentido (use --semantico)"]),
            "medido_em": datetime.now().astimezone().isoformat(timespec="seconds")}


def medir_semantico(raiz: Path, n: int = 40, seed: int = 7) -> dict | None:
    lista = casos(raiz, n, seed)
    if not lista:
        return None
    try:
        pos = [posicao_semantica(c["consulta"], c["esperado"]) for c in lista]
    except Exception as exc:  # serviço de embeddings fora do ar ou índice ausente
        print(f"busca semântica indisponível: {str(exc)[:120]}", file=sys.stderr)
        return None
    return _resumo(pos, "busca por sentido (busca_semantica.py, embeddings locais, mesmas consultas lexicais)", seed)


def medir(raiz: Path, n: int = 40, seed: int = 7) -> dict | None:
    lista = casos(raiz, n, seed)
    if not lista:
        return None
    pos = [posicao(c["consulta"], c["esperado"], raiz) for c in lista]
    return _resumo(pos, "busca_texto (léxica, só conteúdo, 3 palavras raras por nota)", seed)


def _salvar(resultado: dict, nome: str = "recuperacao.json") -> Path:
    pasta = Path(os.environ.get("AGATA_MEDICOES_DIR", Path.home() / ".cache" / "agata" / "painel" / "medicoes"))
    pasta.mkdir(parents=True, exist_ok=True, mode=0o700)
    arq = pasta / nome
    arq.write_text(json.dumps(resultado, ensure_ascii=False), encoding="utf-8")
    return arq


def _selftest() -> int:
    falhou = 0
    def conferir(nome, cond):
        nonlocal falhou
        print(("PASS " if cond else "FALHA ") + nome); falhou += 0 if cond else 1
    with tempfile.TemporaryDirectory() as t:
        r = Path(t); pasta = r / "memoria" / "obsidian" / "entradas"; pasta.mkdir(parents=True)
        temas = ["zebrafish", "quokkaland", "plankton", "mandolina", "obsidiana", "turbulencia", "fosforo", "bergamota"]
        for i, tema in enumerate(temas, 1):
            (pasta / f"{i:04d}.md").write_text(
                f'---\ntitulo: "Entrada {i} comum"\n---\n# Entrada {i}\nTexto comum sobre sistema {tema} e outro {tema}x{i} mais {tema}y{i} ainda {tema}z{i}.\n', encoding="utf-8")
        lista = casos(r, 40, 7)
        conferir("gera caso para cada nota com 3 palavras raras", len(lista) == len(temas))
        conferir("o gabarito nunca usa palavra do título", all("entrada" not in c["consulta"] and "comum" not in c["consulta"] for c in lista))
        res = medir(r, 40, 7)
        conferir("corpus sintético: recall@1 = 1,0 e MRR = 1,0", res["recall"]["1"] == 1.0 and res["mrr"] == 1.0)
        conferir("diz o que não mediu", len(res["nao_medido"]) == 2)
        conferir("mesma seed, mesmos casos", casos(r, 5, 3) == casos(r, 5, 3))
        conferir("sem notas devolve None", medir(r / "vazio") is None)
        import types
        falso = types.ModuleType("busca_semantica")
        falso.buscar_dados = lambda q, n=10, blocos=True: [{"tipo": "entrada", "num": 3}, {"tipo": "bloco", "num": 1}, {"tipo": "entrada", "num": 1}]
        sys.modules["busca_semantica"] = falso
        conferir("posição semântica conta só entradas, em ordem", posicao_semantica("x", "memoria/obsidian/entradas/0001.md") == 2 and posicao_semantica("x", "memoria/obsidian/entradas/0009.md") is None)
        ms = medir_semantico(r, 40, 7)
        conferir("medir_semantico usa o mesmo formato e diz que é por sentido", ms is not None and "sentido" in ms["metodo"] and set(ms["recall"]) == {"1", "5", "10"})
        def cai(*a, **k): raise OSError("serviço fora do ar")
        falso.buscar_dados = cai
        conferir("serviço fora do ar devolve None, não número", medir_semantico(r, 40, 7) is None)
        del sys.modules["busca_semantica"]
        os.environ["AGATA_MEDICOES_DIR"] = str(r / "saida")
        conferir("salvar grava o JSON", json.loads(_salvar(res).read_text(encoding="utf-8"))["n"] == len(temas))
    return 1 if falhou else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    def opt(nome, padrao):
        return type(padrao)(argv[argv.index(nome) + 1]) if nome in argv else padrao
    raiz = Path(opt("--raiz", str(RAIZ)))
    semantico = "--semantico" in argv
    resultado = (medir_semantico if semantico else medir)(raiz, opt("--n", 40), opt("--seed", 7))
    if resultado is None:
        print("sem notas em memoria/obsidian/entradas/ ou serviço de embeddings fora do ar: não medido", file=sys.stderr)
        return 3
    if "--salvar" in argv:
        _salvar(resultado, "recuperacao-semantica.json" if semantico else "recuperacao.json")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
