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

O que faz: registra nome, tamanho, digest e Modelfile de cada modelo Ollama, para
reconstrução sem depender do blob.

```fish
cd $HOME/agata
git switch redesign
python3 - <<'PY'
import json, subprocess
out = subprocess.run(["ollama","list"], capture_output=True, text=True).stdout
rows = []
for line in out.splitlines()[1:]:
    p = line.split()
    if len(p) < 3: continue
    name = p[0]
    mf = subprocess.run(["ollama","show","--modelfile",name], capture_output=True, text=True).stdout
    rows.append({"name": name, "id": p[1], "size": p[2],
                 "modelfile_first_lines": mf.splitlines()[:6]})
json.dump({"gerado": "P0-01", "modelos": rows}, open("models/manifest.json","w"),
          ensure_ascii=False, indent=2)
print(len(rows), "modelos registrados")
PY
git add models/manifest.json
git status -s
```

Colar de volta: a contagem de modelos e o `git status -s`.
Sucesso: `models/manifest.json` existe e lista os modelos de `ollama list`.
Desfazer: `git checkout -- models/manifest.json` (ou `rm` se novo).

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
Desfazer: não precisa — repo restic novo, isolado. Se quiser zerar: `rm -rf <MNT>/restic-agata-local`.

---

## Aceite

- `git tag --list pre-redesign` retorna `pre-redesign` (local e no remoto).
- `models/manifest.json` existe no branch `redesign` e lista os modelos.
- `restic snapshots` mostra pelo menos 1 snapshot **OU** P0-01 está marcado como bloqueado
  em `STATUS.md` com o motivo "HD AgataBkup01 não montado".

## Rollback

- `git tag -d pre-redesign; git push origin :refs/tags/pre-redesign`
- `git checkout -- models/manifest.json`
- repo restic é isolado; apagar a pasta se necessário.

## Registro

- `STATUS.md`: mover P0-01 para "Feito"; se o restic ficou pendente, anotar em "Bloqueios".
- `LOG.md`: nova entrada com o que rodou, a saída-chave (nº de snapshots, nº de modelos),
  e o `HEAD` no fim.
