#!/usr/bin/env python3
"""sombra_capacidade.py — roteamento por capacidade: escolha de produção (23/11/2026) e sombra (24/10/2026).

V9, seção 35; desenho em "Área de trabalho/DESENHO_roteamento_por_capacidade_rascunho.md".

Escolha de PRODUÇÃO (`escolher`, 23/11/2026; decisão do Humano, 16:40: "todos os modelos devem ser escolhidos a partir de
suas capacidades"): o gateway pede o modelo concreto que o registro recomenda para o tipo do pedido, SÓ se a nota é
>= PISO e a amostra é >= AMOSTRA_MIN. Senão, segue pelo combo de sempre. Desligável com SETH_ESCOLHA_CAPACIDADE=0
(o padrão é ligado, decisão do Humano = produção). Sem a nota, sem amostra ou sem filtro, não escolhe: a fila vale.

Sombra (`registrar`): com SETH_SOMBRA_CAPACIDADE=1, registra em `~/.cache/agata/decisor/roteador-capacidade.jsonl`, sem o
texto do pedido, a recomendação do registro, e se a escolha de produção foi aplicada (campo "aplicada").

Requisitos (passo 3, mecânico antes de modelo): o Laya é um classificador de 4 classes e não devolve requisitos sem novo
treino. Por isso os requisitos saem do próprio pedido: tokens estimados, ferramentas, código, JSON e dado pessoal.

Tipo da escolha (23/11/2026): parte da rota do Laya (codigo -> codigo). Sem ela, complementa com os requisitos:
ferramenta (há ferramentas), código, json, contexto ou conversa. A métrica lida é `qualidade_<tipo>` (contexto usa
`qualidade_contexto_longo`).

Dado pessoal (23/11/2026): a escolha manda pedido com dado pessoal SÓ a modelo local (`ollama-local/`). A régua
é o `sanitizar.varrer_pessoal` sobre TODAS as falas do pedido (conteúdo de qualquer papel, nomes e chamadas de
ferramenta). O proxy NÃO varre dado pessoal desde a decisão relaxa-pessoal (22/10): ele só bloqueia segredo. Por isso
esta regra é mais estrita que o combo. Queda: sem modelo local qualificado, vale o combo de hoje, como antes do lote.
Segredo nunca escolhe (quem chama confere com rotas_locais.tem_segredo).

Uso real (observado, 23/11/2026): fora da escolha, modelo com taxa_ok < TAXA_OK_MIN (0,8) e amostra >= UPTIME_AMOSTRA_MIN
(20) para o tipo (degradado), ou com taxa_achado >= TAXA_ACHADO_MAX (0,3) e a mesma amostra (muitos achados da verificação). Em pedido com stream, fora também o modelo cujo latencia_p95_s do tipo é >= o prazo do
primeiro conteúdo (40 s). Sem p95 conhecido, não filtra por latência; a amostra mínima vale em todo caso.

Passo 4 (escolha), com uma política PROVISÓRIA (os pisos são decisão do Humano):
- candidatos = a fila da classe, na ordem do OmniRoute (`filas` do registro);
- filtros duros: janela >= tokens estimados; se há dado pessoal, só modelo local;
- entre os que passam, sobe o de maior `qualidade_<tipo>` medida >= PISO (o tipo vem dos
  requisitos; empate = menor latência p50); sem medida acima do piso, vale a ordem da fila;
- nenhum candidato passa -> recomenda o 1º da fila, com o motivo.
- As medidas são a camada `medido` e a `observado` (uso real, incorporado pela Capivara).

Nunca derruba a resposta.
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = Path(os.environ.get("SETH_REPO", str(AQUI.parents[1])))
SCRIPTS = RAIZ / "scripts"
REGISTRO = RAIZ / "config" / "capivara" / "capacidades.json"   # queda: o registro do repositório
LOG = Path(os.path.expanduser("~/.cache/agata/decisor/roteador-capacidade.jsonl"))
PISO = 0.7                 # provisório; o piso de qualidade por tarefa é decisão do Humano
# provisório (23/11/2026, Humano pode mudar): nota com menos amostra não escolhe modelo em produção
AMOSTRA_MIN = 6
# provisórios (23/11/2026, Humano pode mudar): uso real que tira o modelo da escolha, e o prazo de stream
TAXA_OK_MIN = 0.8
TAXA_ACHADO_MAX = 0.3      # taxa de achado da verificação no uso real a partir da qual o modelo sai da escolha
UPTIME_AMOSTRA_MIN = 20
PRAZO_1O_CONTEUDO_S = 40.0   # espelha SETH_PRAZO_1O_CONTEUDO_S do gateway; o gateway passa o valor dele
TOKENS_LONGO = 30000
CHARS_POR_TOKEN = 3.5
LOCAL = "ollama-local/"
_METRICA_DO_TIPO = {"contexto": "contexto_longo"}   # tipo do gateway -> sufixo da métrica no registro
_RE_CODIGO = re.compile(r"```|\b(def|class|function|import|bash|python|script|stack ?trace|traceback|regex)\b", re.I)
_RE_JSON = re.compile(r"\bjson\b", re.I)
_TRAVA = threading.Semaphore(1)
_CACHE_REG: dict = {"caminho": None, "mtime": None, "dados": {}}


def ligado() -> bool:
    """Sombra: só com SETH_SOMBRA_CAPACIDADE=1 (desligada por padrão)."""
    return os.environ.get("SETH_SOMBRA_CAPACIDADE") == "1"


def _texto(conteudo) -> str:
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):
        return "\n".join(p.get("text", "") for p in conteudo if isinstance(p, dict) and p.get("type") == "text")
    return ""


def requisitos(payload: dict, varrer_pessoal=None) -> dict:
    msgs = payload.get("messages") or []
    total = sum(len(_texto(m.get("content"))) for m in msgs if isinstance(m, dict))
    ultima = next((_texto(m.get("content")) for m in reversed(msgs)
                   if isinstance(m, dict) and m.get("role") == "user"), "")
    if varrer_pessoal is None:
        sys.path.insert(0, str(AQUI))
        import sanitizar  # noqa: E402
        varrer_pessoal = lambda t: sanitizar.varrer_pessoal(t, sanitizar._nomes_projeto())  # noqa: E731
    r = {"tokens_est": int(total / CHARS_POR_TOKEN), "ferramentas": bool(payload.get("tools")),
         "codigo": bool(_RE_CODIGO.search(ultima)), "json": bool(_RE_JSON.search(ultima)),
         "privado": bool(varrer_pessoal(ultima))}
    r["tipo"] = ("codigo" if r["codigo"] else "json" if r["json"]
                 else "contexto_longo" if r["tokens_est"] > TOKENS_LONGO else "conversa")
    return r


def _texto_livre(valor) -> str:
    """Texto de um campo do pedido: str direto; objeto ou lista vira o JSON, para a régua ver tudo."""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, (dict, list)):
        try:
            return json.dumps(valor, ensure_ascii=False)
        except (TypeError, ValueError):
            return ""
    return ""


def textos_do_pedido(msgs: list) -> list[str]:
    """Tudo o que o pedido leva nas falas, de qualquer papel (usuário, assistente, ferramenta): conteúdo, nome, e as
    chamadas de ferramenta (nome e argumentos, em tool_calls e em function_call). Não é a injeção da Máquina."""
    out: list[str] = []
    for m in msgs:
        if not isinstance(m, dict):
            continue
        conteudo = m.get("content")
        out.append(_texto(conteudo) if isinstance(conteudo, (str, list)) else _texto_livre(conteudo))
        if isinstance(m.get("name"), str):
            out.append(m["name"])
        for tc in m.get("tool_calls") or []:
            fn = tc.get("function") if isinstance(tc, dict) and isinstance(tc.get("function"), dict) else None
            if fn is None:
                out.append(_texto_livre(tc))
                continue
            out.append(_texto_livre(fn.get("name")))
            out.append(_texto_livre(fn.get("arguments")))
        fc = m.get("function_call")
        if isinstance(fc, dict):
            out.append(_texto_livre(fc.get("name")))
            out.append(_texto_livre(fc.get("arguments")))
    return out


def privado_no_historico(msgs: list, varrer_pessoal=None) -> bool:
    """Dado pessoal em qualquer parte do pedido (ver textos_do_pedido), pela régua do sanitizar. Devolve só sim/não,
    nunca o texto. Régua indisponível = sim (falha fechada: o pedido fica só com modelo local)."""
    texto = "\n".join(textos_do_pedido(msgs))
    try:
        if varrer_pessoal is None:
            if str(AQUI) not in sys.path:
                sys.path.insert(0, str(AQUI))
            import sanitizar  # noqa: E402
            varrer_pessoal = lambda t: sanitizar.varrer_pessoal(t, sanitizar._nomes_projeto())  # noqa: E731
        return bool(varrer_pessoal(texto))
    except Exception:  # noqa: BLE001 -- falha fechada
        return True


def _metrica(tipo: str) -> str:
    return f"qualidade_{_METRICA_DO_TIPO.get(tipo, tipo)}"


def _medidas(info: dict) -> list:
    """Medidas do modelo: a camada `medido` (benchmark) e a `observado` (uso real). A observada vem depois."""
    med = info.get("medido")
    obs = info.get("observado")
    return (med if isinstance(med, list) else []) + (obs if isinstance(obs, list) else [])


def _ultimo(medidas, metrica: str) -> dict | None:
    vals = [x for x in medidas or [] if isinstance(x, dict) and x.get("metrica") == metrica]
    return vals[-1] if vals else None


def _ultima(medidas, metrica: str):
    r = _ultimo(medidas, metrica)
    return r.get("valor") if r else None


def _amostra(rec: dict | None) -> int:
    n = (rec or {}).get("amostra")
    return n if isinstance(n, int) and not isinstance(n, bool) else 0


def _escalar(x) -> int | None:
    """Janela em tokens como escalar (número). Qualquer outra coisa não conta."""
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0 else None


def _janela(info: dict, perfil_janela) -> int | None:
    cat = info.get("catalogo") if isinstance(info.get("catalogo"), dict) else {}
    decl = info.get("declarado") if isinstance(info.get("declarado"), dict) else {}
    # declarado.janela é escalar (23/11/2026: o formato novo do registro mantém o campo)
    return _escalar(cat.get("janela")) or _escalar(decl.get("janela")) or _escalar(perfil_janela)


def recomendar(req: dict, rota: str, registro: dict, janelas: dict | None = None) -> dict:
    base = rota.removesuffix("-longo")
    fila = (registro.get("filas") or {}).get(base) or []
    modelos = registro.get("modelos") or {}
    janelas = janelas or {}
    if not fila:
        return {"recomendado": None, "motivo": f"fila {base} fora do registro"}
    passa, motivos = [], []
    for m in fila:
        info = modelos.get(m) or {}
        j = _janela(info, janelas.get(m))
        if j is not None and j < req["tokens_est"]:
            motivos.append(f"{m}: janela {j} < {req['tokens_est']}")
            continue
        if req["privado"] and not m.startswith(LOCAL):
            motivos.append(f"{m}: dado pessoal, só local")
            continue
        passa.append(m)
    if not passa:
        return {"recomendado": fila[0], "motivo": "nenhum candidato passa nos filtros; fica o 1º da fila",
                "descartes": motivos, "passa": False}
    metrica = _metrica(req["tipo"])

    def chave(m):
        med = _medidas(modelos.get(m) or {})
        q = _ultima(med, metrica)
        lat = _ultima(med, "latencia_p50_s")
        if q is not None and q >= PISO:          # medido acima do piso: o melhor sobe
            return (0, -q, lat if lat is not None else 1e9, fila.index(m))
        return (1, fila.index(m))                # sem medida ou abaixo do piso: vale a ordem da fila
    melhor = sorted(passa, key=chave)[0]
    q = _ultima(_medidas(modelos.get(melhor) or {}), metrica)
    return {"recomendado": melhor, "motivo": f"{metrica}={q}" if q is not None
            else "sem medida de qualidade; ordem da fila", "descartes": motivos, "passa": True}


def _sem_amostra_pequena(registro: dict, metrica: str) -> dict:
    """Cópia do registro sem as medidas da métrica com amostra < AMOSTRA_MIN. Sem amostra suficiente, o modelo fica
    sem nota para a escolha de produção (ele só sai se a fila não tiver outro com nota e amostra)."""
    def _filtra(lista):
        if not isinstance(lista, list):
            return lista
        return [x for x in lista if not (isinstance(x, dict) and x.get("metrica") == metrica
                                         and _amostra(x) < AMOSTRA_MIN)]
    modelos = {m: dict(info, medido=_filtra(info.get("medido")), observado=_filtra(info.get("observado")))
               for m, info in (registro.get("modelos") or {}).items() if isinstance(info, dict)}
    return dict(registro, modelos=modelos)


def tipo_da_escolha(rota_laya: str | None, req: dict) -> str:
    """Tipo do pedido para a escolha por capacidade (23/11/2026). Parte da rota do Laya (codigo -> codigo). Sem ela, ou
    se o Laya não pediu código, complementa com os requisitos: ferramenta, código, json, contexto ou conversa."""
    if rota_laya == "codigo":
        return "codigo"
    if req.get("ferramentas"):
        return "ferramenta"
    if req.get("codigo"):
        return "codigo"
    if req.get("json"):
        return "json"
    if int(req.get("tokens_est") or 0) > TOKENS_LONGO:
        return "contexto"
    return "conversa"


def _ultimo_por_tipo(medidas, metrica: str, tipo: str) -> dict | None:
    """Último registro da métrica para o tipo (registro com "tipo" igual vale mais). Sem registro do tipo, vale o que não
    traz tipo (medida geral do modelo)."""
    recs = [x for x in medidas or [] if isinstance(x, dict) and x.get("metrica") == metrica]
    exato = [x for x in recs if x.get("tipo") == tipo]
    if exato:
        return exato[-1]
    geral = [x for x in recs if "tipo" not in x]
    return geral[-1] if geral else None


def _numero(x) -> float | None:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _fora_da_escolha(info: dict, req: dict, prazo_stream_s: float | None) -> bool:
    """Modelo que não entra na escolha agora: uso real degradado (taxa_ok < TAXA_OK_MIN com amostra >= UPTIME_AMOSTRA_MIN,
    para o tipo) ou, em pedido com stream, latencia_p95_s do tipo >= o prazo do primeiro conteúdo."""
    med = _medidas(info)
    tipo = req["tipo"]
    taxa = _ultimo_por_tipo(med, "taxa_ok", tipo)
    valor_taxa = _numero(taxa.get("valor")) if taxa else None
    if valor_taxa is not None and valor_taxa < TAXA_OK_MIN and _amostra(taxa) >= UPTIME_AMOSTRA_MIN:
        return True
    achado = _ultimo_por_tipo(med, "taxa_achado", tipo)
    valor_achado = _numero(achado.get("valor")) if achado else None
    if valor_achado is not None and valor_achado >= TAXA_ACHADO_MAX and _amostra(achado) >= UPTIME_AMOSTRA_MIN:
        return True
    if req.get("stream") and prazo_stream_s is not None:
        p95 = _numero((_ultimo_por_tipo(med, "latencia_p95_s", tipo) or {}).get("valor"))
        if p95 is not None and p95 >= prazo_stream_s:
            return True
    return False


def _sem_os_que_nao_servem(registro: dict, req: dict, prazo_stream_s: float | None) -> dict:
    """Cópia do registro em que os modelos fora da escolha não têm medida: não ganham nota, então não são escolhidos."""
    modelos = {}
    for m, info in (registro.get("modelos") or {}).items():
        if isinstance(info, dict):
            modelos[m] = {} if _fora_da_escolha(info, req, prazo_stream_s) else info
    return dict(registro, modelos=modelos)


def escolher(req: dict, rota: str, registro: dict, janelas: dict | None = None,
             prazo_stream_s: float | None = None) -> dict | None:
    """Escolha de PRODUÇÃO (23/11/2026). Devolve {modelo, tipo, nota, n, motivo} só quando o recomendar, sobre o registro
    sem os modelos fora da escolha (uso degradado; em stream, p95 >= prazo_stream_s) e sem as medidas de amostra pequena,
    aponta um modelo com nota >= PISO e amostra >= AMOSTRA_MIN para o tipo. None = o gateway segue pelo combo de sempre
    (queda segura). Quem chama trata exceção como None."""
    metrica = _metrica(req["tipo"])
    reg = _sem_amostra_pequena(_sem_os_que_nao_servem(registro or {}, req, prazo_stream_s), metrica)
    rec = recomendar(req, rota, reg, janelas)
    m = rec.get("recomendado")
    if not m or not rec.get("passa"):  # (23/11) nenhum candidato passou nos filtros: vale o combo
        return None
    if req.get("privado") and not m.startswith(LOCAL):  # (23/11) pessoal só a modelo local, também na escolha
        return None
    janela = _janela(reg.get("modelos", {}).get(m) or {}, (janelas or {}).get(m))
    if janela is None or janela < req["tokens_est"]:  # (23/11) sem janela conhecida e suficiente, não se prova que cabe
        return None
    r = _ultimo(_medidas((reg.get("modelos") or {}).get(m) or {}), metrica)
    nota = r.get("valor") if r else None
    n = _amostra(r)
    if not isinstance(nota, (int, float)) or isinstance(nota, bool) or nota < PISO or n < AMOSTRA_MIN:
        return None
    return {"modelo": m, "tipo": req["tipo"], "nota": nota, "n": n, "motivo": f"{metrica}={nota} n={n}"}


_CAMINHO_VALIDADE_S = 5.0
_CACHE_CAMINHO: dict = {"quando": 0.0, "valor": None}


def _caminho_registro() -> Path:
    """Caminho do registro, lembrado por 5 s: a função da Capivara confere o estado a cada chamada."""
    agora = time.monotonic()
    if _CACHE_CAMINHO["valor"] is not None and agora - _CACHE_CAMINHO["quando"] < _CAMINHO_VALIDADE_S:
        return _CACHE_CAMINHO["valor"]
    valor = _resolver_caminho_registro()
    _CACHE_CAMINHO.update(quando=agora, valor=valor)
    return valor


def _resolver_caminho_registro() -> Path:
    """Onde está o registro de capacidades (23/11/2026, coordenação): o estado que a Capivara mantém, pela função
    capivara_capacidades.caminho_registro() (~/.local/share/agata/capivara/capacidades.json se válido), e, sem ela, ou se
    ela falhar, o registro do repositório (REGISTRO). Importado de scripts/, como o gateway já faz com capivara_perfis."""
    try:
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        import capivara_capacidades  # noqa: E402  (scripts/: só leitura, sem efeito ao importar)
        fn = getattr(capivara_capacidades, "caminho_registro", None)
        if callable(fn):
            return Path(fn())
    except Exception:  # noqa: BLE001 -- queda: o registro do repositório
        pass
    return REGISTRO


def carregar_registro() -> dict:
    """Registro de capacidades (ver _caminho_registro), lembrado por mtime. Ausente ou ilegível = {}, que faz a escolha
    cair no combo."""
    caminho = _caminho_registro()
    try:
        mt = caminho.stat().st_mtime
    except OSError:
        return {}
    if _CACHE_REG["caminho"] == str(caminho) and _CACHE_REG["mtime"] == mt:
        return _CACHE_REG["dados"]
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(dados, dict):
        return {}
    _CACHE_REG.update(caminho=str(caminho), mtime=mt, dados=dados)
    return dados


def linha_sombra(req: dict, rota: str, registro: dict, janelas: dict | None, escolhida: str | None) -> dict:
    """Linha da sombra (pura). `aplicada` = a escolha de produção pediu um modelo concreto neste pedido."""
    rec = recomendar(req, rota, registro, janelas)
    fila = (registro.get("filas") or {}).get(rota.removesuffix("-longo")) or []
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rota": rota, "primeiro_da_fila": fila[0] if fila else None,
            "recomendado": rec.get("recomendado"), "difere": bool(fila) and rec.get("recomendado") != fila[0],
            "motivo": rec.get("motivo"), "requisitos": req,
            "aplicada": escolhida is not None, "escolhida": escolhida}


def registrar(payload: dict, rota: str, janelas: dict | None = None, req: dict | None = None,
              escolhida: str | None = None) -> None:
    """Dispara a sombra sem esperar; uma por vez. Nunca levanta. `req` é o perfil de produção, se houver."""
    if not ligado() or not _TRAVA.acquire(blocking=False):
        return

    def _rodar():
        try:
            r = req if req is not None else requisitos(payload)
            linha = linha_sombra(r, rota, carregar_registro(), janelas, escolhida)
            LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(linha, ensure_ascii=False) + "\n")
        except Exception as e:  # noqa: BLE001
            print(f"sombra_capacidade: não registrou ({e.__class__.__name__})", file=sys.stderr, flush=True)
        finally:
            _TRAVA.release()
    threading.Thread(target=_rodar, daemon=True).start()


def _selftest() -> int:
    nada = lambda t: []  # noqa: E731
    pessoal = lambda t: [1] if "@" in t else []  # noqa: E731
    reg = {"filas": {"seth-livre": ["r/a", "r/b", LOCAL + "m"]},
           "modelos": {"r/a": {"catalogo": {"janela": 128000}, "medido": [
                           {"metrica": "qualidade_codigo", "valor": 0.6}, {"metrica": "latencia_p50_s", "valor": 2}]},
                       "r/b": {"catalogo": {"janela": 256000}, "medido": [
                           {"metrica": "qualidade_codigo", "valor": 0.9}, {"metrica": "latencia_p50_s", "valor": 5},
                           {"metrica": "qualidade_conversa", "valor": 0.8}]},
                       LOCAL + "m": {"catalogo": None, "medido": [{"metrica": "qualidade_codigo", "valor": 0.75}]}}}
    p = lambda txt, tools=True: {"messages": [{"role": "user", "content": txt}], "tools": [1] if tools else []}  # noqa: E731
    rq = requisitos(p("escreva um script python"), nada)
    rp = requisitos(p("meu email é a@b.c, resuma"), pessoal)
    grande = requisitos({"messages": [{"role": "user", "content": "x" * 600000}]}, nada)
    casos = [
        ("requisito: código detectado", rq["codigo"] and rq["tipo"] == "codigo" and rq["ferramentas"]),
        ("requisito: JSON detectado", requisitos(p("devolva só json"), nada)["tipo"] == "json"),
        ("requisito: dado pessoal marca privado", rp["privado"]),
        ("requisito: tokens estimados", grande["tokens_est"] == int(600000 / CHARS_POR_TOKEN)),
        ("escolhe a maior qualidade do tipo acima do piso", recomendar(rq, "seth-livre", reg)["recomendado"] == "r/b"),
        ("privado: só local", recomendar(rp, "seth-livre", reg, {LOCAL + "m": 65536})["recomendado"] == LOCAL + "m"),
        ("janela pequena descarta", recomendar(grande, "seth-livre", reg, {LOCAL + "m": 65536})["recomendado"] == "r/b"),
        ("ninguém passa -> 1º da fila, com motivo",
         recomendar(dict(grande, privado=True), "seth-livre", reg, {LOCAL + "m": 65536})["recomendado"] == "r/a"),
        ("abaixo do piso não passa na frente de quem vem antes na fila",
         recomendar(requisitos(p("oi"), nada), "seth-livre", {"filas": reg["filas"], "modelos": {
             "r/a": {"medido": [{"metrica": "qualidade_conversa", "valor": 0.5}]}, "r/b": {}}})["recomendado"] == "r/a"),
        ("fila -longo usa a fila base", recomendar(rq, "seth-livre-longo", reg)["recomendado"] == "r/b"),
        ("fila fora do registro -> sem recomendação", recomendar(rq, "seth-x", reg)["recomendado"] is None),
        ("desligado por padrão", os.environ.get("SETH_SOMBRA_CAPACIDADE") == "1" or not ligado()),
        ("observado conta como medida", recomendar(rq, "seth-livre", {"filas": reg["filas"], "modelos": {
            "r/a": {"observado": [{"metrica": "qualidade_codigo", "valor": 0.95, "amostra": 9}]},
            "r/b": {"medido": [{"metrica": "qualidade_codigo", "valor": 0.8}]}}})["recomendado"] == "r/a"),
        ("tipo da escolha: a rota do Laya codigo vale", tipo_da_escolha("codigo", rq) == "codigo"),
        ("tipo da escolha: ferramenta vem antes de conversa",
         tipo_da_escolha("livre", {"ferramentas": True, "codigo": False, "json": False, "tokens_est": 10}) == "ferramenta"),
        ("tipo da escolha: contexto grande", tipo_da_escolha(None, {"ferramentas": False, "codigo": False,
                                                                    "json": False, "tokens_est": 40000}) == "contexto"),
        ("escolha: amostra 6 com nota 0,9 escolhe", (escolher(dict(rq, tipo="codigo"), "seth-livre", {
            "filas": reg["filas"], "modelos": {"r/a": {"catalogo": {"janela": 128000}, "medido": [
                {"metrica": "qualidade_codigo", "valor": 0.9, "amostra": 6}]}}}) or {}).get("modelo") == "r/a"),
        ("escolha: fila só nuvem com dado pessoal -> None", escolher(dict(rq, tipo="codigo", privado=True),
            "seth-livre", {"filas": {"seth-livre": ["r/a"]}, "modelos": {"r/a": {"catalogo": {"janela": 128000},
            "medido": [{"metrica": "qualidade_codigo", "valor": 0.9, "amostra": 6}]}}}) is None),
        ("escolha: nuvem com janela e local sem janela (o melhor) -> None", escolher(dict(rq, tipo="codigo"),
            "seth-livre", {"filas": {"seth-livre": ["r/a", LOCAL + "m"]}, "modelos": {
            "r/a": {"catalogo": {"janela": 128000}, "medido": [{"metrica": "qualidade_codigo", "valor": 0.8,
                                                              "amostra": 6}]},
            LOCAL + "m": {"medido": [{"metrica": "qualidade_codigo", "valor": 0.95, "amostra": 6}]}}}) is None),
        ("escolha: nenhum candidato passa na janela -> None", escolher(dict(rq, tipo="codigo", tokens_est=500000),
            "seth-livre", {"filas": {"seth-livre": ["r/a"]}, "modelos": {"r/a": {"catalogo": {"janela": 1000},
            "medido": [{"metrica": "qualidade_codigo", "valor": 0.9, "amostra": 6}]}}}) is None),
        ("escolha: amostra 5 não escolhe", escolher(dict(rq, tipo="codigo"), "seth-livre", {
            "filas": reg["filas"], "modelos": {"r/a": {"medido": [{"metrica": "qualidade_codigo", "valor": 0.9,
                                                                  "amostra": 5}]}}}) is None),
        ("escolha: nota 0,6 com amostra boa não escolhe", escolher(dict(rq, tipo="codigo"), "seth-livre", {
            "filas": reg["filas"], "modelos": {"r/a": {"medido": [{"metrica": "qualidade_codigo", "valor": 0.6,
                                                                  "amostra": 20}]}}}) is None),
        ("linha da sombra: aplicada true só com escolha", linha_sombra(rq, "seth-livre", reg, None, "r/b")["aplicada"]
         and not linha_sombra(rq, "seth-livre", reg, None, None)["aplicada"]),
    ]
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(_selftest())
    print(__doc__)
    sys.exit(2)
