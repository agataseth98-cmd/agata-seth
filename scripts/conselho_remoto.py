#!/usr/bin/env python3
"""Coletor do Conselho Remoto -- Fase 1 (MEMÓRIAS (206)/(207)).

UMA tarefa: enviar um pedido de parecer ja escrito pelo Humano a UM modelo
remoto, guardar a resposta crua. Nada alem disso -- ver REGRAS "Segunda
opiniao" e PROJETO "Conselho Remoto".

Desde P1-04 (branch redesign, 2026-09-02): a chamada externa vai pelo OmniRoute
-- combo `conselho` (glm-4.7-flash -> gemini-2.5-flash) -- ATRAVES do proxy de
sanitizacao em 127.0.0.1:20127 (P1-02). Este script NAO le mais chave nenhuma
e NAO faz backoff proprio: o fallback GLM->Gemini, o circuit breaker e o
cooldown 429 sao todos do OmniRoute agora.

O QUE NAO MUDOU (a razao do script existir):
  - so material do repo PUBLICO sai: checar_conteudo_privado trava memoria/missoes
  - teto de tamanho do pedido (heuristica pre-envio)
  - UMA chamada externa por invocacao -- sem laco, sem encadear
  - os provedores externos esgotaram -> ABORTA. Cair pro modelo local segue
    sendo decisao do Humano caso a caso (MEMÓRIAS (276)).
  - nao escreve MEMORIAS/PROJETO/REGRAS; nao interpreta, resume nem julga
  - guarda a resposta crua; so relata "fora do formato" quando aplicavel

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
COMBO = "conselho"   # combo do OmniRoute: glm-4.7-flash -> gemini-2.5-flash

DESTINO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memoria", "missoes", "conselho-remoto",
)

# Tetos, primeiro corte -- ajustavel pelo Humano, nao um numero canonizado.
TETO_CHARS_PEDIDO = 60_000   # heuristica pre-envio -- nao ha tokenizador local
TETO_TOKENS_SAIDA = 4_000    # vira max_tokens no pedido -- teto mecanico

# Achado real na primeira invocacao (MEMÓRIAS (212)): com "thinking" habilitado
# o GLM-4.7-Flash gastou os tokens de saida inteiros tentando calcular um hash
# de cabeca, em loop, e nunca produziu o parecer. Pedimos para desligar; o
# OmniRoute repassa se o provedor aceitar. Se o loop voltar apesar disso, e
# follow-up de P1-04 (config no lado do OmniRoute).
DESABILITAR_THINKING = True
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


def enviar_omniroute(pedido_texto):
    """UMA chamada. POST no proxy de sanitizacao, que scrub-a o pedido e repassa
    ao OmniRoute na combo `conselho`. Devolve o JSON cru (shape OpenAI-compat)."""
    payload = {
        "model": COMBO,
        "messages": [{"role": "user", "content": pedido_texto}],
        "max_tokens": TETO_TOKENS_SAIDA,
    }
    if DESABILITAR_THINKING:
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

    inicio = time.time()
    try:
        resposta = enviar_omniroute(pedido_texto)
    except urllib.error.HTTPError as e:
        corpo_erro = e.read().decode("utf-8", errors="replace")
        if e.code == 422 and "secret_blocked_before_egress" in corpo_erro:
            print(f"ABORTADO: o proxy de sanitização (P1-02) bloqueou o pedido -- há um padrão de segredo no texto. Nada foi enviado. Detalhe: {corpo_erro[:400]}")
            return 1
        print(f"ABORTADO: OmniRoute retornou HTTP {e.code}: {corpo_erro[:500]}. Nada foi guardado -- cair pro modelo local é decisão do Humano (ver (276)).")
        return 1
    except Exception as e:  # noqa: BLE001 -- qualquer falha de rede/gateway aborta igual
        print(f"ABORTADO: falha ao falar com o OmniRoute ({SANITIZADOR_ENDPOINT}) -- {type(e).__name__}: {e}. O gateway está no ar? (`systemctl --user status omniroute-sanitizer omniroute`). Cair pro modelo local é decisão do Humano (276).")
        return 1

    duracao_s = round(time.time() - inicio, 1)
    conteudo, tokens_entrada, tokens_saida, tokens_total = _normalizar(resposta)
    modelo_usado = resposta.get("model") or COMBO
    custo_usd = round(
        tokens_entrada * PRECO_ENTRADA_POR_TOKEN_USD
        + tokens_saida * PRECO_SAIDA_POR_TOKEN_USD,
        6,
    )

    os.makedirs(DESTINO_DIR, exist_ok=True)
    agora = datetime.now(timezone.utc).astimezone()
    modelo_slug = re.sub(r"[^A-Za-z0-9._-]", "_", str(modelo_usado))
    nome_arquivo = agora.strftime("%Y%m%d-%H%M%S") + f"-{modelo_slug}.json"
    destino = os.path.join(DESTINO_DIR, nome_arquivo)
    registro = {
        "data": agora.isoformat(),
        "via": "omniroute",
        "combo": COMBO,
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
    print(f"Tokens: {tokens_entrada} entrada + {tokens_saida} saída = {tokens_total} total. Custo: US${custo_usd}. (custo real do gateway: `omniroute cost`)")

    faltando = checar_formato_parecer(conteudo)
    if faltando:
        print(f"FORA DO FORMATO: faltam {', '.join(faltando)} (Origem / Posição / Fundamentação / Emenda). REGRAS manda devolver o pedido UMA vez, com o formato junto -- decisão de reenviar é do Humano, não deste script.")
        return 1

    print("Formato OK (as 4 partes apareceram). Conteúdo NÃO avaliado -- leia o arquivo salvo antes de qualquer coisa acontecer com ele.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
