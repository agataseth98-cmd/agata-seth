# Inventário do Agata — fotografia de auditoria

**Fotografia atual:** 04/11/2026 13:55:30 -03.  
**Fonte reproduzível:** [evidencias-iniciais.json](auditoria-2026-11-04/evidencias-iniciais.json).  
**Histórico anterior:** versão de 09:25 preservada no arquivo de originais da auditoria.

## 1. O que foi medido

Consultas GET locais a Ollama e OmniRoute, estado de oito unidades de usuário e portas TCP. Nenhuma chamada de geração, cobrança, troca de fila, inicialização ou reinício de serviço foi feita.

| Evidência | Resultado | O que não prova |
|---|---|---|
| Ollama /api/tags | 7 tags: 6 generativas e 1 de embeddings | saúde de geração, ferramentas ou independência dos modelos |
| OmniRoute /api/models | 15 registros; 12 flags available=true e 3 false | cota, acesso contratado, geração funcional ou roster completo |
| Entre as 12 flags true | 11 IDs específicos + openrouter/auto | auto é rota, não modelo único |
| OmniRoute /v1/models | 311 registros de rotas/modelos/serviços | 311 LLMs; na medição anterior eram 313 |
| OmniRoute /api/combos | filas reais incluindo seth-* | sucesso de cada elo ou autorização para trocar a ordem |

Um modelo presente no combo pode estar ausente do catálogo resumido; um modelo anunciado no catálogo pode estar fora das filas. Não usar nenhum desses endpoints como única lista de todas as LLMs utilizáveis.

## 2. Tags locais

`lumi-4b:latest`, `qwen3-30b-a3b-64k:latest`, `qwen3:4b`, `rlm-qwen3-8b-teste:latest`, `qwen3.5-9b-64k:latest`, `qwen3.5:9b`; embeddings: `nomic-embed-text:latest`.

Tags e quantizações não equivalem a famílias independentes. O Agata documenta preferência pela variante Qwen 9B com override 64K; a tag oficial não é substituta automática.

Há cinco modelos llama.cpp documentados no Agata, em serviços sob demanda. Nesta fotografia não foram observados listeners nas portas 20129 e 20142–20145; a existência física e integridade de todos os respectivos pesos não foram revalidadas nesta auditoria.

## 3. Serviços observados

| Unidade | ActiveState/SubState |
|---|---|
| omniroute.service | active/running |
| omniroute-sanitizer.service | active/running |
| seth-escriba.service | active/running |
| seth-gateway.service | inactive/dead |
| seth-verificador.service | inactive/dead |
| openvino-embeddings.service | inactive/dead |
| laya-roteador.service | inactive/dead |
| painel-operacional.service | inactive/dead |

A porta Ollama 11434 respondeu aos metadados. Não presumir quebra por serviço sob demanda estar inativo. Docker, áudio, Tailscale e demais serviços do inventário de 09:25 não foram novamente testados nesta fotografia.

## 4. Filas observadas

| Fila | Ordem retornada pela API |
|---|---|
| seth-rapido | Ministral 14B → Gemini 3.5 Flash Lite → Gemini 3.1 Flash Lite → Qwen3.5 9B 64K local |
| seth-livre | Ministral 14B → Gemini 2.5 Flash → Nemotron Ultra free → GLM 4.7 Flash → Gemini 3 Flash Preview → Qwen local |
| seth-pesado | Nemotron Ultra free → Gemini 2.5 Flash → Qwen local |
| seth-codigo | Codestral → Gemini 3 Flash Preview → North Mini Code free → GLM 4.7 Flash → Qwen local |

Os IDs completos e filas -longo constam do JSON. Groq foi retirado do caminho automático por decisão documentada, mesmo estando anunciado no catálogo. Mistral Large/Devstral não substituem o titular por aparecerem com available=true.

O Conselho Remoto usa o ROSTER de `scripts/conselho_remoto.py`, não a mesma ordem dos combos. As duas LLMs pagas foram relatadas pelo Humano; identidade, acesso programático e quotas não foram mapeados nesta auditoria.

## 5. Uso na Alexandria

Usar esta fotografia como apresentação e compreensão do estado. Antes de promover uma rota para execução, testar capacidade pertinente e conferir autorização, dependências e recursos. A falta de fallback reduz resiliência; não altera o fato de um serviço ter respondido.

Instalação, anúncio, elegibilidade por política, teste funcional, uso em fila e prontidão para tarefa são campos separados. Cada verificação recebe data e prazo de revalidação apropriado; inventário datado não é monitor contínuo.

O corpo operacional, o catálogo e a coleção são descritos em [Alexandria](proposta-tecnica-alexandria-editorial.md); [matriz](matriz-redundancia-agata-2026-11-04.md) contém os limites de redundância.
