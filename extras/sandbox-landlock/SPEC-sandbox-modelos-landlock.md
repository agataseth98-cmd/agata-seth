# Spec: Sandbox Landlock para Modelos — Capability-Based Access Control

**Status:** Draft para revisão independente (peixinhos dourados)
**Decisão Humana registrada:** cache 583
**Origem:** SDD time de inovação — elefante (este modelo) + entrevista Humano

---

## 1. Problema (evidência)

| Evidência | Fonte |
|---|---|
| Modelos têm acesso físico a `sudo` e `~/.config/agata/.env` — barreira é só procedural (Regra 2/7) + detecção pós-fato (P-1, P-2) | Auditoria 19/11/2026 |
| P-1 PARCIAL: "sem root, não enxerga todos processos — controle vê menos do que deveria" | perimetro.sh medido agora |
| P-2: verifica sudoers timestamp mas não impede uso | perimetro.sh |
| Nenhum sandbox obrigatório, capability drop, namespace isolado, SELinux/AppArmor para modelos | Auditoria 19/11 |
| Hermes `code_execution` já usa sandbox com env filtrada mas só para execução de código, não para o modelo todo | MEMÓRIAS-FRIO-2026-09-06-6:297 |
| `redesign/grafo/sandbox.py` já implementa `bwrap --unshare-all` para tools do grafo | ROADMAP P4-02, STATUS.md |
| Serviços systemd já usam `ProtectSystem=strict`, `ProtectHome=read-only`, `ReadWritePaths=` | MEMÓRIAS-FRIO-2026-09-06-3:217 |
| Capability broker investigado em 505 e devolvido como backlog B9 — não implementado | MEMÓRIAS 505, INDICE_MEMORIAS 1170 |

---

## 2. Decisões do Humano (entrevista)

| Decisão | Escolha | Rationale |
|---|---|---|
| **Escopo** | Apenas ferramentas de escrita (write, edit, bash com escrita) | Leitura livre; contenção onde está o risco |
| **Segredos** | Mediador de capability (capability broker) | Modelo pede → mediador valida → injeta só o necessário; modelo nunca vê segredo |
| **Mecanismo** | Landlock LSM (Linux 5.13+) | Mais granular que seccomp/bwrap; ruleset por thread; kernel-enforced |
| **Sudo** | Portão das 3 perguntas mediado | Modelo propõe → Humano aprova → executor privilegiado roda fora do sandbox com audit trail |
| **Critério de aceite** | P-1/P-2 viram OK sem root | Sandbox permite que perimetro.sh veja tudo sem sudo |

---

## 3. Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    MODELO (processo non-root)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Leitura   │  │  Escrita    │  │   Bash      │             │
│  │  (livre)    │──▶│  (sandbox)  │──▶│  (sandbox)  │             │
│  └─────────────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────────────────────┼─────────────────┼────────────────────┘
                          │                 │
                          ▼                 ▼
              ┌─────────────────────┐ ┌───────────────┐
              │  Landlock Ruleset   │ │  Landlock     │
              │  (ro: repo, config) │ │  Ruleset      │
              │  (rw: propostas/,   │ │  (rw: tmp,    │
              │   memoria/, logs)   │ │   no secrets) │
              └─────────────────────┘ └───────────────┘
                          │                 │
                          ▼                 ▼
              ┌─────────────────────┐ ┌───────────────┐
              │ Capability Broker   │ │ Privileged    │
              │ (mediador segredos) │ │ Executor      │
              │ • Valida pedido     │ │ (fora sandbox)│
              │ • Injeta só necessário│ │ • sudo via    │
              │ • Audit trail       │ │   Portão 3P   │
              └─────────────────────┘ └───────────────┘
```

### 3.1 Landlock Rulesets (por tipo de ferramenta)

| Ferramenta | Ruleset Landlock | Acesso |
|---|---|---|
| `read`, `grep`, `glob`, `task` (leitura) | **Nenhum** (livre) | RO repo + config |
| `write`, `edit` | `ruleset_write` | RO: repo, config<br>RW: `propostas/`, `memoria/`, `logs/` |
| `bash` (com escrita) | `ruleset_bash` | RO: repo, config<br>RW: `propostas/`, `memoria/`, `logs/`, `/tmp`<br>**NEGA**: `/etc`, `/root`, `~/.config/agata/`, `/usr/bin/sudo` |
| `bash` (leitura só) | `ruleset_bash_ro` | RO: tudo exceto segredos |

### 3.2 Capability Broker (mediador de segredos)

```python
# redesign/mcp/capability_broker.py (novo)
class CapabilityBroker:
    """
    Modelo NUNCA lê ~/.config/agata/.env
    Modelo pede capability → Broker valida → Injeta via env temporária no subprocesso
    """
    CAPABILITIES = {
        "openrouter": ["OPENROUTER_API_KEY"],
        "gemini": ["GEMINI_API_KEY"],
        "discord": ["DISCORD_TOKEN"],
        "restic": ["RESTIC_PASSWORD", "RESTIC_REPOSITORY"],
        "obsidian": ["OBSIDIAN_TOKEN"],
        "omniroute": ["OMNIROUTE_TOKEN"],
    }

    def request(self, model_id: str, capability: str, purpose: str) -> dict:
        # 1. Valida: capability existe? propósito legítimo? modelo autorizado?
        # 2. Lê segredo do .env (só broker tem acesso)
        # 3. Retorna dict com APENAS a variável necessária
        # 4. Loga: modelo, capability, purpose, timestamp, hash do segredo (não o valor)
        pass
```

### 3.3 Executor Privilegiado (Portão das 3 Perguntas)

```python
# scripts/executor_privilegiado.py (novo)
class PrivilegedExecutor:
    """
    Fora do sandbox. Só roda após:
    1. Modelo propõe ação (comando + justificativa)
    2. Humano aprova via Portão das 3 Perguntas (respostas por escrito)
    3. Executa com audit trail completo
    """
    def execute(self, proposal: PrivilegedProposal, human_approval: ApprovalRecord) -> Result:
        # Verifica approval record assinado
        # Executa comando via subprocess (sem shell injection)
        # Loga: stdout, stderr, exit_code, duração
        # Retorna resultado estruturado para o modelo
        pass
```

---

## 4. Implementação

### 4.1 Arquivos novos/modificados

| Arquivo | Tipo | Descrição |
|---|---|---|
| `redesign/mcp/landlock.py` | Novo | Wrapper Landlock: `LandlockRuleset`, `apply_ruleset()`, perfis pré-definidos |
| `redesign/mcp/capability_broker.py` | Novo | Mediador de segredos (substitui `redesign/mcp/capability.py` parcial) |
| `scripts/executor_privilegiado.py` | Novo | Executor sudo via Portão 3P |
| `redesign/grafo/tools.py` | Modifica | Integra `landlock.apply_ruleset()` antes de cada tool de escrita |
| `scripts/perimetro.sh` | Modifica | Roda dentro de `ruleset_perimetro` (RO tudo) para virar OK sem root |
| `config/landlock-profiles.yaml` | Novo | Perfis declarativos: `write`, `bash`, `bash_ro`, `perimetro` |
| `.githooks/pre-commit` | Modifica | Adiciona verificação: Landlock ruleset válido? |

### 4.2 Landlock Ruleset (exemplo YAML)

```yaml
# config/landlock-profiles.yaml
profiles:
  write:
    read_only:
      - "/home/orusoua/agata"
      - "/home/orusoua/.config/agata"  # só leitura, NÃO .env
    read_write:
      - "/home/orusoua/agata/propostas"
      - "/home/orusoua/agata/memoria"
      - "/home/orusoua/agata/logs"
    deny:
      - "/etc"
      - "/root"
      - "/home/orusoua/.config/agata/.env"
      - "/usr/bin/sudo"
      - "/usr/bin/systemctl"

  bash:
    read_only:
      - "/home/orusoua/agata"
      - "/home/orusoua/.config"
    read_write:
      - "/home/orusoua/agata/propostas"
      - "/home/orusoua/agata/memoria"
      - "/home/orusoua/agata/logs"
      - "/tmp"
    deny:
      - "/home/orusoua/.config/agata/.env"
      - "/usr/bin/sudo"
      - "/usr/bin/systemctl"
      - "/etc/systemd"

  perimetro:
    read_only:
      - "/"
    deny: []  # vê tudo, não escreve nada
```

### 4.3 Integração no fluxo de ferramentas

```python
# redesign/grafo/tools.py (trecho)
from redesign.mcp.landlock import apply_ruleset
from redesign.mcp.capability_broker import CapabilityBroker

async def write_file(path: str, content: str) -> ToolResult:
    # 1. Aplica ruleset Landlock para escrita
    apply_ruleset("write")
    # 2. Executa escrita (já contido pelo kernel)
    return await _do_write(path, content)

async def bash(command: str, writes: bool = False) -> ToolResult:
    ruleset = "bash" if writes else "bash_ro"
    apply_ruleset(ruleset)
    # Se comando pede segredo → capability broker
    if "OPENROUTER_API_KEY" in command or "GEMINI_API_KEY" in command:
        # Modelo NÃO deve ter segredo no comando
        # Redireciona para capability broker
        return ToolResult(error="Use capability broker para segredos")
    return await _do_bash(command)
```

---

## 5. Testes e Critérios de Aceite

### 5.1 Testes unitários (redesign/mcp/test_landlock.py)

| Teste | Esperado |
|---|---|
| `test_write_ruleset_blocks_etc_passwd` | `open("/etc/passwd", "w")` → `EPERM` |
| `test_write_ruleset_allows_propostas` | `open("propostas/test.diff", "w")` → OK |
| `test_bash_ruleset_blocks_sudo` | `subprocess.run(["sudo", "ls"])` → `EPERM` |
| `test_bash_ruleset_blocks_env_read` | `open("~/.config/agata/.env")` → `EPERM` |
| `test_perimetro_ruleset_sees_all_ro` | `os.walk("/")` completa sem erro |
| `test_capability_broker_injects_only_requested` | Broker retorna só `OPENROUTER_API_KEY`, não `GEMINI_API_KEY` |
| `test_capability_broker_logs_audit_trail` | Log contém modelo, capability, purpose, hash(segredo) |

### 5.2 Testes de integração (perimetro.sh)

```bash
# Adicionar ao perimetro.sh como P-27 (novo controle)
P-27: Landlock ativo para modelos
  - Tenta: sudo ls /root → deve falhar com EPERM
  - Tenta: cat ~/.config/agata/.env → deve falhar com EPERM
  - Tenta: write em /etc → deve falhar
  - Confirma: perimetro.sh roda com ruleset_perimetro → vê tudo, OK sem root
```

### 5.3 Critérios de aceite (decisão do Humano)

| Critério | Como medir | Pass/Fail |
|---|---|---|
| **P-1 vira OK sem root** | `bash scripts/perimetro.sh` → P-1 OK (não PARCIAL) | ✓/✗ |
| **P-2 vira OK sem root** | `bash scripts/perimetro.sh` → P-2 OK (não PARCIAL) | ✓/✗ |
| **Modelo não acessa .env** | Red team: modelo tenta `cat ~/.config/agata/.env` → EPERM | ✓/✗ |
| **Modelo não usa sudo** | Red team: modelo tenta `sudo systemctl restart x` → EPERM | ✓/✗ |
| **Capability broker funciona** | Modelo pede `openrouter` → recebe só `OPENROUTER_API_KEY` | ✓/✗ |
| **Executor privilegiado auditado** | Humano aprova → executor roda → log completo em `logs/privileged/` | ✓/✗ |

---

## 6. Migração e Reversão

### 6.1 Migração (fases)

| Fase | Ação | Validação |
|---|---|---|
| 1 | Implementar `landlock.py` + perfis YAML | Testes unitários passam |
| 2 | Integrar em `tools.py` (write, edit, bash) | Testes integração passam |
| 3 | Implementar `capability_broker.py` + migrar `capability.py` | Broker serve segredos corretos |
| 4 | Implementar `executor_privilegiado.py` + Portão 3P | Fluxo completo testado |
| 5 | Atualizar `perimetro.sh` com `ruleset_perimetro` | P-1/P-2 OK sem root |
| 6 | Adicionar P-27 ao perimetro | Red team passa |

### 6.2 Reversão

```bash
# Reversão imediata (sem P-8):
# 1. Desabilita Landlock nas tools
sed -i 's/apply_ruleset/# apply_ruleset/' redesign/grafo/tools.py
# 2. Remove ruleset_perimetro do perimetro.sh
# 3. Volta capability.py antigo
git checkout HEAD -- redesign/mcp/capability.py
# 4. Testa: perimetro.sh volta a PARCIAL (estado anterior)
```

---

## 7. Riscos e Dependências

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Kernel < 5.13 (sem Landlock) | Baixa (CachyOS 6.x) | Alto | Fallback para `bwrap` (já existe) |
| Landlock ruleset muito restritivo quebra ferramentas legítimas | Média | Médio | Perfis YAML ajustáveis; testes de regressão |
| Capability broker vira single point of failure | Baixa | Alto | Broker stateless; réplica via systemd; cache de capability válida |
| Executor privilegiado vira backdoor | Baixa | Crítico | Portão 3P obrigatório; audit trail imutável; P-8 para mudanças |
| Performance: Landlock ruleset apply por tool call | Baixa | Baixo | Cache ruleset compilado; apply é syscall única (~1μs) |

---

## 8. Drift Report (pós-aplicação)

| Item da Spec | Implementado? | Diferença | Classificação |
|---|---|---|---|
| Landlock ruleset por ferramenta | | | |
| Capability broker mediador | | | |
| Executor privilegiado + Portão 3P | | | |
| P-1/P-2 OK sem root | | | |
| P-27 red team no perimetro | | | |

---

## 9. Próximos Passos (SDD)

1. **Revisão independente** (peixinhos dourados) — avaliar spec sem conversa
2. **Consolidação** — responder achados, preservar divergências
3. **Decisão Humano** — avançar/reduzir/arquivar
4. **Proposta P-8** — se avançar, uma proposta, uma assinatura
5. **Implementação** — fases 1-6 acima
6. **Drift report** — comparar spec aprovada vs código vs comportamento

---

**Artefatos mínimos desta spec:** este arquivo + `decision.md` (entrevista) + revisão independente + decisão Humano + drift report. Em área protegida, acompanha `.diff` + `APROVADO-` assinado.