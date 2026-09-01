# P0-01 — tag `pre-redesign` + backup restic inicial + manifesto de modelos

**Objetivo:** congelar o estado pré-redesenho de forma reproduzível antes de qualquer
mudança de máquina.

**Pré-requisitos:** nenhum.

**Arquivos que a tarefa toca:**
- cria a tag git `pre-redesign` em `main`
- cria/atualiza `models/manifest.json` (na raiz do repo, branch `redesign`)
- cria o repositório restic em `AgataBkup01` (HD externo) — fora do repo

---

## Passos (blocos para o Humano colar no fish)

### 1. Confirmar estado limpo e criar a tag

O que faz: marca o commit atual de `main` como ponto de retorno.

```fish
cd $HOME/agata
git switch main
git status -sb
git tag -a pre-redesign -m "estado pré-redesenho do sistema local (MEMÓRIAS 309)"
git push origin pre-redesign
git tag --list pre-redesign
```

Colar de volta: a saída inteira.
Sucesso: `git status` limpo antes da tag; `git tag --list` mostra `pre-redesign`.
Desfazer: `git tag -d pre-redesign; git push origin :refs/tags/pre-redesign`.

### 2. Gerar o manifesto de modelos

O que faz: registra, por modelo Ollama, o `blob_sha256` (do arquivo de pesos), a origem
e o **Modelfile completo** — o suficiente para reconstruir sem depender do blob backupeado.

> **Correção P0-00:** o gerador antigo só guardava o `id` do Ollama e as 6 primeiras
> linhas do Modelfile. Isso não sustenta o aceite de "reconstrução". O gerador abaixo
> captura `blob_sha256` (64 hex, da linha `FROM .../blobs/sha256-...`), `blob_path`,
> `origem` e o Modelfile inteiro.

```fish
cd $HOME/agata
git switch redesign
python3 - <<'PY'
import json, subprocess, re, datetime
def sh(*a): return subprocess.run(a, capture_output=True, text=True).stdout
rows = []
for line in sh("ollama","list").splitlines()[1:]:
    p = line.split()
    if len(p) < 3: continue
    name = p[0]
    mf = sh("ollama","show","--modelfile",name)
    m = re.search(r"blobs/sha256-([0-9a-f]{64})", mf)
    blob_path = next((ln[5:].strip() for ln in mf.splitlines()
                      if ln.startswith("FROM ") and "/blobs/" in ln), None)
    base = name.split(":")[0]
    if base in ("qwen3.5","qwen2.5","qwen3","llama3.1","llama3.2","llama3.3",
                "gemma2","phi3","deepseek-r1"):
        origem = f"ollama registry: library/{base}"
    else:
        origem = "build local / tag custom -- reconstruir pelo modelfile + blob base"
    rows.append({"name": name, "ollama_id": p[1], "size_gb": p[2],
                 "blob_sha256": m.group(1) if m else None,
                 "blob_path": blob_path, "origem": origem, "modelfile": mf})
json.dump({"gerado_por": "P0-01",
           "gerado_em": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "n_modelos": len(rows), "modelos": rows},
          open("models/manifest.json","w"), ensure_ascii=False, indent=2)
print(len(rows), "modelos; sha256 em",
      sum(1 for r in rows if r["blob_sha256"]), "de", len(rows))
PY
git add models/manifest.json
git status -s
```

Colar de volta: a linha de contagem (`N modelos; sha256 em N de N`) e o `git status -s`.
Sucesso: `sha256 em N de N` (todos), e `models/manifest.json` staged.
Desfazer (não destrutivo): `git checkout -- models/manifest.json`.

### 3. **INSTALA SOFTWARE** — restic + repo de backup no HD externo

**Este passo instala um pacote e escreve no HD externo. Rode só com o HD `AgataBkup01` montado.**

```fish
# confirmar que o restic existe (ou instalar)
type -q restic; or sudo pacman -S --noconfirm restic
restic version
# achar o ponto de montagem do HD
lsblk -o NAME,LABEL,MOUNTPOINT | grep -i agatabkup
```

Colar de volta: `restic version` e a linha do `lsblk`.
Sucesso: `restic` responde a versão; o HD aparece montado.
Se o HD não estiver montado: pare aqui, marque P0-01 como bloqueado em `STATUS.md`,
siga para P0-02.

### 4. Inicializar o repo restic e a primeira cópia

O que faz: cria o repositório restic cifrado e faz o primeiro snapshot dos itens de config.
Ajuste `<MNT>` para o ponto de montagem real do passo 3.

```fish
set -x RESTIC_REPOSITORY <MNT>/restic-agata-local
set -x RESTIC_PASSWORD_FILE $HOME/.config/agata/restic.pass
mkdir -p $HOME/.config/agata
test -f $RESTIC_PASSWORD_FILE; or begin; openssl rand -base64 32 > $RESTIC_PASSWORD_FILE; chmod 600 $RESTIC_PASSWORD_FILE; end
restic init
restic backup $HOME/.hermes/config.yaml $HOME/agata/config $HOME/.config/agata $HOME/agata/models/manifest.json
restic snapshots
```

Colar de volta: a saída de `restic init`, `restic backup` (linha "Added to the repository")
e `restic snapshots`.
Sucesso: `restic snapshots` mostra 1 snapshot.
**Guarde o arquivo `$HOME/.config/agata/restic.pass` — sem ele o backup não abre.** Ele
NÃO vai para o git (é segredo).

---

## Aceite

- `git tag --list pre-redesign` retorna `pre-redesign` (local e no remoto).
- `models/manifest.json` existe no branch `redesign`, tem `blob_sha256` para **todos** os
  modelos e o Modelfile completo de cada um.
- `restic snapshots` mostra pelo menos 1 snapshot **OU** P0-01 está marcado como bloqueado
  em `STATUS.md` com o motivo "HD AgataBkup01 não montado".

## Rollback

Não destrutivo:
- `git tag -d pre-redesign` e depois `git push origin :refs/tags/pre-redesign`
- `git checkout -- models/manifest.json`

O repo restic é novo e isolado; normalmente não precisa desfazer. **Só se for
explicitamente necessário zerá-lo**, e como passo isolado com o Humano ciente:

> ⚠️ **DESTRUTIVO — apaga o repositório de backup. Rode sozinho, confirmando o caminho.**
> ```fish
> rm -rf <MNT>/restic-agata-local
> ```

## Registro

- `STATUS.md`: mover P0-01 para "Feito"; se o restic ficou pendente, anotar em "Bloqueios".
- `LOG.md`: nova entrada com o que rodou, a saída-chave (nº de snapshots, nº de modelos),
  e o `HEAD` no fim.
