# Proposta `nvidia-gemma-20261105`: NVIDIA Gemma por passagem na lista de gratuitos (lote 7, complemento)

**Pedido do Humano (05/11/2026):** incluir o NVIDIA já, com assinatura.

**O que é:** a conexão NVIDIA NIM está no OmniRoute. Testei com uma chamada mínima: `nvidia/google/gemma-4-31b-it` respondeu (HTTP 200). Os outros modelos NVIDIA testados deram 404 (a conta não tem acesso) ou 410 (descontinuados). Só o Gemma entra.

**O que muda:**
- `config/gratuitos_omniroute.json`: acrescenta `nvidia/google/gemma-4-31b-it` com `ativo: true`.
- `redesign/conexoes/tests/test_gratuitos.py`: o teste de lista passa a aceitar o prefixo `nvidia/` e confere que o Gemma está na lista.

**Medido:** 8 testes de `redesign/conexoes` verdes. Uma chamada real ao Gemma: 200, em cerca de 11 s.

**Não medido:** a cota do NVIDIA para essa conta. Os limites que achei em fontes de terceiros divergem; a fonte é o painel da conta em build.nvidia.com.

**Reversão:** `ativo: false` na mesma entrada.
