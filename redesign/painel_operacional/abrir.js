// Botões do Conselho: abrir os destinos e conferir os conselheiros ao entrar na seção. Isolado em IIFE.
(function () {
// Botões "Abrir": pedem só o nome do destino; o servidor tem a lista fixa e decide o comando.
// Delegação no documento: os botões de modelos são criados de /api/provedores depois que este arquivo carrega.
document.addEventListener('click', async (evento) => {
  const botao = evento.target && evento.target.closest ? evento.target.closest('[data-alvo]') : null;
  if (!botao) return;
  const aviso = document.getElementById('abrir-aviso');
  try {
    const r = await fetch('/api/abrir', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({alvo: botao.dataset.alvo})});
    aviso.textContent = r.ok ? 'Abrindo ' + botao.textContent + '…' : 'Não consegui abrir ' + botao.textContent + '.';
  } catch (e) {
    aviso.textContent = 'Painel fora do ar.';
  }
});
// Entrar na aba Conselho (a cada clique) confere os conselheiros e abre só os que faltam.
async function conferirConselheiros() {
  const aviso = document.getElementById('abrir-aviso');
  try {
    const r = await fetch('/api/abrir', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({alvo: 'conselho'})});
    if (!r.ok) { aviso.textContent = 'Não consegui conferir os conselheiros.'; return; }
    const d = await r.json();
    aviso.textContent = d.faltando.length ? 'Abrindo ' + d.faltando.length + ' conselheiro(s) que faltavam…' : 'Conselheiros conferidos: nenhum faltava.';
  } catch (e) {
    aviso.textContent = 'Painel fora do ar.';
  }
}
document.querySelectorAll('button[data-secao="conselho"], [data-open-page="conselho"]').forEach((b) => b.addEventListener('click', conferirConselheiros));
})();
