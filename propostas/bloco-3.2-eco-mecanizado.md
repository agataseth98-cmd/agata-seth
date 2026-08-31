# Bloco 3.2 — Eco pós-carregar mecanizado — Camada A

**Par:** `bloco-3.2-eco-mecanizado.diff` (sha256 `090c64e1b848caa2a3ba80535009bf45f5d5d6a1face6a5d750475aebe0ef4ae`).
**SEM `APROVADO-`.** Falta Camada B (sessão separada), Camada C (Máquina), decisão do Humano.

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
