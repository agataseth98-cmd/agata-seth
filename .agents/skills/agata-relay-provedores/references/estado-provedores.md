# Estado dos provedores

Atualizado em 29/10/2026 para a proposta P-8 da extensão oficial. É um registro, não prova de login, disponibilidade ou suporte vigente.

| ID | URL principal permitida | Estado no catálogo proposto | Nota histórica |
|---|---|---|---|
| `deepseek` | `https://chat.deepseek.com/` | `experimental` | Testes técnicos no protótipo em 27/10; confirmar na extensão oficial carregada. |
| `gemini` | `https://gemini.google.com/` | `experimental` | Respondeu com a aba em evidência em teste anterior; validar após aprovação e reload. |
| `zai` | `https://chat.z.ai/` | `experimental` | Retry anterior obteve resposta formal; testar o caminho oficial atual. |
| `chatgpt` | `https://chatgpt.com/` | `experimental` | Renderer DOM mudou anteriormente; confirmar que a resposta nova não é eco. |
| `claude` | `https://claude.ai/` | `experimental` | Teste técnico anterior não substitui validação da extensão oficial atual. |
| `grok` | `https://grok.com/` | `experimental` | O protótipo já confundiu eco do prompt com resposta; exigir resposta nova. |
| `qwen` | `https://qwen.ai/` | `experimental` | Seletor DOM específico foi necessário anteriormente; manter no modo atual da aba. |
| `mistral` | `https://chat.mistral.ai/` | `experimental` | Resposta técnica anterior, sem promoção automática na versão oficial. |
| `kimi` | `https://www.kimi.ai/` | `experimental` | O provedor exibiu aviso de excesso de usuários em 28/10; classificar como `provider_busy` se repetir. |

Perplexity está fora do roster por decisão do Humano. Os resultados anteriores ocorreram no protótipo e são evidência histórica datada, não estado verde da versão oficial. A extensão detecta uma aba pela URL; ela não verifica se a conta está autenticada.
