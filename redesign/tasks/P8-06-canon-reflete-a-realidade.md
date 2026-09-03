# P8-06 — canon reflete a realidade

**Status:** ⏳ a fazer. Mexe em `REGRAS.md` / `PROJETO.md` / `MEMÓRIAS.md` / `ONDE_ESTAMOS.md`
— **linha vermelha.** Só pela Cadeia de auditoria em camadas + autorização explícita do
Humano por mudança.

**Objetivo:** o canon descreve o sistema que passou a existir (grafo + OmniRoute + iGPU +
liga/desliga + backup verificável), não o Hermes. Uma entrada em `MEMÓRIAS.md` por fase do
redesenho.

**Pré-requisitos:** P8-02..P8-05 verdes.

## Passos
1. **`MEMÓRIAS.md` — uma entrada DIÁRIO por fase (0–8), append-only, no topo** (ordem
   nova, abaixo do marcador `ENTRADAS-NOVAS`). Cada uma: o que a fase entregou, o aceite
   cumprido, o commit do branch, o `.diff`/`APROVADO-` quando houve. Numeração: conferir o
   topo do remoto antes (a numeração é única a partir de (49)); provável (310)–(318).
   **Correção nunca é edição** — se algo do branch estiver errado, entrada nova apontando.
2. **`REGRAS.md`** — o que mudou de regra: gates suspensos voltam a valer (fim do estado de
   exceção); a Cadeia de auditoria em camadas para canon segue; P-10/P-11/P-12 no
   perímetro; hidratação por consulta vs. injeção. Cada mudança pela **Cadeia A→B→C**
   (Modelo A propõe, B audita, C verifica na Máquina) + **2ª opinião de outro modelo** +
   autorização do Humano. Registrar o que cada camada acertou (Cadeia, item 5).
3. **`PROJETO.md`** — "Estado dos bugs e dos testes", "Serviços", "Memória e hidratação",
   "Fronteira de recusas" atualizados para o sistema novo. `.hermes.md` → papel novo.
4. **`ONDE_ESTAMOS.md`** — reescrito: o mapa do sistema pós-redesenho (portas, `agata.target`,
   `agata-jogo`, OmniRoute, iGPU, restic/P-12, quem dirige o loop).
5. Cada arquivo canônico via o processo normal do `perimetro.sh` (P-7 citação, P-8 se
   `scripts/`, P-10 vault, etc.) — **sem `--no-verify`** (o estado de exceção acaba aqui).

## Aceite
- `MEMÓRIAS.md`: entradas (0–8) presentes, append-only (o `git diff` só acrescenta abaixo
  do marcador), cada uma com aceite + commit citados.
- `REGRAS.md`/`PROJETO.md`/`ONDE_ESTAMOS.md` descrevem o sistema real; cada mudança tem a
  cadeia A/B/C + 2ª opinião registrada.
- `perimetro.sh` verde com o canon novo staged (P-7, P-8, P-10 incluídos).

## Verificação independente
É o núcleo da tarefa: Cadeia de auditoria em camadas (multi-modelo), REGRAS "O que cada
camada deve entregar" (6 itens). Camada C verifica cada alegação de B contra REGRAS/git/hash.
Confirmação pós-push do hash em P8-07.

## Rollback
Enquanto não empurrado: `git restore --staged` + `git checkout --` dos canônicos.
`MEMÓRIAS.md` **nunca** se reescreve — se uma entrada saiu errada, corrige-se com entrada
nova, não revert.

## Registro
`STATUS.md`: P8-06 → Feito; canon == realidade.
`LOG.md`: a cadeia de cada mudança de canon (achados de B, verificação de C, o que cada um
acertou), os números das entradas de MEMÓRIAS.
