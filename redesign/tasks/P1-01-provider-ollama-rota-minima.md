# P1-01 — provider Ollama local + uma rota mínima que responde

**Objetivo:** um pedido chega ao OmniRoute e volta com resposta do Ollama local — o
primeiro item do aceite da Fase 1 ("um pedido roteia"), sem nuvem ainda.

**Pré-requisitos:** P1-00 FEITO. Ollama de produção rodando (não tocar a config dele —
só apontar o OmniRoute para o endpoint que ele já expõe, `http://127.0.0.1:11434`).

**Arquivos que a tarefa toca:**
- config de provedores do OmniRoute (via dashboard `/dashboard/providers` ou o arquivo
  que ela persiste em `~/.config/omniroute/`)
- `redesign/tasks/P1-01-*.md` (marca FEITO)

---

## Passos

### 1. Registrar o Ollama como provedor

Pelo dashboard em `http://127.0.0.1:20128/dashboard/providers` (ou o comando equivalente —
confirmar na doc):
- tipo: `ollama` (ou "OpenAI-compatible" apontando para `http://127.0.0.1:11434/v1`)
- base URL: `http://127.0.0.1:11434`
- sem chave (local)
- habilitar 1 modelo que já existe no `ollama list` (ex.: o denso 9B — confirmar o nome
  exato com `ollama list`)

Colar de volta: a lista de provedores do OmniRoute depois (`curl -s http://127.0.0.1:20128/v1/models`).
Sucesso: o modelo do Ollama aparece em `/v1/models`.

### 2. Rota mínima — um pedido, uma resposta

```fish
curl -s http://127.0.0.1:20128/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"model":"<modelo-ollama>","messages":[{"role":"user","content":"responda só: ok"}]}' \
  | tee /tmp/p1_01_resp.json
echo "exit: $status"
```

Colar de volta: o JSON da resposta.
Sucesso: `choices[0].message.content` não vazio; `usage` presente (para o custo depois).

### 3. Conferir que o OmniRoute logou o pedido (custo/observabilidade nativa)

```fish
# confirmar o caminho do log/painel na doc; provável: dashboard "Requests" ou
# ~/.config/omniroute/logs/  ou  `omniroute logs`
omniroute logs --tail 5      # ou o equivalente
```

Colar de volta: as linhas do log referentes ao pedido do passo 2.
Sucesso: o pedido aparece com modelo, tokens e latência.

---

## Aceite

- `curl .../v1/chat/completions` com um `model` do Ollama devolve `choices[0].message.content` não vazio (exit 0, HTTP 200).
- O pedido aparece no log/painel nativo do OmniRoute com contagem de tokens.
- Ollama de produção intocado: `systemctl status ollama` (ou o gerenciador dele) sem mudança; `ollama list` igual ao de antes.

## Verificação independente

- **Quem:** fallback afinado ou Humano.
- **O quê:** que a resposta veio mesmo do Ollama local (não de um provedor nuvem que
  alguém configurou sem querer) e que nada saiu da máquina.
- **Como:** repetir o `curl` do passo 2 com o Ollama parado (`systemctl stop ollama` num
  scratch, ou desabilitar o provedor) → o OmniRoute tem que falhar/retornar erro, não
  "responder" de outro lugar. Religar depois. Conferir `ss -tnp` durante o pedido: só
  conexão a `127.0.0.1:11434`.
- **Resultado:** anotar no LOG.

## Rollback

Não destrutivo: remover o provedor Ollama pelo dashboard, ou
`git`-nada (config fora do repo). Reverter a config:
```fish
# se a config for arquivo:
cp ~/.config/omniroute/<config>.bak ~/.config/omniroute/<config>   # se houver backup
# senão, remover o provedor pelo dashboard
```

## Registro

- `STATUS.md`: P1-01 → "Feito".
- `LOG.md`: o JSON de resposta (resumido), a linha de log do OmniRoute, o resultado da
  verificação independente, `HEAD` no fim.
