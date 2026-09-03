# P8-05 — Hermes sai do loop

**Status:** 🔶 **INVENTÁRIO FEITO — 2026-09-03 (chat 6). Execução NÃO feita** — toca serviço
de produção (Hermes) e depende de P8-02 verde (7 dias reais). Tirar o Hermes do loop antes
de o paralelo provar o substituto = risco → parei aqui de propósito.

## Inventário (2026-09-03, read-only)

- **`hermes-gateway.service`** (user, `active` + **`enabled`** p/ boot). `ExecStart` =
  `hermes_cli.main gateway run`, `WorkingDirectory=~/.hermes`, porta **8642** (compartilha
  com o `api_server`, bind `127.0.0.1`). É o **executor** do loop de governança: segura o
  contexto do modelo, hidrata via `.hermes.md`, roda as tools/skills.
- **`channel_directory.json`** → `"platforms": {}` — **nenhuma** ponte Slack/Discord/
  Telegram ativa agora. `platform_toolsets` no `config.yaml` existe mas ocioso.
- **Frontend/voz (Docker, à parte):** `open-webui` (8080) + `kokoro-tts` (8880). PROJETO.md:
  "Open WebUI como frontend puro — tools/memória/search nativos desligados; o executor e a
  memória são do Hermes."
- **`agata-consolidacao.timer`** usa o Hermes (SQLite `state.db`) — vira flow do grafo
  (P6-03 já fez `flows/consolidacao.py`), mas o timer ainda aponta pro Hermes.
- **P-9** (`perimetro.sh`) monitora `hermes-gateway.service`, `open-webui`, `kokoro-tts` —
  se desabilitar o gateway, ajustar o P-9 (senão vira AVISO permanente).
- **`.hermes.md`** — hidratação primária hoje (`.githooks/gerar-hermes-md.sh`). No cutover
  vira referência; a hidratação do loop é `estado_para_eco.sh` + `query_canon`/`consulta.py`.

## Passos (quando P8-02 fechar + "vai")

1. Confirmar com o Humano: usa Open WebUI? usa voz (kokoro-tts)? → definem o que fica de pé.
2. `agata-consolidacao.timer` → repontar pro `flows/consolidacao.py` (grafo) ou desabilitar.
3. `systemctl --user disable --now hermes-gateway.service` **se** nada de OWUI/voz depender
   dele. Se depender, manter o gateway só p/ esse caminho e documentar.
4. Ajustar **P-9** (`perimetro.sh`, via `.diff` P-8) p/ não exigir o que saiu de pé.
5. `.hermes.md` → nota de papel novo em PROJETO.md (parte do P8-06).
6. Teste de fumaça: `agata up` → `grafo.py run` de pedido real num clone → 6 nós + portão +
   commit, tudo sem o Hermes.

## Perguntas abertas p/ o Humano

- Você ainda usa **Open WebUI** (a UI web em 8080)? E **voz** (kokoro-tts)?
- O `hermes-gateway` na porta 8642 — algo além do loop de governança depende dele hoje
  (algum script, o `api_server`)?

**Objetivo:** o caminho novo (grafo + OmniRoute) vira o **único** que dirige o Agata. O
Hermes deixa de estar no loop de governança; fica **só** como serviço de voz / Open WebUI
se esses estiverem em uso, como unidades à parte.

**Pré-requisitos:** P8-02 (decisão "empatou/superou"), P8-03 (fabricação PASS), P8-04.

## Passos
1. **Inventariar o que o Hermes faz hoje** — `hermes-gateway.service` (user), o que chama,
   quem depende (`~/.hermes/`, Open WebUI, voz). Registrar antes de mexer.
2. **Tirar do loop:** o loop de governança passa a ser `redesign/grafo/grafo.py` (via o
   `agata` CLI / `agata.target`). O Hermes **não** é mais chamado para hidratar/rotear/
   trabalhar. Se nada de voz/OWUI usa o Hermes → `systemctl --user disable --now
   hermes-gateway.service` (reversível). Se voz/OWUI usam → manter só esse caminho,
   documentar que o gateway agora serve só isso.
3. **`.hermes.md` de produção** — deixa de ser a hidratação primária (passa a ser consulta
   ao índice / `query_canon`). O arquivo não se apaga; o `post-commit` segue gerando (é
   barato e serve de referência). Registrar a mudança de papel.
4. **Teste de fumaça:** com o Hermes fora do loop, `agata up` → `grafo.py run` de um pedido
   real num clone → 6 nós + portão + commit no clone. Voz/OWUI (se em uso) respondem como
   serviço isolado.

## Aceite
- Loop roda ponta a ponta **sem** o Hermes no caminho.
- Voz / Open WebUI (se em uso) seguem funcionando como serviço à parte; se não em uso,
  `hermes-gateway.service` `disabled`.
- Papel do `.hermes.md` redefinido e registrado.

## Verificação independente
Camada C: `systemctl --user status hermes-gateway` bate com o que o passo 2 decidiu;
`grafo.py` não importa nem chama nada de `~/.hermes/` no caminho do loop (grep); o teste de
fumaça roda de estado limpo.

## Rollback
`systemctl --user enable --now hermes-gateway.service`; reapontar o loop para o Hermes.
Reversível enquanto `main` não mudou (P8-07).

## Registro
`STATUS.md`: P8-05 → Feito; quem dirige o Agata agora (grafo + OmniRoute).
`LOG.md`: inventário do Hermes, o que foi desabilitado/mantido, o teste de fumaça.
