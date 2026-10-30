# Decreto: botões "Abrir" no painel (30/10/2026)

**O que muda:** o painel ganha uma lista "Abrir" na barra lateral, com Obsidian, LibreChat e cada modelo (DeepSeek, Gemini, Z.ai, ChatGPT, Claude, Grok, Qwen, Mistral e Kimi). Ao clicar, o painel abre o programa ou a página na própria janela de navegador do sistema.

**Como é seguro:**
- O painel só envia o nome do destino (por exemplo, `obsidian`). O servidor tem uma lista fixa de destinos e decide o comando; não aceita comando, caminho nem endereço digitado.
- Sem shell: o comando é uma lista de argumentos fixa.
- Só aceita pedidos da própria página do painel (mesma origem, JSON).

**Mudanças:**
- `redesign/painel_operacional/server.py`: rota `POST /api/abrir` e a lista fixa de destinos.
- `redesign/painel_operacional/prototipo.html`: a lista "Abrir" e o script que chama a rota.

**Validado:** os 22 testes do painel passam, e o servidor compila.

**Aplicação:** depois da assinatura (`bash scripts/aprovar.sh botoes-abrir-20261030 "aprovo: botões Abrir do painel"`). Depois de aplicar, reiniciar o serviço do painel.
