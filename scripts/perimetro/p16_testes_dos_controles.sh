#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

p16_testes_dos_controles() {
  # Guarda de recursão: a suíte roda o perímetro dentro do clone dela.
  if [ -n "${AGATA_TESTE_PERIMETRO:-}" ]; then
    echo "P-16: rodando DENTRO da suíte -- pulado (senão recursa infinitamente)."
    PERIMETRO_ESTADO="SKIP"; return 0
  fi
  local staged tocados
  staged="$(git -c core.quotepath=false diff --cached --no-renames --name-only 2>/dev/null)"
  tocados="$(echo "$staged" | grep -E "$P16_ARQUIVOS_DE_CONTROLE" || true)"
  if [ -z "$tocados" ]; then
    echo "P-16: nenhum arquivo de controle staged -- suíte não precisa rodar."
    PERIMETRO_ESTADO="SKIP"; return 0
  fi
  if [ ! -f "$_PERIMETRO_DIR/testar_perimetro.sh" ]; then
    echo "SUSPEITO (P-16): arquivo de controle staged ($(echo "$tocados" | tr '\n' ' ')) mas scripts/testar_perimetro.sh não existe -- o controle mudou sem que exista teste dele."
    return 1
  fi
  # Cobertura ANTES de rodar: todo controle do main() precisa ter caso na
  # suíte OU motivo escrito na tabela SEM_TESTE dela. Acrescentado em (422)
  # porque a suíte nasceu cobrindo 5 de 16 e os outros 11 não estavam
  # isentos -- estavam esquecidos, e ninguém sabia dizer quais. É a mesma
  # doutrina do resto: a diferença entre "não dá pra testar" e "ninguém
  # testou" tem de estar escrita, senão vira o P-7 outra vez.
  local declarados testados descobertos
  declarados="$(grep -oE 'cabecalho "P-[0-9]+"' "$_PERIMETRO_DIR/perimetro.sh" | grep -oE 'P-[0-9]+' | sort -u)"
  testados="$( { grep -oE '_caso P-[0-9]+' "$_PERIMETRO_DIR/testar_perimetro.sh" | grep -oE 'P-[0-9]+'
                 grep -oE '^\s*\[P-[0-9]+\]=' "$_PERIMETRO_DIR/testar_perimetro.sh" | grep -oE 'P-[0-9]+'; } | sort -u)"
  descobertos="$(comm -23 <(echo "$declarados") <(echo "$testados") | tr '\n' ' ')"
  if [ -n "${descobertos// /}" ]; then
    echo "SUSPEITO (P-16): controle(s) sem caso na suíte E sem motivo escrito: $descobertos"
    echo "  O que fazer: ou escreva um caso em scripts/testar_perimetro.sh, ou declare o motivo na tabela SEM_TESTE de lá. Controle sem teste e sem justificativa é como o P-7 antes de (419) -- ninguém sabe se está dispensado ou esquecido."
    return 1
  fi
  echo "P-16: controle staged ($(echo "$tocados" | tr '\n' ' ')) -- rodando a suíte de regressão (pode levar 1-2 min)..."
  local saida codigo
  saida="$(AGATA_TESTE_PERIMETRO=1 bash "$_PERIMETRO_DIR/testar_perimetro.sh" 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "$saida" | tail -1
    return 0
  fi
  echo "SUSPEITO (P-16): a suíte de regressão dos controles REPROVOU com um arquivo de controle staged. O que fazer: rode 'bash scripts/testar_perimetro.sh' e conserte antes de comitar -- um controle que perdeu cobertura não deve entrar no canon."
  echo "$saida" | sed 's/^/  /'
  return 1
}

