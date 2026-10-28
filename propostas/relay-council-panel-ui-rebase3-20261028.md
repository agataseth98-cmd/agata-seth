# Proposta P-8 — Conselho de Modelos em Rede (base 8519794)

**Nome para assinatura:** `relay-council-panel-ui-rebase3-20261028`  
**Base:** `main` em `8519794574a15207a4afe98f12307c3302f23269` (PR #688).

## Motivo

O PR #684 contém uma proposta anterior e está aberto com conflito contra o `main`. Esta versão refaz o patch da interface sobre a base atual. O PR #684 fica preservado e não é alterado por esta proposta. Assinaturas ou marcadores de versões anteriores não valem para este novo diff.

## Mudança proposta

Adicionar a página **Conselho de Modelos em Rede** ao painel operacional, consultar o catálogo local de 17 provedores e permitir registro manual de resposta ou falha observada pelo humano. O registro usa o endpoint local existente e grava somente no cache comum sanitizado.

## Limites

Não envia prompts nem chama provedores; não automatiza DOM; não acessa abas, cookies, sessões ou credenciais; não reinicia serviços. A proposta altera somente `redesign/painel_operacional/README.md`, `prototipo.css`, `prototipo.html` e `prototipo.js`.

## Verificação

O diff foi regenerado sobre `8519794`; `git apply --check` passa nessa base e `git diff --check` não apontou whitespace. Os testes e a conferência visual descritos na proposta anterior foram feitos sobre `ebc770ea`, não foram repetidos nesta base. Esta proposta não afirma validação de runtime após o rebase.

Após este registro entrar em `main` e o CI passar, a versão exige assinatura própria: `bash scripts/aprovar.sh relay-council-panel-ui-rebase3-20261028`. O executor não executa o comando.
