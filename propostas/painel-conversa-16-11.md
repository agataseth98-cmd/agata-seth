# Painel conversa 16/11: conversa da Seth no padrão de chat, menu único, Conhecimento numa tela e filtro de estilo (`painel-conversa-16-11`)

Classe: Comportamento (código e spec do painel) e skill do painel (`.agents/skills/agata-painel/`, com `ESTILO.md` novo).

Proposta P-8 de `painel-conversa-16-11`. Diff: `propostas/painel-conversa-16-11.diff` (18 arquivos, 6764 linhas). Base: `origin/main` (5205dc4c). O diff não traz registro, derivados nem `ONDE_ESTAMOS.md`; esses entram no PR de proposta, fora do diff assinado.

Decisões do Humano (16/11/2026):
- às 14:46: "o painel está confuso e precisa ser responsivo para todos os tamanhos, todo o conhecimento tem que estar na mesma tela, e a tela de conversa com a Seth tem que ter o padrão ChatGPT e Claude de design, com seu menu integrado ao menu geral e sem redundâncias, todas as funções úteis em um chat com modelo LLM tem que estar disponiveis"
- às 18:27: "esse estilo é o último filtro de requinte a partir de agora, estabeleça."

## O que muda

1. Menu único: nova conversa, busca e a lista de conversas no menu geral, agrupadas por data, com as ações de cada conversa num menu, e uma janela para organizar (pastas, filtros, importar).
2. Tela da conversa: coluna de leitura, estado vazio com sugestões, compositor fixo com Ditar, Anexar, Enviar e Parar, ir para o fim, altura da janela.
3. Funções de chat: Markdown com tabela, citação, lista numerada e código com copiar; links com endereço visível e sem navegação externa; hora na mensagem; rascunho por conversa só em memória; tentar de novo no erro; instruções por conversa; anexo de texto por botão, arrastar ou colar; uso do contexto informado pelo gateway.
4. Servidor: hora, instruções e metadado de anexo gravados; anexos e instruções no pedido, com filtro; teto do corpo em 262144 bytes; parar fecha a chamada ao gateway; recusa de instrução de sistema escondida nas mensagens.
5. Conhecimento numa tela só, com âncoras.
6. Estilo: o painel inteiro pelo filtro (plano, borda de 1px, um acento, paleta e tipografia da referência, sem sombra nem gradiente), responsivo com quatro pontos de quebra e gaveta em tela estreita.
7. Skill do painel com o filtro de estilo (`.agents/skills/agata-painel/ESTILO.md`) e a regra de medir com navegador que só deixa passar leitura.
8. Spec com 105 critérios novos (número informado pelo agente de spec; não recontado por mim).

Mudanças de comportamento para o Humano confirmar:
- pergunta que falha fica na conversa com "Tentar de novo";
- o botão "Abrir conversa da Seth" do Panorama saiu (o menu abre a Conversa);
- o anexo grava só nome e tamanho.

Não existe e não foi criado: imagem na conversa, compartilhar, mais modelos no seletor.

Fica para lote seguinte: fundir listas repetidas do Sistema e telas de equipe, perímetro, CI, backup e saída de rede em Rust; divergência de texto entre a spec-mãe e a de conexões.

## Medido (16/11/2026)

- CI local (`scripts/ci_sdd_local.sh`, com `PYTEST` do cache do uv, `pytest 9.2.0` confirmado por `--version` antes da rodada): última linha `CI LOCAL: TUDO OK`; 88 linhas `OK`, 0 `FALHA`; rc=0. Log: `/home/orusoua/agata-arquivo/auditoria-conceito-16-11/painel/ci-local-conversa-final.log`. O log não traz a versão do pytest; ela está no `--version` acima.
- Cópia limpa de `origin/main` (worktree `check-painel-conversa-16-11`): `git apply --check` retorna APLICA; `git apply` roda sem erro.
- Na cópia limpa, com o diff aplicado:
  - `scripts/testar_sem_goose_ativo.py`: 6 testes OK, rc=0.
  - `scripts/testar_tira_librechat.py`: 5 testes OK, rc=0.
  - `scripts/gate_spec_sync.py`: rc=0, 0 falha; 1 aviso sobre `alexandria` (componente fora deste diff; por inferência, pré-existente, não medido em `origin/main`).
  - `redesign/sdd_flow/anchor.py . redesign/painel_operacional`: `ANCHOR: OK`, rc=0.
  - Suíte do painel (`unittest discover`, 659 testes): 1 falha em `test_sdd_painel`, `ProjetosExternosTests.test_executar_projeto_roda_o_ciclo_e_recusa_o_que_nao_esta_em_config_sdd`. É a falha conhecida e aceita (pytest fora do PATH, segundo o relato do coordenador). A causa não foi lida por mim.
- Medido pelo agente de estilo (relato, não reconferido por mim): 64 combinações de largura sem rolagem horizontal; contraste mínimo calculado 5,16:1. Fotos em `/home/orusoua/agata-arquivo/auditoria-conceito-16-11/painel/` (pastas `estilo-antes`, `final` e `final-interacao`, existência conferida por listagem).

## Não medido

- Leitor de tela.
- Voz e ditado na tela nova.
- Anexar, arrastar e colar em navegador real.
- Tema claro em todas as seções.
- O que a via pública faz com as instruções.
- A página real na porta 20146 (só depois de aplicar e reiniciar).
- Horas de agente: cerca de 4 horas (estimativa do coordenador, não medida).
- Código sem emoji: não conferido no diff (só o `.md` foi conferido).

## Apetite

Os caminhos do lote (18 arquivos). Cerca de 4 horas de agente (estimativa).

## Reversão

`git apply -R propostas/aplicadas/painel-conversa-16-11.diff` numa worktree, por proposta; depois reiniciar `painel-operacional.service`.

Leitura pelo código antigo (lido em `origin/main`, `redesign/painel_operacional/armazem.py`, não executado): as conversas com os campos novos continuam legíveis. `_conversa_ler` valida com `_conversa_validar(leve=True)`, que monta a conversa só com os campos conhecidos (titulo, modelo, mensagens, arvore, ramificada_de); chave desconhecida é ignorada, não derruba a leitura. `_mensagem_limpa` monta cada mensagem só com role, content, modelo, modelo_real, interrompida, feedback e cortes. Os campos novos somem na leitura (instruções no topo; hora e anexos em cada mensagem).
Risco: se o código antigo salvar uma conversa de novo, `_formato_gravar` grava só os campos conhecidos, e instruções, hora e anexos se perdem nesse salvamento. Não medido: o código antigo não foi rodado sobre um arquivo com os campos novos; a resposta é leitura de código.

## Comando de assinatura

Depois do merge deste PR, no terminal, sem `!`:

bash scripts/aprovar.sh painel-conversa-16-11

## Modelos

Claude Fable 5.2 coordenou; agentes Claude Haiku 5.5 implementaram, revisaram e montaram a proposta.

## Definição de pronto (R3)

- [x] CI local com `CI LOCAL: TUDO OK` (log acima)
- [ ] run verde no GitHub no `headSha` do PR (fica no registro do PR)
- [x] captura de tela: fotos em `~/agata-arquivo/auditoria-conceito-16-11/painel/` (medidas pelo agente de estilo)
- [x] sem emoji no `.md`; no código não conferido
- [x] testes medidos, o que não foi medido e a reversão (acima)
- [ ] nenhuma falha pré-existente sem dono e data: a falha de `test_sdd_painel` é conhecida; dono e data a definir pelo Humano
- [x] texto da entrada de MEMÓRIAS sem citação `caminho:número` (conferido com grep depois de escrever)
