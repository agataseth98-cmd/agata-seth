const nav=[...document.querySelectorAll('.nav button')],pages=[...document.querySelectorAll('.page')],crumb=document.getElementById('crumb');
const shell=document.querySelector('.shell'),sidebarToggle=document.getElementById('sidebar-toggle');
function setSidebarCollapsed(collapsed){shell.classList.toggle('sidebar-collapsed',collapsed);sidebarToggle.setAttribute('aria-expanded',String(!collapsed));sidebarToggle.setAttribute('aria-label',collapsed?'Expandir navegação lateral':'Recolher navegação lateral');sidebarToggle.title=collapsed?'Expandir navegação lateral':'Recolher navegação lateral';nav.forEach(b=>b.title=b.getAttribute('aria-label')||b.textContent.trim());try{localStorage.setItem('agata-sidebar-collapsed',String(collapsed))}catch{}}
const savedSidebarState=(()=>{try{return localStorage.getItem('agata-sidebar-collapsed')==='true'}catch{return false}})();setSidebarCollapsed(savedSidebarState);sidebarToggle.addEventListener('click',()=>setSidebarCollapsed(!shell.classList.contains('sidebar-collapsed')));
function showPage(name){pages.forEach(p=>p.classList.toggle('active',p.id==='page-'+name));nav.forEach(b=>{if(b.dataset.page===name)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});const p=document.getElementById('page-'+name);crumb.textContent='Agata / '+(p?.dataset.title||'Panorama');document.getElementById('search').value='';filterSearch('')}
nav.forEach(b=>b.addEventListener('click',()=>showPage(b.dataset.page)));
const search=document.getElementById('search');let capFilter='all';function filterSearch(q){const active=document.querySelector('.page.active');if(!active)return;const cards=[...active.querySelectorAll('.cap-card')];let visible=0;cards.forEach(c=>{const byText=!q||c.innerText.toLocaleLowerCase('pt-BR').includes(q.toLocaleLowerCase('pt-BR'));const byChip=active.id!=='page-capacidades'||capFilter==='all'||c.dataset.state===capFilter;const match=byText&&byChip;c.hidden=!match;if(match)visible++});const no=document.getElementById('no-results');if(no)no.classList.toggle('show',cards.length>0&&visible===0)}search.addEventListener('input',e=>filterSearch(e.target.value.trim()));
document.querySelectorAll('.filterbar button').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.filterbar button').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');capFilter=b.dataset.filter;filterSearch(search.value.trim())}));
const dialog=document.getElementById('evidence-dialog');document.querySelectorAll('.evidence').forEach(b=>b.addEventListener('click',()=>{document.getElementById('dialog-title').textContent=b.dataset.title||'Evidência';document.getElementById('dialog-body').textContent=b.dataset.body||'';document.getElementById('dialog-source').textContent=b.dataset.source||'Fonte não informada';dialog.showModal()}));document.querySelectorAll('.close,.close-dialog').forEach(b=>b.addEventListener('click',()=>dialog.close()));dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close()});
document.getElementById('preview-refresh')?.addEventListener('click',()=>setDemoScenario('fresh'));
const wikiDemoForm=document.getElementById('wiki-demo-form');
function filterWikiDemo(){const query=document.getElementById('wiki-demo-query').value.trim().toLocaleLowerCase('pt-BR');const kind=document.getElementById('wiki-demo-kind').value;const results=[...document.querySelectorAll('.wiki-demo-result')];let visible=0;results.forEach(card=>{const match=(!query||card.dataset.search.includes(query)||card.innerText.toLocaleLowerCase('pt-BR').includes(query))&&(kind==='todas'||card.dataset.kind===kind);card.hidden=!match;if(match)visible++});document.getElementById('wiki-demo-empty').hidden=visible>0;document.getElementById('wiki-demo-status').textContent=visible+' exemplo(s) local(is) · nenhuma consulta foi feita.'}
wikiDemoForm.addEventListener('submit',event=>event.preventDefault());document.getElementById('wiki-demo-query').addEventListener('input',filterWikiDemo);document.getElementById('wiki-demo-kind').addEventListener('change',filterWikiDemo);
const demoScenarioButtons=[...document.querySelectorAll('[data-demo-scenario]')];
const demoGitSnapshot={branch:'main',head:'2fceada',upstream:'origin/main · alinhada',dirty:'2 itens não rastreados'};
function setDemoScenario(mode){
  const cfg={
    fresh:{unitState:'active',unitChip:'ATIVO · DEMO',unitTitle:'4/4 ativos',unitNote:'Cenário fictício · dentro da validade de 60 s',unitAge:'Exemplo: observado há 12 s · válido por mais 48 s · último valor active',unitValidity:'Cenário recente · horários ilustrativos',unitsHeader:'RECENTE · DEMO',gitState:'RECENTE · DEMO',gitValue:'Recente',gitNote:'Cenário fictício · main · HEAD 2fceada',gitAge:'Exemplo: observado há 12 s · válido por mais 48 s',timerState:'AGENDA RECENTE · DEMO',timerIntro:'Leitura fictícia recente da configuração; a última execução continua não medida.',timerAge:'Exemplo: configuração lida há 12 s · validade 60 s · execução não medida',healthClass:'teal'},
    stale:{unitState:'stale',unitChip:'DESATUALIZADO',unitTitle:'Leitura vencida',unitNote:'Cenário fictício · último valor conhecido, 4 ativos',unitAge:'Exemplo: observado há 5 min · validade 60 s vencida · último valor active',unitValidity:'Exemplo vencido · não é uma coleta atual',unitsHeader:'LEITURA VENCIDA',gitState:'SNAPSHOT VENCIDO',gitValue:'Vencido',gitNote:'Snapshot histórico · main · HEAD 2fceada',gitAge:'Exemplo: observado às 13:26 · validade 60 s vencida',timerState:'CONFIGURAÇÃO VENCIDA',timerIntro:'Exemplo vencido · os horários permanecem como último valor conhecido, sem alegar execução.',timerAge:'Exemplo vencido · configuração não consultada nesta sessão',healthClass:'gold'},
    unknown:{unitState:'unknown',unitChip:'DESCONHECIDO',unitTitle:'Sem leitura',unitNote:'Exemplo: nenhuma resposta válida da fonte',unitAge:'Sem valor válido neste cenário de demonstração',unitValidity:'Sem horário de observação válido',unitsHeader:'SEM LEITURA',gitState:'SEM LEITURA',gitValue:'Sem leitura',gitNote:'Exemplo: fonte Git indisponível',gitAge:'Nenhum snapshot válido neste cenário',timerState:'SEM LEITURA',timerIntro:'Não há configuração válida disponível neste cenário fictício; execução também não medida.',timerAge:'Sem observação válida · próximo disparo não medido',healthClass:'violet'}
  }[mode];
  if(!cfg)return;
  const unitKpi=document.getElementById('unit-kpi');unitKpi.className='kpi '+cfg.healthClass;
  document.getElementById('unit-kpi-value').textContent=cfg.unitTitle;
  document.getElementById('unit-kpi-note').textContent=cfg.unitNote;
  const unitsHeader=document.getElementById('units-panel-state');unitsHeader.className='chip '+(mode==='fresh'?'active':mode==='stale'?'partial':'horizon');unitsHeader.textContent=cfg.unitsHeader;
  document.querySelectorAll('.demo-unit').forEach(row=>{
    const light=row.querySelector('.ops-light');light.className='ops-light '+cfg.unitState;
    const badge=row.querySelector('.unit-badge');badge.className='chip unit-badge '+(mode==='fresh'?'active':mode==='stale'?'partial':'horizon');badge.textContent=cfg.unitChip;
    row.querySelector('.unit-age').textContent=cfg.unitAge;
  });
  document.getElementById('unit-validity').textContent=cfg.unitValidity;
  const gitHeader=document.getElementById('git-panel-state');gitHeader.className='chip '+(mode==='fresh'?'active':mode==='stale'?'partial':'horizon');gitHeader.textContent=cfg.gitState;
  document.getElementById('git-kpi-value').textContent=cfg.gitValue;document.getElementById('git-kpi-note').textContent=cfg.gitNote;
  document.getElementById('git-age').textContent=cfg.gitAge;
  const gitValues=mode==='unknown'?{branch:'—',head:'—',upstream:'Sem leitura válida',dirty:'—'}:demoGitSnapshot;
  document.getElementById('git-branch').textContent=gitValues.branch;
  document.getElementById('git-head').textContent=gitValues.head;
  document.getElementById('git-upstream').textContent=gitValues.upstream;
  document.getElementById('git-dirty').textContent=gitValues.dirty;
  const timerHeader=document.getElementById('timer-panel-state');timerHeader.className='chip '+(mode==='fresh'?'active':mode==='stale'?'partial':'horizon');timerHeader.textContent=cfg.timerState;
  document.getElementById('timer-intro').textContent=cfg.timerIntro;
  document.getElementById('timer-age').textContent=cfg.timerAge;
  document.getElementById('inbox-interval').textContent=mode==='unknown'?'—':'A cada 15 min · exemplo';
  document.getElementById('maintenance-interval').textContent=mode==='unknown'?'—':'Diária · exemplo';
  document.getElementById('consolidation-window').textContent=mode==='unknown'?'—':'Janela 12:15–13:15 · exemplo';
  document.getElementById('consolidation-note').textContent=mode==='unknown'?'Configuração não disponível':'Timer das 23:00: desativado · exemplo';
  demoScenarioButtons.forEach(button=>{const selected=button.dataset.demoScenario===mode;button.classList.toggle('selected',selected);button.setAttribute('aria-pressed',String(selected))});
  document.getElementById('preview-response').textContent='Cenário de demonstração: '+(mode==='fresh'?'leitura recente.':mode==='stale'?'leitura vencida.':'sem leitura válida.');
}
demoScenarioButtons.forEach(button=>button.addEventListener('click',()=>setDemoScenario(button.dataset.demoScenario)));
setDemoScenario('stale');
/* Ligação ao painel real (formação em recortes): só saúde de unidades e Git.
   Agenda e Wiki ficam como demonstração local até serem liberadas. */
(async function () {
  const set = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
  const nomes = {
    "omniroute.service": "OmniRoute",
    "omniroute-sanitizer.service": "Sanitizador",
    "seth-gateway.service": "Seth Gateway",
    "seth-verificador.service": "seth-verificador",
  };
  try {
    const resposta = await fetch("/api/status", { cache: "no-store" });
    if (!resposta.ok) throw new Error("HTTP " + resposta.status);
    const dados = await resposta.json();
    const hora = (iso) => new Date(iso).toLocaleTimeString("pt-BR");
    const ativos = dados.services.filter((s) => s.state === "ok").length;
    set("unit-kpi-value", ativos + "/" + dados.services.length + " ativos");
    set("unit-kpi-note", "Leitura real do painel · commit " + dados.commit);
    set("units-panel-state", dados.state === "ok" ? "LEITURA REAL" : "ATENÇÃO");
    set("unit-validity", "Observado " + hora(dados.observed_at) + " · válido até " + hora(dados.fresh_until));
    document.querySelectorAll(".demo-unit").forEach((linha) => {
      const nome = linha.querySelector("strong").textContent;
      const servico = dados.services.find((s) => nomes[s.unit] === nome);
      if (!servico) return;
      const ok = servico.state === "ok";
      linha.querySelector(".ops-light").className = "ops-light " + (ok ? "active" : "stale");
      linha.querySelector(".unit-age").textContent =
        "Leitura real · " + servico.active_state + "/" + servico.sub_state + " · observado " + hora(dados.observed_at);
      const badge = linha.querySelector(".unit-badge");
      badge.className = "chip unit-badge " + (ok ? "active" : "partial");
      badge.textContent = ok ? "ATIVO" : "ATENÇÃO";
    });
    const git = dados.git;
    set("git-branch", git.branch);
    set("git-head", git.head);
    set("git-kpi-value", git.state === "ok" ? "Alinhado" : "Ver detalhe");
    set("git-kpi-note", "Leitura real · main " + git.head);
    set("git-panel-state", git.state === "ok" ? "LEITURA REAL" : "ATENÇÃO");
    set("git-age", "Observado " + hora(dados.observed_at) + " · sem consulta à rede");
  } catch (erro) {
    set("unit-validity", "Leitura real indisponível: " + erro.message + ". Nada anterior foi mantido como atual.");
    set("units-panel-state", "SEM LEITURA");
  }
  set("timer-panel-state", "NÃO LIBERADO");
  set("timer-intro", "Agenda ainda não liberada: os horários abaixo são exemplos locais, sem leitura da Máquina.");
})();

/* Cartão do Panorama: leitura viva do Git; o snapshot de 23/10 fica como referência histórica. */
(async function () {
  const put = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
  try {
    const r = await fetch("/api/status", { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();
    put("hero-sync-label", "Git local · " + (d.git.state === "ok" ? "alinhado" : "atenção"));
    put("hero-sync-head", d.git.head);
    const note = document.getElementById("hero-sync-note");
    if (note) note.innerHTML = "";
    if (note) {
      note.append("Leitura real · " + new Date(d.observed_at).toLocaleTimeString("pt-BR"), document.createElement("br"),
        "Referência histórica: 65f76af (23 out 2026 · 10:01 -03)");
    }
  } catch (erro) {
    put("hero-sync-label", "Git local · sem leitura");
    put("hero-sync-head", "—");
  }
})();
