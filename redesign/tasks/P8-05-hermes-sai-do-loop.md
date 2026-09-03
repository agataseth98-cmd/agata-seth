# P8-05 — Hermes sai do loop

**Status:** ⏳ a fazer. Toca serviço de produção (Hermes) → **precisa do "vai"** e só
depois de P8-02 (paralelo) e P8-03 (fabricação) darem verde.

**Objetivo:** o caminho novo (grafo + OmniRoute) vira o **único** que dirige o Agata. O
Hermes deixa de estar no loop de governança; fica **só** como serviço de voz / Open WebUI
se esses estiverem em uso, como unidades à parte.

**Pré-requisitos:** P8-02 (decisão "empatou/superou"), P8-03 (fabricação PASS), P8-04.

## Passos
1. **Inventariar o que o Hermes faz hoje** — `hermes-gateway.service` (user), o que chama,
   quem depende (`~/.hermes/`, Open WebUI, voz). Registrar antes de mexer.
2. **Tirar do loop:** o loop de governança passa a ser `redesign/grafo/grafo.py` (via o
   `agata` CLI / `agata.target`). O Hermes **não** é mais chamado para hidratar/rotear/
   trabalhar. Se nada de voz/OWUI usa o Hermes → `systemctl --user disable --now
   hermes-gateway.service` (reversível). Se voz/OWUI usam → manter só esse caminho,
   documentar que o gateway agora serve só isso.
3. **`.hermes.md` de produção** — deixa de ser a hidratação primária (passa a ser consulta
   ao índice / `query_canon`). O arquivo não se apaga; o `post-commit` segue gerando (é
   barato e serve de referência). Registrar a mudança de papel.
4. **Teste de fumaça:** com o Hermes fora do loop, `agata up` → `grafo.py run` de um pedido
   real num clone → 6 nós + portão + commit no clone. Voz/OWUI (se em uso) respondem como
   serviço isolado.

## Aceite
- Loop roda ponta a ponta **sem** o Hermes no caminho.
- Voz / Open WebUI (se em uso) seguem funcionando como serviço à parte; se não em uso,
  `hermes-gateway.service` `disabled`.
- Papel do `.hermes.md` redefinido e registrado.

## Verificação independente
Camada C: `systemctl --user status hermes-gateway` bate com o que o passo 2 decidiu;
`grafo.py` não importa nem chama nada de `~/.hermes/` no caminho do loop (grep); o teste de
fumaça roda de estado limpo.

## Rollback
`systemctl --user enable --now hermes-gateway.service`; reapontar o loop para o Hermes.
Reversível enquanto `main` não mudou (P8-07).

## Registro
`STATUS.md`: P8-05 → Feito; quem dirige o Agata agora (grafo + OmniRoute).
`LOG.md`: inventário do Hermes, o que foi desabilitado/mantido, o teste de fumaça.
