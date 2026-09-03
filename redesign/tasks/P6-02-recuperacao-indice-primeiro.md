# P6-02 — recuperação índice-primeiro (refs rastreáveis, zero vector DB)

**Status:** ✅ **FEITO — 2026-09-02 ~19:25 (relógio da máquina).** `redesign/obsidian/
consulta.py` — duas vias, mesmo formato de hit (`ref`+`arquivo`+`trecho`): `query_canon`
(PRIMÁRIA, índice derivado) + FTS do plugin pelo `:27125` (SECUNDÁRIA). **Zero vector DB**
(`_sem_vector_db()` + `pip list` limpos). 5 consultas com gabarito: `presence_penalty` e
`TES-002 nonce` convergem nas refs `(151)-(154)` / `(70)(89)(90)`; as outras 3 são
complementares (seção vs texto), toda hit rastreável. Adicionado `/search/` ao allowlist
do `ro_proxy`. Ver `redesign/obsidian/README.md`.

**Objetivo:** uma ferramenta que consulta o vault e devolve **referências rastreáveis**
(`(NNN)` + arquivo + linha), pelo MCP `:27124/mcp/` **e** por leitura direta de disco
(fallback), sem nenhum índice vetorial.

**Pré-requisitos:** P6-01 FEITO (o MCP no ar). `query_canon` (P4-02).

**Arquivos:** `redesign/obsidian/consulta.py` (novo) · `redesign/obsidian/README.md` · este.

Classe de risco: runtime (chama o MCP local). Sem `sudo`, sem instalação. Auto-revisão.

---

## Passos

1. **`consulta.py`** — `consultar(termos) -> [{ref, arquivo, linha, trecho}]`:
   - via MCP: chama a tool de busca do `:27124/mcp/` (bearer token do store local).
   - fallback: `tools.query_canon(termos)` sobre o índice derivado (P4-02).
   - normaliza os dois para o mesmo formato: cada hit carrega o **nº de entrada** `(NNN)`
     (extraído do arquivo/trecho), o caminho e a linha. Nada de score opaco.
2. **Zero vector DB:** `pip list` no venv sem `faiss`/`chroma`/`qdrant`/`weaviate`/`lancedb`
   /`milvus`; `consulta.py` não importa nenhum. Se um dia usar o `e5-small` (P2-03), é só
   para **reordenar** hits já achados por texto — nunca como store, e o resultado ainda
   carrega a ref rastreável.
3. **Teste:** 5 perguntas cujo gabarito está no canon → `consulta.py` devolve as refs
   certas (spot-check: a `(NNN)` existe, o arquivo/linha batem). Comparar MCP vs
   disco-direto — mesmas refs.

## Aceite

- `consulta.py` devolve refs rastreáveis (`(NNN)` + arquivo + linha) pelo MCP e por disco.
- Nenhum vector DB (`pip list` limpo; sem import).
- MCP e disco-direto convergem nas mesmas refs para as 5 perguntas de teste.

## Verificação independente

- **Quem:** fallback ou Humano. **O quê:** que toda resposta carrega uma ref checável e que
  não há índice vetorial. **Como:** abrir 3 refs devolvidas e conferir; `pip list`.
- **Resultado:** no LOG.

## Rollback

`git checkout -- redesign/obsidian`. Não destrutivo.

## Registro

- `STATUS.md`: P6-02 → "Feito".
- `LOG.md`: as 5 consultas, a convergência MCP↔disco, `HEAD`.
