# P1-02 — sanitização de segredo ANTES da chamada sair

**Objetivo:** nenhum segredo (padrões de `PADROES_SEGREDO`) sai da máquina numa chamada
roteada pelo OmniRoute — a sanitização acontece **antes** do egresso. Item do aceite da
Fase 1: "segredo plantado é bloqueado antes de sair".

**Pré-requisitos:** P1-00 e P1-01 FEITO.

> **`redesign/router/sanitizar.py` JÁ EXISTE e está testado offline** (feito 2026-09-01,
> "continuar sem o HD"). Régua única: extrai `PADROES_SEGREDO` de
> `scripts/varredura_segredo.sh` via `bash -c 'source ...; printf ...'` — sem 2ª cópia.
> Única tradução ERE→Python: `[[:space:]]` → conjunto explícito; outra classe POSIX faz o
> módulo falhar alto. `--autoteste` verde (7 padrões casam os positivos, casos de menção
> não-valor passam). `--selftest` aceita payload JSON **ou** texto cru, exit 3 = bloqueado,
> redige o trecho (`sk-7…[33 chars]`, nunca o valor). **Falha fechada:** `sanitizar_payload`
> **levanta** `SegredoNoPayload`, não mascara-e-envia. Ver `redesign/router/README.md`.
> **O que falta desta tarefa:** só ligar o módulo no caminho de egresso (passo 3, A ou B)
> e os testes de integração (passos 4–5).

**Arquivos que a tarefa toca:**
- `redesign/router/sanitizar.py` — **já existe**; a tarefa só o wira no egresso
- config do OmniRoute: um hook de pré-request **ou** um proxy fino local (ver passo 3)
- `redesign/router/proxy.py` (novo, se for a opção B)
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

### 1. Confirmar que a régua ainda casa (o módulo já existe)

```fish
cd $HOME/agata
python3 redesign/router/sanitizar.py --padroes      # 7 padrões, iguais aos de varredura_segredo.sh
python3 redesign/router/sanitizar.py --autoteste    # tem que sair 0
```
Sucesso: `AUTOTESTE OK`, exit 0. Se `varredura_segredo.sh` mudou os padrões desde
2026-09-01, o `--autoteste` acusa (é a mesma fonte) — reconciliar antes de seguir.

### 2. — (feito) `sanitizar.py` está escrito e testado. Ver o cabeçalho desta tarefa e `redesign/router/README.md`.

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
- `python3 redesign/router/sanitizar.py --autoteste` → exit 0 (a régua ainda casa; mesma
  fonte que `varredura_segredo.sh`).
- `python3 redesign/router/sanitizar.py --padroes` == os 7 padrões de
  `bash -c 'source scripts/varredura_segredo.sh; printf "%s\n" "${PADROES_SEGREDO[@]}"'`.
- `redesign/router/` não contém nenhum segredo real (só regexes e código).

## Verificação independente

- **Quem:** fallback afinado ou Humano.
- **O quê:** que os padrões do `.py` vêm mesmo do `.sh` sem 2ª cópia, e que o bloqueio
  falha **fechado** (não "sanitiza e envia").
- **Como:** `diff <(python3 redesign/router/sanitizar.py --padroes | cut -f2) <(bash -c 'source scripts/varredura_segredo.sh; printf "%s\n" "${PADROES_SEGREDO[@]}"')`
  → sem diferença; ler o corpo de `sanitizar_payload` — confirma `raise SegredoNoPayload`,
  nunca `return payload` depois de achar.
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
