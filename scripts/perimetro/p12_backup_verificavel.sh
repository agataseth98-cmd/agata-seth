#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

p12_backup_verificavel() {
  local manifesto="models/manifest.json"
  if [ ! -f "$manifesto" ]; then
    echo "P-12: $manifesto ausente -- pulado."
    PERIMETRO_ESTADO="SKIP"; return 0
  fi
  if ! command -v restic >/dev/null 2>&1; then
    echo "PARCIAL (P-12): restic nao instalado -- nao da pra conferir backup por recurso."
    PERIMETRO_ESTADO="PARCIAL"; return 0
  fi

  local hd_ok=0
  if [ -d "$P12_REPO" ] && [ -f "$P12_PASS" ] && \
     RESTIC_PASSWORD_FILE="$P12_PASS" restic -r "$P12_REPO" cat config >/dev/null 2>&1; then
    hd_ok=1
  fi

  # nome<TAB>sha256 de cada recurso (blob_sha256 ou ir_sha256_xmlbin).
  local linhas
  linhas="$(python3 - "$manifesto" <<'PY'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
for x in m["modelos"]:
    h = x.get("blob_sha256") or x.get("ir_sha256_xmlbin") or ""
    print(x["name"] + "\t" + h)
PY
)"

  local falhou_p12=0 nome hash em_falha em_aviso fresco
  local TAB
  TAB="$(printf '\t')"
  while IFS="$TAB" read -r nome hash; do
    [ -z "$nome" ] && continue
    case " $P12_FALHA_SEM_BACKUP " in *" $nome "*) em_falha=1 ;; *) em_falha=0 ;; esac
    case " $P12_AVISO_SEM_BACKUP " in *" $nome "*) em_aviso=1 ;; *) em_aviso=0 ;; esac
    [ "$em_falha" = 0 ] && [ "$em_aviso" = 0 ] && continue

    if [ "$hd_ok" = 1 ]; then
      fresco="$(RESTIC_PASSWORD_FILE="$P12_PASS" P12_REPO="$P12_REPO" \
        python3 - "$nome" "$hash" "$P12_N_DIAS" <<'PY'
import json, os, subprocess, sys, datetime
nome, alvo, ndias = sys.argv[1], sys.argv[2], int(sys.argv[3])
try:
    out = subprocess.run(
        ["restic", "-r", os.environ["P12_REPO"], "snapshots", "--json", "--tag", nome],
        check=True, capture_output=True, text=True, timeout=60,
    ).stdout
    snaps = json.loads(out or "[]")
except Exception:
    snaps = []
agora = datetime.datetime.now(datetime.timezone.utc)
ok = False
for s in snaps:
    tags = s.get("tags") or []
    if alvo and alvo not in tags:
        continue
    t = (s.get("time") or "")[:19]
    try:
        dt = datetime.datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
    except Exception:
        continue
    if (agora - dt).days <= ndias:
        ok = True
print("1" if ok else "0")
PY
)"
      if [ "$fresco" != 1 ]; then
        if [ "$em_falha" = 1 ]; then
          echo "SUSPEITO (P-12): recurso '$nome' (sha256 ${hash:0:12}...) sem snapshot restic do conteudo atual < ${P12_N_DIAS}d. Por que importa: build local irrecuperavel -- disco morto = trabalho perdido. O que fazer: com o HD montado, redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md -- 'restic backup --tag $nome --tag $hash <path>' + 'restic check'."
          falhou_p12=1
        else
          echo "AVISO (P-12): recurso '$nome' sem snapshot restic < ${P12_N_DIAS}d (reconstruivel do HF/registry, mas o re-download e' lento -- vale um snapshot). Ver redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md."
        fi
      fi
    fi
  done <<EOF
$linhas
EOF

  [ "$falhou_p12" = 1 ] && return 1

  if [ "$hd_ok" = 0 ]; then
    local visto="nunca"
    if [ -f "$P12_CACHE" ]; then
      visto="$(python3 - "$P12_CACHE" <<'PY'
import json, sys
try:
    c = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception:
    c = {}
ds = [v.get("verificado_em", "") for v in c.values() if isinstance(v, dict) and v.get("verificado_em")]
print(min(ds) if ds else "nunca")
PY
)"
    fi
    echo "PARCIAL (P-12): HD ($P12_REPO) ausente -- cobertura de backup nao re-conferida. Cache de cobertura mais velho: $visto. O que fazer: no proximo acesso ao HD, rodar redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md (snapshots + restic check + reescreve o cache)."
    PERIMETRO_ESTADO="PARCIAL"; return 0
  fi
  return 0
}

