const $ = (selector) => document.querySelector(selector);
const tabs = [...document.querySelectorAll('.tabs button')];

tabs.forEach((button) => {
  button.addEventListener('click', () => {
    tabs.forEach((item) => item.classList.remove('active'));
    document.querySelectorAll('.panel').forEach((panel) => panel.classList.remove('active'));
    button.classList.add('active');
    $(`#${button.dataset.tab}`).classList.add('active');
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
    empty.className = 'empty';
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
