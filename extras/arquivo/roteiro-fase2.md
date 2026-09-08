# Roteiro — Fase 2 (silos por modelo · eco pós-carregar mecanizado · TES-002 restaurado)

**Rascunho versionável. SEM `APROVADO-`. NÃO é para execução imediata.**
Este documento existe para o Humano **autorizar sessões separadas**, uma por camada.
Não autoriza nenhuma mudança por si.

- Base: canon HEAD `9190c58` (MEMÓRIAS (303)), 31/08/2026.
- Ordem do Humano, 31/08/2026: "monte o roteiro… a execução exige as 3 camadas
  independentes (A/B/C) — nenhum executor sozinho pode fazer."

---

## Regra que governa este roteiro inteiro

Fase 2 muda **o que chega a cada modelo** e toca `.githooks/*` — é "Mudança
estrutural" (REGRAS) e destino é o canon. Por isso, para **cada** um dos três
blocos abaixo, a execução passa pela **Cadeia de auditoria em camadas**
(REGRAS.md, seção própria), sem pular salto nenhum:

```
Camada A  — um modelo propõe a mudança e a testa em clone descartável
Camada B  — outro modelo, SESSÃO DE HIDRATAÇÃO SEPARADA, audita A e levanta achados
Camada C  — um terceiro, na Máquina, verifica as alegações de A e de B contra
            REGRAS/git/hash/grep — não contra o texto de A ou de B
Humano    — recebe os pareceres de B e de C, autoriza ou não
Máquina   — quem tem shell escreve no canon, comita, empurra
Confirmação — um modelo com acesso ao remoto confere o hash pós-push
```

- **Independência é o ponto.** A, B e C são hidratações distintas, sem
  compartilhar histórico de turno nem contexto de resposta. Um executor fazendo
  dois papéis anula a camada.
- **Cada camada entrega os 6 itens** da tabela "O que cada camada deve entregar"
  (REGRAS.md): verificação na Máquina antes de afirmar · citação exata, nunca
  paráfrase entre aspas · hedge sobre o que a camada seguinte não pode verificar ·
  autorização explícita do Humano antes de tocar canônico · registro do que cada
  ator **acertou**, não só do que errou · confirmação pós-push por acesso
  independente ao remoto.
- **Assinatura é uma só** por entrada de MEMÓRIAS — de quem escreve o registro.
  As camadas se identificam no corpo do achado ("proposto por A, auditado por B,
  verificado por C na Máquina"), nunca em assinaturas próprias.
- **Regra 8** (verificação tripla) vale onde a escolha **não tem oráculo de
  Máquina** — ver a lista "Decisões de desenho sem oráculo" no fim. Três passadas
  independentes no modelo local, hidratações distintas; divergência = `lacuna`
  que sobe pro Humano.

---

## O que já está verificado na Máquina (31/08/2026) — insumo, não decisão

- `.githooks/gerar-hermes-md.sh` gera **um** `.hermes.md`: REGRAS.md + PROJETO.md
  + `janela_memorias()` (orçamento 25.000 chars, por entrada inteira) +
  `INDICE_MEMORIAS.md`. A função `janela_memorias()` **já reconhece** blocos
  `^(n) MOD` — mas **não filtra por `modelo-alvo`**. Tudo entra no arquivo único.
  Comentário no próprio script (linhas ~24-25): "sem silo por modelo — Fase 2
  ainda não construída; calibração por modelo depende dessa fase existir".
- O Hermes auto-injeta **exatamente um** de `.hermes.md / AGENTS.md / CLAUDE.md
  / .cursorrules`. Silo por modelo precisa de (a) `.hermes-<modelo>.md` por alvo
  **e** (b) um mecanismo que faça o Hermes injetar o arquivo certo por sessão —
  isto é design aberto (ver Regra 8 no fim).
- Blocos MOD no canon hoje: **um só** — `(51) MOD claude — 26/07/2026`,
  `modelo-alvo: claude` (string não verificada), nenhum trecho liberado.
- Infra do nonce sucessor de TES-002 **já existe**: `~/agata/mod-nonce-claude.secret`
  (casado com `*.secret` no `.gitignore`, `git check-ignore` confirma), gerado
  `openssl rand -hex 3`, valor nunca em canon, entrega manual do Humano ao
  modelo-alvo. `e1d1a` aposentado em MEMÓRIAS (90).
- Enquanto Fase 2 não existir: nenhum MOD com conteúdo sensível entra em MEMÓRIAS
  de produção (REGRAS.md, "O Conselho", nota final).

---

## Passo 0.4 — Dimensionamento (read-only; UMA sessão de Máquina pode fazer)

Único passo que **não** precisa da cadeia A/B/C: é leitura, não muda nada, não é
P-8. Mas o resultado é **insumo da Camada A**, não uma decisão. Entregável: um
dossiê em `propostas/` (rascunho) com:

1. `.githooks/gerar-hermes-md.sh` lido inteiro; onde exatamente entraria o filtro
   por `modelo-alvo` em `janela_memorias()` e no `gerar_indice`.
2. Lista dos `modelo-alvo` reais (hoje: `claude`) + os alvos previsíveis de
   Fase 3 (Seth/qwen local, GLM, Gemini fallback) — quantos arquivos
   `.hermes-<modelo>.md` o mecanismo geraria.
3. Como o Hermes escolhe qual arquivo injetar: investigar config do
   `hermes-agent` (fora do repo), sem alterar nada — só documentar as opções
   (arquivo por diretório de sessão? symlink? variável?).
4. Tamanho estimado de cada `.hermes-<modelo>.md` e se o orçamento de janela
   (25.000) precisa variar por modelo.
5. A "lição da Fase 2": mudança no que chega ao modelo pode regredir
   chamada de ferramenta — desenhar o reteste de tool-calling a rodar depois
   de 3.1.

---

## Bloco 3.1 — Silos por modelo (a espinha)

- **O que muda:** `.githooks/gerar-hermes-md.sh` passa a emitir
  `.hermes-<modelo>.md` por `modelo-alvo`, filtrando blocos MOD alheios; +
  o mecanismo de seleção do Passo 0.4(3).
- **Toca:** `.githooks/*` → **P-8** (par `.diff` + `APROVADO-<nome>`). Muda o que
  cada modelo recebe → **cadeia de auditoria em camadas obrigatória**.
- **Destrava:** 3.3 (TES-002) e o uso de blocos MOD sensíveis em produção.
- **Depois:** reteste de tool-calling (lição da Fase 2).
- **Cadeia:** A propõe + testa em clone → B audita em sessão separada → C
  verifica na Máquina (o filtro realmente exclui só o MOD alheio? `.hermes.md`
  dos outros modelos não perde nada do canon comum?) → Humano → aplica+push →
  confirma hash.

## Bloco 3.2 — Eco pós-carregar mecanizado

- **O que muda:** o protocolo do eco (≤5 linhas resumindo o estado herdado, o
  Humano confirma antes do trabalho) hoje é só texto em REGRAS.md. Mecanizar =
  script/checagem que produz ou valida esse resumo.
- **Toca:** provável `scripts/*` → **P-8**. Pequeno. Pode entrar junto ou logo
  depois de 3.1, na mesma cadeia.
- **Cadeia:** mesma A/B/C. Se andar colado a 3.1, o parecer de B e C cobre os
  dois no mesmo ciclo — mas são dois `.diff` e dois `APROVADO-`.

## Bloco 3.3 — TES-002 restaurado com nonce novo

- **O que muda:** ativar o teste de continuidade com o nonce sucessor já gerado
  (`mod-nonce-claude.secret`). O nonce vive fora do canon, nunca comitado, nunca
  em hidratação; entrega manual do Humano ao modelo-alvo, uma vez.
- **Depende de 3.1 aplicado** (silo real, senão o nonce vaza no arquivo único).
- **Toca canon:** só a reativação registrada em PROJETO.md "Estado dos bugs e
  dos testes" + entrada MEMÓRIAS → **P-8** no PROJETO.md.
- **Cadeia:** A propõe a reativação e o protocolo exato → B audita (o nonce
  não aparece em lugar nenhum versionado? o silo de 3.1 cobre o alvo?) → C
  verifica na Máquina (`git check-ignore`, `git log -S` do valor, grep no
  `.hermes-*.md` gerado) → Humano → registro.

---

## Sequência de sessões que o Humano autoriza (uma autorização por linha)

| # | Sessão | Papel | Pode ser executor local? |
|---|--------|-------|--------------------------|
| S1 | Dimensionamento (Passo 0.4) | leitura, produz dossiê | **sim** — Máquina, read-only |
| S2 | Camada A de 3.1 | propõe + testa em clone | sim (qualquer modelo) |
| S3 | Camada B de 3.1 | audita A, sessão separada | **não pode ser a mesma de S2** |
| S4 | Camada C de 3.1 | verifica A e B na Máquina | **não pode ser S2 nem S3** |
| S5 | Humano decide 3.1 | recebe pareceres B e C | Humano |
| S6 | Aplica 3.1 + push | Máquina | sim |
| S7 | Confirma hash pós-push 3.1 | acesso independente ao remoto | **não pode ser S6** |
| S8–S13 | mesmo padrão para 3.2 (pode encavalgar a cadeia de 3.1) | | |
| S14–S19 | mesmo padrão para 3.3 (só depois de 3.1 aplicado) | | |

Regra 8 dispara dentro de S2 (e S8/S14) sempre que a escolha não tiver oráculo
de Máquina: três passadas independentes no modelo local antes de A apresentar.

---

## Decisões de desenho sem oráculo de Máquina (exigem Regra 8 dentro da Camada A)

1. **Como o Hermes seleciona `.hermes-<modelo>.md` por sessão.** Não há resposta
   verificável só medindo — depende de escolha entre mecanismos.
2. **O que exatamente o filtro exclui:** só `MOD` com `modelo-alvo` diferente?
   `MOD` sem `modelo-alvo`? blocos `CONSELHO` ficam comuns a todos?
3. **Orçamento de janela por modelo:** 25.000 fixo para todos, ou calibrado?
4. **Fallback:** modelo sem `.hermes-<modelo>.md` próprio recebe qual arquivo?

---

## O que NÃO entra neste roteiro

- **TES-001** — teste empírico (N sessões consecutivas independentes, N nem
  definido). Roteiro próprio, ver plano-execucao-backlog BLOCO 0.3. Não é Fase 2.
- **Fase 3+** — GLM membro pleno, discordância sintética, IPFS, curador, DAO.
  Contenção de escopo: só sob ordem explícita item a item.
- **Aceite 2.8 de (302)** — segundo fornecedor de nuvem carregando o prompt v2.
  Tarefa de sessão de nuvem, não do executor local.

---

**Rascunho. Sem `APROVADO-`. Não autoriza nada.** Cada bloco (3.1, 3.2, 3.3)
ainda passa, no momento da execução, pelo **portão das três perguntas** com o
Humano e pela **cadeia de auditoria em camadas** completa antes de virar
`APROVADO-<nome>`.
