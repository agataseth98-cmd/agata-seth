// Operator Console dentro do /prototipo (seção Qualidade). Lê o pacote no navegador; nada sobe para o servidor.
// Isolado em IIFE e restrito a #oc-raiz: não declara nada no escopo global e não mexe em outras partes da página.
(function () {
  const raiz = document.getElementById('oc-raiz');
  if (!raiz) return;
  const $ = (selector) => raiz.querySelector(selector);
  const abas = [...raiz.querySelectorAll('.oc-abas button')];

  abas.forEach((botao) => {
    botao.addEventListener('click', () => {
      abas.forEach((item) => item.classList.remove('active'));
      raiz.querySelectorAll('.oc-painel').forEach((painel) => painel.classList.remove('active'));
      botao.classList.add('active');
      const painel = document.getElementById('oc-' + botao.dataset.tab);
      if (painel) painel.classList.add('active');
    });
  });

  const read = async (file) => (file ? file.text() : '');
  const addTextArticle = (container, text) => {
    const article = document.createElement('article');
    article.textContent = text;
    container.replaceChildren(article);
  };

  $('#package').addEventListener('change', async (event) => {
    const files = [...event.target.files];
    const byName = (name) => files.find((file) => file.webkitRelativePath.endsWith(`/${name}`) || file.name === name);
    const provenance = byName('provenance.json');
    if (!provenance) {
      $('#state').textContent = 'PACOTE INVÁLIDO';
      $('#summary').textContent = 'provenance.json não encontrado.';
      return;
    }

    let data;
    try {
      data = JSON.parse(await read(provenance));
    } catch {
      $('#state').textContent = 'INTEGRIDADE NÃO MEDIDA';
      return;
    }

    $('#state').textContent = 'PACOTE CARREGADO';
    $('#summary').textContent = `Objetivo: ${data.goal || 'não informado'} · raiz: ${data.root || 'não medida'}`;
    $('#files').textContent = (data.files || []).length;
    $('#integrity').textContent = 'não medido';
    $('#source').textContent = provenance.webkitRelativePath || provenance.name;
    $('#freshness').textContent = data.generated_at || 'não medido';

    const capabilities = byName('capabilities.md');
    if (capabilities) addTextArticle($('#capability-list'), await read(capabilities));

    const drift = byName('drift-report.md');
    if (drift) $('#drift-text').textContent = await read(drift);

    const reviews = files.filter((file) => file.name === 'packet.md');
    const reviewList = $('#review-list');
    reviewList.replaceChildren();
    if (!reviews.length) {
      const empty = document.createElement('p');
      empty.className = 'oc-vazio';
      empty.textContent = 'Não medido.';
      reviewList.append(empty);
      return;
    }
    reviews.forEach((file) => {
      const article = document.createElement('article');
      article.textContent = file.webkitRelativePath || file.name;
      reviewList.append(article);
    });
  });
})();
