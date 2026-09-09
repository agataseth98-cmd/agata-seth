#!/usr/bin/env python3
"""Coletor do Conselho Remoto -- Fase 1 (MEMÓRIAS (206)/(207)).

UMA tarefa: enviar um pedido de parecer ja escrito pelo Humano a UM modelo
remoto, guardar a resposta crua. Nada alem disso -- ver REGRAS "Segunda
opiniao" e PROJETO "Conselho Remoto".

Desde P1-04 (branch redesign, 2026-09-02): a chamada externa vai pelo OmniRoute,
ATRAVES do proxy de sanitizacao em 127.0.0.1:20127 (P1-02). Este script NAO le
mais chave nenhuma.

ROTACAO JUSTA (06/09/2026, ordem do Humano: "ninguem tem papel fixo... revogo
GLM... deve ser decidido entre modelos gratuitos sob um regime de regras
justas de rotatividade"). Desde MEMÓRIAS (381) a granularidade e' por FAMILIA
(fornecedor/vendor), nao por modelo -- ordem do Humano: "silo proprio por
familia nao modelo". Escolhe, a cada chamada, um modelo da FAMILIA com MENOS
usos bem-sucedidos entre os DISPONIVEIS do roster gratuito (ROSTER abaixo); o
circuit breaker segue POR MODELO, entao um modelo problematico nao resfria a
familia inteira.

CAMADA DE PROTECAO (MEMORIAS (374), depois de o roster inteiro cair no mesmo
dia -- 403 Cloudflare no Groq, 404 no MiniMax, 504/reasoning-burn no Gemini,
529 na z.ai):
  - CIRCUIT BREAKER por modelo: falha de transporte OU rejeicao no portao ->
    cooldown exponencial (5min, 10, 20... teto 6h); a rotacao PULA quem esta
    em cooldown. Fecha o bug de (360) (modelo que sempre falha ficava "menos
    usado" pra sempre). Sucesso zera o breaker daquele modelo.
  - PORTAO DE RESPOSTA (_portao_resposta): rejeita resposta vazia, truncada
    por reasoning-burn (reasoning_tokens ~ completion_tokens), ou curta demais.
    Rejeitada vale a mesma penalidade de uma falha de rede.
  - LACA entre os modelos disponiveis numa invocacao (era: 1 tiro so). Ainda
    UMA chamada BEM-SUCEDIDA por invocacao -- para no 1o que passa no portao.
  - FALLBACK LOCAL automatico: roster remoto inteiro fora/rejeitado -> UMA
    chamada ao qwen local, registrada com `fallback_local: true` e aviso de
    que NAO e opiniao de familia independente. Antes de (374) isso era
    "decisao do Humano" (276); agora e automatico mas rotulado sem disfarce.
  - CHECAGEM DE IDENTIDADE: se a resposta assina um nome != resposta_crua.model
    -> `IDENTIDADE SUSPEITA` no registro (nao bloqueia; catalogo de falhas).
  - P-15 (perimetro.sh) le SUCESSOS_LOG: AVISO se < 2 familias tiveram sucesso
    em 24h.

O QUE NAO MUDOU (a razao do script existir):
  - so material do repo PUBLICO sai: checar_conteudo_privado trava memoria/missoes
  - teto de tamanho do pedido (heuristica pre-envio)
  - o proxy de sanitizacao :20127 continua barrando segredo antes do egresso
  - o fallback local (antes decisao do Humano caso a caso, MEMÓRIAS (276)) agora
    e automatico QUANDO o roster remoto inteiro cai -- mas rotulado sem disfarce
    (ver CAMADA DE PROTECAO acima); o Humano decide o que fazer com ele.
  - nao escreve MEMORIAS/PROJETO/REGRAS; nao interpreta, resume nem julga
  - guarda a resposta crua; so relata "fora do formato" quando aplicavel

Rastreabilidade (Cadeia de auditoria em camadas, Camada B/C, 03/09/2026): a combo
`conselho` do OmniRoute e' config (hoje `zai/glm-4.7-flash -> gemini-2.5-flash`,
strategy=priority, SEM tier local -- verificado na Maquina em storage.sqlite). Se
a combo mudar, o parecer usa outro modelo sem mudanca aqui -- por isso o registro
`.json` grava `combo`, `modelo` e `provider` (derivado) do parecer especifico,
alem da `resposta_crua`. Camada C tambem confirmou: I4 preservado (combo sem local),
`checar_conteudo_privado` byte a byte identico ao de `main`. Os logs do OmniRoute
(`~/.omniroute/call_logs/`) guardam o texto do pedido -- por I1 e' material publico;
segredo e' barrado no proxy `:20127` antes do egresso.

Merge para `main`: so na Fase 8 (Cadeia de auditoria). Ate la vive no branch.

Uso: python3 scripts/conselho_remoto.py <arquivo-com-o-pedido.txt>
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# P1-04: egresso unico pelo proxy de sanitizacao -> OmniRoute. Overridavel por
# env so para teste (CONSELHO_ENDPOINT).
SANITIZADOR_ENDPOINT = os.environ.get(
    "CONSELHO_ENDPOINT", "http://127.0.0.1:20127/v1/chat/completions"
)
COMBO = "conselho"   # legado -- so usado se ROSTER ficar vazio (nunca deveria)

DESTINO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memoria", "missoes", "conselho-remoto",
)

# Roster da rotação justa -- só modelos com free tier CONFIRMADO e testado ao
# vivo. Revisto em MEMÓRIAS (374) depois de o roster inteiro cair no mesmo dia:
#  - fora: `groq/openai/gpt-oss-120b` -- Cloudflare fichou o cliente HTTP do
#    OmniRoute como bot (403 browser_signature_banned, PERSISTENTE); e gpt-oss
#    queima o orçamento de tokens em "reasoning" e devolve vazio.
#  - fora: `openrouter/minimax/minimax-m3:free` -- rota 404 (modelo saiu do free
#    tier). OpenRouter fica SEM entrada: `openrouter/auto` e' produto PAGO
#    ("Auto Best Available"), nao um alias grátis do OmniRoute (o proprio painel
#    de Combos avisa) -- MEMÓRIAS (376). Um modelo `openrouter/<x>:free` volta ao
#    roster quando confirmado ao vivo.
#  - dentro: `cerebras/gemma-4-31b` -- testado ao vivo em (374): 200, finish=stop,
#    zero reasoning tokens, limpo.
#  - dentro (MEMÓRIAS (379)): `huggingface/meta-llama/Llama-3.3-70B-Instruct` --
#    testado ao vivo pelo :20127: 200, finish=stop, ~1,3s, sem reasoning burn.
#    Infra HF Inference Providers (empresa distinta). Ressalva: free tier da HF
#    e' credito mensal pequeno; esgotou -> 402 -> o breaker poe em cooldown e a
#    rotacao segue. `Llama-3.1-8B-Instruct` (mesma conta) e' a alternativa barata.
#  - dentro (MEMÓRIAS (379)): `mistral/ministral-8b-latest` -- 200, finish=stop,
#    ~0,55s pelo :20127. `mistral/mistral-small-latest` foi testado junto e da
#    429 no free tier desta conta; ministral-8b (e ministral-3b) respondem
#    normal. 5ª familia independente.
# Ordem = desempate determinístico quando a contagem empata.
ROSTER = [
    "zai/glm-4.7-flash",
    "gemini/gemini-2.5-flash",
    "cerebras/gemma-4-31b",
    "huggingface/meta-llama/Llama-3.3-70B-Instruct",
    "mistral/ministral-8b-latest",
]
# Modelos que gastam o orçamento em "reasoning" antes de responder precisam de
# teto alto pra sobrar espaço pro conteúdo visível (medido em (374): Gemini
# 2.5-flash queimou 3836/3996 tokens em reasoning e truncou). Default = TETO.
MAX_TOKENS_POR_MODELO = {
    "gemini/gemini-2.5-flash": 12_000,
}
ROTACAO_ESTADO = os.path.join(DESTINO_DIR, "rotacao-estado.json")
BREAKER_ESTADO = os.path.join(DESTINO_DIR, "breaker.json")
SUCESSOS_LOG = os.path.join(DESTINO_DIR, "sucessos.log")   # P-15 lê daqui
BREAKER_BASE_S = 300        # 1ª falha -> 5 min de cooldown
BREAKER_MAX_S = 6 * 3600    # teto do backoff exponencial
MIN_CHARS_RESPOSTA = 80     # abaixo disso a resposta não consolida nada
# Fallback local quando o roster remoto inteiro está indisponível/rejeitado.
FALLBACK_OLLAMA = os.environ.get("AGATA_OLLAMA_URL", "http://localhost:11434/api/generate")
FALLBACK_MODELO = os.environ.get("AGATA_FALLBACK_MODELO", "qwen3.5-9b-64k:latest")


def _familias_do_roster():
    """Conjunto de famílias representadas no ROSTER agora."""
    return {_familia(m) for m in ROSTER}


def _carregar_rotacao():
    """Contagem de usos BEM-SUCEDIDOS por FAMÍLIA (MEMÓRIAS (381)): soma dos
    sucessos de qualquer modelo daquela família. Lê o formato ANTIGO do
    arquivo (chaves = id de modelo) e migra somando na família; o formato
    novo (chaves = nome de família) é lido direto. Família nova entra com 0."""
    bruto = {}
    if os.path.isfile(ROTACAO_ESTADO):
        try:
            with open(ROTACAO_ESTADO, encoding="utf-8") as f:
                bruto = json.load(f)
        except Exception:  # noqa: BLE001 -- arquivo corrompido não trava a escolha
            bruto = {}
    familias = _familias_do_roster()
    cont = {fam: 0 for fam in familias}
    for chave, n in (bruto.items() if isinstance(bruto, dict) else []):
        # chave já é nome de família (formato novo) OU id de modelo (antigo).
        fam = chave if chave in familias else _familia(chave)
        if fam in cont:
            try:
                cont[fam] += int(n)
            except (TypeError, ValueError):  # valor lixo no arquivo -- ignora
                pass
    return cont


# --- circuit breaker por modelo (MEMÓRIAS (374)) -----------------------------
# Fecha o bug de (360): um modelo que sempre falha ficava "menos usado" pra
# sempre e era escolhido em loop. Agora falha gera cooldown exponencial e a
# rotação PULA quem está em cooldown.
def _carregar_breaker():
    try:
        with open(BREAKER_ESTADO, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def _gravar_breaker(b):
    os.makedirs(DESTINO_DIR, exist_ok=True)
    with open(BREAKER_ESTADO, "w", encoding="utf-8") as f:
        json.dump(b, f, ensure_ascii=False, indent=2)


def _registrar_falha(modelo):
    """Falha de transporte OU rejeição no portão -- vale a mesma penalidade."""
    b = _carregar_breaker()
    e = b.get(modelo, {"fails": 0, "cooldown_ate": 0})
    e["fails"] = int(e.get("fails", 0)) + 1
    espera = min(BREAKER_BASE_S * (2 ** (e["fails"] - 1)), BREAKER_MAX_S)
    e["cooldown_ate"] = time.time() + espera
    b[modelo] = e
    _gravar_breaker(b)
    return int(espera)


def _familia(modelo):
    m = (modelo or "").lower()
    # "huggingface" tem que vir ANTES de "llama"/"qwen": o id da HF e'
    # `huggingface/meta-llama/Llama-3.3-70B-Instruct` e o casamento e' por
    # substring, primeira chave que bate ganha. Sem isto cairia em "local"
    # (errado -- e' chamada remota) e o P-15 contaria familia de menos.
    for chave, fam in (("glm", "zhipu"), ("zai", "zhipu"), ("gemini", "google"),
                       ("cerebras", "cerebras"), ("groq", "groq"),
                       ("huggingface", "huggingface"), ("mistral", "mistral"),
                       ("openrouter", "openrouter"), ("qwen", "local"),
                       ("llama", "local"), ("minimax", "openrouter")):
        if chave in m:
            return fam
    return "?"


def _disponiveis():
    """ROSTER menos os modelos em cooldown ativo."""
    b = _carregar_breaker()
    agora = time.time()
    return [m for m in ROSTER if float(b.get(m, {}).get("cooldown_ate", 0)) <= agora]


def escolher_modelo():
    """Família MENOS usada primeiro, ENTRE os modelos disponíveis (fora de
    cooldown). Dentro da família, e no empate entre famílias, a ordem do
    ROSTER decide. None = roster inteiro em cooldown. (MEMÓRIAS (381): a
    granularidade passou de modelo pra família; o breaker segue por modelo,
    então um modelo problemático não resfria a família toda.)"""
    disp = _disponiveis()
    if not disp:
        return None
    cont = _carregar_rotacao()
    return min(disp, key=lambda m: (cont.get(_familia(m), 0), ROSTER.index(m)))


def _registrar_sucesso(modelo_escolhido):
    """Sucesso: zera o breaker DO MODELO, conta uso na rotação DA FAMÍLIA,
    loga p/ P-15. A 1ª gravação depois de (381) já sai no formato novo
    (chaves = família), migrando o arquivo."""
    b = _carregar_breaker()
    if modelo_escolhido in b:
        b[modelo_escolhido] = {"fails": 0, "cooldown_ate": 0}
        _gravar_breaker(b)
    fam = _familia(modelo_escolhido)
    cont = _carregar_rotacao()
    if fam in cont:
        cont[fam] += 1
    os.makedirs(DESTINO_DIR, exist_ok=True)
    with open(ROTACAO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(cont, f, ensure_ascii=False, indent=2)
    try:
        with open(SUCESSOS_LOG, "a", encoding="utf-8") as f:
            f.write(f"{int(time.time())}\t{modelo_escolhido}\t{fam}\n")
    except Exception:  # noqa: BLE001 -- log é auditoria, não trava
        pass

# Tetos, primeiro corte -- ajustavel pelo Humano, nao um numero canonizado.
TETO_CHARS_PEDIDO = 60_000   # heuristica pre-envio -- nao ha tokenizador local
TETO_TOKENS_SAIDA = 4_000    # vira max_tokens no pedido -- teto mecanico

# Achado real na primeira invocacao (MEMÓRIAS (212)): com "thinking" habilitado
# o GLM-4.7-Flash gastou os tokens de saida inteiros tentando calcular um hash
# de cabeca, em loop, e nunca produziu o parecer. Pedimos para desligar; o
# OmniRoute repassa se o provedor aceitar. Se o loop voltar apesar disso, e
# follow-up de P1-04 (config no lado do OmniRoute).
DESABILITAR_THINKING = True
# ...mas o campo `thinking` no topo do payload SO vai pros provedores que (a) o
# aceitam e (b) de fato entram em loop de raciocinio sem ele. Medido 08/09
# (MEMÓRIAS (379)) ao vivo pelo :20127: `cerebras/*` rejeita (400
# wrong_api_format), `mistral/*` rejeita (422 extra_forbidden), `huggingface/*`
# aceita mas ignora. Mandar pra todos punha 3 dos 5 do ROSTER em cooldown
# permanente e esvaziava o ganho de (379). Pros modelos que NAO recebem o flag,
# quem protege contra reasoning-burn e' o _portao_resposta (rejeita e penaliza).
THINKING_DISABLED_PREFIXOS = ("zai/", "gemini/")
PRECO_ENTRADA_POR_TOKEN_USD = 0.0   # grátis nesta camada; formula pronta p/ quando nao for
PRECO_SAIDA_POR_TOKEN_USD = 0.0     # o custo real agora sai de `omniroute cost`

# Condicao 1 (MEMÓRIAS (206)): so material ja no repositorio PUBLICO pode sair
# daqui. memoria/missoes/ e a camada privada, local, sem remote por desenho
# (PROJETO, "Memoria e hidratacao") -- nunca deve aparecer no texto de um pedido
# que vai pra fora. Checagem mecanica, generosa nas variacoes de caminho,
# travando o envio se achar.
PADRAO_CONTEUDO_PRIVADO = re.compile(r"memoria[/\\]missoes", re.IGNORECASE)


def checar_conteudo_privado(texto):
    m = PADRAO_CONTEUDO_PRIVADO.search(texto)
    if m:
        return m.group(0)
    return None


def checar_formato_parecer(texto):
    """Confere se as 4 partes do parecer (REGRAS, 'Segunda opiniao') aparecem,
    generoso o bastante pra aceitar variacao de acento/caixa. Nao julga o
    CONTEUDO -- so a presenca estrutural das 4 partes."""
    baixo = texto.lower()
    tem_origem = "origem" in baixo
    tem_posicao = "posição" in baixo or "posicao" in baixo
    tem_fundamentacao = "fundamentação" in baixo or "fundamentacao" in baixo
    tem_emenda = "emenda" in baixo
    faltando = []
    if not tem_origem:
        faltando.append("Origem")
    if not tem_posicao:
        faltando.append("Posição")
    if not tem_fundamentacao:
        faltando.append("Fundamentação")
    if not tem_emenda:
        faltando.append("Emenda")
    return faltando


def enviar_omniroute(pedido_texto, modelo):
    """UMA chamada. POST no proxy de sanitizacao, que scrub-a o pedido e repassa
    ao OmniRoute pro `modelo` raw escolhido pela rotação (não mais uma combo
    de prioridade fixa). Devolve o JSON cru (shape OpenAI-compat)."""
    payload = {
        "model": modelo,
        "messages": [{"role": "user", "content": pedido_texto}],
        "max_tokens": MAX_TOKENS_POR_MODELO.get(modelo, TETO_TOKENS_SAIDA),
    }
    if DESABILITAR_THINKING and modelo.startswith(THINKING_DISABLED_PREFIXOS):
        # Só zai/ e gemini/ (ver THINKING_DISABLED_PREFIXOS). Gemini aceita o
        # campo mas raciocina mesmo assim (374) -- quem protege aí é o portão
        # de resposta, não este flag. cerebras/mistral/huggingface NÃO recebem:
        # rejeitam o campo ou o ignoram (379).
        payload["thinking"] = {"type": "disabled"}
    corpo = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SANITIZADOR_ENDPOINT, data=corpo, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _normalizar(resposta):
    """(conteudo, tokens_entrada, tokens_saida, tokens_total) do shape
    OpenAI-compat que o OmniRoute devolve. Nao julga nada."""
    conteudo = resposta.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
    uso = resposta.get("usage", {}) or {}
    te = uso.get("prompt_tokens", 0)
    ts = uso.get("completion_tokens", 0)
    tt = uso.get("total_tokens", te + ts)
    return conteudo, te, ts, tt


def _provider_do_modelo(modelo):
    """Emenda 2 (Cadeia de auditoria, Camada B). A resposta do OmniRoute so traz
    `model` (ex.: 'gemini-2.5-flash'), sem `provider`. Deriva o provedor do nome
    para o registro -- best-effort; a `resposta_crua` continua sendo a fonte."""
    m = (modelo or "").lower()
    for chave, prov in (("glm", "zai"), ("gemini", "gemini"), ("gpt-oss", "groq/cerebras"),
                        ("gemma", "cerebras"), ("huggingface", "huggingface"),
                        ("mistral", "mistral"), ("qwen", "local?"), ("llama", "local?"),
                        ("minimax", "openrouter"), ("auto", "openrouter")):
        if chave in m:
            return prov
    return "?"


# --- portão de resposta + checagem de identidade (MEMÓRIAS (374)) ------------
def _portao_resposta(resposta, conteudo):
    """(ok, motivo). MECÂNICO. Pega a classe de falha que 'parece' resposta:
    vazia, truncada por reasoning-burn, curta demais. NÃO julga o mérito."""
    ch = (resposta.get("choices") or [{}])[0]
    fr = ch.get("finish_reason")
    uso = resposta.get("usage") or {}
    ts = int(uso.get("completion_tokens", 0) or 0)
    rt = int((uso.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) or 0)
    c = (conteudo or "").strip()
    if not c:
        return False, f"conteúdo vazio (finish_reason={fr}, reasoning_tokens={rt}/{ts})"
    if fr == "length" and rt and rt >= ts * 0.9:
        return False, f"truncada: {rt}/{ts} tokens foram reasoning, sobrou pouco pro conteúdo"
    if len(c) < MIN_CHARS_RESPOSTA:
        return False, f"resposta curta demais ({len(c)} chars)"
    return True, "ok"


_ASSINA_MODELO = re.compile(r"(?im)^\s*modelo\s*[:\-]\s*([A-Za-z0-9 ._/\-]{2,40})")


def _checar_identidade(conteudo, resposta):
    """A resposta assina um nome de modelo que bate com resposta_crua.model?
    Não bloqueia -- marca SUSPEITA pro Humano decidir (catálogo de falhas)."""
    real = (resposta.get("model") or "").lower()
    m = _ASSINA_MODELO.search(conteudo or "")
    if not m or not real:
        return {"suspeita": False, "assinou": None, "real": real or None}
    assinou = m.group(1).strip().lower()
    # bate se qualquer token do nome real aparece no que ele assinou
    toks = [t for t in re.split(r"[^a-z0-9.]+", real) if len(t) >= 3]
    ok = any(t in assinou for t in toks)
    return {"suspeita": not ok, "assinou": m.group(1).strip(), "real": resposta.get("model")}


def _chamar_local(pedido_texto):
    """Fallback: uma chamada ao modelo LOCAL (Ollama) quando o roster remoto
    inteiro está fora. Devolve um dict no shape OpenAI-compat (parcial) + a
    marca `_fallback_local` pra ninguém confundir com opinião de família
    independente na nuvem."""
    body = json.dumps({"model": FALLBACK_MODELO, "prompt": pedido_texto,
                       "stream": False, "options": {"temperature": 0.2}}).encode("utf-8")
    req = urllib.request.Request(FALLBACK_OLLAMA, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read().decode("utf-8"))
    txt = (d.get("response") or "").strip()
    return {
        "_fallback_local": True,
        "model": FALLBACK_MODELO,
        "choices": [{"message": {"role": "assistant", "content": txt},
                     "finish_reason": "stop" if d.get("done") else "length"}],
        "usage": {"prompt_tokens": d.get("prompt_eval_count", 0),
                  "completion_tokens": d.get("eval_count", 0),
                  "total_tokens": d.get("prompt_eval_count", 0) + d.get("eval_count", 0)},
        "_ollama_raw_done": d.get("done"),
    }


def _salvar(caminho_pedido, modelo_escolhido, resposta, conteudo, duracao_s, extra=None):
    os.makedirs(DESTINO_DIR, exist_ok=True)
    uso = resposta.get("usage") or {}
    te = int(uso.get("prompt_tokens", 0) or 0)
    ts = int(uso.get("completion_tokens", 0) or 0)
    modelo_usado = resposta.get("model") or modelo_escolhido
    agora = datetime.now(timezone.utc).astimezone()
    slug = re.sub(r"[^A-Za-z0-9._-]", "_", str(modelo_usado))
    destino = os.path.join(DESTINO_DIR, agora.strftime("%Y%m%d-%H%M%S") + f"-{slug}.json")
    registro = {
        "data": agora.isoformat(), "via": "omniroute",
        "rotacao_escolheu": modelo_escolhido, "modelo": modelo_usado,
        # provider/familia SEMPRE do id do ROSTER (modelo_escolhido), não do
        # `model` cru da resposta (MEMÓRIAS (384)): a API devolve p.ex.
        # `ministral-8b-latest` sem o prefixo `mistral/`, e "mistral" não é
        # substring de "ministral" -> _familia/_provider davam "?" no registro.
        "provider": _provider_do_modelo(modelo_escolhido), "familia": _familia(modelo_escolhido),
        "duracao_s": duracao_s, "tokens_entrada": te, "tokens_saida": ts,
        "tokens_total": te + ts,
        "pedido_arquivo": os.path.abspath(caminho_pedido),
        "identidade": _checar_identidade(conteudo, resposta),
        "resposta_crua": resposta,
    }
    if extra:
        registro.update(extra)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)
    return destino, registro


def main():
    if len(sys.argv) != 2:
        print(f"uso: {sys.argv[0]} <arquivo-com-o-pedido.txt>", file=sys.stderr)
        return 2

    caminho_pedido = sys.argv[1]
    with open(caminho_pedido, encoding="utf-8") as f:
        pedido_texto = f.read()

    achado_privado = checar_conteudo_privado(pedido_texto)
    if achado_privado:
        print(f"ABORTADO: o pedido menciona '{achado_privado}' -- conteúdo da camada privada (memoria/missoes/) nunca sai daqui. Remova a referência e tente de novo.")
        return 1
    if len(pedido_texto) > TETO_CHARS_PEDIDO:
        print(f"ABORTADO: pedido tem {len(pedido_texto)} caracteres, acima do teto de {TETO_CHARS_PEDIDO}. Confira o texto antes de mandar.")
        return 1

    # --- rotação com circuit breaker + portão de resposta (MEMÓRIAS (374)) ---
    tentados = []
    for _ in range(len(ROSTER)):
        modelo = escolher_modelo()
        if modelo is None or modelo in tentados:
            break
        tentados.append(modelo)
        print(f"Rotação: {modelo} (família {_familia(modelo)})")
        inicio = time.time()
        try:
            resposta = enviar_omniroute(pedido_texto, modelo)
        except urllib.error.HTTPError as e:
            corpo = e.read().decode("utf-8", errors="replace")
            if e.code == 422 and "secret_blocked_before_egress" in corpo:
                print(f"ABORTADO: o proxy de sanitização (P1-02) bloqueou -- padrão de segredo no texto. Nada enviado. {corpo[:300]}")
                return 1
            espera = _registrar_falha(modelo)
            print(f"  falha: HTTP {e.code} -- cooldown {espera}s. {corpo[:180]}")
            continue
        except (ConnectionRefusedError, urllib.error.URLError) as e:
            print(f"ABORTADO: o proxy de sanitização não responde em {SANITIZADOR_ENDPOINT} ({type(e).__name__}). Suba: `systemctl --user start omniroute-sanitizer omniroute`. Nada enviado.")
            return 1
        except Exception as e:  # noqa: BLE001
            espera = _registrar_falha(modelo)
            print(f"  falha: {type(e).__name__}: {e} -- cooldown {espera}s")
            continue

        duracao_s = round(time.time() - inicio, 1)
        conteudo, te, ts, tt = _normalizar(resposta)
        ok, motivo = _portao_resposta(resposta, conteudo)
        if not ok:
            espera = _registrar_falha(modelo)
            print(f"  rejeitada no portão: {motivo} -- cooldown {espera}s")
            continue

        _registrar_sucesso(modelo)
        destino, reg = _salvar(caminho_pedido, modelo, resposta, conteudo, duracao_s)
        print(f"Guardado: {destino}")
        print(f"Tokens: {te}+{ts}={tt}. Duração {duracao_s}s.")
        if reg["identidade"]["suspeita"]:
            print(f"IDENTIDADE SUSPEITA: a resposta assina '{reg['identidade']['assinou']}' mas o modelo é '{reg['identidade']['real']}' (catálogo de falhas). NÃO bloqueado -- o Humano decide.")
        faltando = checar_formato_parecer(conteudo)
        if faltando:
            print(f"FORA DO FORMATO: faltam {', '.join(faltando)} (Origem / Posição / Fundamentação / Emenda). REGRAS manda devolver o pedido UMA vez -- decisão do Humano.")
            return 1
        print("Formato OK (as 4 partes apareceram). Conteúdo NÃO avaliado -- leia o arquivo salvo.")
        return 0

    # --- fallback local: roster remoto inteiro fora/rejeitado ---
    print("\n" + "=" * 64)
    print("ROSTER REMOTO INTEIRO INDISPONÍVEL -- caindo pro modelo LOCAL.")
    print(f"Tentados: {', '.join(tentados) or '(nenhum -- tudo em cooldown)'}")
    print("O que vier abaixo NÃO é segunda opinião de família independente na")
    print("nuvem -- é o modelo local. Vale menos pro requisito de REGRAS.")
    print("=" * 64)
    inicio = time.time()
    try:
        resposta = _chamar_local(pedido_texto)
    except Exception as e:  # noqa: BLE001
        print(f"ABORTADO: o fallback local também falhou -- {type(e).__name__}: {e}. Ollama no ar? (`curl localhost:11434/api/tags`)")
        return 1
    duracao_s = round(time.time() - inicio, 1)
    conteudo, te, ts, tt = _normalizar(resposta)
    ok, motivo = _portao_resposta(resposta, conteudo)
    destino, _ = _salvar(caminho_pedido, FALLBACK_MODELO, resposta, conteudo, duracao_s,
                         extra={"fallback_local": True, "portao_ok": ok,
                                "portao_motivo": motivo, "tentados_remoto": tentados})
    print(f"Guardado (FALLBACK LOCAL): {destino}")
    print(f"Tokens: {te}+{ts}={tt}. Duração {duracao_s}s.")
    if not ok:
        print(f"  atenção: o fallback local também não passou no portão: {motivo}")
    faltando = checar_formato_parecer(conteudo)
    if faltando:
        print(f"FORA DO FORMATO (local): faltam {', '.join(faltando)}.")
    return 3   # respondeu, mas foi fallback local degradado -- código distinto


if __name__ == "__main__":
    sys.exit(main())
