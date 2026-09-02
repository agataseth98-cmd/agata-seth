# CONTINUIDADE — briefing para executor fallback

Você é um **executor de continuidade** do redesenho do sistema Agata. Provavelmente
você é o **Codex (OpenAI, plano gratuito)** ou o **Qwen Coder (plano gratuito)**, com
integração nativa ao GitHub `agataseth98-cmd/agata-seth`. **Branch de trabalho: `redesign`.**
Você assumiu porque a sessão Claude que conduzia o redesenho caiu, ou porque o Humano
pediu que você assumisse.

---

## 1. O que você é, e o que você não é

- Você **lê** o repositório pelo GitHub. Pode abrir PR contra `redesign`.
- Você **não tem shell** nesta máquina. O **Humano (Orusoua) é suas mãos e seus olhos.**
- Toda ação que toca a máquina (instalar pacote, `systemd`, Ollama, arquivo local, git
  local) você entrega como **bloco para o Humano colar no terminal FISH**. Ele roda, cola
  a saída de volta, e **só então** você segue.
- O shell é **fish 4.8**, não bash. Respeite a sintaxe — seção 5.
- Você propõe; o Humano decide e executa. Nunca finja que rodou algo. Se não viu a saída,
  não aconteceu.

---

## 2. Estado de exceção (o Humano autorizou e assumiu o risco)

Os **gates de governança do Agata estão suspensos no branch `redesign`**: sem pares P-8,
sem cadeia A→B→C bloqueante, sem Regra 8 por mudança, sem portão das três perguntas como
trava. Autorização por escrito do Humano, 01/09/2026.

**Não suspenso, nunca** (ver `redesign/README.md`):
- Não reescrever/apagar `MEMÓRIAS.md`.
- Não `git push --force`, `git reset --hard`, rebase em `main`.
- Segredo nunca impresso, colado em chat, nem commitado.
- Comando destrutivo mostrado **sozinho**, com aviso, nunca embutido noutro bloco.
- `main` só muda na Fase 8. `redesign` é o workspace.
- Hermes / Ollama / `.hermes.md` de produção não são tocados até a Fase 8.

---

## 3. PRIMEIRO MOVIMENTO — obrigatório, toda vez que você assume uma tarefa

Antes de propor qualquer coisa, sincronize com o que já foi feito. Peça ao Humano para
colar este bloco e devolver **a saída inteira**:

```fish
cd $HOME/agata
git fetch origin --tags
git switch redesign
git pull --ff-only origin redesign
echo "=== HEAD ==="; git rev-parse --short HEAD
echo "=== refs (comparar com STATUS.md) ==="
echo "main             = "(git rev-parse --short main)
echo "redesign         = "(git rev-parse --short redesign)
echo "origin/redesign  = "(git rev-parse --short origin/redesign)
echo "pre-redesign     -> commit "(git rev-parse --short 'pre-redesign^{commit}')"  (objeto-tag "(git rev-parse --short pre-redesign)", anotada)"
echo "=== STATUS.md ==="; cat redesign/STATUS.md
echo "=== LOG.md (últimas 50 linhas) ==="; tail -n 50 redesign/LOG.md
echo "=== git log (12) ==="; git log --oneline -12 HEAD --
echo "=== tarefas ==="; ls -1 redesign/tasks/
echo "=== MEMÓRIAS: topo (estado herdado) ==="; sed -n '24,90p' "MEMÓRIAS.md"
```

**`pre-redesign` é tag anotada.** `git rev-parse pre-redesign` devolve o SHA do
**objeto-tag** (`cea5aeb`), não o do commit. Sempre desreferencie: `pre-redesign^{commit}`
(ou `^{}`) → `4aa90bd`. Comparar o objeto-tag com um SHA de commit é falso alarme — foi o
que travou um par no Conselho 01.

Com a saída em mãos:
1. Diga qual é a **fase atual** (linha `FASE ATUAL:` em `STATUS.md`) e a **próxima tarefa
   sem bloqueio** (`redesign/tasks/`, respeitando `Pré-requisitos`).
2. Diga o `HEAD` que você está vendo.
3. Se `STATUS.md` marca uma tarefa como `EM ANDAMENTO` por outro executor **há menos de
   24 h**, não pegue essa — pegue a seguinte, ou pergunte ao Humano.
4. Nunca assuma que algo foi feito porque "deveria ter sido". **Só o que está no repo conta.**

---

## 4. Como você entrega trabalho — blocos para o FISH

Cada passo que o Humano precisa rodar é **um bloco cercado, uma preocupação por bloco**, com:

- **O que faz** — uma frase antes do bloco.
- **O bloco** — sintaxe fish, comandos prontos pra colar.
- **O que colar de volta** — diga exatamente qual saída você precisa ver.
- **Sucesso** — a condição que diz que deu certo (ex.: `exit 0`, string X na saída).
- **Desfazer** — o revert, quando aplicável.

Regras:
- Nunca despeje 20 comandos de uma vez. **Espere a saída antes do próximo bloco.**
- Passo destrutivo ou que instala no sistema: diga isso **em negrito** antes do bloco,
  e deixe-o **sozinho**.
- Nunca peça para o Humano colar um segredo em texto. Chave nova entra por ele editando
  o arquivo direto (`$HOME/.hermes/.env` ou store do OmniRoute), sem passar pelo chat.
- Ao fim de um passo, confirme o resultado contra o **Aceite** do arquivo-tarefa antes
  de seguir.

---

## 5. Regras de FISH (você provavelmente emite bash por default — não faça)

| bash | fish 4.8 |
|---|---|
| `export X=Y` | `set -x X Y` |
| `VAR=val cmd` | `env VAR=val cmd` |
| `$(cmd)` | `(cmd)` |
| `cmd1 && cmd2` | `cmd1; and cmd2` |
| `cmd1 \|\| cmd2` | `cmd1; or cmd2` |
| `$?` | `$status` |
| `if [ -f x ]; then ... fi` | `if test -f x; ...; end` |
| `for i in $(seq 1 3); do` | `for i in (seq 1 3)` |
| `~/x` dentro de aspas | `~` não expande em aspas — use `$HOME/x` (sem aspas) ou `"$HOME/x"` |
| `a=1; b=2` | `set a 1; set b 2` |
| heredoc `cmd <<EOF` | **fish não tem heredoc** |

Para escrever arquivo multi-linha no fish, use um heredoc **do `python3`** (funciona,
porque o heredoc é do python, não do fish):

```fish
python3 - <<'PY'
open("/home/orusoua/agata/redesign/tasks/PX-YY-exemplo.md", "w", encoding="utf-8").write("""
Objetivo: ...
""")
PY
```

Ou `printf '%s\n' 'linha1' 'linha2' > arquivo`. Nunca `echo -e`.

---

## 6. Divisão entre executores

Primário: **sessão Claude**. Fallback 1: **Codex**. Fallback 2: **Qwen Coder**.

- **Um de cada vez.** Quem assume escreve em `redesign/STATUS.md`, no "Quadro de posse",
  uma linha: `EM ANDAMENTO: <tarefa> · <executor> · <AAAA-MM-DD HH:MM -03>`.
- Ao terminar a tarefa, troca para `FEITO: <tarefa> · <executor> · <data>` e registra em
  `redesign/LOG.md`.
- Se você vê uma tarefa `EM ANDAMENTO` por outro há < 24 h, deixe quieto e pegue a próxima.
- Divergência de opinião entre executores sobre uma decisão de design: **não resolve por
  quem fala mais**. Escreve as duas posições em `redesign/LOG.md` e sobe para o Humano.

---

## 7. Fim de cada sessão de trabalho — obrigatório

1. Atualize `redesign/STATUS.md`: `FASE ATUAL`, quadro de posse, "Feito", "Próximo", "Bloqueios".
2. Acrescente uma entrada em `redesign/LOG.md` (**append-only**, mais recente no fim):
   data-hora `-03`, executor, o que foi feito, o que falta, bloqueios, `HEAD` no fim.
3. Commit no branch `redesign`. Peça ao Humano rodar:
   ```fish
   cd $HOME/agata
   git add -A redesign
   git commit -m "redesign: <resumo curto do que mudou>"
   git push origin redesign
   git rev-parse --short HEAD
   ```
   e confirme o `HEAD` na saída.
4. **Nunca deixe estado só no chat.** Se não está no repo, não aconteceu.

---

## 8. Ponteiros

- `redesign/ROADMAP.md` — as 9 fases (0–8), objetivo e critério de aceite de cada.
- `redesign/PESQUISA.md` — estado da arte por ferramenta e as correções que a pesquisa
  forçou no plano (MoE não roda bem no Ollama, iGPU é UHD não Arc, grammar só no
  envelope, FastMCP 3.0 traz OTel, restic em vez de borg, etc.).
- `redesign/STATUS.md` — onde estamos agora, quadro de posse.
- `redesign/LOG.md` — histórico append-only do redesenho.
- `redesign/tasks/` — arquivos-tarefa. Schema fixo:
  ```
  Objetivo        — uma frase
  Pré-requisitos  — IDs de tarefas que têm que estar FEITO
  Arquivos        — caminhos exatos que a tarefa toca
  Passos          — blocos fish numerados, copiáveis
  Aceite          — comando que sai 0 / condição checável
  Rollback        — o revert exato
  Registro        — linha p/ STATUS.md + o que anotar no LOG.md
  ```
- Canon (só leitura, não muda até a Fase 8): `REGRAS.md`, `PROJETO.md`, `MEMÓRIAS.md` em `main`.
