# RELAY — auditoria do `conselho-remoto-omniroute.diff` (Cadeia de auditoria, camada B)

**Para o Humano colar num modelo em nuvem (Kimi / outro).** O modelo é a **camada B**
(audita o `.diff` e a auto-revisão da camada A abaixo). Depois o resultado volta, a
**camada C** (esta Máquina) verifica as alegações de B contra git/código, e só então o
Humano cria `redesign/propostas/APROVADO-conselho-remoto-omniroute`.

---

## Contexto

Sistema Agata, redesenho, Fase 8 (cutover). O `scripts/conselho_remoto.py` é o coletor do
**Conselho Remoto**: envia UM pedido de parecer (já escrito pelo Humano) a UM modelo
externo e guarda a resposta crua. Não interpreta, não resume, não escreve canon.

Na **Fase 1 (P1-04)** a rede desse script foi trocada: em vez de falar direto com a API do
GLM/Gemini (com chave, backoff próprio, circuit breaker próprio), ele agora faz **uma POST
em `http://127.0.0.1:20127/v1/chat/completions`** — o proxy de sanitização de segredo
(P1-02) — que repassa ao OmniRoute na combo `conselho` (`glm-4.7-flash → gemini-2.5-flash`).
O script **não lê mais chave nenhuma**.

Isso foi commitado no branch `redesign` com `git commit --no-verify` (estado de exceção
autorizado). Para entrar em `main` precisa do par P-8 (`.diff` + `APROVADO-`) **e** desta
Cadeia de auditoria, porque toca **rede** e o **mecanismo do Conselho**.

Diff: −246 / +70 linhas. O `.diff` completo está em
`redesign/propostas/conselho-remoto-omniroute.diff`.

## Invariantes que NÃO podiam mudar (e a camada A diz que não mudaram)

| # | invariante | onde no código novo |
|---|---|---|
| I1 | só material do repo **público** sai | `checar_conteudo_privado` — regex `memoria[/\\]missoes`, aborta o envio |
| I2 | teto de tamanho do pedido | `TETO_CHARS_PEDIDO = 60_000`, aborta acima |
| I3 | **uma** chamada externa por invocação, sem laço | `enviar_omniroute` chamado 1× em `main`, sem `for`/`while` |
| I4 | provedores externos esgotaram → **ABORTA** (não cai pro local) | `HTTPError` e `except Exception` → `return 1`; cair pro local é decisão do Humano |
| I5 | não escreve MEMÓRIAS/PROJETO/REGRAS | só grava `memoria/missoes/conselho-remoto/<ts>.json` (resposta crua) |
| I6 | formato do parecer conferido, não o conteúdo | `checar_formato_parecer` — 4 partes (Origem/Posição/Fundamentação/Emenda) |
| I7 | segredo nunca sai | delega ao proxy `:20127`; o caminho HTTP 422 `secret_blocked_before_egress` é tratado explícito |

## Auto-revisão da camada A (esta sessão Claude, na Máquina)

Verifiquei no código e no git:
- **I3** ✓ — `grep -n "enviar_omniroute"` = 1 definição + 1 chamada; sem loop.
- **I4** ✓ — os dois `except` retornam 1; nenhuma referência a modelo local no caminho de erro.
- **sem chave** ✓ — `grep -nE "KEY|TOKEN|api_key|Authorization"` no arquivo novo = nada além
  do comentário; o único `os.environ.get` fora do endpoint é inexistente.
- **I5** ✓ — o único `open(..., "w")` é o `destino` em `memoria/missoes/conselho-remoto/`.
- **I1** ✓ — `checar_conteudo_privado` + `PADRAO_CONTEUDO_PRIVADO` são **byte a byte
  idênticos** entre `main` e `redesign` (`git show main:… | grep -A6`). A regex
  `memoria[/\\]missoes` não pega `memoria / missoes` com espaços nem `missoes` sozinho —
  mas isso é **herdado, não introduzido** por este `.diff`. **Sem regressão em I1.**
- **removido de propósito** (passa a ser responsabilidade do OmniRoute): `carregar_chave`,
  `enviar_glm`/`enviar_gemini`, toda a máquina de backoff 429 (`checar_backoff`,
  `BACKOFF_ESTADO_PATH`), o contador de cota local do Gemini (`GEMINI_CONTADOR_PATH`,
  `GEMINI_AVISO_LIMIAR`). `TETO_CHARS_PEDIDO`/`TETO_TOKENS_SAIDA` inalterados.
- Testado de verdade no branch (LOG redesign 2026-09-02 ~08:45): combo `conselho` → GLM
  lento → **fallback para Gemini** → 4 partes presentes → `checar_formato_parecer` PASS,
  registro `.json` gravado. `python3 -m py_compile` OK.

## O que a camada B deve auditar (perguntas)

1. **A delegação ao OmniRoute está completa e correta?** O que saiu do script (chave,
   backoff 429, contador de cota, circuit breaker) agora é do OmniRoute. Há alguma dessas
   garantias que o OmniRoute **não** oferece de forma equivalente, deixando um buraco? (A
   camada A checou que a combo `conselho` tem fallback e que `omniroute cost` contabiliza,
   mas não auditou o backoff/breaker do OmniRoute em profundidade.)
2. **Rota por config vs. pino explícito.** Antes o script fixava o provedor (GLM, com
   fallback Gemini) no próprio código. Agora usa a combo `conselho` do OmniRoute — se
   alguém reconfigurar essa combo, o Conselho passa a usar outros modelos **sem** mudança
   no script nem no canon. Isso fere a rastreabilidade que o Conselho exige (REGRAS "Segunda
   opinião" / "Cadeia de auditoria")? Como mitigar sem voltar ao pino no código?
3. **Logs do OmniRoute.** O pedido do Conselho (texto público, por I1) passa pelo OmniRoute,
   que mantém `~/.omniroute/logs` e `db_backups`. Guardar o texto do pedido nesses logs
   locais é aceitável (é material público), ou merece uma nota/mitigação?
4. **`thinking: {"type": "disabled"}`** no payload — o OmniRoute repassa isso por-provedor?
   Se não repassar, o loop de "thinking" de (212) pode voltar. É bloqueante para o merge ou
   é follow-up?
5. **Superfície de erro.** O `except Exception` genérico (BLE001) captura tudo e aborta. Há
   algum modo de falha em que ele **deveria** propagar em vez de virar "ABORTADO" silencioso
   com `return 1`?
6. **Algo que a camada A não viu.**

Formato da resposta: **Origem · Posição · Fundamentação · Emenda** (as 4 partes que o
próprio Conselho exige). Sem executar nada — você não tem shell; aponte o que a camada C
(Máquina) deve rodar para confirmar cada achado seu.

---

## Camada B — resposta (Qwen, Qwen Studio, nuvem, 2026-09-03) — RESUMO

**Posição:** diff seguro para merge sob P-8, com 3 emendas (1 documental obrigatória,
2 código recomendada, 3 nice-to-have). Delegação ao OmniRoute completa; I1–I7 preservados;
nenhum bloqueio para a Fase 8. 6 perguntas respondidas; sem achado bloqueante.

## Camada C — verificação na Máquina (sessão Claude, 2026-09-03) — VEREDITO

Rodado no `~/.omniroute/storage.sqlite` e no `:20127`:

| ponto de B | o que a Máquina achou |
|---|---|
| **I4 — combo `conselho` tem tier local?** | **NÃO.** `combos` v2 (2026-09-02T11:42): exatamente `zai/glm-4.7-flash → gemini/gemini-2.5-flash`, `strategy=priority`, **sem tier local**. `session_model_history` mostra entradas `conselho → ollama-local/llama3.2:3b` mas TODAS **antes** da v2 (03:17 / 11:37) — combo antiga. **I4 preservado.** |
| B: "código em `router/providers.py`, `_request_with_backoff`, `~/.omniroute/state.json`, `~/.omniroute/costs/`" | **Esses paths NÃO EXISTEM.** OmniRoute é Node (`~/.npm-global`) + SQLite (`~/.omniroute/storage.sqlite`), não Python. As alegações de B sobre os internos do OmniRoute são **não verificadas**. A *posição* de B (delegação sonora, sem bloqueio) se sustenta pelo teste prático do fallback (LOG 02/09 ~08:45) + a combo v2 conferida agora. |
| B: timeout da combo 30–120s | Real: o deadline é `resilienceSettings.requestQueue.maxWaitMs=15000` (15 s, default de código do OmniRoute — não está em `key_value`). Não afeta o `conselho_remoto.py` (que tem `urlopen(timeout=180)` próprio + os modelos de nuvem estão quentes). Mitigado p/ modelo local frio pelo `agata-warmup.service` (B2). |
| B: logs do OmniRoute com texto do pedido | `~/.omniroute/call_logs/<data>/` + tabelas `call_logs`/`request_detail_logs` no sqlite. Guardam o pedido. Por I1 é material público; segredo barrado no `:20127`. Aceitável — nota adicionada ao docstring (Emenda 1). |
| B Emenda 1 (doc) | **aplicada** — nota de rastreabilidade + logs no docstring. |
| B Emenda 2 (`provider` no `.json`) | **aplicada** — `_provider_do_modelo()` deriva do nome; testado: `.json` de saída agora tem `"provider": "gemini"`. A `resposta_crua` continua sendo a fonte. |
| B Emenda 3 (erro de conexão claro) | **aplicada** — `except (ConnectionRefusedError, URLError)` → "suba o serviço P1-02". |
| `checar_conteudo_privado` vs `main` | **byte a byte idêntico** (Camada A já tinha verificado; C confirma). |

**Veredito C:** o `.diff` (com as 3 emendas) está **pronto para o merge**. As camadas A, B e C
concordam na direção; C corrigiu as alegações de B sobre internos do OmniRoute (paths
inexistentes) sem mudar a conclusão. `py_compile` OK; parecer real de teste gravado com os
4 campos + `provider`.
