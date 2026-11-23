# Proposta reaproveita-23-11 — duas propostas órfãs, rebaseadas no main (uma assinatura)

Origem: limpeza de branches de 23/11, pedida pelo Humano ("pode reaproveitar já faça e sanitize o sistema"). Das 41 branches remotas, estas eram as duas únicas com conteúdo não implementado nem registrado.

**1. Skill agata-voz, seção 3a** (de `proposta/agata-voz-piper-chamada-20261107`, nunca registrada nem assinada). Em chamada num app com voz própria, o modelo silencia só a saída do app (ou pede ao Humano e espera), fala pelo Piper só o texto final, não pede autorização duas vezes e descreve o código de saída do `agata_falar.py` com precisão (0 não prova que o Humano ouviu; 3 e 4 = não falou). Texto idêntico ao de 07/11; só entrou como seção numerada 3a, porque a skill foi renumerada depois. Conferido: `--preparar`, `--sem-tocar` e os retornos 3 e 4 existem no script atual.

**2. Spec de telemetria experimental da avaliação** (de `proposta/telemetria-spec-v1-20261117-r2`). Só spec (`redesign/avaliacao/spec/spec.md`, `brainstorm.md`, `decision.md`); sem código, sem instrumentação contínua, sem mudança de rota. Aplicou sem conflito.

**Medido:** `anchor.py . redesign/avaliacao` → ANCHOR: OK; `bash scripts/ci_sdd_local.sh` → CI LOCAL: TUDO OK; `git apply --check` em cópia limpa do origin/main → OK.

**Não medido:** efeito da seção 3a numa chamada real; a implementação futura da telemetria.

**Reversão:** `git apply -R propostas/aplicadas/reaproveita-23-11.diff`.

Assinatura: bash scripts/aprovar.sh reaproveita-23-11
