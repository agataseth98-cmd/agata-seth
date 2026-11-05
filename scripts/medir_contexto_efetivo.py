#!/usr/bin/env python3
"""medir_contexto_efetivo.py -- mede até que comprimento um modelo local ainda acha um fato no meio do contexto.

Por quê: RULER (Hsieh et al., COLM 2024) e Chroma (2025) mostram que a janela declarada superestima a
efetiva; o Agata declara tags de 64 mil tokens e nunca mediu. Teste de agulha em palheiro: um código
aleatório de 6 hexadecimais vai a 25%, 50% e 75% do texto (3 tentativas por comprimento) e o modelo tem de
devolvê-lo. É o caso mais fácil do RULER (recuperação simples); tarefas de agregação e múltiplos saltos NÃO
estão cobertas. Comprimento efetivo = o maior comprimento até o qual TODAS as tentativas acertaram. Acerto = o código correto
aparece na resposta (modelos que expõem o raciocínio no texto contam se citarem o código certo).

Tarefas: `agulha` (um fato), `varias` (8 fatos parecidos espalhados, pergunta por um: multi-chave do RULER),
`rastreio` (cadeia de 4 variáveis que herdam um valor, com 3 distratoras: rastreio de variáveis do RULER) e `agregacao`
(5 palavras inventadas repetidas 12 vezes entre 40 que aparecem uma vez: extração de palavras comuns do RULER). Só fala com o endpoint local do Ollama (padrão http://127.0.0.1:11434/api/chat). Gasta GPU e minutos: só roda
quando pedido. Com --salvar escreve em AGATA_MEDICOES_DIR (padrão ~/.cache/agata/painel/medicoes).
  medir_contexto_efetivo.py --modelo TAG [--url URL] [--comprimentos 2048,4096,8192,16384,32768]
                            [--tarefa agulha|varias|rastreio|agregacao] [--raciocinio] [--ctx-maximo 65536] [--tentativas 3] [--salvar]     |     --selftest
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
TAREFAS = ("agulha", "varias", "rastreio", "agregacao")
N_VARIAS = 8
N_CADEIA, N_DISTRATORAS = 4, 3
N_MARCADORES, REPETICOES, N_DISTRATORES = 5, 12, 40


def palheiro(chars: int, base: str) -> str:
    texto = re.sub(r"\s+", " ", base).strip() or "Texto de enchimento. "
    return (texto * (chars // len(texto) + 1))[:chars]


def montar(chars: int, profundidade: float, codigo: str, base: str) -> str:
    miolo = palheiro(chars, base)
    corte = int(len(miolo) * profundidade)
    agulha = f" O código de verificação do lote é {codigo}. "
    return miolo[:corte] + agulha + miolo[corte:] + "\n\n" + PERGUNTA


def montar_varias(chars: int, codigos: list[str], alvo: int, base: str) -> str:
    miolo = palheiro(chars, base)
    pos = [int(len(miolo) * (i + 1) / (len(codigos) + 1)) for i in range(len(codigos))]
    pedacos, ant = [], 0
    for i, (p, c) in enumerate(zip(pos, codigos)):
        pedacos += [miolo[ant:p], f" O código de verificação do lote-{i + 1} é {c}. "]
        ant = p
    pedacos.append(miolo[ant:])
    return "".join(pedacos) + f"\n\nQual é o código de verificação do lote-{alvo + 1}? Responda apenas o código, sem mais nada."


# Tarefas de várias respostas fazem o qwen3 raciocinar no texto da resposta (medido em 04/11: com 400 tokens a saída
# vem cortada, done_reason=length, e a medição vira falso zero). Dão mais espaço e só a parte depois de </think> vale.
NUM_PREDICT = {"agulha": 400, "varias": 400, "rastreio": 2500, "agregacao": 2000}
NUM_PREDICT_RACIOCINIO = 8000  # com o raciocínio ligado o modelo pensa antes de responder (medido: 1.400 a 1.500 tokens no qwen3:4b)
CTX_MAXIMO = 65536


def so_resposta(texto: str, tarefa: str) -> str:
    if tarefa in ("agulha", "varias") or "</think>" not in texto:
        return texto
    return texto.rsplit("</think>", 1)[1]


_VISTOS: list = []  # só o selftest usa: o que o servidor falso recebeu


def _inserir(miolo: str, pares: list) -> str:
    """Insere (fração, texto) no miolo; da última posição para a primeira, para não deslocar as outras."""
    total = len(miolo)
    cortes = sorted(((int(total * fracao), i, texto) for i, (fracao, texto) in enumerate(pares)), reverse=True)
    for corte, _, texto in cortes:
        miolo = miolo[:corte] + texto + miolo[corte:]
    return miolo


def _nome(rnd, prefixo: str, n: int, alfabeto: str) -> str:
    return prefixo + "".join(rnd.choice(alfabeto) for _ in range(n))


def montar_rastreio(chars: int, rnd, base: str) -> tuple[str, list, list]:
    valor = str(rnd.randrange(10**5, 10**6))
    nomes = [_nome(rnd, "VAR_", 4, "ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(N_CADEIA + N_DISTRATORAS)]
    cadeia, distrat = nomes[:N_CADEIA], nomes[N_CADEIA:]
    frases = [f" A variável {cadeia[0]} recebe {valor}. "] + [f" A variável {cadeia[i]} recebe o valor de {cadeia[i - 1]}. " for i in range(1, N_CADEIA)]
    outras = [f" A variável {d} recebe {rnd.randrange(10**5, 10**6)}. " for d in distrat]
    fracoes = sorted(rnd.sample(range(5, 96), len(frases) + len(outras)))
    posicao_cadeia = sorted(rnd.sample(range(len(fracoes)), len(frases)))
    pares, resto = [], iter(outras)
    for i, f in enumerate(fracoes):
        pares.append((f / 100, frases[posicao_cadeia.index(i)] if i in posicao_cadeia else next(resto)))
    texto = _inserir(palheiro(chars, base), pares)
    return (texto + f"\n\nQuais variáveis têm o valor {valor}? Liste os nomes de todas elas, separados por vírgula, sem mais nada.",
            [n.lower() for n in cadeia], [n.lower() for n in distrat])


def montar_agregacao(chars: int, rnd, base: str) -> tuple[str, list, list]:
    palavras = []
    while len(palavras) < N_MARCADORES + N_DISTRATORES:
        w = _nome(rnd, "pal_", 5, "abcdefghijklmnopqrstuvwxyz")
        if w not in palavras:
            palavras.append(w)
    marcadores, distratores = palavras[:N_MARCADORES], palavras[N_MARCADORES:]
    pares = [(rnd.randrange(3, 98) / 100, f" {w} ") for w in marcadores for _ in range(REPETICOES)] + [(rnd.randrange(3, 98) / 100, f" {w} ") for w in distratores]
    texto = _inserir(palheiro(chars, base), pares)
    return (texto + f"\n\nNeste texto aparecem palavras inventadas que começam com pal_. Quais são as {N_MARCADORES} que mais se repetem? Responda só as palavras, separadas por vírgula.",
            marcadores, distratores)


def perguntar(url: str, modelo: str, prompt: str, num_ctx: int, timeout: int = 900, num_predict: int = 400, raciocinio: bool = False) -> dict:
    corpo = json.dumps({"model": modelo, "stream": False, "think": raciocinio,
                        "messages": [{"role": "user", "content": prompt}],
                        "options": {"temperature": 0, "num_ctx": num_ctx, "num_predict": num_predict}}).encode()
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


def medir(url: str, modelo: str, comprimentos=COMPRIMENTOS, tentativas: int = 3, base: str = "", progresso=None, tarefa: str = "agulha", raciocinio: bool = False, ctx_maximo: int = CTX_MAXIMO) -> dict:
    if tarefa not in TAREFAS:
        raise ValueError("tarefa fora da lista")
    linhas = []
    for alvo in comprimentos:
        acertos, tokens, segundos = 0, [], 0.0
        for t in range(tentativas):
            rnd = random.Random(alvo * 31 + t)
            tam = int(alvo * CHARS_POR_TOKEN)
            if tarefa == "agulha":
                codigo = "%06x" % rnd.randrange(16**6)
                prompt = montar(tam, PROFUNDIDADES[t % len(PROFUNDIDADES)], codigo, base)
                certos, errados = [codigo], []
            elif tarefa == "varias":
                codigos = ["%06x" % rnd.randrange(16**6) for _ in range(N_VARIAS)]
                indice = (t * 3 + 1) % N_VARIAS
                prompt = montar_varias(tam, codigos, indice, base)
                certos, errados = [codigos[indice]], [c for i, c in enumerate(codigos) if i != indice]
            elif tarefa == "rastreio":
                prompt, certos, errados = montar_rastreio(tam, rnd, base)
            else:
                prompt, certos, errados = montar_agregacao(tam, rnd, base)
            t0 = time.time()
            limite = NUM_PREDICT_RACIOCINIO if raciocinio else NUM_PREDICT[tarefa]
            r = perguntar(url, modelo, prompt, min(ctx_maximo, alvo + limite + 600), num_predict=limite, raciocinio=raciocinio)
            segundos += time.time() - t0
            tokens.append(r.get("prompt_eval_count"))
            resposta = so_resposta(r.get("message", {}).get("content", "") or "", tarefa).lower()
            acertos += all(c in resposta for c in certos) and not any(c in resposta for c in errados)
        linhas.append({"alvo_tokens": alvo, "tokens_reais": [x for x in tokens if x], "acertos": acertos,
                       "tentativas": tentativas, "segundos": round(segundos, 1)})
        if progresso:
            progresso(linhas[-1])
    metodo = {"agulha": "agulha no palheiro, 3 profundidades; só recuperação simples",
              "varias": f"{N_VARIAS} fatos parecidos espalhados, pergunta por um (multi-chave do RULER); resposta com outro código conta como erro",
              "rastreio": f"cadeia de {N_CADEIA} variáveis que herdam um valor, com {N_DISTRATORAS} distratoras (rastreio de variáveis do RULER); acerta se lista as {N_CADEIA} e nenhuma distratora",
              "agregacao": f"{N_MARCADORES} palavras inventadas repetidas {REPETICOES} vezes entre {N_DISTRATORES} que aparecem uma vez (extração de palavras comuns do RULER); acerta se lista as {N_MARCADORES} e nenhuma única"}[tarefa]
    metodo += "; raciocínio LIGADO (think: true, até %d tokens de saída)" % NUM_PREDICT_RACIOCINIO if raciocinio else "; raciocínio desligado (think: false)"
    return {"modelo": modelo, "tarefa": tarefa, "raciocinio": "ligado" if raciocinio else "desligado", "metodo": metodo,
            "linhas": linhas, "efetivo_tokens": efetivo(linhas),
            "nao_medido": ["outros modelos", "tarefas do RULER não rodadas neste arquivo: " + ", ".join(x for x in TAREFAS if x != tarefa)],
            "medido_em": datetime.now().astimezone().isoformat(timespec="seconds")}


def _salvar(resultado: dict) -> Path:
    pasta = Path(os.environ.get("AGATA_MEDICOES_DIR", Path.home() / ".cache" / "agata" / "painel" / "medicoes"))
    pasta.mkdir(parents=True, exist_ok=True, mode=0o700)
    sufixo = ("" if resultado.get("tarefa", "agulha") == "agulha" else "-" + resultado["tarefa"]) + ("-raciocinio" if resultado.get("raciocinio") == "ligado" else "")
    arq = pasta / ("contexto-" + re.sub(r"[^a-z0-9._-]", "_", resultado["modelo"].lower()) + sufixo + ".json")
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
            _VISTOS.append((dados.get("think"), dados["options"]["num_predict"]))
            if "Quais variáveis têm o valor" in prompt:
                valor = re.search(r"valor (\d+)\?", prompt).group(1)
                dono = {a: v for a, v in re.findall(r"A variável (VAR_[A-Z]+) recebe (\d+)\.", prompt)}
                herda = dict(re.findall(r"A variável (VAR_[A-Z]+) recebe o valor de (VAR_[A-Z]+)\.", prompt))
                nomes = [n for n, v in dono.items() if v == valor]
                for _ in range(N_CADEIA):
                    nomes += [n for n, de in herda.items() if de in nomes and n not in nomes]
                resp = ", ".join(nomes) if len(prompt) <= LIMITE_CHARS else "não sei"
                corpo = json.dumps({"message": {"content": resp}, "prompt_eval_count": len(prompt) // 3}).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(corpo))); self.end_headers(); self.wfile.write(corpo); return
            if "mais se repetem" in prompt:
                cont = {}
                for w in re.findall(r"pal_[a-z]{5}", prompt):
                    cont[w] = cont.get(w, 0) + 1
                resp = ", ".join(w for w, _ in sorted(cont.items(), key=lambda x: -x[1])[:N_MARCADORES]) if len(prompt) <= LIMITE_CHARS else "não sei"
                corpo = json.dumps({"message": {"content": resp}, "prompt_eval_count": len(prompt) // 3}).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(corpo))); self.end_headers(); self.wfile.write(corpo); return
            q = re.search(r"lote-(\d+)\? Responda", prompt)
            if q:  # sem regex montado com dado do pedido: procura o trecho literal e lê o código depois dele
                chave = f"lote-{q.group(1)} é "
                i = prompt.find(chave)
                m = re.match(r"([0-9a-f]{6})\.", prompt[i + len(chave):]) if i >= 0 else None
            else:
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
    srv2 = ThreadingHTTPServer(("127.0.0.1", 0), Falso); threading.Thread(target=srv2.serve_forever, daemon=True).start()
    rv = medir(f"http://127.0.0.1:{srv2.server_address[1]}/api/chat", "falso:1", (1000, 4000), 3, "Texto de enchimento do canon. ", tarefa="varias")
    srv2.shutdown(); srv2.server_close()
    conferir("varias: acerta o alvo no curto e perde no longo", rv["tarefa"] == "varias" and [l["acertos"] for l in rv["linhas"]] == [3, 0])
    srv4 = ThreadingHTTPServer(("127.0.0.1", 0), Falso); threading.Thread(target=srv4.serve_forever, daemon=True).start()
    _VISTOS.clear()
    medir(f"http://127.0.0.1:{srv4.server_address[1]}/api/chat", "falso:1", (1000,), 1, "Texto. ", tarefa="rastreio")
    medir(f"http://127.0.0.1:{srv4.server_address[1]}/api/chat", "falso:1", (1000,), 1, "Texto. ", tarefa="rastreio", raciocinio=True)
    srv4.shutdown(); srv4.server_close()
    conferir("raciocínio: padrão manda think false e saída curta; --raciocinio manda think true e 8000", _VISTOS == [(False, 2500), (True, NUM_PREDICT_RACIOCINIO)])
    rr = medir(f"http://127.0.0.1:1/api/chat", "falso:1", (), 1, "x ", tarefa="rastreio", raciocinio=True)
    conferir("raciocínio: o resultado declara ligado e o método diz", rr["raciocinio"] == "ligado" and "LIGADO" in rr["metodo"])
    for tarefa in ("rastreio", "agregacao"):
        srv3 = ThreadingHTTPServer(("127.0.0.1", 0), Falso); threading.Thread(target=srv3.serve_forever, daemon=True).start()
        rt = medir(f"http://127.0.0.1:{srv3.server_address[1]}/api/chat", "falso:1", (1000, 4000), 3, "Texto de enchimento do canon. ", tarefa=tarefa)
        srv3.shutdown(); srv3.server_close()
        conferir(f"{tarefa}: acerta no curto e perde no longo", [l["acertos"] for l in rt["linhas"]] == [3, 0])
    conferir("so_resposta: ignora o raciocínio nas tarefas novas e mantém o texto inteiro nas antigas",
             so_resposta("pensa var_x </think>\nvar_a", "rastreio").strip() == "var_a" and so_resposta("pensa </think> ab", "agulha") == "pensa </think> ab" and so_resposta("sem tag", "rastreio") == "sem tag")
    prompt, certos, errados = montar_rastreio(3000, random.Random(5), "x ")
    conferir("rastreio: a cadeia tem 4 nomes, há 3 distratoras e nenhum nome se repete", len(certos) == N_CADEIA and len(errados) == N_DISTRATORAS and len(set(certos + errados)) == N_CADEIA + N_DISTRATORAS)
    conferir("rastreio: a pergunta traz o valor e as frases de herança aparecem depois da primeira", prompt.rstrip().endswith("sem mais nada.") and prompt.index(certos[0].upper()) < prompt.index(f"recebe o valor de {certos[0].upper()}"))
    prompt, certos, errados = montar_agregacao(6000, random.Random(5), "x ")
    conferir("agregacao: marcadores aparecem 12 vezes e as outras uma vez", all(prompt.count(w) == REPETICOES for w in certos) and all(prompt.count(w) == 1 for w in errados))
    conferir("agregacao: mesma semente, mesmo prompt", montar_agregacao(6000, random.Random(5), "x ")[0] == prompt)
    p = montar_varias(3000, ["aaaaaa", "bbbbbb", "cccccc"], 1, "x ")
    conferir("varias: 3 fatos espalhados e a pergunta pelo segundo", p.count("O código de verificação do lote-") == 3 and p.rstrip().endswith("lote-2? Responda apenas o código, sem mais nada."))
    try:
        medir("http://x", "m", (1,), 1, "", tarefa="outra"); conferir("tarefa fora da lista levanta erro", False)
    except ValueError:
        conferir("tarefa fora da lista levanta erro", True)
    os.environ["AGATA_MEDICOES_DIR"] = tempfile.mkdtemp()
    conferir("salvar usa nome distinto para a tarefa varias", _salvar({"modelo": "m", "tarefa": "varias"}).name == "contexto-m-varias.json")
    conferir("salvar usa sufixo -raciocinio quando ligado", _salvar({"modelo": "m", "tarefa": "rastreio", "raciocinio": "ligado"}).name == "contexto-m-rastreio-raciocinio.json")
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
    tarefa = opt("--tarefa", "agulha")
    if tarefa not in TAREFAS:
        print(f"tarefa inválida: {tarefa}; use {' ou '.join(TAREFAS)}", file=sys.stderr)
        return 2
    try:
        resultado = medir(opt("--url", URL_PADRAO), modelo, comprimentos, int(opt("--tentativas", "3")), base, tarefa=tarefa,
                          raciocinio="--raciocinio" in argv, ctx_maximo=int(opt("--ctx-maximo", str(CTX_MAXIMO))),
                          progresso=lambda l: print(f"{l['alvo_tokens']} tokens: {l['acertos']}/{l['tentativas']} em {l['segundos']} s", file=sys.stderr))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"endpoint não respondeu: {exc}", file=sys.stderr)
        return 4
    if "--salvar" in argv:
        _salvar(resultado)
    if "--registro" in argv:   # lote 5, A5: uma linha por comprimento, no registro comum
        import registro_medidor  # noqa: E402
        itens = [{"task_id": f"contexto-{l['alvo_tokens']}", "condition": resultado["tarefa"], "model_id": modelo,
                  "outcome": "passou" if l["acertos"] == l["tentativas"] else ("falhou" if l["acertos"] == 0 else "parcial"),
                  "usage": {"input_tokens": (sum(l["tokens_reais"]) // max(len(l["tokens_reais"]), 1)) if l.get("tokens_reais") else None},
                  "latency_ms": int(float(l.get("segundos") or 0) * 1000)} for l in resultado["linhas"]]
        print("registro:", registro_medidor.gravar("medir_contexto_efetivo", "dev", itens, {"efetivo_tokens": resultado.get("efetivo_tokens")}))
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
