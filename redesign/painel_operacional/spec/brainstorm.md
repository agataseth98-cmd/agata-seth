# Brainstorm — Painel unificado

## Usuários

- O Humano, operador único, em `127.0.0.1`. Abre o painel para ver o estado, conversar com a Seth, conferir o Conselho, medir e decidir.
- Agentes e auditores leem os mesmos dados pelas rotas `/api/*`; nada muda para eles.
- Quem chega por link antigo (`/index.html`, `/frentes`, `/operator_console`, `/conselho-rede/`) cai na seção certa.

## Estado que muda

- Servidor: tabela de redirects e `_ASSETS` em `server.py`. Nenhum estado de dados muda.
- Página: `prototipo.html` vira sete seções com subpainéis. `prototipo.js` ganha roteamento por hash e estados. `prototipo.css` absorve as folhas antigas.
- Scripts `conselho-rede/app.js` e `operator_console/app.js` deixam de declarar globais de topo.
- Arquivos retirados: `index.html`, `app.js`, `styles.css`, `frentes.html`, `frentes.js`, `nova_versao.css`, `conselho-rede/index.html`, `conselho-rede/style.css`, `operator_console/index.html`, `operator_console/style.css`.
- Cache do painel em `~/.cache/agata/painel/` não muda de formato.

## Erros e concorrência

- Hash desconhecido: cai em `panorama`; nada quebra.
- Hash de seção que não existe mais (link antigo com `#page-operacao`): cai em `panorama`. Não há redirect para esses nomes; é aceito.
- API ocupada (HTTP 429 de `medicoes`, `sdd`, `nova-versao`): aparece como `erro` com "ocupado; tente depois". Não repete sozinho.
- Duas abas abertas: cada aba faz as próprias leituras; o servidor já trata o lock de execução (`_SDD_LOCK`, `_PROPOSAL_LOCK`, `_RELAY_LOCK`).
- Dois scripts com o mesmo nome global: hoje o `refresh` de Panorama é sobrescrito pelo do Conselho (medido por leitura). O teste de globais impede isso.
- Conselho: nenhuma execução sem aprovação individual; a fila e o lease ficam como estão.
- Operator Console sem iframe: o pacote é lido no navegador, como hoje; nada sobe para o servidor.

## Migração

- Sem migração de dados.
- URLs antigas redirecionam. Favoritos e marcadores antigos continuam válidos.
- Testes existentes que pinam a estrutura antiga (`page-*`, `data-page`, `nova_versao.css`) são reescritos na aplicação; a cobertura é mantida no teste novo.

## Observabilidade

- Nenhuma métrica nova. As seções mostram a hora da leitura (`observed_at`) quando a API devolve.
- Estado sem leitura aparece como `carregando`, `vazio` ou `erro` com "não medido". Não aparece como "ok".
- A verificação de que a tela abre e troca de seção fica no navegador (NOT RUN, ver spec).

## Reversão

- `git revert` do commit de aplicação. Os arquivos retirados voltam com o revert.
- Se a aplicação tiver ido em passos, reverter do último para o primeiro.
- Links antigos voltam a ser páginas próprias com o revert.

## Sucesso

- Todos os critérios automatizados de `spec/acceptance.json` passam, com `pytest` 9.2.0, na base d1b6b4f7 mais a aplicação.
- A suíte de `redesign/painel_operacional` passa.
- A verificação no navegador é feita pelo Humano e registrada como medida. Até lá, o resultado visual é "não medido".
- Nenhuma função das telas atuais fica sem seção (tabela de mapeamento completa, com o teste de subpainéis).
