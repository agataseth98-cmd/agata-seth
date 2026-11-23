#!/usr/bin/env bash
# P-23 -- toda porta de entrada de modelo traz as diretrizes comuns da Agata
# (MEMÓRIAS (667)): modo conciso como padrão e economia de tokens permanente -- e, desde (849), a memória
# comum do Conselho (cache_conselho) -- ou importa o AGENTS.md, que as traz.
# Lista em config/portas-de-entrada.txt (coluna 3, leitura: arquivo | doutrina).
# AVISA, nunca falha: é cobertura de instrução, não segurança. Fecha a classe "plataforma nova
# entra sem diretriz" (o AGENTS.md da raiz não existia: Codex/Gemini/Cursor entrariam soltos).
#
# 23/11/2026 (caminho-visao-23-11): a leitura 'doutrina' (o gateway seth_gateway.py) confere o TEXTO QUE O MÓDULO
# MONTA (doutrina_montada(): seção SETH-GATEWAY do PROTOCOLOS.md + AGENTS.md), não o arquivo do módulo. Conferir o
# arquivo dava AVISO falso (a frase 'economia de tokens' não está no .py) e OK falso ('modo conciso' só estava
# num comentário). O módulo é importado sem rodar o __main__ (o gateway sobe o servidor quando roda como script).

# Carrega o módulo $1 sem executar o __main__ e imprime doutrina_montada(). Vazio se não der.
_p23_texto_montado() {
  python3 - "$1" <<'PY' 2>/dev/null
import importlib.util, os, sys
caminho = os.path.abspath(sys.argv[1])
sys.path.insert(0, os.path.dirname(caminho))
spec = importlib.util.spec_from_file_location("porta_p23", caminho)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.stdout.buffer.write(mod.doutrina_montada().encode("utf-8"))
PY
}

p23_portas_entrada() {
  local lista="config/portas-de-entrada.txt" caminho quem leitura texto onde faltam
  [ -f "$lista" ] || { echo "AVISO (P-23): $lista não existe -- ninguém confere as portas de entrada."; return 0; }
  while IFS='|' read -r caminho quem leitura; do
    case "$caminho" in \#*|"") continue ;; esac
    leitura="${leitura//[[:space:]]/}"
    [ -n "$leitura" ] || leitura=arquivo
    if [ ! -f "$caminho" ]; then
      echo "AVISO (P-23): porta de entrada '$caminho' ($quem) declarada mas o arquivo não existe."
      continue
    fi
    case "$leitura" in
      arquivo)
        if grep -q '^@AGENTS\.md' "$caminho"; then
          echo "OK (P-23): '$caminho' ($quem) importa o AGENTS.md."
          continue
        fi
        texto="$(cat "$caminho")"
        onde="no arquivo" ;;
      doutrina)
        texto="$(_p23_texto_montado "$caminho")"
        if [ -z "$texto" ]; then
          echo "AVISO (P-23): '$caminho' ($quem) não dá para conferir: doutrina_montada() não existe ou falhou ao rodar. O que fazer: o módulo precisa expor doutrina_montada() com o texto que ele põe antes do modelo."
          continue
        fi
        onde="no texto que o módulo monta" ;;
      *)
        echo "AVISO (P-23): '$caminho' ($quem) tem leitura '$leitura' desconhecida (use arquivo ou doutrina)."
        continue ;;
    esac
    faltam=""
    grep -qi 'modo conciso' <<<"$texto" || faltam="modo conciso"
    grep -qi 'economia de tokens' <<<"$texto" || faltam="${faltam:+$faltam e }economia de tokens"
    # (26/10/2026, (849)) "todo modelo aberto em ~/agata usa as mesmas regras e as mesmas ferramentas":
    # a porta tem de levar também à memória comum do Conselho
    grep -q 'cache_conselho' <<<"$texto" || faltam="${faltam:+$faltam e }a memória comum (cache_conselho)"
    if [ -n "$faltam" ]; then
      echo "AVISO (P-23): '$caminho' ($quem) não traz $faltam $onde. Por que importa: o modelo que entra por ali segue sem as diretrizes comuns (MEMÓRIAS (667)). O que fazer: acrescentar a linha das diretrizes ou '@AGENTS.md'."
    else
      echo "OK (P-23): '$caminho' ($quem) traz modo conciso, economia de tokens e a memória comum $onde."
    fi
  done < "$lista"
  return 0
}
