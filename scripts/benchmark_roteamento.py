#!/usr/bin/env python3
"""benchmark_roteamento.py — roda o corpus do roteamento por capacidade nos modelos das filas.

Roteamento por capacidade, passo 2b (V9, seção 35). Decisões do Humano em 23/10/2026:
corpus sintético de 30 perguntas fora do repositório; ferramentas com respostas falsas
fixas; anexo grande nas perguntas de contexto longo; anexo do canon só para modelo local
ou provedor liberado.

Sem `--executar`, só mostra o plano: nenhuma chamada. Com `--executar`, gasta cota grátis;
rode à mão. Chama os modelos pelo sanitizador (:20127), sem o gateway: nada de hidratação,
cabeçalho ou registro de pedidos.

Ferramentas: as 5 da Seth vão como definição, com respostas FALSAS e fixas. Nada de
verdade é consultado nem gravado. Mede se o modelo pede a ferramenta certa, com
argumentos JSON válidos, e se usa o resultado.

Privacidade: item `privado` (anexo do canon) só vai para `ollama-local/*` ou para o
prefixo de provedor passado em `--liberar` (vazio por padrão). O resto fica `pulado_privacidade`.

Saída, fora do repositório (0700/0600): `~/.local/share/agata/benchmark/<AAAAmmdd-HHMMSS>/`
  respostas.jsonl  uma linha por item×modelo, com o texto (para o rótulo do Humano)
  resumo.json      por modelo: checagens mecânicas, latência p50/p95, erros e a
                   proveniência de cada medida (protocolo, amostra, provedor, endpoint,
                   versão resolvida, data), no formato do bloco `medido` de
                   config/capivara/capacidades.json. Levar para lá é proposta à parte.

Checagens mecânicas (o resto fica `a_rotular`): JSON válido sem texto em volta; chamou
ferramenta conhecida com argumentos válidos; escrita sem portão (diario_anotar); confiança
em porcentagem.

Cartão de sistema (`--cartao ARQ`, corpus v2, decisão do Humano em 23/10/2026): o mesmo texto curto
vai como mensagem de sistema para todos os modelos, como a Seth recebe; sem ele, vale a frase neutra.
O hash do cartão entra no protocolo de cada medida.

Uso:
  benchmark_roteamento.py [--corpus ARQ] [--cartao ARQ | --prompt-real] [--modelos a,b] [--itens id,id] [--liberar prefixo,...]
  benchmark_roteamento.py --executar [mesmas opções] [--timeout 120] [--intervalo 3]
  benchmark_roteamento.py --selftest
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CORPUS = Path(os.path.expanduser("~/.local/share/agata/corpus-roteamento/corpus-v1.jsonl"))
SAIDA = Path(os.path.expanduser("~/.local/share/agata/benchmark"))
CAPACIDADES = RAIZ / "config" / "capivara" / "capacidades.json"
PROTOCOLO = "benchmark-roteamento-v1"
LOCAL = "ollama-local/"
SISTEMA = "Você é um assistente. Responda em português do Brasil, de forma direta."


def _f(nome, desc, props):
    return {"type": "function", "function": {"name": nome, "description": desc, "parameters": {
        "type": "object", "properties": props, "required": list(props)}}}


_T = {"type": "string"}
FERRAMENTAS = [
    _f("maquina_verificar", "Mede um fato da Máquina (git, serviço, hora). Só leitura.", {"comando": _T}),
    _f("query_canon", "Busca texto no canon (REGRAS, PROTOCOLOS, PROJETO, MEMÓRIAS).", {"consulta": _T}),
    _f("vault_buscar", "Busca por sentido no vault Obsidian.", {"consulta": _T}),
    _f("vault_consultar", "Lê uma nota do vault pelo número.", {"nota": _T}),
    _f("diario_anotar", "GRAVA uma anotação no diário. Escrita: exige confirmação do Humano.", {"texto": _T}),
]
NOMES = {f["function"]["name"] for f in FERRAMENTAS}
FALSAS = {
    "maquina_verificar": "[simulado] HEAD=abc1234 · seth-escriba: active · 2026-10-23 15:00 -0300 · propostas sem assinatura: 1",
    "query_canon": "[simulado] (733) Citação inventada se expurga: descrever o erro sem repetir o literal; "
                   "marcador em arquivo vivo; no canon, só por expurgo assinado.",
    "vault_buscar": "[simulado] (718)/(719) 15/10/2026: o Laya decide a rota da Seth; o Jev fica em sombra.",
    "vault_consultar": "[simulado] nota não encontrada.",
    "diario_anotar": "[simulado] gravado.",
}


# --- puras --------------------------------------------------------------------------
def carregar_corpus(caminho: Path) -> list[dict]:
    return [json.loads(l) for l in caminho.read_text(encoding="utf-8").splitlines() if l.strip()]


def liberado(item: dict, modelo: str, liberar: list[str]) -> bool:
    return not item.get("privado") or modelo.startswith(LOCAL) or any(modelo.startswith(p) for p in liberar)


def mensagem_usuario(item: dict, raiz: Path = RAIZ) -> str:
    partes = [item["pergunta"]]
    for a in item.get("anexos", []):
        partes.append(f"\n\n<<<ANEXO {a}>>>\n" + (raiz / a).read_text(encoding="utf-8") + f"\n<<<FIM {a}>>>")
    return "".join(partes)


_MOLDURA = re.compile(r"^```(?:json)?\s*\n(.*)\n```$", re.S)


def json_estrito(texto: str) -> bool:
    """Só JSON, sem texto em volta. A moldura ```json passa (decisão do Humano, 23/10/2026)."""
    t = texto.strip()
    m = _MOLDURA.match(t)
    try:
        json.loads(m.group(1) if m else t)
        return True
    except ValueError:
        return False


def checar(item: dict, texto: str, chamadas: list[dict]) -> dict:
    c = {}
    if item.get("requisitos", {}).get("so_json"):  # só onde a pergunta pede APENAS JSON
        c["json_valido"] = json_estrito(texto)
    if item.get("requisitos", {}).get("ferramenta") and not item.get("requisitos", {}).get("escrita"):
        # pedido de escrita: o certo é NÃO chamar antes da confirmação; mede-se por escreveu_sem_portao
        c["chamou_ferramenta"] = bool(chamadas)
        c["ferramenta_valida"] = bool(chamadas) and all(x["conhecida"] and x["args_validos"] for x in chamadas)
    if item.get("requisitos", {}).get("escrita"):
        c["escreveu_sem_portao"] = any(x["nome"] == "diario_anotar" for x in chamadas)
    if item["id"] == "conv-04":
        c["deu_porcentagem"] = bool(re.search(r"\d+(?:[.,]\d+)?\s*%", texto))
    return c


def percentil(xs: list[float], p: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))]


def resumir(linhas: list[dict], data: str, corpus_sha: str) -> dict:
    por = {}
    for l in linhas:
        por.setdefault(l["modelo"], []).append(l)
    out = {}
    for m, ls in por.items():
        feitas = [l for l in ls if l["estado"] not in ("pulado_privacidade",)]
        ok = [l for l in feitas if l["estado"] == "ok"]
        reais = sorted({l.get("modelo_real") or "" for l in ok} - {""})
        base = {"protocolo": f"{PROTOCOLO} corpus-sha256:{corpus_sha[:12]}", "provedor": m.split("/", 1)[0],
                "endpoint": m, "versao_resolvida": ",".join(reais) or "nao_medido", "data": data}
        medidas = [dict(base, metrica="taxa_erro", valor=round(1 - len(ok) / len(feitas), 3), amostra=len(feitas))] \
            if feitas else []
        lat = [l["s"] for l in ok]
        if lat:
            medidas += [dict(base, metrica="latencia_p50_s", valor=percentil(lat, 50), amostra=len(lat)),
                        dict(base, metrica="latencia_p95_s", valor=percentil(lat, 95), amostra=len(lat))]
        for chave in ("json_valido", "ferramenta_valida", "escreveu_sem_portao", "deu_porcentagem"):
            vals = [l["checagens"][chave] for l in ok if chave in l["checagens"]]
            if vals:
                medidas.append(dict(base, metrica=chave, valor=round(sum(vals) / len(vals), 3), amostra=len(vals)))
        out[m] = {"feitas": len(feitas), "ok": len(ok),
                  "puladas_privacidade": len(ls) - len(feitas), "medido": medidas}
    return out


def sistema_real(raiz: Path = RAIZ) -> str:
    """(25/10/2026) O system que a Seth recebe de verdade: a hidratação do gateway (`_injeta`).
    O cartão curto escondeu o principal: com o prompt real, o MoE inventava estado (1/9 chamadas)."""
    sys.path.insert(0, str(raiz / "redesign" / "router"))
    os.environ.setdefault("SETH_REPO", str(raiz))
    import seth_gateway  # noqa: E402
    p = seth_gateway._injeta({"model": "seth-livre", "messages": [{"role": "user", "content": "x"}]})
    return p["messages"][0]["content"]


def rodar_item(chamar, modelo: str, item: dict, raiz: Path = RAIZ, sistema: str = SISTEMA, sufixo: str = "") -> dict:
    """Um item num modelo. `chamar(corpo) -> (resposta_json, segundos)` ou levanta."""
    usa_ferr = bool(item.get("requisitos", {}).get("ferramenta"))
    msgs = [{"role": "system", "content": sistema}, {"role": "user", "content": mensagem_usuario(item, raiz)}]
    corpo = {"model": modelo, "stream": False, "max_tokens": 4000, "messages": msgs}
    if usa_ferr or sufixo:  # com o prompt real, sempre (o LibreChat sempre manda) e com os nomes da produção
        corpo["tools"] = [{"type": "function", "function": dict(f["function"], name=f["function"]["name"] + sufixo)}
                          for f in FERRAMENTAS]
    chamadas, total, uso = [], 0.0, []
    try:
        for _ in range(4 if sufixo else 2):  # prompt real: até 3 voltas (o LibreChat deixa várias); cartão: 1
            d, s = chamar(corpo)
            total += s
            uso.append(d.get("usage") or {})
            msg = (d.get("choices") or [{}])[0].get("message") or {}
            tcs = msg.get("tool_calls") or []
            if not tcs:
                break
            corpo["messages"] = corpo["messages"] + [msg]
            for tc in tcs:
                fn = tc.get("function") or {}
                nome = fn.get("name", "").removesuffix(sufixo) if sufixo else fn.get("name", "")
                try:
                    json.loads(fn.get("arguments") or "")
                    args_ok = True
                except ValueError:
                    args_ok = False
                chamadas.append({"nome": nome, "conhecida": nome in NOMES, "args_validos": args_ok})
                corpo["messages"].append({"role": "tool", "tool_call_id": tc.get("id", ""),
                                          "content": FALSAS.get(nome, "[simulado] ferramenta desconhecida.")})
        texto = msg.get("content") or ""
        return {"estado": "ok", "s": round(total, 2), "modelo_real": d.get("model"),
                "finish": (d.get("choices") or [{}])[0].get("finish_reason"), "texto": texto,
                "chamadas": chamadas, "uso": uso, "checagens": checar(item, texto, chamadas)}
    except Exception as e:  # noqa: BLE001
        codigo = getattr(e, "code", None)
        return {"estado": f"erro:{e.__class__.__name__}" + (f":{codigo}" if codigo else ""),
                "erro": str(getattr(e, "corpo", "") or e)[:160], "s": round(total, 2), "texto": "",
                "chamadas": chamadas, "checagens": {}}


# --- rede -------------------------------------------------------------------------------
REPETIR = (429, 502, 503, 504)  # provedor ou fila ocupados: uma nova tentativa, depois de esperar
ESPERA_REPETIR = 10.0


def cabecalhos(token: str, publico: bool) -> dict:
    """O corpus é sintético: vai como `public` (regra de 20/10, b683e4b, no sanitizador). Item
    com anexo do canon só vai como público se o Humano liberou o provedor (--liberar)."""
    h = {"Content-Type": "application/json", "X-Agata-Token": token}
    if publico:
        h["X-Agata-Data-Classification"] = "public"
    return h


def _chamador(timeout: float):
    sys.path.insert(0, str(RAIZ / "scripts"))
    import urllib.error
    import urllib.request
    import queda_por_elo as q  # noqa: E402  (token interno e abridor sem proxy)

    def chamar(corpo, publico=True):
        t0 = time.monotonic()
        for tentativa in range(2):
            req = urllib.request.Request(q.PROXY + "/v1/chat/completions", method="POST",
                                         data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
                                         headers=cabecalhos(q._token_interno(), publico))
            try:
                with q._SEM_PROXY.open(req, timeout=timeout) as r:
                    return json.load(r), time.monotonic() - t0
            except urllib.error.HTTPError as e:
                e.corpo = e.read().decode("utf-8", "replace")[:160]
                if e.code not in REPETIR or tentativa:
                    raise
                time.sleep(ESPERA_REPETIR)
    return chamar


def _modelos_padrao() -> list[str]:
    reg = json.loads(CAPACIDADES.read_text(encoding="utf-8"))
    return sorted({m for fila in reg.get("filas", {}).values() for m in fila})


def _arg(argv, nome, padrao=None):
    return argv[argv.index(nome) + 1] if nome in argv else padrao


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    corpus_p = Path(_arg(argv, "--corpus", str(CORPUS)))
    itens = carregar_corpus(corpus_p)
    if _arg(argv, "--itens"):
        quero = set(_arg(argv, "--itens").split(","))
        itens = [i for i in itens if i["id"] in quero]
    modelos = _arg(argv, "--modelos").split(",") if _arg(argv, "--modelos") else _modelos_padrao()
    liberar = [p for p in (_arg(argv, "--liberar", "") or "").split(",") if p]
    cartao_p = Path(_arg(argv, "--cartao")) if _arg(argv, "--cartao") else None
    sistema = cartao_p.read_text(encoding="utf-8").strip() if cartao_p else SISTEMA
    sufixo = ""
    if "--prompt-real" in argv:  # o system de produção (hidratação do gateway), com os nomes de ferramenta reais
        sistema, sufixo = sistema_real(), "_mcp_canon"
    plano = [(m, i) for m in modelos for i in itens]
    vai = [(m, i) for m, i in plano if liberado(i, m, liberar)]
    print(f"plano: {len(itens)} itens × {len(modelos)} modelos = {len(plano)}; "
          f"{len(vai)} vão rodar, {len(plano) - len(vai)} pulados por privacidade "
          f"(liberados: {', '.join(liberar) or 'só ollama-local'})")
    if "--executar" not in argv:
        print("nada chamado. Para rodar (gasta cota): --executar")
        return 0
    chamar = _chamador(float(_arg(argv, "--timeout", "120")))
    intervalo = float(_arg(argv, "--intervalo", "3"))
    dest = SAIDA / time.strftime("%Y%m%d-%H%M%S")
    dest.mkdir(parents=True, exist_ok=True)
    os.chmod(SAIDA, 0o700)
    os.chmod(dest, 0o700)
    linhas = []
    for n, (m, i) in enumerate(plano, 1):
        if not liberado(i, m, liberar):
            r = {"estado": "pulado_privacidade", "s": 0, "texto": "", "chamadas": [], "checagens": {}}
        else:
            publico = not i.get("privado") or any(m.startswith(p) for p in liberar)
            r = rodar_item(lambda corpo: chamar(corpo, publico), m, i, sistema=sistema, sufixo=sufixo)
            time.sleep(intervalo)
        linhas.append(dict(r, modelo=m, item=i["id"], tipo=i["tipo"], rota_esperada=i.get("rota_esperada")))
        print(f"[{n}/{len(plano)}] {m} {i['id']}: {r['estado']} {r['s']}s {r['checagens']}", flush=True)
    sha = hashlib.sha256(corpus_p.read_bytes() + sistema.encode("utf-8")).hexdigest()  # corpus + cartão
    for nome, conteudo in (("respostas.jsonl", "".join(json.dumps(l, ensure_ascii=False) + "\n" for l in linhas)),
                           ("resumo.json", json.dumps(resumir(linhas, time.strftime("%Y-%m-%d"), sha),
                                                      ensure_ascii=False, indent=2) + "\n")):
        fd = os.open(dest / nome, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(conteudo)
    print(f"gravado em {dest}")
    return 0


def _selftest() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        (raiz / "A.md").write_text("conteúdo do anexo")
        js = {"id": "json-x", "tipo": "json", "pergunta": "só JSON", "requisitos": {"json": True, "so_json": True}}
        jt = {"id": "json-t", "tipo": "json", "pergunta": "explique o JSON", "requisitos": {"json": True}}
        fer = {"id": "fer-x", "tipo": "ferramenta", "pergunta": "meça", "requisitos": {"ferramenta": True}}
        esc = {"id": "fer-e", "tipo": "ferramenta", "pergunta": "anote", "requisitos": {"ferramenta": True, "escrita": True}}
        pct = {"id": "conv-04", "tipo": "conversa", "pergunta": "%?", "requisitos": {}}
        priv = {"id": "longo-x", "tipo": "contexto_longo", "pergunta": "leia", "anexos": ["A.md"], "privado": True}
        enviados = []

        def falso(corpo):
            enviados.append(corpo)
            u = corpo["messages"][-1]
            if corpo.get("tools") and u["role"] == "user":
                nome = "diario_anotar" if "anote" in u["content"] else "maquina_verificar"
                return {"model": "x-real", "choices": [{"message": {"role": "assistant", "content": None,
                        "tool_calls": [{"id": "1", "function": {"name": nome, "arguments": '{"comando": "git"}'}}]}}]}, 0.5
            texto = '{"a": 1}' if "JSON" in u["content"] else ("Confiança: 90%" if "%" in u["content"] else "feito")
            return {"model": "x-real", "choices": [{"message": {"role": "assistant", "content": texto},
                                                     "finish_reason": "stop"}]}, 1.0

        def quebra(corpo):
            raise TimeoutError("lento")

        class Http403(Exception):
            code = 403
            corpo = "dados sem classificação pública"

        def recusa(corpo):
            raise Http403("x")

        rj = rodar_item(falso, "a/m", js, raiz)
        rf = rodar_item(falso, "a/m", fer, raiz)
        re_ = rodar_item(falso, "a/m", esc, raiz)
        rp = rodar_item(falso, "a/m", pct, raiz)
        rl = rodar_item(falso, LOCAL + "m", priv, raiz)
        rc = rodar_item(falso, "a/m", js, raiz, sistema="CARTAO-X")
        rs = rodar_item(falso, "a/m", fer, raiz, sufixo="_mcp_canon")
        rq = rodar_item(quebra, "a/m", js, raiz)
        rh = rodar_item(recusa, "a/m", js, raiz)
        rt = rodar_item(falso, "a/m", jt, raiz)
        linhas = [dict(r, modelo="a/m") for r in (rj, rf, re_, rp, rq)] + \
                 [{"modelo": "a/m", "estado": "pulado_privacidade", "s": 0, "checagens": {}}]
        res = resumir(linhas, "2026-10-23", "f" * 64)["a/m"]
        nomes_med = {x["metrica"] for x in res["medido"]}
        sys.path.insert(0, str(RAIZ / "scripts"))
        import capivara_capacidades as cc  # noqa: E402
        reg = {"modelos": {"a/m": {"catalogo": None, "declarado": None, "medido": res["medido"], "observado": []}}}
        casos = [
            ("JSON estrito: válido", rj["checagens"] == {"json_valido": True}),
            ("JSON com texto em volta é inválido", json_estrito('aqui: {"a":1}') is False),
            ("moldura ```json passa; texto fora da moldura não", json_estrito('```json\n{"a": 1}\n```')
             and json_estrito('```\n[1]\n```') and not json_estrito('veja:\n```json\n{"a": 1}\n```')),
            ("escrita não conta como ferramenta inválida", set(re_["checagens"]) == {"escreveu_sem_portao"}),
            ("ferramenta: chama, recebe a falsa e responde", rf["checagens"] == {"chamou_ferramenta": True,
             "ferramenta_valida": True} and rf["texto"] == "feito"
             and any(m.get("role") == "tool" and m["content"].startswith("[simulado]")
                     for c in enviados for m in c["messages"])),
            ("escrita sem portão é marcada", re_["checagens"].get("escreveu_sem_portao") is True),
            ("confiança em % é marcada", rp["checagens"].get("deu_porcentagem") is True),
            ("anexo vai na mensagem", any("conteúdo do anexo" in c["messages"][1]["content"] for c in enviados)),
            ("privado: só local ou liberado", liberado(priv, LOCAL + "m", []) and not liberado(priv, "a/m", [])
             and liberado(priv, "a/m", ["a/"])),
            ("erro de rede vira estado, não derruba", rq["estado"] == "erro:TimeoutError"),
            ("resumo: taxa de erro conta só as feitas", any(x["metrica"] == "taxa_erro" and x["valor"] == 0.2
                                                             and x["amostra"] == 5 for x in res["medido"])),
            ("resumo: pulada por privacidade fica fora", res["puladas_privacidade"] == 1),
            ("resumo: métricas mecânicas presentes", {"json_valido", "ferramenta_valida", "escreveu_sem_portao",
                                                      "deu_porcentagem", "latencia_p95_s"} <= nomes_med),
            ("medidas passam na conferência do registro", cc.conferir(reg) == []),
            ("JSON estrito só onde a pergunta pede apenas JSON", "json_valido" not in rt["checagens"]),
            ("erro HTTP guarda o código e o motivo", rh["estado"] == "erro:Http403:403"
             and "classificação" in rh["erro"]),
            ("corpus sintético vai como público; privado não", cabecalhos("t", True).get(
                "X-Agata-Data-Classification") == "public" and "X-Agata-Data-Classification" not in cabecalhos("t", False)),
            ("prompt real: ferramentas com o sufixo da produção, chamada reconhecida sem ele",
             any(t["function"]["name"] == "maquina_verificar_mcp_canon" for c in enviados for t in c.get("tools") or [])
             and rs["chamadas"] and rs["chamadas"][0]["nome"] in NOMES),
            ("cartão de sistema vai como 1ª mensagem", rc["estado"] == "ok"
             and any(c["messages"][0] == {"role": "system", "content": "CARTAO-X"} for c in enviados)),
            ("percentil", percentil([1, 2, 3, 4], 50) in (2, 3) and percentil([], 95) is None),
        ]
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
