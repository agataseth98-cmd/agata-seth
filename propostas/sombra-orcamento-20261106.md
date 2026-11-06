# Proposta `sombra-orcamento-20261106`: orçamento do turno em sombra (metacognição durante, lote 9)

**O que é:** a Seth não tem, hoje, um limite de rodadas por turno que seja medido e registrado. Esta proposta acrescenta, só em sombra, a conta do turno: quantas rodadas de ferramenta e quantas respostas o turno teve, e se teria estourado o orçamento (6 rodadas de ferramenta, ou o teto de chamadas).

**O que muda:** `redesign/router/sombra_nova_versao.py` ganha o bloco `orcamento_turno` no registro da sombra. Não altera a resposta, não bloqueia, não chama modelo. Liga só com `SETH_SOMBRA_NOVA_VERSAO=1`, que continua desligado por padrão.

**Limites:**
- O prazo do turno não é medido nesta sombra. O registro diz isso explicitamente.
- A conta usa o histórico que chega ao gateway. Não vê o tempo real de cada rodada.

**Medido:** o selftest do módulo passa, com o caso novo (seis rodadas de ferramenta esgotam o orçamento). Os 32 testes de `nova_versao/tests` e `router` passam.

**Não medido:** o efeito em tráfego real.

**Reversão:** remover o bloco `orcamento_turno` de `observar()`.
