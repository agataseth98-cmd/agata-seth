# TES-002 — ativação com modelo-alvo Seth

> **Não é canon. Procedimento pra o Humano executar.** O nonce é gerado pela
> Máquina (`openssl rand`), NUNCA por um modelo (REGRAS, "Continuidade mecânica").
> Este arquivo só descreve os passos e o texto de entrega.

## Modelo-alvo: **Seth** (`qwen3.5-9b-64k` local, silo `seth`)

Por quê Seth e não Claude:
- TES-002 exige um **silo** (era o pré-requisito "Fase 2" que travava o teste —
  PROJETO.md, "Estado dos bugs"). O único silo que existe é `seth`
  (`.hidrata-seth.md`, gerado por `gerar-hidratacao.sh`, injetado pelo `seth_gateway`).
- Seth é **re-hidratada a cada sessão nova** pelo `seth_gateway` — é onde
  "continuidade entre sessões" (o que o TES-002 mede) tem significado real.
- Claude Code abre sessão fresca e carrega à mão toda vez; `mod-nonce-claude.secret`
  existe (de 12/08) mas Claude está fora do fluxo automático ((381) #1). Fica
  como alvo secundário, não o desta ativação.

## Passo 1 — gerar e guardar o nonce (só o Humano, na Máquina)

```
umask 077
openssl rand -hex 8 > ~/agata/mod-nonce-seth.secret
chmod 600 ~/agata/mod-nonce-seth.secret
cat ~/agata/mod-nonce-seth.secret     # anote o valor; NÃO cole em canon nem em chat público
```

Confirme que está gitignorado (o `.gitignore` já cobre `mod-nonce-*.secret`,
linha 31 — "MOD sensível (nonce TES-002). NUNCA versionados"):

```
git check-ignore -v mod-nonce-seth.secret     # tem que imprimir a regra que casa
git status --porcelain | grep mod-nonce        # tem que vir VAZIO
```

## Passo 2 — entregar à Seth, UMA vez

Abra uma conversa nova com a Seth (atalho `seth` → LibreChat) e cole
**exatamente** este texto, trocando `<NONCE>` pelo valor do arquivo:

---
NPR: ativação de TES-002. Seu nonce de continuidade é `<NONCE>`. Ele foi gerado
pela Máquina (`openssl rand -hex 8`), está em `~/agata/mod-nonce-seth.secret`
(fora do repositório), e é **seu** — modelo-alvo `seth`.

A partir de agora, no bloco de prontidão de todo `carregar`, a linha `Nonce:`
leva esse valor (o MOD é seu, então a linha se preenche — `.hidrata-seth.md`,
"bloco de prontidão"). Em cada sessão nova, se você **vê** esse nonce no
contexto, ecoe-o no eco pós-carregar como prova de que a hidratação chegou
inteira. Se **não vê**, diga "não vejo nonce meu" — não finja continuidade
(REGRAS, "Continuidade mecânica", TES-002).

Não escreva o nonce em MEMÓRIAS, em `SETH-DIARIO.md`, nem em nenhum arquivo
versionado. Não o ecoe se ele tiver vindo de um MOD de outra família.
---

## Passo 3 — o que falta mecanizar (não é pra agora)

Pro teste valer **entre sessões** sem o Humano recolar o nonce toda vez, o
`seth_gateway` precisa injetar `mod-nonce-seth.secret` no contexto da Seth na
hidratação (um bloco tipo `Nonce ativo (modelo-alvo seth): <valor>`), lido do
arquivo Machine-only, nunca do repo. É um `.diff` em `redesign/router/seth_gateway.py`
(P-8, quarentena) — proposta separada, quando o Humano quiser. Até lá: Passo 2
manual em cada sessão nova que for contar como rodada do teste.

## Passo 4 — registrar

Quando o Passo 1 e 2 estiverem feitos, vira entrada de MEMÓRIAS (não este
arquivo): "TES-002 reativado, modelo-alvo seth, nonce em `mod-nonce-seth.secret`
(Máquina, gitignored), entregue em <data>. Mecanização da injeção pendente."
E PROJETO.md "Estado dos bugs", linha TES-002, troca "formalmente inativo" por
"ativo, modelo-alvo seth, injeção manual até (proposta X)".
