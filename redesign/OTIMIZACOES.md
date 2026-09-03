# OTIMIZAÇÕES — revisão do redesenho (2026-09-03, chat 6)

Revisão pedida pelo Humano ao fim da rodada da Fase 8. **Nada aqui foi aplicado**, exceto o
que está marcado ✅ FEITO. O resto é proposta com risco/benefício — o Humano escolhe.

Princípio da revisão: manter a **espinha determinística mínima e verificável**; cortar peso
e footgun sem tocar o que funciona.

---

## ✅ FEITO nesta rodada (risco zero)

### B1 — as 3 unidades base entraram no repo
`openvino-whisper.service`, `openvino-embeddings.service`, `obsidian-ro-proxy.service`
viviam **só** em `~/.config/systemd/user/` (nunca versionadas; o chat 5 as editou e o
backup foi pro scratchpad efêmero). Copiadas para `redesign/systemd/` com o fix do chat 5
(`After=default.target` removido, `[Install] WantedBy=agata.target`). Fecha a lacuna que o
próprio LOG do chat 5 apontou. Se uma unidade voltar ao estado antigo (update, `revert`), o
repo agora tem a boa.

### D1 — varredura do footgun do heredoc
O bug do P-12 (`restic ... | python3 - <<'PY'` — o heredoc vence o pipe) foi conferido nos
outros dois `python3 - <<'PY'` do controle (linhas `linhas=$(...)` e `visto=$(...)`):
**ambos lêem `sys.argv`/arquivo, nenhum tem pipe entrando** — limpos. Só o caminho
`hd_ok=1` tinha o defeito, e está corrigido.

---

## Propostas (o Humano decide)

### A1 — reconstruir `igpu/.venv` sem torch-CUDA · **~5 GB de volta** · risco baixo
`redesign/igpu/.venv` tem **6,2 GB** — o LOG da Fase 2 já anotou "puxou ~2 GB de libs CUDA
à toa". OpenVINO + optimum-intel servem os modelos na **iGPU Intel**; não precisam de
`torch` compilado para CUDA. Reconstruir o venv com `torch` CPU-only (ou sem torch, se o
`optimum-cli export` não precisar em runtime) derruba `redesign/` de 6,4 GB para ~400 MB.
- **Teste:** re-rodar `--selftest` de `whisper_server.py` e `embeddings_server.py` + o
  aceite conjunto da Fase 2 (`nvidia-smi` sem carga, RTF < 1, embedding responde).
- **Rollback:** o venv é descartável e gitignorado; reconstrói pelo `requisitos` da Fase 2.

### B2 — pré-aquecer o modelo local no `agata up` · corrige um 504 real · risco baixo
Achado no P8-04: a **1ª** chamada a um modelo Ollama frio (~30 s de load) estoura o
`resilienceSettings.requestQueue.maxWaitMs=15000` do OmniRoute → **504**
`RATE_LIMIT_EXECUTION_TIMEOUT`. O modelo carrega mesmo assim; a 2ª responde em ~0,5 s.
Duas saídas, a 1ª é mais espelho:
- **B2a (preferida):** `ExecStartPost` no `agata.target`/`agata-drain` (ou um
  `agata-warmup.service` oneshot) que faz um `curl` de 1 token em `ollama-local/qwen3.5:9b`
  logo após subir — determinístico, no nosso controle, sem tocar config de terceiro.
- **B2b:** subir o `maxWaitMs` do OmniRoute para ~45000. Mais simples, mas é config do
  OmniRoute (fora do nosso código) e afrouxa o deadline para todo request.

### B3 — fixar a fórmula do `ir_sha256_xmlbin` · risco zero
O manifesto usa `ir_sha256_xmlbin` como tag do P-12, mas **a fórmula de cálculo não está
registrada em lugar nenhum** (o chat 3 calculou e não anotou; nenhum recorte óbvio
reproduz). Escrever `models/hash_ir.sh` (o comando exato) + uma linha no `manifest.json`
por recurso OpenVINO dizendo qual é. Sem isso, um dia alguém restaura um IR e não tem como
conferir que bate.

### C1 — unificar `mcp/.venv` + `grafo/.venv` · ~100 MB + menos manutenção · risco médio
Dois venvs (`fastmcp` 115 MB, `langgraph` 84 MB) que provavelmente não conflitam. Um
`redesign/.venv` só reduz duplicação de stdlib/pip e dá um lugar único para pinar deps. O
`igpu/.venv` fica separado (deps pesadas e específicas). **Risco médio:** checar conflito
`fastmcp` vs `langgraph`/`langchain-core` antes; ganho modesto.

### C2 — repontar `agata-consolidacao.timer` para o flow do grafo · tira 1 amarra do Hermes cedo · risco baixo
O `agata-consolidacao.timer` ainda chama o Hermes (contenção de SQLite no `state.db`,
`Restart=on-failure` cobrindo isso). O `redesign/grafo/flows/consolidacao.py` (P6-03) é o
substituto pronto. Repontar o timer agora é userspace, **não toca o Hermes-executor**, e
adianta parte do P8-05.

### D2 — `redesign/grafo/rodar_par.sh` para o paralelo de 7 dias · risco zero · aumenta a chance de P8-02 acontecer
Um script que padroniza o par do P8-02: clone fresco → `grafo.py run` → captura
rota/modelo/perímetro/fabricação/tempo → `resume --recusar` → 1 linha em `paralelo.md`.
Reduz o atrito do Humano nos 7 dias (hoje é copiar/colar comando + parsear JSON à mão).

---

## Observações sem ação proposta

- **`redesign/` no git é pequeno** — os 6,4 GB são os `.venv` gitignorados no disco local,
  não o repositório. A1 resolve o disco.
- **6 serviços `--user` sempre de pé** (~1,2 GB RAM idle, 4060 em 152 MiB). Socket-activation
  do whisper/embeddings (subir na 1ª chamada) economizaria RAM, mas eles são baratos e o
  atraso de load na 1ª transcrição pesaria — **não vale o risco/complexidade agora.**
- **OmniRoute escuta 4 portas** (20127/8 + 20131/2). As duas extras são internas dele;
  documentar só, não mexer.
- **A trava do fim do chat 4** segue `lacuna` não medida — não reabrir sem evidência nova.
