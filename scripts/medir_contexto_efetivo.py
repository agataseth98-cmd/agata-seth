#!/usr/bin/env python3
"""medir_contexto_efetivo.py -- mede até que comprimento um modelo local ainda acha um fato no meio do contexto.

Por quê: RULER (Hsieh et al., COLM 2024) e Chroma (2025) mostram que a janela declarada superestima a
efetiva; o Agata declara tags de 64 mil tokens e nunca mediu. Teste de agulha em palheiro: um código
aleatório de 6 hexadecimais vai a 25%, 50% e 75% do texto (3 tentativas por comprimento) e o modelo tem de
devolvê-lo. É o caso mais fácil do RULER (recuperação simples); tarefas de agregação e múltiplos saltos NÃO
estão cobertas. Comprimento efetivo = o maior comprimento até o qual TODAS as tentativas acertaram. Acerto = o código correto
aparece na resposta (modelos que expõem o raciocínio no texto contam se citarem o código certo).

Só fala com o endpoint local do Ollama (padrão http://127.0.0.1:11434/api/chat). Gasta GPU e minutos: só roda
quando pedido. Com --salvar escreve em AGATA_MEDICOES_DIR (padrão ~/.cache/agata/painel/medicoes).
  medir_contexto_efetivo.py --modelo TAG [--url URL] [--comprimentos 2048,4096,8192,16384,32768]
                            [--tentativas 3] [--salvar]     |     --selftest
Exit 0 = medido; 2 = uso; 4 = o endpoint não respondeu.
"""
import json
import os
import random
import re
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
URL_PADRAO = "http://127.0.0.1:11434/api/chat"
COMPRIMENTOS = (2048, 4096, 8192, 16384, 32768)
PROFUNDIDADES = (0.25, 0.5, 0.75)
CHARS_POR_TOKEN = 3.0
PERGUNTA = "Qual é o código de verificação do lote? Responda apenas o código, sem mais nada."


def palheiro(chars: int, base: str) -> str:
    texto = re.sub(r"\s+", " ", base).strip() or "Texto de enchimento. "
    return (texto * (chars // len(texto) + 1))[:chars]


def montar(chars: int, profundidade: float, codigo: str, base: str) -> str:
    miolo = palheiro(chars, base)
    corte = int(len(miolo) * profundidade)
    agulha = f" O código de verificação do lote é {codigo}. "
    return miolo[:corte] + agulha + miolo[corte:] + "\n\n" + PERGUNTA


def perguntar(url: str, modelo: str, prompt: str, num_ctx: int, timeout: int = 900) -> dict:
    corpo = json.dumps({"model": modelo, "stream": False, "think": False,
                        "messages": [{"role": "user", "content": prompt}],
                        "options": {"temperature": 0, "num_ctx": num_ctx, "num_predict": 400}}).encode()
    req = urllib.request.Request(url, data=corpo, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def efetivo(linhas: list[dict]) -> int | None:
    melhor = None
    for linha in sorted(linhas, key=lambda x: x["alvo_tokens"]):
        if linha["acertos"] == linha["tentativas"]:
            melhor = linha["alvo_tokens"]
        else:
            break
    return melhor


def medir(url: str, modelo: str, comprimentos=COMPRIMENTOS, tentativas: int = 3, base: str = "", progresso=None) -> dict:
    linhas = []
    for alvo in comprimentos:
        acertos, tokens, segundos = 0, [], 0.0
        for t in range(tentativas):
            codigo = "%06x" % random.Random(alvo * 31 + t).randrange(16**6)
            prompt = montar(int(alvo * CHARS_POR_TOKEN), PROFUNDIDADES[t % len(PROFUNDIDADES)], codigo, base)
            t0 = time.time()
            r = perguntar(url, modelo, prompt, min(65536, alvo + 1024))
            segundos += time.time() - t0
            tokens.append(r.get("prompt_eval_count"))
            acertos += codigo in (r.get("message", {}).get("content", "") or "").lower()
        linhas.append({"alvo_tokens": alvo, "tokens_reais": [x for x in tokens if x], "acertos": acertos,
                       "tentativas": tentativas, "segundos": round(segundos, 1)})
        if progresso:
            progresso(linhas[-1])
    return {"modelo": modelo, "metodo": "agulha no palheiro, 3 profundidades; só recuperação simples",
            "linhas": linhas, "efetivo_tokens": efetivo(linhas),
            "nao_medido": ["agregação e múltiplos saltos (RULER completo)", "outros modelos"],
            "medido_em": datetime.now().astimezone().isoformat(timespec="seconds")}


def _salvar(resultado: dict) -> Path:
    pasta = Path(os.environ.get("AGATA_MEDICOES_DIR", Path.home() / ".cache" / "agata" / "painel" / "medicoes"))
    pasta.mkdir(parents=True, exist_ok=True, mode=0o700)
    arq = pasta / ("contexto-" + re.sub(r"[^a-z0-9._-]", "_", resultado["modelo"].lower()) + ".json")
    arq.write_text(json.dumps(resultado, ensure_ascii=False), encoding="utf-8")
    return arq


def _selftest() -> int:
    falhou = 0
    def conferir(nome, cond):
        nonlocal falhou
        print(("PASS " if cond else "FALHA ") + nome); falhou += 0 if cond else 1
    LIMITE_CHARS = 9000  # o modelo falso "esquece" acima disso

    class Falso(BaseHTTPRequestHandler):
        def do_POST(self):
            dados = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            prompt = dados["messages"][0]["content"]
            m = re.search(r"lote é ([0-9a-f]{6})\.", prompt)
            resp = m.group(1) if (m and len(prompt) <= LIMITE_CHARS) else "não sei"
            corpo = json.dumps({"message": {"content": resp}, "prompt_eval_count": len(prompt) // 3}).encode()
            self.send_response(200); self.send_header("Content-Length", str(len(corpo))); self.end_headers(); self.wfile.write(corpo)
        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Falso); threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/api/chat"
    res = medir(url, "falso:1", (1000, 2000, 4000), 3, "Texto de enchimento do canon. ")
    srv.shutdown(); srv.server_close()
    conferir("acha a agulha nos comprimentos curtos e perde nos longos", [l["acertos"] for l in res["linhas"]] == [3, 3, 0])
    conferir("comprimento efetivo = maior com todas as tentativas certas", res["efetivo_tokens"] == 2000)
    conferir("efetivo é None se nem o menor acerta", efetivo([{"alvo_tokens": 10, "acertos": 2, "tentativas": 3}]) is None)
    conferir("efetivo para no primeiro buraco", efetivo([{"alvo_tokens": 1, "acertos": 3, "tentativas": 3}, {"alvo_tokens": 2, "acertos": 1, "tentativas": 3},
                                                       {"alvo_tokens": 3, "acertos": 3, "tentativas": 3}]) == 1)
    conferir("a agulha cai nas 3 profundidades", len({montar(3000, p, "abcdef", "x ").index("abcdef") for p in PROFUNDIDADES}) == 3)
    conferir("diz o que não mediu", len(res["nao_medido"]) == 2)
    os.environ["AGATA_MEDICOES_DIR"] = tempfile.mkdtemp()
    conferir("salvar usa nome seguro por modelo", _salvar({"modelo": "Qwen3:4B/../x"}).name == "contexto-qwen3_4b_.._x.json")
    return 1 if falhou else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    def opt(nome, padrao=None):
        return argv[argv.index(nome) + 1] if nome in argv else padrao
    modelo = opt("--modelo")
    if not modelo:
        print("uso: medir_contexto_efetivo.py --modelo TAG [--url URL] [--comprimentos a,b] [--tentativas N] [--salvar]", file=sys.stderr)
        return 2
    comprimentos = tuple(int(x) for x in opt("--comprimentos", ",".join(map(str, COMPRIMENTOS))).split(","))
    base = " ".join((RAIZ / a).read_text(encoding="utf-8", errors="replace") for a in ("REGRAS.md", "PROTOCOLOS.md") if (RAIZ / a).exists())
    try:
        resultado = medir(opt("--url", URL_PADRAO), modelo, comprimentos, int(opt("--tentativas", "3")), base,
                          progresso=lambda l: print(f"{l['alvo_tokens']} tokens: {l['acertos']}/{l['tentativas']} em {l['segundos']} s", file=sys.stderr))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"endpoint não respondeu: {exc}", file=sys.stderr)
        return 4
    if "--salvar" in argv:
        _salvar(resultado)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
