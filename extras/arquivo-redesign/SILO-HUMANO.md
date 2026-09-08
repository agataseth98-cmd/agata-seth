# SILO-HUMANO — decisões que ficam com o Humano, resolvidas na implementação

Não é canon. É onde uma decisão que **é do Humano** e que fica **mais prática de tomar
com o sistema real na frente** espera — em vez de travar o trabalho agora ou de eu
escolher por ele. Cada item diz: o que decidir, a informação que falta, e **quando**
(qual passo da implementação) ele resolve.

Regra: eu **não** aplico nada de um item daqui sozinho. Quando o passo de implementação
chegar, eu trago a informação que faltava, ele decide, e aí sim vai para o LOG + (na
Fase 8) para o canon.

---

## H-1 — Régua do controle P-12 (backup verificável por recurso)

**Decisão dele:** R1 (quais recursos entram, em que severidade) · R2 (N dias de
frescor) · R3 (comportamento com o HD ausente — já desenhado como PARCIAL).
Detalhe e recomendação: `redesign/fase7-hd/REGUA-P12.md`.

**Por que fica aqui (palavra do Humano, 02/09/2026):** *"preciso de mais informações por
aqui, é mais prático para os recursos do sistema."* — decidir N dias e "quais recursos"
sem os snapshots restic reais na frente é chutar. Com o HD montado e a primeira passada
de backup feita, dá para ver o tamanho real, o tempo de cada `restic backup`, e o ritmo
plausível de ida ao trabalho — e aí a régua sai calibrada, não estimada.

**Informação que falta (junta-se durante a implementação):**
- tamanho e tempo real do `restic backup` de cada um dos 4 artefatos (GGUF MoE 18G;
  whisper base 81M / small 245M; e5-small 262M) — o runbook
  `redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md` já coleta isso.
- se o blob do `rlm` entra por `ollama cp`, `sudo restic` ou re-tag do snapshot
  `c19275ec` (muda o custo de manter fresco).
- ritmo real de acesso ao HD nas primeiras semanas (define se N=14 é folgado ou apertado).

**Quando:** durante o **P7-03** (HD presente, passada de backup feita). O `.diff`
(`redesign/propostas/p12-backup-verificavel.diff`) já está pronto e testado — só as 3
linhas `P12_*` e o `APROVADO-p12-backup-verificavel` esperam a régua calibrada.

**Estado:** aberto. Última atualização: 2026-09-02 (chat 4).
