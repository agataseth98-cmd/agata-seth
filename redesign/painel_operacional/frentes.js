"use strict";

// Somente leitura: busca /api/frentes e desenha a lista só com textContent e createElement.
(function () {
  const estado = document.getElementById("estado");
  const cabecalho = document.getElementById("cabecalho");
  const lista = document.getElementById("lista");

  const CAMPOS = [
    ["Entregável", "entregavel"],
    ["Gate", "gate"],
    ["Bloqueios", "bloqueios"],
  ];

  function item(frenta) {
    const li = document.createElement("li");
    const titulo = document.createElement("h2");
    titulo.textContent = `${frenta.id} · ${frenta.nome}`;
    li.appendChild(titulo);

    for (const [rotulo, campo] of CAMPOS) {
      const p = document.createElement("p");
      const b = document.createElement("strong");
      b.textContent = `${rotulo}: `;
      p.appendChild(b);
      p.appendChild(document.createTextNode(String(frenta[campo] ?? "")));
      li.appendChild(p);
    }

    if (frenta.piloto_sintetico) {
      const p = document.createElement("p");
      const b = document.createElement("strong");
      b.textContent = "Piloto sintético: ";
      p.appendChild(b);
      p.appendChild(document.createTextNode(String(frenta.piloto_sintetico)));
      li.appendChild(p);
    }
    return li;
  }

  function desenhar(dados) {
    const frentes = Array.isArray(dados.frentes) ? dados.frentes : [];
    cabecalho.textContent = `Palavra atual: ${dados.palavra_atual ?? ""} · Dados reais: ${dados.dados_reais ?? ""}`;
    lista.replaceChildren(...frentes.map(item));
    estado.textContent = `${frentes.length} frentes.`;
  }

  fetch("/api/frentes", { cache: "no-store", credentials: "same-origin", headers: { Accept: "application/json" } })
    .then((resposta) => {
      if (!resposta.ok) throw new Error("status " + resposta.status);
      return resposta.json();
    })
    .then(desenhar)
    .catch(() => {
      estado.textContent = "Não foi possível carregar as frentes.";
    });
})();
