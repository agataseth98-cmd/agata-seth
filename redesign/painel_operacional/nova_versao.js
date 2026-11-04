// Nova versão do Agata no painel (Experimento GPT, lote 1): Alexandria, metacognição, corpo, orçamento.
// Arquivo externo por causa da CSP (script-src 'self'). Usa fetchJson/byId de prototipo.js.
// Todo texto vindo do servidor entra por textContent, nunca como HTML.
(function () {
  "use strict";
  const H = {"Content-Type": "application/json", Accept: "application/json"};
  const el = (tag, texto) => { const e = document.createElement(tag); if (texto !== undefined) e.textContent = texto; return e; };
  const li = (alvo, texto) => { const x = el("li", texto); byId(alvo).append(x); return x; };
  const limpar = (...ids) => ids.forEach((i) => byId(i) && byId(i).replaceChildren());
  const kpi = (alvo, rotulo, valor) => {
    const d = el("div"); d.className = "kpi";
    const l = el("div", rotulo); l.className = "label";
    const v = el("div", String(valor)); v.className = "value";
    d.append(l, v); byId(alvo).append(d);
  };
  let estado = null;

  async function ler() {
    try { estado = await fetchJson("/api/nova-versao/estado", {headers: {Accept: "application/json"}}); }
    catch (_) { estado = null; }
    return estado;
  }
  async function executar(acao, extra) {
    return fetchJson("/api/nova-versao/executar", {method: "POST", headers: H, body: JSON.stringify({acao, ...(extra || {})})}, 120000);
  }
  function confirmar(botao, rotulo, fazer) {
    if (!botao) return;
    let armado = false;
    botao.addEventListener("click", async () => {
      if (!armado) { armado = true; botao.textContent = "Confirmar: " + rotulo.toLowerCase(); return; }
      armado = false; botao.textContent = rotulo; botao.disabled = true;
      try { await fazer(); } finally { botao.disabled = false; }
    });
  }

  function alexandria() {
    limpar("nv-alex-kpis");
    const a = (estado && estado.alexandria) || {};
    const ind = a.indice || {};
    kpi("nv-alex-kpis", "Objetos no índice", ind.objetos || "não medido");
    kpi("nv-alex-kpis", "Trechos", ind.trechos || "não medido");
    kpi("nv-alex-kpis", "Skills catalogadas", ind.skills || "não medido");
    kpi("nv-alex-kpis", "Commit do acervo", ind.commit ? ind.commit.slice(0, 12) : "sem snapshot");
    byId("nv-alex-titulo").textContent = a.iniciado ? "Pastas criadas" : "Pastas ainda não criadas";
    byId("nv-alex-nota").textContent = ind.gerado_em ? "Índice gerado em " + ind.gerado_em + "." : "Sem índice: crie as pastas e indexe.";
  }
  function mostrarPacote(p) {
    limpar("nv-resultados");
    byId("nv-consulta-titulo").textContent = p.estado + (p.metodos.length ? " · " + p.metodos.join(" + ") : "");
    (p.avisos || []).forEach((a) => li("nv-resultados", "Aviso: " + a));
    (p.resultados || []).forEach((r) => {
      const ref = r.caminho + ":" + r.linha + (r.entrada !== null ? " (" + r.entrada + ")" : "");
      li("nv-resultados", "[" + r.metodo + "] " + ref + " · sha " + r.sha256.slice(0, 10) + (r.trecho ? " — " + r.trecho.slice(0, 160) : ""));
    });
  }
  function mostrarSkills(s) {
    limpar("nv-resultados");
    byId("nv-consulta-titulo").textContent = "Skills sugeridas (nada foi carregado)";
    (s.candidatos || []).forEach((c) => li("nv-resultados", "[" + c.motivo + "] " + c.nome + " · " + c.origem + " — " + (c.descricao || "").slice(0, 140)));
    if (!(s.candidatos || []).length) li("nv-resultados", "Nenhuma skill: não encontrado nesta busca.");
  }

  function metacognicao() {
    limpar("nv-sombra");
    const s = (estado && estado.sombra) || {registros: 0};
    byId("nv-sombra-titulo").textContent = s.registros + " registros";
    if (!s.ultimo) { li("nv-sombra", "Sem registro. A sombra liga com SETH_SOMBRA_NOVA_VERSAO=1 no gateway."); return; }
    const u = s.ultimo; const p = u.previo || {};
    li("nv-sombra", "Último: " + u.ts + " · rota " + u.rota + " · " + u.ms + " ms");
    li("nv-sombra", "Prévio: " + [p.tipo, p.atualidade, p.risco, p.privado ? "privado" : "sem dado pessoal"].join(" · "));
    li("nv-sombra", "Alexandria: " + ((u.alexandria || {}).estado || "não medido") + " · " + ((u.alexandria || {}).objetos || []).length + " objetos");
    li("nv-sombra", "Skills: " + ((u.skills || []).join(", ") || "nenhuma"));
  }

  function corpo() {
    limpar("nv-corpo-kpis", "nv-corpo-lista");
    const c = (estado && estado.corpo) || {};
    const sa = c.saude || {estado: "não medido"};
    kpi("nv-corpo-kpis", "Saúde", sa.estado);
    const f = c.fotografia;
    if (!f) { byId("nv-corpo-titulo").textContent = "Sem fotografia"; return; }
    const r = f.recursos || {};
    kpi("nv-corpo-kpis", "Disco livre", r.disco_livre_pct === null ? "não medido" : r.disco_livre_pct + "%");
    kpi("nv-corpo-kpis", "Memória livre", r.memoria_disponivel_pct === null ? "não medido" : r.memoria_disponivel_pct + "%");
    kpi("nv-corpo-kpis", "Temperatura máx.", r.temperatura_max_c === null ? "não medido" : r.temperatura_max_c + " °C");
    byId("nv-corpo-titulo").textContent = "Fotografia de " + f.quando + " (revalidar até " + f.revalidar_ate + ")";
    (sa.motivos || []).forEach((m) => li("nv-corpo-lista", "Motivo: " + m));
    Object.entries(f.servicos || {}).forEach(([u, s]) => li("nv-corpo-lista", u + ": " + s));
  }

  function orcamento() {
    const o = (estado && estado.orcamento) || null;
    if (o) {
      byId("nv-orc-local").checked = !!o.provedores.local;
      byId("nv-orc-gratuito").checked = !!o.provedores.gratuito;
      byId("nv-orc-assinatura").checked = !!o.provedores.assinatura;
      byId("nv-orc-pago").checked = !!o.provedores.pago;
      byId("nv-orc-chamadas").value = o.max_chamadas; byId("nv-orc-tokens").value = o.max_tokens;
      byId("nv-orc-timeout").value = o.timeout_s; byId("nv-orc-reais").value = o.teto_reais;
    }
    limpar("nv-eventos");
    const ev = (estado && estado.eventos) || [];
    byId("nv-eventos-titulo").textContent = ev.length + " últimos eventos · ledger " + (estado && estado.ledger_ok === true ? "íntegro" : "não verificado");
    ev.slice().reverse().forEach((e) => li("nv-eventos", e.timestamp + " · " + e.componente + " · " + e.kind + " · " + e.status + " · " + e.source));
  }


  function conexoes() {
    limpar("nv-con-lista", "nv-red-lista");
    const cs = (estado && estado.conexoes) || [];
    byId("nv-con-titulo").textContent = cs.length + " provedores · gasto estimado R$ " + ((estado && estado.gasto_reais) || 0).toFixed(4);
    const sel = byId("nv-api-provedor"); const atual = sel.value; sel.replaceChildren();
    cs.forEach((c) => {
      const m = c.modos || {}; const partes = [];
      if (m.navegador) partes.push("navegador: adaptador " + (m.navegador.adaptador || "não medido") + ", envio só com sua aprovação");
      if (m.cli) partes.push("programa: " + (m.cli.instalado ? "instalado" : "não instalado") + ", login " + m.cli.login + (m.cli.modelo ? ", modelo " + m.cli.modelo : ""));
      if (m.api) {
        const ch = m.api.chave || {};
        partes.push("API: " + (m.api.disponivel ? "pronta" : "falta " + m.api.falta.join(", ")) + " · chave " + (ch.no_cofre ? "no cofre desde " + ch.desde : ch.no_ambiente ? "no ambiente" : "ausente") + (m.api.modelo ? " · modelo " + m.api.modelo : ""));
        const o = document.createElement("option"); o.value = c.id; o.textContent = c.nome; sel.append(o);
      }
      li("nv-con-lista", c.nome + (c.origem === "local" ? " (adicionado por você)" : "") + " — " + partes.join(" | "));
    });
    if (atual) sel.value = atual;
    const tr = (estado && estado.teste_rotas) || {};
    const j = tr.job || {}; const u = tr.ultimo;
    byId("nv-red-titulo").textContent = j.estado === "rodando" ? "Testando…" : u ? "Último teste " + u.run_id + " · " + u.estado + (u.obsoleto ? " (contexto mudou: revalidar)" : "") : "Sem teste";
    if (j.estado === "rodando") setTimeout(() => window.carregarNovaVersao("nv-conexoes"), 5000);
    if (u) Object.entries(u.rotas_que_passaram || {}).forEach(([cap, rs]) => li("nv-red-lista", cap + ": " + (rs.length ? rs.join(", ") : "nenhuma rota passou")));
    (tr.resultados || []).filter((r) => !r.passou).slice(0, 12).forEach((r) => li("nv-red-lista", "não passou · " + r.rota + " · " + r.capacidade + " · " + (r.falha_etapa || "resposta fora da prova") + (r.erro ? " — " + r.erro : "")));
  }
  const telas = {"nv-conexoes": conexoes, "nv-alexandria": alexandria, "nv-metacognicao": metacognicao, "nv-corpo": corpo, "nv-orcamento": orcamento};
  window.carregarNovaVersao = async function (nome) {
    await ler();
    if (!estado) { const t = {"nv-alexandria": "nv-alex-nota", "nv-metacognicao": "nv-sombra-titulo", "nv-corpo": "nv-corpo-titulo", "nv-orcamento": "nv-orc-nota", "nv-conexoes": "nv-con-titulo"}[nome]; if (t && byId(t)) byId(t).textContent = "Nova versão indisponível no servidor."; return; }
    (telas[nome] || (() => {}))();
  };

  confirmar(byId("nv-iniciar"), "Criar pastas e indexar", async () => {
    try { const r = await executar("iniciar"); byId("nv-alex-nota").textContent = "Indexado: " + r.resultado.objetos + " objetos."; }
    catch (_) { byId("nv-alex-nota").textContent = "Não foi possível (ocupado?)."; }
    window.carregarNovaVersao("nv-alexandria");
  });
  confirmar(byId("nv-indexar"), "Reindexar a partir do HEAD", async () => {
    try { const r = await executar("indexar"); byId("nv-alex-nota").textContent = "Reindexado: " + r.resultado.objetos + " objetos, " + r.resultado.mudaram + " mudaram."; }
    catch (_) { byId("nv-alex-nota").textContent = "Não foi possível (crie as pastas antes?)."; }
    window.carregarNovaVersao("nv-alexandria");
  });
  const consultar = (acao) => async () => {
    const q = byId("nv-consulta").value.trim(); if (!q) return;
    try {
      const r = await executar(acao, {consulta: q, semantica: byId("nv-semantica").value});
      acao === "consultar" ? mostrarPacote(r.resultado) : mostrarSkills(r.resultado);
    } catch (_) { limpar("nv-resultados"); li("nv-resultados", "Sem resposta: índice ausente ou servidor ocupado."); }
  };
  if (byId("nv-consultar")) byId("nv-consultar").addEventListener("click", consultar("consultar"));
  if (byId("nv-skills")) byId("nv-skills").addEventListener("click", consultar("skills"));
  if (byId("nv-classificar")) byId("nv-classificar").addEventListener("click", async () => {
    const q = byId("nv-pedido").value.trim(); if (!q) return;
    limpar("nv-classificacao");
    try {
      const r = (await executar("classificar", {consulta: q})).resultado;
      li("nv-classificacao", "Tipo " + r.tipo + " · " + r.atualidade + " · risco " + r.risco + (r.privado ? " · dado pessoal" : ""));
      r.estrategia.forEach((e) => li("nv-classificacao", "Estratégia: " + e));
      if (r.problema_ambiguo) li("nv-classificacao", "\"Problema\" é ambíguo: distinguir " + r.problema_ambiguo.join(", "));
      if (r.limite_interacao) li("nv-classificacao", "Limite combinado: " + r.limite_interacao.restantes + " de " + r.limite_interacao.declarado + " restantes");
    } catch (_) { li("nv-classificacao", "Não foi possível classificar."); }
  });
  confirmar(byId("nv-fotografar"), "Fotografar agora", async () => {
    try { await executar("fotografar"); } catch (_) { byId("nv-corpo-titulo").textContent = "Não foi possível fotografar."; }
    window.carregarNovaVersao("nv-corpo");
  });
  confirmar(byId("nv-orc-salvar"), "Salvar orçamento", async () => {
    const n = (id) => Number(byId(id).value);
    const orc = {provedores: {local: byId("nv-orc-local").checked, gratuito: byId("nv-orc-gratuito").checked, assinatura: byId("nv-orc-assinatura").checked, pago: byId("nv-orc-pago").checked},
      max_chamadas: n("nv-orc-chamadas"), max_tokens: n("nv-orc-tokens"), timeout_s: n("nv-orc-timeout"), teto_reais: n("nv-orc-reais")};
    try { const r = await executar("salvar_orcamento", {orcamento: orc}); byId("nv-orc-nota").textContent = r.resultado.mudou ? "Salvo e registrado no ledger." : "Nada mudou."; }
    catch (_) { byId("nv-orc-nota").textContent = "Recusado: valor fora do limite."; }
    window.carregarNovaVersao("nv-orcamento");
  });
  const val = (id) => byId(id).value.trim();
  const nota = (id, t) => { byId(id).textContent = t; };
  confirmar(byId("nv-api-ajustar"), "Salvar modelo e tarifa", async () => {
    const pid = val("nv-api-provedor"); if (!pid) return;
    const corpo = {provedor: pid, api_modelo: val("nv-api-modelo") || null, cli_modelo: val("nv-cli-modelo") || null};
    if (val("nv-tar-entrada") || val("nv-tar-saida")) corpo.tarifa = {entrada_usd_mtok: Number(val("nv-tar-entrada")), saida_usd_mtok: Number(val("nv-tar-saida")), cambio_brl: Number(val("nv-tar-cambio")), fonte: val("nv-tar-fonte"), data: val("nv-tar-data")};
    try { await executar("ajustar_conexao", corpo); nota("nv-api-nota", "Ajuste salvo e registrado no ledger."); }
    catch (_) { nota("nv-api-nota", "Recusado: confira modelo, tarifa (com fonte e data) e câmbio."); }
    window.carregarNovaVersao("nv-conexoes");
  });
  confirmar(byId("nv-api-gravar"), "Gravar chave", async () => {
    const campo = byId("nv-api-chave"); const chave = campo.value; campo.value = "";
    const pid = val("nv-api-provedor"); if (!pid || !chave) return;
    try { await executar("gravar_chave", {provedor: pid, chave}); nota("nv-api-nota", "Chave gravada no cofre. Ela não volta para a tela."); }
    catch (_) { nota("nv-api-nota", "Recusada: formato ou prefixo não confere com o provedor."); }
    window.carregarNovaVersao("nv-conexoes");
  });
  confirmar(byId("nv-api-remover"), "Remover chave", async () => {
    const pid = val("nv-api-provedor"); if (!pid) return;
    try { const r = await executar("remover_chave", {provedor: pid}); nota("nv-api-nota", r.resultado.removida ? "Chave removida do cofre." : "Não havia chave no cofre."); }
    catch (_) { nota("nv-api-nota", "Não foi possível remover."); }
    window.carregarNovaVersao("nv-conexoes");
  });
  confirmar(byId("nv-add-salvar"), "Adicionar provedor", async () => {
    try { await executar("adicionar_provedor", {provedor: val("nv-add-id"), nome: val("nv-add-nome"), formato: val("nv-add-formato"), url: val("nv-add-url"), env: val("nv-add-env") || null, api_modelo: val("nv-add-modelo") || null}); nota("nv-add-nota", "Provedor adicionado. Agora grave a chave e a tarifa acima."); }
    catch (_) { nota("nv-add-nota", "Recusado: id, formato ou URL (só https) inválidos, ou id repetido."); }
    window.carregarNovaVersao("nv-conexoes");
  });
  confirmar(byId("nv-red-testar"), "Testar rotas permitidas pelo orçamento", async () => {
    try { await executar("testar_rotas", {}); nota("nv-red-nota", "Teste iniciado."); } catch (_) { nota("nv-red-nota", "Já há um teste rodando."); }
    window.carregarNovaVersao("nv-conexoes");
  });
  confirmar(byId("nv-red-cancelar"), "Cancelar teste", async () => {
    try { await executar("cancelar_teste", {}); nota("nv-red-nota", "Cancelamento pedido: nenhum item novo começa."); } catch (_) { nota("nv-red-nota", "Nada para cancelar."); }
  });
})();
