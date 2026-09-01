# P0-02 — servidor FastMCP das ferramentas de Máquina

**Objetivo:** expor as verificações determinísticas do Agata (git, perímetro, citação,
cabeçalho, consulta ao canon, commit de entrada) como um servidor MCP, para que qualquer
executor — sessão Claude, Codex, Qwen Coder, Goose, humano — dirija a camada de
verificação de forma idêntica. É a cola que faz o handoff funcionar.

**Pré-requisitos:** P0-01 FEITO.

**Arquivos que a tarefa toca (branch `redesign`):**
- `redesign/mcp/servidor.py` — o servidor FastMCP
- `redesign/mcp/requisitos.txt` — `fastmcp>=3.2`
- `redesign/mcp/README.md` — como rodar e como um cliente MCP se conecta

---

## Ferramentas a expor (cada uma é wrapper fino de um script existente)

| Tool MCP | Envolve | Retorno |
|---|---|---|
| `git_sync` | `git fetch` + compara `HEAD` local vs `origin/main` (`git ls-remote`) | `{head, origin_head, em_dia: bool}` |
| `run_perimetro` | `bash scripts/perimetro.sh` | `{exit_code, resumo, linhas}` |
| `check_citation` | `scripts/checar_citacao.sh` no texto recebido | `{suspeitos: [...]}` |
| `lint_header` | `scripts/verificar_cabecalho.py` (stdin) | `{ok: bool, motivo}` |
| `query_canon` | busca por palavra no índice derivado (`scripts/consultar_indice.py`) — **read-only** | `{trechos: [...]}` |
| `commit_entry` | valida + estagia uma entrada nova de MEMÓRIAS + `ONDE_ESTAMOS.md` no mesmo commit (**não faz push**; **recusa** editar linha existente de MEMÓRIAS) | `{commit, arquivos}` |

Regras:
- Nenhuma tool escreve em `REGRAS.md`/`PROJETO.md`. `commit_entry` só **acrescenta** a
  `MEMÓRIAS.md` (append-only) e atualiza `ONDE_ESTAMOS.md`.
- Toda tool retorna dado estruturado, nunca texto livre "achando" que algo é verdade.
- `query_canon` é read-only e nunca toca `memoria/missoes/`.
- O servidor roda em stdio (local) por default; um cliente MCP aponta para ele.

---

## Passos (blocos para o fish)

### 1. **INSTALA SOFTWARE** — FastMCP num venv isolado

```fish
cd $HOME/agata
python3 -m venv redesign/mcp/.venv
redesign/mcp/.venv/bin/pip install --upgrade pip
redesign/mcp/.venv/bin/pip install "fastmcp>=3.2"
redesign/mcp/.venv/bin/python -c "import fastmcp; print(fastmcp.__version__)"
```

Colar de volta: a versão do fastmcp.
Sucesso: imprime `3.2.x` ou maior.

### 2. Escrever o servidor

O executor entrega o conteúdo de `redesign/mcp/servidor.py` como um bloco `python3 - <<'PY'`
que escreve o arquivo, ou como um patch para o Humano aplicar. O servidor:
- registra as 6 tools acima com `@mcp.tool`
- cada tool faz `subprocess.run` do script correspondente com `cwd=$HOME/agata`
- valida entrada com type hints (FastMCP gera o schema)
- `mcp.run()` no fim

### 3. Testar cada tool contra o script cru

```fish
cd $HOME/agata
# perímetro: MCP e script têm que dar o mesmo exit e o mesmo placar
bash scripts/perimetro.sh > /tmp/perim_script.txt 2>&1; echo "script exit: $status"
redesign/mcp/.venv/bin/python redesign/mcp/servidor.py --selftest run_perimetro > /tmp/perim_mcp.txt 2>&1; echo "mcp exit: $status"
diff (grep 'RESULTADO GERAL' /tmp/perim_script.txt | psub) (grep 'RESULTADO GERAL' /tmp/perim_mcp.txt | psub); echo "diff exit: $status"
```

Colar de volta: os dois exit codes e o resultado do `diff`.
Sucesso: mesmo placar de perímetro pelos dois caminhos.

---

## Aceite

- `redesign/mcp/servidor.py` sobe sem erro e lista as 6 tools.
- Para `run_perimetro`, `check_citation` e `lint_header`: o resultado pelo MCP é igual ao
  do script cru num caso conhecido.
- `commit_entry` **recusa** um payload que tente editar uma linha existente de `MEMÓRIAS.md`.

## Rollback

- `rm -rf redesign/mcp` (é tudo novo, isolado no branch `redesign`).

## Registro

- `STATUS.md`: P0-02 → "Feito"; anotar a versão do fastmcp instalada.
- `LOG.md`: entrada com os resultados dos testes de equivalência e o `HEAD` no fim.
