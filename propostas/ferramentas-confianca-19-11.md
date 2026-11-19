# Proposta ferramentas-confianca-19-11 — ferramentas por confiança e bloqueio do que é inventado

Ordens do Humano, 19/11/2026 10:24–10:28: todos os modelos com acesso às ferramentas, por capacidade, de forma homogênea e segura; "sem modo sombra, quero ver uma diferença real no uso da Seth hoje". Base: auditoria da conversa da Seth de 18/11 (`~/agata-arquivo/auditoria-conversa-seth-18-11/relatorio.md`): 17 turnos com escrita alegada sem ferramenta, identidade de modelo forjada, saída de ferramenta fabricada.

**O quê:**
- `config/ferramentas-rotulos.json`: rótulo por ferramenta (dado publico|pessoal|segredo; efeito leitura|escrita) e nível por provedor (local e pago_sem_treino até pessoal; gratuito só público; nvidia gratuito). Ferramenta desconhecida = pessoal + escrita.
- `redesign/router/ferramentas_confianca.py`: oferece a cada pedido só as ferramentas que o nível permite; recusa resultado acima do nível; identifica o resultado só pelo `tool_call_id` (nunca pelo `name`).
- `redesign/router/bloqueio_turno.py` + gancho no `seth_gateway.py`: bloqueia antes de entregar (a) escrita/aplicação afirmada sem ferramenta de escrita com resultado positivo explícito; (b) saída de ferramenta simulada; (c) segundo cabeçalho ou modelo diferente do roteado. Devolve ao modelo uma vez; se persistir, resposta mínima honesta. Resposta longa ou lenta demais para conferir não sai sem checagem (resposta mínima). A correção da Máquina vai só ao modelo, nunca à tela.
- Faixa pública: passa a aceitar ferramentas de dado público (navegar, buscar, ler página).
- Desligar: `SETH_FERRAMENTAS_CONFIANCA=0`, `SETH_BLOQUEIO_TURNO=0`; `SETH_CORRECAO_VISIVEL=1` volta a correção visível.

**Medido:** 388 testes (router, rotas, sentidos); selftest do gateway OK; CI local TUDO OK; na revisão final, 147 + 79 testes rodados pelo Opus.

**Revisão:** Codex final (só o diff) reprovou 3 pontos (vazamento por `name` falso, erro de gravação contado como sucesso, resposta longa sem checagem); todos corrigidos com teste.

**Decisão do Humano na assinatura:** os níveis de confiança propostos (local/pago até pessoal; gratuito só público). As filas seth-* mantêm hoje as ferramentas sob o sanitizador.

**Reversão:** `git revert` ou as chaves acima.

**Modelo:** Sonnet 5.5 (implementação) orquestrado e revisado pelo Opus 5.5; revisão final do Codex.
