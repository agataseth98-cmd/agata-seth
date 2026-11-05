# Proposta `gratuitos-cota-20261105`: gratuitos por passagem e cota esgotada sinalizada (lote 7)

**O que é, em português comum:** o Humano pediu que todos os modelos gratuitos do Agata participem da avaliação, e que o modelo que esgotar a cota fique marcado, não apareça como quebrado. Esta proposta faz duas coisas:
1. **Lista de gratuitos** em `config/gratuitos_omniroute.json`: 11 modelos gratuitos do OpenRouter (NVIDIA Nemotron, Gemma, Liquid, Cohere e outros) e o Z.AI GLM-4.7-Flash, todos chamados por passagem pelo OmniRoute. O `stealth/crouton-alpha` entra na lista com `ativo: false`: origem anônima, e o provedor pode reter os prompts (não usados para treino). Só entra com decisão sua.
2. **Cota esgotada:** `chamar_rota` (em `redesign/conexoes/testar_rotas.py`) passa a marcar `falha_etapa = "cota_esgotada"` quando o erro é 429, limite ou quota. Antes isso caía em "transporte", igual a queda de rede.

**O que não muda:** a categoria `gratuito` continua desligada no orçamento até você ligar. Nada de rota paga. O `openrouter/auto` continua fora.

**Medido:** pytest de `redesign/conexoes` e `redesign/avaliacao` verde (35 + 8 novos). Os 12 gratuitos ativos carregam da lista. Erro 429 vira `cota_esgotada`; erro de rede continua `transporte`. Os 11 modelos OpenRouter responderam por passagem no teste de OmniRoute (um deles, o NVIDIA Nemotron Lightning, respondeu com `max_tokens` de 8).

**Não medido:** a cota real de cada modelo. Os limites que achei vieram de agregadores e divergem; o console de cada provedor é a fonte.

**Limite conhecido:** modelos de raciocínio (Nemotron) gastam o `max_tokens` pensando. Com 400 tokens na avaliação costuma bastar; com 8 não.

**Reversão:** remover o bloco novo de `testar_rotas.py` e o arquivo `config/gratuitos_omniroute.json`. Nenhum estado persistente novo.
