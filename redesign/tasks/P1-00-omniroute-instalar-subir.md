# P1-00 — instalar OmniRoute e subir o gateway em :20128

**Objetivo:** ter o `omniroute` rodando local em `:20128` (endpoint OpenAI-compatível +
dashboard), isolado, sem nenhum provedor ainda configurado — a base da Fase 1.

**Pré-requisitos:** P0-02 FEITO (o servidor MCP e o venv já mostram o padrão de isolamento).
Fase 1 recebeu o "vai" do Humano.

**Arquivos que a tarefa toca (fora do repo, exceto o registro):**
- instala o pacote `omniroute` (ver passo 1 — AUR ou npm global, decidir na hora pelo que
  estiver são no CachyOS)
- `~/.config/omniroute/` (ou o dir de config que a versão usar) — só a config do gateway,
  **sem chaves** neste passo
- `redesign/tasks/P1-00-omniroute-instalar-subir.md` (este arquivo, marca FEITO)

---

## Passos (blocos para o fish)

### 1. **INSTALA SOFTWARE** — OmniRoute

> **Instala pacote no sistema. Rode sozinho. Revisão de plano por 2º par de olhos antes
> (CONTINUIDADE §7, classe de risco: instala-pacote).**

Confirmar a via de instalação atual em `github.com/pitbaden/omniroute` (a pesquisa de
01/09/2026 viu: npm global `omniroute`, além de AUR / Docker / pnpm / Nix; sobe API +
dashboard em `:20128`; MIT). Preferir, nesta máquina (CachyOS/Arch):

```fish
# opção A -- AUR (preferida se o pacote existir e a PKGBUILD estiver limpa)
paru -Si omniroute        # inspecionar antes
paru -S omniroute

# opção B -- npm global (fallback), se AUR não servir
type -q npm; or sudo pacman -S --noconfirm nodejs npm
npm install -g omniroute
```

Colar de volta: o comando usado e a saída de `omniroute --version` (ou equivalente).
Sucesso: binário instalado, versão impressa.

### 2. Subir o gateway (foreground, primeiro teste)

```fish
omniroute            # ou `omniroute serve` / `omniroute start` -- confirmar o subcomando
```

Em outro terminal:

```fish
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:20128/            # dashboard
curl -s http://127.0.0.1:20128/health; echo                                 # se existir
curl -s http://127.0.0.1:20128/v1/models; echo                              # OpenAI-compat
```

Colar de volta: os 3 resultados.
Sucesso: dashboard responde (200/301/302); `/v1/models` responde JSON (lista vazia ou não).

### 3. Rodar como serviço de usuário (systemd --user), sem habilitar no boot ainda

```fish
mkdir -p $HOME/.config/systemd/user
printf '%s\n' \
  '[Unit]' \
  'Description=OmniRoute AI gateway (Agata, Fase 1)' \
  'After=network-online.target' \
  '' \
  '[Service]' \
  'ExecStart=%h/.local/bin/omniroute'  \
  'Restart=on-failure' \
  'Environment=OMNIROUTE_PORT=20128' \
  '' \
  '[Install]' \
  'WantedBy=default.target' \
  > $HOME/.config/systemd/user/omniroute.service
# ATENÇÃO: conferir o ExecStart real (caminho do binário: `type -p omniroute`) e o nome
# da env var de porta na doc antes de `daemon-reload`.
systemctl --user daemon-reload
systemctl --user start omniroute.service
systemctl --user status omniroute.service --no-pager
```

Colar de volta: o `status` (tem que estar `active (running)`).
**Não** rodar `systemctl --user enable` ainda — habilitar no boot é da Fase 7 (`agata.target`).

---

## Aceite

- `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:20128/v1/models` → `200`.
- `systemctl --user is-active omniroute.service` → `active`.
- Nenhuma chave/segredo em `~/.config/omniroute/` (`grep -rIlE '(KEY|TOKEN|SECRET)' ~/.config/omniroute/` → vazio).
- `git status` do repo limpo fora deste arquivo-tarefa.

## Verificação independente

- **Quem:** um fallback afinado ou o Humano.
- **O quê:** que o processo escuta só em `127.0.0.1:20128` (não `0.0.0.0`), e que nenhuma
  chave foi escrita em disco neste passo.
- **Como:** `ss -tlnp | grep 20128` (tem que ser `127.0.0.1`); `grep -rIE '(sk-|AKIA|AIza|ghp_)' ~/.config/omniroute/` → vazio.
- **Resultado:** anotar no LOG.

## Rollback

Não destrutivo:
```fish
systemctl --user stop omniroute.service
systemctl --user disable omniroute.service 2>/dev/null; or true
rm -f $HOME/.config/systemd/user/omniroute.service
systemctl --user daemon-reload
```
Remover o pacote (isolado):
> ⚠️ **Remove o OmniRoute do sistema. Rode sozinho.**
> ```fish
> paru -Rns omniroute      # ou: npm uninstall -g omniroute
> rm -rf $HOME/.config/omniroute
> ```

## Registro

- `STATUS.md`: P1-00 → "Feito"; anotar a via de instalação e a versão.
- `LOG.md`: entrada com a versão, o `status` do serviço, o resultado da verificação
  independente, e o `HEAD` no fim.
