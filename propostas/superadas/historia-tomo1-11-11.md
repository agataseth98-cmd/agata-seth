# História canônica, Tomo I, Texto 1, e aba História no painel — proposta de 11/11/2026

Proposta P-8 de `historia-tomo1-11-11`. Diff: `propostas/historia-tomo1-11-11.diff` (sha256 `d76841ae0d519a0252fa4ff2e916d209ac75cf21cc6dfb66453da2d7289fed9a`). Base do diff: `182310d0`; aplica limpo sobre `origin/main` `bdbdca6c` e sobre `d782dad0` (conferido com `git apply --check`, a segunda vez depois da mesclagem de `origin/main` nesta branch). Assinatura do Humano, uma vez, depois do merge deste PR de proposta.

## Em resumo (para o Humano)

- Cria a pasta `historia/` com o Texto 1 do Tomo I, copiado sem alterar o texto escrito pelo orquestrador, e um README curto para modelos.
- Põe `historia/` na quarentena P-8: nenhum modelo muda a História sem o par assinado.
- Acrescenta a seção História ao `/prototipo` (agora oito seções): índice de tomos à esquerda, texto à direita, somente leitura.
- O botão Ouvir lê o texto com a voz do sistema (`scripts/agata_falar.py`) e diz se falou. Não foi clicado nas medições: falaria no alto-falante.
- Cada decisão de escopo e cada número estão abaixo, com o que não foi medido.

## O que muda (14 arquivos no diff)

- `historia/README.md` (novo): o que é a História, LLM first, marcas F0, regra append-only, expurgo de citação inventada, estrutura `tomo-NN/NN-titulo.md`, a lente do Protocolo de Inclusão Humana contínua (brainstorm de 07/11, fora do repositório).
- `historia/tomo-01/01-a-casa-propria-da-conversa.md` (novo): cópia do texto de `agata-documentacao/historia/tomo-01/`. Conferido por `sha256`: `fe79c529046075dcf03f713eec10b91d7f9b13936cd4c561122408d68eb9906a` nos dois lados. Estado no frontmatter: "rascunho para proposta P-8; não canônico até a assinatura do Humano".
- `scripts/perimetro/p08_quarentena.sh`: uma linha `historia/*) return 0 ;;` em `_p8_eh_comportamento`, com comentário. Por isso este diff pede assinatura: toca `scripts/*`.
- `redesign/painel_operacional/historia_painel.py` (novo): lê `historia/` do checkout. Funções: `listar`, `ler`, `ouvir`, `frontmatter`. Caminho e tomo com formato fixo; link para fora de `historia/` é recusado; uma fala por vez (lock).
- `redesign/painel_operacional/server.py`: rotas `GET /api/historia`, `GET /api/historia/texto`, `POST /api/historia/ouvir` (origem própria e JSON, corpo até 512 bytes) e o ativo `/historia.js`.
- `redesign/painel_operacional/historia.js` (novo): índice, leitura e Ouvir. Markdown mínimo montado só com `createElement` e `createTextNode`. As marcas `[medido]`, `[relato]` e `[inferência]` viram etiquetas com classe própria.
- `redesign/painel_operacional/prototipo.html`, `prototipo.js`, `prototipo.css`: seção `historia` depois de `conhecimento`, botão de menu, estados carregando/vazio/erro, tokens de cor do `:root`.
- `redesign/painel_operacional/test_historia.py` (novo): 19 testes (rota, voz falsa, origem, UI no node, consistência com `historia/`, P-8 e emoji).
- `redesign/painel_operacional/test_painel_unificado.py`, `test_menu_painel.py`: `SECOES` passa de 7 para 8. Os testes "sete seções" viram "oito seções".
- `redesign/painel_operacional/spec/spec.md` e `spec/acceptance.json`: seção História no escopo, nas rotas, nos ativos, no mapeamento de funções e nos critérios (15 novos; o de sete seções vira oito). `Código` lista os três arquivos novos.

## Registro fora do diff

- `MEMÓRIAS.md`: entrada (992), abaixo do marcador. Os números 990 (`spec-primeiro-11-11`, PR #968) e 991 (`painel-importantes-11-11`, PR #969) já estão no `main`.
- `ONDE_ESTAMOS.md`: uma linha na tabela de lotes em andamento.
- Nenhum desses dois arquivos está no P-8 (`scripts/perimetro/p08_quarentena.sh` não protege registro).

## Decisão para o Humano confirmar na assinatura

- Pôr `historia/` na quarentena foi pedido direto ("para que nenhum modelo mude a História sem assinatura"). Pela regra antiga, a quarentena cobre comportamento, e texto de canon não é código. O diff trata `historia/` como quarentenado mesmo assim. Se não quiser, a linha sai e o diff fica menor.

## Testes medidos

- Suíte do painel (`cd redesign/painel_operacional && python3 -m unittest discover -s . -p "test_*.py"`, com o node do scratchpad no PATH): 342 testes, 1 falha. A falha é `test_sdd_painel.ProjetosExternosTests.test_executar_projeto_roda_o_ciclo_e_recusa_o_que_nao_esta_em_config_sdd`, já registrada como pré-existente em MEMÓRIAS (489), (491) e (986). Não é desta mudança. Dono e data dessa falha: não registrados.
- `test_historia.py` isolado: 19 testes, todos passam.
- CI local (`uv run --offline --with pytest bash scripts/ci_sdd_local.sh`): `CI LOCAL: TUDO OK`, 33 passos OK, código 0.
- Aplicação do diff: `git apply` sobre `origin/main` `bdbdca6c`, com os 12 arquivos de código comparados com a cópia testada (`cmp`): todos idênticos. Depois da conferência, a árvore foi revertida.
- Texto 1 para fala: `scripts/agata_falar.py --preparar` deu 11980 caracteres. O teto de fala é 12000. Um texto maior seria recusado com código 2, e o painel diria "não falei".

## Captura da aba (Chromium headless, servidor na porta 20255, HOME falso)

- `historia-aba.png` (1440 px): menu com História entre Conhecimento e Custos; índice com o Tomo I; texto com títulos, listas, negrito e as três marcas. Medido: 48 nós no corpo, 1 h2, 1 h3, 9 marcas `medido`, 6 `relato`, 3 `inferência`; largura do texto 664 px; corpo 17 px.
- `historia-indice.png`: índice rolado para o topo da coluna.
- `historia-aba-390px.png` (390 px): colunas empilhadas. Medido: largura da página 390 px, igual à janela, sem rolagem horizontal.
- Console: um erro 404, de `/favicon.ico`, que o servidor não tem (já existia). Uma mensagem DOM de campo de senha sem formulário, que também já existia. Nenhum erro de CSP.
- O botão Ouvir não foi clicado na captura.

## Não medido

- O Ouvir com a voz real: testado só por HTTP com voz falsa. A fala real não foi disparada.
- Desempenho do botão Ouvir: um texto de 12000 caracteres pode levar minutos. O pedido fica aberto até o fim da fala. Não há botão Parar.
- Comportamento com mais de um tomo ou texto: só existe o Texto 1.
- Efeito da quarentena de `historia/` no fluxo de propostas: não medido; a primeira assinatura será a medição.

## Limite R1 (duas propostas abertas por componente)

- Medido em `propostas/*.diff` sem `APROVADO-`, em `origin/main` `d782dad0`: três propostas abertas tocam `redesign/painel_operacional/`: `chat-lote4-09-11`, `painel-importantes-11-11` (PR #969, entrou no `main` depois da abertura desta) e esta.
- Com as três, o painel passa do limite de duas. A regra R1 ainda não está em vigor (`processo-agil-11-11` sem assinatura), então esta proposta não é barrada. O número fica registrado para a fila de assinatura.
- A História é componente novo: não há outra proposta dela na fila.
- Nenhuma proposta foi aplicada nem superada por esta.

## Conflito com `painel-importantes-11-11`

- As duas mudam os mesmos arquivos do painel (`prototipo.css`, `prototipo.html`, `prototipo.js`, `server.py`, `spec/spec.md`, `spec/acceptance.json`, `test_painel_unificado.py`). Cada diff aplica sozinho sobre o `main` atual (conferido com `git apply --check`). Aplicadas juntas, a segunda precisa de rebase.
- Ordem sugerida: assinar e aplicar a que entrar primeiro; a outra é refeita sobre o resultado antes de ser aplicada, com o teste do painel de novo.

## Apetite (R2, declarado)

- Apetite declarado agora, depois da medição: até 15 arquivos e 2 h de agente (estimativa).
- Medido: 14 arquivos no diff (2 em `historia/`, 11 em `redesign/painel_operacional/`, 1 em `scripts/perimetro/`). Dentro do apetite.
- Horas de agente: medido com `date`, de 19:42 a 19:57 pelo relógio, incluindo a espera do CI local. Dentro do apetite.

## Checklist de pronto (R3)

- [x] CI local `TUDO OK` (33 passos), saída colada acima.
- [x] Suíte do painel: 342 testes, 1 falha pré-existente, nomeada acima.
- [x] Captura de tela da aba em 1440 px e 390 px, medições colhidas.
- [x] Sem emoji: conferido por teste (`test_sem_emoji_na_historia`) nos arquivos novos da História.
- [x] Texto do Tomo I copiado sem alteração, conferido por `sha256`.
- [ ] Run verde no GitHub no `headSha` do PR: preenchido depois do push.
- [ ] Dono e data de `test_sdd_painel`: não registrados; pendência para o Humano.

## Artefatos regravados pelo CI local (fora do diff)

- O `ci_sdd_local.sh` regravou `redesign/nova_versao/spec/criterion-drift.md`, `redesign/nova_versao/spec/evidence.json` e criou `redesign/sdd_flow/spec/criterion-drift.md` e `evidence.json`. Foram revertidos antes da proposta. Não entram no diff nem no PR.

## Reversão

- Proposta própria que aplica `propostas/aplicadas/historia-tomo1-11-11.diff` ao contrário (`git apply -R`), assinada à parte. Entradas de MEMÓRIAS são append-only: a reversão do registro é entrada nova.

## Assinatura

Depois do merge deste PR, o Humano roda:

```
bash scripts/aprovar.sh historia-tomo1-11-11 "<motivo>"
```

Verificação depois da assinatura, no checkout vivo, com `git rev-parse HEAD` igual a `origin/main`:

```
bash scripts/p8_verificar.sh historia-tomo1-11-11
```
