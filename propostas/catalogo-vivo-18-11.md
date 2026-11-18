# Proposta catalogo-vivo-18-11 — a pesquisa semanal compara o OmniRoute com a lista viva dos provedores

Decisão do Humano em 18/11/2026 (3ª correção autorizada às 16:03; "1-ok" às 16:09). Motivo medido: o OmniRoute listava 12 modelos NVIDIA e 11 estavam aposentados (410/404).

**O quê** (`scripts/pesquisar_modelos_gratuitos.py`, modo DESCOBERTA, zero cota, nenhuma chamada a modelo):
- Lê as listas públicas da NVIDIA e do OpenRouter, sem token, e compara com os ids do OmniRoute: "aposentado" (no OmniRoute, fora da lista viva) e "novo" (na lista viva, fora do OmniRoute; OpenRouter só `:free`; NVIDIA rotulada "gratuidade não verificada").
- Compara só modelos de texto, fora imagem, voz, busca, segurança e tradução.
- Marca "suspeito" quando mais da metade some ou quando a lista viva cai mais de 30% desde a semana anterior.
- OmniRoute fora, rede fora, JSON inválido ou HTTP de erro viram erro por provedor, sem derrubar a rodada.
- Proposta semanal só quando mudam aposentados, novos ou o suspeito.
- Token interno: só para host local, sem seguir redirecionamento (302 vira erro).

**Medido:** `--selftest` 28 PASS (normal e `-I`); CI local TUDO OK; teste de mutação do revisor: as mutações de token, host, filtro, queda, totais e OmniRoute fora reprovam o selftest. Rodada real: NVIDIA 11 aposentados (batem com os 410/404 medidos no catálogo de 18/11) e 22 novos, suspeito; OpenRouter 0 e 0.

**Revisão:** Codex sem cota (volta 20:04); agata-revisor (Haiku) r1 e r2 reprovaram, todos os achados corrigidos com teste.

**Reversão:** `git revert` do commit de aplicação.

**Modelo:** Sonnet 5.5 (implementação) orquestrado pelo Opus 5.5.
