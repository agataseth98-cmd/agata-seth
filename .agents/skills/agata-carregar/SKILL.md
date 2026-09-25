---
name: agata-carregar
description: Abrir uma sessão no sistema Agata (comando "carregar", "carregar agata", início de sessão, ou quando o bloco de estado não chegou injetado). Mede sync/hashes/HEAD/hora na Máquina e monta o bloco de prontidão de 3 linhas de REGRAS.md.
---

# Carregar o Agata (na Máquina, com shell)

Por quê: sessão que não sincroniza e mede trabalha sobre cópia velha sem saber (MEMÓRIAS (248)-(252)).
O bloco de estado que o `seth_gateway` injeta já traz quase tudo; se ele veio, use-o. Se não veio, meça.

1. `bash ~/agata/scripts/estado_para_eco.sh` — read-only. Dá HEAD, topo de MEMÓRIAS, `sync:`, idade da
   hidratação, propostas abertas, hora da Máquina e `HASH-ESTADO`. É a fonte dos campos; não estime nenhum.
2. Se `sync:` não for `PASS`: `git -C ~/agata fetch -q` e `git -C ~/agata status -sb`. **Nunca** descarte
   mudança local (`checkout --`, `reset`, `restore`, `stash`) pra "consertar" sync — pode ser aplicação
   assinada em andamento. Mostre `git diff --stat` e pergunte ao Humano.
3. Leia a entrada do topo de `MEMÓRIAS.md` (logo abaixo de `<!-- ENTRADAS-NOVAS:AQUI -->`) — número e título.
4. `quebrado:` — itens abertos nas entradas recentes e `propostas/` com `.diff` sem `APROVADO-`.
5. Responda com o bloco de REGRAS.md, "Carregar e formatos" — 3 linhas, nada antes:
   ```
   Agata · modelo: <nome> · sync: <forma> · <dd/mm/aaaa HH:MM -03> (relógio da Máquina)
   Última entrada: (<n>) <título> — <1 linha>
   <quebrado: … | pronto.>
   ```
6. Eco (≤5 linhas) citando o `HASH-ESTADO` e dizendo em 1 linha por que o estado é coerente. O Humano
   confirma antes do trabalho começar.

Depois do carregar, toda resposta começa com a linha de turno:
`Agata · <modelo> · t=<n> (contado no contexto) · <hora medida AGORA com date> (relógio da Máquina)`.
Hora nunca é copiada da resposta anterior.
