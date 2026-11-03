# Decreto: os botões do painel não funcionavam (script bloqueado) e o Kimi abria em chinês (03/11/2026)

Achado de 03/11/2026, medido no servidor vivo: a política de segurança que o painel serve (`Content-Security-Policy: script-src 'self'`) **bloqueia `<script>` embutido**. Os botões "Abrir" da barra lateral (serviços e modelos) e o novo clique da aba Conselho estavam num `<script>` embutido no `prototipo.html`, então **nunca rodaram** no navegador: `typeof conferirConselheiros` deu `undefined` numa página recém-carregada. Por isso o "Abrir" nunca foi validado ao vivo e a aba Conselho não fez nada. O servidor estava certo: o mesmo pedido feito à mão abriu os nove conselheiros (catálogo passou a mostrar nove abas abertas).

Mudanças:
1. O script sai do HTML para `abrir.js`, servido na rota nova `/abrir.js`; a política de segurança fica como está (nada de `unsafe-inline`). Um teste novo impede script embutido em `prototipo.html` e `index.html` e confere que `/abrir.js` responde 200.
2. Kimi: `www.kimi.com` serve a página em chinês (`zh-CN`, medido); `www.kimi.ai` serve em português (`pt-BR`, medido) e é o endereço do canon (`estado-provedores.md`). `ABRIR_PROVEDORES` e `relay_catalog.py` passam a usar `https://www.kimi.ai/`. Um teste novo exige que os endereços de abrir dos nove conselheiros coincidam com os do catálogo. A extensão já aceita `kimi.ai` no manifesto e no inventário.
3. Qwen: **não alterei.** Não consegui verificar o idioma de `qwen.ai` nem de `chat.qwen.ai` (a página muda de idioma no navegador). Espera a decisão do Humano sobre o endereço.

Muda `server.py`, `prototipo.html`, `abrir.js` (novo), `relay_catalog.py` e `test_painel.py`. 49 testes OK. O painel precisa reiniciar e a janela dele precisa de `Ctrl+R` depois de aplicar.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh painel-script-externo-20261103 "aprovo: script do painel externo e Kimi em português"`.
