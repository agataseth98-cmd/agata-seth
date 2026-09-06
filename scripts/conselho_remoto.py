#!/usr/bin/env python3
"""Coletor do Conselho Remoto -- Fase 1 (MEMÓRIAS (206)/(207)).

UMA tarefa: enviar um pedido de parecer ja escrito pelo Humano a UM modelo
remoto, guardar a resposta crua. Nada alem disso -- ver REGRAS "Segunda
opiniao" e PROJETO "Conselho Remoto".

Desde P1-04 (branch redesign, 2026-09-02): a chamada externa vai pelo OmniRoute,
ATRAVES do proxy de sanitizacao em 127.0.0.1:20127 (P1-02). Este script NAO le
mais chave nenhuma e NAO faz backoff proprio: o circuit breaker e o cooldown
429 sao do OmniRoute.

ROTACAO JUSTA (06/09/2026, ordem do Humano: "ninguem tem papel fixo... revogo
GLM... deve ser decidido entre modelos gratuitos sob um regime de regras
justas de rotatividade"). Ate aqui a combo `conselho` era prioridade fixa
(GLM sempre primeiro). Agora este script escolhe, a cada chamada, o modelo
com MENOS usos bem-sucedidos entre o roster gratuito (ROSTER abaixo), envia
o pedido direto pro raw model id escolhido (nao mais pela combo), e conta o
uso em ROTACAO_ESTADO só se a chamada tiver sucesso. Continua **UMA chamada
externa por invocacao** (o invariante do script nao mudou) -- se a escolhida
falhar, o script ABORTA como sempre fazia; nao laca entre modelos sozinho.
Rodar de novo escolhe outro (o que falhou nao teve uso contado, entao ainda
compete pela vez -- nao criei penalidade por falha, so recompensa por
sucesso, pra nao afundar um modelo bom que teve 1 erro de rede).

O QUE NAO MUDOU (a razao do script existir):
  - so material do repo PUBLICO sai: checar_conteudo_privado trava memoria/missoes
  - teto de tamanho do pedido (heuristica pre-envio)
  - UMA chamada externa por invocacao -- sem laco, sem encadear
  - os provedores externos esgotaram -> ABORTA. Cair pro modelo local segue
    sendo decisao do Humano caso a caso (MEMÓRIAS (276)).
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

# Roster da rotação justa -- só modelos com free tier CONFIRMADO. Groq
# (`groq/openai/gpt-oss-120b`) entrou em 06/09/2026 depois de confirmar de
# verdade (WebSearch, não memória de treino): free tier real, sem cartão, 30
# req/min, 14.400 req/dia, cobre todos os modelos incl. gpt-oss-120b -- fontes
# em MEMÓRIAS (353). Ordem = desempate quando dois modelos têm a mesma
# contagem (determinístico, não aleatório -- auditável).
ROSTER = [
    "zai/glm-4.7-flash",
    "gemini/gemini-2.5-flash",
    "openrouter/minimax/minimax-m3:free",
    "groq/openai/gpt-oss-120b",
]
ROTACAO_ESTADO = os.path.join(DESTINO_DIR, "rotacao-estado.json")


def _carregar_rotacao():
    """Contagem de usos BEM-SUCEDIDOS por modelo do ROSTER. Modelo novo no
    ROSTER que nunca apareceu no arquivo entra com 0 -- nunca levanta."""
    estado = {}
    if os.path.isfile(ROTACAO_ESTADO):
        try:
            with open(ROTACAO_ESTADO, encoding="utf-8") as f:
                estado = json.load(f)
        except Exception:  # noqa: BLE001 -- arquivo corrompido não trava a escolha
            estado = {}
    return {m: int(estado.get(m, 0)) for m in ROSTER}


def escolher_modelo():
    """Menos usado primeiro; empate quebrado pela ordem fixa do ROSTER
    (determinístico -- a mesma contagem sempre escolhe o mesmo, auditável)."""
    estado = _carregar_rotacao()
    return min(ROSTER, key=lambda m: (estado[m], ROSTER.index(m)))


def _registrar_sucesso(modelo_escolhido):
    """Só chamada depois de confirmar sucesso -- falha não penaliza."""
    estado = _carregar_rotacao()
    if modelo_escolhido in estado:
        estado[modelo_escolhido] += 1
    os.makedirs(DESTINO_DIR, exist_ok=True)
    with open(ROTACAO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)

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


def enviar_omniroute(pedido_texto, modelo):
    """UMA chamada. POST no proxy de sanitizacao, que scrub-a o pedido e repassa
    ao OmniRoute pro `modelo` raw escolhido pela rotação (não mais uma combo
    de prioridade fixa). Devolve o JSON cru (shape OpenAI-compat)."""
    payload = {
        "model": modelo,
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


def _provider_do_modelo(modelo):
    """Emenda 2 (Cadeia de auditoria, Camada B). A resposta do OmniRoute so traz
    `model` (ex.: 'gemini-2.5-flash'), sem `provider`. Deriva o provedor do nome
    para o registro -- best-effort; a `resposta_crua` continua sendo a fonte."""
    m = (modelo or "").lower()
    for chave, prov in (("glm", "zai"), ("gemini", "gemini"), ("gpt-oss", "groq/cerebras"),
                        ("qwen", "local?"), ("llama", "local?"), ("minimax", "openrouter")):
        if chave in m:
            return prov
    return "?"


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

    modelo_escolhido = escolher_modelo()
    print(f"Rotação escolheu: {modelo_escolhido} (menos usos bem-sucedidos no roster)")

    inicio = time.time()
    try:
        resposta = enviar_omniroute(pedido_texto, modelo_escolhido)
    except urllib.error.HTTPError as e:
        corpo_erro = e.read().decode("utf-8", errors="replace")
        if e.code == 422 and "secret_blocked_before_egress" in corpo_erro:
            print(f"ABORTADO: o proxy de sanitização (P1-02) bloqueou o pedido -- há um padrão de segredo no texto. Nada foi enviado. Detalhe: {corpo_erro[:400]}")
            return 1
        print(f"ABORTADO: OmniRoute retornou HTTP {e.code}: {corpo_erro[:500]}. Nada foi guardado -- cair pro modelo local é decisão do Humano (ver (276)).")
        return 1
    except (ConnectionRefusedError, urllib.error.URLError) as e:
        # Emenda 3 (Cadeia de auditoria, Camada B): mensagem clara quando o proxy
        # de sanitizacao nao responde (causa mais comum: servico P1-02 parado).
        print(f"ABORTADO: o proxy de sanitização não responde em {SANITIZADOR_ENDPOINT} ({type(e).__name__}). Suba o serviço P1-02: `systemctl --user start omniroute-sanitizer omniroute`. Nada foi enviado. Cair pro modelo local é decisão do Humano (276).")
        return 1
    except Exception as e:  # noqa: BLE001 -- qualquer falha de rede/gateway aborta igual
        print(f"ABORTADO: falha ao falar com o OmniRoute ({SANITIZADOR_ENDPOINT}) -- {type(e).__name__}: {e}. O gateway está no ar? (`systemctl --user status omniroute-sanitizer omniroute`). Cair pro modelo local é decisão do Humano (276).")
        return 1

    duracao_s = round(time.time() - inicio, 1)
    conteudo, tokens_entrada, tokens_saida, tokens_total = _normalizar(resposta)
    modelo_usado = resposta.get("model") or modelo_escolhido
    _registrar_sucesso(modelo_escolhido)  # só chega aqui se enviar_omniroute não levantou
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
        "rotacao_escolheu": modelo_escolhido,
        "modelo": modelo_usado,
        "provider": _provider_do_modelo(modelo_usado),
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
