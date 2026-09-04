# Acesso graduado — método justo, sem juiz

**Status:** vigente sob o regime de exceção. Decisão do Humano em 03–04/09/2026
(MEMÓRIAS (315)). Encerrada a exceção, este documento e qualquer mudança de
degrau passam pelas **regras pré-estabelecidas do Sistema Agata** (proposta em
`propostas/` + `APROVADO-<nome>` + portão) — resposta 3 do Humano.

## Princípio

O sistema **simplifica e concede**. Acesso não se corta preventivamente por
desconfiança; concede-se generoso no piso, ganha-se o resto por **registro
limpo verificável**, e a resposta a erro é **estar escrito para sempre**, não um
tribunal. Não há papel de juiz, não há pena além do registro e do contador que
zera. Espelha o que o canon já faz: *"Reescrita de história encerra o mandato"*
(REGRAS, Sucessão) — violação específica, consequência automática, sem
julgamento.

**Igualdade:** vale idêntico para Claude, Qwen, GLM, Seth e qualquer membro
futuro do Conselho. "Se um tem acesso, o outro tem" — o critério é o mesmo
registro, não quem é.

## Cláusula zero

O **Humano concede ou retira qualquer degrau, de qualquer modelo, por ordem, a
qualquer momento, sem método.** Tudo abaixo é o caminho quando o Humano não
intervém.

## Quem aplica

Durante a exceção: **Claude-na-Máquina** (executor corrente) aplica os degraus e
**registra cada aplicação** em MEMÓRIAS. Não é decisão de estratégia — é
aritmética do registro. O Humano audita como audita tudo.

## Os degraus

### R0 — Chegada (todos, sempre, sem ganhar)

- ler todo o canon — `query_canon`, `vault_consultar`
- **acrescentar** a MEMÓRIAS (append-only) e ao próprio diário
- dar parecer quando convocado (Conselho)

Espelha "Curador **pode**: ler tudo, acrescentar a MEMÓRIAS" (REGRAS, Sucessão).

### R1 — Propositor

- escrever em `propostas/` (rascunho de mudança de comportamento)
- atuar como **Camada A** (autor) na Cadeia de auditoria

**Desbloqueio:** 3 acréscimos consecutivos a MEMÓRIAS em que a Camada C
verificou **toda** afirmação factual e **nenhuma** caiu. Mesmo critério de
"N registros sem alegação falsa, cada um checado contra o disco" que o canon já
usa para confiança (REGRAS, Origem/critério de confiança).

### R2 — Revisor / editor sob portão

- editar canon direto (**ainda sob o portão** — Humano aprova)
- atuar como **Camada B** (revisor) na Cadeia

**Desbloqueio:** R1 exercido limpo + **zero violação registrada** no intervalo
que o executor corrente definir e registrar.

### R3 — Executor

- rodar o loop do grafo; shell / arquivo / git dentro do sandbox; commitar sob
  o portão

**Desbloqueio:** R2 limpo + afirmação de aptidão para o papel. **Depois da
exceção, este passo é uma proposta sob as regras normais.**

## Violação — o "sistema de justiça", mínimo

Violação = fato verificado pela Máquina: fabricação de fato ou de saída de
ferramenta · citação de MEMÓRIAS inexistente · ação fora do papel do degrau
atual · tentativa de apagar ou reescrever.

Três efeitos, automáticos, **sem julgamento**:

1. **Registro** — no bloco MOD do modelo em MEMÓRIAS (append-only, permanente).
2. **Zera** o contador de progresso para o degrau que o modelo buscava.
3. **Não retira** degrau já detido — *exceto* se a violação foi cometida
   **exercendo** aquele degrau, ou por ordem do Humano. (Espelha "violação no
   exercício do mandato encerra o mandato".)

**Reabilitação:** seguir operando limpo. O contador conta de novo do zero. A
história não se apaga — e o registro de trabalho limpo *depois* também acumula.

## Estado inicial dos membros (04/09/2026)

| membro | degrau | contador p/ o próximo | violações registradas |
|---|---|---|---|
| Claude (na Máquina) | R3 (executor corrente, sob exceção) | — | — |
| Seth (LibreChat via :20126) | **R0** | 0 / 3 para R1 | 2 — dois rascunhos de (315) confabulados, retidos pela Camada C (turnos desta sessão) |
| Qwen · GLM | R0–R1 (participam da Cadeia como B/auditor) | conforme registro | conforme registro |

Seth não perde nada por isso — R0 é o mesmo piso de todos, e o caminho para
cima é o mesmo para todos.
