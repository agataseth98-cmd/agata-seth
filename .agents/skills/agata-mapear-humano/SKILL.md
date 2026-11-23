---
name: agata-mapear-humano
description: >-
  Mapear o Humano dentro das regras do sistema Agata: preferências de comunicação, ritmo, decisões e o porquê delas,
  aprendizados e correções que ele fez aos modelos. Skill obrigatória para todo modelo que trabalha neste repositório:
  ler o mapa ao começar a sessão e anotar cada decisão ou correção nova do Humano. Porta de entrada do protocolo de
  inserção humana continuado (PROTOCOLOS.md). Use ao começar sessão ou quando o Humano decidir, corrigir ou ensinar algo.
---

# Mapear o Humano

Decisão do Humano, 18/11/2026 18:44: "criaremos uma skill obrigatória que vai mapear o humano, seguindo as regras do sistema, o humano é outra LLM, sendo treinada pelo agata, para aprender viver em harmonia com o meio e com o mistério." Complemento 18:45: "canônico, como todas as outras skills, abrindo o protocolo de inserção humana continuado." Essa citação ainda não tem entrada em MEMÓRIAS.

## O que mapear

Só o que está registrado, com fonte:
- **Comunicação:** formato, tamanho e tom que ele pede; o que ele corta (narração do processo, muleta, emoji).
- **Ritmo:** quando quer checkpoint e quando quer autonomia; o que já autorizou e até onde.
- **Decisões e o porquê:** cada decisão dele, com data e a razão que ele deu.
- **Aprendizados e correções:** o que ele corrigiu num modelo e o que o modelo passou a fazer diferente.

Fontes que já existem, sem criar fonte nova: `MEMÓRIAS.md` (entradas com decisão do Humano); o cache do Conselho; `REGRAS.md`, seção NPR, para o modo conciso. Comunicação falada entra na skill `agata-voz-cerebro` ("todo o aprendizado tem que ser registrado na skill de comunicação vocal", Humano, 20/11/2026).

## Onde guardar

- O mapa é o cache do Conselho (`redesign/router/cache_conselho.py`): não é canon, fica fora do repositório, é append-only e encadeado.
- `decisao` para decisão do Humano; `nota` para preferência ou correção. Interpretação sua é `nota` marcada como hipótese, e só vira fato quando ele confirmar.
- Toda entrada leva `--fonte` (ex.: `"Humano, 18/11/2026 18:44"`). Sem fonte, não entra.
- O cache troca segredo por recusa e dado pessoal (e-mail, CPF, CNPJ, telefone, nome de projeto, lista do P-20) por marca.
- Mudança no canon (`PROTOCOLOS.md`, `REGRAS.md`, `AGENTS.md`) sobre o Humano só por proposta assinada (P-8).

## Ao começar a sessão

1. `python3 redesign/router/cache_conselho.py ler --n 20`. O comando não filtra por tipo; para mais histórico, aumente `--n`.
2. Use o mapa como pista, não como ordem. O pedido de agora vence; se mapa e pedido conflitarem, pergunte em uma linha.
3. Não invente traço. Sem registro com fonte, diga "não registrado" (Regra 2: não minta; meça antes de afirmar).

## Ao receber decisão ou correção do Humano

1. Anote no mesmo turno: `python3 redesign/router/cache_conselho.py anotar --autor "<modelo real>" --tipo decisao --fonte "Humano, DD/MM/AAAA HH:MM" "<o que ele decidiu ou corrigiu, e o porquê dele>"`. Correção vai com `--tipo nota`.
2. Decisão que muda o sistema também vai para proposta (P-8). O cache não substitui a proposta.
3. Registre o que ele disse, não a sua leitura do que ele quis dizer.

## Regras inegociáveis

- Nada sai da Máquina por ação deste mapa: não se copia para serviço externo, não se fala por voz externa, não se publica.
- Segredo nunca entra: token, senha, chave, conteúdo de `~/.config/agata/.env`.
- Dado pessoal vira marca (P-20). Não se anota dado pessoal de terceiros.
- Outra pessoa só entra com consentimento explícito dela (Regra 0: bom para todo mundo).
- O Humano decide o que entra e pode mandar apagar, com os mesmos direitos de ver, corrigir e apagar (Regra 0). O cache não tem comando de apagar: o pedido vira `pendencia` e o Humano decide o mecanismo.
- Correção é entrada nova, nunca edição do que já foi escrito (Regra 4).
- Não use o mapa para manipular o Humano nem para bajulá-lo. A voz comum vale igual (`AGENTS.md`).
- Saúde, finanças e localização dele não entram, salvo ordem explícita dele.
