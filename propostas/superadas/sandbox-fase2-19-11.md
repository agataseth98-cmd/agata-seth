# Proposta sandbox-fase2-19-11 — lançador `agata-run`: uma porta única para todas as plataformas

Pedidos do Humano, 19/11/2026: sandbox "da maneira correta e elegante"; Codex "igual a você, mesmas ferramentas e mesma funcionalidade"; "o usuário final não pode perceber quem está determinando a ação". Plano escrito pela Seth (nemotron via OpenCode), auditado pelo Opus com 3 ajustes; implementação Sonnet; revisão Opus.

**O quê:**
- `scripts/agata_run.py` + `scripts/agata-run`: abre Claude Code, Codex, OpenCode ou Gemini com o mesmo estado (hidratação), o mesmo turno (`turno.py`) e contenção Landlock (fase 1) aplicada ao processo filho; fallback bwrap ativo; sem Landlock nem bwrap recusa rodar (código 3). `AGATA_LANDLOCK=0` desliga (aviso visível). `--dry-run` mostra o plano.
- Rede por porta (Landlock ABI 4): padrão 53, 80, 443, 11434, 20127, 20134 (`AGATA_RUN_PORTAS`). Limite declarado: porta, não endereço.
- `scripts/test_agata_run.py` (18 testes, processo real) + passo no `scripts/ci_sdd_local.sh`.

**Medido:** 27 testes (lançador + landlock) rodados pelo Opus; CI local TUDO OK (agente). Prova: o filho recebe PermissionError ao abrir `~/.config/agata/.env` e ao escrever fora; `AGATA_LANDLOCK=0` libera; fallback bwrap rodou de verdade.

**Não medido / fica para depois:** uso diário com as plataformas reais (critérios 3–6 do plano); `.claude.json` (rename em ~) ; instalar em ~/.local/bin; broker e executor (fase 3).

**Reversão:** `git revert`; nada é instalado nem ativado sozinho.

**Modelo:** Seth/nemotron (plano), Sonnet 5.5 (código), Opus 5.5 (orquestração e revisão).
