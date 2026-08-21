#!/usr/bin/env bash
# Lê uma página sem navegador -- item do documento do Humano, 20/08/2026.
# "Antes de acrescentar ferramenta, esgote o que já se alcança com o que
# existe. Ferramenta nova é decisão, não conserto." (PROJETO.md, ACB)
#
# Só leitura: não envia formulário, não clica, não executa nada do que
# baixou. Sempre diz QUAL dos 4 casos resolveu. NUNCA relata "casca
# vazia" como "o site não tem conteúdo" -- são coisas diferentes.
#
# Conserto 21/08/2026 (autorizado pelo Humano, MEMÓRIAS (232)): checagem
# de HTTP antes de extrair (página de erro nunca é conteúdo -- caso
# medido: URL morta no S3 devolvendo "404 Not Found" que o CASO 1 velho
# tratava como conteúdo real); CASO 3 rebaixado de conclusão pra
# suspeita, sempre reportando junto qualquer URL de API achada no mesmo
# pacote (caso medido: erros internos do Angular/React/Vue são frases
# longas sem sintaxe de código -- a heurística velha não distinguia
# isso de conteúdo); filtro de idioma quando o HTML declara `lang`.
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

# 1. HTML cru + código HTTP -- checagem obrigatória ANTES de qualquer
# extração. Página de erro (404 etc.) nunca é conteúdo.
HTTP_CODE=$(curl -sSL -A "$UA" -o "$TMP/pg.html" -w "%{http_code}" "$URL")
CURL_RC=$?
if [ $CURL_RC -ne 0 ]; then
  echo "lacuna: não consegui baixar $URL (rede ou URL inválida, curl saiu com código $CURL_RC)"
  exit 1
fi
case "$HTTP_CODE" in
  2[0-9][0-9]) ;;
  *)
    echo "abortado: HTTP $HTTP_CODE em $URL -- página de erro nunca é conteúdo, nenhuma extração foi tentada."
    exit 4
    ;;
esac

# 1b. Idioma declarado no HTML, pra guiar a extração (recomendado, não
# obrigatório). Sem `lang`, reporta a ausência em vez de calar.
LANG_ATTR=$(grep -ioE '<html[^>]*\blang="?[a-zA-Z-]*"?' "$TMP/pg.html" | head -1)
LANG_PT=0
if echo "$LANG_ATTR" | grep -qiE 'lang="?pt(-br)?"?'; then
  LANG_PT=1
  echo "idioma declarado no HTML: pt -- priorizando trechos em português na extração." >&2
else
  echo "idioma não declarado no HTML (sem atributo lang reconhecido) -- filtro de idioma NÃO aplicado." >&2
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
      # espaço -- descarta source code minificado, fica com frase. Isto
      # NÃO distingue conteúdo real de mensagem de erro de framework
      # (Angular/React/Vue) -- ver rebaixamento pra SUSPEITA abaixo.
      STRINGS_LONGAS=$(grep -oE '"[^"\\]{40,}"' "$TMP/pacote.js" 2>/dev/null \
        | grep -avE '[(){};=$<>]' \
        | grep -aE '([[:alpha:]]{2,}[[:space:]]+){3,}[[:alpha:]]{2,}')
      if [ -n "$STRINGS_LONGAS" ]; then
        TEXTO_PACOTE="${TEXTO_PACOTE}${STRINGS_LONGAS}
"
      fi
      # Procura chamada de API no pacote, sem chamar -- SEMPRE reportada
      # junto do texto achado, nunca escolhida em vez dele.
      APIS=$(grep -oE '"(https?://[a-zA-Z0-9.\-]+)?/[a-zA-Z0-9_/.\-]*api[a-zA-Z0-9_/.\-]*"' "$TMP/pacote.js" 2>/dev/null | sort -u | head -5)
      [ -n "$APIS" ] && ENDERECOS_API="${ENDERECOS_API}${APIS}
"
    fi
  done <<< "$PACOTES"
  ENDERECOS_API=$(echo "$ENDERECOS_API" | sort -u | sed '/^$/d')

  if [ "$(echo "$TEXTO_PACOTE" | tr -d '[:space:]' | wc -c)" -ge 100 ]; then
    if [ "$LANG_PT" -eq 1 ]; then
      TEXTO_PACOTE=$(echo "$TEXTO_PACOTE" | python3 -c "
import sys
linhas = [l for l in sys.stdin.read().split(chr(10)) if l.strip()]
acentos = set('áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ')
comuns = (' de ', ' para ', ' com ', ' não ', ' que ', ' você ', ' está ', ' são ', ' uma ', ' pelo ', ' pela ')
def eh_pt(l):
    return any(c in acentos for c in l) or any(p in l.lower() for p in comuns)
pt = [l for l in linhas if eh_pt(l)]
resto = [l for l in linhas if not eh_pt(l)]
print(chr(10).join(pt + resto))
")
    fi
    echo "SUSPEITA (possível conteúdo, com ruído de framework provável -- cadeia longa sem sintaxe de código, não é conclusão. Mensagens de erro do Angular/React/Vue têm a mesma forma que conteúdo real e não são distinguidas por esta heurística; revisão humana recomendada):"
    if [ "$LANG_PT" -eq 1 ]; then
      echo "(idioma pt detectado -- trechos com acentuação/palavras comuns em português priorizados no topo)"
    fi
    echo "$TEXTO_PACOTE"
    echo
    if [ -n "$ENDERECOS_API" ]; then
      echo "Endereço(s) de API encontrado(s) no mesmo pacote, NÃO CHAMADO(S) -- mostrado lado a lado com o texto acima, não em vez dele:"
      echo "$ENDERECOS_API"
    else
      echo "Nenhum endereço de API encontrado no mesmo pacote."
    fi
    exit 0
  fi

  # Texto no pacote insuficiente -- reporta endereço de API achado, sem chamar.
  if [ -n "$ENDERECOS_API" ]; then
    echo "CASO 4 (pacote JS não tem texto suficiente -- provavelmente vem de API em tempo de execução). Endereço(s) de API encontrado(s) no pacote, NÃO CHAMADO(S):"
    echo "$ENDERECOS_API"
    exit 0
  fi
fi

# 5. Nenhum dos casos serviu.
echo "lacuna: conteúdo não está no HTML nem no pacote -- provavelmente vem de API em tempo de execução, e nenhuma chamada óbvia foi encontrada pra reportar. Ler isto exigiria navegador de verdade -- decisão do Humano, não conserto automático."
exit 3
