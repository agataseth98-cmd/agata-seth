#!/usr/bin/env python3
"""Coletor do Conselho Remoto -- Fase 1 (MEMÓRIAS (206)/(207)).

UM modelo (GLM-4.7-Flash, Zhipu), UMA tarefa: enviar um pedido de parecer
ja escrito pelo Humano a UM modelo remoto, guardar a resposta crua. Nada
alem disso -- ver REGRAS "Segunda opiniao" e PROJETO "Conselho Remoto".

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
DESTINO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memoria", "missoes", "conselho-remoto",
)

# Tetos, primeiro corte -- ajustavel pelo Humano, nao um numero canonizado.
# Custo em US$ e 0 nesta camada (grátis, GLM-4.7-Flash) -- a formula fica
# pronta pra quando não for.
TETO_CHARS_PEDIDO = 60_000   # heurística pré-envio -- não há tokenizador local
TETO_TOKENS_SAIDA = 8_000    # vira max_tokens no pedido -- teto mecânico, não só aviso
PRECO_ENTRADA_POR_TOKEN_USD = 0.0
PRECO_SAIDA_POR_TOKEN_USD = 0.0

# Condição 1 (MEMÓRIAS (206)): só material já no repositório PÚBLICO pode
# sair daqui. memoria/missoes/ é a camada privada, local, sem remote por
# desenho (PROJETO, "Memória e hidratação") -- nunca deve aparecer no
# texto de um pedido que vai pra fora. Checagem mecânica, generosa nas
# variações de caminho, travando o envio se achar.
PADRAO_CONTEUDO_PRIVADO = re.compile(r"memoria[/\\]missoes", re.IGNORECASE)

PARTES_PARECER = ["origem", "posição", "posicao", "fundamentação", "fundamentacao", "emenda"]


def carregar_chave():
    if not os.path.exists(ENV_PATH):
        return None
    with open(ENV_PATH, encoding="utf-8") as f:
        for linha in f:
            m = re.match(r"^ZHIPU_API_KEY=(.*)$", linha.strip())
            if m:
                valor = m.group(1).strip()
                return valor or None
    return None


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


def enviar(pedido_texto, chave):
    corpo = json.dumps({
        "model": MODELO,
        "messages": [{"role": "user", "content": pedido_texto}],
        "max_tokens": TETO_TOKENS_SAIDA,
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=corpo,
        method="POST",
        headers={
            "Authorization": f"Bearer {chave}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


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

    chave = carregar_chave()
    if not chave:
        print(f"ABORTADO: ZHIPU_API_KEY ausente em {ENV_PATH}. Nada foi enviado. Ver PROJETO, 'Conselho Remoto', ordem da chave (Condição 2).")
        return 1

    inicio = time.time()
    try:
        resposta = enviar(pedido_texto, chave)
    except urllib.error.HTTPError as e:
        corpo_erro = e.read().decode("utf-8", errors="replace")
        print(f"ABORTADO: chamada falhou, HTTP {e.code}. Corpo: {corpo_erro[:2000]}")
        return 1
    except Exception as e:
        print(f"ABORTADO: chamada falhou -- {type(e).__name__}: {e}")
        return 1
    duracao_s = round(time.time() - inicio, 1)

    conteudo = resposta.get("choices", [{}])[0].get("message", {}).get("content", "")
    uso = resposta.get("usage", {})
    tokens_entrada = uso.get("prompt_tokens", 0)
    tokens_saida = uso.get("completion_tokens", 0)
    tokens_total = uso.get("total_tokens", tokens_entrada + tokens_saida)
    custo_usd = round(
        tokens_entrada * PRECO_ENTRADA_POR_TOKEN_USD
        + tokens_saida * PRECO_SAIDA_POR_TOKEN_USD,
        6,
    )

    os.makedirs(DESTINO_DIR, exist_ok=True)
    agora = datetime.now(timezone.utc).astimezone()
    nome_arquivo = agora.strftime("%Y%m%d-%H%M%S") + f"-{MODELO}.json"
    destino = os.path.join(DESTINO_DIR, nome_arquivo)
    registro = {
        "data": agora.isoformat(),
        "modelo": MODELO,
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
