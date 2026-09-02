# P1-04 — aposentar a REDE do conselho_remoto.py (mantém política + regex)

**Objetivo:** o `conselho_remoto.py` deixa de fazer syscall de rede próprio (urllib direto
a z.ai / Google) e passa a mandar o pedido pelo OmniRoute (`:20128`). **Toda a política
continua** — check de conteúdo privado, teto de chars, uma chamada por invocação, nunca
escreve canon, nunca encadeia. É o último item da Fase 1.

**Pré-requisitos:** P1-00 a P1-03 FEITO. Em especial P1-03 (a combo que substitui o
fallback GLM→Gemini que hoje está codado no script).

**Arquivos que a tarefa toca:**
- `scripts/conselho_remoto.py` — **canônico, mas NÃO em `main`**: fica no branch
  `redesign`. A mudança em `main` é só na Fase 8, pelo processo normal (Cadeia de
  auditoria). Aqui edita-se a cópia do branch e testa-se; o merge é Fase 8.
- `redesign/router/conselho_via_omniroute.md` (novo) — o desenho e o antes/depois
- `redesign/tasks/P1-04-*.md`

> **Classe de risco (CONTINUIDADE §7): mexe em script canônico + rede.** Revisão de plano
> por 2º par de olhos antes de qualquer passo. E: como toca um arquivo que existe em
> `main`, o `git diff main..redesign -- scripts/conselho_remoto.py` passa a ter conteúdo —
> **esperado**, é trabalho de branch; não reverter. O merge para `main` é a Fase 8.

---

## O que muda e o que NÃO muda

| Fica igual (é a razão do script existir) | Muda |
|---|---|
| `checar_conteudo_privado()` — pedido some se cita `memoria/missoes/` | `enviar_glm()` / `enviar_gemini()` (urllib direto) → **uma** função `enviar_omniroute()` que faz `POST 127.0.0.1:20128/v1/chat/completions` |
| `TETO_CHARS_PEDIDO` | O fallback GLM→Gemini codado no script → **delegado à combo do OmniRoute** (ex.: uma combo `conselho` = [glm-flash → gemini-flash]) |
| "uma chamada externa por invocação, nunca as duas de propósito, nunca encadeia" | A leitura de `ZHIPU_API_KEY`/`GOOGLE_API_KEY` do `~/.hermes/.env` → o OmniRoute é quem tem as chaves; o script não lê mais chave nenhuma |
| "não escreve MEMÓRIAS/PROJETO/REGRAS, não interpreta, não decide" | O backoff/429 local do script → o **circuit breaker do OmniRoute** (o script só repassa o erro) |
| Guarda a resposta crua; normaliza tokens/custo | O custo agora sai do OmniRoute (já vem no response ou no log) |
| Aborta se os dois externos falharem (cair pro local é decisão do Humano) | — mantém: se a combo `conselho` esgotar, `enviar_omniroute` devolve erro e o script ABORTA, como hoje |

O **módulo de regex** de segredo já não estava no `conselho_remoto.py` (está em
`varredura_segredo.sh` / agora `redesign/router/sanitizar.py`, P1-02). A sanitização de
egresso do pedido do Conselho passa a ser a mesma da P1-02, porque a chamada vai pelo
OmniRoute.

---

## Passos

### 1. Combo `conselho` no OmniRoute

Configurar uma combo dedicada `conselho` = [`glm-4.7-flash` (z.ai) → `gemini-2.5-flash`
(Google)], mesma ordem que o script tem hoje. Chaves `ZHIPU_API_KEY` / `GOOGLE_API_KEY`
no store do OmniRoute (o Humano move/replica do `~/.hermes/.env`, sem chat).

### 2. Reescrever a camada de rede do script (na cópia do branch)

Em `scripts/conselho_remoto.py` (branch `redesign`):
- remover `enviar_glm`, `enviar_gemini`, `carregar_chave`, `checar_backoff`,
  `_backoff_log`, os contadores Gemini, `ENDPOINT`/`GEMINI_ENDPOINT`.
- adicionar:
  ```python
  OMNIROUTE = "http://127.0.0.1:20128/v1/chat/completions"
  COMBO = "conselho"
  def enviar_omniroute(pedido_texto: str) -> dict:
      corpo = json.dumps({"model": COMBO,
                          "messages": [{"role": "user", "content": pedido_texto}]}).encode()
      req = urllib.request.Request(OMNIROUTE, data=corpo, method="POST",
                                   headers={"content-type": "application/json"})
      with urllib.request.urlopen(req, timeout=180) as resp:
          return json.loads(resp.read())
  ```
- `main()` mantém: `checar_conteudo_privado` → teto de chars → `enviar_omniroute` (uma vez)
  → se erro, ABORTA com a mensagem de sempre → normaliza resposta/tokens → grava cru.
- `_normalizar` já cobre o formato OpenAI-compatível (`choices[0].message.content`,
  `usage`) — que é o que o OmniRoute devolve. Conferir.

### 3. Teste — pedido real pelo novo caminho

```fish
cd $HOME/agata
printf '%s\n' "Pergunta de teste do Conselho: em uma frase, o que é uma tag anotada no git?" > /tmp/pedido_teste.txt
python3 scripts/conselho_remoto.py /tmp/pedido_teste.txt | tee /tmp/p1_04_resp.txt
echo "exit: $status"
```
Colar de volta: a saída inteira.
Sucesso: resposta crua guardada como antes; `exit 0`; o pedido aparece no log do OmniRoute
na combo `conselho`.

### 4. Teste — política intacta

```fish
cd $HOME/agata
printf '%s\n' "isto cita memoria/missoes/agata-sistema para forçar o abort" > /tmp/pedido_privado.txt
python3 scripts/conselho_remoto.py /tmp/pedido_privado.txt; echo "exit: $status"
# esperado: "ABORTADO: o pedido menciona ... camada privada ...", exit 1, NADA enviado
```
Colar de volta: a saída + exit.
Sucesso: aborta local, sem tocar a rede (conferir com `tcpdump` como na P1-02 passo 5).

### 5. Teste — os dois provedores fora ⇒ ABORTA (não cai pro local sozinho)

```fish
# desabilitar glm e gemini na combo (dashboard) ou chave inválida
python3 scripts/conselho_remoto.py /tmp/pedido_teste.txt; echo "exit: $status"
# esperado: ABORTA, exit != 0, mensagem de que cair pro local é decisão do Humano
```

---

## Aceite

- `python3 scripts/conselho_remoto.py <pedido.txt>` funciona **sem** o script ler chave
  nenhuma (`grep -nE 'ZHIPU_API_KEY|GOOGLE_API_KEY|api.z.ai|generativelanguage' scripts/conselho_remoto.py` → vazio) e sem urllib para fora (só `127.0.0.1:20128`).
- Pedido que cita `memoria/missoes/` ⇒ ABORTA local, exit 1, nada na rede.
- Combo `conselho` esgotada ⇒ ABORTA, exit != 0 (não cai pro local automático).
- Resposta crua é guardada no mesmo formato/local de antes; tokens e custo normalizados.
- `git diff --stat main..redesign -- scripts/conselho_remoto.py` mostra a mudança
  (esperado — merge só na Fase 8).
- `main` intocado: `git rev-parse main` inalterado.

## Verificação independente

- **Quem:** fallback afinado ou Humano.
- **O quê:** que nenhuma das garantias do `conselho_remoto.py` foi perdida na reescrita
  (privado, teto, uma chamada, sem encadear, não escreve canon, aborta ao invés de cair
  pro local), e que o script não guarda mais segredo.
- **Como:** `diff` das duas versões (`git show main:scripts/conselho_remoto.py` vs a do
  branch) lido inteiro; rodar os passos 3–5 de novo num clone.
- **Resultado:** anotar no LOG.

## Rollback

Não destrutivo (a versão de `main` é a fonte):
```fish
cd $HOME/agata
git checkout main -- scripts/conselho_remoto.py    # traz a versão canônica de volta pro branch
git checkout -- redesign/router
# remover a combo `conselho` pelo dashboard do OmniRoute
```

## Registro

- `STATUS.md`: P1-04 → "Feito"; **Fase 1 fechada** (todos os itens do aceite). Nota: o
  merge de `scripts/conselho_remoto.py` para `main` é da Fase 8.
- `LOG.md`: o antes/depois do script (resumo), os resultados dos 3 testes, o resultado da
  verificação independente, `HEAD` no fim.
