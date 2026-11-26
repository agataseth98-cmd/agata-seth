---
name: agata-arranque
description: >-
  Arranque universal do Agata para qualquer modelo (Claude Code, Codex, OpenCode ou outro). Use ao começar uma sessão
  neste repositório: cabeçalho da Regra 1, memória do Conselho, mapa do Humano, índice de skills, fluxo P-8 e problemas recorrentes.
---

# Arranque Agata

Esta skill é a mesma para todo modelo. O hook de início de sessão (SessionStart) a lê quando o Humano aplica o gerador (`scripts/ferramentas/instalar_hook_arranque.py --aplicar`). Sem o hook, leia-a à mão. Quem a instala é `scripts/ferramentas/sincronizar.py`, a partir de `config/ferramentas/`.

## 1. Cabeçalho (Regra 1, toda resposta)
- Abra a resposta com `agata · <modelo> · t=<n> (contador mecânico) · <hora + selo>`. A hora vem de `date`, medida agora, nunca copiada da resposta anterior.
- Subagente usa `t=<n>.sub`. O `t=` vem do contador: `python3 scripts/turno.py proximo --sessao <id> --modelo <modelo>`.
- Formato e voz: `PROTOCOLOS.md` (seção "Carregar e formatos").

## 2. Memória do Conselho
- Ao começar: `python3 redesign/router/cache_conselho.py ler --n 20`.
- Ao fechar trabalho relevante: `python3 redesign/router/cache_conselho.py anotar --autor "<modelo real>" --tipo fato "<texto>"`. Tipos: fato, decisao, pendencia, nota. Segredo é recusado.
- Antes de entregar afirmação verificável: `python3 redesign/router/auditoria_turno.py --verificar --cliente <nome>`.
- Fala: só a voz `pt_BR-agata-last`, pelo `scripts/agata_falar.py`. Nenhum modelo usa outra voz.

## 3. Mapa do Humano (obrigatório)
- Leia `.agents/skills/agata-mapear-humano/SKILL.md` ao começar. Decisão ou correção do Humano vai ao cache com a fonte.

## 4. Índice de skills
- Lista e escolha: `.agents/skills/INDICE.md`. Comece por `.agents/skills/agata-fluxo/SKILL.md`.

## 5. Fluxo P-8 em dez linhas
1. Trabalho em worktree `.claude/worktrees/<nome>`, a partir de `origin/main`. Nunca no checkout principal.
2. Medir o estado antes: `bash scripts/estado_para_eco.sh`.
3. Mudança em arquivo protegido: proposta com `.diff` e registro em `propostas/`. Código entra só dentro do `.diff`.
4. Antes de propor: `bash scripts/ci_sdd_local.sh`. Só siga com "CI LOCAL: TUDO OK".
5. Quem assina é o Humano, com `scripts/aprovar.sh`. O modelo não roda `aprovar.sh`.
6. Nada de `git push`, PR ou serviço externo sem aviso prévio e um "sim" para aquela ação.
7. Não use `rm`. Para tirar algo do caminho, use `mv`. Remover só com ordem do Humano, pelo nome.
8. Nada de sudo, de segredo nem de leitura de `.env`.
9. Afirmação com número leva o rótulo: medido, inferido ou não medido.
10. Detalhe e comandos: `.agents/skills/agata-aplicar-proposta/SKILL.md`.

## 6. Problemas recorrentes (de `agata-fluxo`, seção 1)
- Cabeçalho sem hora medida, ou com hora copiada.
- Narrar o processo ("vou verificar..."). O modo conciso é o padrão: resultado primeiro; processo só para constatar erro, em uma linha.
- Ação externa sem aviso: push, PR, Drive, Discord, Gmail ou reinício de serviço compartilhado.
- Mexer em pasta de outro modelo ou pessoa sem conferir o dono.
- Leitura declarada de forma vaga. Diga quais linhas leu.
- Citação inventada: não repita o literal. Troque por `[citação inventada, expurgada em DATA por ordem do Humano]`.
- Sudo, `aprovar.sh` ou segredo.
- Afirmar sem medir.

## 7. Ferramentas comuns
- Ver o que está instalado em cada CLI: `python3 scripts/ferramentas/listar.py`.
- Adicionar uma ferramenta: `python3 scripts/ferramentas/instalar.py <mcp|skill|agente> <nome> --params ...`. Pede "sim" do Humano.
- Não edite à mão `~/.claude/settings.json`, `~/.codex/hooks.json` nem os arquivos nativos das CLIs.

Regras completas: `AGENTS.md`.
