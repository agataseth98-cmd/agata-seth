# fecha-ancora-pos-canon — companheiro do `.diff`

**Rascunho versionável. SEM `APROVADO-`.** É P-8 (muda comportamento: `.githooks/post-commit` +
`scripts/perimetro.sh`). Não autoriza nada por si — precisa do portão das três perguntas,
de `propostas/APROVADO-fecha-ancora-pos-canon` criado pelo Humano, e de uma entrada
MEMÓRIAS (303) + `ONDE_ESTAMOS.md` no mesmo commit que aplicar.

## De onde veio

Ficou **na árvore de trabalho, não-commitada**, deixada por uma sessão interrompida
(reboot acidental — a máquina tem histórico disso). Encontrada ao `carregar` em
31/08/2026. Congelada aqui verbatim para não se perder e para sair da árvore
(estava viva, meio-aplicada, sob risco de entrar num commit por engano).

- Diff congelado: `fecha-ancora-pos-canon.diff` — `sha256` `49009a9a` (5328 B).
- `git apply --check` limpo contra o `.githooks/post-commit` / `scripts/perimetro.sh`
  do HEAD `233ac2c` (verificado em 31/08/2026, na Máquina).

## O que faz

"Opção 2, forma A" do plano (item N / BLOCO 0.0, `plano-execucao-backlog.md`):

1. **`.githooks/post-commit`, passo 4** — se o commit recém-criado tocou canon
   (`REGRAS.md` / `PROJETO.md` / `MEMÓRIAS.md`), faz **um commit de follow-up** que só
   toca `PROMPT_CARREGAMENTO.md`, apontando a âncora de SHA para o próprio commit de
   canon. Resultado: defasagem de canon = 0 (contra a defasagem de 1 commit que o
   `pre-commit` deixa por auto-referência). Guarda de recursão: o commit de âncora não
   toca canon, então a segunda passada para sozinha. Cada falha é AVISO alto em
   stderr, nunca silêncio; o commit de conteúdo já está feito e intacto.
2. **`scripts/perimetro.sh`, P-11** — se o HEAD toca canon e **não** é seguido pelo
   commit de âncora, AVISA (nunca falha — mesma doutrina de P-9). Fecha a
   falha-silenciosa que fez a "forma B" ser descartada.

## Pontos que o Humano precisa pesar antes de `APROVADO-`

- **`lacuna`:** não há entrada MEMÓRIAS nem `APROVADO-` registrando que a "forma A" foi
  a escolhida (só os comentários do código e o plano-rascunho a afirmam, citando a
  auditoria em nuvem Claude Opus 5). Não verificável na Máquina.
- **É mesmo necessário?** A entrada (302) já reescreveu o detector para uma checagem de
  defasagem em 3 degraus que **tolera âncora 1 commit atrás** como estado normal. A
  "forma A" leva a defasagem a 0, mas ao custo de **1 commit automático extra por
  commit de canon** — dobra a contagem de commits do repo ao longo do tempo. Pode ser
  gold-plating sobre um problema que (302) já resolveu no nível certo.
- **Portão das três perguntas** (a responder com o Humano):
  1. *Reversível sozinho?* — sim: `git revert` de 2 hunks, mais reverter os commits de
     âncora que já tiverem sido criados; nada apagado.
  2. *O que mais toca?* — todo commit futuro de canon passa a gerar um commit-filho
     automático; `perimetro.sh` ganha um 11º controle; `PROMPT_CARREGAMENTO.md` é
     reescrito 2x por ciclo em vez de 1x.
  3. *Saberia se quebrasse?* — sim, por desenho: AVISO em stderr no post-commit +
     P-11 no `perimetro.sh`. Foi essa exigência que derrubou a forma B.

## Se aprovado, o fluxo é

`APROVADO-fecha-ancora-pos-canon` (Humano) → `git apply fecha-ancora-pos-canon.diff` →
`perimetro.sh` verde → move o par para `propostas/aplicadas/` no mesmo commit →
entrada MEMÓRIAS (303) + `ONDE_ESTAMOS.md`.
