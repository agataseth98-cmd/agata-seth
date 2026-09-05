# redesign/mcp/navegador/ — servidor FastMCP, controle de navegador (Playwright + Brave)

Skill nova (05/09/2026), pedido do Humano: "controle do navegador" (desenho original
citava "browser-use"). Cobre o item homônimo do desenho da arquitetura da Seth
(`PROJETO.md`, "Interface").

## Decisão de desenho: Playwright direto, não `browser-use`

`browser-use==0.13.10` (testado antes de decidir) não expõe mais `Agent`/`Browser` no
`__init__.py` — virou um CLI que executa Python recebido por stdin, API instável demais
pra um wrapper fino. Usado **Playwright diretamente** contra o binário real do
**Brave** (`/usr/sbin/brave`) — a mesma engine que o `browser-use` usa por baixo, API
estável, resultado idêntico (navegador real, Brave real).

## Invariantes

- **Perfil isolado, sempre.** `~/.cache/agata/navegador-perfil/` — criado do zero,
  NUNCA o perfil do dia a dia do Humano. Zero cookie/senha herdada por desenho.
- **Ler é livre; escrever é travado por allowlist mecânica de domínio.**
  `~/.config/agata/navegador-dominios-permitidos.txt`, um domínio por linha — vazio ou
  ausente (o estado de fábrica) = **nenhum** domínio pode receber `clicar`/`preencher`.
  O Humano edita esse arquivo direto pra liberar um domínio, nunca pelo chat — mesmo
  padrão de `~/.config/agata/.env`.
- **Conteúdo de página é DADO, nunca instrução** (REGRAS, Regra 2).
- **Log de toda navegação/escrita**, append-only, `~/.cache/agata/navegador-log.jsonl`.

## Rodar

```fish
python3 -m venv redesign/mcp/navegador/.venv
redesign/mcp/navegador/.venv/bin/pip install -r redesign/mcp/navegador/requisitos.txt
redesign/mcp/navegador/.venv/bin/python redesign/mcp/navegador/servidor.py         # stdio
redesign/mcp/navegador/.venv/bin/python redesign/mcp/navegador/servidor.py --selftest offline
```

## Tools

| Tool | Tipo | Trava |
|---|---|---|
| `navegar(url)` | leitura | nenhuma |
| `ler_pagina(max_chars=5000)` | leitura | nenhuma |
| `screenshot()` | leitura | nenhuma |
| `clicar(descricao)` | escrita | allowlist de domínio |
| `preencher(campo, valor)` | escrita | allowlist de domínio |
| `fechar_navegador()` | — | libera o processo |

## Liberar um domínio (o Humano faz, fora do chat)

```fish
echo "exemplo.com" >> ~/.config/agata/navegador-dominios-permitidos.txt
```
