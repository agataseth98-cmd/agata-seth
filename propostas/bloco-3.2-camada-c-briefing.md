# Camada C — Bloco 3.2 (eco pós-carregar mecanizado) — briefing

**Para uma sessão de hidratação SEPARADA, na Máquina.** Não pode ser a sessão que
fez a Camada A / a emenda v2 (Claude Sonnet 5 na Máquina, commits `7a6b6cc` →
`0945c02`) nem a que fez a Camada B (parecer `bloco-3.2-camada-b-parecer.md`). Um
executor em dois papéis anula a camada (REGRAS, "Cadeia de auditoria em camadas").

## Seu papel

Você é a terceira camada. Verifica as **alegações** da Camada A e da Camada B
**contra `git` / `hash` / `grep` / execução real — não contra o texto delas**. O
antídoto para "auditor que alega sem verificar" é auditar o auditor na Máquina.
Você **não** toca canônico, **não** cria `propostas/APROVADO-*`, **não** aplica o
`.diff`, **não** comita/pusha. Sua saída é um parecer para o Humano.

## Contexto da cadeia até aqui

- **Camada A** propôs o Bloco 3.2: script novo `scripts/estado_para_eco.sh`
  (read-only, imprime fatos de estado herdado para fundamentar o "eco
  pós-carregar") + expansão do bullet "Eco pós-carregar" em `REGRAS.md`.
- **Camada B** (sessão independente, na Máquina) auditou o **v1** e fechou
  **CONDICIONAL**: 1 condição (Achado 1) + 2 ressalvas (2, 3) + 5 notas (4–8).
- **Camada A revisora** (mesma sessão de A, com autorização ao vivo do Humano)
  emendou v1 → **v2**, tratando Achados 1–4.

## O que ler (o repo é público; fixe no HEAD vivo do seu turno)

Base viva: `github.com/agataseth98-cmd/agata-seth` @ `0945c02` ou o que estiver em
`git -C /home/orusoua/agata log -1` quando você rodar.

1. `propostas/bloco-3.2-eco-mecanizado.diff` — **v2**. Alegado: sha256
   `4ac5c14aa8026c45ad0c1ad07ae758965089970f67888ea8b6cae233f90dcfe7`, 145 linhas.
2. `propostas/rejeitadas/bloco-3.2-eco-mecanizado-v1.diff` — v1. Alegado: sha256
   `090c64e1b848caa2a3ba80535009bf45f5d5d6a1face6a5d750475aebe0ef4ae`.
3. `propostas/bloco-3.2-eco-mecanizado.md` — registro da Camada A (cabeçalho v2 +
   changelog da emenda; corpo v1 como histórico).
4. `propostas/bloco-3.2-camada-b-parecer.md` — o parecer da Camada B.
5. `propostas/bloco-3.2-camada-b-briefing.md` — o que a Camada B recebeu.
6. Na Máquina: `memoria/missoes/fase2-eco-camada-a/` — `prompt.txt`,
   `passada_{1,2,3}.txt` (saída crua das 3 passadas de Regra 8), `regra8-3-passadas.md`,
   `bateria-clone.md` (v1), `bateria-v2.md` (v2). Fora do repo público, sem remote.
7. `REGRAS.md` — "Cadeia de auditoria em camadas", "Carregar e formatos" (`sync:` —
   três formas), "Continuidade mecânica (TES)". `PROJETO.md` — "Estado dos bugs e
   dos testes" (linha TES-002). `scripts/perimetro.sh`, `.githooks/pre-commit`.

## O que você precisa verificar na Máquina (não aceitar de nenhum texto)

### Sobre os hashes e a aplicabilidade
- `sha256sum` dos dois `.diff` bate com o alegado? `wc -l` do v2 = 145?
- `git apply --check propostas/bloco-3.2-eco-mecanizado.diff` contra o HEAD vivo:
  limpo? (Se o HEAD andou, rode contra o que está vivo e diga qual é.)
- `git diff` entre v1 e v2 (aplique cada um a um clone e compare, ou leia os dois
  `.diff`): a emenda mudou **só** o que o changelog diz, ou mexeu em mais coisa?

### Sobre os 4 achados que a Camada B levantou (eram reais?) e a emenda (resolveu?)
Para cada um, reproduza na Máquina num **clone descartável** com o v2 aplicado:

- **Achado 1** — v1 dava `sync: PASS` + exit 0 com árvore suja? (aplique o **v1**
  num clone, suje `REGRAS.md` sem commitar, rode). O **v2** agora dá `sync: FALHA`
  + exit 1 no mesmo cenário? Cobre o caso **staged** (`git add` sem commit)?
- **Achado 2** — v2 imprime `sync:` minúsculo e `não verificado` com espaço, batendo
  as "três formas" de `REGRAS.md`? Compare `grep` do texto do script com as linhas
  ~205–211 de `REGRAS.md`.
- **Achado 3** — rode o v2 com `LC_ALL=C bash scripts/estado_para_eco.sh`: o campo
  TES-002 sai íntegro (sem byte multibyte cortado)? Confirme com `xxd`/`hexdump`.
  `C.UTF-8` existe nesta Máquina (`locale -a`)?
- **Achado 4** — o campo TES-002 do v2 **não** contém `e1d1a`? Rode e `grep`.

### Sobre a Camada B — ela alegou sem verificar em algum ponto?
- A Camada B disse "reproduzi na Máquina" para o Achado 1. As `Lacunas` do parecer
  dela (ramo `?/?` não exercido; não rodou as passadas qwen; sem `shellcheck`) são
  honestas ou escondem um furo?
- Ela leu as 3 passadas de Regra 8 "só os blocos de conclusão via `tail`". Você:
  leia os `passada_{1,2,3}.txt` inteiros (têm lixo de terminal do `ollama` — filtre).
  A convergência de Q1 e Q3 que o `regra8-3-passadas.md` alega existe mesmo no
  corpo do `thinking`, ou alguma passada raciocina para o lado oposto e só
  conclui do lado "certo"? O Achado 8 (paráfrase entre aspas no
  `regra8-3-passadas.md`) procede?

### Sobre a Camada A — o changelog da emenda é fiel ao `.diff` v2?
- Cada item do "Emenda v1 → v2" no `.md` corresponde a uma mudança real no `.diff`?
- Alguma mudança no `.diff` v2 que o changelog **não** menciona?
- O script v2 continua read-only? (`git status` limpo após N execuções num clone.)
- `bash -n` limpo. Sem `shellcheck`? Faça leitura manual à procura de: `set -e` +
  `$(( ))` que avalia 0; globs; `paste -sd' '` com nome de arquivo com espaço;
  `sed`/`grep` não-POSIX que sobraram; o novo `git -c core.quotepath=false diff`
  se comporta com o nome `MEMÓRIAS.md` (acento)?

## O que você deve entregar (REGRAS, "O que cada camada deve entregar")

1. Verificação na Máquina antes de afirmar (hash, git, grep, execução) — cada
   alegação sua ancorada num comando que você rodou.
2. Citação exata, nunca paráfrase entre aspas.
3. Hedge sobre o que o Humano não pode verificar a partir do seu texto.
4. Não tocar canônico. `APROVADO-` é decisão do Humano.
5. Registro do que a Camada A **e** a Camada B **acertaram**, não só do que erraram.
6. (A confirmação pós-push é etapa posterior — não sua.)

## Posição final

Feche com uma das três:
- `PRONTO PARA O HUMANO` — v2 resolve o que a Camada B levantou, sem furo novo; o
  Humano decide o `APROVADO-`.
- `CONDICIONAL — <o que ainda falta>` — precisa de outra rodada de emenda.
- `REJEITA — <por quê>` — problema de fundo que emenda não conserta.

Escreva em `/home/orusoua/agata/propostas/bloco-3.2-camada-c-parecer.md` (só
escrever; NÃO `git add`/commit). Assinatura única no fim. No relatório final para
quem te chamou: a posição, a contagem de achados por severidade, e os achados mais
importantes em uma linha cada. Não invente resultado de teste.
