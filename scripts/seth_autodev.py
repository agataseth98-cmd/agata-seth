#!/usr/bin/env python3
"""seth_autodev.py -- ferramenta de AUTODESENVOLVIMENTO da Seth, com o Humano no laço (17/10/2026).

O ciclo (estado da arte em 2026: desenvolvimento guiado por avaliação, recompensa verificável, mudança só com A/B):
  1. RODAR   uma bateria de casos com resposta esperada CALCULADA na hora, pelo mesmo caminho da produção: o gateway (:20126, com hidratação,
             rédea e cabeçalho) e as MESMAS ferramentas (o servidor MCP canon-mcp.mjs, só as de leitura), sem navegador, sem áudio, sem conversa do Humano.
  2. PONTUAR sem modelo: conferência determinística (golden + citação inventada).
  3. DIAGNOSTICAR cada falha por regra (descrição da ferramenta, erro mal lido, entrada cortada, citação inventada, sem ferramenta...) e dizer QUAL
             mudança propor. A ferramenta NUNCA edita o repositório: a mudança é uma proposta P-8, assinada pelo Humano.
  4. COMPARAR duas rodadas (antes/depois): melhora, regressão, e se atingiu a meta (padrão 90%).

Segurança: só ferramentas de leitura (lista fechada: query_canon, vault_consultar, vault_buscar, maquina_verificar); escrita da Seth (diario_anotar,
memoria_acrescentar) é RECUSADA; um caso por vez; teto de chamadas ao gateway por rodada; aborta após 3 erros seguidos de infraestrutura; resultados só em
~/.cache/agata/autodev/ (modo 700); nenhum segredo lido; a resposta da Seth é tratada como dado.

TRANSPARÊNCIA COM O HUMANO NO LAÇO (visual): a cada caso a ferramenta regrava um PAINEL ao vivo, `~/.cache/agata/autodev/painel.html`, para o Humano
abrir no navegador (file://, sem porta, sem rede, sem script): placar contra a meta, cada caso com pergunta, ferramentas chamadas e resposta. O
Humano PARA a rodada quando quiser com `touch ~/.cache/agata/autodev/parar` (checado entre os casos). Nada do que a Seth escreve é executado: tudo
no painel é escapado.

Uso:
  seth_autodev.py --rodar [--suite ouro|gerada|tudo] [--ids a,b] [--instrucao ARQ] [--max-casos N] [--max-chamadas N] [--saida ARQ] [--abrir]
  seth_autodev.py --diagnosticar ARQ        o que propor, por causa
  seth_autodev.py --comparar ANTES DEPOIS [--meta 0.9]
  seth_autodev.py --selftest
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GATEWAY = os.environ.get("SETH_GATEWAY", "http://127.0.0.1:20126").rstrip("/")
MODELO = os.environ.get("SETH_AUTODEV_MODELO", "seth-livre")
MCP_SERVIDOR = RAIZ / "redesign" / "librechat" / "canon-mcp.mjs"
PERMITIDAS = ("query_canon", "vault_consultar", "vault_buscar", "maquina_verificar")
SAIDA_DIR = Path(os.environ.get("AGATA_AUTODEV_DIR", str(Path.home() / ".cache" / "agata" / "autodev")))
MAX_PASSOS = 6
MAX_SAIDA_FERRAMENTA = 12000
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "redesign" / "router"))


def _n(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.replace("*", "").replace("`", "").split()).casefold()


# ------------------------------------------------------------------ cliente MCP (stdio, JSON-RPC por linha)
class MCP:
    def __init__(self, argv):
        env = dict(os.environ)
        self.p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env, bufsize=1)
        self._id = 0

    def _enviar(self, obj):
        self.p.stdin.write(json.dumps(obj) + "\n")
        self.p.stdin.flush()

    def _ler(self, id_, prazo=60):
        resultado = {}

        def _l():
            while True:
                linha = self.p.stdout.readline()
                if not linha:
                    return
                try:
                    o = json.loads(linha)
                except ValueError:
                    continue
                if o.get("id") == id_:
                    resultado["o"] = o
                    return
        t = threading.Thread(target=_l, daemon=True)
        t.start()
        t.join(prazo)
        if "o" not in resultado:
            raise TimeoutError("MCP sem resposta")
        return resultado["o"]

    def _chamar(self, metodo, params=None, prazo=60):
        self._id += 1
        self._enviar({"jsonrpc": "2.0", "id": self._id, "method": metodo, "params": params or {}})
        o = self._ler(self._id, prazo)
        if "error" in o:
            raise RuntimeError(str(o["error"])[:200])
        return o.get("result", {})

    def iniciar(self):
        self._chamar("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "seth-autodev", "version": "1"}})
        self._enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def ferramentas(self):
        return [t for t in self._chamar("tools/list").get("tools", []) if t.get("name") in PERMITIDAS]

    def chamar(self, nome, args):
        if nome not in PERMITIDAS:
            return f"RECUSADA: '{nome}' não é ferramenta de leitura permitida ao autodesenvolvimento."
        r = self._chamar("tools/call", {"name": nome, "arguments": args or {}}, prazo=90)
        txt = "".join(c.get("text", "") for c in r.get("content", []) if isinstance(c, dict))
        return txt[:MAX_SAIDA_FERRAMENTA]

    def fechar(self):
        try:
            self.p.stdin.close()
            self.p.terminate()
        except OSError:
            pass


# ------------------------------------------------------------------ o laço do Agent (réplica do que o LibreChat faz, só leitura)
def _post_gateway(payload, prazo=170):
    req = urllib.request.Request(GATEWAY + "/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=prazo).read())


def rodar_caso(pergunta, mcp, post=_post_gateway, max_passos=MAX_PASSOS, sistema=None):
    tools = [{"type": "function", "function": {"name": t["name"], "description": t.get("description", "")[:1500],
                                               "parameters": t.get("inputSchema", {"type": "object"})}} for t in mcp.ferramentas()]
    msgs = ([{"role": "system", "content": sistema}] if sistema else []) + [{"role": "user", "content": pergunta}]
    chamadas, erros, chamadas_gw = [], [], 0
    for passo in range(max_passos):
        try:
            r = post({"model": MODELO, "stream": False, "messages": msgs, "tools": tools})
            chamadas_gw += 1
        except Exception as e:  # noqa: BLE001
            return {"texto": "", "chamadas": chamadas, "passos": passo, "erro": f"gateway:{type(e).__name__}", "gw": chamadas_gw, "saidas": erros}
        m = (r.get("choices") or [{}])[0].get("message", {})
        tcs = m.get("tool_calls") or []
        if not tcs:
            return {"texto": m.get("content") or "", "chamadas": chamadas, "passos": passo + 1, "erro": None, "gw": chamadas_gw, "saidas": erros}
        msgs.append({"role": "assistant", "content": m.get("content") or "", "tool_calls": tcs})
        for tc in tcs:
            nome = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except ValueError:
                args = {}
            chamadas.append({"nome": nome, "args": args})
            try:
                saida = mcp.chamar(nome, args)
            except Exception as e:  # noqa: BLE001
                saida = f"ERRO DA FERRAMENTA: {type(e).__name__}"
            erros.append(saida[:200])
            msgs.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": saida})
    return {"texto": "", "chamadas": chamadas, "passos": max_passos, "erro": "sem_resposta_final(laço de ferramentas)", "gw": chamadas_gw, "saidas": erros}


# ------------------------------------------------------------------ casos: ouro (golden) + gerados (verdade na hora)
UNIDADES = ["seth-gateway.service", "seth-escriba.service", "seth-verificador.service", "piper-tts.service", "omniroute.service",
            "laya-roteador.service", "agata-vigia@claude.service", "agata-vigia@codex.service", "agata-manutencao.timer",
            "agata-vault-inbox.timer", "agata-laya-treino.timer", "agata-consolidacao.timer", "agata-avaliacao-decisor.timer",
            "agata-pesquisa-modelos.timer"]


def _estado_unidade(u):
    r = subprocess.run(["systemctl", "--user", "show", "--no-pager", "-p", "LoadState,ActiveState", "--", u], capture_output=True, text=True)
    d = dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)
    if d.get("LoadState") == "not-found":
        return "inexistente"
    return "ativo" if d.get("ActiveState") == "active" else "inativo"


def casos_ouro():
    import seth_golden as g
    return [{"id": c["id"], "origem": "ouro", "pergunta": c["pergunta"], "caso": c} for c in g.carregar()]


def casos_gerados(raiz=RAIZ):
    import auditoria_turno as a
    idx = a._entradas(raiz)
    out = []
    for N in range(700, 800):
        e = idx.get(N)
        if not e:
            continue
        iguais = [int(x) for x, y in set(re.findall(r"\b(\d{1,3})/(\d{1,3})\b", e)) if x == y and int(x) >= 5]
        if iguais:
            out.append({"id": f"num-{N}", "origem": "gerada", "tipo": "numero", "N": N, "verdade": str(max(iguais)), "pos": e.find(f"{max(iguais)}/{max(iguais)}"),
                        "pergunta": f"Com query_canon, qual o MAIOR número de testes passados no formato a/a (como 18/18) citado na entrada ({N})? Responda só o número."})
    for u in UNIDADES:
        out.append({"id": f"uni-{u}", "origem": "gerada", "tipo": "unidade", "N": u, "verdade": _estado_unidade(u),
                    "pergunta": f"Use maquina_verificar com o comando unidade e consulta {u}. Ela existe e está ativa? Responda numa linha: ativa, inativa ou não existe."})
    return out


def pontuar(caso, res, raiz=RAIZ):
    """-> (passou:bool, motivos:list[str])."""
    import auditoria_turno as a
    texto = res.get("texto", "")
    if res.get("erro"):
        return False, [f"erro:{res['erro']}"]
    if len(texto.strip()) < 3:
        return False, ["resposta vazia"]
    motivos = []
    if a._citacao_inventada(texto, raiz):
        motivos.append("citação inventada")
    corpo = _n("\n".join(texto.splitlines()[1:])) if re.match(r"\s*(agata-seth|agata)\s*·", texto, re.I) else _n(texto)
    if caso["origem"] == "ouro":
        import seth_golden as g
        v = g.verdade(caso["caso"], raiz)
        crit = g.julgar(caso["caso"], v, texto, raiz)
        motivos += [n for n, ok, _ in crit if not ok]
    elif caso["tipo"] == "numero":
        _ls = [l for l in texto.splitlines()[1 if re.match(r"\s*(agata-seth|agata)\s*·", texto, re.I) else 0:] if l.strip()]
        ult = _n(_ls[-1]) if _ls else ""
        if not re.search(rf"\b{re.escape(caso['verdade'])}\b", ult):
            motivos.append("número errado ou ausente")
    elif caso["tipo"] == "unidade":
        neg = re.search(r"\b(nao esta ativ|inativ|nao ativ|parad|dead)", corpo) is not None
        nex = re.search(r"(nao existe|inexistente|not-found|nao encontr)", corpo) is not None
        pos = re.search(r"\b(ativ[ao]|active|running)\b", corpo) is not None
        v = caso["verdade"]
        ok = (pos and not neg and not nex) if v == "ativo" else (nex if v == "inexistente" else (neg and not nex))
        if not ok:
            motivos.append("estado da unidade errado")
    return (not motivos), motivos


# ------------------------------------------------------------------ diagnóstico por regra: qual mudança propor
CAUSAS = {
    "descricao_ferramenta": "a descrição/esquema da ferramenta no cliente MCP não deixou claro qual comando usar (ver canon-mcp.mjs)",
    "erro_mal_lido": "a ferramenta devolveu erro e a Seth o leu como resposta de domínio; tornar o texto do erro explícito e apontar o comando certo",
    "entrada_cortada": "o número estava depois do corte da rédea de entradas literais; subir o teto ou enviar o trecho certo",
    "citacao_inventada": "citação entre aspas que não está na entrada; reforçar o filtro/expurgo e a rédea",
    "sem_ferramenta": "respondeu sem chamar nenhuma ferramenta; exigir a chamada no pedido ou na rédea",
    "laco_ferramentas": "laço de chamadas sem resposta final; teto de passos e instrução de uma só chamada",
    "infra": "erro de gateway/fila; ver o log do gateway (fila inexistente, cota, tempo)",
    "leitura_errada": "usou a ferramenta certa e leu errado a saída; pode pedir a saída filtrada ou o trecho literal",
}


def diagnosticar(caso, res, motivos):
    if res.get("erro", "") and "gateway" in res["erro"]:
        return "infra"
    if res.get("erro", "") and "laço" in res["erro"]:
        return "laco_ferramentas"
    if "citação inventada" in motivos:
        return "citacao_inventada"
    nomes = [c["nome"] for c in res.get("chamadas", [])]
    if not nomes:
        return "sem_ferramenta"
    saidas = " ".join(res.get("saidas", [])).lower()
    if caso.get("tipo") == "unidade" and "unidade" not in nomes and not any(c["args"].get("comando") == "unidade" for c in res["chamadas"] if c["nome"] == "maquina_verificar"):
        return "descricao_ferramenta"
    if "não aceita" in saidas or "inválid" in saidas or "recusad" in saidas or "erro da ferramenta" in saidas:
        return "erro_mal_lido"
    if caso.get("tipo") == "numero" and caso.get("pos", 0) > 6000:
        return "entrada_cortada"
    return "leitura_errada"


# ------------------------------------------------------------------ painel visual (Humano no laço)
def _esc(s):
    import html
    return html.escape(str(s), quote=True)


def painel_html(dados, em_curso, total, atual=None, meta=0.9):
    rs = [r for r in dados["registros"] if r.get("passou") is not None]
    ok = sum(1 for r in rs if r["passou"])
    pct = round(100 * ok / max(1, len(rs)))
    cor = "#2e7d32" if pct >= round(100 * meta) else ("#b26a00" if pct >= 60 else "#b3261e")
    linhas = []
    for r in dados["registros"]:
        est = "…" if r.get("passou") is None else ("✓" if r["passou"] else "✗")
        classe = "p" if r.get("passou") else ("f" if r.get("passou") is False else "n")
        linhas.append(f"<tr class='{classe}'><td>{est}</td><td>{_esc(r['id'])}</td><td>{_esc(r.get('causa') or '')}</td>"
                      f"<td>{_esc(', '.join(r.get('ferramentas', [])))}</td><td>{_esc('; '.join(r.get('motivos', [])))}</td>"
                      f"<td class='t'>{_esc(r.get('texto_inicio', ''))}</td></tr>")
    refresh = "<meta http-equiv='refresh' content='3'>" if em_curso else ""
    estado = (f"RODANDO — caso {len(dados['registros']) + 1} de {total}: {_esc(atual or '')}" if em_curso else "FIM da rodada")
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">{refresh}<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Autodesenvolvimento da Seth</title><style>
:root{{--bg:#fff;--fg:#1b1b1f;--mut:#5b5b66;--bd:#d8d8e0}}@media (prefers-color-scheme:dark){{:root{{--bg:#16161d;--fg:#ececf1;--mut:#a0a0ae;--bd:#34343f}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0;padding:16px;max-width:1100px;margin-inline:auto}}
h1{{font-size:20px;margin:0 0 4px}}.m{{color:var(--mut)}}.placar{{font-size:34px;font-weight:700;color:{cor}}}
.barra{{height:12px;background:var(--bd);border-radius:6px;position:relative;margin:8px 0 16px}}.barra i{{display:block;height:100%;width:{pct}%;background:{cor};border-radius:6px}}
.barra b{{position:absolute;top:-4px;left:{round(100 * meta)}%;height:20px;border-left:2px dashed var(--fg)}}
table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border-bottom:1px solid var(--bd);padding:4px 6px;text-align:left;vertical-align:top}}
tr.p td:first-child{{color:#2e7d32}}tr.f td:first-child{{color:#b3261e}}tr.f{{background:rgba(179,38,30,.08)}}.t{{max-width:360px;word-break:break-word;color:var(--mut)}}
.box{{border:1px solid var(--bd);border-radius:8px;padding:10px 12px;margin:12px 0}}code{{background:var(--bd);padding:1px 5px;border-radius:4px}}
</style></head><body>
<h1>Autodesenvolvimento da Seth — ao vivo</h1>
<div class="m">{_esc(estado)} · modelo {_esc(dados.get('modelo', ''))} · suíte {_esc(dados.get('suite', ''))} · chamadas ao gateway: {dados.get('chamadas_gateway', 0)} · {_esc(dados.get('quando', ''))}</div>
<div class="placar">{ok}/{len(rs)} · {pct}%</div><div class="barra"><i></i><b title="meta"></b></div>
<div class="m">A linha tracejada é a meta de {round(100 * meta)}%.</div>
<div class="box"><b>Você audita.</b> Esta rodada só LÊ: não altera o sistema, não escreve nada da Seth e não mexe na sua conversa. Para <b>parar agora</b>: <code>touch ~/.cache/agata/autodev/parar</code>
(vale entre um caso e outro). Qualquer mudança que a ferramenta sugerir vira proposta que só vale com a sua assinatura.</div>
<table><tr><th></th><th>caso</th><th>causa</th><th>ferramentas</th><th>motivo</th><th>resposta (início)</th></tr>{''.join(linhas)}</table>
</body></html>"""


def gravar_painel(dados, em_curso, total, atual=None):
    arq = SAIDA_DIR / "painel.html"
    arq.write_text(painel_html(dados, em_curso, total, atual), encoding="utf-8")
    os.chmod(arq, 0o600)
    return arq


# ------------------------------------------------------------------ rodada, relatório, comparação
def rodar(suite, max_casos, max_chamadas, saida, post=_post_gateway, mcp=None, ids=None, instrucao=None, abrir=False):
    casos = (casos_ouro() if suite in ("ouro", "tudo") else []) + (casos_gerados() if suite in ("gerada", "tudo") else [])
    if ids:
        casos = [c for c in casos if c["id"] in ids]
    casos = casos[:max_casos]
    SAIDA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    parar = SAIDA_DIR / "parar"
    dados_vivos = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "suite": suite, "modelo": MODELO, "chamadas_gateway": 0, "registros": []}
    painel = gravar_painel(dados_vivos, True, len(casos), casos[0]["id"] if casos else None)
    print("painel ao vivo:", f"file://{painel}", flush=True)
    if abrir:
        subprocess.Popen(["xdg-open", f"file://{painel}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    dono = mcp is None
    mcp = mcp or MCP(["node", str(MCP_SERVIDOR)])
    if dono:
        mcp.iniciar()
    registros, usadas, seguidas = [], 0, 0
    try:
        for i, c in enumerate(casos):
            if parar.exists():
                print("PARADO pelo Humano (arquivo parar)", flush=True)
                parar.unlink(missing_ok=True)
                break
            if usadas >= max_chamadas:
                registros.append({"id": c["id"], "passou": None, "motivos": ["não rodado: teto de chamadas"]})
                continue
            gravar_painel({**dados_vivos, "chamadas_gateway": usadas, "registros": registros}, True, len(casos), c["id"])
            res = rodar_caso(c["pergunta"], mcp, post, sistema=instrucao)
            usadas += res["gw"]
            ok, motivos = pontuar(c, res)
            causa = None if ok else diagnosticar(c, res, motivos)
            seguidas = seguidas + 1 if (res.get("erro") or "").startswith("gateway") else 0
            registros.append({"id": c["id"], "origem": c["origem"], "passou": ok, "motivos": motivos, "causa": causa,
                              "ferramentas": [x["nome"] for x in res["chamadas"]], "passos": res["passos"],
                              "texto_inicio": res["texto"][:120].replace("\n", " ")})
            print(("PASS  " if ok else "FALHA ") + c["id"] + ("" if ok else f"  [{causa}] {'; '.join(motivos)[:90]}"), flush=True)
            gravar_painel({**dados_vivos, "chamadas_gateway": usadas, "registros": registros}, True, len(casos), casos[i + 1]["id"] if i + 1 < len(casos) else None)
            if seguidas >= 3:
                print("ABORTADO: 3 erros seguidos de gateway")
                break
    finally:
        if dono:
            mcp.fechar()
    dados = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "suite": suite, "modelo": MODELO, "chamadas_gateway": usadas, "registros": registros}
    arq = Path(saida) if saida else SAIDA_DIR / f"run-{time.strftime('%Y%m%d-%H%M%S')}.json"
    arq.parent.mkdir(parents=True, exist_ok=True)
    gravar_painel(dados, False, len(casos))
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    os.chmod(arq, 0o600)
    _resumo(dados)
    print("relatório:", arq)
    return dados


def _resumo(d):
    rs = [r for r in d["registros"] if r.get("passou") is not None]
    ok = sum(1 for r in rs if r["passou"])
    print(f"== {ok}/{len(rs)} passaram ({round(100 * ok / max(1, len(rs)))}%) · chamadas ao gateway: {d['chamadas_gateway']}")


def relatorio_diagnostico(d):
    por = {}
    for r in d["registros"]:
        if r.get("passou") is False:
            por.setdefault(r["causa"], []).append(r["id"])
    if not por:
        print("nada a diagnosticar: nenhuma falha")
        return
    for causa, ids in sorted(por.items(), key=lambda kv: -len(kv[1])):
        print(f"- {causa} ({len(ids)}): {CAUSAS.get(causa, '?')}\n    casos: {', '.join(ids[:8])}{' …' if len(ids) > 8 else ''}")


def comparar(a, b, meta=0.9):
    ra = {r["id"]: r.get("passou") for r in a["registros"] if r.get("passou") is not None}
    rb = {r["id"]: r.get("passou") for r in b["registros"] if r.get("passou") is not None}
    comuns = sorted(set(ra) & set(rb))
    melhoraram = [i for i in comuns if not ra[i] and rb[i]]
    pioraram = [i for i in comuns if ra[i] and not rb[i]]
    pa = sum(ra[i] for i in comuns) / max(1, len(comuns))
    pb = sum(rb[i] for i in comuns) / max(1, len(comuns))
    print(f"casos comuns: {len(comuns)} | antes {round(100 * pa)}% | depois {round(100 * pb)}% | melhoraram {len(melhoraram)} | pioraram {len(pioraram)}")
    if pioraram:
        print("REGRESSÃO:", ", ".join(pioraram))
    print("meta", f"{round(100 * meta)}%:", "ATINGIDA" if pb >= meta else "NÃO atingida")
    return 0 if (not pioraram and pb >= meta) else 1


# ------------------------------------------------------------------ selftest (offline: gateway e MCP falsos)
def _selftest():
    import tempfile
    global SAIDA_DIR
    SAIDA_DIR = Path(tempfile.mkdtemp())
    res = {}
    stub = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
    stub.write('''import sys, json
for l in sys.stdin:
    try: o = json.loads(l)
    except ValueError: continue
    if "id" not in o: continue
    m = o.get("method")
    if m == "initialize": r = {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "stub"}}
    elif m == "tools/list": r = {"tools": [{"name": "query_canon", "description": "d", "inputSchema": {"type": "object"}}, {"name": "diario_anotar", "description": "ESCRITA", "inputSchema": {"type": "object"}}]}
    elif m == "tools/call": r = {"content": [{"type": "text", "text": "SAIDA " + o["params"]["name"]}]}
    else: r = {}
    print(json.dumps({"jsonrpc": "2.0", "id": o["id"], "result": r}), flush=True)
''')
    stub.close()
    mcp = MCP([sys.executable, stub.name])
    mcp.iniciar()
    nomes = [t["name"] for t in mcp.ferramentas()]
    res["MCP só expõe as ferramentas de leitura da lista fechada"] = nomes == ["query_canon"]
    res["escrita da Seth é recusada pelo cliente"] = "RECUSADA" in mcp.chamar("diario_anotar", {})
    res["leitura passa pelo servidor"] = mcp.chamar("query_canon", {"doc": "X"}) == "SAIDA query_canon"

    def gw_ok(payload):
        n_tool = sum(1 for m in payload["messages"] if m["role"] == "tool")
        if n_tool == 0:
            return {"choices": [{"message": {"content": "", "tool_calls": [{"id": "1", "function": {"name": "query_canon", "arguments": "{}"}}]}}]}
        return {"choices": [{"message": {"content": "agata-seth · m · t=1 · hora\nResposta 45"}}]}
    r = rodar_caso("pergunta", mcp, gw_ok)
    res["laço: chama a ferramenta e devolve a resposta final"] = r["texto"].endswith("Resposta 45") and len(r["chamadas"]) == 1 and r["erro"] is None
    res["laço: duas chamadas ao gateway (uma por passo)"] = r["gw"] == 2

    def gw_laco(payload):
        return {"choices": [{"message": {"content": "", "tool_calls": [{"id": "1", "function": {"name": "query_canon", "arguments": "{}"}}]}}]}
    r2 = rodar_caso("p", mcp, gw_laco, max_passos=3)
    res["laço sem fim para no teto de passos, com erro"] = r2["erro"] and "laço" in r2["erro"] and r2["passos"] == 3

    def gw_cai(payload):
        raise OSError("fora")
    res["gateway fora: erro de infraestrutura, sem levantar"] = rodar_caso("p", mcp, gw_cai)["erro"] == "gateway:OSError"
    caso_n = {"id": "n", "origem": "gerada", "tipo": "numero", "verdade": "45", "pos": 100, "pergunta": "q"}
    ok1, _ = pontuar(caso_n, {"texto": "agata-seth · m · t=1 · 16:00\n45", "chamadas": [{"nome": "query_canon", "args": {}}], "erro": None})
    ok2, m2 = pontuar(caso_n, {"texto": "agata-seth · m · t=1 · 16:00\n32", "chamadas": [{"nome": "query_canon", "args": {}}], "erro": None})
    res["pontua número certo (ignora o número do cabeçalho)"] = ok1 and not ok2
    caso_u = {"id": "u", "origem": "gerada", "tipo": "unidade", "verdade": "ativo", "pergunta": "q"}
    res["unidade ativa: 'está ativa' passa, 'não existe' falha"] = (
        pontuar(caso_u, {"texto": "x · y\nA unidade está ativa.", "chamadas": [{"nome": "query_canon", "args": {}}], "erro": None})[0]
        and not pontuar(caso_u, {"texto": "x · y\nnão existe", "chamadas": [{"nome": "query_canon", "args": {}}], "erro": None})[0])
    d_err = diagnosticar({"tipo": "unidade"}, {"chamadas": [{"nome": "maquina_verificar", "args": {"comando": "servicos", "consulta": "x"}}], "saidas": ["x não aceita o parâmetro consulta"]}, ["estado da unidade errado"])
    res["diagnóstico: comando errado de ferramenta -> descricao_ferramenta"] = d_err == "descricao_ferramenta"
    res["diagnóstico: erro lido como resposta -> erro_mal_lido"] = diagnosticar({"tipo": "numero"}, {"chamadas": [{"nome": "query_canon", "args": {}}], "saidas": ["ERRO DA FERRAMENTA: X"]}, ["número errado"]) == "erro_mal_lido"
    res["diagnóstico: entrada cortada pela rédea"] = diagnosticar({"tipo": "numero", "pos": 7000}, {"chamadas": [{"nome": "query_canon", "args": {}}], "saidas": ["ok"]}, ["número errado"]) == "entrada_cortada"
    res["diagnóstico: sem ferramenta"] = diagnosticar({"tipo": "numero"}, {"chamadas": [], "saidas": []}, ["número errado"]) == "sem_ferramenta"
    res["diagnóstico: gateway -> infra"] = diagnosticar({"tipo": "numero"}, {"erro": "gateway:OSError", "chamadas": []}, []) == "infra"
    a = {"registros": [{"id": "1", "passou": True}, {"id": "2", "passou": False}, {"id": "3", "passou": False}]}
    b = {"registros": [{"id": "1", "passou": True}, {"id": "2", "passou": True}, {"id": "3", "passou": True}]}
    c = {"registros": [{"id": "1", "passou": False}, {"id": "2", "passou": True}, {"id": "3", "passou": True}]}
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        res["comparar: melhora sem regressão e meta atingida -> 0"] = comparar(a, b) == 0
        res["comparar: regressão -> 1 mesmo com meta atingida"] = comparar(b, c, meta=0.5) == 1
        res["comparar: abaixo da meta -> 1"] = comparar(a, a) == 1
        dados = rodar("ouro", 0, 5, str(SAIDA_DIR / "r.json"), post=gw_ok, mcp=mcp)
        (SAIDA_DIR / "parar").write_text("x")
        d_par = rodar("ouro", 3, 5, str(SAIDA_DIR / "r2.json"), post=gw_ok, mcp=mcp)
        (SAIDA_DIR / "parar").unlink(missing_ok=True)
    res["Humano para a rodada com o arquivo parar: nenhum caso roda"] = len(d_par["registros"]) == 0
    res["rodada vazia grava relatório com modo 600"] = oct((SAIDA_DIR / "r.json").stat().st_mode & 0o777) == "0o600"
    # painel visual
    dv = {"quando": "agora", "suite": "s", "modelo": "m", "chamadas_gateway": 3,
          "registros": [{"id": "<script>alert(1)</script>", "passou": False, "causa": "x", "ferramentas": ["query_canon"], "motivos": ["a<b"], "texto_inicio": "<img src=x onerror=alert(1)>"},
                        {"id": "ok1", "passou": True, "ferramentas": [], "motivos": [], "texto_inicio": "bom"}]}
    h = painel_html(dv, True, 5, "proximo")
    res["painel: conteúdo da Seth é escapado (nada executável)"] = "<script>" not in h and "<img src=x" not in h and "&lt;script&gt;" in h
    res["painel: mostra o placar, a meta e o botão de parar do Humano"] = "1/2" in h and "50%" in h and "touch ~/.cache/agata/autodev/parar" in h and "Você audita" in h
    res["painel: rodando atualiza sozinho; no fim não"] = "http-equiv='refresh'" in h and "http-equiv='refresh'" not in painel_html(dv, False, 5)
    res["painel: sem script, sem recurso externo, sem rede"] = "<script" not in h and "http://" not in h.replace("http-equiv", "").replace("file://", "") and "https://" not in h
    arqp = gravar_painel(dv, False, 5)
    res["painel: arquivo modo 600"] = oct(arqp.stat().st_mode & 0o777) == "0o600"
    # parar pelo Humano, ids e instrução
    (SAIDA_DIR / "parar").write_text("x")
    cap = {}

    def gw_cap(payload):
        cap["msgs"] = payload["messages"]
        return {"choices": [{"message": {"content": "agata-seth · m · t=1 · h\n45"}}]}
    r3 = rodar_caso("q", mcp, gw_cap, sistema="ENSINAMENTO")
    res["instrução opcional entra como mensagem de sistema antes do pedido"] = cap["msgs"][0] == {"role": "system", "content": "ENSINAMENTO"} and cap["msgs"][-1]["role"] == "user"
    res["pontuação do número olha só a última linha"] = (
        pontuar(caso_n, {"texto": "agata-seth · m · t=1 · h\ncandidatos: 45, 32\n32", "chamadas": [{"nome": "query_canon", "args": {}}], "erro": None})[0] is False
        and pontuar(caso_n, {"texto": "agata-seth · m · t=1 · h\ncandidatos: 45, 32\n45", "chamadas": [{"nome": "query_canon", "args": {}}], "erro": None})[0] is True)
    (SAIDA_DIR / "parar").unlink()
    mcp.fechar()
    os.unlink(stub.name)
    for k, v in res.items():
        print(("OK    " if v else "FALHOU"), k)
    print(f"seth_autodev selftest: {sum(bool(v) for v in res.values())}/{len(res)}")
    return 0 if all(res.values()) else 1


def main(argv):
    if argv[:1] == ["--selftest"]:
        return _selftest()
    def opt(nome, padrao):
        return argv[argv.index(nome) + 1] if nome in argv else padrao
    if argv[:1] == ["--rodar"]:
        ids = set(opt("--ids", "").split(",")) if "--ids" in argv else None
        instr = Path(opt("--instrucao", "")).read_text(encoding="utf-8") if "--instrucao" in argv else None
        d = rodar(opt("--suite", "tudo"), int(opt("--max-casos", 60)), int(opt("--max-chamadas", 200)), opt("--saida", None),
                  ids=ids, instrucao=instr, abrir="--abrir" in argv)
        return 0 if all(r.get("passou") for r in d["registros"] if r.get("passou") is not None) else 1
    if argv[:1] == ["--diagnosticar"] and len(argv) >= 2:
        relatorio_diagnostico(json.loads(Path(argv[1]).read_text(encoding="utf-8")))
        return 0
    if argv[:1] == ["--comparar"] and len(argv) >= 3:
        return comparar(json.loads(Path(argv[1]).read_text(encoding="utf-8")), json.loads(Path(argv[2]).read_text(encoding="utf-8")), float(opt("--meta", 0.9)))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
