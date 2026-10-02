#!/usr/bin/env python3
"""combos_sem_cota.py -- cria/atualiza os combos gêmeos "<rota>-sg" da Seth no OmniRoute.

Por quê (02/10/2026, MEMÓRIAS (627)-(631)): os 3 combos da Seth (seth-rapido,
seth-livre, seth-pesado) começam no `groq/openai/gpt-oss-120b`, cujo plano grátis
aceita 8.000 tokens por minuto. O OmniRoute não deixa pular a posição 0 de um
combo por pedido; então cada combo ganha um gêmeo `-sg` ("sem Groq"): MESMA
ordem, MESMOS modelos, sem o modelo cotado. O `seth_gateway` escolhe o gêmeo
quando o pedido não cabe na cota que sobra no minuto (SETH_ROTA_COTA=1).

O gêmeo é DERIVADO do combo vivo a cada execução -- nunca uma lista escrita à
mão aqui. Assim a ordem que o Humano escolhe na UI (ex.: (546)) continua sendo
a fonte da verdade, e o gêmeo só repete essa ordem sem o tier cotado.

Uso:
  python3 scripts/combos_sem_cota.py            # só mostra o plano (padrão, não escreve nada)
  python3 scripts/combos_sem_cota.py --aplicar  # cria (POST) ou atualiza (PUT) os -sg
  python3 scripts/combos_sem_cota.py --selftest # testa contra um OmniRoute falso local

Só stdlib. Fala só com o OmniRoute local (OMNIROUTE_URL, padrão
http://127.0.0.1:20128). Não lê ~/.config/agata/.env nem chave nenhuma.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE = os.environ.get("OMNIROUTE_URL", "http://127.0.0.1:20128").rstrip("/")
ROTAS = ("seth-rapido", "seth-livre", "seth-pesado")
SUFIXO = "-sg"
MODELO_COTADO = "groq/openai/gpt-oss-120b"


def _req(metodo: str, caminho: str, corpo: dict | None = None, base: str = BASE):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    r = urllib.request.Request(base + caminho, data=dados, method=metodo,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=15) as resp:
        txt = resp.read().decode("utf-8") or "null"
    return json.loads(txt)


def _lista(resp) -> list:
    """GET /api/combos pode vir como lista ou como {"combos": [...]}; aceita os dois."""
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict):
        for k in ("combos", "data", "items"):
            if isinstance(resp.get(k), list):
                return resp[k]
    raise SystemExit(f"formato inesperado de /api/combos: {type(resp).__name__} -- confira a API antes")


def _id_modelo(m) -> str:
    return (m.get("model") or m.get("id") or "") if isinstance(m, dict) else str(m)


def planejar(combos: list) -> list[tuple[str, str | None, dict]]:
    """[(nome_sg, id_existente_ou_None, corpo)] para cada rota encontrada."""
    por_nome = {c.get("name"): c for c in combos if isinstance(c, dict)}
    plano = []
    for rota in ROTAS:
        orig = por_nome.get(rota)
        if orig is None:
            raise SystemExit(f"combo {rota!r} não existe no OmniRoute -- nada a derivar; pare e confira")
        modelos = [m for m in orig.get("models") or [] if _id_modelo(m) != MODELO_COTADO]
        if not modelos:
            raise SystemExit(f"{rota}: sem o modelo cotado não sobra nenhum -- não crio combo vazio")
        if len(modelos) == len(orig.get("models") or []):
            print(f"aviso: {rota} não tem {MODELO_COTADO}; o gêmeo sai igual ao original")
        nome = rota + SUFIXO
        corpo = {"name": nome, "strategy": orig.get("strategy", "priority"),
                 "models": [{k: v for k, v in m.items() if k != "id"} if isinstance(m, dict) else m
                            for m in modelos]}
        existente = por_nome.get(nome)
        plano.append((nome, existente.get("id") if existente else None, corpo))
    return plano


def executar(aplicar: bool, base: str = BASE) -> int:
    plano = planejar(_lista(_req("GET", "/api/combos", base=base)))
    for nome, cid, corpo in plano:
        ordem = " -> ".join(_id_modelo(m) for m in corpo["models"])
        print(f"{'PUT ' + cid if cid else 'POST'}  {nome}  [{corpo['strategy']}]  {ordem}")
        if aplicar:
            if cid:
                _req("PUT", f"/api/combos/{cid}", corpo, base=base)
            else:
                _req("POST", "/api/combos", corpo, base=base)
    if not aplicar:
        print("(só o plano -- nada escrito; rode com --aplicar)")
    else:
        vivos = {c.get("name") for c in _lista(_req("GET", "/api/combos", base=base))}
        faltam = [n for n, _, _ in plano if n not in vivos]
        if faltam:
            print(f"FALHA: depois de aplicar, não achei {faltam} no GET -- confira a API")
            return 1
        print("OK: os 3 combos -sg existem no OmniRoute")
    return 0


def _selftest() -> int:
    estado = {"combos": [
        {"id": "a1", "name": "seth-livre", "strategy": "priority", "models": [
            {"id": "x", "kind": "model", "model": MODELO_COTADO, "weight": 0},
            {"id": "y", "kind": "model", "model": "zai/glm-4.7-flash", "weight": 0}]},
        {"id": "a2", "name": "seth-rapido", "strategy": "priority", "models": [
            {"id": "x", "kind": "model", "model": MODELO_COTADO, "weight": 0},
            {"id": "z", "kind": "model", "model": "mistral/ministral-14b-latest", "weight": 0}]},
        {"id": "a3", "name": "seth-pesado", "strategy": "priority", "models": [
            {"id": "x", "kind": "model", "model": MODELO_COTADO, "weight": 0},
            {"id": "w", "kind": "model", "model": "gemini/gemini-2.5-flash", "weight": 0}]},
        {"id": "a4", "name": "seth-livre-sg", "strategy": "priority", "models": []}]}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _resp(self, obj):
            b = json.dumps(obj).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            self._resp(estado["combos"])

        def _corpo(self):
            return json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))

        def do_POST(self):
            c = self._corpo()
            c["id"] = f"n{len(estado['combos'])}"
            estado["combos"].append(c)
            self._resp(c)

        def do_PUT(self):
            cid = self.path.rsplit("/", 1)[-1]
            c = self._corpo()
            for i, x in enumerate(estado["combos"]):
                if x["id"] == cid:
                    estado["combos"][i] = {**c, "id": cid}
            self._resp(c)

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    falhas = 0
    antes = json.dumps(estado, sort_keys=True)
    executar(False, base)
    ok = json.dumps(estado, sort_keys=True) == antes
    print(f"{'PASS' if ok else 'FALHA'}  sem --aplicar não escreve nada"); falhas += 0 if ok else 1
    rc = executar(True, base)
    por = {c["name"]: c for c in estado["combos"]}
    ok = (rc == 0 and all(r + SUFIXO in por for r in ROTAS)
          and all(_id_modelo(m) != MODELO_COTADO for r in ROTAS for m in por[r + SUFIXO]["models"]))
    print(f"{'PASS' if ok else 'FALHA'}  --aplicar cria/atualiza os 3 -sg sem o modelo cotado"); falhas += 0 if ok else 1
    ok = [_id_modelo(m) for m in por["seth-livre-sg"]["models"]] == ["zai/glm-4.7-flash"] and por["seth-livre-sg"]["id"] == "a4"
    print(f"{'PASS' if ok else 'FALHA'}  -sg existente é atualizado (PUT no mesmo id), ordem preservada"); falhas += 0 if ok else 1
    ok = [_id_modelo(m) for m in por["seth-livre"]["models"]][0] == MODELO_COTADO
    print(f"{'PASS' if ok else 'FALHA'}  combo original intocado"); falhas += 0 if ok else 1
    srv.shutdown()
    print(f"\n{'SELFTEST OK' if not falhas else f'SELFTEST FALHOU ({falhas})'}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(executar("--aplicar" in sys.argv))
