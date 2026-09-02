# P2-03 — openvino-embeddings.service (bge-small / e5-small) na iGPU

**Objetivo:** um endpoint de embedding pequeno rodando na iGPU via OpenVINO — o que a
Fase 5 (RLM) e a Fase 6 (recuperação índice-primeiro) vão consumir, sem tocar a 4060.
Item do aceite da Fase 2: "endpoint de embedding responde".

**Pré-requisitos:** P2-02 FEITO (venv `redesign/igpu/.venv` e OpenVINO já provados na iGPU).

**Arquivos que a tarefa toca:**
- `redesign/igpu/.venv` (reusa o da P2-02; só adiciona deps se preciso)
- modelo de embedding convertido para OpenVINO IR em `~/.cache/agata/openvino/embeddings/`
- `redesign/igpu/embeddings_server.py` (novo)
- `~/.config/systemd/user/openvino-embeddings.service` (novo)
- `redesign/tasks/P2-03-*.md`

---

## Contexto

- PESQUISA C2: numa UHD 32 EU dá para **um** modelo de embedding pequeno — `bge-small`
  (384 dim) ou `e5-small` (384 dim), via `optimum-intel`. Não mais que isso.
- **Zero vector DB** é invariante do projeto (ROADMAP Fase 6). Este serviço só devolve o
  vetor; quem guarda/recupera é o índice derivado + a lógica do grafo. Não introduzir
  FAISS/Chroma/etc. aqui.

---

## Passos

### 1. Escolher e converter o modelo

```fish
cd $HOME/agata
redesign/igpu/.venv/bin/optimum-cli export openvino \
  --model BAAI/bge-small-en-v1.5 \
  --task feature-extraction \
  --weight-format int8 \
  ~/.cache/agata/openvino/embeddings/bge-small-en-v1.5-int8
ls -lh ~/.cache/agata/openvino/embeddings/bge-small-en-v1.5-int8
```
Colar de volta: o `ls`.
(Se o corpus do Agata for majoritariamente PT-BR, avaliar `intfloat/multilingual-e5-small`
no lugar — decidir aqui, anotar o porquê.)

### 2. `embeddings_server.py`

Escrever `redesign/igpu/embeddings_server.py`:
- carrega com `optimum.intel.OVModelForFeatureExtraction.from_pretrained(dir, device="GPU")`
  + o tokenizer.
- `POST /embed` (HTTP `127.0.0.1:20131`) — body `{"input": ["texto", ...]}` → resposta
  no formato OpenAI embeddings (`{"data":[{"embedding":[...], "index":0}], "model":...,
  "usage":{...}}`), para o OmniRoute / o grafo consumirem sem adaptador.
- mean-pooling + L2-normalize (padrão bge/e5). Prefixos `query:` / `passage:` se for e5.
- `--selftest`: embeda 2 frases próximas e 1 distante, imprime as similaridades de cosseno.

### 3. Teste — endpoint responde, na iGPU

```fish
cd $HOME/agata
redesign/igpu/.venv/bin/python redesign/igpu/embeddings_server.py &
sleep 3
curl -s http://127.0.0.1:20131/embed -H 'content-type: application/json' \
  -d '{"input":["a âncora de sha detecta versão velha","tag anotada aponta um commit","o gato dorme no sofá"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); v=d['data']; print('n=',len(v),'dim=',len(v[0]['embedding']))"
# durante:
timeout 5 intel_gpu_top -l | head
nvidia-smi --query-compute-apps=pid,process_name --format=csv   # embeddings NÃO deve aparecer
kill %1
```
Colar de volta: `n=`, `dim=`, a carga da iGPU, o `nvidia-smi`.
Sucesso: devolve N vetores de dim esperada (384); carga na iGPU; nada na 4060; as 2 frases
próximas têm cosseno claramente maior que a distante (`--selftest`).

### 4. systemd --user

```fish
printf '%s\n' \
  '[Unit]' 'Description=OpenVINO embeddings na iGPU (Agata, Fase 2)' 'After=default.target' \
  '' '[Service]' \
  'ExecStart=%h/agata/redesign/igpu/.venv/bin/python %h/agata/redesign/igpu/embeddings_server.py' \
  'Restart=on-failure' 'Nice=5' \
  '' '[Install]' 'WantedBy=default.target' \
  > $HOME/.config/systemd/user/openvino-embeddings.service
systemctl --user daemon-reload
systemctl --user start openvino-embeddings.service
systemctl --user status openvino-embeddings.service --no-pager
```
**Não** `enable` (boot é Fase 7).

### 5. Fechar o aceite da Fase 2 (verificação conjunta)

```fish
# com whisper + embeddings + display todos na iGPU, medir a 4060 de novo:
nvidia-smi --query-gpu=memory.used,power.draw --format=csv -l 1 -c 10
nvidia-smi   # rodapé: sem compositor, sem whisper, sem embeddings
```
Colar de volta: as 10 amostras + o rodapé.
Sucesso: a 4060 em repouso ≈ só o que Ollama/keep-alive segura; nada de display/STT/embed.

---

## Aceite

- `POST /embed` devolve vetores no formato OpenAI embeddings, dim 384, `usage` presente.
- `--selftest`: cosseno(frases próximas) > cosseno(frase distante) por margem clara.
- Durante: carga na iGPU (`intel_gpu_top`), nada no `nvidia-smi`.
- `systemctl --user is-active openvino-embeddings.service` → `active`.
- **Aceite da Fase 2 inteiro:** `nvidia-smi` sem display/STT/embeddings na 4060; Whisper
  RTF < 1 (P2-02); endpoint de embedding responde (esta).
- Nenhum vector DB introduzido (`pip list | grep -Ei 'faiss|chroma|qdrant|weaviate'` → vazio).

## Verificação independente

- **Quem:** fallback afinado ou Humano.
- **O quê:** que roda na iGPU (não CPU), que o formato de resposta é OpenAI-compatível
  (para não precisar de adaptador no grafo), e que a 4060 ficou de fato livre de
  display+STT+embeddings ao mesmo tempo.
- **Como:** `--selftest` com `device="CPU"` para comparar latência; `diff` do JSON de
  resposta contra o schema OpenAI; a medição conjunta do passo 5 relida no LOG.
- **Resultado:** anotar no LOG.

## Rollback

Não destrutivo:
```fish
systemctl --user stop openvino-embeddings.service
rm -f $HOME/.config/systemd/user/openvino-embeddings.service
systemctl --user daemon-reload
git checkout -- redesign/igpu
```
> ⚠️ **Remove o modelo de embedding convertido. Rode sozinho.**
> ```fish
> rm -rf ~/.cache/agata/openvino/embeddings
> ```

## Registro

- `STATUS.md`: P2-03 → "Feito"; **Fase 2 fechada** (aceite conjunto). Anotar o modelo
  escolhido e a dim.
- `LOG.md`: `n=`/`dim=`, as similaridades do `--selftest`, a medição conjunta da 4060 do
  passo 5, o resultado da verificação independente, `HEAD` no fim.
