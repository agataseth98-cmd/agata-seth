# Bloco 3.2 — Eco pós-carregar mecanizado — Parecer da Camada B

## Cabeçalho

- **Sessão/modelo:** Claude Sonnet 5 (`claude-sonnet-5`), hidratação independente,
  sem contexto compartilhado com a Camada A. Sessão com Máquina (shell).
- **Data/hora da Máquina (`date`):** `seg 31 ago 2026 14:34:51 -03` (início) →
  `2026-08-31 14:40 -0300` (fechamento).
- **Canon no momento da auditoria:** `git -C /home/orusoua/agata log -1` →
  `a8bd19a1c35f9799387bd3462ae2d86747135b19`
  ("propostas: bloco-3.2 -- briefing da Camada B"). Working tree limpo antes e
  depois (`git status --porcelain` vazio; a Camada B não tocou canônico).
- **Vetor (o que rodei):**
  - `sha256sum propostas/bloco-3.2-eco-mecanizado.diff` →
    `090c64e1b848caa2a3ba80535009bf45f5d5d6a1face6a5d750475aebe0ef4ae` — **bate**
    com o que o registro da Camada A afirma. `wc -l` → 114 linhas.
  - `git apply --check propostas/bloco-3.2-eco-mecanizado.diff` contra HEAD
    `a8bd19a` → **limpo** (e `git apply --check -3` também).
  - Clone descartável `git clone /home/orusoua/agata /tmp/camada-b-clone`, aplicado
    o `.diff`, `bash -n scripts/estado_para_eco.sh` → OK (sem `shellcheck`
    disponível na Máquina).
  - Rodei `scripts/estado_para_eco.sh` no clone nos casos: estado normal;
    remoto inacessível; HEAD 1 commit atrás; marcador `ENTRADAS-NOVAS` ausente;
    marcador ausente + HEAD atrás (precedência); **árvore suja** (edições não
    commitadas em `REGRAS.md`/`MEMÓRIAS.md`).
  - `git ls-remote origin main` na Máquina real (remoto
    `https://github.com/agataseth98-cmd/agata-seth.git`) → devolve `a8bd19a…`.
  - `grep -rn estado_para_eco` no repo; leitura de `.githooks/pre-commit`,
    `scripts/perimetro.sh` (P-8) para procurar caller.
  - `cut -c1-110` da linha TES-002 sob `LC_ALL=C.UTF-8` vs `LC_ALL=C`.
  - Li as 3 passadas cruas (`passada_{1,2,3}.txt`, blocos de conclusão via
    `tail`) contra `regra8-3-passadas.md`.

---

## Posição

**CONDICIONAL** — o `.diff` aplica, o script é read-only, determinístico no
essencial e passa todos os casos de borda de código de saída que a Camada A
declarou. Falta **uma correção** antes de virar `APROVADO-`:

1. **O script reporta `SYNC: PASS` + exit 0 com a árvore de trabalho suja.**
   `git ls-remote` só compara o SHA do commit `HEAD` com o do remoto; edições
   não commitadas em `REGRAS.md`/`MEMÓRIAS.md`/`PROJETO.md` passam sem detecção,
   e o `HASH-ESTADO` sai calculado sobre bytes que não são o canon. Isso é uma
   forma de "cópia diverge do canon" — exatamente o que o `SYNC` deveria pegar.
   Condição: detectar árvore suja (ao menos nos três arquivos de canon) e, nesse
   caso, **não** emitir `SYNC: PASS` sem qualificação — rebaixar para `FALHA` ou
   anexar `árvore suja` explícito. Ver Achado 1.

As demais entradas abaixo são **ressalvas** e **notas** — não bloqueiam, mas a
Camada C / o Humano deveriam decidir sobre a 2 e a 3 antes da aplicação.

---

## Achados

### Achado 1 — `SYNC: PASS` falso com árvore suja — **ressalva (condição da posição)**

**Trecho exato (script, ramo do `SYNC`):**

```
remoto=$(git ls-remote origin main 2>/dev/null | awk '{print $1}' | head -c 40 || true)
if [ -z "$remoto" ]; then
  sync_linha="SYNC: não-verificado · lacuna: remoto inacessível (rede ou credencial)"
elif [ "$remoto" = "$head_full" ]; then
  sync_linha="SYNC: PASS · REGRAS=$h_regras · MEMÓRIAS=$h_memorias · HEAD=$head7"
```

com `head_full=$(git rev-parse HEAD)` e
`h_regras=$(sha256sum REGRAS.md   | cut -c1-8)` (idem `MEMÓRIAS.md`, `PROJETO.md`).

**O que está errado.** O único teste de `PASS` é `"$remoto" = "$head_full"` — ou
seja, "o commit apontado por `refs/heads/main` no remoto é igual ao meu `HEAD`".
Não há `git diff --quiet` nem checagem de árvore limpa. Os hashes `REGRAS=…`,
`MEMÓRIAS=…` impressos são do arquivo **na árvore de trabalho**, que pode ter
modificação não commitada. Resultado: `SYNC: PASS · …` e `exit 0` num estado em
que a cópia local do canon **não** é o canon publicado. O `HASH-ESTADO` (que a
regra nova manda o eco citar como prova anti-cópia) é derivado desses mesmos
bytes adulterados.

Isto conflita com o que `REGRAS.md` (canon, "sync tem preço", linha ~226) exige
de um `PASS`:

> Só diga `sync: PASS` com evidência de Máquina desta sessão: hash real
> (`sha256sum`), `git rev-parse`/`ls-tree`/`ls-remote`, ou fetch do raw comparado
> byte a byte — nunca hash citado de memória ou herdado de resposta anterior sem
> re-medir.

O `sha256sum` é feito ao vivo, sim, mas de um arquivo que pode divergir do commit;
o `PASS` afirma sincronia com o canon que não foi verificada.

**O que verifiquei na Máquina.** Clone limpo de `/home/orusoua/agata`, `.diff`
aplicado, depois:

```
printf '\n\nLINHA FALSA INJETADA NAO COMMITADA\n' >> MEMÓRIAS.md
printf '\n\nregra falsa nao commitada\n' >> REGRAS.md
git status --porcelain   →  M "MEM..RIAS.md" / M REGRAS.md / ?? scripts/estado_para_eco.sh
bash scripts/estado_para_eco.sh
```

Saída (recortada):

```
SYNC: PASS · REGRAS=b3e064eb · MEMÓRIAS=98250bb9 · HEAD=a8bd19a
HASH-ESTADO: a72394a3376b
EXIT=0
```

Comparado com a árvore limpa (`SYNC: PASS · REGRAS=c1526525 · MEMÓRIAS=b5af2638`):
os hashes mudaram para valores que não correspondem a nenhum commit, e o `SYNC`
continuou `PASS`, exit `0`.

**Nota de contexto.** O `bateria-clone.md` da Camada A observou o sintoma
adjacente — "`REGRAS=6baf5c77` (não `c1526525` da árvore-mãe) porque o `.diff`
altera REGRAS.md no clone; `HASH-ESTADO` acompanha — mudou o canon, mudou o hash.
Propriedade desejada, não bug." — e classificou como desejável. O hash acompanhar
a mudança é desejável; o que ninguém registrou é que o `SYNC` **continua `PASS`**
enquanto a árvore está suja. Um modelo que `carregar` num repo em meio a edição
(ou logo após aplicar uma proposta sem commit) produz um eco que afirma sincronia
com o canon que é falsa.

**Hedge para a Camada C.** Meu teste sujou os arquivos com `>>` num clone cujo
`origin` é um caminho local; `git ls-remote` num clone de caminho local lê o repo
mãe e devolve o SHA — por isso `HEAD == remoto`. Numa Máquina com o `origin` do
GitHub o comportamento é o mesmo desde que `HEAD` esteja no commit publicado
(confirmei que `git ls-remote origin main` na Máquina real devolve `a8bd19a`, =
`HEAD`). Reproduzir: em qualquer working tree cujo `HEAD` = `origin/main`, editar
`REGRAS.md` sem commitar e rodar o script.

### Achado 2 — o rótulo `SYNC` do script não é a forma canônica `sync:` — **ressalva**

**Trecho exato (script):**

```
  sync_linha="SYNC: PASS · REGRAS=$h_regras · MEMÓRIAS=$h_memorias · HEAD=$head7"
...
  sync_linha="SYNC: não-verificado · lacuna: remoto inacessível (rede ou credencial)"
```

**Trecho exato (`REGRAS.md` canon, "Carregar e formatos"):**

```
**`sync:` — três formas, nunca uma quarta:**
```
```
sync: PASS · REGRAS=<hash8> · MEMÓRIAS=<hash8> · HEAD=<commit7>
sync: FALHA · <o que diverge, em 1 linha>
sync: não verificado · lacuna: <motivo>
```

**O que está errado / arriscado.** O script imprime `SYNC:` (maiúsculo) e
`não-verificado` (com hífen); o canon usa `sync:` (minúsculo) e `não verificado`
(com espaço — ver também a linha canon "não confundir com 'não verificado'").
O registro da Camada A afirma que o campo sai "no formato exato do `sync:` de
REGRAS" — isso é impreciso: os **valores** (`REGRAS=<hash8> · MEMÓRIAS=<hash8> ·
HEAD=<commit7>`) batem, o **rótulo e a grafia** não. A regra nova diz "escreva o
eco a partir da saída dele" (não "copie"), e o próprio rodapé do script diz "não
é o eco"; mesmo assim, um modelo apressado que cole a linha `SYNC: não-verificado`
do script no bloco de prontidão introduz uma quarta grafia numa regra cujo texto
é "**três formas, nunca uma quarta**".

**O que verifiquei.** Comparação direta do texto do `.diff` (script) com
`REGRAS.md` linhas ~205–211 na árvore atual. Rodei o script; a saída literal é
`SYNC: não-verificado · lacuna: remoto inacessível (rede ou credencial)` e
`SYNC: PASS · REGRAS=6baf5c77 · MEMÓRIAS=b5af2638 · HEAD=a8bd19a`.

**Recomendação (não bloqueia):** alinhar o rótulo (`sync:` minúsculo, "não
verificado" com espaço) OU acrescentar uma linha no rodapé do script dizendo
explicitamente "não cole esta linha; reescreva no formato `sync:` de REGRAS".

### Achado 3 — `cut -c` / `sed -E '\s'` dependem de locale; "determinístico" é condicional — **ressalva**

**Trecho exato (script):**

```
tes002=$(grep -m1 -E '^\s*-\s+\*\*TES-002:\*\*' PROJETO.md \
  | sed -E 's/^\s*-\s+//; s/\*\*//g' \
  | cut -c1-110 || true)
```

**O que está errado / arriscado.** O script não fixa `LC_ALL`/`LC_CTYPE`. A linha
TES-002 do `PROJETO.md` tem UTF-8 (travessão `—`, acentos, crases). `cut -c1-110`
conta **caracteres** sob locale UTF-8 e **bytes** sob `LC_ALL=C` — no segundo caso
corta no meio de um caractere multibyte e imprime bytes quebrados. `\s` em
`sed -E` / `grep -E` é extensão GNU (funciona na Máquina; não é POSIX — quebraria
em `sed`/`grep` BSD).

**O que verifiquei na Máquina.** `locale` → `LANG=pt_BR.UTF-8`. Extraí a linha e
apliquei `cut -c1-110`:

```
utf8 (C.UTF-8):  ...)) — não deve se
C (LC_ALL=C):    ...S (90)) M-bM-^@M-^T nM-CM-#o de     (via cat -v: travessão e "não" viram bytes crus)
```

O comprimento da linha extraída é 467 caracteres / 486 bytes, então `cut -c1-110`
sempre trunca (e pode partir palavra: no caso atual para em "…— não deve se").

**Alcance real.** O script é "rodado à mão pelo modelo" na Máquina, cujo locale
interativo é `pt_BR.UTF-8` — no uso previsto, sem mojibake. O risco aparece se
algum dia um cron/CI/serviço o invocar com `LC_ALL=C` (não há caller hoje — ver
Achado 7). Por isso: ressalva, não bloqueio. Correção barata: `export LC_ALL` num
locale UTF-8 no topo, ou trocar `cut -c` por `cut -b`/`head -c` com truncagem
ciente de multibyte. Consequência para o registro: a afirmação "determinístico"
da Camada A vale para o núcleo (`HEAD`, topo, `HASH-ESTADO`) num ambiente estável;
não é incondicional (depende de locale + árvore limpa + rede).

### Achado 4 — o script imprime o nonce aposentado `e1d1a` no campo TES-002 — **nota**

**Trecho exato (saída do script, medida):**

```
TES-002: formalmente inativo até existir silo (Fase 2). Nonce `e1d1a` aposentado (MEMÓRIAS (90)) — não deve se …(ver PROJETO.md "Estado dos bugs")
```

**Trecho exato (`PROJETO.md` canon, "Estado dos bugs e dos testes"):**

> **TES-002:** **formalmente inativo até existir silo (Fase 2).** Nonce `e1d1a`
> aposentado (MEMÓRIAS (90)) — não deve ser ecoado por ninguém.

**O que é.** O `grep`/`sed`/`cut` recorta a linha e o token `e1d1a` cai dentro dos
110 caracteres. `REGRAS.md` (canon, tabela de falhas) lista "Ecoar nonce de MOD
alheio como saúde" como falha documentada; o `PROJETO.md` diz que este nonce "não
deve ser ecoado por ninguém". O script mecaniza a extração desse token para um
"cartão de estado" a partir do qual o modelo é instruído a escrever o eco — um
modelo que cole a linha inteira ecoa `e1d1a`.

**Severidade baixa:** `e1d1a` é público, já canônico, e está marcado como
aposentado — não é um segredo vivo. O nonce sucessor "guardado fora do canônico,
nunca commitado" não aparece (o script não tem como vazá-lo). Ainda assim, é
atrito com a higiene "nonce não se ecoa". Correção trivial: truncar antes da
primeira crase, ou substituir por `[nonce aposentado]`.

**O que verifiquei.** Rodei o script; o campo TES-002 sai como acima em todos os
casos de borda testados.

### Achado 5 — `HASH-ESTADO` × nonce do TES-002: separação adequada, colisão residual é de local — **nota**

**Trecho exato (`.diff`, texto novo em `REGRAS.md`):**

> O `HASH-ESTADO` é derivado e público: não é o nonce do TES-002 e não substitui
> a linha `Nonce:` do bloco de prontidão.

**Trecho exato (comentário do script):**

> HASH-ESTADO é derivado e PÚBLICO — não tem relação com o nonce secreto do
> TES-002 (esse é gerado por openssl, nunca versionado, entregue à mão).

**Avaliação (ponto 1 da Camada A).** Não encontrei caminho no **script** em que o
`HASH-ESTADO` seja tratado como prova de continuidade: ele é `sha256` de
`HEAD + topo + hash de REGRAS/MEMÓRIAS/PROJETO`, tudo público e recomputável por
qualquer um com o repo. O papel do nonce (TES-002) é outro: prova que o sucessor
herdou o MOD privado da sessão anterior. A negativa explícita existe nos dois
lugares. **Concordo com a Camada A: não colidem conceitualmente.**

Risco residual, com hedge: a colisão não é na derivação, é no **local**. A regra
nova põe o `HASH-ESTADO` como o token anti-cópia do eco pós-carregar; o TES-002
(bullet logo acima, canon) diz que o nonce "é reproduzido no eco pós-carregar".
Quando a Fase 2 reativar o TES-002, o mesmo eco de ≤5 linhas carrega dois tokens
de significados distintos, e um modelo sob carga pode citar o `HASH-ESTADO` e
sentir que cumpriu a prova de continuidade. Hoje o TES-002 está "formalmente
inativo", então não há conflito vivo. A frase "não substitui a linha `Nonce:`"
mitiga; sugiro que a Camada C considere se o texto novo deveria também lembrar
"o `HASH-ESTADO` não dispensa reproduzir o nonce quando o TES-002 estiver ativo".

### Achado 6 — âncora do `grep` da linha TES-002 é frágil e sem sinal de saída — **nota**

**Trecho exato (script):** `grep -m1 -E '^\s*-\s+\*\*TES-002:\*\*' PROJETO.md`
com fallback `[ -z "$tes002" ] && tes002="TES-002: (linha não encontrada em PROJETO.md)"`.

**O que verifiquei.** O padrão casa a linha atual do `PROJETO.md`
(`- **TES-002:** **formalmente inativo…**`). Se essa linha for reformatada
(cabeçalho `###`, sem negrito, `- TES-002 —`), o campo vira
"(linha não encontrada em PROJETO.md)". Diferente do marcador `ENTRADAS-NOVAS`
(cuja ausência dá `exit 2`), a falha da âncora TES-002 **não** mexe no código de
saída — o script sai `0`/`1` normalmente com o campo degradado.

**Avaliação (ponto 4 da Camada A).** Concordo que é falha suave aceitável: o
campo TES-002 é um ponteiro ("…(ver PROJETO.md 'Estado dos bugs')"), não a fonte
autoritativa, e o Humano confere o eco. Registro só que, ao contrário do marcador,
não há sinal mecânico quando degrada — quem reformatar a linha do PROJETO só
percebe relendo a saída.

### Achado 7 — `exit 1` compartilhado entre "SYNC FALHA" e abortos de `set -e`; sem caller hoje — **nota**

**Trecho exato (script):** `set -euo pipefail` / `cd "$(git rev-parse --show-toplevel)"`
/ (no ramo FALHA) `SAIDA=$(( SAIDA < 1 ? 1 : SAIDA ))` / `exit $SAIDA`.

**O que observei.** `exit 1` sai tanto de "SYNC FALHA" (documentado) quanto de
qualquer aborto de `set -e` antes do `exit $SAIDA` — ex.: rodar fora de um repo
git faz `git rev-parse --show-toplevel` falhar, `cd ""` falhar, e o script morrer
com `1`; idem se faltar `REGRAS.md`/`MEMÓRIAS.md` (o `sha256sum` no pipe com
`pipefail` aborta). Um consumidor de código de saída não distinguiria
"cópia diverge" de "ambiente quebrado".

**Por que não bloqueia (ponto 3 da Camada A — confirmado).** Não há consumidor.
`grep -rn estado_para_eco` no repo só acha os próprios documentos da proposta
(`bloco-3.2-eco-mecanizado.{md,diff}`, o briefing). `.githooks/pre-commit` roda
`scripts/perimetro.sh` (P-1..P-10) e `.githooks/gerar-hermes-md.sh` — nenhum
importa nem executa o script novo. `perimetro.sh` P-8 (`_p8_eh_comportamento`)
classifica `scripts/*` como mudança de comportamento que exige o par
`.diff` + `APROVADO-` — ou seja, o próprio bloco 3.2 está sob a quarentena
correta, mas nada automatiza a **execução** do script. **A proposta não cria
dependência oculta desse exit.**

### Achado 8 — `regra8-3-passadas.md` cita as passadas entre aspas com paráfrase — **nota**

**Trecho exato (`regra8-3-passadas.md`):**

```
- Passada 1: "Apenas imprimir. Validação do eco é tarefa Humana."
...
- Fundamento comum nas três: "Máquina arbitra fatos; não a qualidade da
  proposta."
```

**Trecho exato (`passada_1.txt`, bloco de conclusão):**

> 1. **Apenas imprimir.** (Porquê: Preserva o papel da máquina como fornecedora
> de fatos neutros; a validação da coerência do eco é humana, evitando que a
> máquina "decida" sobre a qualidade da proposta do modelo.)

**Trecho exato (`passada_3.txt`, bloco de conclusão):**

> 1. **Apenas fatos (stdout de estado).** Por que: A Máquina deve ser fonte
> passiva de *ground truth*. Validar o texto do modelo desvia a função da Máquina
> (fatos) para arbitragem de valores/qualidade, competência humana.

**O que está errado.** Os bullets das passadas 1 e 3 e a linha "Fundamento comum"
estão entre aspas mas são **compressões reescritas**, não trechos copiados. A
frase "Máquina arbitra fatos; não a qualidade da proposta" aparece literal em
nenhuma das três (a passada 2 traz "O script é fonte de verdade (Máquina arbitra
fatos)"; o resto é síntese). A regra do sistema — e do meu briefing — é
"nunca paráfrase entre aspas".

**O que verifiquei.** Li os blocos de conclusão de `passada_{1,2,3}.txt` (os
arquivos têm caracteres de controle de terminal do `ollama`; li via `tail`).
**A convergência substantiva é real:** as três respondem Q1 com "apenas
imprimir/só fatos" e Q3 com "obrigar/OBRIGAR", cada uma com o fundamento
"Máquina = fatos, Humano = qualidade". A passada 2 é a única cujo bullet no
resumo é quase literal. O `.diff` implementa o que o resumo conclui (script só
imprime; regra obriga com shell). O achado é sobre a **forma da citação** no
arquivo de evidência, não sobre o veredito.

---

## O que a Camada A acertou

1. **sha256 do `.diff`** bate exatamente com o declarado
   (`090c64e1b848…0ef4ae`); 114 linhas, como no `bateria-clone.md`.
2. **`git apply --check` limpo** — confirmei contra o HEAD atual `a8bd19a`, que
   está 3 commits à frente da base que o registro cita (`8678a46`); os 3 commits
   intermediários (`7a6b6cc`, `8588fab`, `a8bd19a`) são todos `propostas/…`,
   nenhum toca `REGRAS.md` nem `scripts/` — por isso ainda aplica.
3. **`bash -n` OK** e o script **evita as armadilhas de `set -euo pipefail`**: não
   há `((...))` solto (que retornaria 1 ao avaliar 0); os incrementos são
   `SAIDA=$(( SAIDA < 1 ? 1 : SAIDA ))` e `abertas=$((abertas + 1))`, forma de
   atribuição, imune. Os `[ -z … ] && { … }` são elos não-finais de lista `&&`,
   fora do alcance do `set -e`. O `|| true` cobre `git ls-remote` e o pipe do
   TES-002. O heredoc `<<FIM` (não `<<'FIM'`) expande `$head_subject` mas não
   re-avalia `$( )` no valor expandido — seguro contra assunto de commit
   malicioso.
4. **Códigos de saída** — reproduzi todos: `0` estado normal · `0` remoto
   inacessível · `1` HEAD atrás (`SYNC: FALHA · … (atrás/à-frente: 0/1)`) · `2`
   marcador `ENTRADAS-NOVAS` ausente · `2` quando marcador ausente **e** HEAD
   atrás (precedência do 2 sobre o 1). Casam a tabela do `bateria-clone.md`.
5. **Read-only confirmado** — `git status --porcelain` após N execuções mostra só
   o que o `.diff` introduz (`M REGRAS.md`, `?? scripts/estado_para_eco.sh`); o
   script não escreve, não commita, não faz push. Só lê e faz `git ls-remote`.
6. **`HASH-ESTADO` como prova anti-cópia é um desenho sólido**: um modelo recém
   carregado tem REGRAS/MEMÓRIAS/PROJETO no contexto mas não computa `sha256`
   confiável de cabeça — citar o `HASH-ESTADO` certo evidencia que o script (ou
   uma ferramenta de hash) rodou no estado atual.
7. **Separação `HASH-ESTADO` × nonce** está explícita no comentário do script e
   no texto novo de REGRAS (ver Achado 5). A nota da Camada A sobre a passada 3
   ter usado a palavra "nonce" e o `.diff` tê-la evitado de propósito procede.
8. **Convergência Q1/Q3 é real** nas saídas cruas das 3 passadas (Achado 8).
9. **Emenda "obrigar só quando há shell" é razoável.** Avaliei o ponto 2 do
   briefing: a alternativa "sempre obrigar a *tentar* e declarar a falha" é vazia
   para um modelo sem execução de código — ele não tem como tentar. O que
   importa é que a sessão sem shell não fabrique os campos, e o texto novo diz
   isso ("não preenche o que não mediu"); o caso já é coberto por
   `sync: não verificado` no canon. Não enfraquece o controle de forma
   relevante. Ressalva miúda: "com shell / sem shell" é auto-declarado pelo
   modelo, sem árbitro — mas isso é problema de modelo mentiroso, que nenhuma
   redação resolve, e o Humano confere o eco.
10. **Ponto 4 da Camada A (âncora do `grep` frágil) é correto** e concordo com a
    classificação de falha suave aceitável (Achado 6).
11. **Ponto 3 da Camada A (exit 1 sem caller) confirmado** — não há consumidor do
    código de saída em lugar nenhum do repo (Achado 7).

---

## Lacunas (o que não consegui verificar e por quê)

1. **Ramo "remoto genuinamente à frente com objetos que o clone não tem"**
   (`git rev-list --left-right --count "$head_full...$remoto"` → `?/?`). Meu teste
   de "HEAD atrás" usou `git reset --hard HEAD~1`, então o objeto do remoto ainda
   estava local e o resultado foi `0/1`, não `?/?`. O caminho em que o `git
   rev-list` falha e cai no `|| echo "?/?"` não foi exercido. Hedge: o `exit`
   continua `1`; só a string `(atrás/à-frente: …)` mudaria para `?/?`.
2. **Não rodei as 3 passadas de Regra 8.** Não tenho como reproduzir
   `qwen3.5-9b-64k` de forma determinística. Auditei os `passada_{1,2,3}.txt`
   salvos contra `regra8-3-passadas.md` — e só os blocos de conclusão (via
   `tail`); os arquivos têm lixo de terminal do `ollama` e não revisei o corpo
   inteiro do `thinking` de cada um. A Camada C deveria confirmar que nada no
   `thinking` contradiz a conclusão citada.
3. **Q2 (forma da prova anti-cópia: "hash + frase")** está marcada como decidida
   pelo Humano em 31/08 — não reauditei, conforme instrução.
4. **Autenticação do `git ls-remote` na Máquina em todo contexto de invocação.**
   Minha execução na Máquina funcionou (HTTPS para o GitHub, sem prompt). Não
   consigo, daqui, enumerar todo ambiente em que um modelo poderia chamar o
   script; num contexto com credential-helper interativo ou env despida, o
   `git ls-remote` falharia em silêncio e viraria `SYNC: não-verificado` (exit
   `0`) — degradação segura, mas o operador pode não notar que perdeu a checagem.
5. **Divergência de commit-base entre os documentos.** O briefing diz "fixado em
   `8588fab`", o registro da Camada A diz "Base de canon: HEAD `8678a46`" (e o
   `bateria-clone.md`, `8678a46`), e o HEAD vivo é `a8bd19a`. Todos os commits
   entre eles são `propostas/…`, então não muda a análise — mas a Camada C deve
   re-rodar `git apply --check` contra o HEAD que estiver vivo no turno dela.
6. **`shellcheck` não está instalado na Máquina** — a análise estática do shell
   acima é leitura manual minha, não saída de ferramenta.

---

*Modelo: Claude Sonnet 5 (`claude-sonnet-5`) · vetor: Máquina `/home/orusoua/agata`
@ `a8bd19a`, clone descartável `/tmp/camada-b-clone` + `/tmp/cb2`, `git apply
--check` + `bash -n` + execução do script nos 6 casos de borda + `sha256sum` do
`.diff` + `grep` de caller + `cut`/locale + leitura das 3 passadas cruas ·
turno: 2026-08-31 14:34–14:41 -03 (relógio da Máquina)*
