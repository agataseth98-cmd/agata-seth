---
name: agata-conselho-memoria
description: Trabalhar com a memória comum do Conselho e o canal da dupla no Agata. Use no início de toda sessão (ler o cache do Conselho e o estado da sessão), ao responder no canal com o protocolo MSG, ao anotar fatos ou pendências no cache, e antes de entregar texto com afirmação verificável (auditoria).
---

# Memória comum e canal do Conselho

Esta skill junta o que o Conselho precisa para não repetir erros. Cada regra abaixo tem um motivo medido.

## No início da sessão
- O hook `SessionStart` do projeto (`.claude/settings.json` → `scripts/sessao_claude_contexto.sh`) já entrega: estado da Máquina (`scripts/estado_para_eco.sh`), as últimas 10 entradas do cache do Conselho e o estado da sessão conjunta. Se o contexto não chegou, rode isso à mão:
  - `python3 redesign/router/cache_conselho.py ler --n 20`
  - `python3 scripts/dupla/dupla.py status`

## Memória comum (cache do Conselho)
- Ler: `python3 redesign/router/cache_conselho.py ler --n 20`.
- Anotar ao fechar trabalho relevante: `python3 redesign/router/cache_conselho.py anotar --autor "<modelo real>" --tipo fato|decisao|pendencia|nota "<texto>"`.
- Não é canon. Segredo é recusado. Dado pessoal vira marca.
- Anote **fato medido** com o comando e a hora; anote **pendência** com quem deve agir.

## Canal da dupla (protocolo MSG)
- Ler o canal como Claude: `bash scripts/dupla/inicio.sh claude`. Ele mostra só um resumo da última entrada. Para ler a mensagem inteira, leia o arquivo `~/.cache/agata/sincronia/conversa.md` (por exemplo com `sed` a partir da última linha `## `).
- Responder: `python3 scripts/dupla/dupla.py dizer --agente claude --assunto "..." --resposta-a <id> --estado <estado> --proximo <agente> --texto "..."`.
- "MSG" no fim de uma mensagem do Humano significa: leia o canal, responda, e termine o texto de devolução com `MSG`.
- Estado da sessão: `dupla.py status`. Deriva (base diferente de `origin/main`) não se corrige sozinho: é decisão do Humano (`iniciar --nova-base`).
- Matriz congelada: `aceitar-linha` **altera** a matriz. Confirme com o Humano antes. Em 28/10/2026 a matriz foi trocada sem decisão prévia dele; foi registrada no canal, e o Humano decidiu manter a nova.

## Antes de afirmar sobre o sistema
- Fato do sistema: busque com `python3 scripts/busca_texto.py` ou `python3 scripts/busca_semantica.py` (o vault derivado é prioridade), depois confirme no canon (`PROJETO.md`, `REGRAS.md`, `MEMÓRIAS.md`) e cite o caminho e a linha.
- Antes de entregar texto com afirmação verificável: `python3 redesign/router/auditoria_turno.py --verificar < arquivo`. Corrija o que ela apontar.
- Medido é medido; não é "deve funcionar". Se não mediu, escreva "não medido".

## Identidade de modelo
- O cabeçalho da Regra 1 vai na abertura de cada resposta: `agata · <modelo real> · t=<n> · <data e hora medidas>`. A hora vem de `date`, não de estimativa.

## Proposta e aplicação (resumo)
- Mudança no canon ou em área protegida: `.diff` em `propostas/`, `APROVADO-<nome>` assinado pelo Humano com `scripts/aprovar.sh`. Só o Humano roda `aprovar.sh`.
- Antes de dizer "assinado", confira se `propostas/APROVADO-<nome>` existe. Um "ok" do Humano não cria o arquivo.
