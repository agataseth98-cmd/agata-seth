#!/usr/bin/env bash
# Lê uma página sem navegador -- item do documento do Humano, 20/08/2026.
# "Antes de acrescentar ferramenta, esgote o que já se alcança com o que
# existe. Ferramenta nova é decisão, não conserto." (PROJETO.md, ACB)
#
# Só leitura: não envia formulário, não clica, não executa nada do que
# baixou. Sempre diz QUAL dos 4 casos resolveu. NUNCA relata "casca
# vazia" como "o site não tem conteúdo" -- são coisas diferentes.
#
# Uso: ler_pagina.sh <url>
set -uo pipefail

if [ $# -ne 1 ]; then
  echo "uso: $0 <url>" >&2
  exit 2
fi
URL="$1"
UA="Mozilla/5.0"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# 1. HTML cru.
if ! curl -sSL -A "$UA" "$URL" -o "$TMP/pg.html"; then
  echo "lacuna: não consegui baixar $URL (rede ou URL inválida)"
  exit 1
fi

# 2. Texto visível no HTML cru -- tira <script>/<style>/tags, mede o que sobra.
TEXTO_CRU=$(python3 -c "
import re, sys
html = open('$TMP/pg.html', encoding='utf-8', errors='replace').read()
html = re.sub(r'<script\b[^>]*>.*?</script>', ' ', html, flags=re.S | re.I)
html = re.sub(r'<style\b[^>]*>.*?</style>', ' ', html, flags=re.S | re.I)
texto = re.sub(r'<[^>]+>', ' ', html)
texto = re.sub(r'\s+', ' ', texto).strip()
print(texto)
")
if [ "${#TEXTO_CRU}" -ge 200 ]; then
  echo "CASO 1 (HTML cru tinha o texto):"
  echo "$TEXTO_CRU"
  exit 0
fi

# 3. Casca vazia -- acha o(s) pacote(s) .js referenciado(s), baixa, extrai strings longas.
echo "casca vazia no HTML cru (${#TEXTO_CRU} caracteres de texto visível) -- isto NÃO significa que o site não tem conteúdo, só que ele não vem no HTML. Procurando pacote JS..." >&2

ORIGEM=$(python3 -c "from urllib.parse import urlsplit; u=urlsplit('$URL'); print(f'{u.scheme}://{u.netloc}')")
PACOTES=$(grep -oE 'src="[^"]+\.js"' "$TMP/pg.html" | sed -E 's/^src="//; s/"$//' | sort -u)

if [ -n "$PACOTES" ]; then
  TEXTO_PACOTE=""
  ENDERECOS_API=""
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    case "$p" in
      http://*|https://*) URL_JS="$p" ;;
      /*) URL_JS="${ORIGEM}${p}" ;;
      *) URL_JS="${ORIGEM}/${p}" ;;
    esac
    if curl -sSL -A "$UA" "$URL_JS" -o "$TMP/pacote.js" 2>/dev/null; then
      # Heurística: cadeia longa, sem caractere de sintaxe de código
      # ({}();=$), com pelo menos 4 palavras de 2+ letras separadas por
      # espaço -- descarta source code minificado, fica com frase.
      STRINGS_LONGAS=$(grep -oE '"[^"\\]{40,}"' "$TMP/pacote.js" 2>/dev/null \
        | grep -avE '[(){};=$<>]' \
        | grep -aE '([[:alpha:]]{2,}[[:space:]]+){3,}[[:alpha:]]{2,}')
      if [ -n "$STRINGS_LONGAS" ]; then
        TEXTO_PACOTE="${TEXTO_PACOTE}${STRINGS_LONGAS}
"
      fi
      # 4. Procura chamada de API no pacote, sem chamar -- guarda pra reportar
      # se o passo 3 não render texto suficiente.
      APIS=$(grep -oE '"(https?://[a-zA-Z0-9.\-]+)?/[a-zA-Z0-9_/.\-]*api[a-zA-Z0-9_/.\-]*"' "$TMP/pacote.js" 2>/dev/null | sort -u | head -5)
      [ -n "$APIS" ] && ENDERECOS_API="${ENDERECOS_API}${APIS}
"
    fi
  done <<< "$PACOTES"

  if [ "$(echo "$TEXTO_PACOTE" | tr -d '[:space:]' | wc -c)" -ge 100 ]; then
    echo "CASO 3 (texto estava embutido no pacote JS):"
    echo "$TEXTO_PACOTE"
    exit 0
  fi

  # 4. Nada de texto no pacote -- reporta endereço de API achado, sem chamar.
  if [ -n "$ENDERECOS_API" ]; then
    echo "CASO 4 (pacote JS não tem o texto -- provavelmente vem de API em tempo de execução). Endereço(s) de API encontrado(s) no pacote, NÃO CHAMADO(S):"
    echo "$ENDERECOS_API" | sort -u
    exit 0
  fi
fi

# 5. Nenhum dos casos serviu.
echo "lacuna: conteúdo não está no HTML nem no pacote -- provavelmente vem de API em tempo de execução, e nenhuma chamada óbvia foi encontrada pra reportar. Ler isto exigiria navegador de verdade -- decisão do Humano, não conserto automático."
exit 3
