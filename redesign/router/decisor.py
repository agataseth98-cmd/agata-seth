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
`winnow:e4b` e nenhum uso fica no caminho quente da resposta.

Uso: python3 redesign/router/decisor.py --selftest
Env: AGATA_DECISOR_URL (default http://127.0.0.1:11435),
     AGATA_DECISOR_MODELO (default winnow:e4b),
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
TIMEOUT_PADRAO = 15.0
# loopback: nunca passar por proxy de ambiente
_ABRIR = urllib.request.build_opener(urllib.request.ProxyHandler({})).open


def decidir(uso: str, state, perguntas: dict, timeout: float = TIMEOUT_PADRAO,
            meta: dict | None = None) -> dict | None:
    """`answers` do Ollaya (dict por id de pergunta) ou None em qualquer falha."""
    t0 = time.monotonic()
    respostas, erro = None, None
    try:
        corpo = json.dumps({"model": MODELO, "state": state, "questions": perguntas}).encode()
        req = urllib.request.Request(URL + "/v1/systemone", corpo,
                                     {"Content-Type": "application/json"})
        with _ABRIR(req, timeout=timeout) as r:
            respostas = json.load(r)["answers"]
        if not isinstance(respostas, dict) or set(respostas) != set(perguntas):
            respostas, erro = None, "resposta sem as perguntas pedidas"
    except Exception as e:  # fronteira com serviço externo: tudo vira None
        respostas, erro = None, f"{type(e).__name__}: {e}"[:200]
    _registrar(uso, respostas, erro, (time.monotonic() - t0) * 1000, meta)
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
    divergências, para o Humano julgar. Arquivo separado, modo 600, apagado
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


def _registrar(uso, respostas, erro, ms, meta):
    linha = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "uso": uso, "modelo": MODELO,
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


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(_selftest())
    print(__doc__)
