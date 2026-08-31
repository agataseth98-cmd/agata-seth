# Bloco 3.2 — Eco pós-carregar mecanizado — Camada A

**Par (v2):** `bloco-3.2-eco-mecanizado.diff` (sha256
`4ac5c14aa8026c45ad0c1ad07ae758965089970f67888ea8b6cae233f90dcfe7`, 145 linhas).
**SEM `APROVADO-`.** Falta Camada C (Máquina) e decisão do Humano. Camada B já rodou
(parecer `bloco-3.2-camada-b-parecer.md`, posição CONDICIONAL contra o v1).

## Emenda v1 → v2 (31/08/2026, autorização do Humano "faz a emenda nesta sessão, achados 1 a 4")

v1 (`propostas/rejeitadas/bloco-3.2-eco-mecanizado-v1.diff`, sha256
`090c64e1b848caa2a3ba80535009bf45f5d5d6a1face6a5d750475aebe0ef4ae`) tratado pelos
achados da Camada B:

- **Achado 1 (condição da posição CONDICIONAL) — resolvido.** O script agora
  detecta árvore de trabalho suja num canônico (`git -c core.quotepath=false diff
  --name-only HEAD -- REGRAS.md MEMÓRIAS.md PROJETO.md`, que cobre staged +
  não-staged) e, se houver, emite `sync: FALHA · árvore de trabalho com edição não
  commitada em: <arquivos>` + exit 1 — não mais `PASS`. Testes A2/A3 da bateria v2.
- **Achado 2 (ressalva) — resolvido.** O rótulo saiu de `SYNC:` / `não-verificado`
  para a forma canônica de REGRAS: `sync:` minúsculo, `não verificado` com espaço.
  Testes A1/A5.
- **Achado 3 (ressalva) — resolvido.** `export LC_ALL="${LC_ALL_ECO:-C.UTF-8}"` no
  topo — `cut -c` volta a contar caractere mesmo sob `LC_ALL=C`. `\s` de `grep`/`sed`
  trocado por `[[:space:]]` (POSIX). Teste A8 (campo TES-002 íntegro sob `LC_ALL=C`).
- **Achado 4 (nota) — resolvido.** O campo TES-002 agora corta na 1ª frase
  (`sed -E 's/^(TES-002:[^.]*\.).*/\1/'`), que deixa o status e larga o nonce
  aposentado `e1d1a`; se mesmo assim sobrar uma crase no trecho, o campo vira
  "(status não extraído da forma esperada)". Teste A7 (nonce ausente).

Achados 5–8 da Camada B eram notas de concordância / documentação (separação
`HASH-ESTADO`×nonce ok; âncora do `grep` frágil mas aceitável; exit 1 sem caller;
paráfrase entre aspas no arquivo de evidência de Regra 8) — sem mudança de código.
O item "paráfrase entre aspas" (Achado 8) fica para a Camada C ou o Humano decidir
se o `regra8-3-passadas.md` precisa reescrever as citações.

Bateria v2 completa (10 casos): `memoria/missoes/fase2-eco-camada-a/bateria-v2.md`.
`git apply --check` do v2 contra HEAD `1c99d05`: limpo.

---
_O texto abaixo é do registro original do v1; vale como histórico. Onde diverge do
v2 (sha256 do par, "Falta Camada B"), vale o cabeçalho acima._


- Camada A: Claude Sonnet 5, na Máquina, 31/08/2026. Continuação de (307).
- Base de canon: HEAD `8678a46`.
- Autorização: Humano, 31/08 — "abre o item 4". O roteiro (`roteiro-fase2.md`,
  linha S8) prevê Camada A de 3.2 por "qualquer modelo".
- **Honestidade de contexto:** esta sessão leu o `roteiro-fase2.md`, o dossiê S1,
  as entradas (303)-(307) e escreveu o `dossie-selecao-silo-gateway.md` hoje. Não
  fez trabalho específico de 3.2 antes desta proposta. A independência de A/B/C se
  cumpre com B e C em hidratações distintas.

## O que a proposta faz

1. **Script novo `scripts/estado_para_eco.sh`** (read-only, determinístico).
   Imprime os fatos de estado herdado que o eco deve espelhar:
   - `HEAD` (sha7 + assunto do commit)
   - `TOPO-MEMÓRIAS` — primeira entrada após o marcador `ENTRADAS-NOVAS`
   - `SYNC` — `PASS` / `FALHA` / `não-verificado` contra `git ls-remote origin main`,
     no formato exato do `sync:` de REGRAS (`REGRAS=<hash8> · MEMÓRIAS=<hash8> · HEAD=<commit7>`)
   - `PROPOSTAS-ABERTAS` — nº de `propostas/*.diff` sem `APROVADO-` correspondente
   - `TES-002` — linha de estado curta do PROJETO.md
   - `HASH-ESTADO` — sha256(HEAD + topo + hash de REGRAS/MEMÓRIAS/PROJETO)[:12],
     derivado e público, para o eco citar
   - Código de saída: `0` utilizável · `1` SYNC FALHA · `2` marcador ausente.
2. **REGRAS.md, bullet "Eco pós-carregar"** ganha o mecanismo: com shell, rodar o
   script e fundamentar o eco nele (citar `HASH-ESTADO` + 1 linha de porquê); sem
   shell, declarar `sync: não verificado` e não preencher o que não mediu. O
   script imprime fatos — não escreve nem julga o eco; a conferência é do Humano.

## Regra 8 (detalhe completo em `memoria/missoes/fase2-eco-camada-a/regra8-3-passadas.md`)

3 passadas independentes em `qwen3.5-9b-64k` (produção), `ollama run`, prompt idêntico.

- **Q1 (só imprime vs. também valida o eco): CONVERGE — só imprime.** As três:
  "Máquina arbitra fatos, não a qualidade da proposta".
- **Q3 (obrigar vs. oferecer): CONVERGE — obrigar.** Emenda da Camada A: "obrigar
  **quando há shell**"; o caso sem-shell (nuvem) não estava no prompt e é tratado
  pelo `sync: não verificado` que já existe.
- **Q2 (prova anti-cópia): CONVERGE no risco, DIVERGE na forma.** 2/3 "hash que o
  eco cita"; 1/3 "exigir frase explicando a consistência". A proposta implementa
  **as duas juntas** (cita o `HASH-ESTADO` E dá 1 linha de porquê).
  **`lacuna` RESOLVIDA — Humano, 31/08/2026: "hash + frase", mantém as duas.**
  O `.diff` já implementa exatamente isso (sha256 inalterado); nada muda no par.
  Racional das duas: o hash prova que o script foi lido no estado atual (cópia
  cega de saída velha erra o hash); a frase prova que o modelo entendeu o que
  leu (cópia cega não conecta topo × SYNC). Uma sem a outra deixa meio buraco.

## Testes (clone descartável — `memoria/missoes/fase2-eco-camada-a/bateria-clone.md`)

- `git apply --check` contra `8678a46`: LIMPO. `bash -n`: OK.
- Saídas medidas: normal → `SYNC: PASS`, exit 0 · remoto inacessível →
  `não-verificado`, exit 0 · HEAD atrás → `SYNC: FALHA ... (atrás/à-frente: 0/1)`,
  exit 1 · marcador `ENTRADAS-NOVAS` ausente → topo desconhecido, exit 2.
- `PROPOSTAS-ABERTAS` casa a regra do P-8 (1 com `.diff` órfão, 0 após criar o
  `APROVADO-`). Determinístico entre execuções. `git status` limpo após rodar
  (não escreve nada).
- Evidência preservada em disco (a Camada C do v1 de 3.1 pediu isso):
  `memoria/missoes/fase2-eco-camada-a/` — `prompt.txt`, `passada_{1,2,3}.txt`
  (saída crua das 3 passadas), `regra8-3-passadas.md`, `bateria-clone.md`.

## Para a Camada B auditar

- O `HASH-ESTADO` não colide conceitualmente com o nonce do TES-002? (A proposta
  diz que não — derivado/público vs. secreto/`openssl`/nunca versionado — mas é
  ponto de auditoria.)
- A emenda "obrigar só quando há shell" enfraquece o controle? Alternativa seria
  "sempre obrigar a *tentar*, e declarar a falha" — B avalia.
- `SYNC: FALHA` sai com exit 1: algum caller trata esse exit hoje? (Não há caller
  ainda — o script é rodado à mão pelo modelo. B confirma que não se está criando
  dependência oculta.)
- O `grep -m1` do TES-002 depende do texto atual do PROJETO.md ("`- **TES-002:**`").
  Se o PROJETO reformatar essa linha, o campo vira "(linha não encontrada)" — falha
  suave, mas B decide se é aceitável.

## Para a Camada C verificar na Máquina

- `git apply --check` do `.diff` contra o HEAD do momento.
- Rodar `scripts/estado_para_eco.sh` do `.diff` num clone e conferir cada campo
  contra `git`/`sha256sum`/`grep` diretos — não contra este texto.
- `sha256sum` do `.diff` bate com o citado aqui.
- As 3 passadas em `passada_{1,2,3}.txt` dizem o que o `regra8-3-passadas.md` resume.
