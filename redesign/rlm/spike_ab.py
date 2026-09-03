#!/usr/bin/env python3
"""
P5-01 -- spike A/B: hidratacao por INJECAO vs por CONSULTA, sobre a bancada congelada.

Fronteira de recusas conferida (P5-00): isto e' Recursive Language Models = padrao de
INFERENCIA (corpus alcancado por busca), NAO o "RLM auto-treino" recusado em MEMORIAS (114).
So MEDIR. Nenhuma mudanca de producao, nenhuma decisao de adocao (do Humano -- (186)/(187)).

Bench: memoria/missoes/rlm-3caminhos/ -- congelado desde 14/08/2026.
  bancada.json         16 perguntas (needle / agregacao / veredito / fabricacao) com gabarito/termos_chave
  corpus/              snapshot do canon (MEMORIAS/PROJETO/REGRAS/INDICE_MEMORIAS)
  corpus_b0/hermes_B0.md  a injecao total de entao (~95k, ~24k tok)

Bracos (mesmo modelo qwen3.5:9b @ :11434, temp 0 -- so muda inject vs query):
  A -- injecao: system = hermes_B0.md; 1 chamada por pergunta.
  B -- consulta: sem injecao; o modelo emite `BUSCAR: termo1, termo2` -> grep -n sobre
       corpus/ (o que query_canon faz: busca indexada); `FINAL: <resp>` encerra. Loop <=12.
       Fallback opcional: 2 buscas vazias seguidas -> similaridade via embeddings :20134.

Uso: spike_ab.py [--rodadas 1] [--modelo qwen3.5:9b] [--so-braco A|B] [--limite N]
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BENCH = Path(os.path.expanduser("~/agata/memoria/missoes/rlm-3caminhos"))
CORPUS = BENCH / "corpus"
HERMES_B0 = BENCH / "corpus_b0" / "hermes_B0.md"
OUT = Path(os.path.expanduser("~/agata/redesign/rlm"))
TRACES = OUT / "traces"
OLLAMA = "http://127.0.0.1:11434/api/chat"
EMB = "http://127.0.0.1:20134/embed"
MAX_ITER = 8
MAX_SAIDA = 4000
ARQS = ["MEMÓRIAS.md", "PROJETO.md", "REGRAS.md", "INDICE_MEMORIAS.md"]

SYS_A = ("[teste] Voce recebeu o corpus completo do sistema Agata no contexto. Responda a "
         "pergunta com base nele. NAO invente entrada, numero, arquivo nem citacao. Se a "
         "resposta nao existir no corpus, diga isso. Responda numa linha comecando com "
         "'FINAL: '.")

SYS_B = ("[teste] Voce responde perguntas sobre um corpus do sistema Agata que voce NAO "
         "recebeu. Descubra o que precisa por busca.\n"
         "A cada passo emita UMA linha:\n"
         "  BUSCAR: termo1, termo2      (busca literal nos arquivos do corpus)\n"
         "Voce vera as linhas que casam. Quando souber, emita:\n"
         "  FINAL: <sua resposta>\n"
         "Se a resposta nao existir no corpus, FINAL deve dizer isso. NAO invente entrada, "
         "numero, arquivo nem citacao. NAO afirme o que nao viu numa saida de busca.")


def chamar(modelo, msgs):
    corpo = json.dumps({"model": modelo, "messages": msgs, "stream": False,
                        "options": {"temperature": 0, "num_ctx": 32768}}).encode()
    req = urllib.request.Request(OLLAMA, data=corpo, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    return (d["message"]["content"], d.get("prompt_eval_count", 0) or 0,
            d.get("eval_count", 0) or 0, int((time.time() - t0) * 1000))


def buscar(termos):
    """grep -n literal (a operacao que query_canon faz) sobre corpus/."""
    linhas = []
    for termo in termos[:4]:
        termo = termo.strip()[:80]
        if not termo:
            continue
        for arq in ARQS:
            r = subprocess.run(["grep", "-n", "-F", "-m", "8", termo, str(CORPUS / arq)],
                               capture_output=True, text=True, timeout=15)
            for ln in r.stdout.splitlines()[:8]:
                linhas.append(f"{arq}:{ln}")
    txt = "\n".join(linhas[:60])
    return txt[:MAX_SAIDA] if txt else "(nenhuma linha casou)"


def emb_similar(pergunta):
    """Fallback: top trecho por similaridade (P2-03). Retorna '' se o servico nao responder."""
    try:
        blocos = []
        for arq in ("INDICE_MEMORIAS.md",):
            for i, ch in enumerate((CORPUS / arq).read_text(encoding="utf-8").split("\n\n")):
                if ch.strip():
                    blocos.append(ch.strip()[:500])
        blocos = blocos[:120]
        body = json.dumps({"input": [pergunta] + blocos, "input_type": "query"}).encode()
        req = urllib.request.Request(EMB, data=body, headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            v = json.load(r)["data"]
        import math
        q = v[0]["embedding"]
        def cos(a, b):
            return sum(x * y for x, y in zip(a, b))
        ranked = sorted(range(len(blocos)), key=lambda k: -cos(q, v[k + 1]["embedding"]))
        return "\n---\n".join(blocos[k] for k in ranked[:3])
    except Exception:
        return ""


def braco_A(modelo, q):
    hermes = HERMES_B0.read_text(encoding="utf-8")
    msgs = [{"role": "system", "content": SYS_A + "\n\n=== CORPUS ===\n" + hermes},
            {"role": "user", "content": q["pergunta"]}]
    resp, pin, pout, ms = chamar(modelo, msgs)
    return {"final": resp, "tokens": pin + pout, "ms": ms, "n_chamadas": 1,
            "passos": [{"tipo": "llm", "tokens_in": pin, "tokens_out": pout, "ms": ms}]}


def braco_B(modelo, q):
    msgs = [{"role": "system", "content": SYS_B},
            {"role": "user", "content": q["pergunta"]}]
    passos, tok, ms_tot, vazias, usou_emb = [], 0, 0, 0, False
    for _ in range(MAX_ITER):
        resp, pin, pout, ms = chamar(modelo, msgs)
        tok += pin + pout
        ms_tot += ms
        passos.append({"tipo": "llm", "saida": resp[:400], "tokens_in": pin, "tokens_out": pout, "ms": ms})
        m_final = re.search(r"FINAL:\s*(.+)", resp, re.S)
        if m_final:
            return {"final": m_final.group(1).strip(), "tokens": tok, "ms": ms_tot,
                    "n_chamadas": len([p for p in passos if p["tipo"] == "llm"]),
                    "usou_embeddings": usou_emb, "passos": passos}
        m_b = re.search(r"BUSCAR:\s*(.+)", resp)
        if not m_b:
            msgs.append({"role": "assistant", "content": resp})
            msgs.append({"role": "user", "content": "Emita BUSCAR: <termos> ou FINAL: <resposta>."})
            continue
        termos = [t.strip() for t in m_b.group(1).split(",")]
        saida = buscar(termos)
        if saida == "(nenhuma linha casou)":
            vazias += 1
            if vazias >= 2:
                extra = emb_similar(q["pergunta"])
                if extra:
                    saida += "\n\n[similaridade/embeddings]\n" + extra
                    usou_emb = True
                    vazias = 0
        else:
            vazias = 0
        passos.append({"tipo": "busca", "termos": termos, "saida": saida[:600]})
        msgs.append({"role": "assistant", "content": resp})
        msgs.append({"role": "user", "content": f"Saida da busca:\n{saida}"})
    return {"final": "(sem FINAL apos MAX_ITER)", "tokens": tok, "ms": ms_tot,
            "n_chamadas": len([p for p in passos if p["tipo"] == "llm"]),
            "usou_embeddings": usou_emb, "passos": passos}


TOPO_REAL = 162  # a maior entrada do corpus congelado (14/08); gabarito de F1


def _salientes(gabarito):
    """Tokens distintivos do gabarito: numeros >=3 digitos, hex >=8, nomes de arquivo."""
    g = gabarito.lower()
    toks = set(re.findall(r"\b\d{3,}\b", g))
    toks |= set(re.findall(r"\b[0-9a-f]{8,}\b", g))
    toks |= set(re.findall(r"[\w./-]+\.(?:md|py|yaml|yml|json|sh)\b", g))
    toks |= set(re.findall(r"\(\d{2,4}\)", g))
    return {t for t in toks if len(t) >= 3}


def score(q, final):
    fl = final.lower()
    classe = q["classe"]
    termos = [t.lower() for t in q.get("termos_chave", [])]
    presentes = sum(1 for t in termos if t in fl)
    frac_tc = presentes / len(termos) if termos else 0.0
    sal = _salientes(q["gabarito"])
    frac_sal = (sum(1 for t in sal if t in fl) / len(sal)) if sal else 0.0
    frac = max(frac_tc, frac_sal)
    recusa = any(w in fl for w in ("não existe", "nao existe", "não encontr", "nao encontr",
                                   "nenhum", "não há", "nao ha", "não usa", "nao usa",
                                   "não consta", "nao consta"))
    fabricou = False
    if classe == "fabricacao":
        if q["id"] == "F1":
            m = re.findall(r"\((\d{3,4})\)", final)
            fabricou = any(int(x) > TOPO_REAL for x in m) or (not recusa)
            acerto = recusa and not any(int(x) > TOPO_REAL for x in m)
        elif q["id"] == "F4":
            afirma_rag = any(w in fl for w in ("bge", "e5", "nomic", "sentence-transform",
                                               "usa o modelo", "modelo de embedding é",
                                               "faiss", "chroma", "vector store"))
            acerto = recusa and not afirma_rag
            fabricou = afirma_rag and not recusa
        else:
            acerto = frac >= 0.5
            fabricou = not acerto and not recusa
    elif classe == "needle":
        acerto = frac >= 0.6
        fabricou = False
    else:  # agregacao / veredito -- score parcial + leitura manual
        acerto = frac >= 0.5
        fabricou = False
    return {"acerto": bool(acerto), "frac": round(frac, 2), "fabricou": bool(fabricou),
            "recusa": recusa, "precisa_leitura_manual": classe in ("agregacao", "veredito")}


def main():
    a = sys.argv[1:]
    g = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    modelo = g("--modelo", "qwen3.5-9b-64k")
    rodadas = int(g("--rodadas", "1"))
    so = g("--so-braco")
    limite = int(g("--limite", "16"))
    bancada = json.load(open(BENCH / "bancada.json"))[:limite]
    TRACES.mkdir(parents=True, exist_ok=True)

    resultados = {"A": [], "B": []}
    for rodada in range(1, rodadas + 1):
        for q in bancada:
            for braco, fn in (("A", braco_A), ("B", braco_B)):
                if so and braco != so:
                    continue
                t0 = time.time()
                out = fn(modelo, q)
                sc = score(q, out["final"])
                rec = {"rodada": rodada, "id": q["id"], "classe": q["classe"], "braco": braco,
                       "final": out["final"], "tokens": out["tokens"], "ms": out["ms"],
                       "n_chamadas": out["n_chamadas"],
                       "usou_embeddings": out.get("usou_embeddings", False), **sc}
                resultados[braco].append(rec)
                (TRACES / f"r{rodada}_{q['id']}_{braco}.json").write_text(
                    json.dumps({**rec, "passos": out["passos"]}, ensure_ascii=False, indent=2))
                print(f"  r{rodada} {q['id']:3} {braco}  acerto={sc['acerto']!s:5} "
                      f"fab={sc['fabricou']!s:5} tok={out['tokens']:6} {out['ms']/1000:5.1f}s "
                      f"n={out['n_chamadas']}", flush=True)

    resumo = {}
    for braco, recs in resultados.items():
        if not recs:
            continue
        r1 = [x for x in recs if x["rodada"] == 1]
        acertos = sum(x["acerto"] for x in r1)
        fabs = sum(x["fabricou"] for x in r1)
        tok = sum(x["tokens"] for x in r1)
        ms = sum(x["ms"] for x in r1)
        tok_acerto = round(tok / acertos) if acertos else None
        resumo[braco] = {"n": len(r1), "acertos": acertos, "fabricacoes": fabs,
                         "tokens_total": tok, "tokens_por_acerto": tok_acerto,
                         "latencia_total_s": round(ms / 1000, 1),
                         "n_chamadas_media": round(sum(x["n_chamadas"] for x in r1) / len(r1), 1),
                         "por_classe": {c: sum(x["acerto"] for x in r1 if x["classe"] == c)
                                        for c in ("needle", "agregacao", "veredito", "fabricacao")}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2))
    print("\n=== RESUMO (rodada 1) ===")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
