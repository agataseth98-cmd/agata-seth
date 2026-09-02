# redesign/propostas/ — quarentena P-8 do redesenho

Aqui ficam os `.diff` de mudanca de COMPORTAMENTO em arquivos que a quarentena P-8
protege (`scripts/*`, `.githooks/*`, `REGRAS.md`, `PROJETO.md`, `config/*`) e que o
redesenho precisa tocar.

**Nada aqui esta aplicado.** Um `.diff` so entra em vigor quando:

1. o Humano revisa o `.diff`;
2. o Humano cria o arquivo `APROVADO-<nome>` neste diretorio (== aprovacao, uso unico);
3. na **Fase 8** (ou antes, com "vai" explicito do Humano e risco assumido), o `.diff` e
   aplicado a `main`/arvore de verdade pelo processo normal, e o par
   `.diff` + `APROVADO-<nome>` acompanha o commit que o P-8 do `perimetro.sh` exige.

Enquanto o redesenho vive no branch `redesign` sob estado de excecao, o P-8 do
`perimetro.sh` **nao** dispara (nao estamos com `scripts/*` staged). Estes arquivos sao
**preparacao**: o trabalho feito enquanto o HD nao esta disponivel ("juntamos
informacoes; quando o HD vier, a gente salva" — Humano, 02/09/2026).

## Conteudo

| arquivo | toca | o que muda | estado |
|---|---|---|---|
| `p12-backup-verificavel.diff` | `scripts/perimetro.sh` | acrescenta o controle **P-12** (recurso do manifesto sem backup restic verificavel < N dias) | aguarda a **regua do Humano** (`redesign/fase7-hd/REGUA-P12.md`) + `APROVADO-p12-backup-verificavel` |
| `cifrar-env.diff` | `scripts/cifrar_env.sh` | quando o repo restic esta alcancavel, poe o `.gpg` do `~/.hermes/.env` DENTRO do repo restic (`restic backup --tag agata-env`), nao so um `cp` solto que o `restic check` nunca ve | aguarda HD + `APROVADO-cifrar-env` |

## Regua da Fase 8 (quando aplicar de verdade)

O `.diff` foi escrito contra o blob atual do arquivo em `main`
(`scripts/perimetro.sh` @ `70387a97`, `scripts/cifrar_env.sh` @ `670dc6ad`). Se `main`
mudar esses arquivos antes da Fase 8, rebasear o `.diff` antes de aplicar — o P-8 exige
que o `.diff`, aplicado ao HEAD do arquivo, reproduza **byte a byte** o conteudo staged.
