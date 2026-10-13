#!/usr/bin/env bash
# Aplica no Agent "Seth" do LibreChat (Mongo) os parâmetros versionados em
# agente-seth.json, ou só confere se batem (MEMÓRIAS (666)/(667)/(678)): janela,
# plugins sob demanda e as ferramentas do canon que ficam sempre (ferramentas_sempre). A janela de contexto
# vem dos perfis da Capivara (capivara_perfis.py --janela-agente), não de número fixo.
#   aplicar_agente_seth.sh            backup do documento + aplica + confere
#   aplicar_agente_seth.sh --conferir só confere; saída 1 se divergir
# Depois de aplicar, `docker restart librechat` (o LibreChat guarda o Agent em cache).
set -euo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JANELA="$(python3 "$AQUI/../../scripts/capivara_perfis.py" --janela-agente)"
CFG="$(python3 -c 'import json,sys; c=json.load(open(sys.argv[1])); c["model_parameters"]={"maxContextTokens": int(sys.argv[2])}; print(json.dumps(c))' "$AQUI/agente-seth.json" "$JANELA")"
MONGO=(docker exec -i librechat-mongodb mongosh --quiet LibreChat)

conferir() {
  "${MONGO[@]}" --eval "
    const c = $CFG;
    const a = db.agents.findOne({id: c.agent_id});
    if (!a) { print('FALHA: Agent ' + c.agent_id + ' não existe'); quit(1); }
    const erros = [];
    const mp = a.model_parameters || {};
    for (const [k, v] of Object.entries(c.model_parameters))
      if (mp[k] !== v) erros.push('model_parameters.' + k + ' = ' + mp[k] + ', esperado ' + v);
    for (const t of (c.ferramentas_sempre || []))
      if (!(a.tools || []).includes(t)) erros.push('ferramenta ' + t + ' não está no Agent (ferramentas_sempre)');
    const to = a.tool_options || {};
    for (const t of c.plugins_sob_demanda) {
      if (!(a.tools || []).includes(t)) erros.push('ferramenta ' + t + ' não está no Agent');
      else if (!(to[t] && to[t].defer_loading === true)) erros.push(t + ' sem defer_loading');
    }
    if (erros.length) { erros.forEach(e => print('DIVERGE: ' + e)); quit(1); }
    print('OK: Agent ' + c.agent_id + ' bate com agente-seth.json');"
}

if [ "${1:-}" = "--conferir" ]; then conferir; exit $?; fi

BK="$HOME/.cache/agata/agente-seth.bak-$(date +%Y%m%d-%H%M%S).json"
mkdir -p "$(dirname "$BK")"
"${MONGO[@]}" --eval "const c=$CFG; print(EJSON.stringify(db.agents.findOne({id: c.agent_id}), null, 1))" > "$BK"
echo "backup: $BK"
"${MONGO[@]}" --eval "
  const c = $CFG;
  const set = {};
  for (const [k, v] of Object.entries(c.model_parameters)) set['model_parameters.' + k] = v;
  for (const t of c.plugins_sob_demanda) set['tool_options.' + t + '.defer_loading'] = true;
  const r = db.agents.updateOne({id: c.agent_id},
    {\$set: set, \$addToSet: {tools: {\$each: (c.ferramentas_sempre || []).concat(c.plugins_sob_demanda)}}});
  print('alterados: ' + r.modifiedCount);"
conferir
