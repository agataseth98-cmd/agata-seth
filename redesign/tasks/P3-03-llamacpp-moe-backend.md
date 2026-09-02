# P3-03 — llama.cpp como 2º backend local (worker MoE) exposto ao OmniRoute

**Objetivo:** rodar um modelo MoE (Qwen3-30B-A3B **ou** Qwen3.6-35B-A3B) via `llama.cpp`
com `--n-cpu-moe` varrido, servido em endpoint OpenAI-compat local, registrado no OmniRoute
como provider `llamacpp-local` e posto na combo `auto`. Fecha o aceite da Fase 3.

**Pré-requisitos:** P3-00, P3-01 FEITO. P3-02 recomendável antes (libera VRAM/RAM/disco).
OmniRoute de pé (Fase 1).

**Arquivos que a tarefa toca:**
- **INSTALA SOFTWARE:** `llama.cpp` (pacote `llama.cpp` no repo Arch/CachyOS, ou build).
- GGUF do MoE em `~/.cache/agata/models/` (fora do repo; entra no manifesto)
- `redesign/router/llamacpp.md` (novo) — a varredura `--n-cpu-moe`, o número escolhido, o
  comando do serviço
- `~/.config/systemd/user/llamacpp-agata.service` (novo)
- `redesign/tasks/P3-03-*.md`

> **Classe de risco: instala-pacote + baixa ~18 GB + serviço novo.** Revisão de plano por
> 2º par de olhos antes. O `pacman`/AUR precisa de sudo (senha do Humano) — se a sessão
> não puder, entregar o bloco de instalação para o Humano e retomar depois.

---

## Contexto (PESQUISA, correção C1)

- MoE 30B-A3B tem **GPU-util ruim no Ollama** (bug #10458) — por isso llama.cpp direto.
- `llama.cpp` com `--n-cpu-moe N` deixa N camadas de experts na RAM e a atenção na GPU.
  Varrer `N` em 8/12/16/20/24/30 medindo tok/s e saturação de CPU/VRAM.
- Qwen3-30B-A3B: 30,5 B total / ~3,3 B ativos. Q4_K_M ≈ 17–18 GB. **Não cabe** nos 8 GB da
  RTX 4060 — roda por offload, ~20–30 tok/s esperado. Aceite: **≥ ~20 tok/s**.
- Alternativa conservadora (PESQUISA): se o MoE não fechar 20 tok/s, o worker local fica
  sendo o denso 9B + LoRA e o MoE vira experimento da Fase 5 — registrar os números e seguir.

---

## Passos

### 1. **INSTALA SOFTWARE** — llama.cpp

```fish
# preferir o pacote (traz o llama-server com backend CUDA):
pacman -Ss llama.cpp
sudo pacman -S llama.cpp        # OU: llama.cpp-cuda / llama.cpp-hip conforme o repo
llama-server --version
```
Se precisar de build (sem pacote CUDA): `cmake -B build -DGGML_CUDA=ON` etc. — documentar
no `llamacpp.md`.
Colar de volta: `llama-server --version` e se tem CUDA (`llama-server --help | grep -i cuda`).

### 2. Baixar o GGUF do MoE

```fish
mkdir -p ~/.cache/agata/models
# escolher entre Qwen3-30B-A3B e Qwen3.6-35B-A3B (ver disponibilidade de GGUF Q4_K_M).
# ex.: huggingface-cli download <repo> <arquivo.gguf> --local-dir ~/.cache/agata/models
ls -lh ~/.cache/agata/models/*.gguf
sha256sum ~/.cache/agata/models/*.gguf
```
Colar de volta: `ls -lh` e o sha256.

### 3. Varredura `--n-cpu-moe`

```fish
set GGUF ~/.cache/agata/models/<moe>.gguf
for N in 8 12 16 20 24 30
    echo "=== n-cpu-moe=$N ==="
    llama-bench -m $GGUF -ngl 999 --n-cpu-moe $N -p 128 -n 128 2>&1 | tail -5
    # e olhar VRAM: nvidia-smi --query-gpu=memory.used --format=csv
end
```
Colar de volta: a tabela tok/s por `N` + a VRAM usada em cada.
Escolher o `N` com melhor tok/s que **não estoure** a VRAM da 4060 (deixar folga p/ jogo
não é requisito aqui — Fase 7 cuida do liga/desliga).

### 4. Serviço `llama-server` OpenAI-compat

```fish
printf '%s\n' \
  '[Unit]' 'Description=llama.cpp MoE backend (Agata, Fase 3)' 'After=default.target' \
  '' '[Service]' 'Type=simple' \
  "ExecStart=/usr/bin/llama-server -m $HOME/.cache/agata/models/<moe>.gguf -ngl 999 --n-cpu-moe <N> --host 127.0.0.1 --port 20129 --api-key-file /dev/null" \
  'Restart=on-failure' 'Nice=5' \
  '' '[Install]' 'WantedBy=default.target' \
  > $HOME/.config/systemd/user/llamacpp-agata.service
systemctl --user daemon-reload
systemctl --user start llamacpp-agata.service
curl -s http://127.0.0.1:20129/v1/models; echo
```
**Não** `enable` (boot é Fase 7). Bind `127.0.0.1`.

### 5. Registrar no OmniRoute + pôr na combo `auto`

```fish
omniroute setup --add-provider --non-interactive --provider llamacpp-local \
  --provider-name "llama.cpp MoE" --provider-base-url http://127.0.0.1:20129/v1 \
  --api-key "llamacpp-nokey" --default-model "<moe>"
omniroute combo delete auto --yes
omniroute combo create auto --strategy priority --models \
  "cerebras/gpt-oss-120b,llamacpp-local/<moe>,groq/openai/gpt-oss-120b,gemini/gemini-2.5-flash,ollama-local/qwen3.5:9b"
# testar pelo proxy :20127
curl -s http://127.0.0.1:20127/v1/chat/completions -H 'content-type: application/json' \
  -d '{"model":"llamacpp-local/<moe>","messages":[{"role":"user","content":"responda so: ok"}]}'
```

### 6. Manifesto + `llamacpp.md`

Acrescentar o GGUF do MoE ao `models/manifest.json` (sha256, origem = repo HF, caminho).
`redesign/router/llamacpp.md`: a tabela da varredura, o `N` escolhido e o porquê, o
comando do serviço, e — se o MoE não fechou 20 tok/s — o número medido + a decisão
(worker = 9B+LoRA, MoE p/ Fase 5).

---

## Aceite

- `llama-server` no ar em `127.0.0.1:20129`, `/v1/models` responde.
- `llamacpp-local/<moe>` roteia pelo OmniRoute e responde pelo proxy `:20127`.
- Varredura `--n-cpu-moe` registrada; **MoE ≥ ~20 tok/s** no `N` escolhido **OU**
  `llamacpp.md` registra o número medido e a decisão conservadora.
- `models/manifest.json` inclui o GGUF do MoE, `blob_sha256` de tudo.
- `ollama list` + o backend llama.cpp batem com o manifesto.
- unit `disabled` (boot = Fase 7). Bind `127.0.0.1`.

## Verificação independente

- **Quem:** fallback afinado ou Humano.
- **O quê:** que o MoE roda de fato pela GPU+offload (não 100% CPU); que o número de
  tok/s foi medido com `llama-bench`, não estimado; que o serviço está em loopback.
- **Como:** `nvidia-smi` durante uma geração (deve ter carga); `ss -tlnp | grep 20129`
  (127.0.0.1); repetir 1 linha da varredura.
- **Resultado:** anotar no LOG.

## Rollback

Não destrutivo:
```fish
systemctl --user stop llamacpp-agata.service
rm -f $HOME/.config/systemd/user/llamacpp-agata.service
systemctl --user daemon-reload
# tirar llamacpp-local dos combos / providers pelo omniroute
git checkout -- redesign/router/llamacpp.md
```
> ⚠️ **Remove o GGUF do MoE (~18 GB) e o pacote. Rode sozinho.**
> ```fish
> rm -f ~/.cache/agata/models/<moe>.gguf
> sudo pacman -Rns llama.cpp
> ```

## Registro

- `STATUS.md`: P3-03 → "Feito"; o `N` do `--n-cpu-moe`, os tok/s do MoE, e se o MoE virou
  worker ou experimento de Fase 5. **Fase 3 FECHADA.**
- `LOG.md`: a tabela da varredura, o teste de rota, o resultado da verificação
  independente, `HEAD` no fim.
