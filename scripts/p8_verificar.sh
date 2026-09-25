#!/usr/bin/env bash
# p8_verificar.sh <nome> -- confere, SEM aplicar nada, se a proposta P-8 <nome> pode ser aplicada:
#   1. propostas/<nome>.diff e propostas/APROVADO-<nome> existem (pendentes, fora de aplicadas/);
#   2. sha256 do .diff == linha `diff-sha256:` do APROVADO;
#   3. assinatura ssh válida de `agata-humano`, namespace agata-aprovacao-p8, contra a raiz de
#      confiança de HEAD (`git show HEAD:propostas/.allowed_signers`, nunca a cópia de trabalho --
#      mesma regra do P-8, MEMÓRIAS (367));
#   4. `git apply --check` limpo contra a árvore atual.
# Read-only. Exit 0 = pode aplicar; 1 = alguma checagem falhou (diz qual); 2 = uso errado.
# Por que existe (MEMÓRIAS (543)): esta verificação era feita à mão, comando a comando, a cada
# aplicação -- 7 vezes só em 24/09/2026. Passo determinístico não deve depender de o modelo
# lembrar a sequência (bússola B4); e o Goose, fallback do Claude Code, precisa do MESMO passo.
set -u
nome="${1:-}"
case "$nome" in ''|*/*|*.diff|*.) echo "uso: bash scripts/p8_verificar.sh <nome>  (basename, sem .diff, sem ponto no fim)"; exit 2 ;; esac
raiz="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "FALHA: fora de um repositório git"; exit 1; }
cd "$raiz" || exit 1
diff_path="propostas/$nome.diff"; apr="propostas/APROVADO-$nome"
[ -f "$diff_path" ] || { echo "FALHA 1: $diff_path não existe (já aplicada? nome certo?)"; exit 1; }
[ -f "$apr" ] || { echo "FALHA 1: $apr não existe -- o Humano ainda não assinou (bash scripts/aprovar.sh $nome)"; exit 1; }
echo "OK 1: par presente"

dsha="$(sha256sum "$diff_path" | cut -d' ' -f1)"
if grep -qx "diff-sha256: $dsha" "$apr"; then echo "OK 2: sha256 do .diff bate ($(printf %.12s "$dsha"))"
else echo "FALHA 2: sha256 do .diff ($(printf %.12s "$dsha")) não bate com o diff-sha256: do APROVADO -- o .diff mudou depois de assinado"; exit 1; fi

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
if ! git show HEAD:propostas/.allowed_signers > "$tmp/signers" 2>/dev/null; then
  echo "FALHA 3: sem propostas/.allowed_signers em HEAD -- não há raiz de confiança pra verificar"; exit 1; fi
sed -n '/BEGIN SSH SIGNATURE/,/END SSH SIGNATURE/p' "$apr" > "$tmp/sig"
[ -s "$tmp/sig" ] || { echo "FALHA 3: APROVADO sem bloco de assinatura ssh"; exit 1; }
if out="$(printf '%s  %s' "$dsha" "$nome" | ssh-keygen -Y verify -f "$tmp/signers" -I agata-humano -n agata-aprovacao-p8 -s "$tmp/sig" 2>&1)"; then
  echo "OK 3: $out"
else echo "FALHA 3: assinatura inválida -- $out"; exit 1; fi

if out="$(git apply --check "$diff_path" 2>&1)"; then echo "OK 4: git apply --check limpo"
else echo "FALHA 4: não aplica na árvore atual -- $out"; exit 1; fi
echo "PODE APLICAR: $nome"
