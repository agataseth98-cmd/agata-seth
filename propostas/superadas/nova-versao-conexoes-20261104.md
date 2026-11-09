# Proposta `nova-versao-conexoes-20261104` — nova versão, lote 2: conexões de modelos, redundância e coordenação

**O que é, em português comum:** o Agata ganha um jeito único de se ligar a qualquer modelo, por três caminhos:
- **navegador:** o Conselho em Rede, em que você aprova cada envio;
- **programa da sua assinatura:** `claude` e `codex`, que já estão instalados;
- **API com chave.**

Claude e ChatGPT entram como os dois exemplos preenchidos, para outros usuários ligarem os modelos que preferirem pelo mesmo formato.

A chave de API é digitada numa aba segura do painel (Nova versão → Conexões de modelos). Ela vai para um cofre só de escrita e nunca volta para a tela.

Um botão testa cada rota em três provas fixas (conversa, JSON e código) e mostra quem passou em cada capacidade. Só isso conta como redundância.

Nada é chamado sem você ligar a categoria no orçamento. Pago só gasta com tarifa datada e teto em R$.

**Decisões do Humano (04/11/2026):**
- "as duas são: Claude e Chat GPT. Devem servir de exemplo para futuros usuarios conseguirem conectar as de sua preferencia";
- "todas as opções disponiveis e o preenchimento de API deve ter aba segura de configuração onde fizer mais sentido no painel".

## O que entra

| Arquivo | O quê |
|---|---|
| `redesign/conexoes/provedores.json` | catálogo com `claude` e `chatgpt` nos três caminhos e a categoria de orçamento de cada caminho |
| `redesign/conexoes/segredos.py` | cofre `~/.config/agata/conexoes/` (pasta 0700, chave 0600, gravação atômica); o estado diz só se a chave existe; gravar e remover viram evento sem valor. Não toca no `~/.config/agata/.env` |
| `redesign/conexoes/adaptadores.py` | contrato único. Por navegador nunca envia. O programa roda em pasta temporária vazia, sem ferramentas e sem sessão. API nos formatos `anthropic` e `openai`. Antes de sair, passa por três portas: orçamento, privacidade (`sanitizar.py`) e custo (tarifa datada e teto em R$). Provedor novo pelo painel: só API e só https |
| `redesign/conexoes/testar_rotas.py` | redundância por capacidade: rotas locais, gratuitas, de assinatura e pagas; três provas mecânicas; independência descrita; a resposta não é guardada; as filas do OmniRoute não mudam |
| `redesign/conexoes/README.md` | guia para outros usuários ligarem o seu modelo |
| `redesign/nova_versao/tarefas.py` | coordenação: `task_id`, versão de contexto, prazo, teto de chamadas, cancelamento, GPU em fila única, escritor único; contexto mudado manda o resultado para revisão |
| `redesign/nova_versao/orcamento.py` | categoria nova `assinatura` (cota do plano, não R$), desligada por padrão |
| `redesign/corpo/fotografar.py` | `testado` e `pronto` passam a vir do último teste de rotas |
| painel | página "Conexões de modelos" (estado por caminho, modelo e tarifa, chave em campo `password`, provedor novo, testar e cancelar), caixa "assinatura" no orçamento, 6 ações novas de lista fechada, spec e testes |
| `CHAVES.md`, `PROJETO_REFERENCIA.md`, `redesign/README.md`, `.github/workflows/sdd.yml` | onde fica a chave, a linha do lote 2, a tabela e a CI do componente |

## Evidência (worktree, 04/11/2026)

- **Testes:** pytest com 146 verdes. São as suítes da CI mais `redesign/conexoes/tests` e `redesign/nova_versao/tests/test_tarefas.py`. Depois de aplicar este `.diff` sobre `origin/main` (`43ad732e`), 88 continuam verdes.
- **SDD:** âncora OK em 11 componentes. Critérios: 25 `pass` nos quatro manifestos tocados. O ciclo SDD da spec-mãe terminou com código de saída 0. `nv.py --selftest` OK.
- **Teste real só local,** com dados de rascunho e `--limite 2`: `lumi-4b` e `qwen3-30b-a3b-64k` passaram em conversa, formato e código.
- **Estado real das conexões:**
  - Claude: programa instalado; API sem chave e sem tarifa.
  - ChatGPT: programa instalado; API sem chave, sem modelo e sem tarifa.
  - Navegador: adaptador `experimental` nos dois.
- **Painel no navegador:** página carregada, sem erro no console. Testei numa porta temporária porque o painel vivo estava ativo na 20146.

## Não medido

- **Login dos dois programas:** só se confirma no primeiro teste. Não rodei para não gastar a cota da sua assinatura sem você ligar a categoria.
- **Chamadas pagas reais:** não há chave.
- **Modelo vigente do ChatGPT na API:** ficou vazio de propósito; você escolhe no painel.
- **Egresso pela API:** não passa pelo sanitizador. Neste lote só as provas fixas saem; a integração com o caminho real (lote 4) precisa passar por ele.

## Reversão

Revert do commit de aplicação. Apagar `~/.config/agata/conexoes/` remove chaves e ajustes.
