# conselho_via_omniroute.md — desenho da P1-04

Como `scripts/conselho_remoto.py` passa a falar pelo OmniRoute em vez de fazer `urllib`
direto a z.ai / Google. **A política não muda — só a camada de rede.**

> **APLICADO 2026-09-02 (branch): código feito, plumbing testado.** −246/+70 linhas.
> `enviar_omniroute()` faz UMA POST em `http://127.0.0.1:20127/v1/chat/completions` (o
> proxy de sanitização — o pedido do Conselho passa a ser scrub-ado antes de sair) na
> combo `conselho`. O script não lê mais chave. Testes T1/T2/T3 + abort-em-erro passaram
> (ver `redesign/tasks/P1-04-*.md`). Falta: combo `conselho` com glm→gemini reais (chaves
> do Humano) e um pedido de parecer real. Merge p/ `main`: Fase 8.

> Toca um arquivo que existe em `main`. A edição é na cópia do branch `redesign`; o merge
> para `main` é só na **Fase 8**, pela Cadeia de auditoria. `git diff main..redesign --
> scripts/conselho_remoto.py` passa a ter conteúdo — esperado, não reverter.

## O que o script é (não muda)

UMA tarefa: mandar um pedido de parecer já escrito pelo Humano a UM modelo remoto, guardar
a resposta crua. Não interpreta, não resume, não julga, não encadeia, não escreve canon,
não decide. (`MEMÓRIAS (206)/(207)`, REGRAS "Segunda opinião", PROJETO "Conselho Remoto".)

## Garantias que TÊM que sobreviver à mudança

| Garantia | Hoje | Depois |
|---|---|---|
| Pedido some se cita `memoria/missoes/` | `checar_conteudo_privado()` | **igual** — roda antes de qualquer envio |
| Teto de tamanho | `TETO_CHARS_PEDIDO` | **igual** |
| Uma chamada externa por invocação, nunca as duas de propósito, nunca encadeia | laço ausente + comentário | **igual** — uma chamada a `enviar_omniroute()` |
| Os dois externos falharam ⇒ ABORTA (cair pro local é decisão do Humano, `(276)`) | `return 1` com a mensagem | **igual** — combo `conselho` esgotada ⇒ `enviar_omniroute` erra ⇒ ABORTA |
| Não escreve MEMÓRIAS/PROJETO/REGRAS | por desenho | **igual** |
| Guarda a resposta crua; normaliza tokens/custo | `_normalizar()` | **igual** — o OmniRoute devolve shape OpenAI-compat, que `_normalizar` já cobre |
| Segredo não vaza no pedido | (hoje não há scrub aqui) | **melhora** — a chamada vai pelo OmniRoute, que tem a sanitização da P1-02 |

## O que muda

| Remove | Por quê |
|---|---|
| `enviar_glm()`, `enviar_gemini()` | viram uma função só, `enviar_omniroute()` |
| `carregar_chave("ZHIPU_API_KEY")`, `carregar_chave("GOOGLE_API_KEY")` | o script não lê mais chave nenhuma — o OmniRoute tem as chaves |
| `ENDPOINT`, `GEMINI_ENDPOINT`, `GEMINI_MODELO` | endpoint único = `127.0.0.1:20128` |
| `checar_backoff()`, `_backoff_log()`, `registrar_falha_429()`, `registrar_chamada_sem_429()` | o circuit breaker do OmniRoute cuida disso; o script só repassa o erro |
| contadores Gemini (`_gemini_contador_*`, `GEMINI_AVISO_LIMIAR`) | idem — o painel do OmniRoute é a observabilidade |
| a lógica de fallback GLM→Gemini dentro do `main()` | vira a combo `conselho` = [glm-4.7-flash → gemini-2.5-flash] no OmniRoute |

## Código novo (esboço)

```python
OMNIROUTE = "http://127.0.0.1:20128/v1/chat/completions"
COMBO = "conselho"          # combo definida no OmniRoute: glm-4.7-flash -> gemini-2.5-flash

def enviar_omniroute(pedido_texto: str) -> dict:
    corpo = json.dumps({
        "model": COMBO,
        "messages": [{"role": "user", "content": pedido_texto}],
    }).encode("utf-8")
    req = urllib.request.Request(
        OMNIROUTE, data=corpo, method="POST",
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read())
```

`main()` fica:

```
checar_conteudo_privado(pedido)  -> se achado: ABORTA, exit 1, nada enviado
len(pedido) > TETO_CHARS_PEDIDO  -> ABORTA, exit 1
resposta = enviar_omniroute(pedido)         # UMA chamada
  exceção / erro do gateway  -> ABORTA com a mensagem de sempre
                                ("cair pro modelo local é decisão do Humano, ver (276)")
conteudo, te, ts, tt = _normalizar("openai", resposta)   # shape choices[0].message.content + usage
grava a resposta crua no mesmo local/formato de hoje
```

`_normalizar` já tem o ramo openai-compatível (`choices[0].message.content`, `usage` com
`prompt_tokens`/`completion_tokens`/`total_tokens`) — que é exatamente o que o OmniRoute
devolve. Conferir na execução; se o OmniRoute anexar campo de custo próprio, `_normalizar`
pode passar a ler ele em vez de recalcular.

## Combo `conselho` no OmniRoute

- provedores: z.ai (`ZHIPU_API_KEY`) e Google (`GOOGLE_API_KEY`) — chaves movidas/replicadas
  do `~/.hermes/.env` pelo Humano para o store do OmniRoute, sem chat.
- ordem: `glm-4.7-flash` → `gemini-2.5-flash` (a mesma de hoje).
- **sem** fallback para modelo local nesta combo — esgotou, erra, e o script ABORTA.

## Testes (P1-04 passos 3–5)

1. Pedido real → resposta crua guardada como antes, `exit 0`, aparece no log do OmniRoute
   na combo `conselho`.
2. Pedido citando `memoria/missoes/` → ABORTA local, `exit 1`, nada na rede (`tcpdump`).
3. Combo `conselho` desabilitada → ABORTA, `exit != 0`, mensagem de que cair pro local é
   decisão do Humano.

## Rollback

`git checkout main -- scripts/conselho_remoto.py` traz a versão canônica de volta ao
branch; remover a combo `conselho` no dashboard.
