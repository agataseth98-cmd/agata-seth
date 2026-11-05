# Proposta `crouton-condicoes-20261105`: stealth/crouton-alpha liberado sob condições (lote 7, complemento)

**Decisão do Humano (05/11/2026):** o `stealth/crouton-alpha` pode ser usado, com estas condições:
1. **Dados redigidos somente:** sem informação pessoal, senha ou código fonte proprietário.
2. **Plano de contingência sempre nomeado:** um modelo gratuito conhecido precisa estar pronto para substituir o crouton.

**Origem:** o provedor é anônimo (stealth). A página do OpenRouter diz que os prompts podem ser retidos pelo provedor, mas não usados para treino. A disponibilidade nos últimos 3 dias foi de 98,1%, com latência de 2,98 s.

**O que muda:**
- `config/gratuitos_omniroute.json`: `openrouter/stealth/crouton-alpha` passa a `ativo: true`, com a nota das condições.
- `redesign/conexoes/tests/test_gratuitos.py`: o teste que proibia o crouton passa a exigir que ele esteja na lista, com a nota das condições.

**Medido:** os 8 testes de `redesign/conexoes` passaram.

**Não medido:** o comportamento do crouton nos dados reais da avaliação. Por decisão do Humano, ele só vê dados redigidos e sintéticos.

**Reversão:** voltar `ativo` para `false`.
