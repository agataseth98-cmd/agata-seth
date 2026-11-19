# Proposta placar-modelos-19-11 — placar único: cada modelo × tipo de pedido

Princípio do Humano, 19/11/2026 10:44: "todos os modelos tem que ter sua chance no que são bons"; pedido de "sistema de trocas mais refinado aproveitando ao máximo todos os modelos".

**O quê:** `redesign/rotas/placar.py` agrega as provas (benchmark, porta de entrada, catálogo) por modelo × tipo (conversa, código, json, ferramenta, contexto): nota (mesma lógica de `scripts/porta_entrada.py`, importada), n, p50/p95, data, protocolo, custo, confiança do provedor e estado no painel (standby tira). `gerar` grava `~/.local/share/agata/placar/placar.json` (0600); `melhores --tipo X --classe publico|pessoal` devolve os elegíveis em ordem (pessoal só local; segredo nenhum). Amostra pequena entra com aviso e peso menor; nenhum modelo é descartado se for o melhor em algum tipo. Spec nova de `redesign/rotas`.

**Não muda o gateway:** o placar é a fonte; a escolha por pedido vem no lote seguinte.

**Medido:** 18 testes (rotas), CI local TUDO OK; com os dados reais leu 35 modelos sem aviso.

**Limite conhecido:** a nota é mecânica (forma, vazio, sintaxe) e quase tudo empata em 1,00 com n=6; a auditoria de conteúdo de 18/11 (lfm3 vazio em texto longo e pedindo segredo) ainda não entra na nota — próximo passo é somar o veredito de conteúdo e medir com mais pedidos.

**Reversão:** `git revert` do commit de aplicação.

**Modelo:** Sonnet 5.5 (implementação) orquestrado pelo Opus 5.5; revisão final pelo Opus.
