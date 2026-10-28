# Proposta P-8 — fronteira do RelayCouncil para integração

## Objetivo

Substituir a proposta contract-only v1 `relay-council-contrato-20261028` por uma fronteira que possa entrar na integração do painel oficial. O contrato aceita resultado de API oficial ou entrada manual; recusa `browser_dom`. O catálogo contém 17 provedores, sem Perplexity. Só cinco aparecem hoje no roster de API do Conselho Remoto; os demais continuam candidatos.

## O que muda

- `redesign/router/relay_council_contract.py`: contrato v3, lista fechada dos 17 IDs, campo obrigatório `access_mode` (`official_api` ou `manual`), normalização de estado, limites e timestamp com fuso. Campos desconhecidos são descartados; chaves com nomes que indiquem credenciais, cookies ou sessão são recusadas. O contrato não detecta valores secretos dentro de texto livre; o consumidor ainda precisa usar o sanitizador antes de gravar ou encaminhar texto.
- `redesign/painel_operacional/relay_catalog.py`: roster de 17 IDs. `in_roster` significa apenas que o modelo consta em `scripts/conselho_remoto.py`; não afirma disponibilidade atual nem resposta verde. `candidate` requer validação de API, condições e conta antes de ativação.
- Os testes garantem que o contrato rejeita DOM e provedores fora do roster, e que nenhum item do catálogo declara automação DOM.

## Auditoria do protótipo e fronteira de dados

Leitura estática do protótipo em `Área de trabalho/relay-council-integracao-NBKY0Z/workspace`:

- `extension-v2/manifest.json` pede `activeTab`, `scripting`, `storage`, `tabs` e `alarms`; inclui origens dos nove serviços e do painel local `127.0.0.1:20147`. Não declara a permissão `cookies`.
- `extension-v2/background.js` localiza abas, ativa a aba do turno, envia comandos de escrita/envio/leitura ao content script e faz poll e POST apenas para `http://127.0.0.1:20147`.
- Os content scripts escrevem o prompt e leem o resultado no DOM. O site do provedor recebe o prompt pelo próprio fluxo autenticado da página. Não encontrei leitura direta de senha, cookie ou token pelo código inspecionado. A sessão autenticada do perfil é usada indiretamente pela página.
- `painel-ui/painel_conselho.py` grava o histórico em `~/.local/share/agata/painel-conselho/history.jsonl` e encaminha respostas ao serviço local `127.0.0.1:20148`, que as sanitiza antes do cache compartilhado. Os dados do histórico ficam fora do repositório.

Essa auditoria descreve o protótipo observado; não prova o conteúdo de arquivos ignorados nem o tráfego interno dos provedores. O contrato proposto não incorpora a extensão, o perfil do navegador ou cookies ao painel oficial.

## Condições de acesso

O protótipo automatiza a interface web. As fontes oficiais consultadas proíbem ou restringem partes desse uso: os termos da OpenAI vedam extração automática/programática de dados ou saídas; o acordo do DeepSeek restringe coleta/cópia automatizada; os termos de Qwen vedam interação/extração automatizada; os termos de Z.ai restringem automação não autorizada; os termos web do Groq vedam automação e extração. O acesso por API segue termos próprios e exige revisão por provedor. Fontes: [OpenAI](https://openai.com/policies/terms-of-use/), [DeepSeek](https://platform.deepseek.com/downloads/DeepSeek%20User%20Agreement.pdf), [Qwen](https://qwen.ai/termsservice), [Z.ai](https://chat.z.ai/legal-agreement/terms-of-service), [Groq](https://console.groq.com/docs/legal).

Por isso esta proposta não ativa automação DOM. Para Claude, Grok, Mistral, Kimi e candidatos sem conclusão na fonte consultada, o acesso também permanece API oficial ou manual até verificação específica. Não há bypass de CAPTCHA, detecção de bot, limites ou restrições de provedor.

## Limite desta etapa

Este P-8 prepara o contrato e o roster. Ainda não adiciona a interface do RelayCouncil ao painel oficial, não altera serviços, não abre abas e não faz chamadas externas. Depois da assinatura e aplicação desta etapa, a próxima proposta poderá integrar a interface usando apenas APIs autorizadas e entrada manual, com histórico fora do repositório. A extensão do protótipo continua fora do caminho oficial.

## Verificação

Em cópia descartável de `origin/main` (`ef9c794`), o diff aplicou sem conflito. Passaram 10 testes do contrato, 4 do catálogo, `py_compile` dos módulos novos e `git diff --check`.

## Aplicação

Esta proposta supersede `relay-council-contrato-20261028`, que só introduzia o contrato v1. O Humano revisa `relay-council-integracao-20261028.diff` e assina pelo fluxo P-8. O executor não cria `APROVADO-*` e não aplica a mudança.
