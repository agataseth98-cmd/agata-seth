#!/usr/bin/env python3
"""Decisor local -- cliente do Ollaya (`POST :11435/v1/systemone`), modelos de
decisão no estilo Jev rodando na CPU. Padrão "decide e confere" (PROJETO.md,
"Decisor local"): quem chama mantém a regra determinística e usa a resposta
daqui só para decidir DENTRO do que a regra permite, ou para RESTRINGIR
(barrar, avisar). Nunca libera o que a regra barrou; nunca reprova commit.

Contrato: `decidir` NUNCA levanta exceção. Serviço fora do ar, timeout,
modelo ausente, JSON inesperado -> `None`, e o chamador segue pela regra.

Cada chamada vira uma linha em `~/.cache/agata/decisor/<uso>.jsonl` (respostas,
latência, erro e os metadados que o chamador passar) -- é o dado para calibrar.
O TEXTO avaliado nunca vai para o log: só tamanhos e respostas.

Medição de 13/10/2026 (20 pedidos pt-BR rotulados, CPU i7-13650HX):
`winnow:e4b` 20/20 em ~4,3 s; `laya`/`laya:multilingual`/`gliclass` 10/20 ou
menos em ~50-200 ms; heurística por tamanho 5/20. Por isso o padrão é
`winnow:e4b` e nenhum uso do Jev fica no caminho quente da resposta. Exceção desde
(719), decisão do Humano: o Laya ajustado (~70 ms) escolhe a fila da Seth, com a regra
por tamanho de reserva; o Jev fica como sombra dele.

(718)/(719) Laya ajustado que escolhe a fila da Seth (o Jev em sombra): `laya-serve`
(`config/laya-roteador.service`, `:11436`, mesmo protocolo `/v1/systemone`),
checkpoint treinado com dados sintéticos fora do repo. `decidir(..., url=URL_LAYA,
modelo=MODELO_LAYA)` -- o mesmo contrato: nunca levanta, falha vira `None`.

Uso: python3 redesign/router/decisor.py --selftest
Env: AGATA_DECISOR_URL (default http://127.0.0.1:11435),
     AGATA_DECISOR_MODELO (default winnow:e4b),
     AGATA_LAYA_URL (default http://127.0.0.1:11436), AGATA_LAYA_MODELO (default roteador),
     AGATA_DECISOR_LOG (default ~/.cache/agata/decisor)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

URL = os.environ.get("AGATA_DECISOR_URL", "http://127.0.0.1:11435").rstrip("/")
MODELO = os.environ.get("AGATA_DECISOR_MODELO", "winnow:e4b")
LOG_DIR = Path(os.environ.get("AGATA_DECISOR_LOG", "~/.cache/agata/decisor")).expanduser()
URL_LAYA = os.environ.get("AGATA_LAYA_URL", "http://127.0.0.1:11436").rstrip("/")
MODELO_LAYA = os.environ.get("AGATA_LAYA_MODELO", "roteador")
TIMEOUT_PADRAO = 15.0
# loopback: nunca passar por proxy de ambiente
_ABRIR = urllib.request.build_opener(urllib.request.ProxyHandler({})).open


def decidir(uso: str, state, perguntas: dict, timeout: float = TIMEOUT_PADRAO,
            meta: dict | None = None, url: str | None = None,
            modelo: str | None = None) -> dict | None:
    """`answers` do Ollaya (ou de outro servidor `/v1/systemone`, com `url`/`modelo`)
    -- dict por id de pergunta -- ou None em qualquer falha."""
    t0 = time.monotonic()
    respostas, erro = None, None
    url, modelo = (url or URL), (modelo or MODELO)
    try:
        corpo = json.dumps({"model": modelo, "state": state, "questions": perguntas}).encode()
        req = urllib.request.Request(url + "/v1/systemone", corpo,
                                     {"Content-Type": "application/json"})
        with _ABRIR(req, timeout=timeout) as r:
            respostas = json.load(r)["answers"]
        if not isinstance(respostas, dict) or set(respostas) != set(perguntas):
            respostas, erro = None, "resposta sem as perguntas pedidas"
    except Exception as e:  # fronteira com serviço externo: tudo vira None
        respostas, erro = None, f"{type(e).__name__}: {e}"[:200]
    _registrar(uso, respostas, erro, (time.monotonic() - t0) * 1000, meta, modelo)
    return respostas


def escolha(respostas: dict | None, pergunta: str, limiar: float) -> str | None:
    """Rótulo de uma pergunta `choice` se `confidence >= limiar`, senão None."""
    try:
        a = respostas[pergunta]
        return a["choice"] if a["confidence"] >= limiar else None
    except (TypeError, KeyError):
        return None


def probabilidade(respostas: dict | None, pergunta: str) -> float | None:
    """Probabilidade de uma pergunta `noul`, ou None."""
    try:
        return float(respostas[pergunta]["noul"])
    except (TypeError, KeyError, ValueError):
        return None


def nota(respostas: dict | None, pergunta: str) -> float | None:
    """Nível esperado de uma pergunta `score`, ou None."""
    try:
        return float(respostas[pergunta]["score"])
    except (TypeError, KeyError, ValueError):
        return None


def registrar_avaliacao(uso: str, dados: dict) -> None:
    """Eventos da avaliação em produção (PROJETO.md, "Decisor local"): o que
    aconteceu depois da decisão, para medir se ela acertou. Única exceção à
    regra "texto fora do log": o roteador guarda 200 caracteres das
    divergências, para o Humano julgar -- as da heurística contra o Jev
    (`roteador`) e, desde (718), as do Laya contra o Jev (`roteador-laya`). Arquivo separado, modo 600, apagado
    inteiro por `scripts/avaliar_decisor.py --encerrar`."""
    caminho = LOG_DIR / f"{uso}-avaliacao.jsonl"
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        fd = os.open(caminho, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **dados},
                               ensure_ascii=False) + "\n")
    except OSError:
        pass


def _registrar(uso, respostas, erro, ms, meta, modelo=None):
    linha = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "uso": uso, "modelo": modelo or MODELO,
             "ms": round(ms), "respostas": respostas, "erro": erro, **(meta or {})}
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_DIR / f"{uso}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
    except OSError:
        pass  # log é para calibrar; sem ele a decisão continua valendo


def _selftest() -> int:
    import tempfile
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    global URL, LOG_DIR
    modo = {"v": "ok"}

    class _Falso(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            pedido = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if modo["v"] == "404":
                self.send_response(404)
                self.end_headers()
                return
            if modo["v"] == "lento":
                time.sleep(1.5)
            ans = {k: ({"type": "choice", "choice": "b", "confidence": 0.9,
                        "probabilities": {"a": 0.05, "b": 0.95}} if v["type"] == "choice"
                       else {"type": "noul", "noul": 0.2}) for k, v in pedido["questions"].items()}
            if modo["v"] == "incompleto":
                ans = {}
            corpo = json.dumps({"model": pedido["model"], "answers": ans}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            try:
                self.wfile.write(corpo)
            except BrokenPipeError:
                pass  # caso "lento": o cliente já desistiu por timeout

    srv = HTTPServer(("127.0.0.1", 0), _Falso)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    URL = f"http://127.0.0.1:{srv.server_port}"
    LOG_DIR = Path(tempfile.mkdtemp()) / "decisor"
    q = {"r": {"type": "choice", "criteria": ["a", "b"]}, "s": {"type": "noul"}}
    casos = []

    r = decidir("teste", "x", q)
    casos.append(("resposta normal -> escolha e probabilidade",
                  escolha(r, "r", 0.6) == "b" and probabilidade(r, "s") == 0.2))
    casos.append(("confiança abaixo do limiar -> None", escolha(r, "r", 0.95) is None))
    modo["v"] = "404"
    casos.append(("HTTP 404 -> None", decidir("teste", "x", q) is None))
    modo["v"] = "incompleto"
    casos.append(("resposta sem as perguntas -> None", decidir("teste", "x", q) is None))
    modo["v"] = "lento"
    casos.append(("timeout -> None", decidir("teste", "x", q, timeout=0.3) is None))
    modo["v"] = "ok"
    r2 = decidir("teste-laya", "x", q, url=URL, modelo="roteador")
    l2 = (LOG_DIR / "teste-laya.jsonl").read_text().splitlines()
    casos.append(("(718) url/modelo próprios: mesma resposta, log com o modelo pedido",
                  escolha(r2, "r", 0.6) == "b" and json.loads(l2[0])["modelo"] == "roteador"))
    srv.shutdown()
    srv.server_close()
    casos.append(("serviço fora do ar -> None", decidir("teste", "x", q, timeout=1) is None))
    casos.append(("helpers com None -> None", escolha(None, "r", 0) is None
                  and probabilidade(None, "s") is None and nota(None, "s") is None))
    linhas = (LOG_DIR / "teste.jsonl").read_text().splitlines()
    casos.append(("1 linha de log por chamada, texto avaliado fora do log",
                  len(linhas) == 5 and all('"x"' not in l for l in linhas)))

    falhas = 0
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
        falhas += not ok
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


# (705) Segunda opinião local para a Seth: pedido de opinião, decisão ou risco. Mesmo
# formato de pergunta tipada do roteador (seth_gateway._PERGUNTA_ROTA). É opinião de um
# modelo de decisão na CPU -- nunca fato, nunca decide pelo Humano.
PERGUNTAS_OPINIAO = {
    "recomendacao": {"type": "choice",
                     "instructions": "Given this proposed action or question, what is the sensible recommendation?",
                     "criteria": {"fazer": "do it: the benefit clearly outweighs the risk",
                                  "nao_fazer": "don't: the risk or cost outweighs the benefit",
                                  "depende": "it depends on missing information: measure or ask first"}},
    "reversivel": {"type": "noul", "instructions": "The action can be undone easily, without outside help."},
    "risco": {"type": "noul", "instructions": "The action could cause data loss, a service outage or a leak of secrets."},
}


def opinar(texto: str, timeout: float = 40.0) -> str:
    r = decidir("opiniao", texto, PERGUNTAS_OPINIAO, timeout=timeout)
    if r is None:
        return "decisor local indisponível (Ollaya fora do ar ou estourou o prazo) — sem segunda opinião desta vez."
    rec = r.get("recomendacao") or {}
    p_rev, p_risco = probabilidade(r, "reversivel"), probabilidade(r, "risco")
    fmt = lambda p: "?" if p is None else f"{p:.2f}"
    return (f"opinião do decisor local ({MODELO}, CPU; é opinião de um modelo de decisão, não fato): "
            f"recomendação={rec.get('choice', '?')} (confiança {fmt(rec.get('confidence'))}) · "
            f"reversível p={fmt(p_rev)} · risco p={fmt(p_risco)}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(_selftest())
    if len(sys.argv) == 4 and sys.argv[1:3] == ["--opinar", "--"]:
        print(opinar(sys.argv[3]))
        sys.exit(0)
    print(__doc__)
