#!/usr/bin/env bash
# Roda localmente os mesmos passos do job `sdd` (.github/workflows/sdd.yml), na ordem, sem parar no primeiro erro.
# Uso: bash scripts/ci_sdd_local.sh            (a partir da raiz do repositório)
# pytest: usa $PYTEST se definido; senão, o `pytest` do PATH. Não instala nada.
set -u
RAIZ="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$RAIZ" || exit 1
PYTEST="${PYTEST:-$(command -v pytest || true)}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FALHAS=0
passo() { local nome="$1"; shift; if "$@" >"$TMP/saida.txt" 2>&1; then echo "OK    $nome"; else echo "FALHA $nome"; tail -5 "$TMP/saida.txt" | sed 's/^/        /'; FALHAS=$((FALHAS+1)); fi; }

if [ -z "$PYTEST" ]; then echo "FALHA pytest não encontrado (defina PYTEST=/caminho/pytest)"; exit 1; fi
# os ciclos SDD chamam "pytest" pelo nome: o diretório do binário precisa estar no PATH
export PATH="$(dirname "$PYTEST"):$PATH"

passo "testes SDD (pytest)" "$PYTEST" -q -p no:cacheprovider redesign/sdd_flow/tests redesign/review_mesh redesign/project_kit redesign/evidence_ledger redesign/painel_operacional redesign/obsidian redesign/nova_versao/tests redesign/alexandria/tests redesign/metacognicao/tests redesign/corpo/tests redesign/conexoes/tests redesign/avaliacao/tests redesign/sentidos/tests redesign/confiabilidade/tests redesign/rotas/tests redesign/mvp_autoaprimoramento/tests ferramentas/test_ferramentas.py
passo "gate de sincronia das specs (selftest)" python3 -I scripts/gate_spec_sync.py --selftest
passo "gate de sincronia das specs (antes dos ciclos, que regeneram o drift)" python3 -I scripts/gate_spec_sync.py
passo "ciclo SDD sobre o próprio sdd_flow" python3 redesign/sdd_flow/runner.py "$TMP/state.json" cycle redesign/sdd_flow/spec redesign/sdd_flow/spec/acceptance.json --scope redesign/sdd_flow
passo "ciclo SDD sobre a nova versão" python3 redesign/sdd_flow/runner.py "$TMP/state-nv.json" cycle redesign/nova_versao/spec redesign/nova_versao/spec/acceptance.json --scope redesign/nova_versao
passo "âncora dos componentes" python3 redesign/sdd_flow/anchor.py . redesign/sdd_flow redesign/project_kit redesign/review_mesh redesign/evidence_ledger redesign/painel_operacional redesign/nova_versao redesign/alexandria redesign/metacognicao redesign/corpo redesign/conexoes redesign/avaliacao redesign/sentidos
for c in project_kit review_mesh evidence_ledger painel_operacional nova_versao alexandria metacognicao corpo conexoes avaliacao sentidos; do
  passo "critérios e drift: $c" python3 redesign/sdd_flow/acceptance_runner.py "redesign/$c/spec/acceptance.json" "$TMP/$c-evidence.json"
  passo "drift por critério: $c" python3 redesign/sdd_flow/criterion_drift.py "redesign/$c/spec/spec.md" "$TMP/$c-evidence.json" "$TMP/$c-drift.md"
done
passo "qualidade de LLM (selftest)" python3 -I redesign/painel_operacional/qualidade_llm.py --selftest
passo "skills sem problema de lint" python3 -c "import json,subprocess,sys; out=subprocess.run([sys.executable,'redesign/painel_operacional/qualidade_llm.py'],capture_output=True,text=True,check=True).stdout; d=json.loads(out); bad=[s for s in d['skills'] if s['problemas']]; [print(s['skill'], s['problemas']) for s in bad]; sys.exit(1 if bad else 0)"
passo "medição de recuperação (selftest)" python3 -I scripts/medir_recuperacao.py --selftest
passo "medição de contexto (selftest)" python3 -I scripts/medir_contexto_efetivo.py --selftest
passo "teste de português (selftest)" python3 -I scripts/teste_portugues.py --selftest
passo "voz do sistema (selftest)" python3 -I scripts/agata_falar.py --selftest
passo "projeto SDD declarativo (selftest)" python3 -I redesign/sdd_flow/project.py --selftest
passo "pacote mecânico: testes do turno" python3 scripts/testar_turno.py
passo "pacote mecânico: selftest do turno" python3 scripts/turno.py --selftest
passo "pacote mecânico: selftest da auditoria do turno" python3 redesign/router/auditoria_turno.py --selftest
passo "pacote mecânico: testes dos mecanismos do Conselho" python3 scripts/testar_mecanismos.py
passo "pacote mecânico: verificador de mecanismos do Conselho" python3 scripts/conselho_mecanismos.py --verificar

if [ "$FALHAS" -eq 0 ]; then echo "CI LOCAL: TUDO OK"; exit 0; fi
echo "CI LOCAL: $FALHAS passo(s) falharam"; exit 1
