# Decreto: endereços do Qwen e do Kimi em inglês e teste sem regex (03/11/2026)

Decisão do Humano em 03/11/2026: os conselheiros precisam abrir em inglês ou português. Endereços escolhidos por ele:
- Qwen: `https://chat.qwen.ai/` (antes `https://qwen.ai/`).
- Kimi: `https://www.kimi.ai/en` (antes `https://www.kimi.ai/`; medido: responde 200 e serve `en-US`).

Troca em `ABRIR_PROVEDORES` (`server.py`) e em `relay_catalog.py`; o teste que exige a mesma URL nos dois lugares continua valendo. A extensão já aceita `chat.qwen.ai` e `kimi.ai` no manifesto e no inventário, então não precisa recarregá-la por isso.

Também troca, em `test_painel.py`, a regex que procurava `<script>` embutido (alerta #14 do CodeQL, dispensado em 03/11/2026 como falso positivo de teste) por `HTMLParser`; o alerta deixa de existir no código.

49 testes OK. O painel precisa reiniciar depois de aplicar.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh painel-urls-qwen-kimi-20261103 "aprovo: URLs de Qwen e Kimi e teste sem regex"`.
