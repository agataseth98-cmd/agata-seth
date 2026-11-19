# Proposta sem-mistral-19-11 — família Mistral fora da ficha de rotas; registro da unificação das filas

Ordem do Humano, 19/11/2026 13:26: "unifique todas essas rotas para que apenas o roteamento planejado exista, deixe os modelos mais capazes no topo e vá descendo, remova todos os modelos da família do mistral e incorpore todos que encontramos".

**O quê (repo):** remove a rota `mistral-8b` de `config/rotas-ficha.json` (13 → 12 rotas). FICHA OK; 21 testes de ficha e placar passam.

**O que já foi feito no OmniRoute (fora do repo, ordem direta do Humano), registrado aqui:** filas da Seth reordenadas pela medição de 19/11 (prompt real) e sem nenhum Mistral (ministral-14b e codestral saíram):
- seth-livre: nemotron-3.5-super-vl · gemini-3.1-flash-lite · gemini-3.5-flash-lite · gemini-2.5-flash · nemotron-3-ultra (NVIDIA) · glm-4.7-flash · qwen3-30b-a3b (local) · qwen3.5-9b (local)
- seth-rapido: super-vl · gemini-3.1-flash-lite · nemotron-3.5-bolt · gemini-3.5-flash-lite · glm-4.7 · qwen3-30b · qwen3.5-9b
- seth-pesado: nemotron-3-ultra · super-vl · gemini-2.5-flash · gemini-3.5-flash-lite · qwen3-30b · qwen3.5-9b
- seth-codigo: nemotron-3.5-bolt · super-vl · gemini-3-flash-preview · glm-4.7 · north-mini-code · qwen3-30b · qwen3.5-9b
- *-longo: as mesmas sem os locais.
Cópias: `~/agata-arquivo/omniroute-combos-19-11/{antes,depois}.json`. Teste: as quatro filas responderam.

**Motivo medido:** ministral-14b atendia 80% dos pedidos (posição 0) com 31% de citação inventada e p50 de conversa 55 s; não liderou nenhum tipo na medição de 19/11 (`~/agata-arquivo/investigacao-mistral-19-11/`, `~/agata-arquivo/medicao-conversa-19-11/`).

**Reversão:** `git revert`; filas: reaplicar `antes.json`.

**Modelo:** Opus 5.5.
