// Botões do Conselho: abrir os destinos e conferir os conselheiros ao entrar na seção. Isolado em IIFE.
(function () {
// Botões "Abrir": pedem só o nome do destino; o servidor tem a lista fixa e decide o comando.
document.querySelectorAll('[data-alvo]').forEach((botao) => {
  botao.addEventListener('click', async () => {
    const aviso = document.getElementById('abrir-aviso');
    try {
      const r = await fetch('/api/abrir', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({alvo: botao.dataset.alvo})});
      aviso.textContent = r.ok ? 'Abrindo ' + botao.textContent + '…' : 'Não consegui abrir ' + botao.textContent + '.';
    } catch (e) {
      aviso.textContent = 'Painel fora do ar.';
    }
  });
});
// Entrar na aba Conselho (a cada clique) confere os nove conselheiros e abre só os que faltam.
async function conferirConselheiros() {
  const aviso = document.getElementById('abrir-aviso');
  try {
    const r = await fetch('/api/abrir', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({alvo: 'conselho'})});
    if (!r.ok) { aviso.textContent = 'Não consegui conferir os conselheiros.'; return; }
    const d = await r.json();
    aviso.textContent = d.faltando.length ? 'Abrindo ' + d.faltando.length + ' conselheiro(s) que faltavam…' : 'Os nove conselheiros estão abertos.';
  } catch (e) {
    aviso.textContent = 'Painel fora do ar.';
  }
}
document.querySelectorAll('button[data-secao="conselho"], [data-open-page="conselho"]').forEach((b) => b.addEventListener('click', conferirConselheiros));
})();
