#!/usr/bin/env bash
# scripts/aprovar.sh <nome> ["motivo em uma frase"]
#
# Cria propostas/APROVADO-<nome> ASSINADO com a chave ssh do Humano -- o ato
# deliberado que P-8 exige (PROJETO.md, "Quarentena estrutural"). A assinatura
# amarra a aprovação AQUELE propostas/<nome>.diff: editar o diff depois quebra
# a verificação em scripts/perimetro.sh (P-8).
#
# LINHA VERMELHA: o EXECUTOR (modelo) NUNCA roda este script. Agora não é só
# convenção -- assinar exige a passphrase da chave privada, que só o Humano
# tem. Chave privada: ~/.config/agata/aprovacao_ed25519 (fora do repo, nunca
# commitada). Chave pública: propostas/.allowed_signers (no repo).
#
# Sem a chave privada no lugar: cria o arquivo SEM assinatura e AVISA -- só
# serve na janela entre este script existir e o par de chaves ser gerado.
# Depois que propostas/.allowed_signers existe, P-8 recusa APROVADO- sem
# assinatura válida.
set -euo pipefail

nome="${1:?uso: bash scripts/aprovar.sh <nome> [\"motivo\"]  (nome = basename do .diff, sem extensão)}"
motivo="${2:-}"

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
chave="${AGATA_APROVACAO_CHAVE:-$HOME/.config/agata/aprovacao_ed25519}"
ns="agata-aprovacao-p8"

diff_path=""
for d in "$raiz/propostas/$nome.diff" "$raiz/propostas/aplicadas/$nome.diff"; do
  [ -f "$d" ] && { diff_path="$d"; break; }
done
[ -n "$diff_path" ] || { echo "ERRO: não achei propostas/$nome.diff (nem em aplicadas/)." >&2; exit 1; }

alvo="$raiz/propostas/APROVADO-$nome"
[ -e "$alvo" ] && { echo "ERRO: $alvo já existe -- nada a fazer." >&2; exit 1; }

dsha="$(sha256sum "$diff_path" | awk '{print $1}')"
msg="$(printf '%s  %s' "$dsha" "$nome")"

tmp="$(mktemp)"
{
  echo "Aprovado pelo Humano em $(date '+%Y-%m-%d %H:%M %z')."
  [ -n "$motivo" ] && echo "Motivo: $motivo"
  echo "nome: $nome"
  echo "diff-sha256: $dsha"
} > "$tmp"

if [ -f "$chave" ]; then
  if ! printf '%s' "$msg" | ssh-keygen -Y sign -f "$chave" -n "$ns" >> "$tmp"; then
    rm -f "$tmp"
    echo "ERRO: assinatura falhou -- propostas/APROVADO-$nome NÃO criado." >&2
    exit 1
  fi
  mv "$tmp" "$alvo"
  echo "criado e ASSINADO: propostas/APROVADO-$nome"
else
  mv "$tmp" "$alvo"
  echo "AVISO: $chave não existe -- propostas/APROVADO-$nome criado SEM assinatura." >&2
  echo "AVISO: gere o par uma vez:  ssh-keygen -t ed25519 -C $ns -f $chave" >&2
  echo "       depois:  printf 'agata-humano %s\\n' \"\$(awk '{print \$1\" \"\$2}' $chave.pub)\" > $raiz/propostas/.allowed_signers" >&2
  echo "criado (SEM assinatura): propostas/APROVADO-$nome"
fi

echo "próximo: o executor aplica o .diff, move o par para propostas/aplicadas/ e comita."
