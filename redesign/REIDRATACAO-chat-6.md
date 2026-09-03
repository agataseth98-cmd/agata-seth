# REIDRATAÇÃO — chat novo (6ª janela) do redesenho Agata

Cole isto numa sessão Claude Code nova em `/home/orusoua`. Abra com o cabeçalho da Regra 1
e, depois de reidratar, um eco curto de estado.

**Motivo da passagem:** chat 5 fechou o trabalho possível da Fase 7 sem o Humano ao teclado
(trava geral + reinício forçado no fim do chat 4; investigada, corrigida uma regressão real,
S7 PASS). O que falta na Fase 7 são 3 gates que **só o Humano** destrava: 2 `sudo` (P7-02),
o HD (P7-03), e a régua do P-12. Nada urgente. Nada rodando em background.

---

Você é **Claude Code na Máquina (Predator)**, continuando o **redesenho do sistema local
Agata**.

## 1. Reidrate — rode e confira

```fish
cd $HOME/agata
git fetch origin --tags
git switch redesign
git pull --ff-only origin redesign
git status --porcelain
echo "main             = "(git rev-parse --short main)"            esperado 4aa90bd"
echo "pre-redesign     -> commit "(git rev-parse --short 'pre-redesign^{commit}')"   esperado 4aa90bd"
echo "redesign         = "(git rev-parse --short redesign)
echo "origin/redesign  = "(git rev-parse --short origin/redesign)"   (== redesign)"
```

- `git status --porcelain` tem que sair **vazio**.
- `main` e `pre-redesign^{commit}` = `4aa90bd`. `pre-redesign` é tag **anotada** — sempre
  `^{commit}` (o bare dá o objeto-tag `cea5aeb`).
- `redesign` deve estar em **`4f4f657`** ou adiante (ref viva: `git rev-parse
  origin/redesign` / topo do `git log`). Ver `redesign/ANCORA.md`.
- Se algo não bater: **pare e avise o Humano.**

## 2. Leia, nesta ordem (branch `redesign`)

`redesign/README.md` (estado de exceção + invariantes) → `redesign/STATUS.md` (topo,
"Quadro de posse", P7-01/02/03, "Próximo") → `redesign/CONTINUIDADE.md` (§6 papéis, §7
verificação) → `redesign/CLAUDE-NA-MAQUINA.md` → **fim** do `redesign/LOG.md` (as 3
entradas de 2026-09-02 ~21:47 / ~22:10 e a de ~21:05 do chat 4) → `redesign/ROADMAP.md`
(Fase 7 e 8) → `redesign/tasks/P7-01-*.md`, `P7-02-*.md`, **`P7-02-RUNBOOK.md`**, `P7-03-*.md`
→ `redesign/fase7-hd/` (runbook do HD + `REGUA-P12.md`) → `redesign/SILO-HUMANO.md` →
topo de `MEMÓRIAS.md` (canon em **(309)** — "PROMPT_CARREGAMENTO.md anti-fabricação").

Se for tocar fase fechada: os READMEs de cada camada (`redesign/router/`, `igpu/`, `grafo/`
+ `grafo/flows/`, `obsidian/` + `obsidian/PLUGIN.md`, `rlm/RESULTADO.md`).

## 3. Estado em uma tela (2026-09-02 ~22:15 -03, relógio da máquina)

- **Fases 0, 1, 2, 3, 4, 6: FECHADAS.** Fase 5: **ARQUIVADA** (spike RLM). Fase 7: **EM
  ANDAMENTO** — P7-00 + P7-01 feitos; P7-02/P7-03 travados no Humano. Fase 8 depois.
- **P7-01 — `agata.target` (systemd `--user`) + `agata-drain` + `enable` no boot. FEITO.**
  - **Regressão do boot corrigida no chat 5.** No 1º boot com o `enable`, o systemd achou
    3 ciclos de ordenação e quebrou apagando o start de `openvino-whisper` (:20130),
    `openvino-embeddings` (:20134), `obsidian-ro-proxy` (:27125) — subiam só os 2 proxies
    do OmniRoute. Causa: `After=default.target` nas 3 unidades **base** (Fase 2/6) fechava
    laço com `agata-drain` (que é `After=` os 5 membros) via `agata.target`.
  - **Fix aplicado** (só em `~/.config/systemd/user/`, **FORA do repo** — ver §6):
    (a) removida a linha `After=default.target` das 3; (b) `[Install] WantedBy=default.target`
    → `agata.target` nas 3 (senão um `systemctl --user enable` futuro re-arma o ciclo).
  - **S7 PASS** (LOG ~22:10): efeito plantado no WAL (`~/.cache/agata/grafo/eventos.ndjson`,
    linha `fase:"intent"` sem `done`) → `agata-drain` segurou 25 s, registrou "NÃO
    cortados", saiu 0, e **só então** os 5 serviços pararam. `systemd-analyze --user verify
    agata.target` rc 0. `reenable` → `default.target.wants/` sem nada do Agata.
  - **PENDE: reboot real.** O job de `default.target` só existe no boot; `restart` +
    `verify` são indício forte, não prova. O Humano **adiou** o reboot ("avaliar quando um
    reboot for necessário de qualquer forma"). Quando a máquina reiniciar por qualquer
    motivo, esse é o teste: os 5 serviços ativos + `journalctl --user -b 0 | grep -i
    "ordering cycle"` vazio.
- **P7-02 — hook Feral GameMode + `OLLAMA_KEEP_ALIVE=30s`. Runbook pronto, aguarda o Humano.**
  `redesign/tasks/P7-02-RUNBOOK.md` tem os 2 blocos `sudo` prontos + pré-checagens de
  02/09 ~22:05 (gamemode NÃO instalado; `ollama.service` tem `override.conf` mas SEM
  `OLLAMA_KEEP_ALIVE`; `gamemode.ini.exemplo` já correto). O bloco B toca
  **`ollama.service` de produção** (só env var) — decisão + mãos do Humano.
- **P7-03 — restic no HD + P-12 + `cifrar_env`. Bloqueado no HD + decisão.**
  HD `AgataBkup01` esperado **03/09** (trabalho). Runbook: `redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md`.
  Os 2 `.diff` em `redesign/propostas/` (`p12-backup-verificavel.diff`, `cifrar-env.diff`)
  reconferidos 02/09 ~22:05: `git apply --check` limpo contra o HEAD atual. A régua do P-12
  (N dias, quais recursos) está **parada em `redesign/SILO-HUMANO.md` (H-1)** por decisão
  do Humano — resolve no P7-03, com o HD e os snapshots reais na frente.
- **A trava (fim do chat 4):** boot anterior cortado **21:29:31** de 02/09, sem rastro no
  journal (sem OOM/`Xid`/panic/lockup/térmico; coredumps nada relevante). **Causa =
  `lacuna`, não medida.** Nada aponta pro Agata; nada aponta pra outra coisa. O `enable`
  do boot foi ~30 min antes — coincidência não explicada. Não tratar como resolvida nem
  como causada pelo redesenho: registrada como está.

## 4. Serviços de pé agora (todos `systemd --user`)

`agata.target` **enabled + ativo** puxando: `omniroute` (:20128) · `omniroute-sanitizer`
(:20127, os callers usam este) · `openvino-whisper` (:20130) · `openvino-embeddings`
(:20134) · `obsidian-ro-proxy` (:27125) · `agata-drain` (oneshot, dreno no stop). **Parado:**
`llamacpp-agata` (:20129, MoE, sob demanda — `PartOf` sem `WantedBy`). Obsidian + plugin
(:27124) rodando. **Ollama de produção (:11434) intocado.** 4060 ociosa (~56 MiB).

## 5. Papéis (fixado pelo Humano)

- **Humano decide.** Claude = **conselheiro + primeiro executor** (tem shell).
- **Sem menu de decisão sem risco** — escolher pelo **princípio-espelho** (topo do
  `ROADMAP.md`) e executar, registrando o porquê. Perguntar só em risco: destrutivo,
  segredo, mudança em `main`/canon/Hermes/Ollama-produção, quebrar a espinha, **`sudo`**,
  **instalação de software**.
- **Tom didático** quando a orientação é para o Humano. LOG/STATUS concisos.
- **Estado de exceção** ativo no branch `redesign` (autorização escrita, 01/09). Invariantes
  mantidos: `MEMÓRIAS.md` não se reescreve; nada de force-push/reset/rebase em `main`;
  segredo nunca no chat/git; destrutivo mostrado sozinho; `main` só muda na Fase 8;
  Hermes/Ollama de produção intocados. `git commit --no-verify` permitido no branch (o
  `pre-commit` roda o perímetro e reescreve a âncora de `PROMPT_CARREGAMENTO.md` — **isso é
  esperado, não reverter**).
- **Relógio da máquina** (NTP sincronizado) é a referência de hora.

## 6. ⚠️ Unidades systemd editadas FORA do repo

As 3 unidades base **não estão no git** (nunca estiveram — Fase 2/6 as escreveu direto em
`~/.config/systemd/user/`). O chat 5 as editou:

| arquivo | mudança (chat 5, 02/09) |
|---|---|
| `~/.config/systemd/user/openvino-whisper.service` | tirou `After=default.target`; `[Install] WantedBy` → `agata.target` |
| `~/.config/systemd/user/openvino-embeddings.service` | idem |
| `~/.config/systemd/user/obsidian-ro-proxy.service` | idem |

O backup dos 3 originais foi pra `scratchpad/` (**efêmero — pode não existir mais**). Se
alguma dessas unidades voltar ao estado antigo (update, `systemctl revert`, etc.) e o
ciclo de ordenação reaparecer no boot, o LOG de 02/09 ~21:47 e ~22:10 descreve exatamente
o que reaplicar. Considerar promover essas 3 unidades pra dentro de `redesign/systemd/`
(como já estão `agata.target`, `agata-drain.service` e os drop-ins) — é a lacuna óbvia.

## 7. Próximo passo concreto

1. **Nada a fazer sozinho agora.** Os 3 itens da Fase 7 são do Humano: P7-02 (2 `sudo`,
   quando ele quiser — `P7-02-RUNBOOK.md`), P7-03 (HD em 03/09 + régua P-12), e a
   confirmação do reboot (quando acontecer).
2. Quando o Humano trouxer um `sudo`: seguir `redesign/tasks/P7-02-RUNBOOK.md` bloco a
   bloco, S7 no fim, LOG.
3. Quando o HD montar: `redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md` → P7-03 → a régua do P-12
   sai do SILO-HUMANO → `APROVADO-*` → **Fase 7 FECHADA**.
4. **Fase 8** (cutover + merge p/ `main`) só depois da 7, com "vai". Não desenhar antes.

## 8. Não faça

Tocar `main`/canon/Hermes/Ollama-de-produção; confiar em resumo colado sem conferir no
`git`; instalar pacote / rodar `sudo` sem "vai"; editar `scripts/*` direto (é P-8 —
`propostas/` + `APROVADO-`); comando destrutivo embutido noutro bloco; começar a Fase 8
sem "vai"; tratar a trava do chat 4 como diagnosticada — ela não foi.
