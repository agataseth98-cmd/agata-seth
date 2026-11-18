# redesign/systemd/ — units da Fase 7 (P7-01)

Espelho do que está instalado em `~/.config/systemd/user/` (P7-01, 2026-09-02).
**`agata.target` está `enable`d para o boot** (`systemctl --user enable agata.target`,
"sim" do Humano 2026-09-02 ~21:00) — no login, `default.target` → `agata.target` →
puxa os 5 membros. `llamacpp-agata` **não** sobe no boot (PartOf sem WantedBy).
Só `agata.target` está em `default.target.wants/`; os membros só em `agata.target.wants/`.

## Arquivos

| arquivo aqui | instala em | o que faz |
|---|---|---|
| `agata.target` | `~/.config/systemd/user/agata.target` | alvo que agrupa os serviços. Sem `Requires`/`Wants` — os membros se ligam pelo `[Install] WantedBy=agata.target`. |
| `agata-drain.service` | `~/.config/systemd/user/agata-drain.service` | oneshot `RemainAfterExit`. `After=` os 5 serviços ⇒ no stop para **antes** deles ⇒ `ExecStop` roda `drenar.py` (espera o WAL, não corta), e só então o systemd derruba os serviços. **Não** chama `systemctl` (isso deadlocka contra a transação de stop — visto no teste). |
| `dropin-generico.conf` | `<unit>.service.d/agata.conf` em `omniroute-sanitizer`, `openvino-whisper`, `openvino-embeddings`, `obsidian-ro-proxy` | `[Unit] PartOf=agata.target` + `[Install] WantedBy=agata.target`. |
| `dropin-omniroute.conf` | `omniroute.service.d/agata.conf` | igual ao genérico + `[Service] SuccessExitStatus=143 SIGTERM` — `omniroute` é `Type=simple` e o `ExecStop=omniroute stop` mata o próprio main (sai 143); sem isto o stop normal fica `failed`. |
| `dropin-omniroute-resilience.conf` | `omniroute.service.d/resiliencia.conf` | `Environment=RATE_LIMIT_MAX_WAIT_MS=45000` — reproduz o conserto de (363) sem UI, pra um clone que nasce com banco vazio. Achado do laboratório "Ensaio" (MEMÓRIAS 587), lido no código-fonte real do pacote. Nesta Máquina o banco já tem o valor (vence a variável); aplicar aqui não muda nada. |
| `dropin-llamacpp.conf` | `llamacpp-agata.service.d/agata.conf` | **só** `PartOf=agata.target` (sem `WantedBy`): o MoE **para** com o `agata down` (libera a VRAM da 4060) mas **não sobe** junto — fica sob demanda (`agata up --moe`). |
| `llamacpp-agata.service` | `~/.config/systemd/user/llamacpp-agata.service` | **unidade base** do MoE (versionada em 23/10/2026; antes só fora do git). `Restart=no` e **sem** `[Install]`: sob demanda, só à mão, nunca volta sozinho depois de um OOM na GPU (fecha a pendência de (652); mesma regra do `llamacpp@.service`). |
| `ollama-agata.socket`, `ollama-agata-proxy.service`, `ollama-agata.service` | `~/.config/systemd/user/` (**sem sudo**, como links para `config/`) | **18/11/2026, sob demanda** (decisão do Humano: como o Laya e o Ollaya). O socket escuta `127.0.0.1:11434` e fica no `agata.target`; a 1ª conexão sobe o proxy (`systemd-socket-proxyd`, sai após 15 min ociosos) e o backend (`OLLAMA_HOST=127.0.0.1:11447`, `OLLAMA_MODELS=%h/.local/share/ollama/models`, `StopWhenUnneeded`, sem `[Install]`). Substitui o `ollama.service` do sistema, que precisa ficar desabilitado (o socket precisa da porta 11434). Migração, uma vez, com sudo: fim deste arquivo. |
| `dropin-ollama-bind.conf` | `/etc/systemd/system/ollama.service.d/agata-bind.conf` (**sudo**, unit de `system`, não `--user`) | 2 variáveis invariantes (bind `127.0.0.1`, flash attention) — framework, igual em qualquer clone. Achado do laboratório "Ensaio" (MEMÓRIAS 567): antes, essas 2 viviam misturadas com hardware num `override.conf` único, só em prosa (`PROJETO.md`), sem template versionado. |
| `dropin-ollama-gpu.exemplo.conf` | `/etc/systemd/system/ollama.service.d/agata-gpu.conf` (**sudo**) | **exemplo**, não instala direto — 3 variáveis de hardware (VRAM/GPU desta Máquina), ajustar antes de usar. Nunca versionado com valor real (mesmo tratamento de `CHAVES.env.exemplo`). |
| `openvino-whisper.service` · `openvino-embeddings.service` · `obsidian-ro-proxy.service` | `~/.config/systemd/user/<nome>` | **unidades base** (Fase 2/6). Promovidas ao repo em 03/09 (chat 6, otimização B1) — antes só existiam fora do git. Trazem o fix do chat 5 (`After=default.target` removido, `[Install] WantedBy=agata.target`). |
| `agata-jogo` | `~/.local/bin/agata-jogo` (`install -Dm755`, **sem sudo**) | **P7-02 (chat 6).** Wrapper: `stop agata.target` (drena) + `ollama stop` dos modelos ativos → roda o jogo via `game-performance` (wrapper oficial do CachyOS) → `trap EXIT` re-sobe `agata.target`. **Substitui o Feral GameMode** — o CachyOS já roda `ananicy-cpp` (renice automático) e GameMode brigaria com ele. `gamemode.ini.exemplo` foi removido. |

## Instalado assim (P7-01, com "vai" do Humano 2026-09-02 ~20:30)

```
mkdir -p ~/.config/systemd/user/{omniroute,omniroute-sanitizer,openvino-whisper,openvino-embeddings,obsidian-ro-proxy,llamacpp-agata}.service.d
cp agata.target agata-drain.service ~/.config/systemd/user/
cp dropin-generico.conf   ~/.config/systemd/user/omniroute-sanitizer.service.d/agata.conf   # idem whisper, embeddings, ro-proxy
cp dropin-omniroute.conf  ~/.config/systemd/user/omniroute.service.d/agata.conf
cp dropin-llamacpp.conf   ~/.config/systemd/user/llamacpp-agata.service.d/agata.conf
systemctl --user daemon-reload
systemctl --user enable omniroute omniroute-sanitizer openvino-whisper openvino-embeddings obsidian-ro-proxy agata-drain   # popula agata.target.wants/
# remover os default.target.wants/<unit> que o enable também cria (não queremos boot):
rm ~/.config/systemd/user/default.target.wants/{omniroute,omniroute-sanitizer,openvino-whisper,openvino-embeddings,obsidian-ro-proxy}.service
systemctl --user daemon-reload
```

`agata-drain` foi `enable`d p/ `agata.target.wants/` (senão o target não puxa o dreno).
`seth-gateway` entrou no `agata.target` em 18/10/2026 (queda de energia): `[Install] WantedBy=agata.target` + `PartOf=agata.target` na própria unit; instalar com `cp seth-gateway.service ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable seth-gateway` (sem sudo). `seth-escriba`/`seth-verificador` seguem `static`, sob demanda.
`piper-tts` (voz) entrou no `agata.target` em 18/10/2026, mesma queda de energia e decisão do Humano: `WantedBy=agata.target` + `PartOf=agata.target`; instalar com `cp piper-tts.service ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable piper-tts` (sem sudo).
`agata.target` foi `enable`d p/ `default.target.wants/` (boot) — "sim" do Humano
2026-09-02 ~21:00. Rollback do boot: `systemctl --user disable agata.target`.

## Verificação P7-01 (S7, 2026-09-02 ~20:40) — PASS

- **`stop agata.target` com efeito pendente no WAL:** `agata-drain` segurou 26 s
  (`drenar.py`), logou `AVISO -- 1 efeito(s) ainda pendente(s) ... NAO cortados` com
  `thread=/node=/passo=/chave=`, saiu 0 (`Result=success`). Os 5 serviços só caíram
  **depois** do dreno. Nenhum membro `failed`.
- **`stop agata.target` com WAL limpo:** `dreno: WAL limpo` — teardown em 1 s, todos
  `Result=success`.
- **`start agata.target`:** os 5 voltam em ~6 s; portas `:20127 :20128 :20130 :20134
  :27124 :27125` UP.
- **VRAM da 4060:** `start llamacpp-agata` ⇒ 56 → 6229 MiB; `stop agata.target` ⇒
  MoE `inactive` (`success`) e 4060 volta a **54 MiB**. Checkpoint/WAL intactos
  (`drenar.py` não apaga nada).
- **Boot:** `default.target.wants/` sem nada do Agata; `agata.target is-enabled = disabled`.

## Rollback

```
systemctl --user disable agata.target agata-drain omniroute omniroute-sanitizer openvino-whisper openvino-embeddings obsidian-ro-proxy
rm ~/.config/systemd/user/agata.target ~/.config/systemd/user/agata-drain.service
rm ~/.config/systemd/user/{omniroute,omniroute-sanitizer,openvino-whisper,openvino-embeddings,obsidian-ro-proxy,llamacpp-agata}.service.d/agata.conf
systemctl --user daemon-reload
```
Os serviços seguem sobíveis um a um como antes.

## Migrar o Ollama do sistema para o usuário, sob demanda (18/11/2026, uma vez, com sudo)

```
sudo systemctl disable --now ollama.service
sudo ls /usr/share/ollama/.ollama/models/manifests/registry.ollama.ai/library   # confere onde estão os modelos
mkdir -p ~/.local/share/ollama/models
sudo cp -a /usr/share/ollama/.ollama/models/. ~/.local/share/ollama/models/
sudo chown -R "$USER": ~/.local/share/ollama
ln -sf ~/agata/config/ollama-agata.socket ~/agata/config/ollama-agata-proxy.service \
       ~/agata/config/ollama-agata.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now ollama-agata.socket       # só o socket; backend e proxy sobem pela 1ª conexão
ollama list                                             # a 1ª chamada acorda o backend (alguns segundos)
```

Não rode `enable` no backend nem no proxy (sem `[Install]`). Sem o `disable --now` da 1ª linha, o socket
não consegue a porta 11434. O `cp -a` leva os modelos que já existiam; o que sai do conjunto é decisão do
Humano, tomada à parte. Conferido o `ollama list`, o diretório antigo pode ser apagado pelo Humano.

**Partida a frio e o gateway.** O socket deixa a porta 11434 sempre aberta, então o teste de porta do gateway
(`rotas_locais.ollama_no_ar`) passa a ver "no ar" mesmo com o backend parado. A 1ª chamada depois de ociosidade
espera o backend subir (alguns segundos, o socket segura a conexão) e depois o modelo carregar, dentro do prazo
da rota local (`SETH_ROTA_LOCAL_MS`, padrão 100,5 s). Se estourar, ou o backend não subir, o gateway cai na fila
de sempre sem erro ao usuário. Efeito colateral: qualquer cliente que consulte :11434 (painel, `corpo`,
inventário) acorda o Ollama e adia a parada por ociosidade.
