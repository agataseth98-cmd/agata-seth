# redesign/mcp/ — servidor FastMCP das ferramentas de Máquina

**Tarefa:** P0-02 (Fase 0). **Branch:** `redesign`. **Não é canon.**

Expõe as verificações determinísticas **read-only** do Agata como tools MCP, para que
qualquer executor (sessão Claude, Codex, Qwen Coder, Goose, humano) dirija a camada de
verificação de forma idêntica. É a cola que faz o handoff funcionar.

## Invariantes

- **Nenhuma tool escreve.** Não há `commit_entry` aqui — ela escreve `MEMÓRIAS.md`/
  `ONDE_ESTAMOS.md` e comita, o que contradiz "canon só muda na Fase 8". Foi para a Fase 4
  (nó `registrar+commitar` do grafo).
- Cada tool é **wrapper fino** de um script existente em `~/agata/scripts/`, chamado com
  `cwd=~/agata`, sem shell.
- Retorno é sempre **dado estruturado**, nunca texto livre "achando" que algo é verdade.

## As 5 tools

| Tool | Envolve | Entrada | Retorno |
|---|---|---|---|
| `git_sync` | `git fetch` + `git ls-remote origin refs/heads/main` | — | `{head, origin_head, em_dia}` |
| `run_perimetro` | `bash scripts/perimetro.sh` (read-only, ACHA E PARA) | — | `{exit_code, resumo, linhas}` |
| `check_citation` | `scripts/checar_citacao.sh <arquivo>` via adaptador de temp | `texto: str` | `{exit_code, resumo, suspeitos}` |
| `lint_header` | `scripts/verificar_cabecalho.py` (cabeçalho por stdin) | `cabecalho: str` | `{ok, motivo}` |
| `query_canon` | `scripts/consultar_indice.py <termos>` (rejeita flags) | `termos: list[str]` | `{exit_code, trechos, erro}` |

Detalhes:

- **`check_citation`** não é passthrough de stdin — `checar_citacao.sh` recebe um caminho
  de arquivo. O wrapper escreve um temp privado (`tempfile.mkstemp`), chama o script,
  captura o resumo (`__RESUMO_P7__ ...` + linhas `SUSPEITO (P-7):`) e apaga o temp.
  `exit_code` 1 = há citação suspeita.
- **`query_canon`** valida cada termo contra `^[\wÀ-ÿ][\wÀ-ÿ\- ]*$` e **rejeita** qualquer
  termo começando com `-` (barra o `--rebuild`, que regenera o índice — escrita). Nunca
  toca `memoria/missoes/`. Entrada inválida levanta `TermoInvalido` (no MCP vira erro de
  tool; no `--selftest`, JSON `{"erro_validacao": ...}` + exit 3).

## Rodar

Servidor MCP em stdio (local):

```fish
redesign/mcp/.venv/bin/python redesign/mcp/servidor.py
```

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

## Equivalência verificada (01/09/2026, HEAD `798d483`, fastmcp 4.0.1)

| Tool | Caso | Script cru | MCP | Igual? |
|---|---|---|---|---|
| `run_perimetro` | perímetro atual | exit 0 · `RESULTADO GERAL: OK — 10 OK · 0 SKIP · 1 PARCIAL · 0 FALHA` | idem | ✅ |
| `lint_header` | cabeçalho válido | `OK`, exit 0 | `{ok:true, motivo:"OK"}` | ✅ |
| `lint_header` | sem `t=` e sem citação | 2 linhas `FALHA:`, exit 1 | mesmas 2 linhas, `ok:false` | ✅ |
| `check_citation` | `(302 - ...)` real | `__RESUMO_P7__ ... suspeitos=0`, exit 0 | idem, `suspeitos:[]` | ✅ |
| `check_citation` | `(99999 - ...)` inexistente | `SUSPEITO (P-7): ...`, exit 1 | mesma linha em `suspeitos[]`, exit 1 | ✅ |
| `query_canon` | `["--rebuild","x"]` | — | `erro_validacao`, exit 3, **índice não regenerado** | ✅ |
| `query_canon` | `["hidratação","âncora"]` | — | 8 seções de REGRAS + títulos, exit 0, `git status` limpo | ✅ |

## Rollback

Não destrutivo: `git checkout -- redesign/mcp` desfaz mudanças rastreadas.

O diretório é todo novo e isolado no branch `redesign`. **Só se for necessário removê-lo
por inteiro**, como passo isolado:

> ⚠️ **DESTRUTIVO — apaga o servidor MCP e seu venv. Rode sozinho.**
> ```fish
> rm -rf redesign/mcp
> ```
