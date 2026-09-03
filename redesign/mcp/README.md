# redesign/mcp/ — servidor FastMCP das ferramentas de Máquina

**Tarefa:** P0-02 (Fase 0). **Branch:** `redesign`. **Não é canon.**

Expõe as verificações determinísticas **read-only** do Agata como tools MCP, para que
qualquer executor (sessão Claude, Codex, Qwen Coder, Goose, humano) dirija a camada de
verificação de forma idêntica. É a cola que faz o handoff funcionar.

## Invariantes

- **Nenhuma tool escreve no workspace nem no canon.** "read-only" aqui = sem escrita em
  arquivo rastreado / `MEMÓRIAS.md` / índice derivado — **não** "zero escrita no
  filesystem": `git_sync` faz `git fetch`, que atualiza metadados em `.git/` (refs de
  rastreio, `FETCH_HEAD`, objetos); `check_citation` cria um temp e o apaga. Nenhuma
  toca a árvore de trabalho.
- Não há `commit_entry` aqui — ela escreve `MEMÓRIAS.md`/`ONDE_ESTAMOS.md` e comita, o que
  contradiz "canon só muda na Fase 8". Foi para a Fase 4 (nó `registrar+commitar` do grafo).
- Cada tool é **wrapper fino** de um script existente em `~/agata/scripts/`, chamado com
  `cwd=~/agata`, **sem shell**, args em lista.
- Retorno é sempre **dado estruturado**, nunca texto livre "achando" que algo é verdade.
- `_run` **nunca levanta**: timeout → `returncode 124`; binário ausente/não-executável →
  `127`. O erro vai no campo estruturado, não como exceção.

## As 5 tools

| Tool | Envolve | Entrada | Retorno |
|---|---|---|---|
| `git_sync` | `git fetch` + `rev-parse main` vs `ls-remote origin main` + branch vs `@{upstream}` | — | `{canon_local, canon_remote, canon_em_dia, branch, branch_head, branch_upstream, branch_upstream_head, branch_em_dia, fetch_exit_code, fetch_error}` |
| `run_perimetro` | `bash scripts/perimetro.sh` (read-only, ACHA E PARA; usa `mktemp -d` próprio, limpa) | — | `{exit_code, resumo, linhas}` |
| `check_citation` | `scripts/checar_citacao.sh <arquivo>` via adaptador de temp | `texto: str` | `{exit_code, resumo, suspeitos}` |
| `lint_header` | `scripts/verificar_cabecalho.py` (cabeçalho por stdin) | `cabecalho: str` | `{ok, motivo}` |
| `query_canon` | `scripts/consultar_indice.py <termos>` (rejeita flags) | `termos: list[str]` | `{exit_code, trechos, erro}` |

Detalhes:

- **`git_sync`** mede **dois eixos separados**: (a) `canon_*` = `main` local vs
  `origin/main` — é o que alimenta o `sync:` do cabeçalho da Regra 1; (b) `branch_*` = a
  branch atual (ex.: `redesign`) vs o seu upstream. Numa sessão trabalhando em `redesign`,
  o esperado é `canon_em_dia: true` (o canon não mudou) **e** `branch_em_dia: true/false`
  conforme haja commit local não empurrado. `fetch_error` != null = houve erro de
  transporte; nesse caso `canon_remote` pode ter vindo de um `ls-remote` que também
  falhou — cheque `fetch_error` antes de confiar em `canon_em_dia`.
- **`check_citation`** não é passthrough de stdin — `checar_citacao.sh` recebe um caminho
  de arquivo. O wrapper escreve um temp privado (`mkstemp` + `os.fdopen`, fd sempre
  fechado mesmo em erro de escrita), chama o script, captura o resumo (`__RESUMO_P7__ ...`
  + linhas `SUSPEITO (P-7):`) e apaga o temp no `finally`. `exit_code` 1 = citação suspeita.
- **`query_canon`** valida cada termo contra `^[\wÀ-ÿ][\wÀ-ÿ\- ]*$` e **rejeita** qualquer
  termo começando com `-`. A garantia real contra `--rebuild` (que regeneraria o índice)
  vem de **subprocess sem shell + args em lista** — um termo como `"x --rebuild"` chega
  como **um** argumento de texto, nunca como flag; o regex é a 2ª linha de defesa. **Lê**
  o índice em `memoria/missoes/agata-sistema/derivado/` — não escreve lá; índice
  ausente/corrompido continua sendo erro de leitura, nunca reconstrução automática.
  Entrada inválida levanta `TermoInvalido` (no MCP vira erro de tool; no `--selftest`,
  JSON `{"erro_validacao": ...}` + exit 3).

## Rodar

Servidor MCP em stdio (local):

```fish
redesign/mcp/.venv/bin/python redesign/mcp/servidor.py
```

`git_sync` faz um `git fetch` de rede — pode levar dezenas de segundos conforme a
latência do GitHub (timeout interno de 180 s → `fetch_exit_code: 124`). Um cliente MCP não
deve pôr timeout agressivo nessa tool; as outras quatro são locais (timeout interno 120 s)
e respondem rápido.

Um cliente MCP (Claude Code, Goose, Cursor, …) aponta para esse comando como servidor
stdio. Exemplo de entrada no `mcp.json` / config equivalente do cliente:

```json
{
  "mcpServers": {
    "agata-maquina": {
      "command": "/home/orusoua/agata/redesign/mcp/.venv/bin/python",
      "args": ["/home/orusoua/agata/redesign/mcp/servidor.py"]
    }
  }
}
```

## Selftest (equivalência com o script cru)

```fish
redesign/mcp/.venv/bin/python redesign/mcp/servidor.py --selftest run_perimetro
redesign/mcp/.venv/bin/python redesign/mcp/servidor.py --selftest lint_header      < cabecalho.txt
redesign/mcp/.venv/bin/python redesign/mcp/servidor.py --selftest check_citation   < texto.txt
redesign/mcp/.venv/bin/python redesign/mcp/servidor.py --selftest query_canon hidratação âncora
redesign/mcp/.venv/bin/python redesign/mcp/servidor.py --selftest git_sync
```

O `--selftest` imprime o JSON do retorno da tool e sai com o código do script envolvido
(`lint_header` sai 1 quando `ok` é `false`; `query_canon` sai 3 em erro de validação).

## Equivalência verificada (01/09/2026, fastmcp 4.0.1; re-rodar após qualquer mudança em `servidor.py`)

| Tool | Caso | Script cru | MCP | Igual? |
|---|---|---|---|---|
| `run_perimetro` | perímetro atual | exit 0 · `RESULTADO GERAL: OK — 10 OK · 0 SKIP · 1 PARCIAL · 0 FALHA` | idem | ✅ |
| `lint_header` | cabeçalho válido | `OK`, exit 0 | `{ok:true, motivo:"OK"}` | ✅ |
| `lint_header` | sem `t=` e sem citação | 2 linhas `FALHA:`, exit 1 | mesmas 2 linhas, `ok:false`, selftest exit 1 | ✅ |
| `check_citation` | `(302 - ...)` real | `__RESUMO_P7__ ... suspeitos=0`, exit 0 | idem, `suspeitos:[]` | ✅ |
| `check_citation` | `(99999 - ...)` inexistente | `SUSPEITO (P-7): ...`, exit 1 | mesma linha em `suspeitos[]`, exit 1 | ✅ |
| `query_canon` | `["--rebuild","x"]` | — | `erro_validacao`, exit 3, **índice não regenerado** | ✅ |
| `query_canon` | `["hidratação","âncora"]` | — | seções de REGRAS + títulos, exit 0, `git status` limpo | ✅ |

Casos de borda (achados no parecer do Conselho 01 — `gpt-5.6-terra` + auto-revisão):

| Tool | Caso | Comportamento verificado |
|---|---|---|
| `git_sync` | branch atual = `redesign` | `canon_em_dia: true` (canon intocado) **e** `branch_em_dia: true/false` conforme push — os dois eixos são reportados separados, não se confundem |
| `git_sync` | erro de rede no fetch | `fetch_exit_code != 0` + `fetch_error` preenchido; não mascara como `canon_em_dia:false` sem sinal |
| `query_canon` | termo composto `"x --rebuild"` | chega como **um** argumento de texto; tratado como termo de busca (0 seções), **índice não regenerado**, `git status` limpo |
| `query_canon` | índice ausente/corrompido | erro de **leitura** (o script orienta a rodar o gerador), nunca reconstrução automática |
| qualquer | script ausente / não-executável | `_run` devolve `returncode 127` + stderr estruturado; **sem exceção** propagada |
| qualquer | subprocess travado | `_run` devolve `returncode 124` após o timeout (120 s local / 180 s `git_sync`); temp do `check_citation` é apagado no `finally` mesmo assim |

## Rollback

Não destrutivo: `git checkout -- redesign/mcp` desfaz mudanças rastreadas.

O diretório é todo novo e isolado no branch `redesign`. **Só se for necessário removê-lo
por inteiro**, como passo isolado:

> ⚠️ **DESTRUTIVO — apaga o servidor MCP e seu venv. Rode sozinho.**
> ```fish
> rm -rf redesign/mcp
> ```
