# Proposta P-8 — Conselho de Modelos em Rede (segunda base atualizada)

**Nome para assinatura:** `relay-council-panel-ui-rebase2-20261028`  
**Base:** `main` em `ebc770ea` (PR #683).

## Motivo

O PR de aplicação #682 foi fechado após o `main` avançar e ocupar a entrada (907). A primeira correção, PR #684, também ficou conflitante quando a proposta Equipe ocupou a entrada (908) antes do merge. As assinaturas anteriores seguem vinculadas aos hashes anteriores e não serão reaproveitadas.

Esta versão mantém a mesma interface e usa a entrada livre (909). O PR #684 permanece sem merge; esta proposta o substitui se for aprovada.

## Mudança proposta

Adicionar a página **Conselho de Modelos em Rede** ao painel: consulta o catálogo local de 17 provedores e permite registro manual de resposta/falha observada. O registro usa o endpoint local existente e grava apenas no cache comum sanitizado.

## Limites

Não envia prompts, não chama provedores, não automatiza DOM, não acessa abas/cookies/sessões/credenciais e não reinicia serviços.

## Arquivos

- `redesign/painel_operacional/prototipo.html`, `prototipo.js`, `prototipo.css` e `README.md`
- `ONDE_ESTAMOS.md`
- entrada nova (909) em `MEMÓRIAS.md`

## Verificação

Selftest OK; 22 testes do painel; `node --check`; aplicação do diff confirmada sobre `main` em `ebc770ea`. A interface já foi conferida em Chromium isolado: 17 provedores, envio simulado sem gravação e sem overflow em desktop/celular.

Após este registro entrar em `main` e CI passar, a versão exige assinatura própria: `bash scripts/aprovar.sh relay-council-panel-ui-rebase2-20261028`. O executor não executa o comando.
