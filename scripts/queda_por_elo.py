#!/usr/bin/env python3
"""queda_por_elo.py -- mede, ANTES de uma pane real, qual elo de cada fila da Seth
está vivo, qual está morto e qual fila depende de um elo só.

Por quê (03/10/2026, MEMÓRIAS (648)-(650)): a fila só mostra quem respondeu, nunca
quem falhou antes. Um elo morto na posição 0 custa latência em todo pedido; uma fila
cujo único elo remoto vivo cai vira Ollama sem ninguém saber; e o crash de (635)/(636)
era um stream de ZERO chunks, que um teste de "status 200" não vê.

Como (só leitura no OmniRoute -- nunca cria, muda ou apaga combo):
  1. `GET :20128/api/combos` -> os elos de cada fila, na ordem viva.
  2. Fase A, elo isolado: UM pedido direto por modelo distinto (o mesmo modelo em
     duas filas é medido uma vez), pelo sanitizador `:20127`, em stream, com o mesmo
     tamanho de carga da Seth (system de ~9 mil caracteres + 12 ferramentas) e uma
     tarefa que exige ferramenta. "Fila sem o elo i" não precisa ser criada: ela
     sobrevive se e só se outro elo dela passou na Fase A.
  3. Fase B, fila inteira: UM pedido por fila, para ver o roteamento do combo e
     quem de fato atendeu (campo "model" do stream).
Não passa pelo seth_gateway (`:20126`) de propósito: o gateway grava o "modelo real"
do último pedido para a Seth citar no turno seguinte (614), e o teste o sujaria.

Veredito por pedido:
  OK          chamada de ferramenta válida (nome certo, argumentos JSON com 17 e 25)
  SO_TEXTO    respondeu texto, ignorou a ferramenta (vivo, fraco para agente)
  TOOL_RUIM   chamou ferramenta com nome ou argumentos inválidos
  VAZIO       stream com chunks mas sem conteúdo nem ferramenta (ex.: finish=length)
  ZERO_CHUNKS 200 sem nenhum chunk de dados -- a assinatura do crash de (635)
  HTTP_nnn / TIMEOUT / ERRO
Vivo = OK ou SO_TEXTO. Custa cota grátis: rode à mão, depois de cada mudança de fila
ou uma vez por semana.

Uso:
  python3 scripts/queda_por_elo.py              # só o plano (GET /api/combos), nenhum pedido de chat
  python3 scripts/queda_por_elo.py --executar   # as duas fases
     [--filas seth-rapido,seth-livre] [--sem-local] [--intervalo 8] [--timeout 90] [--json ARQ]
  python3 scripts/queda_por_elo.py --selftest
Saída 1 se alguma fila ficou sem elo remoto vivo ou falhou na Fase B. Só stdlib.
Token: `scripts/token_interno.py` (nunca o .env). Nunca imprime o corpo do pedido.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

OMNIROUTE = os.environ.get("OMNIROUTE_URL", "http://127.0.0.1:20128").rstrip("/")
PROXY = os.environ.get("AGATA_PROXY", "http://127.0.0.1:20127").rstrip("/")
FILAS = ("seth-rapido", "seth-livre", "seth-pesado", "seth-codigo")
LOCAL = ("ollama-local/", "llama-cpp/", "llamacpp-local/")
_SEM_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # só localhost


def _token_interno() -> str:
    """Token interno (X-Agata-Token), de `scripts/token_interno.py` -- arquivo
    próprio, nunca o .env (MEMÓRIAS (629)-(631)). Nunca loga o valor."""
    _scripts = str(Path(__file__).resolve().parents[1] / "scripts")
    if _scripts not in sys.path:
        sys.path.insert(0, _scripts)
    import token_interno  # noqa: E402  (scripts/token_interno.py)
    return token_interno.ler()


# --- carga padrão: o tamanho de um turno da Seth, sem dado nenhum do canon -------
_FRASE = ("Contexto sintético de carga para medir a fila: este parágrafo existe só para "
          "ocupar o mesmo espaço que a hidratação da Seth ocupa num turno real. ")


def _ferramenta(nome: str, desc: str, props: dict) -> dict:
    return {"type": "function", "function": {"name": nome, "description": desc, "parameters": {
        "type": "object", "properties": props, "required": list(props)}}}


def corpo_padrao(modelo: str) -> dict:
    extras = [_ferramenta(f"ferramenta_inerte_{i:02d}",
                          "Não use. Existe só para o pedido ter o tamanho real de esquemas. " * 3,
                          {"texto": {"type": "string", "description": "texto livre"}})
              for i in range(11)]
    somar = _ferramenta("somar", "Soma dois inteiros e devolve o resultado.",
                        {"a": {"type": "integer"}, "b": {"type": "integer"}})
    return {"model": modelo, "stream": True, "max_tokens": 2000, "tools": [somar] + extras,
            "messages": [
                {"role": "system", "content": _FRASE * 55 + "Use ferramentas quando pedido."},
                {"role": "user", "content": "Quanto é 17 + 25? Use a ferramenta somar, "
                                            "não faça a conta de cabeça."}]}


# --- leitura do stream -------------------------------------------------------
def ler_stream(linhas) -> dict:
    """Junta um stream SSE OpenAI. Devolve chunks, conteúdo, tool_calls, finish, model."""
    r = {"chunks": 0, "conteudo": "", "tools": {}, "finish": None, "model": None}
    for bruta in linhas:
        linha = bruta.decode("utf-8", "replace").strip() if isinstance(bruta, bytes) else bruta.strip()
        if not linha.startswith("data:"):
            continue                                  # ": ka" e linhas vazias
        dado = linha[5:].strip()
        if dado == "[DONE]":
            break
        try:
            ev = json.loads(dado)
        except ValueError:
            continue
        if not isinstance(ev, dict):
            continue
        if ev.get("model") and ev.get("model") != "keepalive":
            r["model"] = r["model"] or ev["model"]
        for ch in ev.get("choices") or []:
            if not isinstance(ch, dict):
                continue
            r["chunks"] += 1
            d = ch.get("delta") or ch.get("message") or {}
            r["conteudo"] += d.get("content") or ""
            for tc in d.get("tool_calls") or []:
                t = r["tools"].setdefault(tc.get("index", 0), {"nome": "", "args": ""})
                f = tc.get("function") or {}
                t["nome"] += f.get("name") or ""
                t["args"] += f.get("arguments") or ""
            r["finish"] = ch.get("finish_reason") or r["finish"]
    return r


def veredito(r: dict) -> str:
    if r["chunks"] == 0:
        return "ZERO_CHUNKS"
    if r["tools"]:
        t = r["tools"][min(r["tools"])]
        try:
            a = json.loads(t["args"] or "{}")
        except ValueError:
            return "TOOL_RUIM"
        ok = t["nome"] == "somar" and isinstance(a, dict) and sorted(a.values()) == [17, 25]
        return "OK" if ok else "TOOL_RUIM"
    return "SO_TEXTO" if r["conteudo"].strip() else "VAZIO"


VIVO = ("OK", "SO_TEXTO")


def pedir(modelo: str, timeout: float, proxy: str = PROXY) -> dict:
    t0 = time.monotonic()
    req = urllib.request.Request(proxy + "/v1/chat/completions", method="POST",
                                 data=json.dumps(corpo_padrao(modelo)).encode(),
                                 headers={"Content-Type": "application/json",
                                          "X-Agata-Token": _token_interno()})
    try:
        with _SEM_PROXY.open(req, timeout=timeout) as resp:
            r = ler_stream(resp)
        r["veredito"] = veredito(r)
    except urllib.error.HTTPError as e:
        r = {"veredito": f"HTTP_{e.code}", "finish": None, "model": None, "chunks": 0}
    except TimeoutError:
        r = {"veredito": "TIMEOUT", "finish": None, "model": None, "chunks": 0}
    except Exception as e:                             # rede, reset, JSON -- registra a classe só
        r = {"veredito": "TIMEOUT" if "timed out" in str(e) else f"ERRO_{e.__class__.__name__}",
             "finish": None, "model": None, "chunks": 0}
    r["s"] = round(time.monotonic() - t0, 1)
    r.pop("conteudo", None)                            # nunca guarda o texto do modelo
    r["tools"] = len(r.get("tools") or {})
    return r


# --- filas -------------------------------------------------------------------
def ler_filas(omniroute: str = OMNIROUTE, quais=FILAS) -> dict[str, list[str]]:
    try:
        with _SEM_PROXY.open(omniroute + "/api/combos", timeout=15) as r:
            resp = json.loads(r.read().decode("utf-8") or "null")
    except (OSError, ValueError) as e:
        raise SystemExit(f"OmniRoute inacessível em {omniroute} ({e.__class__.__name__}) -- "
                         "nada medido; confira 'systemctl --user status omniroute'")
    if isinstance(resp, dict):
        resp = next((resp[k] for k in ("combos", "data", "items") if isinstance(resp.get(k), list)), None)
    if not isinstance(resp, list):
        raise SystemExit("formato inesperado de /api/combos -- confira a API antes de medir")
    por_nome = {c.get("name"): c for c in resp if isinstance(c, dict)}
    filas = {}
    for nome in quais:
        c = por_nome.get(nome)
        if c is None:
            print(f"aviso: fila {nome!r} não existe no OmniRoute -- pulada")
            continue
        filas[nome] = [(m.get("model") or m.get("id") or "?") if isinstance(m, dict) else str(m)
                       for m in c.get("models") or []]
    return filas


def analisar(filas: dict, elos: dict, fase_b: dict) -> tuple[list[str], int]:
    """Linhas de relatório + código de saída (1 = alguma fila em risco real)."""
    out, rc = [], 0
    for nome, ordem in filas.items():
        vivos = [m for m in ordem if elos.get(m, {}).get("veredito") in VIVO]
        remotos = [m for m in vivos if not m.startswith(LOCAL)]
        mortos = [m for m in ordem if m in elos and elos[m]["veredito"] not in VIVO]
        b = fase_b.get(nome, {})
        out.append(f"\n{nome}: {len(vivos)}/{len(ordem)} elos vivos · fila inteira: "
                   f"{b.get('veredito', '—')} via {b.get('model') or '?'} em {b.get('s', '—')}s")
        if ordem and ordem[0] in mortos:
            out.append(f"  ATENÇÃO: elo 0 ({ordem[0]}) morto -- todo pedido paga o fallback")
        if len(remotos) == 1:
            out.append(f"  ATENÇÃO: só {remotos[0]} segura a fila antes do local -- sem ele, cai no fundo")
        if not remotos:
            out.append("  RISCO: nenhum elo remoto vivo -- a fila hoje é só o fundo local")
            rc = 1
        if b and b.get("veredito") not in VIVO:
            out.append(f"  RISCO: a fila inteira falhou ({b.get('veredito')})")
            rc = 1
        for m in mortos:
            out.append(f"  morto: {m} ({elos[m]['veredito']}, finish={elos[m].get('finish')})")
        for m in ordem:
            if elos.get(m, {}).get("veredito") == "ZERO_CHUNKS":
                out.append(f"  ZERO_CHUNKS em {m}: é a assinatura do crash de (635) -- olhar antes de tudo")
    return out, rc


def executar(aplicar: bool, quais=FILAS, sem_local=False, intervalo=8.0, timeout=90.0,
             arq_json=None, omniroute=OMNIROUTE, proxy=PROXY) -> int:
    filas = ler_filas(omniroute, quais)
    distintos = list(dict.fromkeys(m for o in filas.values() for m in o
                                   if not (sem_local and m.startswith(LOCAL))))
    for nome, ordem in filas.items():
        print(f"{nome}: " + " -> ".join(ordem))
    print(f"Fase A: {len(distintos)} modelo(s) distinto(s) · Fase B: {len(filas)} fila(s) · "
          f"~{(len(distintos) + len(filas)) * intervalo / 60:.1f} min de espaçamento")
    if not aplicar:
        print("(só o plano -- nenhum pedido de chat feito; rode com --executar)")
        return 0
    elos, fase_b, primeiro = {}, {}, True
    for alvo, destino in [(m, elos) for m in distintos] + [(f, fase_b) for f in filas]:
        if not primeiro:
            time.sleep(intervalo)                      # cota grátis: nunca rajada
        primeiro = False
        r = pedir(alvo, timeout, proxy)
        destino[alvo] = r
        print(f"  {'A' if destino is elos else 'B'}  {r['veredito']:<12} {r['s']:>5}s  "
              f"finish={r.get('finish')}  {alvo}" + (f"  (via {r['model']})" if destino is fase_b else ""))
    linhas, rc = analisar(filas, elos, fase_b)
    print("\n".join(linhas))
    if arq_json:
        Path(arq_json).write_text(json.dumps({"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                              "filas": filas, "elos": elos, "fase_b": fase_b},
                                             ensure_ascii=False, indent=1), encoding="utf-8")
    return rc


# --- selftest: OmniRoute + sanitizador falsos, comportamento por nome de modelo ----
def _selftest() -> int:
    import io
    import tempfile
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    tmp = tempfile.mkdtemp()
    tok = Path(tmp) / "token-interno"
    tok.write_text("t" * 40 + "\n", encoding="utf-8")
    os.chmod(tok, 0o600)
    os.environ["AGATA_TOKEN_INTERNO_PATH"] = str(tok)
    import token_interno as _ti                        # já no sys.path pelo _token_interno abaixo
    _ti.CAMINHO = tok
    registro = {"chat": [], "escrita_api": 0, "sem_token": 0}
    combos = [{"id": "c1", "name": "seth-rapido", "models": [
                  {"kind": "model", "model": "p/zero"}, {"kind": "model", "model": "p/ok"},
                  {"kind": "model", "model": "ollama-local/fundo"}]},
              {"id": "c2", "name": "seth-livre", "models": [
                  {"kind": "model", "model": "p/ok"}, {"kind": "model", "model": "p/vazio"},
                  {"kind": "model", "model": "p/texto"}, {"kind": "model", "model": "p/conta"},
                  {"kind": "model", "model": "p/nome"}]},
              {"id": "c3", "name": "seth-pesado", "models": [
                  {"kind": "model", "model": "p/erro"}, {"kind": "model", "model": "p/ruim"},
                  {"kind": "model", "model": "ollama-local/fundo"}]}]

    def sse(*evs, ka=True):
        partes = [b": ka\n\n"] if ka else []
        partes += [b"data: " + json.dumps(e).encode() + b"\n\n" for e in evs]
        return b"".join(partes + [b"data: [DONE]\n\n"])

    def ev(model, delta, fin=None):
        return {"model": model, "choices": [{"index": 0, "delta": delta, "finish_reason": fin}]}

    def tool(model, nome, args):
        return sse(ev(model, {"tool_calls": [{"index": 0, "function": {"name": nome, "arguments": ""}}]}),
                   ev(model, {"tool_calls": [{"index": 0, "function": {"arguments": args}}]}, "tool_calls"))

    respostas = {
        "p/ok": lambda: tool("p/ok", "somar", '{"a": 17, "b": 25}'),
        "ollama-local/fundo": lambda: tool("ollama-local/fundo", "somar", '{"b": 25, "a": 17}'),
        "p/zero": lambda: b": ka\n\n",
        "p/vazio": lambda: sse(ev("p/vazio", {"content": ""}, "length")),
        "p/texto": lambda: sse(ev("p/texto", {"content": "42"}, "stop")),
        "p/ruim": lambda: tool("p/ruim", "somar", '{"a": 17, "b": '),
        "p/conta": lambda: tool("p/conta", "somar", '{"a": 1, "b": 2}'),
        "p/nome": lambda: tool("p/nome", "ferramenta_inerte_00", '{"a": 17, "b": 25}'),
        "seth-rapido": lambda: tool("p/ok", "somar", '{"a": 17, "b": 25}'),
        "seth-livre": lambda: tool("p/ok", "somar", '{"a": 17, "b": 25}'),
        "seth-pesado": lambda: b": ka\n\n",
    }

    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _enviar(self, code, corpo, ctype="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_GET(self):
            self._enviar(200, json.dumps(combos).encode())

        def do_POST(self):
            corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            if self.path.startswith("/api/"):
                registro["escrita_api"] += 1
                return self._enviar(500, b"{}")
            if self.headers.get("X-Agata-Token") != "t" * 40:
                registro["sem_token"] += 1
            registro["chat"].append(corpo["model"])
            registro["ultimo_corpo"] = corpo
            if corpo["model"] == "p/erro":
                return self._enviar(500, b'{"error":"x"}')
            self._enviar(200, respostas[corpo["model"]](), "text/event-stream")

        do_PUT = do_DELETE = lambda self: (registro.__setitem__("escrita_api", registro["escrita_api"] + 1),
                                           self._enviar(500, b"{}"))

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    falhas = 0

    def caso(nome, ok):
        nonlocal falhas
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
        falhas += 0 if ok else 1

    saida = io.StringIO()
    _orig, sys.stdout = sys.stdout, saida
    rc0 = executar(False, ("seth-rapido", "seth-livre", "seth-pesado"), omniroute=base, proxy=base)
    sys.stdout = _orig
    caso("sem --executar: só o plano, nenhum pedido de chat", rc0 == 0 and registro["chat"] == [])
    arq = Path(tmp) / "r.json"
    saida = io.StringIO()
    sys.stdout = saida
    pausas, _sleep = [], time.sleep
    time.sleep = pausas.append
    rc = executar(True, ("seth-rapido", "seth-livre", "seth-pesado"), intervalo=0, timeout=5,
                  arq_json=str(arq), omniroute=base, proxy=base)
    time.sleep = _sleep
    sys.stdout = _orig
    txt = saida.getvalue()
    dados = json.loads(arq.read_text(encoding="utf-8"))
    v = {m: r["veredito"] for m, r in dados["elos"].items()}
    caso("modelo em duas filas é medido uma vez (Fase A)",
         registro["chat"].count("p/ok") == 1 and registro["chat"].count("ollama-local/fundo") == 1)
    caso("ferramenta válida (args em qualquer ordem) -> OK", v["p/ok"] == "OK" and v["ollama-local/fundo"] == "OK")
    caso("só ': ka', nenhum chunk -> ZERO_CHUNKS", v["p/zero"] == "ZERO_CHUNKS")
    caso("chunk sem conteúdo nem ferramenta (finish=length) -> VAZIO", v["p/vazio"] == "VAZIO")
    caso("texto sem ferramenta -> SO_TEXTO (vivo)", v["p/texto"] == "SO_TEXTO")
    caso("argumentos JSON quebrados -> TOOL_RUIM", v["p/ruim"] == "TOOL_RUIM")
    caso("HTTP 500 -> HTTP_500", v["p/erro"] == "HTTP_500")
    caso("argumentos válidos mas conta errada -> TOOL_RUIM", v["p/conta"] == "TOOL_RUIM")
    caso("ferramenta de nome errado -> TOOL_RUIM", v["p/nome"] == "TOOL_RUIM")
    caso("um intervalo entre cada pedido, nunca rajada",
         len(pausas) == len(dados["elos"]) + len(dados["fase_b"]) - 1)
    caso("Fase B: modelo real que atendeu a fila vem do stream",
         dados["fase_b"]["seth-rapido"]["model"] == "p/ok")
    caso("análise: elo 0 morto na seth-rapido", "elo 0 (p/zero) morto" in txt)
    caso("análise: seth-rapido depende de um remoto só", "só p/ok segura a fila" in txt)
    caso("análise: seth-pesado sem remoto vivo + fila inteira falhou -> saída 1",
         "nenhum elo remoto vivo" in txt and "a fila inteira falhou (ZERO_CHUNKS)" in txt and rc == 1)
    caso("ZERO_CHUNKS sinalizado como assinatura do crash", "assinatura do crash" in txt)
    caso("nunca escreve no OmniRoute (nenhum POST/PUT/DELETE em /api)", registro["escrita_api"] == 0)
    caso("todo pedido de chat leva o X-Agata-Token do arquivo próprio", registro["sem_token"] == 0)
    caso("relatório não guarda o texto do modelo", "conteudo" not in json.dumps(dados) and "42" not in txt)
    c = registro["ultimo_corpo"]
    caso("carga com o tamanho da Seth (system >= 8 mil chars, 12 ferramentas, stream)",
         len(c["messages"][0]["content"]) >= 8000 and len(c["tools"]) == 12 and c["stream"] is True)
    saida = io.StringIO()
    sys.stdout = saida
    n0 = len(registro["chat"])
    executar(True, ("seth-rapido",), sem_local=True, intervalo=0, timeout=5, omniroute=base, proxy=base)
    sys.stdout = _orig
    caso("--sem-local pula o fundo local na Fase A",
         "ollama-local/fundo" not in registro["chat"][n0:])
    srv.shutdown()
    print(f"\n{'SELFTEST OK' if not falhas else f'SELFTEST FALHOU ({falhas})'}")
    return 0 if not falhas else 1


def _arg(nome, padrao):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        sys.exit(_selftest())
    sys.exit(executar("--executar" in sys.argv,
                      tuple(_arg("--filas", ",".join(FILAS)).split(",")),
                      sem_local="--sem-local" in sys.argv,
                      intervalo=float(_arg("--intervalo", "8")),
                      timeout=float(_arg("--timeout", "90")),
                      arq_json=_arg("--json", None)))
