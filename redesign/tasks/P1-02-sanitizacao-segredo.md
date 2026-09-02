# P1-02 — sanitização de segredo ANTES da chamada sair

**Objetivo:** nenhum segredo (padrões de `PADROES_SEGREDO`) sai da máquina numa chamada
roteada pelo OmniRoute — a sanitização acontece **antes** do egresso. Item do aceite da
Fase 1: "segredo plantado é bloqueado antes de sair".

**Pré-requisitos:** P1-00 e P1-01 FEITO.

**Arquivos que a tarefa toca:**
- `redesign/router/sanitizar.py` (novo) — o módulo de scrub, que **reusa os mesmos
  padrões** de `scripts/varredura_segredo.sh` (`PADROES_SEGREDO`)
- `redesign/router/PADROES_SEGREDO.txt` (novo) — os padrões extraídos num só lugar, para
  o `.sh` e o `.py` lerem a mesma régua (ou o `.py` lê o próprio `.sh` — decidir no passo 1)
- config do OmniRoute: um hook de pré-request **ou** um proxy fino local (ver passo 2)
- `redesign/tasks/P1-02-*.md`

---

## Decisão de desenho (passo 1)

Duas formas de garantir "antes de sair":
- **(A) hook nativo do OmniRoute** — se a versão expõe um request-transform / policy
  plugin que roda antes do egresso. Confirmar na doc (`/dashboard` → policies, ou config).
- **(B) proxy fino local** — um processo em `127.0.0.1:20127` que recebe do caller, roda
  `sanitizar.py`, e só então repassa para `127.0.0.1:20128`. O caller aponta para `:20127`.

Preferir (A) se existir e rodar in-process. (B) é o fallback determinístico e é o que os
testes abaixo assumem se (A) não servir.

Regra dura: a sanitização **falha fechado** — padrão casado ⇒ a chamada é **bloqueada**
(não mascarada e enviada). Bloqueio devolve erro estruturado ao caller com qual padrão
casou (sem ecoar o segredo).

---

## Passos

### 1. Extrair os padrões para um só lugar

```fish
cd $HOME/agata
# tira o array PADROES_SEGREDO do .sh e grava um por linha
awk '/^PADROES_SEGREDO=\(/{f=1;next} f&&/^\)/{f=0} f{gsub(/^[ \t]*.\x27/,"");gsub(/\x27.*$/,"");print}' \
  scripts/varredura_segredo.sh > redesign/router/PADROES_SEGREDO.txt
cat redesign/router/PADROES_SEGREDO.txt
```
Colar de volta: o conteúdo. Sucesso: 7 regexes, iguais às do `.sh` (conferir à mão).
**Alternativa mais robusta:** `sanitizar.py` faz `source` lógico do `.sh` via `bash -c`
uma vez no import e captura o array — assim nunca há duas cópias. Decidir aqui.

### 2. `sanitizar.py`

Escrever `redesign/router/sanitizar.py`:
- `carregar_padroes()` — lê `PADROES_SEGREDO.txt` (ou extrai do `.sh`), compila com `re`.
- `varrer(texto) -> list[tuple[str,str]]` — devolve [(nome_padrão, trecho_redigido)] dos
  casos; `trecho_redigido` mostra só os 4 primeiros chars + `…` (nunca o segredo inteiro).
- `sanitizar_payload(payload: dict) -> dict` — varre todos os `messages[*].content` (e
  `system`); se achar, **levanta** `SegredoNoPayload` com a lista de nomes de padrão.
- CLI `--selftest`: lê JSON do stdin, imprime `{bloqueado: bool, padroes: [...]}`.

### 3. Ligar no caminho de egresso (A ou B)

- (A): registrar `sanitizar_payload` como policy de pré-request no OmniRoute.
- (B): `redesign/router/proxy.py` — `aiohttp`/`http.server` em `127.0.0.1:20127`, chama
  `sanitizar_payload`, repassa para `:20128`, devolve a resposta. `systemd --user`
  `omniroute-sanitizer.service`.

### 4. Teste — segredo plantado é bloqueado

```fish
cd $HOME/agata
# gerar na hora uma string OpenAI-style FALSA que case o padrão (NÃO colar chave, nem fake,
# num arquivo versionado -- o P-1 do perímetro barra e está certo em barrar):
set FAKE (printf 'sk-%s' (head -c 40 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 30))
curl -s -o /tmp/p1_02.json -w "%{http_code}\n" http://127.0.0.1:2012<7 ou 8> /v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"model":"<modelo-ollama>","messages":[{"role":"user","content":"minha chave é '"$FAKE"'"}]}'
cat /tmp/p1_02.json
# e o caso limpo, que tem que passar:
curl -s -o /tmp/p1_02_ok.json -w "%{http_code}\n" http://127.0.0.1:2012<7 ou 8> /v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"model":"<modelo-ollama>","messages":[{"role":"user","content":"responda só: ok"}]}'
cat /tmp/p1_02_ok.json
```
Colar de volta: os dois HTTP codes e os dois corpos.
Sucesso: o com `$FAKE` é **bloqueado** (4xx, corpo diz qual padrão, sem ecoar a chave);
o limpo passa (200).

### 5. Confirmar que nada saiu no caso bloqueado

```fish
# rodar o curl bloqueado com um sniff simples do egresso
set FAKE (printf 'sk-%s' (head -c 40 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 30))
sudo timeout 8 tcpdump -n -c 20 -i any 'tcp and not host 127.0.0.1' &
sleep 1
curl -s http://127.0.0.1:2012<7 ou 8>/v1/chat/completions -H 'content-type: application/json' \
  -d '{"model":"<modelo-ollama>","messages":[{"role":"user","content":"chave '"$FAKE"'"}]}' >/dev/null
wait
```
Colar de volta: a saída do `tcpdump` (esperado: nada de tráfego externo disparado por essa chamada).

---

## Aceite

- Payload com um padrão de `PADROES_SEGREDO` ⇒ HTTP 4xx do gateway/proxy, corpo nomeia o
  padrão, **não** ecoa o segredo, e **nada** trafega para fora (passo 5).
- Payload limpo ⇒ 200, resposta normal.
- `sanitizar.py --selftest` casa exatamente os mesmos casos que `bash scripts/varredura_segredo.sh`
  casaria para os mesmos textos (rodar os 7 padrões contra strings de exemplo, comparar).
- `redesign/router/` não contém nenhum segredo real (só regexes e código).

## Verificação independente

- **Quem:** fallback afinado ou Humano.
- **O quê:** que os padrões do `.py` são byte-a-byte os do `.sh` (uma régua só), e que o
  bloqueio falha **fechado** (não "sanitiza e envia").
- **Como:** `diff <(sed -n '/PADROES_SEGREDO=(/,/^)/p' scripts/varredura_segredo.sh | grep -oE "\x27[^\x27]+\x27") redesign/router/PADROES_SEGREDO.txt`
  (ajustar); revisar o caminho de erro do `sanitizar_payload` — que ele `raise`, não
  `return payload_limpo`.
- **Resultado:** anotar no LOG.

## Rollback

Não destrutivo: `git checkout -- redesign/router` desfaz o rastreado.
```fish
systemctl --user stop omniroute-sanitizer.service 2>/dev/null; or true
rm -f $HOME/.config/systemd/user/omniroute-sanitizer.service
systemctl --user daemon-reload
# se foi via policy (A): remover a policy pelo dashboard
```

## Registro

- `STATUS.md`: P1-02 → "Feito"; anotar se foi via (A) policy nativa ou (B) proxy.
- `LOG.md`: os HTTP codes dos 2 casos, a saída do `tcpdump`, o diff de padrões, o
  resultado da verificação independente, `HEAD` no fim.
