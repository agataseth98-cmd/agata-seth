# Bloco 3.2 — Eco pós-carregar mecanizado — Parecer da Camada C

## Cabeçalho

- **Sessão/modelo:** Claude Sonnet 5 (`claude-sonnet-5`), sessão na Máquina com
  shell, hidratação independente — sem contexto compartilhado com a Camada A
  (que fez a proposta e a emenda v2) nem com a Camada B.
- **`date` da Máquina:** início `seg 31 ago 2026 14:59:07 -03`; fechamento
  `2026-08-31 15:05 -0300`.
- **HEAD auditado (vivo no turno):** `f5ad3135173a1c596de0edcf6b885d9ddcaa45e5`
  ("propostas: bloco-3.2 -- briefing da Camada C"). O briefing cita `f5ad313`
  como referência e é o que está vivo — não andou. B auditou em `a8bd19a`
  (2 commits atrás; `1c99d05` e `0945c02` no meio, ambos `propostas/…`). A
  emenda v2 (`0945c02`) é posterior ao parecer da B (`1c99d05`) — B só viu o v1.
- **Working tree:** `git status --porcelain` vazio antes e depois. Não toquei
  canônico, não criei `APROVADO-`, não apliquei `.diff`, não comitei.
- **Vetor (comandos que rodei, resumo):**
  - `sha256sum` dos dois `.diff`; `wc -l`; `git apply --check` do v2 contra
    `f5ad313` (3×, sempre limpo); `git apply --check` do v1 idem.
  - 6 clones descartáveis em `/tmp` (`camada-c-clone1/2`, `ccl3/4`, `cv1..4`,
    `cv3` + bare `canonbare`). Em cada um: `git apply` do v1 ou do v2, cenários
    de árvore suja / staged / limpa / HEAD atrás / marcador ausente, `bash -n`,
    execução do script com captura de `EXIT`, `xxd` do campo TES-002 sob
    `LC_ALL=C`, `grep` de `e1d1a`, `git status --porcelain` após N execuções.
  - `diff -u` entre o script do v1 e o do v2 aplicados; `diff -u` entre os
    `REGRAS.md` do v1 e do v2 aplicados (vazio).
  - `LC_ALL=C.UTF-8 locale` na Máquina para confirmar que o locale existe;
    `locale -a`.
  - Leitura de `REGRAS.md` (linhas 202–213, "sync: três formas"; 305–318, onde
    o hunk cai; tabela de falhas), `PROJETO.md` linha 153 (TES-002),
    `.gitignore`.
  - Leitura **integral** de `memoria/missoes/fase2-eco-camada-a/passada_{1,2,3}.txt`
    (filtrados do lixo de terminal do `ollama` com `sed`/`tr`/`cat -v`), contra
    `regra8-3-passadas.md` e `prompt.txt`; leitura de `bateria-clone.md`,
    `bateria-v2.md`, do parecer e do briefing da Camada B, do registro da
    Camada A.

---

## Posição

**PRONTO PARA O HUMANO.**

O `.diff` v2 (`4ac5c14aa8026c45ad0c1ad07ae758965089970f67888ea8b6cae233f90dcfe7`,
145 linhas) aplica limpo no HEAD vivo, o script é read-only e determinístico no
núcleo, e **os quatro achados da Camada B eram reais e o v2 resolve os quatro** —
reproduzi cada um em clone descartável, antes (v1) e depois (v2). Não há mudança
de comportamento no v2 que o changelog não cubra em espírito, e a leitura manual
do shell não achou defeito novo.

As duas pendências que registro (Achados 3 e 4 abaixo) são do **rastro de
evidência** — higiene de citação no `regra8-3-passadas.md` (arquivo local,
`gitignored`, não-canon) e uma passada de Regra 8 truncada — não do `.diff` que
vira canon. A Camada A já encaminhou a primeira "para a Camada C ou o Humano
decidir". Nenhuma das duas exige outra rodada de emenda no `.diff`; são decisão
do Humano sobre o arquivo de evidência. Por isso **PRONTO**, não CONDICIONAL.

---

## Achados

### Achado 1 — os 4 achados da Camada B eram reais e o v2 resolve os 4 — **nota (verificação positiva)**

Reproduzido em clone, HEAD vivo `f5ad313`.

**Achado 1 da B (condição bloqueante — `SYNC: PASS` falso com árvore suja).**
Real. Clone com **v1** aplicado, `MEMÓRIAS.md` e `REGRAS.md` sujados com `>>` sem
commit (`git status --porcelain` → ` M "MEM\303\223RIAS.md"` / ` M REGRAS.md`),
saída do script v1:

```
SYNC: PASS · REGRAS=0e64e7dd · MEMÓRIAS=98250bb9 · HEAD=f5ad313
HASH-ESTADO: e392ad356881
EXIT=0
```

`MEMÓRIAS=98250bb9` reproduz **bit a bit** o valor que a B publicou (mesma string
de sujeira, `MEMÓRIAS.md` idêntico entre `a8bd19a` e `f5ad313`) — corrobora que a
B de fato rodou o teste que alegou.

Clone com **v2** aplicado, `REGRAS.md` sujo sem commit:

```
sync: FALHA · árvore de trabalho com edição não commitada em: REGRAS.md (a cópia local não é o canon publicado)
EXIT=1
```

Caso **staged** (`git add "MEMÓRIAS.md"` sem commit), v2:

```
sync: FALHA · árvore de trabalho com edição não commitada em: MEMÓRIAS.md REGRAS.md (a cópia local não é o canon publicado)
EXIT=1   (script; o grep no meio do pipe mascarava — reexecutado cru)
```

O `git -c core.quotepath=false diff --name-only HEAD -- "${CANONICOS[@]}"` cobre
staged + não-staged, e o `core.quotepath=false` faz `MEMÓRIAS.md` sair literal
(sem o `"MEM\303\223RIAS.md"` que o `git status --porcelain` do mesmo clone
produz — o flag está fazendo trabalho real). **Resolvido.**

**Achado 2 da B (rótulo `SYNC:` / `não-verificado` não é a forma canônica).**
Real: `REGRAS.md` linhas 205–211 fixam `sync:` minúsculo, `sync: não verificado`
(com espaço), `sync: FALHA · <o que diverge>`, e a linha 211 diz textualmente
"não confundir com 'não verificado'". O v1 imprimia `SYNC: PASS` e
`SYNC: não-verificado`. O v2 imprime, verificado em clone:

```
sync: PASS · REGRAS=6baf5c77 · MEMÓRIAS=b5af2638 · HEAD=2ea18d0        (árvore limpa, HEAD==origin, EXIT 0)
sync: FALHA · HEAD local=2ea18d0 diverge do remoto=8e6e0d7 (atrás/à-frente: 0/1)   (EXIT 1)
sync: não verificado · lacuna: remoto inacessível (rede ou credencial)   (EXIT 0)
```

As três formas batem o canon. **Resolvido.**

**Achado 3 da B (`cut -c` conta byte sob `LC_ALL=C` → mojibake no campo TES-002).**
Real no v1 (sem `LC_ALL` fixo). O v2 põe `export LC_ALL="${LC_ALL_ECO:-C.UTF-8}"`
logo após `set -euo pipefail`. Testei em clone com o **caller** exportando
`LC_ALL=C` (o `export` do script sobrepõe); `xxd` da linha TES-002:

```
...61 74 c3 a9 20 65 78 69 73 74 69 72...      → "at" + c3a9 (é) íntegro
...29 2e 20 e2 80 a6 28 76 65 72...            → ". " + e280a6 (…) íntegro
```

Sem corte multibyte. Confirmei na Máquina que `C.UTF-8` resolve
(`LC_ALL=C.UTF-8 locale` sem erro; `locale -a` lista `C.utf8`; glibc normaliza).
O `\s` de `grep`/`sed` do v1 virou `[[:space:]]` (POSIX) no v2. **Resolvido**,
com hedge de portabilidade abaixo (Lacuna).

**Achado 4 da B (campo TES-002 ecoa o nonce aposentado `e1d1a`).**
Real: `PROJETO.md` linha 153 é
`- **TES-002:** **formalmente inativo até existir silo (Fase 2).** Nonce ` + "`e1d1a`" + ` aposentado (MEMÓRIAS (90)) — não deve ser ecoado por ninguém.`
O v1 (`cut -c1-110`) imprimia até "…Nonce `e1d1a` aposentado (MEMÓRIAS (90)) — não deve se". O v2 corta na 1ª frase
(`sed -E 's/^(TES-002:[^.]*\.).*/\1/'`, o `.` de "(Fase 2)."):

```
TES-002: formalmente inativo até existir silo (Fase 2). …(ver PROJETO.md "Estado dos bugs")
```

`grep 'e1d1a'` na saída completa sob `LC_ALL=C` e sob `C.UTF-8`: **ausente** nos
dois. Guarda extra: se sobrar crase no trecho, o campo vira "(status não extraído
da forma esperada …)". **Resolvido.**

Casos de código de saída do v2 (reproduzidos, não herdados de A/B): árvore limpa
+ HEAD==origin → `0`; remoto inacessível → `0`; árvore suja (mod ou staged) →
`1`; HEAD 1 atrás → `1`; marcador `ENTRADAS-NOVAS` ausente → `2` (com precedência
sobre o `1` da divergência de remoto — testei o caso em que ambos ocorrem e o
exit foi `2`). `bash -n` limpo. `git status --porcelain` após 5 execuções mostra
só o que o `.diff` introduz — **read-only confirmado**.

### Achado 2 — o changelog "Emenda v1 → v2" é fiel, mas incompleto — **nota**

`diff -u` entre o script do v1 e o do v2 aplicados: **toda** mudança de código
serve a um dos quatro achados (array `CANONICOS`, ramo `sujos`/`elif [ -n
"$sujos" ]`, `export LC_ALL`, `sync:` minúsculo em todas as strings, `[[:space:]]`,
`sed` da 1ª frase + guarda de crase). Nenhuma mudança **fora** do escopo dos
Achados 1–4. Não há alteração de comportamento não documentada.

O que o changelog **não** menciona, e que aparece no `.diff` v2 como consequência
dos consertos:

- O ramo do `sync:` foi **reestruturado**: v1 era `if vazio / elif igual→PASS /
  else→FALHA`; v2 é `if vazio / elif "!=" →FALHA / elif sujos→FALHA / else→PASS`.
  O teste de igualdade inverteu e o `PASS` foi para o `else` final. Equivalente
  para a comparação com o remoto; necessário para encaixar o ramo de árvore suja.
- A string da divergência mudou de `local=$head7 remoto=…` para
  `HEAD local=$head7 diverge do remoto=…` (o `bateria-v2.md` A4 mostra a nova).
- `cut -c1-110` → `cut -c1-160` na extração do TES-002 (folga; o `sed` já trunca
  na 1ª frase antes do `cut`).
- Comentário de cabeçalho `Q2 divergiu na forma…` → `Q2 decidida pelo Humano —
  "hash + frase", as duas` (sincroniza com o commit `8588fab`).

`diff -u` entre os `REGRAS.md` do v1 e do v2 aplicados: **vazio** — a prosa nova
do bullet "Eco pós-carregar" é idêntica nas duas versões. O changelog não alega
o contrário.

**O que verifiquei:** os dois `diff -u` acima; `git apply --check` do v2 3× no
HEAD vivo; leitura do hunk de `REGRAS.md` contra as linhas 305–318 do canon (cai
entre o bullet "Eco pós-carregar", linha 312, e "Critério de confiança", linha
313; aplica limpo).

### Achado 3 — Achado 8 da Camada B procede: `regra8-3-passadas.md` usa aspas em paráfrase — **ressalva**

Li as três passadas cruas inteiras. A Camada B classificou isto como nota e a
Camada A encaminhou "para a Camada C ou o Humano decidir se o
`regra8-3-passadas.md` precisa reescrever as citações". Confirmo que **procede**:

- `regra8-3-passadas.md` linha:
  `- Passada 1: "Apenas imprimir. Validação do eco é tarefa Humana."`
  Não há essa frase literal em `passada_1.txt`. O que existe é, no `thinking`,
  `the validation of the echo is a Human task` (inglês) e
  `a validação da coerência do eco é humana`. É compressão entre aspas.
- `regra8-3-passadas.md` linha:
  `- Fundamento comum nas três: "Máquina arbitra fatos; não a qualidade da proposta."`
  Essa frase não aparece literal em nenhuma das três. `passada_2.txt` tem
  `O script é fonte de verdade (Máquina arbitra fatos)`; o resto é síntese.
- Contra-exemplos onde a citação **é** quase literal (a favor do arquivo):
  `passada_2.txt` bloco final —
  `**Apenas imprimir.** O script é fonte de verdade (Máquina arbitra fatos). Se o script validasse o texto, ele entraria na decisão sobre a proposta, violando "modelo propõe".`
  → o bullet da Passada 2 em `regra8-3-passadas.md` só corta o meio.
  `passada_3.txt` bloco final —
  `**OBRIGAR.** Por que: A segurança contra "hidratação falha" é crítica e binária.`
  → o bullet Q3 da Passada 3 é fiel.

A regra do sistema e do meu briefing é "nunca paráfrase entre aspas".
**Recomendação (não bloqueia o `.diff`):** no `regra8-3-passadas.md`, tirar as
aspas dos bullets sintéticos ou marcá-los como "em síntese:", e reservar aspas
para os trechos que são cópia (Passada 2 Q1, Passada 3 Q3). É edição de um
arquivo local `gitignored` (`.gitignore` linha 22, `memoria/missoes/`), não do
canon.

### Achado 4 — `passada_1.txt` está truncada; não tem bloco de conclusão — **ressalva**

`passada_1.txt` (18687 bytes) **não** contém o marcador `...done thinking.` e
**não** tem bloco de resposta final numerada. O arquivo termina no meio de uma
frase do `thinking`:

```
    Okay, looks good.
    Wait, Q1 says "OU deve TAMBÉM receber o texto do eco que o
```

`grep -c 'done thinking' passada_1.txt` → `0` (contra `1` em `passada_2.txt` e
`passada_3.txt`, que têm o bloco final entregue).

Consequência: o parecer da Camada B (Achado 8) cita um trecho como
**"`passada_1.txt`, bloco de conclusão"** —
`1. **Apenas imprimir.** (Porquê: Preserva o papel da máquina como fornecedora de fatos neutros; a validação da coerência do eco é humana, evitando que a máquina "decida" sobre a qualidade da proposta do modelo.)`
— e esse texto **existe** no arquivo, mas é o **último rascunho dentro do
`thinking`** (indentado sob "Let's write."), imediatamente seguido do corte. Não
é uma resposta entregue. A Lacuna 2 do parecer da B ("li só os blocos de
conclusão via `tail` … não revisei o corpo inteiro do `thinking`") cobre isto em
parte, mas ninguém — nem A nem B — registrou que **uma das três passadas de
Regra 8 não rodou até o fim**.

**Impacto no veredito de Regra 8:** baixo, mas não nulo. Ver Achado 5 — a
convergência de Q1 e Q3 se sustenta mesmo assim, porque as outras duas passadas
entregaram resposta e o `thinking` inteiro da passada 1 converge; mas o registro
`regra8-3-passadas.md` apresenta a posição da passada 1 com mais firmeza do que o
artefato bruto sustenta. **Recomendação:** o `regra8-3-passadas.md` deveria
anotar que `passada_1.txt` está truncada e que a leitura dela é de um `thinking`
interrompido, não de resposta entregue. Idealmente, re-rodar a passada 1. Não
bloqueia o `.diff`.

### Achado 5 — a convergência Q1/Q3 alegada pelo `regra8-3-passadas.md` é real no corpo do `thinking` — **nota (verificação positiva)**

Li os três `thinking` inteiros, não só o `tail`.

- **Q1 (só imprime vs. também valida): converge em "só imprimir".**
  `passada_2.txt` (resposta entregue): `1. **Apenas imprimir.**`.
  `passada_3.txt` (resposta entregue): `1. **Apenas fatos (stdout de estado).**`.
  `passada_1.txt` (só `thinking`): oscila — chega a escrever
  `So maybe Script SHOULD validate?` e
  `checking if the model cited the correct HEAD *is* arbitrating a fact` — mas
  **toda** vez volta para `Only print` / `Apenas imprimir`, com o fundamento
  "Machine = Facts, Human = Values". Nenhuma das três conclui do lado oposto.
- **Q3 (obrigar vs. oferecer): converge em "obrigar".**
  As três: `passada_1.txt` `MANDATE it` / `Obrigatório rodar`; `passada_2.txt`
  `3. **Obrigar.**`; `passada_3.txt` `3. **OBRIGAR.**`. Sem raciocínio para o
  lado "oferecer" em nenhuma.
- **Q2 (forma da prova anti-cópia): 2/3 hash, 1/3 frase**, exatamente como o
  `regra8-3-passadas.md` diz. `passada_1.txt` → `state_hash` / token que o eco
  cita; `passada_3.txt` → `O script gera um *nonce* ou hash único … O eco do
  modelo deve incluir esse token`; `passada_2.txt` → `exigindo que o modelo
  **explique** a consistência dos dados no texto (ex: "HEAD correto porque X")`.
- A nota da Camada A de que `passada_3.txt` **usa a palavra "nonce"** e o `.diff`
  a evitou de propósito (`HASH-ESTADO` é derivado/público) — **confere**:
  `passada_3.txt` diz `O script gera um *nonce* ou hash único`.

O `.diff` implementa o que as três passadas entregues concluem (script só
imprime; regra obriga com shell) e a decisão do Humano sobre Q2 ("hash + frase",
as duas). Nada no `thinking` de nenhuma passada contradiz isso.

### Achado 6 — leitura manual do shell v2: sem defeito novo — **nota (verificação positiva)**

Sem `shellcheck` na Máquina; leitura manual.

- **`set -e` + `$(( ))` que avalia 0:** não há `(( ))` solto. `SAIDA=$(( SAIDA <
  1 ? 1 : SAIDA ))` e `abertas=$((abertas + 1))` são forma de **atribuição** — o
  status é o da atribuição (0), não o valor da expressão. Nenhuma execução minha
  abortou cedo.
- **`[ -z "$topo_linha" ] && { …; SAIDA=2; }`:** o `[ -z ]` é operando esquerdo
  de `&&` — isento de `set -e`; o `{ }` só roda quando verdadeiro.
- **globs:** `for d in propostas/*.diff` sob `shopt -s nullglob`.
  `CANONICOS=(REGRAS.md MEMÓRIAS.md PROJETO.md)` é literal, sem metacaractere.
- **`paste -sd' '` com nome com espaço:** os canônicos não têm espaço; `paste` é
  line-based (juntaria certo mesmo se tivessem). `git diff --name-only` com
  `core.quotepath=false` devolve `MEMÓRIAS.md` literal — verificado em clone
  (`MEMÓRIAS.md REGRAS.md` unidos por espaço na saída).
- **`sed`/`grep` não-POSIX:** `\s` foi trocado por `[[:space:]]`. Restam
  `grep -m1 -E` (o `-E` é POSIX; `-m1` é extensão GNU, presente na Máquina) e
  `sed -E` (POSIX-2024; GNU e BSD têm). `sed -E 's/^(TES-002:[^.]*\.).*/\1/'`
  com backreference no replacement — padrão.
- **`git -c core.quotepath=false diff` com `MEMÓRIAS.md` (acento):** funciona,
  verificado em clone nos dois cenários (mod e staged).
- **Ramo `|| echo "?/?"`:** `git rev-list … | tr … || echo "?/?"` — com
  `pipefail`, se `git rev-list` falhar o pipeline falha e o `||` dispara.
  `${atras_a_frente:-?/?}` é rede de segurança redundante. Não exercitado ao vivo
  (ver Lacunas).
- **Heredoc `<<FIM`** (sem aspas): expande `$head_subject` mas não re-avalia
  `$( )` dentro do valor expandido — seguro contra assunto de commit hostil.
  (Concordo com o item 3 da lista de acertos da Camada B.)

---

## O que a Camada A e a Camada B acertaram

**Camada A:**

1. `sha256` dos dois `.diff` **exatos**: v2 `4ac5c14a…dcfe7` / 145 linhas;
   v1 `090c64e1…0ef4ae`. Batem o registro e o briefing.
2. `git apply --check` do v2 **limpo** no HEAD vivo — que andou para `f5ad313`
   (a A citou `1c99d05`); os commits no meio são só `propostas/…`, não tocam
   `REGRAS.md` nem `scripts/`, por isso ainda aplica.
3. `bash -n` limpo; as armadilhas de `set -euo pipefail` evitadas (aritmética em
   forma de atribuição).
4. Os quatro consertos (Achados 1–4 da B) caem **exatamente** onde o changelog
   diz, e resolvem o que a B levantou — reproduzido antes/depois em clone.
5. Read-only real; determinismo do núcleo (`HASH-ESTADO` idêntico entre
   execuções no mesmo estado — `bateria-v2.md` A9, e as minhas execuções
   repetidas).
6. Separação `HASH-ESTADO` (derivado/público) × nonce TES-002
   (secreto/`openssl`/nunca versionado) explícita no comentário do script e no
   texto novo de `REGRAS.md`; a passada 3 usou "nonce" e o `.diff` a evitou de
   propósito — confere.
7. A emenda "obrigar só quando há shell" é coerente com o caso de nuvem já
   coberto por `sync: não verificado` no canon.
8. Contagem `PROPOSTAS-ABERTAS` correta: `1` (só o `bloco-3.2-eco-mecanizado.diff`
   sem `APROVADO-`; o v1 em `propostas/rejeitadas/` **não** é contado — glob
   não-recursivo).

**Camada B:**

1. Os quatro achados que levantou são **todos reais** — reproduzi cada um contra
   o v1 no HEAD vivo.
2. O teste do Achado 1 que a B publicou **reproduz bit a bit** aqui
   (`MEMÓRIAS=98250bb9` com a mesma string de sujeira) — a alegação "reproduzi
   na Máquina" é honesta.
3. Citações de `REGRAS.md` (linha 211, "não confundir com 'não verificado'") e
   `PROJETO.md` (linha 153, TES-002 com `e1d1a` "não deve ser ecoado por
   ninguém") **exatas**.
4. Não viu o v2 — e a linha do tempo confirma que não podia (v2 em `0945c02`,
   posterior ao parecer da B em `1c99d05`). A camada se manteve.
5. Achado 8 (paráfrase entre aspas) está **correto** e a B o marcou mesmo
   afirmando que o veredito de Regra 8 se sustenta — as duas coisas são
   verdadeiras (ver meus Achados 3 e 5).
6. Lacunas honestas: ramo `?/?` não exercido; sem `shellcheck`; não re-rodou o
   `qwen`; divergência de commit-base entre os documentos. Todas se confirmam.
7. A classificação da posição (CONDICIONAL com Achado 1 como condição, resto
   ressalva/nota) foi proporcional.

---

## Lacunas (o que não verifiquei e por quê)

1. **Ramo `git rev-list … || echo "?/?"`** (remoto genuinamente à frente com
   objetos ausentes no clone). Não consegui construir sem um remoto real
   divergente com history podada; o meu teste de "HEAD atrás" usou `push` para
   um bare local + `reset --hard`, então o objeto do remoto continuava presente
   e o resultado foi `0/1`, não `?/?`. Pelo `pipefail` + `|| echo`, deve
   degradar para a string `?/?` com `exit` ainda `1` — **não verificado ao
   vivo**.
2. **Portabilidade do `export LC_ALL="${LC_ALL_ECO:-C.UTF-8}"`.** Confirmei que
   `C.UTF-8` resolve **nesta** Máquina (glibc). Num host sem esse locale (musl,
   BusyBox, glibc antigo) o `export` emitiria aviso em stderr e cairia para `C`,
   reexpondo o corte por byte no `cut -c` — mitigado, mas não eliminado, pelo
   fato de o `sed` da 1ª frase já truncar o TES-002 antes do `cut`. Fora do
   alcance do que dá pra testar nesta Máquina.
3. **Autorização ao vivo do Humano** para a emenda ("faz a emenda nesta sessão,
   achados 1 a 4") — não é verificável do `git` (todos os commits são autorados
   `agata`). Aceito o registro da Camada A como está, com este hedge.
4. **Reprodução das 3 passadas de `qwen3.5-9b-64k`** — não é determinística e não
   a rodei. Auditei os `passada_{1,2,3}.txt` salvos (inteiros) contra
   `regra8-3-passadas.md`. O Achado 4 acima (passada 1 truncada) é o limite
   dessa auditoria: não sei o que a passada 1 teria concluído se rodasse até o
   fim — só que todo o `thinking` dela converge com as outras duas.
5. **`git ls-remote` em todo contexto de invocação.** Na Máquina funcionou
   (HTTPS, sem prompt). Num ambiente com credential-helper interativo ou env
   despida, `git ls-remote` falha em silêncio → `sync: não verificado` +
   exit `0` (degradação segura, mas o operador pode não notar que perdeu a
   checagem de remoto). Mesma lacuna que a B registrou.
6. **`shellcheck`** não está instalado na Máquina — o Achado 6 é leitura manual
   minha, não saída de ferramenta.

---

*Camada C: Claude Sonnet 5 (`claude-sonnet-5`) · sessão independente na Máquina
`/home/orusoua/agata` @ `f5ad3135173a1c596de0edcf6b885d9ddcaa45e5` · vetor:
`sha256sum` + `wc -l` dos dois `.diff`; `git apply --check` v2 3× + v1; 8 clones
descartáveis em `/tmp` com v1/v2 aplicados nos cenários árvore-suja / staged /
limpa / HEAD-atrás / marcador-ausente; `bash -n`; `xxd` do campo TES-002 sob
`LC_ALL=C`; `grep e1d1a`; `git status --porcelain` pós-N-execuções;
`diff -u` script v1↔v2 e `REGRAS.md` v1↔v2; `LC_ALL=C.UTF-8 locale` + `locale -a`;
leitura integral de `passada_{1,2,3}.txt` filtradas · turno: 2026-08-31
14:59–15:05 -03 (relógio da Máquina)*
