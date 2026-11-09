# Proposta painel-unificado-07-11

Registro para uma assinatura P-8. Ainda não assinada nem aplicada. O arquivo `.diff` contém o código proposto; a assinatura continua sendo do Humano.

- Base: `origin/main` = `83334fde2f3bfa49bf487e6ce4051b7b2a338bb3`.
- Worktree de proposta: `.claude/worktrees/painel-pr950-atualizacao-20261108`.
- Diff: `propostas/painel-unificado-07-11.diff`.
- SHA-256: `fccf652257aac35dfea2e4051d9d748f222edf64ed15b995f89b06d98a26762`.
- Escopo: 33 arquivos, todos em `redesign/painel_operacional`; 3344 adições e 1779 remoções.
- `git apply --check` passou sobre a base limpa `83334fde`.

## O que esta assinatura aprova

- Unifica o painel em sete seções, preserva as funções mapeadas e redireciona as telas antigas.
- Adiciona a aba somente leitura `Conselho > Memória compartilhada`, alimentada pelo cache do Conselho com filtro de dados sensíveis.
- Corrige a leitura de conversa salva para devolver `schema_version` e `id`; regravar preserva o mesmo ID e não duplica o arquivo. O limite por mensagem passa de 8000 para 65536 caracteres, respeitado o teto existente de 262144 bytes por requisição.
- Restringe a ação de abrir conselheiros ao botão de entrada da seção, para cliques dentro dos subpainéis não dispararem `/api/abrir`.
- Corrige o critério da spec que descrevia as rotas como inalteradas apesar da nova rota de memória, e liga os critérios aos testes correspondentes.

O pacote inclui a correção do identificador tratada na PR #945; o teste abre a conversa, devolve `id` e `schema_version`, salva novamente com o mesmo ID e confirma que permanece um arquivo.

## Verificação registrada

- Cinco testes focados passaram, incluindo leitura e salvamento da conversa, limite de mensagem, rota somente leitura e clique no menu do Conselho.
- `bash scripts/ci_sdd_local.sh`: `CI LOCAL: TUDO OK`.
- Acceptance runner e drift da spec passaram para o painel.
- `git diff --check` passou.
- Medição de navegador anterior nesta mesma interface: aba de memória mostrou 40 entradas; o filtro “Decisão”, 9; estados vazio, erro e carregando foram exibidos; sem violação de CSP. Essa medição foi na prévia local e não substitui a prova na porta 20146 depois da aplicação.

## Limites e escopo deliberado

- Não altera gateway, regras de roteamento automático, provedores, credenciais, serviço systemd ou outros arquivos fora do painel.
- A conversa continua usando as rotas e o comportamento de stream atuais. Cancelamento do upstream e medição de custo não fazem parte desta assinatura.
- O preview em porta alternativa pode responder 403 a `POST /api/abrir` por causa da origem fixa no harness; isso não foi observado como efeito do diff na porta de produção.
- O visual em 390 px, a conversa com provedor real e a prova final das sete seções na porta 20146 ficam para depois da aplicação. Nenhum serviço foi reiniciado.

## Caminho após a assinatura

Depois que esta proposta estiver em `main`, o Humano assina uma vez com `bash scripts/aprovar.sh painel-unificado-07-11`. Em seguida, o processo cria a PR de aplicação; só após ela entrar em `main` o serviço é atualizado e medido pelo caminho real.
