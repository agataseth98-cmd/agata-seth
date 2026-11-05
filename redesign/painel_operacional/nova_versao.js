// Nova versão do Agata no painel (Experimento GPT): Alexandria, metacognição, corpo, conexões, orçamento, avaliação.
// Arquivo externo por causa da CSP (script-src 'self'; style-src 'self': nada de style inline, só classes de nova_versao.css).
// Usa fetchJson/byId de prototipo.js. Todo texto vindo do servidor entra por textContent, nunca como HTML.
(function () {
  "use strict";
  const H = {"Content-Type": "application/json", Accept: "application/json"};
  // h("div", {class: "x", text: "y", title: "z"}, filho1, filho2…)
  const h = (tag, props, ...filhos) => {
    const e = document.createElement(tag);
    Object.entries(props || {}).forEach(([k, v]) => {
      if (v === undefined || v === null || v === false) return;
      if (k === "class") e.className = v; else if (k === "text") e.textContent = String(v); else e.setAttribute(k, v === true ? "" : String(v));
    });
    filhos.flat().forEach((f) => { if (f !== null && f !== undefined && f !== false) e.append(f instanceof Node ? f : document.createTextNode(String(f))); });
    return e;
  };
  const por = (id, ...filhos) => { const e = byId(id); if (e) e.replaceChildren(...filhos.flat()); return e; };
  const mostrar = (id, sim) => { const e = byId(id); if (e) e.hidden = !sim; };
  const nota = (id, texto, tipo) => { const e = byId(id); if (!e) return; e.textContent = texto; e.className = "nv-nota" + (tipo ? " " + tipo : ""); };
  const selo = (texto, tipo) => h("span", {class: "nv-selo " + (tipo || ""), text: texto});
  const kpi = (rotulo, valor, cor, sub) => h("div", {class: "kpi " + (cor || "")}, h("div", {class: "label", text: rotulo}),
    h("div", {class: "value", text: valor === null || valor === undefined || valor === "" ? "não medido" : valor}), sub ? h("div", {class: "note", text: sub}) : null);
  const dl = (pares) => pares.filter(Boolean).flatMap(([k, v]) => [h("dt", {text: k}), h("dd", {}, v instanceof Node ? v : String(v))]);
  const quando = (iso) => {
    if (!iso) return "—";
    const d = new Date(typeof iso === "number" ? iso * 1000 : iso);
    return isNaN(d) ? String(iso) : d.toLocaleString("pt-BR", {day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"});
  };
  const curta = (r) => String(r || "").replace(/^ollama-local\//, "local/").replace(/:latest$/, "");
  const pct = (x) => (x === null || x === undefined ? "—" : Math.round(x * 100) + "%");
  let estado = null;

  async function ler() {
    try { estado = await fetchJson("/api/nova-versao/estado", {headers: {Accept: "application/json"}}); }
    catch (_) { estado = null; }
    return estado;
  }
  async function executar(acao, extra) {
    return fetchJson("/api/nova-versao/executar", {method: "POST", headers: H, body: JSON.stringify({acao, ...(extra || {})})}, 120000);
  }
  const motivoErro = (e) => {
    const m = String((e && e.message) || "");
    if (m.includes("429")) return "ocupado: outra ação ou rodada está em andamento";
    if (m.includes("409")) return "índice ausente: crie as pastas e indexe";
    if (m.includes("403")) return "ainda não permitido";
    if (m.includes("400")) return "recusado: valor fora do contrato";
    return "sem resposta do servidor";
  };
  // ação com efeito: 1º clique arma (botão fica dourado), 2º confirma; desarma sozinho em 6 s
  function confirmar(botao, fazer) {
    if (!botao) return;
    const rotulo = botao.textContent;
    let timer = null;
    const desarmar = () => { botao.dataset.armado = ""; botao.textContent = rotulo; clearTimeout(timer); };
    botao.addEventListener("click", async () => {
      if (botao.dataset.armado !== "1") {
        botao.dataset.armado = "1"; botao.textContent = "Confirmar: " + rotulo.toLowerCase();
        timer = setTimeout(desarmar, 6000); return;
      }
      desarmar(); botao.disabled = true;
      try { await fazer(); } finally { botao.disabled = false; }
    });
  }
  const recarregar = (nome) => window.carregarNovaVersao(nome);

  // ---------------------------------------------------------------- Alexandria
  function alexandria() {
    const a = (estado && estado.alexandria) || {};
    const ind = a.indice || {};
    por("nv-alex-kpis", kpi("Objetos no índice", ind.objetos, "teal"), kpi("Trechos", ind.trechos),
      kpi("Skills catalogadas", ind.skills, "violet"), kpi("Commit do acervo", ind.commit ? ind.commit.slice(0, 10) : "sem snapshot", "gold"));
    byId("nv-alex-titulo").textContent = ind.gerado_em ? "Índice pronto" : a.iniciado ? "Pastas criadas, sem índice" : "Ainda não iniciado";
    por("nv-alex-dl", dl([
      ["situação", ind.gerado_em ? selo("pronto", "ok") : selo("sem índice", "aviso")],
      ["gerado em", quando(ind.gerado_em)],
      ["busca por texto", "SQLite FTS5, sem diferença de acento"],
      ["snapshots", (a.snapshots || []).join(", ") || "nenhum"],
      ["onde mora", "~/.cache/agata/nova-versao (derivado, reconstruível)"],
    ]));
  }
  function mostrarPacote(p) {
    byId("nv-consulta-titulo").textContent = p.estado === "encontrado" ? p.resultados.length + " fontes · " + p.metodos.join(" + ") : "Não encontrado nesta busca";
    por("nv-avisos", (p.avisos || []).map((a) => h("div", {class: "nv-aviso", text: a})));
    const rot = {lexico: ["texto", "ok"], relacao: ["citada por", "neutro"], semantica: ["sentido", "aviso"]};
    por("nv-resultados", (p.resultados || []).map((r) => {
      const [txt, tipo] = rot[r.metodo] || [r.metodo, ""];
      return h("li", {class: "nv-item"},
        h("div", {class: "nv-item-topo"}, selo(txt, tipo), h("span", {class: "nv-ref", text: r.caminho + ":" + r.linha + (r.entrada !== null ? "  (" + r.entrada + ")" : "")}),
          h("span", {class: "nv-sha", text: "sha " + r.sha256.slice(0, 10) + " · " + r.editorial_status}),
          (r.corrigida_por || []).length ? selo("corrigida por (" + r.corrigida_por.join("), (") + ")", "aviso") : null),
        r.trecho ? h("p", {text: r.trecho.slice(0, 280)}) : null);
    }));
    mostrar("nv-resultados-vazio", !(p.resultados || []).length);
    byId("nv-resultados-vazio").textContent = "Não encontrado nesta busca. Isso não prova que não existe.";
  }
  function mostrarSkills(s) {
    byId("nv-consulta-titulo").textContent = "Skills sugeridas (nenhuma foi carregada)";
    por("nv-avisos");
    por("nv-resultados", (s.candidatos || []).map((c) => h("li", {class: "nv-item"},
      h("div", {class: "nv-item-topo"}, selo(c.motivo, c.motivo === "mencionada" ? "ok" : "neutro"), h("span", {class: "nv-ref", text: c.nome}), h("span", {class: "nv-sha", text: c.origem})),
      h("p", {text: (c.descricao || "").slice(0, 200)}))));
    mostrar("nv-resultados-vazio", !(s.candidatos || []).length);
    byId("nv-resultados-vazio").textContent = "Nenhuma skill: não encontrado nesta busca.";
  }

  // ---------------------------------------------------------------- Metacognição
  function metacognicao() {
    const s = (estado && estado.sombra) || {registros: 0};
    const u = s.ultimo; const p = (u && u.previo) || {};
    por("nv-meta-kpis", kpi("Registros na sombra", s.registros || 0, "teal"), kpi("Último tipo", u ? p.tipo : "—"),
      kpi("Risco", u ? p.risco : "—", p.risco === "alto" ? "rose" : "gold"), kpi("Rota", u ? u.rota : "—", "violet"));
    mostrar("nv-sombra-vazio", !u);
    por("nv-sombra", u ? dl([["quando", quando(u.ts)], ["rota", u.rota + " · " + u.ms + " ms"],
      ["prévio", [p.tipo, p.atualidade, p.privado ? "dado pessoal" : "sem dado pessoal"].join(" · ")],
      ["Alexandria", ((u.alexandria || {}).estado || "não medido") + " · " + ((u.alexandria || {}).objetos || []).length + " objetos"],
      ["skills", (u.skills || []).join(", ") || "nenhuma"]]) : []);
  }

  // ---------------------------------------------------------------- Corpo
  function corpo() {
    const c = (estado && estado.corpo) || {};
    const sa = c.saude || {estado: "não medido"};
    const f = c.fotografia; const r = (f && f.recursos) || {};
    const corSaude = {normal: "teal", pressionado: "gold", degradado: "rose", isolado: "rose", indisponivel: "rose"}[sa.estado] || "";
    const v = (x, suf) => (x === null || x === undefined ? null : x + suf);
    por("nv-corpo-kpis", kpi("Saúde", sa.estado, corSaude, f ? "fotografia de " + quando(f.quando) : null),
      kpi("Disco livre", v(r.disco_livre_pct, "%")), kpi("Memória livre", v(r.memoria_disponivel_pct, "%")), kpi("Temperatura máx.", v(r.temperatura_max_c, " °C"), "gold"));
    mostrar("nv-corpo-vazio", !f);
    if (!f) { por("nv-corpo-lista"); por("nv-corpo-motivos"); return; }
    byId("nv-corpo-titulo").textContent = "Serviços · revalidar até " + quando(f.revalidar_ate);
    por("nv-corpo-motivos", (sa.motivos || []).map((m) => h("div", {class: "nv-aviso", text: m})));
    por("nv-corpo-lista", Object.entries(f.servicos || {}).map(([u, s]) => h("div", {class: "service"}, h("span", {text: u.replace(/\.service$/, "")}),
      h("b", {class: s === "active" ? "" : "paused", text: s === "active" ? "ativo" : s === "inactive" ? "parado (sob demanda)" : s}))));
  }

  // ---------------------------------------------------------------- Conexões
  function caminho(nome, ok, texto, detalhe) {
    return h("div", {class: "nv-caminho"}, h("b", {text: nome}), h("div", {}, selo(texto, ok === true ? "ok" : ok === false ? "aviso" : "neutro"),
      detalhe ? h("small", {text: detalhe}) : null));
  }
  function conexoes() {
    const cs = (estado && estado.conexoes) || [];
    const tr = (estado && estado.teste_rotas) || {}; const j = tr.job || {}; const u = tr.ultimo;
    const orc = (estado && estado.orcamento) || {provedores: {}};
    const liberado = (m) => !!(m && m.disponivel && orc.provedores[m.categoria]);
    const prontas = cs.reduce((n, c) => n + ["cli", "api"].filter((m) => liberado(c.modos[m])).length, 0);
    por("nv-con-kpis", kpi("Provedores", cs.length, "teal"), kpi("Caminhos prontos", prontas, prontas ? "teal" : "gold"),
      kpi("Gasto estimado", "R$ " + ((estado && estado.gasto_reais) || 0).toFixed(2), "", "teto R$ " + (orc.teto_reais || 0)),
      kpi("Último teste", u ? quando(u.quando) : "nenhum", "violet", u ? u.estado : null));
    const sel = byId("nv-api-provedor"); const atual = sel.value;
    sel.replaceChildren(...cs.filter((c) => c.modos.api).map((c) => h("option", {value: c.id, text: c.nome})));
    if (atual) sel.value = atual;
    por("nv-con-lista", cs.map((c) => {
      const m = c.modos || {}; const linhas = [];
      if (m.navegador) linhas.push(caminho("navegador", null, "você aprova cada envio", "adaptador " + (m.navegador.adaptador || "não medido") + " · Conselho em Rede"));
      if (m.cli) linhas.push(caminho("programa", liberado(m.cli),
        !m.cli.instalado ? "não instalado" : liberado(m.cli) ? "pronto" : m.cli.disponivel ? "instalado · desligado no orçamento" : "instalado",
        "login " + m.cli.login + (m.cli.modelo ? " · modelo " + m.cli.modelo : "") + " · categoria assinatura"));
      if (m.api) {
        const ch = m.api.chave || {};
        linhas.push(caminho("API", liberado(m.api), !m.api.disponivel ? "falta " + m.api.falta.join(", ") : liberado(m.api) ? "pronta" : "pronta · desligada no orçamento",
          "chave " + (ch.no_cofre ? "no cofre desde " + quando(ch.desde) : ch.no_ambiente ? "no ambiente" : "ausente") + (m.api.modelo ? " · modelo " + m.api.modelo : "")));
      }
      return h("div", {class: "nv-cartao"}, h("div", {class: "nv-cartao-topo"}, h("h3", {text: c.nome}), selo(c.origem === "local" ? "adicionado por você" : "catálogo", "neutro")), ...linhas);
    }));
    byId("nv-red-titulo").textContent = j.estado === "rodando" ? "Testando…" : u ? "Último teste · " + quando(u.quando) + (u.obsoleto ? " · contexto mudou, revalidar" : "") : "Testar rotas";
    if (j.estado === "rodando") setTimeout(() => recarregar("nv-conexoes"), 5000);
    const res = tr.resultados || [];
    const rotas = [...new Set(res.map((x) => x.rota))];
    mostrar("nv-red-wrap", rotas.length > 0);
    por("nv-red-lista", rotas.map((rota) => {
      const da = res.filter((x) => x.rota === rota);
      const cel = (cap) => { const x = da.find((y) => y.capacidade === cap); if (!x) return h("td", {text: "—"});
        return h("td", {title: x.erro || ""}, x.passou ? selo("passou", "ok") : selo(x.falha_etapa || "falhou", "erro")); };
      return h("tr", {}, h("td", {class: "mono", text: rota}), h("td", {text: da[0].categoria}), cel("conversa"), cel("formato"), cel("codigo"));
    }));
  }

  // ---------------------------------------------------------------- Orçamento
  function orcamento() {
    const o = (estado && estado.orcamento) || null;
    if (o) {
      ["local", "gratuito", "assinatura", "pago"].forEach((k) => { byId("nv-orc-" + k).checked = !!o.provedores[k]; });
      byId("nv-orc-chamadas").value = o.max_chamadas; byId("nv-orc-tokens").value = o.max_tokens;
      byId("nv-orc-timeout").value = o.timeout_s; byId("nv-orc-reais").value = o.teto_reais;
    }
    const ev = (estado && estado.eventos) || [];
    byId("nv-eventos-titulo").textContent = ev.length + " últimos eventos · ledger " + (estado && estado.ledger_ok === true ? "íntegro" : "não verificado");
    por("nv-eventos", ev.slice().reverse().map((e) => h("tr", {}, h("td", {class: "mono", text: quando(e.timestamp)}), h("td", {text: e.componente}),
      h("td", {text: e.kind}), h("td", {}, selo(e.status, ["ok", "concluida", "fixada", "revisado"].includes(e.status) ? "ok" : "neutro")), h("td", {class: "mono", text: e.source}))));
  }

  // ---------------------------------------------------------------- Avaliação
  const NOME_COND = {sem_contexto: "sem contexto", busca_texto: "busca por texto (atual)", alexandria: "Alexandria", alexandria_semantica: "Alexandria + sentido", alexandria_guarda: "Alexandria + guarda"};
  const corVeredito = (v) => (v === "melhora" ? "ok" : v === "piora" || v.startsWith("vetado") ? "erro" : v.startsWith("nao_conta") ? "neutro" : "aviso");
  let rotasCarregadas = false;
  async function carregarRotas() {
    try {
      const r = (await executar("rotas_disponiveis")).resultado.rotas;
      por("nv-run-rotas", r.length ? r.map((x) => h("label", {}, h("input", {type: "checkbox", value: x.rota, "data-rota": true}), x.rota + " · " + x.categoria))
        : [h("span", {class: "nv-sha", text: "nenhuma rota: ligue uma categoria no orçamento"})]);
      rotasCarregadas = true;
    } catch (e) { por("nv-run-rotas", h("span", {class: "nv-sha", text: motivoErro(e)})); }
  }
  function avaliacao() {
    const a = (estado && estado.avaliacao) || {};
    if (a.erro) { nota("nv-run-nota", "Conjunto com problema: " + a.erro, "erro"); return; }
    const res = a.reservado || {}; const pol = a.politica; const job = a.job || {};
    por("nv-ava-kpis", kpi("Desenvolvimento", (a.conjuntos || {}).dev, "teal", "no repositório"), kpi("Calibração", (a.conjuntos || {}).calibracao, "", "no repositório"),
      kpi("Reservado", res.tarefas || 0, res.revisado_por ? "teal" : "gold", res.revisado_por ? "revisado em " + quando(res.revisado_em) : "aguarda sua revisão"),
      kpi("Política", pol ? "margem " + pol.margem_minima : "não fixada", pol ? "violet" : "gold", pol ? "fixada em " + quando(pol.fixada_em) : null));
    por("nv-ava-passos",
      h("li", {class: pol ? "feito" : ""}, h("div", {}, "Fixar a política: margem mínima de ganho e tetos", h("small", {text: "Antes de ver resultado, para a régua não mudar depois."}))),
      h("li", {class: res.revisado_por ? "feito" : ""}, h("div", {}, "Revisar as 12 tarefas reservadas", h("small", {text: res.revisao_desatualizada ? "O conjunto mudou depois da sua revisão: revisar de novo." : "Escritas por " + (res.autores || []).join(", ") + "; o executor nunca vê o gabarito."}))),
      h("li", {}, h("div", {}, "Ligar no orçamento as categorias a testar", h("small", {text: "Local já vem ligado. Assinatura e pago consomem cota ou dinheiro."}))),
      h("li", {}, h("div", {}, "Rodar o desenvolvimento, depois o reservado", h("small", {text: "Com 12 tarefas o veredito tende a inconclusivo: é o limite honesto da amostra."}))));
    if (pol) { byId("nv-pol-margem").value = pol.margem_minima; byId("nv-pol-latencia").value = pol.teto_latencia_ms; byId("nv-pol-reais").value = pol.teto_reais; }
    byId("nv-pol-titulo").textContent = pol ? "Política fixada" : "Margem e tetos";
    byId("nv-res-titulo").textContent = res.revisado_por ? "Reservado revisado" : "Revisão do reservado";
    nota("nv-res-nota", (res.tarefas || 0) + " tarefas · " + Object.entries(res.por_grupo || {}).map(([g, n]) => g + " " + n).join(" · ") + (res.conjunto_hash ? " · " + res.conjunto_hash.slice(0, 19) : ""));
    if (!byId("nv-run-condicoes").childElementCount) {
      por("nv-run-condicoes", (a.condicoes || []).map((c) => h("label", {}, h("input", {type: "checkbox", value: c, "data-cond": true, checked: c !== "sem_contexto"}), NOME_COND[c] || c)));
    }
    if (!rotasCarregadas) carregarRotas();
    const rodando = job.estado === "rodando";
    byId("nv-run-titulo").textContent = rodando ? "Rodando " + (job.tipo === "recuperacao" ? "a medição da busca" : "a avaliação") + "…" : "Nova rodada";
    if (rodando) setTimeout(() => recarregar("nv-avaliacao"), 5000);
    else if (job.estado === "falhou") nota("nv-run-nota", "A última rodada falhou: " + (job.detalhe || ""), "erro");
    const runs = a.execucoes || [];
    const sel = byId("nv-out-run"); const atual = sel.value;
    sel.replaceChildren(...runs.map((r) => h("option", {value: r.run_id, text: quando(r.inicio) + " · " + r.split + " · " + (r.resumo && r.resumo.por_metodo ? "busca" : "avaliação")})));
    if (atual && runs.some((r) => r.run_id === atual)) sel.value = atual;
    mostrar("nv-out-vazio", !runs.length);
    const run = runs.find((r) => r.run_id === sel.value) || runs[0];
    mostrarRodada(run);
  }
  function tabela(cab, linhas) {
    return h("div", {class: "nv-tabela-wrap"}, h("table", {class: "nv-tabela"}, h("thead", {}, h("tr", {}, cab.map((c) => h("th", {text: c})))),
      h("tbody", {}, linhas)));
  }
  function mostrarRodada(run) {
    if (!run) { por("nv-out"); return; }
    const r = run.resumo || {};
    byId("nv-out-titulo").textContent = "Rodada " + quando(run.inicio) + " · " + run.split + " · " + (run.estado || "");
    const blocos = [];
    if (r.por_metodo) {   // medição da busca, sem modelo
      blocos.push(tabela(["método", "forma", "n", "precisão@k", "recall@k", "MRR"], Object.entries(r.por_metodo).flatMap(([m, v]) =>
        ["exata", "parafrase"].map((f) => h("tr", {}, h("td", {text: m}), h("td", {text: f}), h("td", {class: "num", text: v[f].n}),
          h("td", {class: "num", text: pct(v[f].p_at_k)}), h("td", {class: "num", text: pct(v[f].recall_at_k)}), h("td", {class: "num", text: v[f].mrr === null ? "—" : v[f].mrr}))))));
      blocos.push(h("p", {class: "nv-nota", text: r.nota || ""}));
      por("nv-out", blocos); return;
    }
    blocos.push(h("div", {class: "panel-kicker nv-mt", text: "comparação com o caminho atual (busca por texto)"}));
    blocos.push(tabela(["rota", "candidata", "pares", "diferença", "intervalo 95%", "veredito"], (r.comparacoes || []).map((c) => h("tr", {},
      h("td", {class: "mono", text: curta(c.rota)}), h("td", {text: NOME_COND[c.candidata] || c.candidata}), h("td", {class: "num", text: c.n_pares}),
      h("td", {class: "num", text: c.diferenca_media === null ? "—" : (c.diferenca_media > 0 ? "+" : "") + pct(c.diferenca_media)}),
      h("td", {class: "num", text: c.ic95 ? pct(c.ic95[0]) + " a " + pct(c.ic95[1]) : "—"}), h("td", {}, selo(c.veredito + (c.falhas_criticas && c.falhas_criticas_baseline ? " · o atual também falha" : ""), corVeredito(c.veredito)))))));
    blocos.push(h("div", {class: "panel-kicker nv-mt", text: "por dimensão (F fidelidade · A aplicação · Suporte · K correção · R resistência · O operação)"}));
    blocos.push(tabela(["condição", "rota", "F", "A", "Suporte", "K", "R", "O", "cobertura", "risco", "críticas", "falha de infra"],
      Object.values(r.por_condicao || {}).map((p) => h("tr", {}, h("td", {text: NOME_COND[p.condicao] || p.condicao}), h("td", {class: "mono", text: curta(p.rota) + (p.contaminado ? " *" : "")}),
        ...["F", "A", "Suporte", "K", "R", "O"].map((d) => h("td", {class: "num", text: pct(p.dimensoes[d])})),
        h("td", {class: "num", text: pct(p.C.cobertura)}), h("td", {class: "num", text: pct(p.C.risco)}),
        h("td", {class: "num"}, p.falhas_criticas ? selo(String(p.falhas_criticas), "erro") : "0"),
        h("td", {class: "mono", text: Object.entries(p.falhas_infra || {}).map(([k, v]) => k + " " + v).join(", ") || "—"})))));
    if (Object.keys(r.mecanicos || {}).length) blocos.push(h("p", {class: "nv-nota", text: "Mecânicos: " + Object.entries(r.mecanicos).map(([k, v]) => k + " " + v).join(" · ")}));
    blocos.push(h("p", {class: "nv-nota", text: "* rota da família do autor das tarefas: não conta para o veredito. " + (r.nota || "")}));
    const det = h("div", {id: "nv-out-respostas"});
    const btn = h("button", {type: "button", class: "btn secondary", text: "Ver respostas para revisão"});
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      try {
        const ls = (await executar("ver_execucao", {run_id: run.run_id})).resultado.linhas;
        det.replaceChildren(...ls.filter((x) => x.condition !== "mecanico").map((x) => h("details", {class: "nv-detalhe"},
          h("summary", {}, selo(x.outcome, x.outcome === "passou" ? "ok" : x.outcome === "nao_rodou" ? "neutro" : "erro"), h("span", {class: "nv-ref", text: x.task_id}),
            h("span", {class: "nv-sha", text: (NOME_COND[x.condition] || x.condition) + " · " + curta(x.rota) + (x.failure_stage ? " · " + x.failure_stage : "") + (x.critical_failure ? " · FALHA CRÍTICA" : "")})),
          h("pre", {text: x.resposta || x.erro || "(sem resposta)"}))));
      } catch (e) { det.replaceChildren(h("p", {class: "nv-nota erro", text: motivoErro(e)})); }
      btn.disabled = false;
    });
    blocos.push(h("div", {class: "nv-acoes"}, btn), det);
    por("nv-out", blocos);
  }

  // ---------------------------------------------------------------- Sentidos
  function sentidos() {
    const s = (estado && estado.sentidos) || {};
    const o = s.ouvido || {}; const u = s.ultima_medicao; const job = ((estado && estado.avaliacao) || {}).job || {};
    const pm = (u && u.resumo && u.resumo.por_motor) || {};
    const lfm = pm["lfm3|limpo"]; const wh = pm["whisper|limpo"];
    por("nv-sen-kpis", kpi("Ouvido principal", o.principal || "—", "teal"), kpi("Erro do principal", lfm ? pct(lfm.wer) : null, "teal", "frases limpas"),
      kpi("Erro da reserva", wh && wh.wer !== null ? pct(wh.wer) : null, "gold", "Whisper"), kpi("Voz", "agata-last", "violet", "inalterada"));
    por("nv-sen-dl", dl([["principal", o.principal || "—"], ["reserva", o.reserva || "—"], ["conversa no LibreChat", o.servidor || "—"], ["voz", o.voz || "—"],
      ["última medição", u ? quando(u.inicio) + " · " + (u.estado || "") : "nenhuma"]]));
    const rodando = job.estado === "rodando" && job.tipo === "ouvido";
    byId("nv-sen-titulo").textContent = rodando ? "Medindo o ouvido…" : "Fala → texto";
    if (rodando) setTimeout(() => recarregar("nv-sentidos"), 5000);
    const linhas = Object.values(pm);
    mostrar("nv-sen-wrap", linhas.length > 0);
    por("nv-sen-lista", linhas.map((x) => h("tr", {}, h("td", {text: x.motor === "lfm3" ? "lfm3-audio" : "Whisper (reserva)"}), h("td", {text: x.condicao === "limpo" ? "limpo" : "com ruído"}),
      h("td", {class: "num", text: x.wer === null ? "não medido" : pct(x.wer)}), h("td", {class: "num", text: x.perfeitas === null ? "—" : x.perfeitas + "/20"}),
      h("td", {class: "num", text: x.tempo_mediano_s === null ? "—" : x.tempo_mediano_s.toFixed(2) + " s"}))));
  }

  const telas = {"nv-acervo": acervo, "nv-sentidos": sentidos, "nv-conexoes": conexoes, "nv-alexandria": alexandria, "nv-metacognicao": metacognicao, "nv-corpo": corpo, "nv-orcamento": orcamento, "nv-avaliacao": avaliacao};
  window.carregarNovaVersao = async function (nome) {
    await ler();
    if (!estado) { const pg = byId("page-" + nome); if (pg) { const k = pg.querySelector(".kpis"); if (k) k.replaceChildren(kpi("Nova versão", "indisponível", "rose", "o servidor não respondeu")); } return; }
    (telas[nome] || (() => {}))();
  };

  // ---------------------------------------------------------------- ações
  const val = (id) => byId(id).value.trim();
  confirmar(byId("nv-iniciar"), async () => {
    try { const r = await executar("iniciar"); nota("nv-alex-nota", "Indexado: " + r.resultado.objetos + " objetos.", "ok"); }
    catch (e) { nota("nv-alex-nota", motivoErro(e), "erro"); }
    recarregar("nv-alexandria");
  });
  confirmar(byId("nv-indexar"), async () => {
    nota("nv-alex-nota", "Reindexando…");
    try { const r = await executar("indexar"); nota("nv-alex-nota", "Reindexado: " + r.resultado.objetos + " objetos, " + r.resultado.mudaram + " mudaram.", "ok"); }
    catch (e) { nota("nv-alex-nota", motivoErro(e), "erro"); }
    recarregar("nv-alexandria");
  });
  const consultar = (acao) => async () => {
    const q = val("nv-consulta"); if (!q) return;
    try {
      const r = await executar(acao, {consulta: q, semantica: byId("nv-semantica").value});
      acao === "consultar" ? mostrarPacote(r.resultado) : mostrarSkills(r.resultado);
    } catch (e) { por("nv-resultados"); mostrar("nv-resultados-vazio", true); byId("nv-resultados-vazio").textContent = motivoErro(e); }
  };
  if (byId("nv-consultar")) byId("nv-consultar").addEventListener("click", consultar("consultar"));
  if (byId("nv-skills")) byId("nv-skills").addEventListener("click", consultar("skills"));
  if (byId("nv-consulta")) byId("nv-consulta").addEventListener("keydown", (e) => { if (e.key === "Enter") consultar("consultar")(); });
  const classificar = async () => {
    const q = val("nv-pedido"); if (!q) return;
    try {
      const r = (await executar("classificar", {consulta: q})).resultado;
      mostrar("nv-classificacao-vazio", false);
      por("nv-classificacao", dl([["tipo", selo(r.tipo, "neutro")], ["atualidade", r.atualidade], ["risco", selo(r.risco, r.risco === "alto" ? "erro" : r.risco === "medio" ? "aviso" : "ok")],
        ["dado pessoal", r.privado ? selo("sim", "aviso") : "não"], ["estratégia", r.estrategia.join(" · ")],
        r.problema_ambiguo ? ["\"problema\"", "ambíguo: distinguir " + r.problema_ambiguo.join(", ")] : null,
        r.limite_interacao ? ["limite combinado", r.limite_interacao.restantes + " de " + r.limite_interacao.declarado + " restantes"] : null]));
    } catch (e) { mostrar("nv-classificacao-vazio", true); byId("nv-classificacao-vazio").textContent = motivoErro(e); }
  };
  if (byId("nv-classificar")) byId("nv-classificar").addEventListener("click", classificar);
  if (byId("nv-pedido")) byId("nv-pedido").addEventListener("keydown", (e) => { if (e.key === "Enter") classificar(); });
  confirmar(byId("nv-fotografar"), async () => {
    try { await executar("fotografar"); } catch (e) { byId("nv-corpo-titulo").textContent = motivoErro(e); }
    recarregar("nv-corpo");
  });
  confirmar(byId("nv-orc-salvar"), async () => {
    const n = (id) => Number(byId(id).value);
    const orc = {provedores: {local: byId("nv-orc-local").checked, gratuito: byId("nv-orc-gratuito").checked, assinatura: byId("nv-orc-assinatura").checked, pago: byId("nv-orc-pago").checked},
      max_chamadas: n("nv-orc-chamadas"), max_tokens: n("nv-orc-tokens"), timeout_s: n("nv-orc-timeout"), teto_reais: n("nv-orc-reais")};
    try { const r = await executar("salvar_orcamento", {orcamento: orc}); nota("nv-orc-nota", r.resultado.mudou ? "Salvo e registrado no ledger." : "Nada mudou.", "ok"); rotasCarregadas = false; }
    catch (e) { nota("nv-orc-nota", motivoErro(e), "erro"); }
    recarregar("nv-orcamento");
  });
  confirmar(byId("nv-api-ajustar"), async () => {
    const pid = val("nv-api-provedor"); if (!pid) return;
    const corpo_ = {provedor: pid, api_modelo: val("nv-api-modelo") || null, cli_modelo: val("nv-cli-modelo") || null};
    if (val("nv-tar-entrada") || val("nv-tar-saida")) corpo_.tarifa = {entrada_usd_mtok: Number(val("nv-tar-entrada")), saida_usd_mtok: Number(val("nv-tar-saida")), cambio_brl: Number(val("nv-tar-cambio")), fonte: val("nv-tar-fonte"), data: val("nv-tar-data")};
    try { await executar("ajustar_conexao", corpo_); nota("nv-api-nota", "Ajuste salvo e registrado no ledger.", "ok"); }
    catch (_) { nota("nv-api-nota", "Recusado: confira modelo, tarifa (com fonte e data) e câmbio.", "erro"); }
    recarregar("nv-conexoes");
  });
  confirmar(byId("nv-api-gravar"), async () => {
    const campo = byId("nv-api-chave"); const chave = campo.value; campo.value = "";
    const pid = val("nv-api-provedor"); if (!pid || !chave) return;
    try { await executar("gravar_chave", {provedor: pid, chave}); nota("nv-api-nota", "Chave gravada no cofre. Ela não volta para a tela.", "ok"); }
    catch (_) { nota("nv-api-nota", "Recusada: formato ou prefixo não confere com o provedor.", "erro"); }
    recarregar("nv-conexoes");
  });
  confirmar(byId("nv-api-remover"), async () => {
    const pid = val("nv-api-provedor"); if (!pid) return;
    try { const r = await executar("remover_chave", {provedor: pid}); nota("nv-api-nota", r.resultado.removida ? "Chave removida do cofre." : "Não havia chave no cofre.", "ok"); }
    catch (e) { nota("nv-api-nota", motivoErro(e), "erro"); }
    recarregar("nv-conexoes");
  });
  confirmar(byId("nv-add-salvar"), async () => {
    try { await executar("adicionar_provedor", {provedor: val("nv-add-id"), nome: val("nv-add-nome"), formato: val("nv-add-formato"), url: val("nv-add-url"), env: val("nv-add-env") || null, api_modelo: val("nv-add-modelo") || null}); nota("nv-add-nota", "Provedor adicionado. Agora grave a chave e a tarifa ao lado.", "ok"); }
    catch (_) { nota("nv-add-nota", "Recusado: id, formato ou endereço (só https) inválidos, ou id repetido.", "erro"); }
    recarregar("nv-conexoes");
  });
  confirmar(byId("nv-red-testar"), async () => {
    try { await executar("testar_rotas", {}); nota("nv-red-nota", "Teste iniciado.", "ok"); } catch (e) { nota("nv-red-nota", motivoErro(e), "erro"); }
    recarregar("nv-conexoes");
  });
  confirmar(byId("nv-red-cancelar"), async () => {
    try { await executar("cancelar_teste", {}); nota("nv-red-nota", "Cancelamento pedido: nenhum item novo começa.", "ok"); } catch (e) { nota("nv-red-nota", motivoErro(e), "erro"); }
  });
  // avaliação
  confirmar(byId("nv-pol-salvar"), async () => {
    try { await executar("salvar_politica", {margem_minima: Number(val("nv-pol-margem")), teto_latencia_ms: Number(val("nv-pol-latencia")), teto_reais: Number(val("nv-pol-reais"))}); nota("nv-pol-nota", "Política fixada e registrada no ledger.", "ok"); }
    catch (e) { nota("nv-pol-nota", "Recusada: margem de 0 a 1, latência de 100 a 600000 ms, teto de 0 a 10000.", "erro"); }
    recarregar("nv-avaliacao");
  });
  if (byId("nv-res-ver")) byId("nv-res-ver").addEventListener("click", async () => {
    try {
      const r = (await executar("ver_reservado")).resultado;
      por("nv-res-lista", r.tarefas.map((t) => h("details", {class: "nv-detalhe"},
        h("summary", {}, selo(t.grupo, "neutro"), h("span", {class: "nv-ref", text: t.task_id}), h("span", {class: "nv-sha", text: t.caso || ""})),
        h("pre", {text: "PEDIDO: " + t.pedido + "\n\n" + (t.documentos || []).map((d) => "[" + d.id + "] (" + [d.origem, d.autoridade, d.data, d.estado, d.classification].filter(Boolean).join("; ") + ") " + d.texto).join("\n")
          + (t.mecanico ? "\nMECÂNICO: " + t.mecanico : "") + (t.relevantes ? "\nRELEVANTES: " + t.relevantes.join(", ") : "")
          + "\n\nCRITÉRIOS: " + JSON.stringify(t.criterios) + (t.criticos ? "\nCRÍTICOS: " + JSON.stringify(t.criticos) : "")}))));
    } catch (e) { nota("nv-res-nota", motivoErro(e), "erro"); }
  });
  confirmar(byId("nv-res-revisar"), async () => {
    try { await executar("revisar_reservado"); nota("nv-res-nota", "Revisão registrada para o conjunto atual.", "ok"); } catch (e) { nota("nv-res-nota", motivoErro(e), "erro"); }
    recarregar("nv-avaliacao");
  });
  confirmar(byId("nv-run-rodar"), async () => {
    const marcados = (sel) => [...document.querySelectorAll(sel)].filter((x) => x.checked).map((x) => x.value);
    const rotas = marcados("#nv-run-rotas input[data-rota]"); const conds = marcados("#nv-run-condicoes input[data-cond]");
    if (!rotas.length || !conds.length) { nota("nv-run-nota", "Marque ao menos uma rota e uma condição.", "erro"); return; }
    try {
      const r = (await executar("avaliar", {split: val("nv-run-split"), rotas, condicoes: conds, repeticoes: Number(val("nv-run-rep")) || 1})).resultado;
      nota("nv-run-nota", r.recusado ? "Ainda não: " + r.recusado + "." : "Rodada iniciada.", r.recusado ? "erro" : "ok");
    } catch (e) { nota("nv-run-nota", motivoErro(e), "erro"); }
    recarregar("nv-avaliacao");
  });
  confirmar(byId("nv-run-cancelar"), async () => {
    try { await executar("cancelar_avaliacao"); nota("nv-run-nota", "Cancelamento pedido: nenhum item novo começa.", "ok"); } catch (e) { nota("nv-run-nota", motivoErro(e), "erro"); }
  });
  if (byId("nv-run-recuperacao")) byId("nv-run-recuperacao").addEventListener("click", async () => {
    try { await executar("medir_recuperacao", {split: val("nv-run-split")}); nota("nv-run-nota", "Medindo a busca, sem modelo.", "ok"); } catch (e) { nota("nv-run-nota", motivoErro(e), "erro"); }
    recarregar("nv-avaliacao");
  });
  confirmar(byId("nv-sen-medir"), async () => {
    try { await executar("medir_ouvido"); nota("nv-sen-nota", "Medição iniciada: leva uns dois minutos.", "ok"); } catch (e) { nota("nv-sen-nota", motivoErro(e), "erro"); }
    recarregar("nv-sentidos");
  });
  if (byId("nv-out-run")) byId("nv-out-run").addEventListener("change", () => avaliacao());

  // ---------------------------------------------------------------- Acervo e fontes (lote 5, C4)
  const ESTADO_TIPO = {revisado: "ok", catalogado: "neutro", quarentena: "aviso", recebido: "aviso", restrito: "erro", rejeitado: "erro", arquivado: "neutro", contestado: "aviso"};
  const TAMANHO_MAX = 25 * 1024 * 1024;
  function sinaisDe(c) {
    const a = c.analise || {}; const s = a.sinais || {};
    const partes = [];
    if (a.parse === "falhou") partes.push("parse falhou: " + (a.motivo || ""));
    if (s.instrucao_embutida) partes.push("instrução embutida");
    if (s.autoridade_alegada) partes.push("alega autorização");
    if (s.dado_pessoal) partes.push("dado pessoal ×" + s.dado_pessoal);
    if (s.segredos) partes.push("segredo ×" + s.segredos);
    return partes.length ? partes.join(" · ") : (a.parse === "ok" ? "sem sinais" : "não analisado");
  }
  function linhaAcervo(c) {
    const d = c.direitos || {};
    const sel = h("select", {"aria-label": "direitos"}, ["pendente", "livre", "permitido_pelo_humano", "desconhecido"].map((v) => h("option", {value: v, text: v, selected: v === d.status ? true : null})));
    const ev = h("input", {type: "text", placeholder: "evidência dos direitos", "aria-label": "evidência dos direitos", value: d.evidencia || ""});
    const bDir = h("button", {type: "button", class: "btn secondary", text: "Gravar direitos"});
    bDir.addEventListener("click", async () => {
      bDir.disabled = true;
      try { await executar("acervo_direitos", {sha256: c.sha256, status: sel.value, evidencia: ev.value}); nota("nv-acv-nota", "Direitos gravados. Índice refeito.", "ok"); }
      catch (e) { nota("nv-acv-nota", motivoErro(e), "erro"); }
      bDir.disabled = false; recarregar("nv-acervo");
    });
    const acoes = [];
    const acao = (rotulo, para, cor) => {
      const b = h("button", {type: "button", class: "btn " + (cor || "secondary"), text: rotulo});
      confirmar(b, async () => {
        try { await executar("acervo_transicionar", {sha256: c.sha256, para, motivo: "decisão no painel"}); nota("nv-acv-nota", "Estado: " + para + ". Índice refeito.", "ok"); }
        catch (e) { nota("nv-acv-nota", motivoErro(e), "erro"); }
        recarregar("nv-acervo");
      });
      acoes.push(b);
    };
    if (c.editorial_status === "catalogado") acao("Revisar (aprovar)", "revisado", "");
    if (["catalogado", "revisado"].includes(c.editorial_status)) acao("Contestar", "contestado");
    if (c.editorial_status !== "arquivado" && c.editorial_status !== "rejeitado") acao("Arquivar", "arquivado");
    if (["catalogado", "contestado"].includes(c.editorial_status)) acao("Rejeitar", "rejeitado", "perigo");
    return h("tr", {},
      h("td", {}, h("div", {class: "mono", text: c.rotulo || "(sem nome)"}), h("div", {class: "nv-sha", text: c.sha256.slice(0, 16) + " · " + c.extensao + " · " + (c.tamanho || 0) + " B"})),
      h("td", {}, h("div", {text: c.origem_tipo || "—"}), c.origem_uri ? h("div", {class: "nv-sha", text: c.origem_uri}) : null),
      h("td", {}, selo(c.editorial_status || "—", ESTADO_TIPO[c.editorial_status] || "neutro")),
      h("td", {text: sinaisDe(c)}),
      h("td", {}, h("div", {class: "nv-form estreito"}, sel, ev), h("div", {class: "nv-acoes"}, bDir, ...acoes)));
  }
  function acervo() {
    const a = (estado && estado.acervo) || {itens: []};
    const itens = a.itens || [];
    por("nv-acv-kpis", kpi("Fontes", itens.length, "teal"), kpi("Revisadas", itens.filter((c) => c.editorial_status === "revisado").length, "teal"),
      kpi("Em quarentena", itens.filter((c) => ["recebido", "quarentena"].includes(c.editorial_status)).length, "gold"),
      kpi("Restritas ou rejeitadas", itens.filter((c) => ["restrito", "rejeitado"].includes(c.editorial_status)).length, "rose"));
    byId("nv-acv-titulo").textContent = itens.length + " fontes · só as revisadas com direitos aparecem na busca";
    por("nv-acv-lista", itens.map(linhaAcervo));
    mostrar("nv-acv-vazio", itens.length === 0);
  }
  async function enviarArquivo() {
    const campo = byId("nv-acv-arquivo"); const arq = campo.files && campo.files[0];
    if (!arq) { nota("nv-acv-nota", "Escolha um arquivo primeiro.", "erro"); return; }
    const ext = (arq.name.split(".").pop() || "").toLowerCase().replace("htm", "html");
    if (!["md", "txt", "html", "pdf"].includes(ext)) { nota("nv-acv-nota", "Extensão não aceita: md, txt, html ou pdf.", "erro"); return; }
    if (arq.size > TAMANHO_MAX) { nota("nv-acv-nota", "Arquivo acima de 25 MB: recusado antes do envio.", "erro"); return; }
    nota("nv-acv-nota", "Enviando…");
    try {
      const r = await fetch("/api/nova-versao/upload", {method: "POST", credentials: "same-origin", cache: "no-store",
        headers: {"Content-Type": "application/octet-stream", "X-Extensao": ext, "X-Nome": encodeURIComponent(arq.name)}, body: arq});
      const txt = await r.text();
      if (!r.ok) { nota("nv-acv-nota", "Recusado (" + r.status + "): " + (txt || "").slice(0, 160), "erro"); return; }
      const j = JSON.parse(txt);
      nota("nv-acv-nota", (j.duplicado ? "Já estava no acervo" : "Recebido") + ": " + j.sha256.slice(0, 16) + ", estado " + j.editorial_status + ". Rode 'Processar pendentes'.", "ok");
    } catch (_) { nota("nv-acv-nota", "Sem resposta do servidor no envio.", "erro"); }
    campo.value = "";
    recarregar("nv-acervo");
  }
  if (byId("nv-acv-enviar")) byId("nv-acv-enviar").addEventListener("click", enviarArquivo);
  if (byId("nv-acv-importar")) byId("nv-acv-importar").addEventListener("click", async () => {
    try { const r = (await executar("acervo_importar")).resultado; nota("nv-acv-nota", "Pasta lida: " + r.pasta.length + " arquivo(s); " + r.processados.length + " analisado(s).", "ok"); }
    catch (e) { nota("nv-acv-nota", motivoErro(e), "erro"); }
    recarregar("nv-acervo");
  });
  if (byId("nv-acv-processar")) byId("nv-acv-processar").addEventListener("click", async () => {
    try { const r = (await executar("acervo_processar", {})).resultado; nota("nv-acv-nota", r.processados.length + " analisado(s) na quarentena.", "ok"); }
    catch (e) { nota("nv-acv-nota", motivoErro(e), "erro"); }
    recarregar("nv-acervo");
  });
  if (byId("nv-acv-baixar")) byId("nv-acv-baixar").addEventListener("click", async () => {
    const u = val("nv-acv-url"); if (!u) { nota("nv-acv-nota", "Cole um endereço https.", "erro"); return; }
    try { await executar("acervo_url", {url: u}); nota("nv-acv-nota", "Endereço baixado e em quarentena. Rode 'Processar pendentes'.", "ok"); }
    catch (e) { nota("nv-acv-nota", motivoErro(e), "erro"); }
    recarregar("nv-acervo");
  });
})();
