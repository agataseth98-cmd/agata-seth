# redesign/router/ — camada do gateway de modelo (Fase 1)

**Não é canon.** Branch `redesign`. Suporte à Fase 1 (OmniRoute como gateway único).

## `sanitizar.py` — scrub de segredo antes do egresso (P1-02)

Feito 2026-09-01 ("continuar sem o HD"), **testado offline**, ainda **não ligado** ao
caminho de saída (isso é o passo 3 da P1-02, quando o OmniRoute estiver de pé).

### Régua única

Os padrões vêm de `scripts/varredura_segredo.sh` (`PADROES_SEGREDO`, 7 regexes ERE),
extraídos em runtime por `bash -c 'source ...; printf "%s\n" "${PADROES_SEGREDO[@]}"'` —
**sem segunda cópia**, sem re-digitar. Se o `.sh` mudar a régua, o `--autoteste` acusa.

Única tradução ERE→Python: `[[:space:]]` → `[ \t\n\r\f\v]` (semântica C-locale). Qualquer
outra classe POSIX (`[[:alnum:]]` etc.) faz `PadraoNaoTraduzivel` — o módulo **não
adivinha**.

### Contrato

- `varrer(texto) -> [{padrao_rotulo, padrao, trecho_redigido, pos}]` — `trecho_redigido` é
  `<4 chars>…[N chars]`, **nunca** o valor.
- `sanitizar_payload(payload: dict) -> dict` — varre `system`, `prompt`, `input[*]`,
  `messages[*].content` (str e content-parts). Casou ⇒ **levanta** `SegredoNoPayload`
  (`.achados`). **Falha fechada:** não existe caminho "mascara e devolve". Payload limpo
  volta igual.

### CLI

```
python3 redesign/router/sanitizar.py --padroes     # os 7 padrões (auditoria da régua)
python3 redesign/router/sanitizar.py --autoteste   # fixtures; exit 0 = OK
python3 redesign/router/sanitizar.py --selftest    # stdin = JSON de payload OU texto cru
                                                   # imprime {bloqueado, achados}; exit 3 = bloqueado
```

### Verificado (2026-09-01, offline)

- `--padroes` == `bash -c 'source scripts/varredura_segredo.sh; printf "%s\n" "${PADROES_SEGREDO[@]}"'` — sem diferença.
- `--autoteste`: os 7 padrões casam um positivo cada; 4 casos de menção-não-valor
  (`"o padrão sk-[A-Za-z0-9]{20,} casa..."`, `"aki de manhã"`, ...) passam limpos.
- `--selftest` com payload contendo `sk-…` (gerado na hora, não versionado) → `bloqueado:
  true`, exit 3, `trecho_redigido: "sk-7…[33 chars]"`. Payload limpo → exit 0.

### O que falta (P1-02, quando o OmniRoute existir)

Escolher (A) policy de pré-request nativa do OmniRoute, **ou** (B) o `proxy.py` abaixo.
Depois os testes de integração contra o OmniRoute real (curl + `tcpdump`).

## `proxy.py` — opção B da P1-02 (feito, testado offline)

Proxy fino em `127.0.0.1:20127`, só stdlib (`http.server` + `urllib`), sem instalar nada.
POST com corpo JSON → `sanitizar.sanitizar_payload` → **só então** repassa para o
`OMNIROUTE_UPSTREAM` (default `:20128`). Casou um padrão ⇒ **422** com erro estruturado
(campo + rótulo + trecho redigido), e o **upstream nunca é tocado**. GET/HEAD passam sem
inspeção. Streaming/SSE passa byte a byte.

```
python3 redesign/router/proxy.py             # sobe (caller aponta para :20127)
python3 redesign/router/proxy.py --selftest  # upstream dummy + proxy; 1 limpo (200) + 1 sujo (422, upstream NAO tocado)
```
Verificado 2026-09-01: `--selftest` verde — pedido limpo passa (200, dummy respondeu),
pedido com `sk-…` plantado → 422, dummy **não tocado**, trecho `sk-Z…[27 chars]`.
Env: `OMNIROUTE_UPSTREAM`, `SANITIZER_BIND`. `systemd --user omniroute-sanitizer.service`
na execução da P1-02.

## `PROVEDORES.md` — P1-03 (template, feito)

Tabela do pool nuvem (Groq/Cerebras/DeepSeek/GitHub Models/Gemini/OpenRouter/Mistral) com
env vars, base URLs, limites vistos em 01/09 (marcados RECONFERIR) e as combos
`cheap`/`auto`/`conselho`. Chaves só no `~/.hermes/.env`, editadas pelo Humano.

## `omniroute-prep/` — P1-00, tudo menos o install

A sessão Claude não pode rodar `npm install` (classificador de permissão). Preparado aqui:
- `INSTALAR.md` — a linha única (`! npm install -g omniroute`, sem sudo, prefix
  `~/.npm-global`) ou a regra `Bash(npm:*)`.
- `omniroute.service` — unit `systemd --user` (bind `127.0.0.1:20128`, headless; CONFERIR
  subcomando/env na doc). Sem `enable`.
- `verificar.sh` — checagens de P1-00 (binário, boot, bind local, `/v1/models` 200, sem
  chave em disco). Read-only.

## `conselho_via_omniroute.md` — P1-04 (desenho, feito)

Antes/depois de `scripts/conselho_remoto.py`: tabela do que **não muda** (política:
conteúdo privado, teto, uma chamada, aborta-não-cai-pro-local, não escreve canon) vs. o
que muda (urllib direto a z.ai/Google → `enviar_omniroute()` na combo `conselho`; script
não lê mais chave; breaker/contadores → OmniRoute). Esboço de código + testes + rollback.
Merge para `main` só na Fase 8.
