# Proposta sandbox-fase1-19-11 — contenção Landlock (fase 1: o mecanismo e a prova)

Plano aprovado em revisão: `PLANO-IMPLEMENTACAO-sandbox-launcher-v2.md` (Área de trabalho), escrito pela Seth (nemotron-3.5-super-vl via OpenCode) a partir da auditoria do Opus de 19/11. Fase 1 só cria o mecanismo e prova; nada passa a usá-lo ainda.

**O quê:**
- `redesign/mcp/landlock.py`: Landlock por `ctypes`, só Python padrão. ABI lido em execução (`LANDLOCK_CREATE_RULESET_VERSION`; na Máquina, ABI 11). Allow-only: o ruleset trata todos os direitos da ABI e o que não está numa regra fica negado. `PR_SET_NO_NEW_PRIVS` antes de `restrict_self`. Direitos de arquivo para regra sobre arquivo.
- `config/containment-profiles.yaml`: perfis declarativos; `~/.config/agata` fora de todos.
- `redesign/mcp/test_landlock.py`: 9 testes, sem skip. Em processo filho contido: abrir `~/.config/agata/.env` dá PermissionError (o pai não lê o arquivo); escrever fora do permitido dá PermissionError; dentro do permitido funciona; números do YAML batem com as constantes.

**Medido:** 9 passed (rodado pelo agente e pelo Opus); CI local TUDO OK.

**História do lote (para o placar):** a Seth implementou e afirmou duas vezes que o kernel dava EINVAL — falso; o Opus provou que funciona; os bugs eram do wrapper (flags no lugar do tamanho, argumentos trocados em restrict_self, modo VERSION com attr). Consertado por agata-dev (Sonnet).

**Fora:** rede, campo `scoped`, lançador, broker e executor (fases seguintes do plano).

**Reversão:** `git revert` do commit de aplicação.

**Modelo:** nemotron-3.5-super-vl (Seth) + Sonnet 5.5, orquestrados e revisados pelo Opus 5.5.
