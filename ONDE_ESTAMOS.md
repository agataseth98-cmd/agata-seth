# Onde estamos

Atualizado em 29/10/2026.

Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 22/10/2026: `extras/arquivo/onde-estamos-ate-2026-10-22.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md`.

## Hoje, 29/10

**Conselho em Rede no Chromium:** proposta P-8 `relay-council-abas-chromium-20261029` pronta para revisão e assinatura. Ela usa nove adaptadores experimentais nas abas já abertas pelo launcher; cada envio precisa de aprovação no painel. Testes locais passaram em cópia descartável. Nenhum prompt real foi enviado, a extensão do Chromium não foi recarregada e o runtime não mudou. Para aplicar depois do merge da proposta e da assinatura: `bash scripts/aprovar.sh relay-council-abas-chromium-20261029`.

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

## Hoje, 22 e 23/10

**Já valendo (assinado e aplicado):**
- A Seth responde pela cascata com a memória completa. Dados pessoais deixaram de bloquear a saída externa; só segredo continua bloqueado.
- A escrita em MEMÓRIAS pelo LibreChat exige sua aprovação, e foi comprovada uma vez. O diário saiu do chat.
- O escriba exige token por projeto e recusa segredo antes de gravar.
- O migrador de história e o gerador do mapa do PROJETO entraram (pacote 2a).
- O mapa do PROJETO na hidratação (pacote 2b). Medido em cópia: a hidratação caiu de 124 mil para 88 mil caracteres.
- A suíte de testes roda em paralelo, até 4 casos ao mesmo tempo. Antes levava cerca de 205 segundos; agora, cerca de 56 segundos, medido duas vezes com os 58 casos passando.

**Esperando você:**
- Assinar as propostas em conjunto, quando estiverem prontas. Hoje, uma: a correção da entrada 817 do MEMÓRIAS.
- Lista de nomes de projeto: não é necessária para a Seth funcionar. Só faz sentido se houver nome que não deva sair para a nuvem.

**Com o Codex:**
- As pastas reports, research_notes e o arquivo sh são do Codex. Serão sanitizadas quando o trabalho dele estiver concluído. Até lá, não são movidas.
- Propostas antigas: cinco não se aplicam mais ao main e não serão assinadas. Uma (cabecalho-modelo-real) ainda se aplica e será conferida antes de qualquer assinatura.

**Em espera:**
- Backfill das 11 tags dos chunks frios: depois de 29/10.
- Roteamento por capacidade: próxima frente, depois da correção da 817.

**Fechado:**
- Sombra em segundo plano (PR 474).
