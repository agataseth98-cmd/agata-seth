#!/usr/bin/env bash
# P-25-SELOS (proposta 21/10/2026, v8): cadeia de SELOS.txt.
# SELOS.chain: c_i = sha256(c_{i-1} + "\n" + linha_i_de_SELOS.txt). Não altera o formato de SELOS.txt.
# NÃO é o P-25 do registro de sessão (C0), que fica para proposta posterior.
p25_selos_cadeia() {
  [ -f SELOS.txt ] || return 0
  if [ ! -f SELOS.chain ]; then
    PERIMETRO_ESTADO="PARCIAL"
    echo "AVISO (P-25-SELOS): SELOS.chain ausente; rodar 'bash scripts/selar.sh --iniciar-cadeia' para começar a cadeia."
    return 0
  fi
  python3 - <<'PY' || return 1
import hashlib,sys
linhas=[l.rstrip('\n') for l in open('SELOS.txt',encoding='utf-8') if l.strip()]
cadeia=[l.split()[0] for l in open('SELOS.chain',encoding='utf-8') if l.strip()]
if len(cadeia)!=len(linhas):
    print(f"SUSPEITO (P-25-SELOS): {len(linhas)} selos e {len(cadeia)} elos; cauda divergente."); sys.exit(1)
c=""
for i,l in enumerate(linhas):
    c=hashlib.sha256((c+"\n"+l).encode('utf-8')).hexdigest()
    if c!=cadeia[i]:
        print(f"SUSPEITO (P-25-SELOS): elo {i+1} não confere; SELOS.txt foi alterado."); sys.exit(1)
print(f"OK (P-25-SELOS): cadeia de {len(linhas)} selos íntegra.")
PY
}
