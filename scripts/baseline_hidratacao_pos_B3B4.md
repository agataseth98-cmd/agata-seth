# Baseline de hidratação — .hermes.md

Gerado por `scripts/medir_hidratacao.py`. Comandos usados: ver rodapé.

## Metodologia
- **bytes**: `len(arquivo.read_bytes())` (UTF-8 no disco).
- **chars**: `len(str)` em Python 3 = contagem de codepoints Unicode. Locale declarado: `LANG=pt_BR.UTF-8`. Verificado contra `LC_ALL=pt_BR.UTF-8 wc -m .hermes.md` no arquivo inteiro -- os dois bateram. Ressalva do Humano confirmada: `wc -m` em locale `C` conta bytes, não chars (mesmo total que `wc -c`); esta medição usa UTF-8 explicitamente.
- **tokens (qwen3.5-9b-64k)**: `prompt_eval_count` retornado por `POST http://localhost:11434/api/generate` (`ollama version is 0.32.11`, modelo `qwen3.5-9b-64k:latest`, `num_ctx=65536`, `num_predict=1` para minimizar geração). Este é o tokenizador real do modelo carregado -- o mesmo valor que o Ollama usa internamente para saber quanto do contexto o prompt ocupa. NÃO é a heurística de 4 chars/token de `estimate_messages_tokens_rough()` (`agent/conversation_loop.py:2237`).
- **gemini-2.5-flash**: lacuna: sem tokenizador local. O tokenizador real (`GenerativeModel.count_tokens`) exige chamada à API do Google -- não executado nesta medição para não consumir cota do free tier (~20 req/dia, monitorado por `gemini_quota_guard`, PROJETO.md). Decisão de escopo, não limitação técnica; reversível se o Humano autorizar gastar 6 chamadas de cota nisso.
- **Claude (este executor)**: lacuna: sem tokenizador local nem chamada de API disponível nesta sessão.

## Por bloco

| # | bloco (linha `# ...`) | bytes | chars (UTF-8) | tokens (qwen3.5-9b-64k, real) | % de 65536 (num_ctx qwen) |
|---|---|---|---|---|---|
| 1 | `# REGRAS.md` | 1175 | 1125 | 321 | 0.49% |
| 2 | `# REGRAS.md — Sistema Agata` | 20989 | 20112 | 5653 | 8.63% |
| 3 | `# PROJETO.md` | 13 | 13 | 14 | 0.02% |
| 4 | `# PROJETO.md — Agata (estado corrente)` | 26105 | 25189 | 7600 | 11.60% |
| 5 | `# Índice de MEMÓRIAS.md` | 19294 | 18092 | 7124 | 10.87% |
| 6 | `# MEMÓRIAS.md (janela por entrada inteira, orçamento 25000 chars)` | 25696 | 24763 | 7080 | 10.80% |

## Totais do arquivo inteiro
- bytes: 93880
- chars (UTF-8): 89889
- tokens (qwen3.5-9b-64k, real, soma dos blocos): 27792 -> 42.41% de 65536 (num_ctx configurado)
- gemini-2.5-flash: lacuna: sem tokenizador para gemini-2.5-flash (ver metodologia)
- Claude (executor desta sessão): lacuna: sem tokenizador para Claude

## Comandos que produziram este relatório
```
cd ~/agata && python3 scripts/medir_hidratacao.py
# internamente, por bloco:
curl -s http://localhost:11434/api/generate -d '{"model":"qwen3.5-9b-64k:latest","prompt":"<bloco>","stream":false,"options":{"num_predict":1,"num_ctx":65536}}' # -> campo prompt_eval_count
ollama -v
```
