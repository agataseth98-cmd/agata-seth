#!/usr/bin/env python3
"""Coletor do Conselho Remoto -- Fase 1 (MEMÓRIAS (206)/(207)).

UMA tarefa: enviar um pedido de parecer ja escrito pelo Humano a UM modelo
remoto, guardar a resposta crua. Nada alem disso -- ver REGRAS "Segunda
opiniao" e PROJETO "Conselho Remoto".

Provedor: GLM-4.7-Flash (Zhipu) por padrao. GLM indisponivel (backoff
ativo, ou 429/5xx nesta chamada) -> tenta gemini-2.5-flash (Google) UMA
vez como fallback (MEMÓRIAS (287)). Os dois externos falharam -> ABORTA;
cair pro modelo local segue sendo decisao do Humano caso a caso (276).
Uma unica chamada externa por invocacao -- nunca as duas de proposito.

O QUE ESTE SCRIPT NUNCA FAZ, por desenho (ordem do Humano):
  - nao escreve em MEMORIAS, PROJETO ou REGRAS
  - nao interpreta, resume nem julga a resposta
  - nao encadeia -- uma chamada por invocacao, sem laco
  - nao decide nada -- so relata "fora do formato" quando aplicavel

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

MODELO = "glm-4.7-flash"
ENDPOINT = "https://api.z.ai/api/paas/v4/chat/completions"
ENV_PATH = os.path.expanduser("~/.hermes/.env")

# Fallback do Conselho (ordem do Humano, 27/08/2026, MEMÓRIAS (287)):
# GLM indisponível (backoff ativo, ou 429/5xx nesta chamada) -> tenta Gemini
# uma vez. Os dois externos falharam -> ABORTA. Cair pro qwen local segue
# sendo decisão do Humano caso a caso, como na (276) -- o Conselho Remoto
# é sobre segunda opinião EXTERNA; automatizar a queda pro local mudaria o
# que ele é.
GEMINI_MODELO = "gemini-2.5-flash"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODELO}:generateContent"
)
# O free tier do Gemini (~20/dia) é COMPARTILHADO com o fallback do Hermes,
# e o circuit breaker gemini_quota_guard NÃO enxerga as chamadas deste
# script (processo separado). Contador local próprio, só aviso, não bloqueia.
GEMINI_CONTADOR_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memoria", "missoes", "conselho-remoto", ".gemini-contador.json",
)
GEMINI_AVISO_LIMIAR = 15
DESTINO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memoria", "missoes", "conselho-remoto",
)

# Tetos, primeiro corte -- ajustavel pelo Humano, nao um numero canonizado.
# Custo em US$ e 0 nesta camada (grátis, GLM-4.7-Flash) -- a formula fica
# pronta pra quando não for.
TETO_CHARS_PEDIDO = 60_000   # heurística pré-envio -- não há tokenizador local
TETO_TOKENS_SAIDA = 4_000    # vira max_tokens no pedido -- teto mecânico, não só aviso

# Achado real na primeira invocação (MEMÓRIAS (212)): com "thinking"
# habilitado (padrão do modelo), o GLM-4.7-Flash gastou os 8.000 tokens
# de saída inteiros tentando CALCULAR um hash SHA256 de cabeça, em loop
# repetitivo, e nunca produziu o parecer (`content` vazio, `finish_reason:
# length`). Desligado explicitamente -- confirmado no OpenAPI oficial
# (`docs.z.ai/api-reference/llm/chat-completion`) que o parâmetro existe.
DESABILITAR_THINKING = True
PRECO_ENTRADA_POR_TOKEN_USD = 0.0
PRECO_SAIDA_POR_TOKEN_USD = 0.0

# Condição 1 (MEMÓRIAS (206)): só material já no repositório PÚBLICO pode
# sair daqui. memoria/missoes/ é a camada privada, local, sem remote por
# desenho (PROJETO, "Memória e hidratação") -- nunca deve aparecer no
# texto de um pedido que vai pra fora. Checagem mecânica, generosa nas
# variações de caminho, travando o envio se achar.
PADRAO_CONTEUDO_PRIVADO = re.compile(r"memoria[/\\]missoes", re.IGNORECASE)

PARTES_PARECER = ["origem", "posição", "posicao", "fundamentação", "fundamentacao", "emenda"]

# Backoff de 429 (item 3, ordem do Humano 20/08/2026, sugestão do Marcos).
# Antes: uma retentativa (a segunda chamada era outra invocação manual do
# script) e desiste, sem memória entre invocações -- nada impedia uma
# terceira, quarta... tentativa em sequência no mesmo minuto. Passa a:
# duas falhas 429 SEGUIDAS (entre invocações, não dentro de uma) travam
# nova chamada por 15 min, e a espera fica registrada em log -- protege a
# conta de parecer abusiva pro provedor. Estado persiste em arquivo na
# camada privada (memoria/missoes/, sem remote, gitignorada do repo
# principal) porque o script não mantém processo vivo entre chamadas.
BACKOFF_ESTADO_PATH = os.path.join(DESTINO_DIR, ".backoff-estado.json")
BACKOFF_LOG_PATH = os.path.join(DESTINO_DIR, "backoff.log")
BACKOFF_LIMIAR_FALHAS_SEGUIDAS = 2
BACKOFF_ESPERA_S = 15 * 60


def _backoff_log(linha):
    os.makedirs(DESTINO_DIR, exist_ok=True)
    carimbo = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S")
    with open(BACKOFF_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{carimbo}] {linha}\n")


def _carregar_estado_backoff():
    if not os.path.exists(BACKOFF_ESTADO_PATH):
        return {"falhas_429_seguidas": 0, "ultima_falha_429": None}
    try:
        with open(BACKOFF_ESTADO_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"falhas_429_seguidas": 0, "ultima_falha_429": None}


def _salvar_estado_backoff(estado):
    os.makedirs(DESTINO_DIR, exist_ok=True)
    with open(BACKOFF_ESTADO_PATH, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def checar_backoff():
    """Retorna segundos restantes de espera (0 = pode chamar agora)."""
    estado = _carregar_estado_backoff()
    if estado.get("falhas_429_seguidas", 0) < BACKOFF_LIMIAR_FALHAS_SEGUIDAS:
        return 0
    ultima = estado.get("ultima_falha_429")
    if not ultima:
        return 0
    decorrido = (datetime.now(timezone.utc) - datetime.fromisoformat(ultima)).total_seconds()
    faltam = BACKOFF_ESPERA_S - decorrido
    return max(0, int(faltam))


def registrar_falha_429():
    estado = _carregar_estado_backoff()
    estado["falhas_429_seguidas"] = estado.get("falhas_429_seguidas", 0) + 1
    estado["ultima_falha_429"] = datetime.now(timezone.utc).isoformat()
    _salvar_estado_backoff(estado)
    if estado["falhas_429_seguidas"] >= BACKOFF_LIMIAR_FALHAS_SEGUIDAS:
        _backoff_log(
            f"BACKOFF ATIVADO: {estado['falhas_429_seguidas']} falhas 429 seguidas -- "
            f"próxima chamada liberada em {BACKOFF_ESPERA_S // 60} min."
        )


def registrar_chamada_sem_429():
    estado = _carregar_estado_backoff()
    if estado.get("falhas_429_seguidas", 0) > 0:
        _salvar_estado_backoff({"falhas_429_seguidas": 0, "ultima_falha_429": None})


def carregar_chave(nome="ZHIPU_API_KEY"):
    if not os.path.exists(ENV_PATH):
        return None
    padrao = re.compile(r"^" + re.escape(nome) + r"=(.*)$")
    with open(ENV_PATH, encoding="utf-8") as f:
        for linha in f:
            m = padrao.match(linha.strip())
            if m:
                valor = m.group(1).strip().strip('"').strip("'")
                return valor or None
    return None


def _gemini_contador_hoje():
    hoje = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    try:
        with open(GEMINI_CONTADOR_PATH, encoding="utf-8") as f:
            est = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        est = {}
    if est.get("data") != hoje:
        est = {"data": hoje, "chamadas": 0}
    return est


def _gemini_contador_incrementar():
    est = _gemini_contador_hoje()
    est["chamadas"] = est.get("chamadas", 0) + 1
    os.makedirs(os.path.dirname(GEMINI_CONTADOR_PATH), exist_ok=True)
    with open(GEMINI_CONTADOR_PATH, "w", encoding="utf-8") as f:
        json.dump(est, f, ensure_ascii=False, indent=2)
    return est["chamadas"]


def checar_conteudo_privado(texto):
    m = PADRAO_CONTEUDO_PRIVADO.search(texto)
    if m:
        return m.group(0)
    return None


def checar_formato_parecer(texto):
    """Confere se as 4 partes do parecer (REGRAS, 'Segunda opinião')
    aparecem, generoso o bastante pra aceitar variação de acento/caixa.
    Não julga o CONTEÚDO -- só a presença estrutural das 4 partes."""
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


def enviar_glm(pedido_texto, chave):
    payload = {
        "model": MODELO,
        "messages": [{"role": "user", "content": pedido_texto}],
        "max_tokens": TETO_TOKENS_SAIDA,
    }
    if DESABILITAR_THINKING:
        payload["thinking"] = {"type": "disabled"}
    corpo = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=corpo, method="POST",
        headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def enviar_gemini(pedido_texto, chave):
    payload = {
        "contents": [{"role": "user", "parts": [{"text": pedido_texto}]}],
        "generationConfig": {"maxOutputTokens": TETO_TOKENS_SAIDA},
    }
    corpo = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{GEMINI_ENDPOINT}?key={chave}", data=corpo, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _normalizar(provedor, resposta):
    """Devolve (conteudo, tokens_entrada, tokens_saida, tokens_total) do
    formato cru de cada provedor. Não julga nada."""
    if provedor == "gemini":
        cands = resposta.get("candidates", [{}])
        partes = cands[0].get("content", {}).get("parts", []) if cands else []
        conteudo = "".join(p.get("text", "") for p in partes)
        um = resposta.get("usageMetadata", {})
        te = um.get("promptTokenCount", 0)
        ts = um.get("candidatesTokenCount", 0)
        tt = um.get("totalTokenCount", te + ts)
        return conteudo, te, ts, tt
    # glm / openai-compatível
    conteudo = resposta.get("choices", [{}])[0].get("message", {}).get("content", "")
    uso = resposta.get("usage", {})
    te = uso.get("prompt_tokens", 0)
    ts = uso.get("completion_tokens", 0)
    tt = uso.get("total_tokens", te + ts)
    return conteudo, te, ts, tt


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

    chave_glm = carregar_chave("ZHIPU_API_KEY")
    chave_gemini = carregar_chave("GOOGLE_API_KEY")
    if not chave_glm and not chave_gemini:
        print(f"ABORTADO: nem ZHIPU_API_KEY nem GOOGLE_API_KEY em {ENV_PATH}. Nada foi enviado. Ver PROJETO, 'Conselho Remoto'.")
        return 1

    espera_restante = checar_backoff() if chave_glm else 0
    glm_pulavel = (not chave_glm) or espera_restante > 0
    if espera_restante > 0:
        minutos = espera_restante // 60 + (1 if espera_restante % 60 else 0)
        print(f"AVISO: GLM em backoff (~{minutos} min restantes) -- tentando Gemini como fallback.")
        _backoff_log(f"GLM em backoff ({espera_restante}s) -- fallback para Gemini.")

    provedor = modelo_usado = resposta = None
    erro_glm = None
    inicio = time.time()

    if not glm_pulavel:
        try:
            resposta = enviar_glm(pedido_texto, chave_glm)
            provedor, modelo_usado = "glm", MODELO
        except urllib.error.HTTPError as e:
            corpo_erro = e.read().decode("utf-8", errors="replace")
            if e.code == 429:
                registrar_falha_429()
            erro_glm = f"HTTP {e.code}: {corpo_erro[:500]}"
        except Exception as e:
            erro_glm = f"{type(e).__name__}: {e}"

    if resposta is None:
        if not chave_gemini:
            print(f"ABORTADO: GLM indisponível ({erro_glm or 'backoff'}) e GOOGLE_API_KEY ausente. Nada foi enviado.")
            return 1
        n_hoje = _gemini_contador_hoje().get("chamadas", 0)
        if n_hoje >= GEMINI_AVISO_LIMIAR:
            print(f"AVISO: {n_hoje} chamadas Gemini deste script hoje -- o teto free (~20/dia) é COMPARTILHADO com o fallback do Hermes e o gemini_quota_guard não enxerga estas. Seguindo mesmo assim.")
        inicio = time.time()
        try:
            resposta = enviar_gemini(pedido_texto, chave_gemini)
            provedor, modelo_usado = "gemini", GEMINI_MODELO
            usadas = _gemini_contador_incrementar()
            print(f"Gemini usado como fallback (chamada {usadas} do dia neste script).")
        except urllib.error.HTTPError as e:
            corpo_erro = e.read().decode("utf-8", errors="replace")
            print(f"ABORTADO: GLM indisponível ({erro_glm or 'backoff'}) E Gemini falhou HTTP {e.code}: {corpo_erro[:500]}. Nada foi enviado -- cair pro modelo local é decisão do Humano (ver (276)).")
            return 1
        except Exception as e:
            print(f"ABORTADO: GLM indisponível ({erro_glm or 'backoff'}) E Gemini falhou -- {type(e).__name__}: {e}. Nada foi enviado.")
            return 1

    duracao_s = round(time.time() - inicio, 1)
    if provedor == "glm":
        registrar_chamada_sem_429()

    conteudo, tokens_entrada, tokens_saida, tokens_total = _normalizar(provedor, resposta)
    custo_usd = round(
        tokens_entrada * PRECO_ENTRADA_POR_TOKEN_USD
        + tokens_saida * PRECO_SAIDA_POR_TOKEN_USD,
        6,
    )

    os.makedirs(DESTINO_DIR, exist_ok=True)
    agora = datetime.now(timezone.utc).astimezone()
    nome_arquivo = agora.strftime("%Y%m%d-%H%M%S") + f"-{modelo_usado}.json"
    destino = os.path.join(DESTINO_DIR, nome_arquivo)
    registro = {
        "data": agora.isoformat(),
        "provedor": provedor,
        "modelo": modelo_usado,
        "duracao_s": duracao_s,
        "tokens_entrada": tokens_entrada,
        "tokens_saida": tokens_saida,
        "tokens_total": tokens_total,
        "custo_usd": custo_usd,
        "pedido_arquivo": os.path.abspath(caminho_pedido),
        "resposta_crua": resposta,
    }
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)

    print(f"Guardado: {destino}")
    print(f"Tokens: {tokens_entrada} entrada + {tokens_saida} saída = {tokens_total} total. Custo: US${custo_usd}.")

    faltando = checar_formato_parecer(conteudo)
    if faltando:
        print(f"FORA DO FORMATO: faltam {', '.join(faltando)} (Origem / Posição / Fundamentação / Emenda). REGRAS manda devolver o pedido UMA vez, com o formato junto -- decisão de reenviar é do Humano, não deste script.")
        return 1

    print("Formato OK (as 4 partes apareceram). Conteúdo NÃO avaliado -- leia o arquivo salvo antes de qualquer coisa acontecer com ele.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
