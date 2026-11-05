#!/usr/bin/env python3
"""Avaliação da nova versão (F2, lote 3): condições pareadas, métricas por dimensão, veredito.

Pergunta (protocolo §1): memória externa (Alexandria) melhora as tarefas sem aumentar erro crítico
nem custo desproporcional? O baseline é o caminho real atual: `busca_texto` (o que a Seth usa
hoje para achar texto), não um controle artificialmente pior.

Condições (uma peça muda por vez):
  sem_contexto          só o pedido
  busca_texto           baseline: trechos da busca por texto; em tarefa com documentos, o texto cru deles
  alexandria            pacote de evidência (origem, autoridade, data, estado; privado filtrado)
  alexandria_semantica  o mesmo, com a busca por sentido sempre ligada (secundária, rotulada)

Tarefas `mecanico` (reconstrução de índice, rede indisponível) não chamam modelo: verificam o
mecanismo e rodam uma vez por rodada.

Regras que o código impõe (protocolo §2 e §6):
- o reservado (`teste`) só roda com revisão do Humano no hash atual e política fixada antes;
- o executor vê só `conjunto.prompt()`; critérios e gabarito nunca;
- rota da família do autor do gabarito sai marcada `contaminado` (não conta para veredito);
- falha de infraestrutura (transporte, orçamento, privacidade…) tem etapa própria e não vira erro cognitivo;
- denominador zero dá `null`; repetições medem variação, não viram tarefas novas;
- veredito: `inconclusivo` com n < 10 pares ou intervalo cruzando a margem; falha crítica tem veto.

Uso: avaliar.py --split dev --rotas ROTA[,ROTA] [--condicoes ...] [--repeticoes 1]
Só roda quando o Humano pede (painel ou terminal): consome inferência das categorias do orçamento.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import threading
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
for _p in (AQUI, REPO / "redesign" / "nova_versao", REPO / "redesign" / "conexoes", REPO / "redesign" / "alexandria",
           REPO / "redesign" / "metacognicao", REPO / "scripts"):
    sys.path.insert(0, str(_p))
import conjunto  # noqa: E402
import eventos  # noqa: E402
import orcamento  # noqa: E402
import registro  # noqa: E402
import tarefas  # noqa: E402

CONDICOES = ("sem_contexto", "busca_texto", "alexandria", "alexandria_semantica", "alexandria_guarda",
               "alexandria_externa")
BASELINE = "busca_texto"
MIN_PARES = 10
AUTOR_PADRAO = "Claude Opus 5.5 (Claude Code)"


# --- política (§6): fixada pelo Humano antes de rodar -------------------------------------------
def _politica_path() -> Path:
    return eventos.dados() / "avaliacao" / "politica.json"


def politica() -> dict | None:
    p = _politica_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def salvar_politica(margem_minima, teto_latencia_ms, teto_reais) -> dict:
    try:
        m, lat, rs = float(margem_minima), int(teto_latencia_ms), float(teto_reais)
    except (TypeError, ValueError):
        raise ValueError("política com valor não numérico") from None
    if not (0 <= m <= 1 and 100 <= lat <= 600000 and 0 <= rs <= 10000):
        raise ValueError("política fora dos limites")
    pol = {"margem_minima": m, "teto_latencia_ms": lat, "teto_reais": rs,
           "fixada_em": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "fixada_por": "humano (painel)"}
    p = _politica_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(pol, ensure_ascii=False), encoding="utf-8")
    eventos.registrar("decision", "fixada", "avaliacao:politica", actor="humano", componente="avaliacao",
                      margem_minima=m, teto_latencia_ms=lat, teto_reais=rs)
    return pol


# --- fontes por condição ---------------------------------------------------------------------------
def _fontes_documentos(t: dict, condicao: str) -> list[dict] | None:
    docs = t.get("documentos") or []
    if condicao == "sem_contexto":
        return None
    if condicao == BASELINE:   # o que a busca por texto entrega hoje: o texto, sem metadado e sem filtro
        return [{"id": d["id"], "texto": d["texto"]} for d in docs]
    import curadoria   # Alexandria: filtra o privado, ordena por autoridade e data e anota cópia, correção e medição antiga
    return curadoria.organizar([{k: d.get(k) for k in ("id", "texto", "origem", "autoridade", "data", "estado")}
                                for d in docs if d.get("classification", "public") == "public"])


def _fontes_repo(t: dict, condicao: str, *, buscar=None, consultar=None, buscar_externa=None) -> tuple[list[dict] | None, str | None]:
    if condicao == "sem_contexto":
        return None, None
    consulta = t.get("consulta") or t["pedido"]
    if condicao == BASELINE:
        if buscar is None:
            import busca_texto
            buscar = busca_texto.buscar
        achados, _m, _ps = buscar(consulta)
        return [{"id": f"f{i}", "texto": f"{rel}:{ln} {txt}"} for i, (_n, rel, ln, txt) in enumerate(achados[:6], 1)], None
    if consultar is None:
        import acervo
        consultar = acervo.consultar
    pac = consultar(consulta, n=6, semantica="sempre" if condicao == "alexandria_semantica" else "nunca")
    fontes = []
    if condicao == "alexandria_externa":   # lote 5 (C3): evidência externa efêmera, só com busca injetada
        import externa  # noqa: E402
        ext = externa.pesquisar(consulta, buscar=buscar_externa)
        fontes += externa.para_contexto(ext)
    for i, r in enumerate(pac["resultados"][:6], 1):
        fid = str(r["entrada"]) if r.get("entrada") is not None else f"f{i}"
        fontes.append({"id": fid, "texto": r.get("trecho") or "(entrada relacionada; trecho não incluído)",
                       "origem": r["caminho"], "estado": f"{r['editorial_status']}, via {r['metodo']}",
                       "notas": [f"há correção posterior ({m}) sobre esta entrada; confira antes de usar"
                                 for m in r.get("corrigida_por") or []]})
    return fontes, pac.get("context_id")


def fontes(t: dict, condicao: str, **kw) -> tuple[list[dict] | None, str | None]:
    if t.get("documentos") and condicao != "alexandria_externa":
        return _fontes_documentos(t, condicao), None
    return _fontes_repo(t, condicao, **kw)


# --- tarefas mecânicas ------------------------------------------------------------------------------
def _mec_reconstrucao() -> dict:
    """O índice se reconstrói do snapshot com os mesmos objetos e hashes."""
    import acervo
    import sqlite3
    m = acervo.meta()
    snap = eventos.dados() / "alexandria" / "acervo" / "snapshots" / str(m.get("commit"))[:12]
    if not m.get("commit") or not snap.exists():
        return {"ok": False, "falha_etapa": "configuracao", "erro": "sem índice ou snapshot"}
    con = sqlite3.connect(acervo.indice_path())
    try:
        atual = dict(con.execute("SELECT object_id, sha256 FROM objects"))
    finally:
        con.close()
    novo = {o["object_id"]: o["sha256"] for o, _ in acervo._objetos(snap, m["commit"])}
    return {"ok": True, "passou": novo == atual, "detalhe": {"objetos": len(atual), "diferentes":
            len(set(novo.items()) ^ set(atual.items()))}}


def _mec_rede() -> dict:
    """Sem a busca por sentido, a consulta degrada para léxico, com aviso, sem erro."""
    import acervo

    def fora(*_a, **_k):
        raise ConnectionError("rede indisponível (simulada)")
    pac = acervo.consultar("busca semântica secundária", semantica="sempre", buscar_semantica=fora)
    ok = any("indisponível" in a for a in pac["avisos"]) and "semantica" not in pac["metodos"]
    return {"ok": True, "passou": ok, "detalhe": {"metodos": pac["metodos"], "avisos": pac["avisos"]}}


CONSULTAS_FIXAS = ("porta painel", "vector store memoria", "suspend travamento", "entrada diario correcao")


def _mec_restauracao() -> dict:
    """Restauração (protocolo §2): apaga o índice num cache temporário, reconstrói do snapshot e compara
    objetos, hashes e os resultados de consultas fixas. Não toca o índice vivo."""
    import acervo  # noqa: E402
    import tempfile as _tf
    m = acervo.meta()
    if not m.get("commit"):
        return {"ok": False, "falha_etapa": "configuracao", "erro": "sem índice"}
    snap = eventos.dados() / "alexandria" / "acervo" / "snapshots" / str(m["commit"])[:12]
    if not snap.exists():
        return {"ok": False, "falha_etapa": "configuracao", "erro": "sem snapshot do commit"}
    antes_objs = {o: h for o, h in acervo.objetos_indice()}
    antes_consultas = {q: [r["object_id"] for r in acervo.consultar(q, semantica="nunca")["resultados"]]
                       for q in CONSULTAS_FIXAS}
    antigo = os.environ.get("AGATA_NV_CACHE")
    with _tf.TemporaryDirectory(prefix="restaura-") as tmp:
        os.environ["AGATA_NV_CACHE"] = tmp
        try:
            acervo.indexar(snap, skills=False)
            depois_objs = {o: h for o, h in acervo.objetos_indice()}
            depois_consultas = {q: [r["object_id"] for r in acervo.consultar(q, semantica="nunca")["resultados"]]
                                for q in CONSULTAS_FIXAS}
        finally:
            if antigo is None:
                os.environ.pop("AGATA_NV_CACHE", None)
            else:
                os.environ["AGATA_NV_CACHE"] = antigo
    iguais = antes_objs == depois_objs and antes_consultas == depois_consultas
    return {"ok": True, "passou": iguais,
            "detalhe": {"objetos": len(depois_objs), "diferencas_objetos": len(set(antes_objs.items()) ^ set(depois_objs.items())),
                        "consultas_diferentes": sum(antes_consultas[q] != depois_consultas[q] for q in CONSULTAS_FIXAS)}}


MECANICOS = {"reconstrucao_indice": _mec_reconstrucao, "rede_indisponivel": _mec_rede,
             "restauracao_indice": _mec_restauracao}


# --- execução ---------------------------------------------------------------------------------------
# Família de modelo pelo nome (mapa próprio: conselho_remoto._familia não cobre Claude nem OpenAI).
FAMILIAS = {"claude": ("claude", "anthropic", "haiku", "opus", "sonnet"),
            "openai": ("gpt", "chatgpt", "openai", "codex"),
            "qwen": ("qwen",), "lfm": ("lfm", "liquid"), "lumi": ("lumi",), "gemini": ("gemini",),
            "mistral": ("mistral", "devstral", "ministral", "codestral"), "llama": ("llama",),
            "nemotron": ("nemotron",), "glm": ("glm",), "deepseek": ("deepseek",)}


def familia_de(texto: str) -> str | None:
    t = (texto or "").lower()
    return next((f for f, kws in FAMILIAS.items() if any(k in t for k in kws)), None)


def _contaminado(rota: dict, t: dict) -> bool:
    """A rota é da mesma família que escreveu as tarefas: o veredito não conta para ela (plano, pacote B1)."""
    autor = familia_de(t.get("autor") or AUTOR_PADRAO)
    if autor is None:
        return False
    rota_fam = familia_de(((rota.get("independencia") or {}).get("familia", "") + " " + (rota.get("rota") or "")))
    return rota_fam == autor


def preparar(split: str, rotas_escolhidas: list[str], condicoes=CONDICOES, repeticoes: int = 1, *, todas_rotas=None):
    ts = conjunto.carregar(split)
    if not ts:
        raise ValueError("conjunto vazio")
    if split in conjunto.RESERVADOS:
        est = conjunto.estado_reservado(split)
        if not est["revisado_por"]:
            raise PermissionError("reservado sem revisão do Humano para o hash atual")
        if not politica():
            raise PermissionError("política (margem e tetos) não fixada")
    if not set(condicoes) <= set(CONDICOES) or not condicoes:
        raise ValueError("condição fora da lista")
    if not 1 <= int(repeticoes) <= 5:
        raise ValueError("repetições entre 1 e 5")
    if todas_rotas is None:
        import testar_rotas
        todas_rotas = testar_rotas.rotas({"local", "gratuito", "assinatura", "pago"})
    por_nome = {r["rota"]: r for r in todas_rotas}
    rs = [por_nome[n] for n in rotas_escolhidas if n in por_nome]
    if not rs:
        raise ValueError("nenhuma rota escolhida está disponível no orçamento")
    return ts, rs


def rodar(split: str, rotas_escolhidas: list[str], condicoes=CONDICOES, repeticoes: int = 1, *,
          todas_rotas=None, chamar=None, fontes_kw: dict | None = None, paralelo: bool = True) -> dict:
    ts, rs = preparar(split, rotas_escolhidas, condicoes, repeticoes, todas_rotas=todas_rotas)
    o = orcamento.ler()
    pol = politica()
    run = registro.abrir("avaliar", split, registro.hash_conjunto(ts),
                         extra={"rotas": [r["rota"] for r in rs], "condicoes": list(condicoes), "repeticoes": repeticoes,
                                "politica": pol, "rubric_version": conjunto.RUBRICA})
    if chamar is None:
        import testar_rotas

        def chamar(r, p):
            return testar_rotas.chamar_rota(r, p, o["timeout_s"], max_tokens=400)
    cache_fontes: dict = {}
    gasto = {"tokens": 0}          # teto de tokens do orçamento, somado sobre todas as chamadas da rodada
    trava_gasto = threading.Lock()
    inicio = time.monotonic()
    itens = []
    for t in ts:
        if t.get("mecanico"):
            itens.append({"chave": f"{t['task_id']}|mecanico", "task": t, "mecanico": t["mecanico"]})
            continue
        for c in condicoes:
            for r in rs:
                for k in range(int(repeticoes)):
                    itens.append({"chave": f"{t['task_id']}|{c}|{r['rota']}|{k}", "task": t, "condicao": c, "rota_info": r,
                                  "seed": k, "recurso": "gpu" if r["categoria"] == "local" else None})

    def executor(item):
        t = item["task"]
        if item.get("mecanico"):
            return MECANICOS[item["mecanico"]]()
        chave_f = (t["task_id"], item["condicao"])
        if chave_f not in cache_fontes:
            cache_fontes[chave_f] = fontes(t, item["condicao"], **(fontes_kw or {}))
        fs, ctx = cache_fontes[chave_f]
        with trava_gasto:
            if gasto["tokens"] >= o["max_tokens"]:
                return {"ok": False, "falha_etapa": "orcamento", "erro": "teto de tokens do orçamento atingido"}
        res = chamar(item["rota_info"], conjunto.prompt(t, fs))
        uso = res.get("usage") or {}
        with trava_gasto:
            gasto["tokens"] += int(uso.get("input_tokens") or 0) + int(uso.get("output_tokens") or 0)
        res["context_id"] = ctx
        if item["condicao"] == "alexandria_guarda" and res.get("ok"):
            import guarda   # o depois da metacognição vê todas as fontes que o sistema tinha, inclusive as privadas
            res["texto"], g = guarda.aplicar(res.get("texto") or "", t.get("documentos") or (fs or []))
            res["guarda"] = g["estado"]
        if res.get("ok"):
            res.update(conjunto.avaliar_resposta(t, res.get("texto") or ""))
        return res

    tf = tarefas.criar("avaliacao", itens, max_chamadas=o["max_chamadas"], prazo_s=max(o["timeout_s"] * 10, 900))
    tf = tarefas.executar(tf, executor, paralelo=paralelo)
    linhas_ = []
    for item in itens:
        r = tf["resultados"].get(item["chave"]) or {"ok": False, "falha_etapa": "execucao", "erro": "não rodou (teto de chamadas)"}
        t = item["task"]
        if item.get("mecanico"):
            outcome = ("passou" if r.get("passou") else "falhou") if r.get("ok") else "nao_rodou"
            linhas_.append(registro.linha(run, task_id=t["task_id"], condition="mecanico", model_id=None, outcome=outcome,
                                          failure_stage=None if r.get("ok") else r.get("falha_etapa"), grupo=t["grupo"],
                                          caso=t.get("caso"), detalhe=r.get("detalhe"), rubric_version=conjunto.RUBRICA))
            continue
        rota = item["rota_info"]
        if not r.get("ok"):
            outcome, stage = "nao_rodou", r.get("falha_etapa") or "execucao"
        else:
            outcome = "passou" if r.get("passou") else ("absteve" if r.get("absteve") else "falhou")
            stage = None
        linhas_.append(registro.linha(
            run, task_id=t["task_id"], condition=item["condicao"], model_id=rota.get("modelo") or rota["rota"],
            outcome=outcome, failure_stage=stage, critical_failure=bool(r.get("criticos_violados")), seed=item["seed"],
            usage=r.get("usage"), latency_ms=r.get("latencia_ms"), context_id=r.get("context_id"),
            budget={"max_calls": o["max_chamadas"], "max_tokens": 400, "timeout_seconds": o["timeout_s"]},
            rubric_version=conjunto.RUBRICA, rota=rota["rota"], categoria=rota["categoria"], grupo=t["grupo"],
            caso=t.get("caso"), criterios_ok=r.get("criterios_ok"), criterios_total=r.get("criterios_total"),
            absteve=r.get("absteve"), criticos_violados=r.get("criticos_violados") or [], erro=r.get("erro"),
            deve_abster=any(c["tipo"] == "abstem" for c in t["criterios"]), guarda=r.get("guarda"),
            contaminado=_contaminado(rota, t), resposta=(r.get("texto") or "")[:4000] or None))
    resumo = metricas(linhas_, pol)
    resumo["chamadas"] = tf["chamadas"]
    resumo["paralelo"] = paralelo
    resumo["duracao_s"] = round(time.monotonic() - inicio, 2)
    resumo["tokens_usados"] = gasto["tokens"]
    resumo["obsoleto"] = tf["obsoleto"]
    return registro.fechar(run, resumo, estado="cancelada" if tf["estado"] == "cancelada" else "concluida")


# --- métricas e veredito ------------------------------------------------------------------------------
def _razao(a, b):
    return None if not b else round(a / b, 4)


def _score(ln):
    return ln["criterios_ok"] / ln["criterios_total"] if ln.get("criterios_total") else None


def metricas(linhas_: list[dict], pol: dict | None = None, *, seed: int = 7) -> dict:
    modelo = [ln for ln in linhas_ if ln["condition"] != "mecanico"]
    grupos_ = {}
    for ln in modelo:
        grupos_.setdefault((ln["condition"], ln["rota"]), []).append(ln)
    por_cond = {}
    for (c, rota), ls in sorted(grupos_.items()):
        avaliaveis = [x for x in ls if x["outcome"] in ("passou", "falhou", "absteve")]
        dims = {}
        for g in conjunto.GRUPOS:
            sc = [_score(x) for x in avaliaveis if x["grupo"] == g and _score(x) is not None]
            dims[conjunto.DIMENSAO[g]] = round(statistics.mean(sc), 4) if sc else None
        resp = [x for x in avaliaveis if not x.get("absteve")]
        devia_abster = [x for x in avaliaveis if x.get("deve_abster")]
        lat = [x["latency_ms"] for x in ls if x.get("latency_ms") is not None]
        tin = [x["usage"]["input_tokens"] for x in ls if x["usage"]["input_tokens"] is not None]
        tout = [x["usage"]["output_tokens"] for x in ls if x["usage"]["output_tokens"] is not None]
        etapas = {}
        for x in ls:
            if x["failure_stage"]:
                etapas[x["failure_stage"]] = etapas.get(x["failure_stage"], 0) + 1
        por_cond[f"{c}|{rota}"] = {
            "condicao": c, "rota": rota, "n": len(ls), "avaliaveis": len(avaliaveis), "dimensoes": dims,
            "C": {"cobertura": _razao(len(resp), len(avaliaveis)),
                  "risco": _razao(sum(x["outcome"] == "falhou" for x in resp), len(resp)),
                  "abstencao_apropriada": _razao(sum(bool(x.get("absteve")) for x in devia_abster), len(devia_abster))},
            "passaram": _razao(sum(x["outcome"] == "passou" for x in avaliaveis), len(avaliaveis)),
            "falhas_criticas": sum(x["critical_failure"] for x in ls), "falhas_infra": etapas,
            "custo": {"chamadas": len(ls) - etapas.get("cancelada", 0) - etapas.get("orcamento", 0),
                      "tokens_entrada": sum(tin) if tin else None, "tokens_saida": sum(tout) if tout else None,
                      "latencia_mediana_ms": round(statistics.median(lat)) if lat else None},
            "contaminado": any(x.get("contaminado") for x in ls)}
    mec = [ln for ln in linhas_ if ln["condition"] == "mecanico"]
    return {"por_condicao": por_cond, "comparacoes": comparar(modelo, pol, seed=seed),
            "mecanicos": {x["task_id"]: x["outcome"] for x in mec},
            "nota": "métricas por dimensão têm precedência; zero falha observada descreve a amostra, não garante risco zero"}


def comparar(linhas_: list[dict], pol: dict | None, *, seed: int = 7) -> list[dict]:
    margem = (pol or {}).get("margem_minima")
    teto_lat = (pol or {}).get("teto_latencia_ms")
    out = []
    rotas_ = sorted({x["rota"] for x in linhas_})
    for rota in rotas_:
        base = _media_por_tarefa([x for x in linhas_ if x["rota"] == rota and x["condition"] == BASELINE])
        for c in CONDICOES:
            if c == BASELINE:
                continue
            cand_l = [x for x in linhas_ if x["rota"] == rota and x["condition"] == c]
            if not cand_l:
                continue
            cand = _media_por_tarefa(cand_l)
            pares = [cand[k] - base[k] for k in sorted(set(base) & set(cand))]
            n = len(pares)
            media = round(statistics.mean(pares), 4) if pares else None
            ic = _bootstrap(pares, seed) if n >= 2 else None
            criticas = sum(x["critical_failure"] for x in cand_l)
            criticas_base = sum(x["critical_failure"] for x in linhas_ if x["rota"] == rota and x["condition"] == BASELINE)
            contaminado = any(x.get("contaminado") for x in cand_l)
            lat = [x["latency_ms"] for x in cand_l if x.get("latency_ms") is not None]
            lat_ok = None if teto_lat is None or not lat else statistics.median(lat) <= teto_lat
            if contaminado:
                v = "nao_conta (rota da família do autor do gabarito)"
            elif criticas:
                v = "vetado (falha crítica)"
            elif n < MIN_PARES or ic is None:
                v = "inconclusivo"
            elif ic[1] < 0:
                v = "piora"                      # piora não depende da margem
            elif margem is None:
                v = "inconclusivo (sem política fixada)"
            elif ic[0] > margem and lat_ok is not False:
                v = "melhora"
            else:
                v = "inconclusivo"
            out.append({"rota": rota, "baseline": BASELINE, "candidata": c, "n_pares": n, "diferenca_media": media,
                        "ic95": ic, "margem": margem, "falhas_criticas": criticas,
                        "falhas_criticas_baseline": criticas_base, "latencia_no_teto": lat_ok, "veredito": v})
    return out


def comparar_rotas(linhas_: list[dict], rota_a: str, rota_b: str, *, condicao: str = "alexandria", seed: int = 7) -> dict:
    """Troca de LLM (continuidade, protocolo §4): mesmas tarefas, mesma condição, duas rotas. Pares e IC95."""
    la = [x for x in linhas_ if x["rota"] == rota_a and x["condition"] == condicao]
    lb = [x for x in linhas_ if x["rota"] == rota_b and x["condition"] == condicao]
    ma, mb = _media_por_tarefa(la), _media_por_tarefa(lb)
    pares = [mb[k] - ma[k] for k in sorted(set(ma) & set(mb))]
    n = len(pares)
    ic = _bootstrap(pares, seed) if n >= 2 else None
    if n < MIN_PARES or ic is None:
        v = "inconclusivo"
    elif ic[0] > 0:
        v = "b_melhor"
    elif ic[1] < 0:
        v = "a_melhor"
    else:
        v = "inconclusivo"
    return {"rota_a": rota_a, "rota_b": rota_b, "condicao": condicao, "n_pares": n,
            "diferenca_media": round(statistics.mean(pares), 4) if pares else None, "ic95": ic, "veredito": v,
            "corpus_snapshot": next((x.get("corpus_snapshot") for x in la + lb if x.get("corpus_snapshot")), None)}


def _media_por_tarefa(ls: list[dict]) -> dict:
    acc: dict = {}
    for x in ls:
        s = _score(x)
        if s is not None:
            acc.setdefault(x["task_id"], []).append(s)
    return {k: statistics.mean(v) for k, v in acc.items()}


def _bootstrap(pares: list[float], seed: int, b: int = 2000) -> list[float]:
    rnd = random.Random(seed)
    n = len(pares)
    medias = sorted(statistics.mean(rnd.choice(pares) for _ in range(n)) for _ in range(b))
    return [round(medias[int(0.025 * b)], 4), round(medias[int(0.975 * b) - 1], 4)]


def estado() -> dict:
    return {"conjuntos": {s: len(conjunto.carregar(s)) for s in ("dev", "calibracao")},
            "reservado": conjunto.estado_reservado(), "politica": politica(), "condicoes": list(CONDICOES),
            "execucoes": [{k: r.get(k) for k in ("run_id", "split", "inicio", "fim", "estado", "rotas", "condicoes", "resumo")}
                          for r in registro.listar(15) if r.get("medidor") in ("avaliar", "recuperacao")][:5]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="dev", choices=conjunto.SPLITS)
    ap.add_argument("--rotas", required=False)
    ap.add_argument("--condicoes", default=",".join(CONDICOES))
    ap.add_argument("--repeticoes", type=int, default=1)
    ap.add_argument("--estado", action="store_true")
    a = ap.parse_args()
    if a.estado or not a.rotas:
        print(json.dumps(estado(), ensure_ascii=False, indent=1))
        sys.exit(0)
    r = rodar(a.split, a.rotas.split(","), a.condicoes.split(","), a.repeticoes)
    print(json.dumps({"run_id": r["run_id"], "estado": r["estado"], "comparacoes": r["resumo"]["comparacoes"]},
                     ensure_ascii=False, indent=1))
