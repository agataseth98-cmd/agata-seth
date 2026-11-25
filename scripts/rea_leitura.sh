#!/usr/bin/env bash
# rea_leitura.sh -- wrapper de leitura estática do REA (rea-agents 6.8.0).
#
# Executa o bin do REA que já está no cache do npx (sem npx, sem download, sem
# setup), mas só aceita os subcomandos da allowlist PERMITIDOS. Qualquer outro
# sai com exit 2. A skill .agents/skills/agata-engenharia-reversa descreve a
# mesma lista; se mudar um lado, mude o outro.
#
# Uso:
#   bash scripts/rea_leitura.sh <subcomando-permitido> [argumentos]
#   bash scripts/rea_leitura.sh --selftest   (testa a checagem; não executa o REA)
set -euo pipefail

# Subcomandos que o `rea --help` (6.8.0) descreve como estáticos ou offline
# sobre arquivos locais ou capturas já salvas. Fora desta lista: recusado.
PERMITIDOS=(
  analyze-javascript-application
  recover-javascript-sources
  export-web-scripts
  trace-javascript-semantics
  compare-source-to-bundle
  compare-application-versions
  compare-javascript-export-shapes
  reconcile-javascript-runtime
  inspect-web-network-capture
  compare-web-captures
  trace-web-module-imports
  trace-web-source-location
  inspect-analysis-view
  inspect-evidence-bundle
  inspect-pe-imports
  inspect-pe-certificates
  inspect-pe-resources
  inspect-pe-load-config
)

# Flags globais que sobem servidor MCP ou atualizam o pacote, em qualquer posição.
FLAGS_PROIBIDAS=(--mcp --update)

# Padrões que nunca podem entrar em PERMITIDOS (conferidos no selftest).
PADROES_PROIBIDOS=(
  setup update uninstall doctor mcp
  'install-*' 'push-*' 'start-*' 'stop-*' 'set-*' 'annotate-*'
  'observe-*' 'capture-*' instrument-with-frida debug-with-gdb
  export-evidence-bundle analyze-web-bundle inspect-electron-page inspect-web-page
)

REA_VERSAO="6.8.0"

subcomando_permitido() {
  local s
  for s in "${PERMITIDOS[@]}"; do
    if [[ "$1" == "$s" ]]; then
      return 0
    fi
  done
  return 1
}

comando_pe() {
  case "$1" in
    inspect-pe-imports|inspect-pe-certificates|inspect-pe-resources|inspect-pe-load-config) return 0 ;;
    *) return 1 ;;
  esac
}

# checar <argumentos do rea>: retorna 0 se pode executar; 1 e mensagem em stderr se recusa.
checar() {
  if [[ $# -eq 0 ]]; then
    echo "rea_leitura: recusado: nenhum subcomando informado" >&2
    return 1
  fi
  if ! subcomando_permitido "$1"; then
    echo "rea_leitura: recusado: '$1' não está na allowlist (ver a skill agata-engenharia-reversa)" >&2
    return 1
  fi
  if comando_pe "$1"; then
    if [[ $# -ne 3 || "$3" != "--json" || "$2" != /* ]]; then
      echo "rea_leitura: recusado: comando PE exige exatamente <caminho-absoluto> --json" >&2
      return 1
    fi
    return 0
  fi
  local a f
  for a in "$@"; do
    for f in "${FLAGS_PROIBIDAS[@]}"; do
      if [[ "$a" == "$f" ]]; then
        echo "rea_leitura: recusado: flag '$f' sobe servidor ou atualiza o pacote" >&2
        return 1
      fi
    done
  done
  return 0
}

# Procura o bin do REA no cache do npx; não baixa nada.
achar_bin() {
  local pkg
  for pkg in "$HOME"/.npm/_npx/*/node_modules/rea-agents/package.json; do
    if [[ -f "$pkg" ]] && grep -q "\"version\": \"$REA_VERSAO\"" "$pkg"; then
      local bin
      bin="$(dirname "$pkg")/scripts/rea.mjs"
      if [[ -f "$bin" ]]; then
        echo "$bin"
        return 0
      fi
    fi
  done
  return 1
}

validar_pe_basico() {
  python3 - "$2" <<'PY'
import struct
import sys
import os

path = sys.argv[1]
try:
    with open(path, "rb") as artifact:
        size = os.fstat(artifact.fileno()).st_size
        dos = artifact.read(0x40)
except OSError as exc:
    print(f"rea_leitura: recusado: não foi possível ler o PE: {exc}", file=sys.stderr)
    raise SystemExit(1)
if len(dos) < 0x40 or dos[:2] != b"MZ":
    print("rea_leitura: recusado: cabeçalho DOS/PE ausente ou truncado", file=sys.stderr)
    raise SystemExit(1)
pe_offset = struct.unpack_from("<I", dos, 0x3C)[0]
if pe_offset > size - 24:
    print("rea_leitura: recusado: assinatura PE ausente ou cabeçalho truncado", file=sys.stderr)
    raise SystemExit(1)
with open(path, "rb") as artifact:
    artifact.seek(pe_offset)
    header = artifact.read(24)
if len(header) != 24 or header[:4] != b"PE\0\0":
    print("rea_leitura: recusado: assinatura PE ausente ou cabeçalho truncado", file=sys.stderr)
    raise SystemExit(1)
machine, _, _, _, _, optional_size, _ = struct.unpack_from("<HHIIIHH", header, 4)
optional = pe_offset + 24
if optional_size < 2 or optional + optional_size > size:
    print("rea_leitura: recusado: cabeçalho opcional PE truncado", file=sys.stderr)
    raise SystemExit(1)
with open(path, "rb") as artifact:
    artifact.seek(optional)
    optional_prefix = artifact.read(2)
magic = struct.unpack("<H", optional_prefix)[0]
expected = {0x014C: 0x010B, 0x01C0: 0x010B, 0x01C2: 0x010B, 0x01C4: 0x010B,
            0x8664: 0x020B, 0xAA64: 0x020B, 0xA641: 0x020B}.get(machine)
minimum = {0x010B: 0x60, 0x020B: 0x70}.get(magic)
if minimum is None or optional_size < minimum or magic not in (0x010B, 0x020B):
    print("rea_leitura: recusado: optional-header não é PE32/PE32+ completo", file=sys.stderr)
    raise SystemExit(1)
if expected is not None and magic != expected:
    print("rea_leitura: recusado: Machine não corresponde ao magic PE32/PE32+", file=sys.stderr)
    raise SystemExit(1)
PY
}

selftest() {
  local ok=0 total=0 p g ruim=""

  # conferir <passa|recusa> <descrição> <argumentos do checar...>
  conferir() {
    local esperado="$1" descricao="$2" obtido
    shift 2
    total=$((total + 1))
    if checar "$@" 2>/dev/null; then
      obtido=passa
    else
      obtido=recusa
    fi
    if [[ "$obtido" == "$esperado" ]]; then
      ok=$((ok + 1))
      echo "ok     $descricao ($obtido)"
    else
      echo "FALHA  $descricao: esperado $esperado, obtido $obtido"
    fi
  }

  conferir passa "subcomando permitido passa a checagem" analyze-javascript-application /caminho/do/app --json
  conferir recusa "subcomando proibido 'setup' é recusado" setup --client codex
  conferir recusa "sem argumento é recusado"
  conferir recusa "subcomando desconhecido é recusado" subcomando-inventado-xyz
  conferir recusa "flag --update é recusada mesmo com subcomando permitido" analyze-javascript-application /caminho --update
  for p in inspect-pe-imports inspect-pe-certificates inspect-pe-resources inspect-pe-load-config; do
    conferir passa "$p aceita path absoluto e --json" "$p" /tmp/amostra.exe --json
    conferir recusa "$p recusa caminho relativo" "$p" amostra.exe --json
    conferir recusa "$p recusa argumento extra" "$p" /tmp/amostra.exe --json --max-file-bytes 100
    conferir recusa "$p exige --json" "$p" /tmp/amostra.exe
  done

  total=$((total + 1))
  local total_esperado=18
  if [[ "${#PERMITIDOS[@]}" -eq "$total_esperado" ]]; then
    ok=$((ok + 1)); echo "ok     allowlist contém os 14 comandos JS/web e os 4 PE"
  else
    echo "FALHA  allowlist contém ${#PERMITIDOS[@]} comandos; esperado $total_esperado"
  fi

  total=$((total + 1))
  for p in "${PERMITIDOS[@]}"; do
    for g in "${PADROES_PROIBIDOS[@]}"; do
      # shellcheck disable=SC2254
      case "$p" in
        $g) ruim="$ruim $p" ;;
      esac
    done
  done
  if [[ -z "$ruim" ]]; then
    ok=$((ok + 1))
    echo "ok     nenhum permitido casa padrão proibido"
  else
    echo "FALHA  permitidos que casam padrão proibido:$ruim"
  fi

  echo "selftest: $ok de $total testes passaram (REA não foi executado)"
  [[ "$ok" -eq "$total" ]]
}

main() {
  if [[ "${1:-}" == "--selftest" ]]; then
    if selftest; then
      exit 0
    fi
    exit 1
  fi
  if ! checar "$@"; then
    exit 2
  fi
  if comando_pe "$1" && ! validar_pe_basico "$1" "$2"; then
    exit 2
  fi
  local bin
  if ! bin="$(achar_bin)"; then
    echo "rea_leitura: REA $REA_VERSAO não está no cache do npx (~/.npm/_npx). Nada foi baixado nem instalado." >&2
    exit 3
  fi
  exec node "$bin" "$@"
}

main "$@"
