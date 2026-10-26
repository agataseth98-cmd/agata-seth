#!/usr/bin/env bash
# P-23 -- toda porta de entrada de modelo traz as diretrizes comuns da Agata
# (MEMÓRIAS (667)): modo conciso como padrão e economia de tokens permanente -- e, desde (849), a memória
# comum do Conselho (cache_conselho) -- ou importa
# o AGENTS.md, que as traz. Lista em config/portas-de-entrada.txt. AVISA, nunca
# falha: é cobertura de instrução, não segurança. Fecha a classe "plataforma nova
# entra sem diretriz" (o AGENTS.md da raiz não existia: Codex/Gemini/Cursor
# entrariam soltos).

p23_portas_entrada() {
  local lista="config/portas-de-entrada.txt" caminho quem faltam
  [ -f "$lista" ] || { echo "AVISO (P-23): $lista não existe -- ninguém confere as portas de entrada."; return 0; }
  while IFS='|' read -r caminho quem; do
    case "$caminho" in \#*|"") continue ;; esac
    if [ ! -f "$caminho" ]; then
      echo "AVISO (P-23): porta de entrada '$caminho' ($quem) declarada mas o arquivo não existe."
      continue
    fi
    grep -q '^@AGENTS\.md' "$caminho" && continue
    faltam=""
    grep -qi 'modo conciso' "$caminho" || faltam="modo conciso"
    grep -qi 'economia de tokens' "$caminho" || faltam="${faltam:+$faltam e }economia de tokens"
    # (26/10/2026, (849)) "todo modelo aberto em ~/agata usa as mesmas regras e as mesmas ferramentas":
    # a porta tem de levar também à memória comum do Conselho
    grep -q 'cache_conselho' "$caminho" || faltam="${faltam:+$faltam e }a memória comum (cache_conselho)"
    [ -n "$faltam" ] && echo "AVISO (P-23): '$caminho' ($quem) não traz $faltam nem importa o AGENTS.md. Por que importa: o modelo que entra por ali segue sem as diretrizes comuns (MEMÓRIAS (667)). O que fazer: acrescentar a linha das diretrizes ou '@AGENTS.md'."
  done < "$lista"
  return 0
}
