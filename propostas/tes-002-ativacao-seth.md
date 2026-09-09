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

## Passo 1 — gerar e guardar o nonce — **FEITO 09/09/2026 (MEMÓRIAS (409))**

`~/agata/mod-nonce-seth.secret` criado pela Máquina (`openssl rand -hex 8`, via
o Bash do executor — é a Máquina gerando, não um modelo escolhendo o valor).
Perm 600, gitignorado (`.gitignore` linha 9, `*.secret`), 16 hex + newline. O
valor NÃO foi impresso no chat de propósito — o executor não o tem em contexto.

Se precisar recriar (ex.: o arquivo se perdeu):
```
umask 077; openssl rand -hex 8 > ~/agata/mod-nonce-seth.secret
chmod 600 ~/agata/mod-nonce-seth.secret
git check-ignore -v mod-nonce-seth.secret     # tem que casar *.secret
```

Pra entregar (Passo 2), você lê o valor:
```
cat ~/agata/mod-nonce-seth.secret     # NÃO cole em canon nem em chat público
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

## Passo 3 — mecanizar a entrega? NÃO (o protocolo proíbe)

A ideia natural — o `seth_gateway` ler `mod-nonce-seth.secret` e injetar o nonce
na hidratação da Seth toda sessão — **bate de frente com o protocolo**:
PROJETO.md e `.hidrata-seth.md` dizem o nonce é "**nunca em hidratação** —
entregue à mão pelo Humano". O motivo: o eco do nonce prova que o conteúdo
ENTREGUE PELO HUMANO sobreviveu à hidratação; se o nonce vier pelo cano
automático, o teste passa a medir o cano, não a continuidade, e um
`seth_gateway` com bug poderia forjar o eco.

Então: **entrega manual por sessão** (Passo 2), por desenho. Mecanizar exigiria
mudar o protocolo em REGRAS.md ("Continuidade mecânica") — Mudança estrutural,
2ª opinião ou risco por escrito — e não está pedido.

## Passo 4 — registrar

Quando o Passo 1 e 2 estiverem feitos, vira entrada de MEMÓRIAS (não este
arquivo): "TES-002 reativado, modelo-alvo seth, nonce em `mod-nonce-seth.secret`
(Máquina, gitignored), entregue em <data>. Mecanização da injeção pendente."
E PROJETO.md "Estado dos bugs", linha TES-002, troca "formalmente inativo" por
"ativo, modelo-alvo seth, injeção manual até (proposta X)".
