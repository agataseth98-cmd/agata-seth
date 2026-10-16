#!/usr/bin/env bash
# scripts/p8_verificar_pr.sh <base> <head>   -- CANDIDATO, nao aplicado.
#
# Fiscal do P-8 para PR no GitHub. O P-8 vigente roda so no hook de commit, na maquina do Humano;
# um PR feito na web ou com --no-verify chega ao `main` sem o par `.diff`/`APROVADO-` assinado.
# Este script fecha isso, com tres regras que vieram dos pareceres do Codex e do Claude:
#
#  1. CONFIANCA ANTERIOR. Quem fiscaliza vem da BASE, nunca do head: o escopo do P-8
#     (`_p8_eh_comportamento`), a raiz de assinaturas (`propostas/.allowed_signers`) e o auxiliar
#     de integralidade (`scripts/p8_integral.py`) sao lidos de `git show <base>:...`. O head e DADO:
#     so se le por plumbing do git, nunca se faz checkout nem se executa. Sem `.allowed_signers`
#     na base o script FALHA (nao ha modo compat nem bootstrap permissivo, ao contrario do hook).
#  2. CONSUMO INTEGRAL. Pares assinados que o PR CONSOME (presentes em `propostas/aplicadas/` no head
#     e ausentes la na base) sao aplicados sobre a base num indice descartavel; o head tem que
#     igualar essa arvore em tudo o que o diff toca e em TODO caminho protegido que mudou, por
#     caminho, modo, tipo e OID. Consumo parcial e mudanca protegida alem do assinado bloqueiam.
#  (Escopo: este fiscal e PROPORCIONAL -- compara o que o diff toca e todo caminho protegido que mudou, nao a arvore
#  inteira do PR. A comparacao da arvore inteira e a do pacote de aplicacao, `p8_integral.py` sem `--restrict`.)
#  3. SO TRANSPORTE EXATO E ANCORA. As unicas diferencas toleradas sao os 4 caminhos exatos de
#     cada par (`propostas/<n>.diff`, `propostas/APROVADO-<n>` e os mesmos em `aplicadas/`) e o
#     bloco `ANCORA-SHA` gerado pelo pre-commit em REGRAS, PROJETO, MEMORIAS e PROMPT_CARREGAMENTO.
#
# Uso no GitHub Actions: workflow `pull_request_target` (roda a versao do `main`), checkout da BASE,
# `git fetch` do head como objetos, e chamar este script. Nunca checkout do head neste job.
#
# Saida: linhas `OK`/`AVISO`/`FALHA`; exit 0 = ok, 1 = falha do controle, 2 = erro de uso/ambiente.
set -uo pipefail

base="${1:-}"; head="${2:-}"
[ -n "$base" ] && [ -n "$head" ] || { echo "uso: bash scripts/p8_verificar_pr.sh <base> <head>" >&2; exit 2; }
git rev-parse --git-dir >/dev/null 2>&1 || { echo "ERRO: fora de um repositorio git" >&2; exit 2; }
git cat-file -e "$base^{commit}" 2>/dev/null || { echo "ERRO: base inexistente: $base" >&2; exit 2; }
git cat-file -e "$head^{commit}" 2>/dev/null || { echo "ERRO: head inexistente: $head (faltou o git fetch do head?)" >&2; exit 2; }

falha() { echo "FALHA P-8 (PR): $*"; exit 1; }
tmp="$(mktemp -d)" || exit 2
trap 'rm -rf "$tmp"' EXIT

# -- 1. tudo o que fiscaliza vem da BASE -----------------------------------------------------
git show "$base:scripts/perimetro/p08_quarentena.sh" > "$tmp/p08.sh" 2>/dev/null \
  || falha "a base nao tem scripts/perimetro/p08_quarentena.sh (escopo do P-8)"
git show "$base:scripts/p8_integral.py" > "$tmp/p8_integral.py" 2>/dev/null \
  || falha "a base nao tem scripts/p8_integral.py (fiscal ainda nao instalado na base)"
git show "$base:propostas/.allowed_signers" > "$tmp/signers" 2>/dev/null && [ -s "$tmp/signers" ] \
  || falha "a base nao tem propostas/.allowed_signers: sem raiz de confianca (sem bootstrap permissivo)"
command -v ssh-keygen >/dev/null 2>&1 || falha "ssh-keygen ausente (falha fechada)"
command -v python3 >/dev/null 2>&1 || falha "python3 ausente (falha fechada)"
# shellcheck disable=SC1091
source "$tmp/p08.sh"   # so define funcoes; `_p8_eh_comportamento` e a da BASE
declare -F _p8_eh_comportamento >/dev/null || falha "escopo do P-8 nao carregou da base"

# -- 2. caminhos protegidos que o PR muda ----------------------------------------------------
git diff --name-only -z --no-renames "$base" "$head" > "$tmp/mudou.z" || exit 2
: > "$tmp/protegidos.z"; n_prot=0
while IFS= read -r -d '' f; do
  if _p8_eh_comportamento "$f"; then printf '%s\0' "$f" >> "$tmp/protegidos.z"; n_prot=$((n_prot+1)); fi
done < "$tmp/mudou.z"

# -- 3. pares que o PR consome (presentes em aplicadas/ no head, ausentes la na base) --------
verificados=(); ignorados=()
while IFS= read -r -d '' caminho; do
  nome="${caminho#propostas/aplicadas/APROVADO-}"
  [ "$nome" != "$caminho" ] || continue
  case "$nome" in */*|'') continue ;; esac
  git cat-file -e "$base:$caminho" 2>/dev/null && continue            # ja estava aplicado na base
  d="propostas/aplicadas/$nome.diff"
  git cat-file -e "$head:$d" 2>/dev/null || { ignorados+=("$nome (sem .diff)"); continue; }
  git show "$head:$d" > "$tmp/$nome.diff" 2>/dev/null; git show "$head:$caminho" > "$tmp/$nome.aprovado" 2>/dev/null
  dsha="$(sha256sum "$tmp/$nome.diff" | awk '{print $1}')"
  grep -qx "diff-sha256: $dsha" "$tmp/$nome.aprovado" || { ignorados+=("$nome (hash do .diff nao bate)"); continue; }
  sed -n '/BEGIN SSH SIGNATURE/,/END SSH SIGNATURE/p' "$tmp/$nome.aprovado" > "$tmp/$nome.sig"
  [ -s "$tmp/$nome.sig" ] || { ignorados+=("$nome (sem assinatura)"); continue; }
  if printf '%s  %s' "$dsha" "$nome" | ssh-keygen -Y verify -f "$tmp/signers" -I agata-humano \
       -n agata-aprovacao-p8 -s "$tmp/$nome.sig" >/dev/null 2>&1; then
    verificados+=("$nome")
  else
    ignorados+=("$nome (assinatura invalida para a raiz da base)")
  fi
done < <(git ls-tree -r --name-only -z "$head" -- propostas/aplicadas | LC_ALL=C sort -z)

for i in "${ignorados[@]:-}"; do [ -n "$i" ] && echo "AVISO P-8 (PR): par ignorado -- $i"; done

if [ "${#verificados[@]}" -eq 0 ]; then
  if [ "$n_prot" -eq 0 ]; then echo "OK P-8 (PR): nenhum caminho protegido mudou e nenhum par foi consumido"; exit 0; fi
  echo "FALHA P-8 (PR): $n_prot caminho(s) protegido(s) mudou(aram) sem nenhum par assinado consumido:"
  tr '\0' '\n' < "$tmp/protegidos.z" | sed 's/^/  - /'
  exit 1
fi
echo "OK P-8 (PR): ${#verificados[@]} par(es) com assinatura valida pela raiz da base: ${verificados[*]}"

# -- 4. transporte exato dos pares + comparacao integral -------------------------------------
python3 -I - "$base" "$head" "${verificados[@]}" > "$tmp/transporte.json" <<'PY' || falha "transporte inválido: par sem arquivo regular (100644) em propostas/aplicadas/ no head"
import json, subprocess, sys
base, head, nomes = sys.argv[1], sys.argv[2], sys.argv[3:]
def entrada(rev, caminho):
    p = subprocess.run(["git", "ls-tree", "-z", rev, "--", caminho], stdout=subprocess.PIPE, check=True)
    if not p.stdout:
        return None
    meta, _ = p.stdout.rstrip(b"\0").split(b"\t", 1)
    modo, tipo, oid = meta.decode().split()
    return {"mode": modo, "type": tipo, "oid": oid}
t = {}
for n in nomes:
    for k in (f"{n}.diff", f"APROVADO-{n}"):
        # aplicadas/: os bytes que o fiscal acabou de AUTENTICAR (hash do .diff e assinatura do APROVADO), lidos do
        # head; só arquivo regular 100644 (symlink, executável ou submódulo não são par).
        e = entrada(head, f"propostas/aplicadas/{k}")
        if e is None or e["mode"] != "100644" or e["type"] != "blob":
            sys.exit(3)
        t[f"propostas/aplicadas/{k}"] = e
        # propostas/: a expectativa vem da BASE, nunca do head (F2 do Codex): o original ou fica idêntico ao da base
        # ou foi removido (movido para aplicadas/); algo novo ou diferente ali é arquivo não autorizado.
        t[f"propostas/{k}"] = entrada(base, f"propostas/{k}") if entrada(head, f"propostas/{k}") is not None else None
print(json.dumps(t))
PY
args=()
for n in "${verificados[@]}"; do args+=(--diff "$tmp/$n.diff"); done
for a in REGRAS.md PROJETO.md MEMÓRIAS.md PROMPT_CARREGAMENTO.md; do args+=(--ancora "$a"); done
args+=(--ancora-ancestral-de "$head")
resultado="$(python3 -I "$tmp/p8_integral.py" --repo . --base "$base" "${args[@]}" \
  --actual-tree "$(git rev-parse "$head^{tree}")" --transport "$tmp/transporte.json" \
  --restrict "$tmp/protegidos.z" --incluir-tocados)"
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "FALHA P-8 (PR): o head nao e exatamente a base mais o(s) diff(s) assinado(s) (consumo parcial, extra ou divergente):"
  printf '%s\n' "$resultado" | python3 -I -c '
import json,sys
r=json.load(sys.stdin)
for k in ("erro","nao_consumido_ou_ausente","extra","divergente"):
    v=r.get(k)
    if v: print(f"  {k}:", v if isinstance(v,str) else ", ".join(v[:20]))
'
  exit 1
fi
echo "OK P-8 (PR): consumo integral (base + $(printf '%s\n' "$resultado" | python3 -I -c 'import json,sys;print(len(json.load(sys.stdin)["diffs_sha256"]))') diff(s)); transporte exato e ancora normalizada"
exit 0
