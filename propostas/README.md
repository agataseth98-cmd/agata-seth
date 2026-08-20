# propostas/ — quarentena de mudança estrutural (P-8)

Mecanismo criado em 20/08/2026 (item 6 do documento do Humano, proposta do Marcos, MEMÓRIAS (218)). Cobre o buraco descrito ali: até então, o executor escrevia em canon, comitava e empurrava — o Humano ficava sabendo depois. Nenhuma checagem do perímetro cobria isso.

## Escopo (proporcional de propósito)

**QUARENTENA OBRIGATÓRIA** — arquivos que MUDAM COMPORTAMENTO:
- `REGRAS.md`
- `PROJETO.md`
- `scripts/*`
- `.githooks/*`
- `config/*` (incluído 20/08/2026, MEMÓRIAS (222) — um prompt que dirige um modelo autônomo contra o canon muda comportamento tanto quanto um script)

**SEM quarentena** — arquivos que só REGISTRAM o que já aconteceu:
- entradas de `MEMÓRIAS.md`
- `ONDE_ESTAMOS.md`
- `INDICE_MEMORIAS.md`
- `.hermes.md` (gerado)
- `PROMPT_CARREGAMENTO.md` (movido pra dentro do repo 20/08/2026 — dirige um modelo, mas sempre com Humano lendo a resposta antes de agir, ao contrário de `config/agata-consolidacao.prompt.txt`; ver PROJETO.md, "Quarentena estrutural")

Motivo da linha: registro errado se corrige com entrada nova — é pra isso que append-only existe. Comportamento errado, não.

## Mecanismo

1. A mudança proposta vira `propostas/<nome>.diff` (formato `git diff`, com cabeçalhos `--- a/<caminho>` / `+++ b/<caminho>`) e fica aqui, versionado.
2. O Humano aprova criando `propostas/APROVADO-<nome>` (arquivo vazio ou com nota — o conteúdo não importa pra P-8, só a presença).
3. `scripts/perimetro.sh`, checagem P-8: FALHA o commit se algum arquivo staged do grupo "muda comportamento" não aparecer nos cabeçalhos de nenhum `.diff` com `APROVADO-` correspondente presente em `propostas/`.
4. Aprovação consumida: ao entrar no canon, quem aplica move o par `<nome>.diff` / `APROVADO-<nome>` para `propostas/aplicadas/` no mesmo commit que aplica a mudança.

## Risco residual (não suavizado)

O marcador de aprovação é um arquivo que o próprio executor TEM PERMISSÃO técnica de criar. P-8 impede automação agindo sem que ninguém perceba — que foi exatamente o caso de 18/08/2026 (MEMÓRIAS (214)) — e NÃO impede um modelo que decida contornar deliberadamente. Aceito por decisão do Humano: a ameaça real aqui é desatenção, não malícia. Se um dia for preciso mais, o caminho é assinatura que o executor não possa produzir, com o custo de o Humano digitar uma senha a cada mudança estrutural.
