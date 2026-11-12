# História canônica do Agata

A História é o relato do que o sistema fez, texto por texto, organizado em tomos. Este diretório guarda os textos. O painel (seção História) lê daqui, só para leitura.

## Para modelos (LLM first)

- Escrita primeiro para modelos retomarem o fio: o texto diz o que foi feito, por que e o que ficou aberto. A leitura do Humano vem depois.
- Lembrança do modelo não é conhecimento do sistema (decisão do Humano, 07/11/2026, cache do Conselho, entrada 421). Antes de citar, leia a prova no repositório, no cache do Conselho ou em MEMÓRIAS.
- Cada afirmação verificável traz uma marca de origem (regra F0):
  - `[medido]`: conferido na Máquina (git, testes, arquivos, navegador);
  - `[relato]`: dito pelo Humano ou por outro modelo, sem reprodução independente;
  - `[inferência]`: leitura do autor, sem prova.
- Textos são append-only. Correção vira texto novo, que diz o que corrige. Texto publicado não se edita (Regra 4).
- Citação inventada se expurga (AGENTS.md). Achada num texto, troca-se o trecho por `[citação inventada, expurgada em DATA por ordem do Humano]` e confere-se com `grep -F`.

## Estrutura

`tomo-NN/NN-titulo.md`, com frontmatter:

- `tomo`, `titulo_tomo`, `texto`, `titulo`, `periodo`, `autor`, `estado`, `protocolo`.

`estado` diz se o texto é canônico. Sem assinatura do Humano, o texto é rascunho.

## Lente

Até virar regra, a História é lida pela lente do Protocolo de Inclusão Humana contínua (brainstorm de 07/11/2026, guardado fora do repositório, na Área de trabalho do Humano).

## Mudança

Este diretório está na quarentena do P-8 (`scripts/perimetro/p08_quarentena.sh`). Nenhum modelo muda a História sem o par `.diff` e `APROVADO-` assinado em `propostas/`.
