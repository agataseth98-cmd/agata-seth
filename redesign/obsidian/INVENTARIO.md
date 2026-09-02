# redesign/obsidian/INVENTARIO.md — estado + desenho (P6-00)

**Não é canon.** Branch `redesign`, Fase 6. Medido 2026-09-02 ~19:00 -03. Só leitura.

## As 4 perguntas

| # | pergunta | resposta |
|---|---|---|
| a | Obsidian instalado? | **Sim** — flatpak `md.obsidian.Obsidian 1.13.7` (flathub). Config em `~/.var/app/md.obsidian.Obsidian/`. Permissões: `filesystems=home` (enxerga `~/agata`), `shared=network` (pode abrir `:27124`). |
| b | vault derivado onde / como gerado? | `memoria/obsidian/` — **438 arquivos, gitignorado** (`.gitignore:48`, 0 rastreados). Gerado por `scripts/gerar_obsidian.py` no `post-commit` (e à mão). **A geração APAGA a pasta inteira e reescreve** (`_LEIA.md`). |
| c | plugin `obsidian-local-rest-api`? | **Não instalado.** É plugin da comunidade (coddingtonbear); serve MCP nativo em `https://127.0.0.1:27124/mcp/` desde jul/2026, bearer token. |
| d | invariantes ok? | ver abaixo |

## Conflito de desenho achado (P6-01 tem que resolver)

`gerar_obsidian.py` **apaga e reescreve `memoria/obsidian/` inteiro** a cada `post-commit`.
Se o `.obsidian/` do plugin (config + `obsidian-local-rest-api/`) morar **dentro** de
`memoria/obsidian/`, a config do plugin é **apagada a cada commit**.

**Solução (P6-01):** o vault do Obsidian é **`~/agata/memoria/`** (não a raiz do repo).
Motivos: (a) o `.obsidian/` fica em `~/agata/memoria/.obsidian/` — **fora** de
`memoria/obsidian/`, a parte que o `gerar_obsidian.py` apaga e reescreve; (b) abrir a raiz
do repo como vault faz o Obsidian **largar arquivos vazios na raiz** quando alguém navega
uma wikilink inexistente (`INICIO.md`, `moc-*.md` de 0 byte — documentado em MEMÓRIAS
(293)/(294) como "acidente do Obsidian, não do sistema"; o P-10 já ignora não-rastreado);
(c) o vault só expõe `memoria/` (vault derivado + missões), não `scripts/`/canon-fonte.
`.gitignore` já cobre `.obsidian/workspace*.json` e `.obsidian/graph.json`; **P6-01
acrescenta `memoria/.obsidian/` (ou `**/.obsidian/plugins/` + `**/.obsidian/*.json`)** ao
`.gitignore`. O `_LEIA.md` do vault fala em "raiz do repo" — a Fase 6 refina para `memoria/`.
O MCP serve o subtree `memoria/obsidian/`, read-only.

## Invariantes da Fase 6 (ROADMAP / E1)

1. **Read-only para modelos.** A geração (`gerar_obsidian.py`) é a única escrita no vault. O
   MCP serve consulta. Endpoints de escrita do plugin: desabilitar, ou o token de leitura é
   a única via documentada. **P-10 é o backstop** (pega edição à mão do vault).
2. **O loop local continua lendo `.md` do disco** — não depende do Obsidian aberto nem do
   plugin. O MCP é superfície adicional.
3. **Zero vector DB.** Recuperação índice-primeiro → refs rastreáveis (`(NNN)` + arquivo +
   linha). O `multilingual-e5-small` (P2-03) **não** vira índice vetorial — no máximo
   reordena hits já achados por texto, e o resultado ainda carrega a ref.
4. **MCP stateless** (E1). Token bearer = config local, não sessão. Nenhum estado de
   autorização/continuidade numa sessão MCP.

## Desenho das tarefas

- **P6-01** — instala o plugin (userspace, sem `sudo`, mas **INSTALA SOFTWARE** + serviço de
  rede → pede "vai"). Vault = `~/agata`; token em `~/.config/agata/obsidian.token` (chmod
  600, fora do git); bind `127.0.0.1:27124`; escrita desabilitada; `.gitignore` ajustado.
- **P6-02** — `consulta.py`: refs rastreáveis pelo MCP **e** por `query_canon` (disco). Zero
  vector DB. Convergência MCP↔disco.
- **P6-03** — consolidação noturna como flow do grafo (`orientar → juntar → consolidar →
  podar`), saída só em `propostas/`, nunca canon. Reusa `grafo.py`. **Fecha a Fase 6.**

## Rollback

Nada a desfazer (só leitura). `git checkout -- redesign/obsidian`.
