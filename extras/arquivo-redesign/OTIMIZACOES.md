# OTIMIZAÇÕES — revisão do redesenho (2026-09-03, chat 6)

Revisão pedida pelo Humano ao fim da rodada da Fase 8. **Nada aqui foi aplicado**, exceto o
que está marcado ✅ FEITO. O resto é proposta com risco/benefício — o Humano escolhe.

Princípio da revisão: manter a **espinha determinística mínima e verificável**; cortar peso
e footgun sem tocar o que funciona.

---

## ✅ FEITO nesta rodada

### B1 — as 3 unidades base entraram no repo
`openvino-whisper.service`, `openvino-embeddings.service`, `obsidian-ro-proxy.service`
copiadas de `~/.config/systemd/user/` para `redesign/systemd/` com o fix do chat 5.

### D1 — varredura do footgun do heredoc
Os outros dois `python3 - <<'PY'` do P-12 lêem `sys.argv`/arquivo, sem pipe entrando —
limpos. Só o caminho `hd_ok=1` tinha o defeito (corrigido em `bc15673`).

### A1 — `igpu/.venv` trocou torch-CUDA por torch-CPU · **~4,4 GB de volta**
`redesign/igpu/.venv`: **6,2 GB → 1,8 GB**; `redesign/` inteiro: 6,4 GB → **199 MB**.
Removidos `torch`(CUDA)+`triton`+18 pacotes `nvidia-*`/`cuda-*`; instalado
`torch==2.14.0+cpu` (wheel cp314, 196 MB) do índice `download.pytorch.org/whl/cpu`.
`pip check` limpo. **Verificado:** `openvino-whisper` e `openvino-embeddings` reiniciados →
`/health` OK nos dois (`device: GPU.0`); `/v1/embeddings` real devolve vetor 384-d;
`WhisperPipeline` carrega em `GPU.0` e **transcreve** um wav de teste (espeak-ng) com **RTF
0.24 em `GPU.0`** (< 1); nenhum processo python na 4060. Rollback:
`redesign/igpu/.venv-freeze-pre-A1.txt` (87 linhas, `pip install -r`).

### B2 — `agata-warmup.service` (manual) · mitiga o 504 de cold start
`redesign/systemd/agata-warmup.service` → `~/.config/systemd/user/`. Oneshot: 1 token pelo
`:20127` que carrega `qwen3.5:9b` na VRAM (o 504 do OmniRoute nesta 1ª chamada é esperado;
o efeito é o load). **Sem `[Install]` — NÃO sobe no boot nem com `agata up`** (mantém a 4060
livre por padrão, mesma lógica do `llamacpp-agata`). Dispare a mão antes de usar o modelo
local pesado: `systemctl --user start agata-warmup.service`. Testado: `Result=success`,
modelo carregado, chamada seguinte em ~0,4 s.

### B3 — `hash_ir.sh` · fórmula reproduzível para os IR OpenVINO
`redesign/fase7-hd/hash_ir.sh` — `sha256` da concatenação de todos os arquivos do dir do IR
(menos `model_cache/`), ordem `LC_ALL=C sort`. Os valores históricos de `ir_sha256_xmlbin`
no manifesto são de uma fórmula não documentada e não reproduzem; **o teste de restore do
P7-03 é a garantia real**. Hashes reproduzíveis medidos:
`multilingual-e5-small-int8` `9f38702dc22c7a99…` · `whisper-base-int8-ov` `d3c0f3645e7cec06…` ·
`whisper-small-int8-ov` `0f7d10a50e792aca…`.

### D2 — `rodar_par.sh` · reduz o atrito dos 7 dias do paralelo
`redesign/grafo/rodar_par.sh <tipo> "<pedido>"` — clone fresco → `grafo.py run` → guarda a
saída em `paralelo-runs/` → `resume --recusar` → 1 linha em `paralelo.md`. Testado:
`rota=cheap · trabalhar:…minimax… · perímetro=OK · fab=0 · portão=pausou`.

### C2 — `.diff` pronto (não aplicado — P-8, job desatendido)
`redesign/propostas/consolidacao-flow.diff` — `config/agata-consolidacao.service` deixa de
chamar `hermes chat` e passa a rodar `flows/consolidacao.py` (grafo). `git apply --check`
limpo. Entra na Fase 8 com os outros `.diff`; precisa de `APROVADO-consolidacao-flow` +
`systemd-analyze --user verify`.

---

## Propostas que sobram

### C1 — unificar `mcp/.venv` + `grafo/.venv` · ~100 MB + menos manutenção · risco médio
Depois do A1, `redesign/` já caiu para 199 MB — o ganho de C1 virou marginal. Só vale se
for para ter um lugar único de pin de deps. Checar conflito `fastmcp` vs `langgraph` antes.

## Observações sem ação proposta

- **`redesign/` no disco: 199 MB** depois do A1 (era 6,4 GB). O repositório git sempre foi
  pequeno (os `.venv` são gitignorados).
- **6 serviços `--user` sempre de pé** (~1,2 GB RAM idle, 4060 em 152 MiB). Socket-activation
  do whisper/embeddings (subir na 1ª chamada) economizaria RAM, mas eles são baratos e o
  atraso de load na 1ª transcrição pesaria — **não vale o risco/complexidade agora.**
- **OmniRoute escuta 4 portas** (20127/8 + 20131/2). As duas extras são internas dele;
  documentar só, não mexer.
- **A trava do fim do chat 4** segue `lacuna` não medida — não reabrir sem evidência nova.
