# P4-04 — `agata` CLI (up / down / status / verify / commit-entry / run / logs)

**Objetivo:** um comando `agata` que opera o sistema — sobe/desce os serviços, mostra
estado, roda a verificação e o `commit-entry` **sem depender de modelo**, e dispara o loop.

**Pré-requisitos:** P4-01 e P4-02 FEITO (o grafo e as tools existem).

**Arquivos:**
- `redesign/grafo/cli.py` (ou `redesign/bin/agata`) — o entrypoint
- `redesign/tasks/P4-04-*.md`
- (na Fase 8, vira `/usr/local/bin/agata` — aqui fica no branch)

> Classe de risco: runtime + toca `systemctl --user`. Auto-revisão. Sem `sudo` (só units `--user`).

---

## Subcomandos

| cmd | faz |
|---|---|
| `agata up` | `systemctl --user start` de omniroute, sanitizer, whisper, embeddings; (llama.cpp opcional `--moe`) |
| `agata down` | para os serviços; **drena** (não corta no meio de um commit — checa o WAL do P4-00) |
| `agata status` | estado dos serviços + `git_sync` (canon vs origin/main; branch vs upstream) + `HASH-ESTADO` do `estado_para_eco.sh` |
| `agata verify` | `perimetro.sh` + `verificar_cabecalho.py` + `checar_citacao.sh` — **exit 0/≠0, sem modelo** |
| `agata commit-entry <arquivo>` | valida cabeçalho + citações, escreve a entrada no LOG/MEMÓRIAS (append-only), `git commit` — **sem modelo** |
| `agata run "<pedido>"` | dispara o grafo (P4-01) com um `thread_id` novo; `--resume <id>` retoma |
| `agata logs [--thread <id>]` | tail do event-stream (`eventos.ndjson`) e do LOG do grafo |

## Passos

1. `cli.py` com `argparse`; cada subcomando chama as tools da P4-02 (não re-implementa).
2. `up`/`down` sobre os units `--user` já existentes (Fases 1-3) + os do grafo.
3. `verify` e `commit-entry` **não importam langgraph nem tocam modelo** — são a espinha
   determinística; têm que rodar com tudo desligado.
4. `down` consulta o WAL (`DURABILIDADE.md`): se há um efeito `intent` sem `done`, espera
   ou marca pendente antes de parar.

## Aceite

- `agata verify` e `agata commit-entry` rodam e dão exit correto **com os serviços de
  modelo parados** (`agata down` antes).
- `agata up` / `down` mexem só nos units `--user`; `down` não interrompe um commit em curso.
- `agata status` mostra serviços + sync + `HASH-ESTADO` numa tela.
- `agata run` dispara o grafo e `--resume` retoma (herda P4-00/P4-01).

## Verificação independente

- **Quem:** fallback ou Humano. **O quê:** que `verify`/`commit-entry` são model-free
  (rodar com `agata down` feito) e que `down` drena. **Como:** `agata down; agata verify;
  echo $status`; simular `intent` sem `done` e ver `down` esperar. **Resultado:** no LOG.

## Rollback

`git checkout -- redesign/grafo`. Não destrutivo (units `--user` já existiam).

## Registro

- `STATUS.md`: P4-04 → "Feito"; a tabela de subcomandos.
- `LOG.md`: `verify`/`commit-entry` model-free comprovado, o teste de drenagem, `HEAD`.
