#!/usr/bin/env bash
# Roda localmente os mesmos passos dos jobs `sdd` (.github/workflows/sdd.yml) e `suite-adversarial`
# (.github/workflows/perimetro.yml, seção no fim), na ordem, sem parar no primeiro erro.
# Uso: bash scripts/ci_sdd_local.sh            (a partir da raiz do repositório)
# pytest: usa $PYTEST se definido; senão, o `pytest` do PATH. Não instala nada.
# Resumo do último CI local (D5, 17/11/2026): ${AGATA_CI_DIR:-$HOME/.cache/agata/ci}/ultimo.json, com gerado_em, head,
# ok e falha (contagens), linha_final e passos [{nome, ok}]. Escrita atômica; falha de escrita é silenciosa e não muda
# o código de saída nem a saída padrão. Definida ANTES de qualquer efeito (sem TMP, sem trap), para o teste carregar
# este arquivo por `source` e chamar a função sem rodar os passos.
CI_PASSOS=()
_ci_texto_json() { sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }
_ci_gravar_ultimo() {
  local linha="$1" dir tmp head gerado item nome okv passos="" sep="" ok=0 falhas="${FALHAS:-0}"
  {
    dir="${AGATA_CI_DIR:-$HOME/.cache/agata/ci}"
    mkdir -p "$dir" || return 0
    head="$(git -C "${RAIZ:-.}" rev-parse --short HEAD 2>/dev/null | tr -cd '0-9a-f')"
    [ -n "$head" ] || head="desconhecido"
    gerado="$(date -Is)"
    for item in "${CI_PASSOS[@]:-}"; do
      [ -n "$item" ] || continue
      nome="${item%|*}"
      okv="${item##*|}"
      [ "$okv" = 1 ] && ok=$((ok + 1))
      passos="${passos}${sep}{\"nome\":\"$(printf '%s' "$nome" | _ci_texto_json)\",\"ok\":$([ "$okv" = 1 ] && echo true || echo false)}"
      sep=","
    done
    tmp="$dir/.ultimo.$$.tmp"
    printf '{"gerado_em":"%s","head":"%s","ok":%d,"falha":%d,"linha_final":"%s","passos":[%s]}\n' \
      "$gerado" "$head" "$ok" "$falhas" "$(printf '%s' "$linha" | _ci_texto_json)" "$passos" > "$tmp" \
      && mv -f "$tmp" "$dir/ultimo.json"
  } >/dev/null 2>&1
  return 0
}
# Progresso em cada linha (Regra 0, decisão do Humano 18/11/2026): "[n/total · tempo decorrido]". O total não é número
# fixo: _ci_passos() roda uma vez em modo de contagem (CI_CONTANDO=1, sem executar comando nenhum) e conta as chamadas.
_ci_marca() {
  local n="$1" total="$2" seg="$3"
  printf '[%s/%s · %dm%02ds]' "$n" "$total" $((seg / 60)) $((seg % 60))
}
# Roda o passo, imprime OK/FALHA com o progresso e guarda o resultado. Em modo de contagem só responde "." (uma linha por chamada).
passo() {
  local nome="$1" marca ok=0
  shift
  if [ "${CI_CONTANDO:-0}" = 1 ]; then echo "."; return 0; fi
  CI_N=$((CI_N + 1))
  # Regra 0 (revisão 23/11): o passo anuncia que começou; a linha OK/FALHA sai ao terminar.
  echo "  ... [$CI_N/$CI_TOTAL] $nome"
  if "$@" >"$TMP/saida.txt" 2>&1; then ok=1; fi
  # o tempo é medido quando o passo TERMINA: a linha sai nesse instante, e o tempo tem de ser o dele
  marca="$(_ci_marca "$CI_N" "$CI_TOTAL" "$(( $(date +%s) - CI_INICIO ))")"
  if [ "$ok" = 1 ]; then echo "OK    $marca $nome"; CI_PASSOS+=("$nome|1")
  else echo "FALHA $marca $nome"; tail -5 "$TMP/saida.txt" | sed 's/^/        /'; FALHAS=$((FALHAS+1)); CI_PASSOS+=("$nome|0"); fi
}
if [ "${BASH_SOURCE[0]}" != "$0" ]; then return 0; fi
# set -u só na execução (R4, 17/11/2026): dar source para testar as funções não muda as opções do shell de quem chamou.
set -u

RAIZ="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$RAIZ" || exit 1
PYTEST="${PYTEST:-$(command -v pytest || true)}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FALHAS=0
CI_N=0
CI_TOTAL=0
CI_INICIO=0
CI_CONTANDO=0

if [ -z "$PYTEST" ]; then echo "FALHA pytest não encontrado (defina PYTEST=/caminho/pytest)"; exit 1; fi
# os ciclos SDD chamam "pytest" pelo nome: o diretório do binário precisa estar no PATH
PATH_ORIGINAL="$PATH"
export PATH="$(dirname "$PYTEST"):$PATH"

_ci_passos() {
passo "testes SDD (pytest)" "$PYTEST" -q -p no:cacheprovider redesign/sdd_flow/tests redesign/review_mesh redesign/project_kit redesign/evidence_ledger redesign/painel_operacional redesign/obsidian redesign/nova_versao/tests redesign/alexandria/tests redesign/metacognicao/tests redesign/corpo/tests redesign/conexoes/tests redesign/avaliacao/tests redesign/sentidos/tests redesign/confiabilidade/tests redesign/rotas/tests redesign/mvp_autoaprimoramento/tests redesign/nucleo-desenvolvimento/tests ferramentas/test_ferramentas.py redesign/router/test_seth_base.py redesign/router/test_rotas_locais.py
passo "gate de sincronia das specs (selftest)" python3 -I scripts/gate_spec_sync.py --selftest
passo "gate de sincronia das specs (antes dos ciclos, que regeneram o drift)" python3 -I scripts/gate_spec_sync.py
passo "ciclo SDD sobre o próprio sdd_flow" python3 redesign/sdd_flow/runner.py "$TMP/state.json" cycle redesign/sdd_flow/spec redesign/sdd_flow/spec/acceptance.json --scope redesign/sdd_flow
passo "ciclo SDD sobre a nova versão" python3 redesign/sdd_flow/runner.py "$TMP/state-nv.json" cycle redesign/nova_versao/spec redesign/nova_versao/spec/acceptance.json --scope redesign/nova_versao
passo "âncora dos componentes" python3 redesign/sdd_flow/anchor.py . redesign/sdd_flow redesign/project_kit redesign/review_mesh redesign/evidence_ledger redesign/painel_operacional redesign/nova_versao redesign/alexandria redesign/metacognicao redesign/corpo redesign/conexoes redesign/avaliacao redesign/sentidos redesign/nucleo-desenvolvimento
passo "gate de spec (núcleo de desenvolvimento)" python3 redesign/sdd_flow/spec_gate.py check redesign/nucleo-desenvolvimento/spec
for c in project_kit review_mesh evidence_ledger painel_operacional nova_versao alexandria metacognicao corpo conexoes avaliacao sentidos sincronia; do
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
passo "processo de aplicação: diff sem bloco gerado (selftest)" python3 -I scripts/equipe/diff_limpo.py --selftest
passo "processo de aplicação: número de MEMÓRIAS (selftest)" python3 -I scripts/equipe/numero_memorias.py --selftest
passo "processo de aplicação: trava de aplicação (selftest)" python3 -I scripts/equipe/trava.py --selftest
passo "egress: critério de em dia da compilação (testes, sem compilar)" python3 -I scripts/testar_egress_em_dia.py
passo "ganchos do git: sintaxe do shell (bash -n)" bash -c 'for h in .githooks/*; do head -1 "$h" | grep -q "^#!.*sh" || continue; bash -n "$h" || exit 1; done'
passo "processo de aplicação: âncora staged devolvida ao HEAD (selftest, com o P-8 de verdade)" python3 -I scripts/equipe/ancora_indice.py --selftest
# verificar_workflows.py usa PyYAML. O python3 do PATH pode ser o venv do uv, sem PyYAML (medido em 16/11/2026:
# os dois passos de workflows falhavam com "PyYAML ausente"). Sem PY_YAML definido, usa /usr/bin/python3 quando
# ele existe e importa yaml; senão, python3. Se nenhum tiver PyYAML, o passo falha fechado, de propósito.
if [ -z "${PY_YAML:-}" ]; then
  PY_YAML=python3
  if [ -x /usr/bin/python3 ] && /usr/bin/python3 -c 'import yaml' >/dev/null 2>&1; then PY_YAML=/usr/bin/python3; fi
fi
passo "workflows: YAML válido e sem chave repetida (selftest)" "$PY_YAML" -I scripts/verificar_workflows.py --selftest
passo "workflows: .github/workflows do repositório" "$PY_YAML" -I scripts/verificar_workflows.py
passo "sincronia: testes (fonte única, porquês, início de sessão, maxTurns)" python3 scripts/testar_sincronia.py
passo "sob demanda: socket, proxy e backend (Laya, Ollaya)" python3 scripts/testar_sob_demanda.py
passo "sincronia: contexto de início de sessão (selftest)" python3 -I scripts/sessao_contexto.py --selftest
passo "sincronia: porquês (selftest)" python3 -I scripts/porques.py --selftest
passo "sincronia: verificador de porquês (aviso na 1ª versão, sai 0)" python3 scripts/porques.py --verificar
passo "projeto índice: testes (pytest)" "$PYTEST" -q -p no:cacheprovider redesign/projeto_indice/tests
passo "projeto índice: destinos do PROJETO (verificar_destinos)" python3 redesign/projeto_indice/verificar_destinos.py
passo "projeto índice: teto do PROJETO (teto.py)" python3 redesign/projeto_indice/teto.py
passo "projeto índice: ESTADO.md em dia (gerar_estado --verificar)" python3 scripts/gerar_estado.py --verificar
passo "ci: progresso e contagem dos passos (testes)" python3 -I scripts/testar_ci_progresso.py

# --- Job suite-adversarial (.github/workflows/perimetro.yml): os mesmos comandos, na mesma ordem, com os mesmos flags.
# Sem sudo, sem rede e sem serviço. Usa o python do sistema (PY_SISTEMA), não o do venv do uv (sem os pacotes do sistema).
# Sem segredo: o token interno aponta para um arquivo que não existe dentro de $TMP, como no runner do GitHub, para
# que nenhum passo desta seção leia o token real do Humano.
if [ -x /usr/bin/python3 ]; then PY_SISTEMA=/usr/bin/python3; else PY_SISTEMA="$(command -v python3)"; fi
export AGATA_TOKEN_INTERNO_PATH="$TMP/token-ausente"
# O perímetro chama "python3" pelo nome. Medido em 16/11/2026: com o PATH do venv do uv na frente, o agregado falha
# (ImportError de cryptography e yaml, 60 ok e 1 falha). Por isso o diretório do python do sistema vai na frente do PATH
# só para este passo; o PATH original (sem o venv do uv) fica como segundo critério.
passo "suite adversarial: controles (testar_perimetro.sh)" env PATH="$(dirname "$PY_SISTEMA"):$PATH_ORIGINAL" bash scripts/testar_perimetro.sh
passo "suite adversarial: selftest auditoria do turno (Seth)" env SETH_REPO="$RAIZ" "$PY_SISTEMA" redesign/router/auditoria_turno.py --selftest
passo "suite adversarial: selftest gateway da Seth" env SETH_REPO="$RAIZ" "$PY_SISTEMA" redesign/router/seth_gateway.py --selftest
passo "suite adversarial: selftest Conselho remoto" env SETH_REPO="$RAIZ" "$PY_SISTEMA" scripts/conselho_remoto.py --selftest
passo "suite adversarial: selftest registro de pedidos" env SETH_REPO="$RAIZ" "$PY_SISTEMA" -I redesign/router/registro_pedidos.py --selftest
passo "suite adversarial: selftest benchmark de roteamento" env SETH_REPO="$RAIZ" "$PY_SISTEMA" -I scripts/benchmark_roteamento.py --selftest
passo "suite adversarial: benchmark: locais e privacidade (testes)" env SETH_REPO="$RAIZ" "$PY_SISTEMA" -I scripts/testar_benchmark_roteamento.py
passo "suite adversarial: porta de entrada de modelo (testes)" "$PYTEST" -q -p no:cacheprovider scripts/testar_porta_entrada.py
passo "suite adversarial: lançador agata-run com Landlock (testes)" "$PYTEST" -q -p no:cacheprovider scripts/test_agata_run.py redesign/mcp/test_landlock.py
passo "suite adversarial: selftest queda por elo" env SETH_REPO="$RAIZ" "$PY_SISTEMA" -I scripts/queda_por_elo.py --selftest
passo "suite adversarial: selftest sombra de capacidade" env SETH_REPO="$RAIZ" "$PY_SISTEMA" -I redesign/router/sombra_capacidade.py --selftest
passo "suite adversarial: selftest sombra nova versão" env SETH_REPO="$RAIZ" "$PY_SISTEMA" -I redesign/router/sombra_nova_versao.py --selftest
passo "suite adversarial: selftest nv (nova versão)" env SETH_REPO="$RAIZ" "$PY_SISTEMA" -I redesign/nova_versao/nv.py --selftest
passo "suite adversarial: selftest busca de texto" env SETH_REPO="$RAIZ" "$PY_SISTEMA" -I scripts/busca_texto.py --selftest
passo "suite adversarial: selftest integralidade P-8" "$PY_SISTEMA" -I scripts/p8_integral.py --selftest
passo "suite adversarial: testes verificar P-8 em PR" "$PY_SISTEMA" -I scripts/testar_p8_verificar_pr.py
passo "suite adversarial: selftest painel de estado" "$PY_SISTEMA" -I scripts/painel_estado.py --selftest
passo "suite adversarial: selftest limpa emoji" "$PY_SISTEMA" -I redesign/router/limpa_emoji.py --selftest
passo "suite adversarial: selftest capivara de capacidades" "$PY_SISTEMA" -I scripts/capivara_capacidades.py --selftest
passo "suite adversarial: selftest pesquisa de modelos gratuitos" "$PY_SISTEMA" -I scripts/pesquisar_modelos_gratuitos.py --selftest
passo "suite adversarial: selftest verificar cofre" "$PY_SISTEMA" -I scripts/verificar_cofre.py --selftest
passo "suite adversarial: selftest cifrar recuperação" "$PY_SISTEMA" -I scripts/cifrar_recuperacao.py --selftest
passo "suite adversarial: selftest verificar expurgo" "$PY_SISTEMA" -I scripts/verificar_expurgo.py --selftest
passo "suite adversarial: selftest seth golden" "$PY_SISTEMA" -I scripts/seth_golden.py --selftest
passo "suite adversarial: selftest seth autodev" "$PY_SISTEMA" -I scripts/seth_autodev.py --selftest
passo "suite adversarial: selftest janela de manutenção" "$PY_SISTEMA" -I scripts/janela_manutencao.py --selftest
passo "suite adversarial: testes da janela de recuperação" "$PY_SISTEMA" -I scripts/testar_janela_recuperacao.py
passo "suite adversarial: selftest equipe" "$PY_SISTEMA" -I scripts/equipe/equipe.py --selftest
passo "suite adversarial: testes dos auxiliares da equipe" "$PY_SISTEMA" -I scripts/equipe/testar_auxiliares.py
passo "suite adversarial: contrato de leitura de memória" "$PY_SISTEMA" -I scripts/testar_memoria_leitura.py
passo "suite adversarial: contrato da trava do escriba" "$PY_SISTEMA" -I scripts/testar_trava_escriba.py
passo "suite adversarial: contrato sem Goose ativo" "$PY_SISTEMA" -I scripts/testar_sem_goose_ativo.py
}

# Contagem e execução (Regra 0). A contagem roda _ci_passos sem executar nada; a execução real vem depois, com o total já sabido.
# CI_SO_CONTAR=1 (testes) imprime só o total e sai, sem gravar o resumo.
CI_CONTANDO=1
CI_TOTAL="$(_ci_passos | grep -c '^\.$')"
CI_CONTANDO=0
if [ "${CI_SO_CONTAR:-0}" = 1 ]; then echo "$CI_TOTAL"; exit 0; fi
CI_INICIO="$(date +%s)"
_ci_passos
if [ "$CI_N" -ne "$CI_TOTAL" ]; then echo "AVISO: o CI rodou $CI_N passo(s), mas a contagem previa $CI_TOTAL -- conferir scripts/ci_sdd_local.sh"; fi

if [ "$FALHAS" -eq 0 ]; then LINHA_FINAL="CI LOCAL: TUDO OK"; else LINHA_FINAL="CI LOCAL: $FALHAS passo(s) falharam"; fi
_ci_gravar_ultimo "$LINHA_FINAL" || true
echo "$LINHA_FINAL"
if [ "$FALHAS" -eq 0 ]; then exit 0; fi
exit 1
