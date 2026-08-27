# CHAVES.md — inventário de credenciais e seus consumidores

Não contém nenhum valor de chave, senha ou token — só nomes de variável, onde cada uma é lida, e o que precisa ser tocado quando uma rotaciona. Pode ir pro canon sem cifra. Motivo de existir: os valores se reemitem em minutos no console de cada fornecedor; a lista de quem consome cada um só existia na cabeça de quem montou o sistema. Ver PROJETO.md, "Ao rotacionar chave, atualize todos os consumidores no mesmo passo — rotação parcial dá 401 silencioso."

## Em `~/.hermes/.env`

| Variável | Serviço | Consumidor | Ao rotacionar |
|---|---|---|---|
| `GOOGLE_API_KEY` (ou `GEMINI_API_KEY`, `gemini_native_adapter.py` aceita as duas) | Google Gemini | `hermes-agent`, provedor primário (`config.yaml: model.provider: gemini`). Usado por `hermes-gateway.service` e qualquer sessão CLI local. | Editar `.env`, `systemctl --user restart hermes-gateway.service`. Não precisa tocar `config.yaml`. **Ativa e em uso agora** — bateu 429 de cota gratuita várias vezes nesta sessão (MEMÓRIAS (110)-(118)). |
| `DEEPSEEK_API_KEY` | DeepSeek | Nenhuma referência ativa encontrada em `config.yaml` nesta sessão. Testado e descartado historicamente (MEMÓRIAS: "Conclusão definitiva: Gemini 2.5 Flash grátis é o único cérebro viável hoje"). | `lacuna`: não confirmado se algum caminho de código ainda lê isso incidentalmente (tarefa auxiliar, fallback antigo). Provável vestígio, não afirmado como morto. |
| `GROQ_API_KEY` | Groq | Idem — sem referência ativa achada. Testado e descartado (TPM insuficiente, MEMÓRIAS). | Mesma ressalva do DeepSeek. |
| `OPENROUTER_API_KEY` | OpenRouter | Idem — sem referência ativa achada. Testado e descartado (429/404, MEMÓRIAS). | Mesma ressalva. |
| `BROWSERBASE_ADVANCED_STEALTH`, `BROWSERBASE_PROXIES` | Browserbase | Sem `BROWSERBASE_API_KEY` explícito encontrado — só flags de configuração presentes. Consumidor provável: ferramentas de navegador do `hermes-agent`. | `lacuna`: não confirmado se a ferramenta de browser está ativa nesta instalação. |
| `BROWSER_INACTIVITY_TIMEOUT`, `BROWSER_SESSION_TIMEOUT`, `TERMINAL_LIFETIME_SECONDS`, `TERMINAL_MODAL_IMAGE`, `TERMINAL_TIMEOUT`, `IMAGE_TOOLS_DEBUG`, `MOA_TOOLS_DEBUG`, `VISION_TOOLS_DEBUG`, `WEB_TOOLS_DEBUG` | — | Flags de configuração de ferramentas, não são segredo. | Não se aplica. |

## Fora do `.env`

| Variável | Serviço | Consumidor | Ao rotacionar |
|---|---|---|---|
| `OPENAI_API_KEY` (env do container Docker) | Autenticação local Open WebUI ↔ hermes-gateway | Só o container `open-webui` — usa `OPENAI_API_BASE_URL=http://localhost:8642/v1` pra falar com o endpoint OpenAI-compatible do `hermes-gateway`. **Não está em `.env`**, não achado em nenhum `docker-compose`/script/unit systemd rastreado nesta máquina — a criação original do container não é reproduzível a partir de arquivo versionado. | Imagem atual: `open-webui-snapshot:pre-owui-permfix`. Volume a preservar: `open-webui` → `/app/backend/data`. Rotação exige `docker rm` + recriar com env novo (sem compose, é manual). **Lado do `hermes-gateway`, achado nesta sessão (não em `authz_mixin.py`/`gateway_state.json`/`auth.json` — no próprio `config.yaml`, campo `API_SERVER_KEY`, perto do fim do arquivo, junto de `API_SERVER_ENABLED: true`):** rotacionar exige trocar o valor nos dois lugares no mesmo passo — `API_SERVER_KEY` em `config.yaml` + o `OPENAI_API_KEY` do container — e reiniciar `hermes-gateway.service` depois. Valor não repetido aqui de propósito. |
| `client_id` + `client_secret` + `refresh_token` (OAuth Desktop, conta Google do projeto `agata.seth98@gmail.com`) em `~/.config/agata/google-project/{client_credentials.json,token.json}`, `600` | Google Drive (escopo único `drive.file`) — esfera do projeto | `scripts/subir_esfera_projeto.py` (cano manual esfera→Drive, MEMÓRIAS (286)); `memoria/missoes/agata-sistema/scripts/{oauth_consent.py,verificar_token.py}` (consentimento e teste dos 8 dias). **Fora de todo repo e do bundle do HD** — por desenho. | Refeito com `python3 memoria/missoes/agata-sistema/scripts/oauth_consent.py` (novo consentimento no navegador). `invalid_grant` no refresh = app ficou em Testing → republicar no Google Cloud Console e refazer. Não há serviço a reiniciar. Ver MEMÓRIAS (285). |

## Fora de escopo deste inventário

TES-002 (nonce de identidade do projeto, MEMÓRIAS (90)) não é credencial de serviço — é mecanismo de verificação de modelo, documentado separadamente em PROJETO.md/MEMÓRIAS. Não confundir os dois tipos de segredo.

## Como manter isto vivo

Estado em 12/08/2026, com a credencial OAuth da conta do projeto acrescentada em 27/08/2026 (MEMÓRIAS (285)/(286)). Se um consumidor novo passar a ler uma chave do `.env`, ou se a chave do Open WebUI for encontrada/documentada, atualizar aqui — é o tipo de arquivo que fica errado sozinho se ninguém tocar.
