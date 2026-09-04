# P4-02 — tools Python do grafo (wrap dos scripts) + execução em sandbox

**Objetivo:** os nós do grafo chamam os scripts de `~/agata/scripts/` como **tools**
tipadas, e qualquer execução de tool que não seja leitura pura roda dentro de `bwrap`
(bubblewrap 0.12, já instalado).

**Status:** ✅ **FEITO — 2026-09-02 ~13:35 (relógio da máquina).** `tools.py` (6 funções:
`git_sync`, `run_perimetro`, `check_citation`, `lint_header`, `query_canon` + `commit_entry`
— esta escreve canon, append-only + `git commit` idempotente, valida cabeçalho/citações
antes). `sandbox.py` (`run_sandboxed` via `bwrap --unshare-all`). `grafo.py::verificar`
passou a usar `tools.py`. Testado: tool == script cru; `query_canon` barra `--rebuild`;
`commit_entry` grava/pula/rejeita corretamente (`git show --stat` = só o alvo); sandbox nega
escrita fora de `rw` (EROFS) e nega rede (Errno 101); escrita dentro de `rw` OK. Loop ponta
a ponta re-testado, verde. Nada instalado, sem `sudo`. Ver `redesign/grafo/README.md`.

**Pré-requisitos:** P4-01 FEITO (o grafo existe). Reusa o P0-02 (o `redesign/mcp/servidor.py`
já wrappa 5 dessas ferramentas read-only — aproveitar o desenho, não duplicar).

**Arquivos:**
- `redesign/grafo/tools.py` — as tools (assinatura tipada, retorno estruturado)
- `redesign/grafo/sandbox.py` — o wrapper `bwrap` (ro-bind no repo, sem rede, sem `/home`
  fora do necessário, tmpfs em `/tmp`)
- `redesign/tasks/P4-02-*.md`

> Classe de risco: runtime + contenção. Auto-revisão. `bwrap` é userspace (sem `sudo`).

---

## Passos

1. **`tools.py`** — as mesmas 5 do P0-02 (`git_sync`, `run_perimetro`, `check_citation`,
   `lint_header`, `query_canon`) + `commit_entry` (que saiu da Fase 0). Cada uma:
   `def tool(args: Modelo) -> Resultado` com Pydantic/TypedDict; nunca `shell=True`; erro
   em campo estruturado (herda o `_run` do P0-02 — timeout 124, binário ausente 127).
2. **`sandbox.py`** — `run_sandboxed(argv, ro_paths, rw_paths=[], net=False)`:
   `bwrap --unshare-all --die-with-parent --ro-bind <repo> <repo> --tmpfs /tmp
   --proc /proc --dev /dev [--bind <rw>] -- <argv>`. `query_canon`/`check_citation`/
   `perimetro` rodam ro; só `commit_entry` recebe `--bind` no `.git/` e no arquivo alvo.
3. Equivalência tool ↔ script cru (como o P0-02 fez): mesmo exit/resumo dentro e fora do
   sandbox, para `run_perimetro`, `lint_header`, `check_citation`.
4. Teste de contenção: uma tool tentando escrever fora do `rw_paths` → **falha** (EROFS);
   uma tool tentando abrir socket → **falha** (sem rede).

## Aceite

- As 6 tools chamáveis pelo grafo com tipos; retorno estruturado; erro nunca levanta.
- `run_sandboxed` nega escrita fora do `rw_paths` e nega rede (testado).
- Resultado por tool == resultado do script cru (`run_perimetro`/`check_citation`/`lint_header`).
- `commit_entry` escreve **só** o LOG/entrada e o `.git/` do alvo, nada mais.

## Verificação independente

- **Quem:** fallback ou Humano. **O quê:** que o sandbox realmente contém (escrita fora
  falha, rede falha) e que a equivalência tool↔script se mantém. **Como:** os 2 testes de
  contenção + 3 de equivalência, relidos no LOG. **Resultado:** no LOG.

## Rollback

`git checkout -- redesign/grafo`. Não destrutivo (nada instalado).

## Registro

- `STATUS.md`: P4-02 → "Feito"; as 6 tools + o perfil `bwrap`.
- `LOG.md`: a tabela de equivalência, os 2 testes de contenção, `HEAD`.
