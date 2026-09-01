# P0-02 — servidor FastMCP das ferramentas de Máquina

**Objetivo:** expor as verificações determinísticas **read-only** do Agata (git, perímetro,
citação, cabeçalho, consulta ao canon) como um servidor MCP, para que qualquer executor —
sessão Claude, Codex, Qwen Coder, Goose, humano — dirija a camada de verificação de forma
idêntica. É a cola que faz o handoff funcionar.

**Pré-requisitos:** P0-01 FEITO, P0-00 FEITO.

> **Correções P0-00 aplicadas nesta tarefa:**
> - `commit_entry` **removida** desta fase — ela escreve `MEMÓRIAS.md`/`ONDE_ESTAMOS.md` e
>   comita, o que contradiz "canon só muda na Fase 8" e não é wrapper fino. Vai para a
>   Fase 4 (dentro do nó `registrar+commitar` do grafo).
> - `query_canon` **rejeita qualquer flag** — só aceita termos de consulta. `--rebuild`
>   do `consultar_indice.py` regenera o índice (escrita); não pode ser alcançável pelo MCP.
> - `check_citation` **não é passthrough de stdin** — `checar_citacao.sh` recebe um
>   caminho de arquivo. O wrapper escreve um temp privado, chama o script, captura o
>   resumo e apaga o temp. Isso está especificado e testado abaixo.

**Arquivos que a tarefa toca (branch `redesign`):**
- `redesign/mcp/servidor.py` — o servidor FastMCP
- `redesign/mcp/requisitos.txt` — `fastmcp>=3.2`
- `redesign/mcp/README.md` — como rodar e como um cliente MCP se conecta

---

## Ferramentas a expor (cada uma é wrapper fino de um script existente)

| Tool MCP | Envolve | Entrada | Retorno |
|---|---|---|---|
| `git_sync` | `git fetch` + `git ls-remote` p/ comparar `HEAD` local vs `origin/main` | — | `{head, origin_head, em_dia: bool}` |
| `run_perimetro` | `bash scripts/perimetro.sh` (read-only, ACHA E PARA) | — | `{exit_code, resumo, linhas}` |
| `check_citation` | `scripts/checar_citacao.sh <arquivo>` via **adaptador de temp** (ver abaixo) | `texto: str` | `{suspeitos: [...]}` |
| `lint_header` | `scripts/verificar_cabecalho.py` (recebe cabeçalho por stdin — confirmado) | `cabecalho: str` | `{ok: bool, motivo}` |
| `query_canon` | `scripts/consultar_indice.py <termos>` — **read-only, rejeita flags** | `termos: list[str]` (validados: só `[\w\-]`, sem `--`) | `{trechos: [...]}` |

Regras:
- **Nenhuma tool escreve.** Não há `commit_entry` nesta fase (foi para a Fase 4).
- `query_canon`: valida cada termo contra `^[\wÀ-ÿ][\wÀ-ÿ\- ]*$`; **rejeita** qualquer
  argumento começando com `-` (barra o `--rebuild`, que regenera o índice). Nunca toca
  `memoria/missoes/`.
- `check_citation` (adaptador de temp, porque o script recebe caminho, não stdin):
  ```python
  import tempfile, os, subprocess
  def check_citation(texto: str) -> dict:
      fd, path = tempfile.mkstemp(prefix="mcp_cit_", suffix=".txt")
      try:
          os.write(fd, texto.encode()); os.close(fd)
          r = subprocess.run(["scripts/checar_citacao.sh", path],
                             cwd=os.path.expanduser("~/agata"),
                             capture_output=True, text=True)
      finally:
          os.unlink(path)
      return {"exit_code": r.returncode, "resumo": r.stdout, "suspeitos": _parse(r.stdout)}
  ```
- Toda tool retorna dado estruturado, nunca texto livre "achando" que algo é verdade.
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
- registra as 5 tools acima com `@mcp.tool`
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

- `redesign/mcp/servidor.py` sobe sem erro e lista as **5** tools.
- Para `run_perimetro`, `check_citation` e `lint_header`: o resultado pelo MCP é igual ao
  do script cru num caso conhecido.
- `query_canon` **rejeita** `["--rebuild", "x"]` com erro de validação e **aceita**
  `["hidratação", "âncora"]`, sem regenerar o índice (conferir `git status` limpo depois).
- `redesign/mcp/.venv` **não aparece** em `git status` (coberto por `.gitignore`).

## Rollback

Não destrutivo: `git checkout -- redesign/mcp` desfaz mudanças rastreadas.

O diretório `redesign/mcp/` é todo novo e isolado no branch `redesign`. **Só se for
necessário removê-lo por inteiro**, como passo isolado:

> ⚠️ **DESTRUTIVO — apaga o servidor MCP e seu venv. Rode sozinho.**
> ```fish
> rm -rf redesign/mcp
> ```

## Registro

- `STATUS.md`: P0-02 → "Feito"; anotar a versão do fastmcp instalada.
- `LOG.md`: entrada com os resultados dos testes de equivalência e o `HEAD` no fim.
