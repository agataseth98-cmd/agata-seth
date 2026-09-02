# REGUA do P-12 — a decisao e sua (Humano)

O P-12 e o controle novo do `perimetro.sh` que a Fase 7 pede: *"recurso no manifesto sem
backup verificavel < N dias = FALHA"*. O `.diff` ja esta escrito
(`redesign/propostas/p12-backup-verificavel.diff`) e testado. Falta **voce decidir a
regua** — tres numeros/listas. Este documento explica cada um: o porque, a minha
recomendacao, e como voce confere depois.

O controle inteiro depende de so tres linhas no `perimetro.sh` (o `.diff` ja as traz com a
recomendacao; se voce concordar, e zero trabalho extra — so criar o `APROVADO-`):

```sh
P12_N_DIAS=14
P12_FALHA_SEM_BACKUP="rlm-qwen3-8b-teste:latest multilingual-e5-small-int8"
P12_AVISO_SEM_BACKUP="qwen3-30b-a3b whisper-base-int8-ov whisper-small-int8-ov"
```

---

## R1 — quais recursos entram, e em que severidade

**O problema:** o `models/manifest.json` tem 9 recursos. Alguns se reconstroem com um
comando (`ollama pull qwen3:4b`); outros sao trabalho local que, num disco morto, **some
para sempre**. Se o P-12 tratar todos igual, ele fica vermelho o tempo todo por causa de
modelos que voce baixa de novo em 5 minutos — e "vermelho que fica sempre vermelho vira
vermelho ignorado" (a mesma logica do canon sobre "verde que ninguem questiona").

**Como eu separei (principio-espelho: a espinha e o sistema; modelo publico e config
reconstruivel, nao estado precioso):**

| recurso | origem | reconstroi sem backup? | onde eu poria |
|---|---|---|---|
| `rlm-qwen3-8b-teste:latest` | build local / tag custom (fine-tune LoRA) | **NAO** — e trabalho seu | **FALHA** |
| `multilingual-e5-small-int8` | `optimum-cli export openvino` local; **servido em producao** (`:20134`); o proprio manifesto nota que o export e fragil ("so o export de Whisper que quebra no optimum 2.3.0") | em tese sim, mas toolchain-sensivel e esta no ar | **FALHA** |
| `qwen3-30b-a3b` (GGUF MoE) | HF publico `unsloth/...`, **sha256 fixado**; o manifesto ja diz "NAO precisa de snapshot restic (publico, hash fixado)" | sim (download HF) | **AVISO** (vale um snapshot porque HF some as vezes e o re-download e 17 GB) |
| `whisper-base-int8-ov` / `whisper-small-int8-ov` | HF publico `OpenVINO/...`, `snapshot_download` | sim | **AVISO** |
| `qwen3:4b`, `qwen3.5:9b`, `nomic-embed-text`, `qwen3.5-9b-64k` | ollama registry (o `-64k` e o blob publico + Modelfile no manifesto) | sim — `ollama pull` / `models/RECONSTRUCAO.md` | **ISENTO** |

- **FALHA** = soma no placar de FALHA do `perimetro.sh`, **trava o commit** (mesma
  severidade do P-8). So dispara quando o **HD esta montado** e o recurso realmente nao tem
  snapshot do conteudo atual < N dias.
- **AVISO** = imprime a linha, **nao trava** nada.
- **ISENTO** = nem aparece.

**Recomendacao:** as listas da tabela acima (ja no `.diff`).
**Alternativa mais dura, se voce quiser:** mover os tres de AVISO para FALHA — ai todo
artefato nao-Ollama precisa de snapshot fresco para o commit passar. Mais seguro, mais
atrito.

## R2 — N dias (`P12_N_DIAS`)

**O que e:** quao velho um snapshot pode ser antes do P-12 reclamar dele.

**Tensao:** o HD so aparece quando voce vai ao trabalho — na pratica, uma vez a cada
poucos dias ou uma vez por semana. Se N for pequeno (ex. 2 dias, como o limiar do P-6), o
P-12 fica cronicamente vermelho/PARCIAL so porque o disco nao estava aqui. Se N for grande
demais (ex. 60), ele nao pega "voce reconstruiu o e5-small e esqueceu de salvar".

Os artefatos em questao **mudam raramente** — so quando um trabalho tipo P2/P3 os
reconstroi. Entao o snapshot fica "velho" mais por ritmo de ida ao trabalho do que por
mudanca real.

**Recomendacao: `N = 14`.** Uma ida ao trabalho por semana mantem verde com folga; duas
semanas sem backup de um artefato que mudou e sinal legitimo.

## R3 — o que o P-12 faz quando o HD NAO esta montado

**Ja decidido no `.diff` assim (nao e knob, e desenho — mas voce manda mudar se quiser):**

- **HD ausente:** o P-12 **nunca FALHA um commit.** Um disco que esta no trabalho nao e
  motivo para travar o hook. Ele le o cache
  `~/.agata-backup-staging/p12-cobertura.json` (que a passada de backup escreve quando o HD
  **esta** presente) e reporta **PARCIAL** com a data de cobertura mais velha. Hoje, sem
  cache ainda, ele diz `cobertura mais velha: nunca` e segue como PARCIAL.
- **HD montado:** ai sim e autoridade — para cada recurso da lista FALHA sem snapshot do
  `sha256` atual < N dias, **FALHA**; para os da lista AVISO, **AVISO**; e reescreve o
  cache.

Isso e o que casa com a sua ordem: *"quando nao [tem HD], juntamos informacoes; quando o
HD vier, a gente salva."* O P-12 PARCIAL e a "informacao juntada"; o P-12 verde exige o
"salvar".

---

## Como voce aprova

1. Le o `.diff`: `redesign/propostas/p12-backup-verificavel.diff`.
2. Se concorda com R1/R2/R3 como estao: cria o arquivo vazio
   `redesign/propostas/APROVADO-p12-backup-verificavel` (isso == sua aprovacao).
3. Se quer outros valores: me diz os tres (ou edita as 3 linhas do `.diff`) antes do
   `APROVADO-`.
4. A aplicacao de verdade em `scripts/perimetro.sh` e na **Fase 8** (ou antes, com "vai"
   explicito). Ate la o P-12 nao roda — o `perimetro.sh` de `main` esta intocado.

## Como conferir depois que aplicar

- `bash scripts/perimetro.sh` — a secao `=== P-12 ===` aparece; com o HD fora, veredito
  `PARCIAL`; com o HD e tudo salvo, `OK`; com o HD e um artefato da lista FALHA sem
  snapshot, `FALHOU` e o commit trava.
- `RESULTADO GERAL` passa a contar 11 controles em vez de 10.
