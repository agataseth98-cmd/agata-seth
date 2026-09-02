# P3-00 — manifesto completo + prova de reconstrutibilidade (gate antes de qualquer prune)

**Objetivo:** garantir que `models/manifest.json` reconstrói **qualquer** modelo que a
Fase 3 decidir manter — testado de verdade num scratch, **sem apagar nada**. É a trava de
segurança que tem que passar antes do P3-02 (prune destrutivo).

**Pré-requisitos:** Fase 1 FECHADA. Fase 3 com o "vai" do Humano.

**Arquivos que a tarefa toca (branch `redesign`):**
- `models/manifest.json` — enriquecer se faltar campo (hoje: 20 modelos, `blob_sha256`
  em 20/20, `origem`, `modelfile` completo — de P0-00)
- `models/RECONSTRUCAO.md` (novo) — o método de reconstrução por classe de modelo + o
  resultado do teste
- `redesign/tasks/P3-00-*.md`

---

## Fatos do estado atual (2026-09-02)

- Modelos em `/usr/share/ollama/.ollama/models/` (daemon roda como user `ollama`;
  `ollama rm` vai pelo daemon, **sem sudo**).
- **Blobs são compartilhados.** Ex.: `qwen3.5:9b` e `qwen3.5-9b-64k` apontam para o mesmo
  blob `sha256-dec52a4456…`; o 64k é só `+ PARAMETER num_ctx 65536`. Somar os `size_gb`
  do manifesto **superestima** o que um prune libera — o `ollama` só apaga um blob quando
  nenhum modelo o referencia. A medida real é `du -sh` do dir de blobs antes/depois.
- Duas classes de `origem` no manifesto:
  - `ollama registry: library/<x>` → reconstrói com `ollama pull <name>` (precisa de rede).
  - `build local / tag custom` → reconstrói com o Modelfile salvo + o blob base. Se o blob
    base também for de registry, ok; se for um GGUF importado à mão, **precisa do arquivo
    GGUF de origem** — é o caso a investigar aqui.

---

## Passos

### 1. Auditar o manifesto — cada modelo tem o suficiente para reconstruir?

```fish
cd $HOME/agata
python3 - <<'PY'
import json, os, subprocess, re
d = json.load(open("models/manifest.json"))
blobs_dir = "/usr/share/ollama/.ollama/models/blobs"
for m in d["modelos"]:
    mf = m.get("modelfile","")
    froms = re.findall(r"^FROM\s+(.+)$", mf, re.M)
    base = froms[0] if froms else None
    tipo = ("registry" if "registry:" in m.get("origem","") else "custom")
    blob_ok = bool(m.get("blob_sha256"))
    # o FROM aponta para um blob local? esse blob existe?
    blob_local = base and base.startswith("/") and os.path.exists(base)
    print(f"{m['name']:<30} tipo={tipo:<9} sha256={'ok' if blob_ok else 'FALTA':<6} "
          f"FROM={'blob-local' if blob_local else (base or '?')[:50]}")
PY
```
Colar de volta: a tabela.
**Sinal de alerta:** modelo `custom` cujo `FROM` aponta para um GGUF que não é de registry
e não está referenciado por nenhum outro modelo → esse GGUF **precisa ser preservado** (ou
o modelo entra na lista de "não dá pra reconstruir → decidir manter ou aceitar perda").

### 2. Escolher 1 modelo de cada classe e reconstruir num scratch (SEM apagar o original)

```fish
cd $HOME/agata
set SC (mktemp -d /tmp/p3-recon-XXXX)
set -x OLLAMA_MODELS $SC/ollama    # daemon de teste isolado, NÃO o de produção
mkdir -p $OLLAMA_MODELS
# subir um ollama serve isolado noutra porta
env OLLAMA_HOST=127.0.0.1:11500 OLLAMA_MODELS=$SC/ollama ollama serve &
set OPID $last_pid
sleep 3

# classe registry: reconstruir por pull
env OLLAMA_HOST=127.0.0.1:11500 ollama pull qwen3.5:9b
# classe custom (blob compartilhado): recriar pelo Modelfile
python3 -c "import json;print(next(m['modelfile'] for m in json.load(open('models/manifest.json'))['modelos'] if m['name']=='qwen3.5-9b-64k:latest'))" > $SC/Modelfile.64k
# trocar o FROM /blob por FROM qwen3.5:9b (o blob compartilhado já veio do pull acima)
sed -i 's#^FROM /.*#FROM qwen3.5:9b#' $SC/Modelfile.64k
env OLLAMA_HOST=127.0.0.1:11500 ollama create qwen3.5-9b-64k:recon -f $SC/Modelfile.64k

# conferir: o blob_sha256 do recriado bate com o do manifesto?
env OLLAMA_HOST=127.0.0.1:11500 ollama show qwen3.5-9b-64k:recon --modelfile | grep -oE 'sha256-[0-9a-f]{64}'
python3 -c "import json;print('manifesto:', next(m['blob_sha256'] for m in json.load(open('models/manifest.json'))['modelos'] if m['name']=='qwen3.5-9b-64k:latest'))"

# parar o daemon de teste e limpar
kill $OPID
rm -rf $SC
```
Colar de volta: os dois sha256 (recriado vs manifesto) e o exit de cada `ollama`.
**Sucesso:** o `sha256` do blob de pesos do modelo recriado == o `blob_sha256` do
manifesto, para os dois casos testados (registry e custom).

### 3. `RECONSTRUCAO.md`

Escrever `models/RECONSTRUCAO.md`: por classe (`registry` / `custom-param` /
`custom-gguf`), o comando exato de reconstrução, e a tabela do passo 1 marcando quais
modelos são reconstrutíveis e quais dependem de um GGUF que precisa ser guardado.

---

## Aceite

- Todo modelo do manifesto cai numa de 3 classes com método de reconstrução escrito.
- Pelo menos 1 modelo de classe `registry` e 1 de classe `custom` foram **reconstruídos
  num daemon ollama isolado** e o `blob_sha256` bateu com o manifesto.
- `models/RECONSTRUCAO.md` lista explicitamente qualquer modelo **não** reconstrutível
  só com o manifesto (→ vira decisão no P3-01: manter, ou guardar o GGUF, ou aceitar perda).
- **Nada foi apagado.** `ollama list` (produção) idêntico ao de antes.

## Verificação independente

- **Quem:** fallback afinado ou Humano.
- **O quê:** que o teste rodou num daemon **isolado** (`OLLAMA_MODELS` próprio, porta
  11500) e não tocou `/usr/share/ollama/`; que o sha256 comparado é o do **blob de pesos**
  (linha `FROM …/blobs/sha256-…`), não de outra camada.
- **Como:** reler os comandos; `ls -la /usr/share/ollama/.ollama/models/blobs | wc -l`
  antes e depois (igual); `ollama list` diff.
- **Resultado:** anotar no LOG.

## Rollback

Nada a desfazer (nada foi apagado). `git checkout -- models redesign/tasks/P3-00-*.md`
desfaz o rastreado. O daemon de teste e o scratch são temporários.

## Registro

- `STATUS.md`: P3-00 → "Feito"; anotar quantos modelos são reconstrutíveis / quantos
  dependem de GGUF preservado.
- `LOG.md`: os sha256 comparados, o resultado da verificação independente, `HEAD` no fim.
