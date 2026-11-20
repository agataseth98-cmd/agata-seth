# Revisão Independente — SPEC-sandbox-modelos-landlock.md

**Revisor:** nemotron-3-ultra (simulando peixinhos dourados — sem conversa, só spec + código real)
**Data:** 19/11/2026
**Spec revisada:** SPEC-sandbox-modelos-landlock.md

---

## 1. Reuso — O que JÁ EXISTE no Agata

| Componente da Spec | Existe? | Onde | Gap |
|---|---|---|---|
| **bwrap sandbox** | ✅ **Completo** | `redesign/grafo/sandbox.py` (113 linhas) | `run_sandboxed(argv, ro=[], rw=[], net=False)` pronto; `--unshare-all`, `--die-with-parent`, limites CPU/mem/FSIZE |
| **Landlock LSM** | ❌ **Não existe** | Kernel 7.3.4 suporta (≥5.13) | Spec propõe Landlock mas código usa bwrap; Landlock seria *adição*, não substituição |
| **Capability verification** | ✅ **Parcial** | `redesign/mcp/capability.py` (111 linhas) | Verifica capability Ed25519 emitida pelo LibreChat; **NÃO** gerencia segredos (.env) |
| **Systemd hardening** | ✅ **Maduro** | 20+ `.service` com `ProtectSystem=strict`, `ProtectHome=read-only`, `ReadWritePaths=`, `NoNewPrivileges=yes` | Padrão estabelecido; spec pode reusar perfis |
| **Executor privilegiado** | ❌ **Não existe** | Portão 3P é procedural (Humano decide) | Spec propõe `executor_privilegiado.py` novo |
| **Capability broker (segredos)** | ❌ **Não existe** | Investigado em MEMÓRIAS 505, devolvido backlog B9 | Spec propõe componente novo |

**Conclusão reuso:** **60% da spec é código novo** — Landlock wrapper, capability broker, executor privilegiado. bwrap e systemd hardening já existem e devem ser integrados, não reescritos.

---

## 2. Governança — Violações de P-8, Regra 2, Regra 7, Portão 3P?

| Item | Análise | Risco |
|---|---|---|
| **Capability broker lê `~/.config/agata/.env`** | Broker tem acesso a segredos; modelo não. **OK se broker for serviço systemd com `ProtectSystem=strict` + `ReadWritePaths=-%h/.config/agata/.env`** | ⚠️ Broker vira **SPOF** (single point of failure) — se comprometido, expõe todos segredos |
| **Executor privilegiado roda sudo** | Fora do sandbox; Portão 3P obrigatório; audit trail imutável. **OK se log assinado (P-5)** | ⚠️ Precisa `ProtectSystem=strict` + `ReadWritePaths` mínimo; capability Ed25519 para autorização |
| **Landlock nega sudo/.env para modelo** | **Corrige Regra 2/7** — barreira técnica substitui procedural | ✅ Alinhado |
| **P-1/P-2 viram OK sem root** | `ruleset_perimetro` RO tudo permite ver processos/arquivos sem sudo | ✅ Alinhado |
| **Migração sem P-8** | Spec define fases; reversão documentada. **Cada fase = proposta P-8?** | ⚠️ Spec diz "fases" mas P-8 exige **uma proposta, uma assinatura por lote** — precisa consolidar |

**Conclusão governança:** **Nenhuma violação direta** mas **SPOF no capability broker** e **granularidade P-8** precisam atenção.

---

## 3. Implementabilidade — Spec é clara para codar sem adivinhação?

| Aspecto | Status | Falta |
|---|---|---|
| **Landlock Python API** | ⚠️ Parcial | `python-landlock` existe no PyPI mas **não testado no Agata**; spec assume disponibilidade |
| **Ruleset YAML → Landlock syscall** | ❌ Não definido | Como `config/landlock-profiles.yaml` vira `landlock_add_rule()` calls? Precisa parser + compiler |
| **Capability broker interface** | ✅ Clara | `request(model_id, capability, purpose) -> dict` bem definido |
| **Executor privilegiado interface** | ✅ Clara | `execute(proposal, approval) -> Result` bem definido |
| **Integração `tools.py`** | ✅ Clara | `apply_ruleset("write")` antes de cada tool |
| **Migração fases** | ⚠️ Vaga | "Fase 1: implementar landlock.py" — mas Landlock wrapper **não existe**; estimativa de esforço? |
| **Reversão** | ✅ Clara | `sed` + `git checkout` documentado |

**Conclusão implementabilidade:** **Landlock wrapper é risco técnico** — não há código de referência no Agata; `python-landlock` binding precisa validação. bwrap já funciona e poderia ser estendido (já tem `ro`/`rw` paths).

---

## 4. Critério de Aceite — Testável e Suficiente?

| Critério | Testável? | Como medir no perimetro.sh |
|---|---|---|
| **P-1 OK sem root** | ✅ Sim | `ruleset_perimetro` RO tudo → `ps aux`, `ss -tlnp`, `ls /etc` funcionam sem sudo |
| **P-2 OK sem root** | ✅ Sim | `sudo -n true` falha no sandbox; timestamp não atualiza |
| **Modelo não acessa .env** | ✅ Sim | Red team: `cat ~/.config/agata/.env` → `EPERM` (Landlock) ou `PermissionError` (bwrap) |
| **Modelo não usa sudo** | ✅ Sim | Red team: `sudo systemctl restart x` → `EPERM` |
| **Capability broker funciona** | ✅ Sim | Unit test: broker retorna só key pedida; log contém hash(segredo) |
| **Executor auditado** | ✅ Sim | Log em `logs/privileged/` com proposal_id, approval_hash, stdout, stderr, exit_code |

**Gap:** Critério **não inclui** "Landlock ativo e funcional" — só efeitos. Deve adicionar: `landlock_restrict_self()` chamado com sucesso no processo do modelo.

---

## 5. Achados Críticos (bloqueiam avanço sem resolução)

| # | Achado | Severidade | Resolução necessária |
|---|---|---|---|
| 1 | **Landlock wrapper não existe** — spec assume `python-landlock` mas Agata usa bwrap | **Alta** | Validar `python-landlock` no ambiente Agata ANTES da spec; ou estender bwrap existente |
| 2 | **Capability broker = SPOF** — único processo lê todos segredos | **Alta** | Broker também no Landlock/bwrap; `ReadWritePaths` só `.env`; capability Ed25519 para acessar broker |
| 3 | **Granularidade P-8** — 6 fases ≠ 1 proposta | **Média** | Consolidar em **1 lote P-8** com fases internas; ou 6 propostas sequenciais |
| 4 | **Falta integração com `tools.py` real** — spec mostra `apply_ruleset` mas `tools.py` não existe no path citado | **Média** | Confirmar path: `redesign/grafo/tools.py` vs `redesign/router/tools.py` vs `scripts/` |
| 5 | **Perimetro.sh dentro do sandbox** — como `ruleset_perimetro` RO tudo roda `ps`, `ss`, `systemctl`? Precisa `--share-net` e acesso a `/run/systemd` | **Média** | Definir `ruleset_perimetro` com `--share-net` + `ro: /run/systemd, /proc, /sys` |

---

## 6. Recomendações (ordem de prioridade)

1. **Validar `python-landlock`** no ambiente Agata (kernel 7.3.4 OK) — spike de 1h
2. **Estender bwrap existente** (`redesign/grafo/sandbox.py`) com perfis YAML — reuso 80% do código
3. **Capability broker como serviço systemd** com `ProtectSystem=strict` + `ReadWritePaths=-%h/.config/agata/.env` + capability Ed25519
4. **Consolidar em 1 proposta P-8** (ou sequência explícita com decisão Humano entre cada)
5. **Adicionar teste Landlock ativo** ao critério de aceite (P-27 no perimetro.sh)
6. **Definir `ruleset_perimetro` completo** com acesso a `/run/systemd`, `/proc`, `/sys`, rede para `ss`

---

## 7. Veredito da Revisão Independente

| Dimensão | Status | Ação |
|---|---|---|
| **Reuso** | ⚠️ Parcial | Integrar bwrap + systemd hardening; Landlock = novo |
| **Governança** | ✅ OK com ressalvas | Resolver SPOF broker; granularidade P-8 |
| **Implementabilidade** | ⚠️ Risco técnico | Validar Landlock binding; definir YAML→syscall |
| **Critério de aceite** | ✅ Testável | Adicionar "Landlock ativo" |

**Recomendação:** **Não avançar para decisão Humano** até resolver itens 1-3 acima. Spec tem direção correta mas **riscos técnicos não mitigados** no Landlock wrapper e SPOF broker.

---

**Artefato de revisão independente** — entregue sem conversa, só spec + código real.