# Seth base: modelo servido no log, cabeçalho único e tool_call em texto convertido com regra estrita (`seth-base-17-11`)

Classe: Comportamento (runtime: `seth_gateway.py`).

Proposta P-8 de `seth-base-17-11`. Diff: `propostas/seth-base-17-11.diff` (3 arquivos). Base: `origin/main` (36f9e438). O diff não traz registro nem `ONDE_ESTAMOS.md`.

Origem: auditoria da Seth em 17/11/2026 (por que a Seth não é confiável: modelo servido não registrado, tool_call saindo como texto, cabeçalho ausente). Decisão do Humano: roteador por capacidade em produção com retorno fácil.

## O que muda

1. `_modo_roteador()`: lê `SETH_ROTEADOR` (padrão `legado`); nada muda na rota com o padrão.
2. Log: `served_by` em toda linha e uma linha "ok" por resposta 200 de chat; `429_pausaria=<fila>` só mede (o 429 nasce no disjuntor do OmniRoute).
3. Cabeçalho da Máquina único (texto, JSON e SSE tardio), removendo duplicata só no bloco inicial, fora de cerca de código.
4. Conversor estrito de `<tool_call>` em texto para `tool_calls`: só converte quando o conteúdo é exclusivamente de blocos completos com nome presente em `tools`; no stream exige `[DONE]` e `finish_reason`; recusa múltiplas choices ou índice diferente de 0; timeout não fabrica término. Desliga com `SETH_TOOLCALL_TEXTO=0`.
5. Testes: `redesign/router/test_seth_base.py` (54) e linha na `spec.md`.

## Medido (17/11/2026)

- `test_seth_base.py`: 54 passed. `seth_gateway.py --selftest`: SELFTEST OK (89 PASS). E2E 20/20 e CI local TUDO OK na rodada r3 (relato do executor).
- `git apply --check` em cópia limpa de `origin/main` (36f9e438): APLICA.
- Revisão independente do Codex em 5 rodadas; r1 a r4 reprovaram com achados, todos corrigidos; r5: "Veredito: aprovar" (ALTO e MÉDIO: nenhum). Textos: `/home/orusoua/agata-arquivo/roteador-capacidade-17-11/codex-review-lote1*.txt`.

## Não medido

- SSE de ponta a ponta com provedor real após a correção r4; efeito na taxa de tool_call em texto do tráfego real.

## Reversão

`git apply -R` do diff por proposta e reiniciar o gateway; ou, sem reverter código, `SETH_TOOLCALL_TEXTO=0` desliga o conversor.

## Comando de assinatura

Depois do merge deste PR, no terminal, sem `!`:

bash scripts/aprovar.sh seth-base-17-11

## Modelos

Claude Opus 5.5 orquestrou e conferiu; agente agata-dev (Claude Haiku 5.5) implementou; Codex revisou.
