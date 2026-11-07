# painel-melhor-20261107 — painel operacional: três defeitos medidos

Proposta P-8. Diff: `propostas/painel-melhor-20261107.diff` (só `redesign/painel_operacional/`). Base: `origin/main` em 40f79f74. Medido em 07/11/2026 por Claude Opus 5.5.

## Medição antes (serviço vivo, 127.0.0.1:20146)

- Rotas: 34 rotas GET de `_ASSETS` e do `do_GET` respondem; `/` e `/conselho-rede` dão 302 (esperado), `/api/relay-council/focos` e `/tasks` dão 403 sem o cabeçalho da extensão (esperado), `/api/vault/item?id=x` dá 400 (id inválido, esperado). O resto dá 200.
- `python3 -m unittest discover -s redesign/painel_operacional -p 'test_*.py'`: 122 testes, 1 falha (`test_sdd_painel.ProjetosExternosTests.test_executar_projeto_...`: "critérios: 0/1 passaram"). Causa confirmada: `python3 -m pytest` não existe e não há `pytest` no PATH; com o binário do cache uv no PATH o mesmo teste passa. O ciclo de projeto externo do painel ignorava `AGATA_PYTEST` (o ciclo por componente já o usava).
- Chromium headless (`--enable-logging=stderr --dump-dom`):
  - `/operator_console` (sem barra, servido com 200): `style.css` relativo virava `/style.css` (404, MIME text/plain, recusado) e `app.js` virava `/app.js` do painel antigo: `Uncaught TypeError: Cannot read properties of null (reading 'addEventListener')`. A página ficava sem estilo e com o script errado.
  - `/prototipo` e `/frentes`: 2 fontes externas (`assets-proxy.anthropic.com`, `@font-face` em `prototipo.css`) bloqueadas pela CSP `default-src 'none'`.
  - `/prototipo`: 11 violações de estilo inline. Fora deste lote: PR 934 (`csp-prototipo-20261106`).
- `style=` e script inline: só em `prototipo.html` (PR 934). Nenhum em `frentes.html`, `index.html`, `operator_console/index.html`, `conselho-rede/index.html`.

## O que muda

1. `server.py`: `/operator_console` responde 302 para `/operator_console/` (mesmo padrão de `/conselho-rede`); sai de `_ASSETS`.
2. `prototipo.css`: removidos os dois `@font-face` remotos; a pilha de fontes cai nas locais (Fira Sans, Noto Sans). Nada é buscado fora da Máquina.
3. `sdd_painel.py`: `_pytest()` (AGATA_PYTEST ou `pytest` do PATH). O ciclo de projeto externo diz "não medido" sem pytest e, com pytest, põe o diretório do binário no PATH do runner (como `scripts/ci_sdd_local.sh`).
4. Testes: redirect de `/operator_console`; CSS servido sem `url(http…)`; projeto sem pytest diz "não medido" e não roda; PATH do ciclo recebe o diretório do pytest. O teste que falhava passa o pytest por `AGATA_PYTEST` (procura em PYTEST, AGATA_PYTEST, PATH e cache uv; sem nenhum, pula com "não medido" em vez de falhar). Os 5 testes ficam vermelhos no código antigo e verdes no novo.

## Medição depois (código da worktree servido em 127.0.0.1:20199)

- `/operator_console`: 302 para `/operator_console/`; Chromium sem erro de console em `/operator_console`, `/operator_console/`, `/frentes` e `/conselho-rede/`.
- `/prototipo`: 0 fontes bloqueadas; restam as 11 violações de estilo inline (PR 934).
- unittest discover: 125 testes, OK.
- `PYTEST=<cache uv>/bin/pytest bash scripts/ci_sdd_local.sh`: `CI LOCAL: TUDO OK`.

## Fora do lote

- Estilo inline do `/prototipo` (PR 934).
- Aviso do Chromium "Password field is not contained in a form" em `/prototipo`: só aviso, não erro.
- O serviço do painel não foi reiniciado; o efeito no 20146 depende de aplicar e reiniciar.
