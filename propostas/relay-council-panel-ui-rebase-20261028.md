# Proposta P-8 — Conselho de Modelos em Rede (base atualizada)

**Nome para assinatura:** `relay-council-panel-ui-rebase-20261028`
**Base:** `main` após PR #681, commit `08cb1f7541c0bc44015cf00d27d237b2dff49689`.

## Motivo da nova versão

A versão inicial foi assinada e aplicada na branch de aplicação, mas o `main` avançou antes do merge. A nova entrada (907) de `aplicar-refazer-base-20261028` ocupou o mesmo número reservado pela proposta inicial. O PR de aplicação #682 ficou conflitante. A assinatura antiga continua vinculada ao hash original e não será reaproveitada para um diff diferente.

Esta proposta preserva o conteúdo da interface e atribui o número livre (908) à nova entrada de memória. A primeira proposta e sua assinatura não são alteradas.

## Mudança proposta

Adicionar a página em português **Conselho de Modelos em Rede**, com consulta ao catálogo local de 17 provedores e registro manual de resultado observado. O registro passa pelo endpoint local existente e acrescenta uma avaliação sanitizada ao cache comum do Conselho.

## Limites

- Não envia prompts, não chama provedores e não automatiza DOM.
- Não lê abas, cookies, sessões ou credenciais.
- Não reinicia serviços nem altera o painel em execução.
- Para modo API oficial, a resposta deve ter sido obtida fora da interface por uso autorizado.

## Arquivos

- `redesign/painel_operacional/prototipo.html`, `prototipo.js`, `prototipo.css` e `README.md`
- `ONDE_ESTAMOS.md`
- entrada nova (908) em `MEMÓRIAS.md`

## Verificação

- Selftest do painel: OK.
- `python3 -m unittest redesign/painel_operacional/test_painel.py`: 22 testes OK.
- `node --check redesign/painel_operacional/prototipo.js`: OK.
- Chromium isolado: 17 provedores, envio simulado sem gravação, sem overflow desktop/celular.
- A nova base contém a entrada (907); o diff corrigido adiciona (908) sem duplicar numeração.

Após entrar em `main` e passar CI, a nova versão exige assinatura própria: `bash scripts/aprovar.sh relay-council-panel-ui-rebase-20261028`. O executor não executa o comando.
