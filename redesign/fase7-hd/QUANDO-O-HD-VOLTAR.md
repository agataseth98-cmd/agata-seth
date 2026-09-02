# QUANDO O HD `AgataBkup01` VOLTAR — passada de backup da Fase 7

Runbook. Escrito 02/09/2026 sem o HD ("juntamos informacoes; quando o HD vier, a gente
salva"). Roda no **trabalho**, com `/run/media/orusoua/AgataBkup01` montado.

**Pre-checado nesta sessao:** os 4 artefatos existem no disco nos caminhos abaixo; os
sha256/ir_sha256 sao os do `models/manifest.json` (9 recursos, `n_modelos: 9`). O repo
restic `d0223c4ffb` foi criado na Fase 0 (P0-01).

Ordem: **0 → 1 → 2 → 3 → 4**. Cada passo diz o que colar de volta.

---

## 0. Montar e conferir o repo

```fish
set -x RESTIC_REPOSITORY /run/media/orusoua/AgataBkup01/restic-agata-local
set -x RESTIC_PASSWORD_FILE $HOME/.config/agata/restic.pass
restic cat config | head -3          # tem que responder (repo alcancavel)
restic snapshots --compact           # o que ja existe -- procure c19275ec (GGUF do rlm, P3-02)
```

**Colar:** a saida dos dois ultimos. Se `restic cat config` falhar, PARE — repo/senha errados.

## 1. Snapshot dos 3 IR OpenVINO + do GGUF MoE (os que faltam — P7-03 passo 1)

Cada `restic backup` leva **duas** tags: o `name` do manifesto (o P-12 filtra por ela) e o
`sha256`/`ir_sha256_xmlbin` do conteudo atual (o P-12 exige que a tag do hash bata).

```fish
# --- e5-small (262M) -- na lista P12_FALHA_SEM_BACKUP: prioridade
restic backup --host predator \
  --tag multilingual-e5-small-int8 \
  --tag fede3ab3e9975b7f300d744d0c16a4f3c9e5be4841a503c7efe405b890e9c042 \
  $HOME/.cache/agata/openvino/embeddings/multilingual-e5-small-int8

# --- whisper base (81M)
restic backup --host predator \
  --tag whisper-base-int8-ov \
  --tag 37f1fc33558914699613c25f24548e571810fc5194b622755d289180d0edc94e \
  $HOME/.cache/agata/openvino/whisper/whisper-base-int8-ov

# --- whisper small (245M)
restic backup --host predator \
  --tag whisper-small-int8-ov \
  --tag 140049e901c45cfe6936de6c1946ec71698a75fd43423b28b5c84a72987d8817 \
  $HOME/.cache/agata/openvino/whisper/whisper-small-int8-ov

# --- Qwen3-30B-A3B GGUF (18G -- vai demorar; publico+hash fixado, so redundancia)
restic backup --host predator \
  --tag qwen3-30b-a3b \
  --tag 6c997b8af17debdfb01d890214400ccbab00db6acc0ba8da5de1cc906c4774d0 \
  $HOME/.cache/agata/models/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf
```

**Colar:** os 4 `snapshot <id> saved`.

## 2. O blob do `rlm-qwen3-8b-teste` (fine-tune local — o mais irrecuperavel)

O blob vive em `/usr/share/ollama/.ollama/models/blobs/sha256-c3b6bfbc...` e e do usuario
`ollama` — **`restic` como `orusoua` nao le** (permissao negada, conferido nesta sessao).
Ja existe no snapshot **`c19275ec`** (P3-02), mas provavelmente **sem** as tags que o P-12
procura. Duas opcoes:

**2a (preferida, sem sudo):** exportar via `ollama` para um arquivo legivel e snapshotar.
```fish
mkdir -p /tmp/rlm-export
ollama show rlm-qwen3-8b-teste:latest --modelfile > /tmp/rlm-export/Modelfile
# copiar o blob pelo proprio ollama (roda como orusoua, le pelo daemon):
ollama cp rlm-qwen3-8b-teste:latest rlm-export-tmp
# (o blob em si so sai com 'ollama pull'/registro; se nao der, use 2b)
```
Se o export limpo nao for trivial, use **2b**.

**2b (com sudo — PARE e peca ao Humano):**
```fish
sudo --preserve-env=RESTIC_REPOSITORY,RESTIC_PASSWORD_FILE restic backup \
  --host predator \
  --tag rlm-qwen3-8b-teste:latest \
  --tag c3b6bfbc3a9d36d62f871232aae75de3a6996eee5fd50b2982167773df6e262b \
  /usr/share/ollama/.ollama/models/blobs/sha256-c3b6bfbc3a9d36d62f871232aae75de3a6996eee5fd50b2982167773df6e262b
```

**OU**, se `c19275ec` ja tem o conteudo certo, so re-taguear (sem re-subir):
```fish
restic tag --add rlm-qwen3-8b-teste:latest \
  --add c3b6bfbc3a9d36d62f871232aae75de3a6996eee5fd50b2982167773df6e262b c19275ec
```
**Colar:** o resultado, e um `restic snapshots --tag rlm-qwen3-8b-teste:latest`.

## 3. `restic check` + semear o cache de cobertura do P-12

```fish
restic check --read-data-subset=10%
```
**Colar:** a ultima linha (`no errors were found`).

Depois, escrever o cache que o P-12 le quando o HD nao esta (o `.diff` do P-12 espera
`~/.agata-backup-staging/p12-cobertura.json` no formato `{ "<name>": {"sha256": "...",
"verificado_em": "<ISO>", "snapshot": "<id>"} }`):

```fish
python3 /home/orusoua/agata/redesign/fase7-hd/semear_cache_p12.py
```
(script abaixo — le `restic snapshots --json`, cruza com o `manifest.json`, grava o cache.)

**Colar:** o conteudo do `p12-cobertura.json` gerado.

## 4. `cifrar_env.sh` — o `.env` cifrado dentro do repo restic

So depois de o Humano aprovar `redesign/propostas/cifrar-env.diff` (cria
`redesign/propostas/APROVADO-cifrar-env`) e o `.diff` estar aplicado ao
`scripts/cifrar_env.sh` (Fase 8, ou "vai" explicito). Ai:

```fish
scripts/cifrar_env.sh      # pede a senha GPG por prompt, 2x; poe o .gpg no repo restic
```
O `env-20260812.gpg` em `~/.agata-backup-staging/` e de **12/08** — desatualizado; esta
passada gera um novo.

**Colar:** as linhas `restic: env cifrado no repo ...` e `no errors were found`.

---

## Depois da passada — fechar o ciclo

1. `bash scripts/perimetro.sh` — se o P-12 ja estiver aplicado, `=== P-12 ===` deve dar
   **OK** (nao mais PARCIAL). Se algum artefato da lista FALHA ficou de fora, ele avisa qual.
2. Atualizar `redesign/STATUS.md` (P7-03 → parte feita), `LOG.md` (os `snapshot` ids, o
   `restic check`, o teste de restore), `ANCORA.md`, commit+push no `redesign`.
3. **Teste de restore** (aceite do ROADMAP): `restic restore <id> --target /tmp/scratch-xxx`
   de um dos IR, conferir o `ir_sha256_xmlbin` do restaurado contra o manifesto. Colar o
   `sha256sum`.

## O que NAO fazer

- Nao rodar `restic forget`/`prune` nesta passada (limpeza e decisao a parte).
- Nao apagar o `env-*.gpg` velho do staging antes de o novo estar no repo + `check` limpo.
- O blob do `rlm` via `sudo`: PARAR e pedir ao Humano (passo 2b).
