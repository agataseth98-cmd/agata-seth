#!/usr/bin/env python3
"""Rotina de pesquisa/saúde do pool de modelos gratuitos (MEMÓRIAS (377)).

Roda semanal (agata-pesquisa-modelos.timer). NÃO implementa nada: só lê e,
se algo mudou, escreve UMA proposta em propostas/ pro Humano decidir (P-8).
Mesma disciplina do flow de consolidação depois de (371).

Dois modos, nunca misturados (roteamento por capacidade, passo 2; V9, seção 35):

DESCOBERTA (padrão; o timer roda este) -- nenhuma chamada a modelo, nenhuma
escrita no OmniRoute, zero cota:
  1. lê os modelos que o OmniRoute conhece (GET /api/models) em provedores
     CONECTADOS que não estão no pool nem no ROSTER;
  2. lê os últimos resultados do Discovery (GET /api/discovery/results), sem
     disparar varredura nova;
  3. (18/11/2026) catálogo VIVO: para provedores com lista pública sem chave
     (NVIDIA, OpenRouter), lê a lista do próprio provedor (GET de metadado, sem
     o token interno) e compara com o que o OmniRoute expõe: no OmniRoute e fora
     da lista viva = provável APOSENTADO; na lista viva e fora do OmniRoute = NOVO;
  4. compara com a última descoberta. Mudou -> propostas/modelos-gratuitos-<data>.md
     com a lista de candidatos ("disponível no catálogo", nunca "funciona").

ENSAIO (`--ensaio`, só à mão, com autorização: gasta cota grátis) -- teste de vida:
  1. re-testa cada modelo do pool confirmado (config/modelos-gratuitos.md) e do
     ROSTER de scripts/conselho_remoto.py -- 1 chamada mínima via :20127;
  2. testa até 12 candidatos fora do pool;
  3. com `--scan`, dispara antes o Discovery do OmniRoute (POST /api/discovery/scan);
  4. compara com o último ensaio e, se mudou, escreve a proposta com o rascunho de
     ROSTER. Um `pong` prova conectividade numa amostra, não qualidade (desenho do
     roteamento, seção 8). Benchmark de qualidade é outra peça, com corpus próprio.

Uso: pesquisar_modelos_gratuitos.py [--repo DIR] [--ensaio [--scan]] | --selftest
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(os.environ.get("AGATA_REPO", os.path.expanduser("~/agata")))
PROXY = os.environ.get("AGATA_PROXY", "http://127.0.0.1:20127")
OMNIROUTE = os.environ.get("AGATA_OMNIROUTE", "http://127.0.0.1:20128")
ESTADO_DIR = Path(os.path.expanduser("~/.cache/agata/pesquisa-modelos"))
ULTIMO = ESTADO_DIR / "ultimo.json"                     # último ENSAIO
ULTIMA_DESCOBERTA = ESTADO_DIR / "ultima-descoberta.json"
LOG = ESTADO_DIR / "runs.log"
POOL_MD = REPO / "config" / "modelos-gratuitos.md"
CONSELHO = REPO / "scripts" / "conselho_remoto.py"
CAPACIDADES = REPO / "config" / "capivara" / "capacidades.json"

# Reaproveita os MESMOS parâmetros da chamada real (achado 22/09/2026: com
# max_tokens fixo baixo, a sonda reportava Gemini como VAZIO -- na verdade só
# precisa de max_tokens alto pra não queimar tudo em reasoning, confirmado
# testando direto com os parâmetros de baixo. Sem isto, todo modelo que
# precisa de max_tokens>padrão (hoje: gemini/, llama-cpp/nemotron-3.5-lightning)
# aparece falso-VAZIO aqui mesmo funcionando limpo em produção).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import conselho_remoto as _cr  # noqa: E402

# famílias que precisam de chave do Humano -- a rotina só as LEMBRA, nunca as
# adiciona (isso é integração, decisão do Humano + .env + proposta assinada).
CANDIDATOS_COM_CHAVE = ["Mistral AI", "GitHub Models", "HuggingFace Inference",
                        "Cloudflare Workers AI", "NVIDIA NIM"]


# Provedores com lista pública de modelos, sem chave (catálogo vivo, 18/11/2026).
# prefixo no OmniRoute -> (URL da lista, filtro opcional dos "novos").
LISTAS_VIVAS = {
    "nvidia": ("https://integrate.api.nvidia.com/v1/models", None),
    "openrouter": ("https://openrouter.ai/api/v1/models", lambda i: i.endswith(":free")),
}
# ids do OmniRoute que não são modelo do provedor (roteadores/combos virtuais).
VIRTUAIS = {"openrouter": {"auto", "free"}}
TETO_LISTA = 60  # itens por seção na proposta; o total vai na contagem


def _token_interno():
    """Token interno (X-Agata-Token), de `scripts/token_interno.py` -- arquivo
    próprio, nunca o .env (MEMÓRIAS (629)-(631)). Nunca loga o valor. Sem ele,
    o proxy sanitizador (:20127) recusa a chamada com 403 (MEMÓRIAS (437)).
    Enviado também nas chamadas diretas ao OmniRoute (:20128) por
    simplicidade -- ele não conhece o header e o ignora."""
    _scripts = str(Path(__file__).resolve().parents[1] / "scripts")
    if _scripts not in sys.path:
        sys.path.insert(0, _scripts)
    import token_interno  # noqa: E402  (scripts/token_interno.py)
    return token_interno.ler()


HOSTS_LOCAIS = {"127.0.0.1", "localhost", "::1"}


class _SemRedirect(urllib.request.HTTPRedirectHandler):
    """3xx vira erro: o token interno nunca segue redirecionamento para outro host."""
    def redirect_request(self, *a, **k):
        return None


_OPENER = urllib.request.build_opener(_SemRedirect)


def _abrir(req, timeout):
    return _OPENER.open(req, timeout=timeout)


def _http(url, metodo="GET", body=None, timeout=45, classification=None):
    host = urllib.parse.urlparse(url).hostname
    if host not in HOSTS_LOCAIS:  # antes de ler o token: ele nunca sai da Máquina
        raise ValueError(f"host não local recusado: {host!r} (AGATA_OMNIROUTE/AGATA_PROXY)")
    data = json.dumps(body).encode() if body is not None else None
    headers = {"content-type": "application/json", "X-Agata-Token": _token_interno()}
    if classification is not None:
        headers["X-Agata-Data-Classification"] = classification
    req = urllib.request.Request(url, data=data, method=metodo,
                                 headers=headers)
    with _abrir(req, timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _http_publico(url, timeout=30):
    """GET de metadado em lista pública de terceiro. NUNCA envia o token interno."""
    req = urllib.request.Request(url, headers={"accept": "application/json",
                                               "user-agent": "agata-catalogo/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


# Só modelo de chat/texto entra na comparação (18/11/2026): as listas públicas
# não cobrem embedding, rerank, áudio nem imagem, e isso virava falso "aposentado".
_NAO_CHAT = re.compile(
    r"(?<![a-z0-9])(tts|stt|asr)(?![a-z0-9])|embed|rerank|flux|whisper|tacotron|fastpitch|"
    r"parakeet|transcribe|chirp|nova-3|voxtral|lyria|image|video|detector|bge-m3|diffusion|"
    r"audio|vision|guard|safeguard|cosmos|ocr|speech|moderation|retriev|safety|translate")
QUEDA_SUSPEITA = 0.30   # total_vivo cair mais que isso vs a execução anterior = suspeito


def _e_chat(i):
    return not _NAO_CHAT.search(i.lower())


def _ids_vivos(url):
    d = _http_publico(url)
    if not isinstance(d, dict) or not isinstance(d.get("data"), list):
        raise ValueError("forma inesperada: esperava objeto com lista em 'data'")
    return {m["id"] for m in d["data"] if isinstance(m, dict) and isinstance(m.get("id"), str) and m["id"]}


def _modelos_omni_api():
    """Lista de /api/models do OmniRoute (UMA chamada por rodada) ou None se falhar."""
    try:
        d = _http(f"{OMNIROUTE}/api/models")
        ms = d.get("models") if isinstance(d, dict) else None
        return ms if isinstance(ms, list) else None
    except Exception:  # noqa: BLE001
        return None


def _ids_omniroute_por_provedor(provedores, models):
    """{prefixo: {id sem prefixo}} de /api/models (já lido, `models`) e /v1/models."""
    out = {p: set() for p in provedores}
    for m in models or []:
        full = m.get("fullModel") if isinstance(m, dict) else None
        if not isinstance(full, str):
            continue
        for p in provedores:
            if full.startswith(p + "/"):
                out[p].add(full[len(p) + 1:])
    try:
        d = _http(f"{OMNIROUTE}/v1/models")
        for m in (d.get("data") or []) if isinstance(d, dict) else []:
            full = m.get("id") if isinstance(m, dict) else None
            if not isinstance(full, str):
                continue
            for p in provedores:
                if full.startswith(p + "/"):
                    out[p].add(full[len(p) + 1:])
    except Exception:  # noqa: BLE001
        pass
    return out


def comparar_catalogo_vivo(anterior=None, models=None):
    """Por provedor: {aposentados, novos, total_vivo, total_omniroute, suspeito} ou {erro}.
    Só GET; nenhuma chamada a modelo. `anterior` = catalogo_vivo da execução anterior."""
    omni = _ids_omniroute_por_provedor(LISTAS_VIVAS, models)
    anterior = anterior if isinstance(anterior, dict) else {}
    res = {}
    for prov, (url, filtro) in LISTAS_VIVAS.items():
        meus = {i for i in omni.get(prov, set()) - VIRTUAIS.get(prov, set()) if _e_chat(i)}
        if not meus:
            res[prov] = {"erro": "OmniRoute não devolveu ids de chat deste provedor (não comparo)"}
            continue
        try:
            vivos = {i for i in _ids_vivos(url) if _e_chat(i)}
        except Exception as e:  # noqa: BLE001
            res[prov] = {"erro": f"{type(e).__name__}: {e}"}
            continue
        if not vivos:
            res[prov] = {"erro": "lista viva vazia (não comparo)"}
            continue
        novos = vivos - meus
        if filtro:
            novos = {i for i in novos if filtro(i)}
        apos = sorted(meus - vivos)
        motivos = []
        if len(apos) * 2 > len(meus):
            motivos.append("mais da metade dos ids do OmniRoute sumiu da lista viva")
        ant = (anterior.get(prov) or {}).get("total_vivo")
        if isinstance(ant, int) and ant > 0 and len(vivos) < ant * (1 - QUEDA_SUSPEITA):
            motivos.append(f"a lista viva caiu de {ant} para {len(vivos)} ids desde a execução anterior")
        res[prov] = {"aposentados": apos, "novos": sorted(novos),
                     "total_vivo": len(vivos), "total_omniroute": len(meus),
                     "suspeito": bool(motivos), "motivo_suspeito": "; ".join(motivos)}
    return res


def _chave_mudanca(cv):
    """O que decide 'mudou': só as listas de aposentados e novos (não os totais)."""
    return {p: ({"erro": True} if "erro" in r else {"aposentados": r["aposentados"], "novos": r["novos"],
                                                    "suspeito": bool(r.get("suspeito"))})
            for p, r in (cv or {}).items()}


def _sondar(modelo):
    """1 chamada mínima, com os mesmos max_tokens/thinking da chamada real de
    conselho_remoto.py (MAX_TOKENS_POR_MODELO / THINKING_DISABLED_PREFIXOS) --
    não um teto fixo curto. Devolve (estado, detalhe)."""
    payload = {
        "model": modelo,
        "messages": [{"role": "user", "content": "Responda apenas: pong"}],
        "max_tokens": _cr.MAX_TOKENS_POR_MODELO.get(modelo, _cr.TETO_TOKENS_SAIDA),
    }
    if _cr.DESABILITAR_THINKING and modelo.startswith(_cr.THINKING_DISABLED_PREFIXOS):
        payload["thinking"] = {"type": "disabled"}
    try:
        d = _http(f"{PROXY}/v1/chat/completions", "POST", payload,
                  classification="public")
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", errors="replace")[:200]
        if e.code in (402,) or "payment" in corpo.lower() or "billing" in corpo.lower():
            return "PAGO", f"HTTP {e.code}: {corpo}"
        return "ERRO", f"HTTP {e.code}: {corpo}"
    except Exception as e:  # noqa: BLE001
        return "ERRO", f"{type(e).__name__}: {e}"
    ch = (d.get("choices") or [{}])[0]
    txt = (ch.get("message", {}).get("content") or "").strip()
    uso = d.get("usage") or {}
    rt = int((uso.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) or 0)
    ts = int(uso.get("completion_tokens", 0) or 0)
    if not txt:
        return "VAZIO", f"finish={ch.get('finish_reason')}, reasoning={rt}/{ts}"
    if ch.get("finish_reason") == "length" and rt and rt >= ts * 0.9:
        return "REASONING_BURN", f"{rt}/{ts} tokens em reasoning"
    return "OK", f"{txt[:40]!r} ({ts} tok)"


def _pool_confirmado():
    """ids na tabela 'Confirmado funcionando' do config/modelos-gratuitos.md."""
    if not POOL_MD.is_file():
        return []
    txt = POOL_MD.read_text(encoding="utf-8")
    m = re.search(r"## Confirmado funcionando.*?\n(.*?)\n##", txt, re.S)
    bloco = m.group(1) if m else ""
    ids = []
    for ln in bloco.splitlines():
        mm = re.match(r"\|\s*`([^`]+)`", ln)
        if mm and "/" in mm.group(1):
            ids.append(mm.group(1))
    return ids


def _roster_conselho():
    if not CONSELHO.is_file():
        return []
    txt = CONSELHO.read_text(encoding="utf-8")
    m = re.search(r"ROSTER\s*=\s*\[(.*?)\]", txt, re.S)
    return re.findall(r'"([^"]+/[^"]+)"', m.group(1)) if m else []


def _modelos_das_filas():
    """(26/10/2026) Os modelos que já estão nas filas da Seth (registro de capacidades). Sem eles,
    o relatório de 25/10 listou como 'candidatos' o Gemini 3.1 Flash-Lite e o 3 Flash, já nas filas."""
    try:
        reg = json.loads(CAPACIDADES.read_text(encoding="utf-8"))
        return sorted({m for fila in (reg.get("filas") or {}).values() for m in fila})
    except (OSError, ValueError, AttributeError):
        return []


def _modelos_omniroute_nao_no_pool(ja_conhecidos, models=None):
    if models is None:
        models = _modelos_omni_api()
    fora = []
    for m in models or []:
        if not isinstance(m, dict):
            continue
        full = m.get("fullModel") or m.get("model")
        if isinstance(full, str) and full and full not in ja_conhecidos and m.get("available"):
            fora.append(full)
    return fora


def _discovery(varrer):
    """Lê os resultados do Discovery. `varrer=True` (só no ensaio com --scan) dispara
    antes uma varredura nova -- escreve no OmniRoute; a descoberta nunca varre."""
    try:
        if varrer:
            _http(f"{OMNIROUTE}/api/discovery/scan", "POST", {}, timeout=20,
                  classification="public")
            time.sleep(30)
        return _http(f"{OMNIROUTE}/api/discovery/results", timeout=20)
    except Exception as e:  # noqa: BLE001
        return {"erro": f"{type(e).__name__}: {e}"}


def _ler_json(caminho):
    if caminho.is_file():
        try:
            return json.loads(caminho.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def descobrir(anterior=None):
    """Modo DESCOBERTA: só GET, nenhuma chamada a modelo. Devolve o estado comparável."""
    conhecidos = set(_pool_confirmado()) | set(_roster_conselho()) | set(_modelos_das_filas())
    models = _modelos_omni_api()   # uma chamada só, reaproveitada abaixo
    candidatos = sorted(_modelos_omniroute_nao_no_pool(conhecidos, models if models is not None else []))
    disc = _discovery(False)
    return {"quando": date.today().isoformat(), "candidatos": candidatos,
            "catalogo_vivo": comparar_catalogo_vivo((anterior or {}).get("catalogo_vivo"), models)}, disc


def _secao_catalogo_vivo(cv):
    linhas = ["## Catálogo vivo x OmniRoute (lista pública de cada provedor, só GET)", "",
              "_Aposentado = está no OmniRoute e saiu da lista viva (provável; confirme antes de tirar)._",
              "_Novo = está na lista viva e não no OmniRoute (OpenRouter: só `:free`). NVIDIA: catálogo, gratuidade não verificada._",
              "_Só modelos de chat/texto entram; embedding, rerank, áudio e imagem ficam fora._", ""]
    for prov, r in sorted((cv or {}).items()):
        if "erro" in r:
            linhas += [f"### {prov}", "", f"- não comparado: {r['erro']}", ""]
            continue
        if r.get("suspeito"):
            linhas += [f"### {prov}: ATENÇÃO", "",
                       f"- {r.get('motivo_suspeito')}: a lista pública pode ser parcial. "
                       "Não trate como aposentado sem conferir.", ""]
        linhas += [f"### {prov}: {len(r['aposentados'])} aposentado(s), {len(r['novos'])} novo(s) "
                   f"(vivo={r['total_vivo']}, OmniRoute={r['total_omniroute']})", "",
                   "Aposentados:", ""]
        linhas += [f"- `{m}`" for m in r["aposentados"][:TETO_LISTA]] or ["- (nenhum)"]
        linhas += ["", "Novos" + (" (catálogo, gratuidade não verificada)" if prov == "nvidia" else "") + ":", ""]
        linhas += [f"- `{m}`" for m in r["novos"][:TETO_LISTA]] or ["- (nenhum)"]
        if len(r["novos"]) > TETO_LISTA:
            linhas.append(f"- ... e mais {len(r['novos']) - TETO_LISTA}")
        linhas.append("")
    return linhas


def _escrever_descoberta(atual, disc):
    hoje = date.today().isoformat()
    alvo = REPO / "propostas" / f"modelos-gratuitos-{hoje}.md"
    linhas = [
        f"# Descoberta de modelos gratuitos — {hoje}",
        "",
        "_Gerada por `scripts/pesquisar_modelos_gratuitos.py` em modo DESCOBERTA: nenhuma",
        "chamada a modelo, zero cota. NÃO é canon, NÃO implementa nada. Candidato aqui",
        "quer dizer disponível no catálogo do OmniRoute, nunca 'funciona': para testar,",
        "rode à mão `--ensaio` (gasta cota). MEMÓRIAS (377)._",
        "",
        "## Candidatos fora do pool, do ROSTER e das filas (catálogo do OmniRoute)",
        "",
    ] + ([f"- `{m}`" for m in atual["candidatos"]] or ["- (nenhum)"]) + [
        "",
    ] + _secao_catalogo_vivo(atual.get("catalogo_vivo")) + [
        "## Últimos resultados do Discovery (leitura, sem varredura nova)",
        "",
        "```json",
        json.dumps(disc, ensure_ascii=False, indent=2)[:2000],
        "```",
    ]
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return alvo


def _casos_catalogo():
    """Casos do catálogo vivo, com dados sintéticos e rede bloqueada."""
    global _http, _http_publico, _token_interno, _abrir
    real_http, real_pub, real_tok, real_abrir = _http, _http_publico, _token_interno, _abrir
    real_urlopen = urllib.request.urlopen
    casos = []
    SEGREDO = "SEGREDO-TOKEN-123"
    vistos = []

    class _Resp:
        def __init__(self, b):
            self.b = b
        def read(self):
            return self.b
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    def urlopen_com(corpo=None, erro=None):
        def f(req, timeout=None):
            vistos.append(req)
            if erro:
                raise erro
            return _Resp(corpo)
        return f

    omni_api = {"models": [{"fullModel": f"nvidia/{i}"} for i in ("a", "b", "c", "d", "e")]
                + [{"fullModel": "nvidia/black-forest-labs/flux.1-dev"}, {"fullModel": "openrouter/auto"},
                   {"fullModel": "openrouter/x/y:free"}, {"fullModel": "groq/z"}]}
    n_api = []

    def http_omni(url, metodo="GET", body=None, timeout=45, classification=None):
        if url.endswith("/api/models"):
            n_api.append(url)
            return omni_api
        if url.endswith("/v1/models"):
            return {"data": [{"id": "nvidia/a"}]}
        return {}

    def pub_com(ids_nv, ids_or=("x/y:free",)):
        def f(url, timeout=30):
            ids = ids_nv if "nvidia" in url else ids_or
            return {"data": [{"id": i} for i in ids]}
        return f

    try:
        _token_interno = lambda: SEGREDO  # noqa: E731
        # (1) _http_publico REAL, urlopen trocado: nenhum cabeçalho leva o token
        urllib.request.urlopen = urlopen_com(b'{"data": []}')
        real_pub("https://exemplo.invalido/v1/models")
        cab = {k.lower(): v for k, v in vistos[-1].header_items()}
        casos.append(("_http_publico real não envia X-Agata-Token nem o valor do token",
                      "x-agata-token" not in cab and not any(SEGREDO in str(v) for v in cab.values())
                      and not any(SEGREDO in str(k) for k in cab)))
        # (5) JSON inválido, 401, formas erradas, sobre o _http_publico real
        _http = http_omni
        for nome, urlopen_f in (
            ("JSON inválido", urlopen_com(b"nao e json")),
            ("HTTP 401", urlopen_com(erro=urllib.error.HTTPError("u", 401, "no", {}, None))),
            ("data null", urlopen_com(b'{"data": null}')),
            ("lista na raiz", urlopen_com(b'[{"id": "a"}]')),
        ):
            urllib.request.urlopen = urlopen_f
            _http_publico = real_pub
            r = comparar_catalogo_vivo(None, omni_api["models"])
            casos.append((f"{nome}: erro por provedor, sem comparar",
                          "erro" in r["nvidia"] and "aposentados" not in r["nvidia"]))
        urllib.request.urlopen = real_urlopen
        # (9) host não local recusado antes de ler o token ou abrir conexão
        vistos.clear()
        _abrir = lambda req, timeout: urlopen_com(b"{}")(req, timeout)  # noqa: E731
        _tok_lido = []
        _token_interno = lambda: _tok_lido.append(1) or SEGREDO  # noqa: E731
        try:
            real_http("http://exemplo.invalido:20128/api/models")
            recusou = False
        except ValueError:
            recusou = True
        casos.append(("host não local: recusa sem abrir conexão nem ler o token",
                      recusou and not vistos and not _tok_lido))
        _abrir = lambda req, timeout: urlopen_com(b'{"ok": 1}')(req, timeout)  # noqa: E731
        casos.append(("host local (127.0.0.1) segue funcionando",
                      real_http("http://127.0.0.1:20128/api/models") == {"ok": 1}
                      and "x-agata-token" in {k.lower() for k, _ in vistos[-1].header_items()}))
        urllib.request.urlopen = real_urlopen
        _abrir = real_abrir
        # (1) 302 para outro host local: o destino não recebe o token (servidores reais, 127.0.0.1)
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer
        recebido = []

        class _Destino(BaseHTTPRequestHandler):
            def do_GET(self):
                recebido.append({k.lower(): v for k, v in self.headers.items()})
                self.send_response(200); self.end_headers(); self.wfile.write(b"{}")
            def log_message(self, *a):
                pass

        destino = HTTPServer(("127.0.0.1", 0), _Destino)

        class _Origem(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{destino.server_port}/x")
                self.end_headers()
            def log_message(self, *a):
                pass

        origem = HTTPServer(("127.0.0.1", 0), _Origem)
        for srv in (destino, origem):
            threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            try:
                real_http(f"http://127.0.0.1:{origem.server_port}/api/models", timeout=5)
                seguiu = True
            except urllib.error.HTTPError as e:
                seguiu = e.code != 302
        finally:
            for srv in (destino, origem):
                srv.shutdown(); srv.server_close()
        casos.append(("302 vira erro e o destino do redirect não recebe o token",
                      not seguiu and not recebido))
        # lógica de comparação com dados sintéticos
        _http = http_omni
        _http_publico = pub_com(["a", "b", "c", "novo-chat", "nvidia/embed-qa-4", "x/tts-voz"])
        r = comparar_catalogo_vivo(None, omni_api["models"])["nvidia"]
        casos += [
            ("40% aposentados (2 de 5) não é suspeito", r["aposentados"] == ["d", "e"] and not r["suspeito"]),
            ("modalidade: flux fora dos aposentados, embed/tts fora dos novos",
             r["novos"] == ["novo-chat"] and "black-forest-labs/flux.1-dev" not in r["aposentados"]),
        ]
        _http_publico = pub_com(["a", "b"])
        r = comparar_catalogo_vivo(None, omni_api["models"])["nvidia"]
        casos.append(("60% aposentados (3 de 5) é suspeito", len(r["aposentados"]) == 3 and r["suspeito"]))
        _http_publico = pub_com(["a", "b", "c", "d", "e"])
        casos.append(("queda de total_vivo vs execução anterior é suspeito",
                      comparar_catalogo_vivo({"nvidia": {"total_vivo": 10}}, omni_api["models"])["nvidia"]["suspeito"]
                      and not comparar_catalogo_vivo({"nvidia": {"total_vivo": 6}}, omni_api["models"])["nvidia"]["suspeito"]))
        rr = comparar_catalogo_vivo(None, omni_api["models"])["openrouter"]
        casos.append(("openrouter: virtual ignorado, novo só :free", rr["aposentados"] == [] and rr["novos"] == []))
        # (2) filtro :free do OpenRouter
        _http = http_omni
        _http_publico = pub_com(["a"], ("x/y:free", "z/pago", "w/novo:free"))
        casos.append(("openrouter: novos == ['w/novo:free'] (pago fora)",
                      comparar_catalogo_vivo(None, omni_api["models"])["openrouter"]["novos"] == ["w/novo:free"]))
        # (3) fullModel não-str ignorado sem derrubar a rodada
        sujo = omni_api["models"] + [{"fullModel": 123}, {"fullModel": ["x"]}, {"fullModel": None}, "texto", None]
        _http_publico = pub_com(["a", "b", "c", "d", "e"])
        try:
            rs = comparar_catalogo_vivo(None, sujo)
            cands = _modelos_omniroute_nao_no_pool(set(), sujo)
            ok_sujo = rs["nvidia"]["total_omniroute"] == 5 and isinstance(cands, list)
        except Exception:  # noqa: BLE001
            ok_sujo = False
        casos.append(("fullModel não-str ignorado, rodada não cai", ok_sujo))
        # (3) OmniRoute sem ids: erro por provedor, não vira 'novos'
        def http_cai(url, **kw):
            raise OSError("sem rede")
        _http = http_cai
        _http_publico = pub_com(["a", "b", "c"])
        rc = comparar_catalogo_vivo(None, _modelos_omni_api())
        casos.append(("OmniRoute indisponível: erro por provedor, não compara",
                      all("erro" in v for v in rc.values())))
        # (6) 'mudou' ignora totais
        c1 = {"nvidia": {"aposentados": ["x"], "novos": ["y"], "total_vivo": 10}}
        c2 = {"nvidia": {"aposentados": ["x"], "novos": ["y"], "total_vivo": 11}}
        c3 = {"nvidia": {"aposentados": ["x"], "novos": ["z"], "total_vivo": 10}}
        casos.append(("mudou: total diferente não conta; lista diferente conta",
                      _chave_mudanca(c1) == _chave_mudanca(c2) != _chave_mudanca(c3)))
        # (7) rótulo dos novos da NVIDIA
        txt = "\n".join(_secao_catalogo_vivo({"nvidia": dict(c1["nvidia"], total_omniroute=1, suspeito=False)}))
        casos.append(("novos NVIDIA rotulados 'gratuidade não verificada'", "gratuidade não verificada" in txt))
        # (8) /api/models lido uma vez só na descoberta
        n_api.clear()
        _http = http_omni
        _http_publico = pub_com(["a"])
        _descobrir_com = (_pool_confirmado, _roster_conselho, _modelos_das_filas)
        try:
            globals().update(_pool_confirmado=lambda: [], _roster_conselho=lambda: [],
                             _modelos_das_filas=lambda: [])
            descobrir()
        finally:
            globals().update(_pool_confirmado=_descobrir_com[0], _roster_conselho=_descobrir_com[1],
                             _modelos_das_filas=_descobrir_com[2])
        casos.append(("descoberta chama /api/models uma única vez", len(n_api) == 1))
        # (5) idem quando /api/models falha
        n_falha = []

        def http_api_falha(url, **kw):
            if url.endswith("/api/models"):
                n_falha.append(url)
                raise OSError("fora")
            return {"data": []}
        _http = http_api_falha
        try:
            globals().update(_pool_confirmado=lambda: [], _roster_conselho=lambda: [],
                             _modelos_das_filas=lambda: [])
            descobrir()
        finally:
            globals().update(_pool_confirmado=_descobrir_com[0], _roster_conselho=_descobrir_com[1],
                             _modelos_das_filas=_descobrir_com[2])
        casos.append(("/api/models falhando: ainda uma única chamada", len(n_falha) == 1))
        # (6) 'suspeito' entra na chave de mudança
        d1 = {"nvidia": dict(c1["nvidia"], suspeito=False)}
        d2 = {"nvidia": dict(c1["nvidia"], suspeito=True)}
        casos.append(("mudar só o suspeito conta como mudança", _chave_mudanca(d1) != _chave_mudanca(d2)))
        # (4) novas famílias não-chat
        casos.append(("modalidade: guard/cosmos/ocr/safety/translate fora",
                      not any(_e_chat(i) for i in ("nvidia/x-guard-8b", "nvidia/cosmos-r", "a/ocr-2",
                                                    "a/safety-1", "a/riva-translate", "a/speech-1",
                                                    "a/audio-x", "a/vision-x", "a/retriever-x"))
                      and _e_chat("meta/llama-4")))
    finally:
        _http, _http_publico, _token_interno, _abrir = real_http, real_pub, real_tok, real_abrir
        urllib.request.urlopen = real_urlopen
    return casos


def _selftest():
    global _http, _pool_confirmado, _roster_conselho, _modelos_das_filas, CAPACIDADES
    chamadas = []

    def falso_http(url, metodo="GET", body=None, timeout=45, classification=None):
        chamadas.append((metodo, url))
        if url.endswith("/api/models"):
            return {"models": [{"fullModel": "a/novo", "available": True},
                               {"fullModel": "b/pool", "available": True},
                               {"fullModel": "c/fora", "available": False},
                               {"fullModel": "d/fila", "available": True}]}
        return {"ok": True}

    orig = (_http, _pool_confirmado, _roster_conselho, _modelos_das_filas)
    _http, _pool_confirmado, _roster_conselho = falso_http, lambda: ["b/pool"], lambda: []
    _modelos_das_filas = lambda: ["d/fila"]  # noqa: E731
    global _http_publico
    _pub = _http_publico
    _http_publico = lambda url, timeout=30: {"data": []}  # noqa: E731  (rede bloqueada)
    try:
        atual, _ = descobrir()
        casos = [
            ("descoberta não chama modelo", not any("/chat/completions" in u for _, u in chamadas)),
            ("descoberta não escreve no OmniRoute (só GET)", all(m == "GET" for m, _ in chamadas)),
            ("candidato = disponível e fora do pool, do ROSTER e das filas", atual["candidatos"] == ["a/novo"]),
            ("descoberta lê os resultados do Discovery", any(u.endswith("/api/discovery/results")
                                                            for _, u in chamadas)),
        ]
        chamadas.clear()
        _discovery(True)
        casos.append(("só o --scan dispara varredura (POST)", ("POST", f"{OMNIROUTE}/api/discovery/scan")
                      in chamadas))
    finally:
        _http, _pool_confirmado, _roster_conselho, _modelos_das_filas = orig
        _http_publico = _pub
    casos += _casos_catalogo()
    _cap = CAPACIDADES
    CAPACIDADES = Path(__file__).resolve().parents[1] / "config" / "capivara" / "capacidades.json"  # o do checkout, não o de AGATA_REPO (o CI não tem ~/agata)
    try:
        casos.append(("filas lidas do registro do checkout", any(m.startswith("ollama-local/") for m in _modelos_das_filas())))
    finally:
        CAPACIDADES = _cap
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


def _log(msg):
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now(timezone.utc).astimezone().isoformat()}] {msg}\n")


def _etapa_capivara(origem=None, estado=None, perfil=None, fetch_omni=None, fetch_publico=None, uso=None, hoje=None):
    """(23/11/2026) Etapa semanal da capivara. Lê o registro em uso (o do estado se for válido; senão o retrato
    do repositório, `origem`) e grava SÓ no estado (`estado`, padrão ~/.local/share/agata/capivara/):
    1) semeadura da camada `declarado` a partir do /v1/models do OmniRoute (local) e das listas públicas
       do OpenRouter e da NVIDIA (GET sem chave, o mesmo LISTAS_VIVAS acima). Uma fonte que falha não
       apaga o que já tinha: a afirmação antiga fica, com a data antiga;
    2) incorporação do uso real (`observado`, uso.jsonl do gateway), só o que é novo;
    3) regenera o perfil derivado no estado (`perfil`).
    NÃO escreve em config/capivara/ (retrato versionado) e NÃO muda o perfil que o gateway lê (ele passa o
    retrato por caminho explícito): mudar roteamento é decisão do Humano, por proposta assinada.
    Nenhuma chamada a modelo, nenhuma escrita no OmniRoute."""
    import capivara_capacidades as cap  # noqa: E402  (scripts/, já no sys.path)
    import capivara_perfis as perf  # noqa: E402
    origem = origem or (REPO / "config" / "capivara" / "capacidades.json")
    estado = estado or cap.ESTADO_REGISTRO
    perfil = perfil or cap.ESTADO_PERFIL
    hoje = hoje or date.today().isoformat()
    base = estado if cap.registro_valido(estado) else origem
    reg = cap.carregar(base)
    if not reg.get("modelos"):
        return {"erro": f"registro ausente em {base.name}"}
    antes = json.dumps(reg, sort_keys=True)
    cap.normalizar(reg)
    buscar_omni = fetch_omni or (lambda: _http(f"{OMNIROUTE}/v1/models"))
    buscar_pub = fetch_publico or _http_publico
    fontes = [
        ("omniroute", lambda: cap.afirma_omniroute(buscar_omni(), hoje)),
        ("openrouter", lambda: cap.afirma_openrouter(buscar_pub(LISTAS_VIVAS["openrouter"][0]), hoje)),
        ("nvidia", lambda: cap.afirma_nvidia(buscar_pub(LISTAS_VIVAS["nvidia"][0]), hoje)),
    ]
    resumo, tudo = {}, {}
    for nome, buscar in fontes:
        try:
            af = buscar()
        except Exception as e:  # noqa: BLE001  (uma fonte fora do ar não derruba a etapa)
            resumo[nome] = f"erro: {type(e).__name__}: {e}"[:160]
            continue
        resumo[nome] = len(af)
        for mid, campos in af.items():
            for campo, lista in campos.items():
                tudo.setdefault(mid, {}).setdefault(campo, []).extend(lista)
    aplicado = cap.aplicar(reg["modelos"], tudo)
    st = cap.incorporar_arquivo(reg, uso or cap.USO)  # só o que é novo desde a posição guardada
    resumo.update(aplicadas=aplicado["aplicadas"], fora_do_inventario=aplicado["fora_do_inventario"],
                  uso_linhas=st["lidas"], uso_novas=st["novas"], uso_malformadas=st["malformadas"],
                  uso_registros=st["registros"], base="estado" if base == estado else "retrato", gravado=False)
    erros = cap.conferir(reg)
    if erros:
        resumo["erro"] = "não gravado: " + "; ".join(erros[:3])
        return resumo
    if json.dumps(reg, sort_keys=True) != antes or base != estado:
        cap.gravar(reg, estado)
        resumo["gravado"] = True
    cap.gravar(perf.derivar(reg), perfil)  # perfil derivado do registro gravado, no estado
    return resumo


def main():
    args = sys.argv[1:]
    if args == ["--selftest"]:
        return _selftest()
    if "--repo" in args:
        global REPO
        REPO = Path(args[args.index("--repo") + 1])

    if "--ensaio" not in args:
        if "--scan" in args:
            print("--scan só vale com --ensaio (a descoberta nunca varre).")
            return 2
        anterior = _ler_json(ULTIMA_DESCOBERTA)
        atual, disc = descobrir(anterior)
        ESTADO_DIR.mkdir(parents=True, exist_ok=True)
        ULTIMA_DESCOBERTA.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")
        try:  # capivara: roda sempre, mesmo quando a descoberta não mudou
            _log(f"capivara: {_etapa_capivara()}")
        except Exception as e:  # noqa: BLE001
            _log(f"capivara: FALHA {type(e).__name__}: {e}")
        if (atual["candidatos"] == anterior.get("candidatos")
                and _chave_mudanca(atual["catalogo_vivo"]) == _chave_mudanca(anterior.get("catalogo_vivo"))):
            _log(f"descoberta: sem mudança. candidatos={atual['candidatos']}")
            print("descoberta: sem mudança -- nenhuma proposta escrita.")
            return 0
        alvo = _escrever_descoberta(atual, disc)
        _log(f"descoberta: MUDOU -> escreveu {alvo.name}. candidatos={atual['candidatos']}")
        print(f"escrito: {alvo}")
        return 0

    confirmados = _pool_confirmado()
    roster = _roster_conselho()
    alvos = list(dict.fromkeys(confirmados + roster))
    resultados = {m: _sondar(m) for m in alvos}

    extras = _modelos_omniroute_nao_no_pool(set(alvos))
    novos = {}
    for m in extras[:12]:            # teto: não martelar 40 modelos
        novos[m] = _sondar(m)

    disc = _discovery("--scan" in args)

    atual = {
        "quando": date.today().isoformat(),
        "pool": {m: r[0] for m, r in resultados.items()},
        "novos_ok": sorted(m for m, r in novos.items() if r[0] == "OK"),
    }
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    anterior = _ler_json(ULTIMO)

    mudou = (atual["pool"] != anterior.get("pool")
             or atual["novos_ok"] != anterior.get("novos_ok", []))
    ULTIMO.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")

    if not mudou:
        _log(f"sem mudança. pool={atual['pool']}")
        print("sem mudança no pool -- nenhuma proposta escrita.")
        return 0

    hoje = date.today().isoformat()
    alvo = REPO / "propostas" / f"modelos-gratuitos-{hoje}.md"
    ok_agora = sorted(m for m, r in resultados.items() if r[0] == "OK")
    linhas = [
        f"# Pesquisa de modelos gratuitos — {hoje}",
        "",
        "_Gerada por `scripts/pesquisar_modelos_gratuitos.py`. NÃO é canon, NÃO",
        "implementa nada. Se aprovada, o Humano aplica à mão: edita",
        "`config/modelos-gratuitos.md` + `ROSTER` de `conselho_remoto.py` (proposta",
        "assinada) e os combos/roteador do OmniRoute (UI). MEMÓRIAS (377)._",
        "",
        "## Pool re-testado",
        "",
        "| modelo | estado | detalhe |",
        "|---|---|---|",
    ]
    for m, (est, det) in sorted(resultados.items()):
        linhas.append(f"| `{m}` | {est} | {det} |")
    linhas += ["", "## Modelos do OmniRoute fora do pool que responderam OK", ""]
    linhas += [f"- `{m}`" for m in sorted(novos) if novos[m][0] == "OK"] or ["- (nenhum)"]
    linhas += [
        "",
        "## Rascunho de ROSTER (só os OK agora, ordem = a atual + novos no fim)",
        "",
        "```python",
        "ROSTER = [",
    ] + [f'    "{m}",' for m in ok_agora] + [
        "]",
        "```",
        "",
        f"## Discovery do OmniRoute",
        "",
        "```json",
        json.dumps(disc, ensure_ascii=False, indent=2)[:2000],
        "```",
        "",
        "## Famílias que dependem de chave do Humano (não integradas aqui)",
        "",
    ] + [f"- {c}" for c in CANDIDATOS_COM_CHAVE] + [
        "",
        "Pra integrar uma: pôr a chave em `~/.config/agata/.env`, adicionar o",
        "provedor no OmniRoute, 1 teste ao vivo, e então proposta assinada.",
    ]
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    _log(f"MUDOU -> escreveu {alvo.name}. ok_agora={ok_agora}")
    print(f"escrito: {alvo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
