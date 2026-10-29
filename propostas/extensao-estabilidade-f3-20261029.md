# Proposta: Fase F3, estabilidade da extensão do Conselho (29/10/2026)

Motivo: observado várias vezes hoje. Depois do reinício do navegador, a aba do provedor é restaurada descarregada. A resposta aparece na tela, mas a extensão não a lê (Kimi, Qwen, Mistral). Além disso, o texto novo era anexado a um rascunho já existente na caixa, o que duplicou o envio no Kimi.

Mudanças em `redesign/painel_operacional/relay-extension-v2/`:
- `background.js`:
  - aba descarregada é recarregada e a página é esperada completa antes de escrever ou ler (`ensureTabLoaded`, erro `sem_carregamento`);
  - antes de escrever, a caixa é limpa (`clear`); se não limpar, o envio é cancelado (`composer_nao_limpo`);
  - se a resposta não for lida, o item termina com `sem_leitura` e não é reenviado.
- `content/_common.js`: novo comando `clear`, que esvazia a caixa visível e confere que ficou vazia.
- Teste novo `ExtensionStabilityTests` em `test_conselho_rede.py`: confirma as proteções e que a extensão não pede permissão `cookies`.

Validado: sintaxe `node --check` nos dois arquivos; teste novo passa.

Não validado ao vivo: o efeito de recarregar a aba restaurada e de limpar a caixa de cada provedor. Depende de um teste aprovado depois da aplicação.

Aplicação: depois da assinatura (`bash scripts/aprovar.sh extensao-estabilidade-f3-20261029`). A extensão precisa ser recarregada no Chromium do sistema.
