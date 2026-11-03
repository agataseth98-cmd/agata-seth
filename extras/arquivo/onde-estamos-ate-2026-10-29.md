# Onde estamos, 28 e 29/10/2026 (arquivado em 03/11/2026)

Movido de `ONDE_ESTAMOS.md` para manter a página em uma tela. Texto original abaixo, sem alteração.

## Hoje, 29/10

**Conselho em Rede:** PR #709 (`df9a50c2`) aplicado no painel oficial. O serviço reiniciou; `/conselho-rede`, o JS e o estado responderam HTTP 200. No Brave, nove abas detectadas e fila vazia. O JS servido não tem `window.confirm()` e mantém a aprovação explícita. Nenhum prompt foi enviado nesta verificação. Backup e rollback estão em MEMÓRIAS (931).

## Hoje, 28/10

**Conselho em Rede:** P-8 `painel-conselho-api-20261028` foi assinada e integrada no PR #701 (`ca80dacc`). `painel-operacional.service` reiniciado; página e catálogo HTTP 200, fila vazia, cinco APIs mapeadas para execução. Selftest e 43 testes passaram; checks do PR verdes.

**Falta para ensaio real:** recarregar manualmente RelayCouncil v2 em `chrome://extensions` no Chromium. A política de navegação impediu o agente de abrir essa página; por isso a versão 0.7.0 no perfil ainda não foi confirmada. Não houve chamadas reais a provedores; cada prompt continua sujeito à aprovação humana no painel.

**Rollback:** backup pré-aplicação e comando estão em MEMÓRIAS (924). A unit e seu drop-in não foram alterados.

**Runtime do Conselho:** drop-in do `painel-operacional.service` concede escrita só a `~/.local/share/agata/painel-conselho/official`. Backup e comando de rollback estão na entrada (920) de MEMÓRIAS.

**Navegador do Conselho:** a extensão oficial está carregada no Chromium persistente e a porta de depuração 9222 está fechada. Registro em MEMÓRIAS (919).

**Proposta publicada:** PR #689 integrado em `2d5b0acc`; o diff e o registro da proposta estão em `propostas/aplicadas/` na branch de aplicação, junto do marcador assinado.

**PR anterior #684:** continua aberto e conflitante; não foi alterado.

**Equipe universal e auditoria encadeada:** PRs #687 e #688 integrados.

**RelayCouncil:** contrato v3 e catálogo de 17 provedores estão aplicados (PR #674). O envio está integrado ao painel; adaptadores e termos variam por provedor.

