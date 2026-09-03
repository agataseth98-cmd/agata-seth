# adapters/dsh.md — adapter DeepSeek Harness (`dsh`), DORMENTE (P4-06)

**Não é canon.** Branch `redesign`, Fase 4. Mapa para trocar o LangGraph pelo `dsh` como
executor do loop de governança, **sem instalar** o preview instável.

## Estado: `ENABLED = False`

`dsh` está em **`0.1.0-rc.5`** (Node 24, micro-kernel Cordis), com aviso explícito no
próprio projeto: *"THERE WILL BE COMPATIBILITY-BREAKING CHANGES"* (PESQUISA). Este adapter
é escrito e mantido **fechado** — o `dsh.py` levanta `NotImplementedError` se chamado.

### Gatilho de reavaliação

Reabrir quando **as duas** condições valerem:
1. `dsh` publica uma **tag estável** (≥ `1.0.0`, ou o fim do aviso de breaking changes);
2. o loop LangGraph (P4-01..P4-05) está em produção pós-Fase 8 e há um motivo concreto
   (ex.: o WAL caseiro do P4-00 virou custo de manutenção; precisa de sandboxes como seam
   de 1ª classe; UI/observabilidade).

Registrado em `PESQUISA.md` (linha do `dsh`).

## Contrato que o adapter tem que cumprir

O mesmo que `grafo.py` expõe hoje:

```python
run(entrada, repo, thread_id, tipo="trabalho", com_envelope=False)  -> imprime o estado final / pausa no portão
resume(thread_id, repo, aprovar=True)                               -> retoma do checkpoint
```

Estado tipado (`estado.py::Estado`), efeito idempotente por `(thread, node, passo)`,
`interrupt` no portão, `verificar`/`registrar_e_commitar` model-free.

## Mapa nó do grafo ↔ seam do `dsh`

| nó (grafo.py) | seam `dsh` | nota |
|---|---|---|
| `hidratar` | **loops** (passo de setup do loop) + **storage** (lê o `estado_para_eco.sh`) | sem modelo; igual |
| `rotear` | **models** (seleção de backend/combo) | o `dsh` tem seleção de modelo como seam — mais rico que a heurística de string atual |
| `trabalhar` | **models** + (opcional) **skills** | a chamada ao modelo; `--com-envelope` = uma skill de formatação |
| `verificar` | **tools** (as 5 do P0-02) rodando em **sandboxes** | o `dsh` tem `sandboxes` como seam de 1ª classe → substitui o `sandbox.py` (bwrap manual) |
| `portao` | **UI** (o `interrupt`/aprovação humana) + **loops** (pausa/retoma) | o `dsh` tem UI como seam; o portão vira um ponto de interação declarado |
| `registrar_e_commitar` | **tools** (`commit_entry`) + **storage** | idempotência: ver "sessions" abaixo |

### O que o `dsh` GANHA (por que o adapter existe)

- **`sessions` — session log append-only NATIVO.** Substitui o WAL caseiro
  (`durabilidade.py::WAL` + `eventos.ndjson` + `os.fsync`) do P4-00. O veredito do P4-00
  (opção A) continua válido; o `dsh` só troca *quem* mantém o log.
- **`sandboxes` como seam** — em vez do `sandbox.py` (bwrap montado à mão), a contenção é
  configuração de seam.
- **`scheduling`** — a consolidação noturna (Fase 6) e o liga/desliga (Fase 7) teriam um
  seam próprio em vez de `systemd` timers soltos.

### O que o `dsh` PERDE hoje

- **Instável** (`rc.5`, breaking changes prometidas) — não dá para construir a Fase 4
  produção em cima.
- **Node 24** — mais uma toolchain (o resto do redesenho é Python + shell + systemd).
- **Cordis (micro-kernel) em fluxo** — a API dos seams pode mudar.

## O que o adapter precisaria implementar, por seam (quando reabrir)

| seam | trabalho |
|---|---|
| `models` | provider que aponta para o OmniRoute `:20127` (sanitizador) + o `llamacpp-local` `:20129` para o `--com-envelope` (GBNF) |
| `tools` | as 6 de `tools.py` (`git_sync`, `run_perimetro`, `check_citation`, `lint_header`, `query_canon`, `commit_entry`) como tool-defs do `dsh` |
| `sandboxes` | perfil equivalente ao `sandbox.py` (`--unshare-all`, ro-bind no repo, sem rede; `rw` só `.git` + alvo para `commit_entry`) |
| `sessions` | mapear o event-stream do P4-00 (`intent`/`done` + idem key) para o log nativo; provar os 4 critérios do E2 de novo no `dsh` |
| `loops` | os 6 nós como passos do loop; `interrupt` no portão |
| `storage` | `SqliteSaver` → o storage do `dsh` (ou manter SQLite) |
| `skills` | `--com-envelope` (2 fases GBNF) como skill |
| `UI` | o portão (3 perguntas + diff) como ponto de interação |
| `scheduling` | (Fases 6/7) |

## Rollback

Nada a desfazer — `dsh.py` está `ENABLED = False` e não é importado por `grafo.py`.
`git checkout -- redesign/grafo/adapters`.
