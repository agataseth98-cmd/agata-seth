# P3-02 — prune (REMOÇÃO DESTRUTIVA de modelos)

**Objetivo:** remover do Ollama os modelos que `models/PRUNE.md` marca `REMOVER` e o
Humano aprovou item a item. Libera ~100–180 GB conforme a lista.

**Pré-requisitos:** P3-00 FEITO (reconstrutibilidade provada) · P3-01 FEITO (`PRUNE.md`) ·
**aprovação explícita do Humano, item a item, do `PRUNE.md`** · manifesto commitado e
empurrado no branch (o registro de como reconstruir).

> ⚠️ **TAREFA DESTRUTIVA.** Apaga arquivos de peso de modelo — irreversível a não ser
> pela reconstrução (pull de rede / GGUF guardado). Classe de risco máxima:
> - Revisão de plano por 2º par de olhos **obrigatória** antes.
> - Cada `ollama rm` é mostrado **sozinho**, em bloco próprio, com o nome do modelo
>   explícito. Nunca uma lista de `rm` embutida noutro bloco.
> - Rodar **um por vez**, conferindo `ollama list` e `du -sh` entre cada um.
> - Antes do 1º `rm`: confirmar que `models/manifest.json` no `origin/redesign` está
>   atualizado (`git log origin/redesign -1 -- models/manifest.json`).

---

## Passos

### 1. Pré-checagem (não destrutiva)

```fish
cd $HOME/agata
git fetch origin
echo "manifesto no remoto:"; git log --oneline origin/redesign -1 -- models/manifest.json
echo "du antes:"; du -sh /usr/share/ollama/.ollama/models
ollama list
# guardar a lista de antes
ollama list > /tmp/p3_ollama_antes.txt
```
Colar de volta: tudo. **Se o manifesto no remoto não refletir o estado atual dos modelos
a manter, PARE** — commite o manifesto primeiro.

### 2. Remover — UM modelo por bloco

Para **cada** modelo aprovado como `REMOVER` no `PRUNE.md`, um bloco isolado assim:

> ⚠️ **DESTRUTIVO — remove o modelo `<NOME>` do Ollama. Rode sozinho.**
> ```fish
> ollama rm <NOME>
> ollama list | grep -c .        # contagem de modelos, deve cair 1
> du -sh /usr/share/ollama/.ollama/models
> ```
> Colar de volta: o `du` (o quanto caiu) e o `ollama list` novo.

Ordem sugerida: do maior blob exclusivo para o menor (`llama3.3:70b` primeiro), para o
ganho aparecer cedo e um erro ser pego antes de ir longe.

### 3. Conferência final

```fish
cd $HOME/agata
ollama list
diff /tmp/p3_ollama_antes.txt <(ollama list)     # mostra só o que saiu
du -sh /usr/share/ollama/.ollama/models
# os modelos da keep-list ainda respondem?
for M in qwen3.5:9b rlm-qwen3-8b-teste:latest <4B-base> nomic-embed-text:latest
    echo "--- $M ---"
    ollama run $M "responda apenas: ok" --keepalive 0
end
```
Colar de volta: o `diff`, o `du` final, e o "ok" de cada modelo da keep-list.

### 4. Regenerar o manifesto (agora só com o que ficou)

```fish
cd $HOME/agata
git switch redesign
# o gerador de P0-01 (está no arquivo-tarefa P0-01, passo 2) — rodar de novo:
# ... produz models/manifest.json só com os modelos que sobraram
git add models/manifest.json
git status -s
```

---

## Aceite

- `ollama list` == keep-list do `PRUNE.md` (nada a mais, nada a menos).
- Cada modelo da keep-list responde `ok`.
- `du -sh` do dir de blobs caiu ~o total previsto no `PRUNE.md` (± margem de blob compartilhado).
- `models/manifest.json` regenerado, `blob_sha256` em 100% dos modelos restantes,
  commitado no branch.
- `ollama list` + (na P3-03) os backends llama.cpp batem com o manifesto.

## Verificação independente

- **Quem:** Humano (autoriza cada `rm`) + uma sessão independente confere o manifesto
  regenerado contra `ollama list` (S7).
- **O quê:** que só saiu o que estava aprovado; que a keep-list está intacta e funcional;
  que o manifesto novo reconstrói cada modelo restante (spot-check de 1, como na P3-00).
- **Como:** `diff` das listas; 1 reconstrução em daemon isolado.
- **Resultado:** anotar no LOG (quais modelos saíram, GB liberado, `HEAD`).

## Rollback

**Parcial e caro:** reconstruir um modelo removido por engano —
`ollama pull <name>` (classe registry) ou `ollama create -f <Modelfile do manifesto>`
(classe custom, se o blob base ainda existir). Modelo custom-gguf cujo GGUF não foi
guardado: **perda definitiva** — por isso o gate P3-00.

## Registro

- `STATUS.md`: P3-02 → "Feito"; lista dos modelos removidos + GB liberado + `du` final.
- `LOG.md`: entrada com a lista removida, o `diff` de `ollama list`, o `du` antes/depois,
  o resultado da verificação independente, `HEAD` no fim.
