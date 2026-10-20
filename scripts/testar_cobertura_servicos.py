#!/usr/bin/env python3
"""Contraprovas offline de P-4/P-9; nenhum serviço real é alterado."""
from pathlib import Path
import subprocess

RAIZ = Path(__file__).resolve().parent.parent

def shell(codigo):
    return subprocess.run(['bash', '-c', codigo], cwd=RAIZ, capture_output=True, text=True, check=False)

n = 0
for porta in (11435, 11436):
    for bind, esperado in [('127.0.0.1', 0), ('0.0.0.0', 1)]:
        r = shell(f'source scripts/perimetro/p04_bind.sh; p4_bind "tcp LISTEN 0 128 {bind}:{porta} 0.0.0.0:*"')
        assert r.returncode == esperado, (porta, bind, r.stdout, r.stderr)
        n += 1

base = '''source scripts/perimetro.sh
systemctl() {
  case "$*" in
    *is-enabled*) echo enabled;;
    *is-active*) case "${@: -1}" in
      "$ALVO") echo "$ESTADO";;
      *) echo active;;
    esac;;
  esac
}
docker() { printf '%s\\n' librechat librechat-mongodb librechat-meilisearch librechat-ponte-host; }
_p9_ollama_na_gpu() { :; }
'''
for alvo, estado in [('agata-manutencao.timer', 'failed'), ('agata-manutencao.timer', 'inactive'), ('agata-manutencao.timer', 'unknown'), ('agata-manutencao.service', 'failed'), ('laya-roteador.service', 'failed')]:
    r = shell(base + f'ALVO={alvo}; ESTADO={estado}; p9_servicos_declarados')
    assert r.returncode == 0 and alvo in r.stdout and 'AVISO (P-9)' in r.stdout, (alvo, estado, r.stdout, r.stderr)
    n += 1
r = shell(base + 'ALVO=nenhum; ESTADO=failed; p9_servicos_declarados')
assert r.returncode == 0 and not r.stdout, (r.stdout, r.stderr)
n += 1
r = shell(base + '''ALVO=nenhum; ESTADO=failed
docker() { case "$*" in *librechat-ponte-host*) :;; *) printf '%s\\n' librechat librechat-mongodb librechat-meilisearch;; esac; }
p9_servicos_declarados''')
assert r.returncode == 0 and 'librechat-ponte-host' in r.stdout, (r.stdout, r.stderr)
n += 1
print(f'COBERTURA SERVICOS OK -- {n}/{n}')
