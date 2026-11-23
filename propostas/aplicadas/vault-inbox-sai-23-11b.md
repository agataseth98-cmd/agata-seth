# Proposta vault-inbox-sai-23-11b — retirar o inbox do Obsidian (nunca usado)

Ordem do Humano, 23/11 12:11: "remova".

**O que era:** nota parada 10 min em `memoria/obsidian-inbox/` virava entrada de MEMÓRIAS pelo escriba (vault-inbox-fase4-2026-09-25).

**Medido em 23/11:** o timer nunca foi instalado em `~/.config/systemd/user` (só o .service), a pasta `memoria/obsidian-inbox/` não existe, nenhuma execução no journal; o P-9 avisava a cada perímetro.

**O que muda:**
- `config/agata-vault-inbox.{service,timer}` e `scripts/vault_importar_inbox.py` vão para `extras/arquivo-vault-inbox-23-11/` (com README de como voltar).
- Sai a linha de `config/servicos-agata.txt` (some o aviso do P-9).
- Painel: o timer sai do `TIMER_ALLOWLIST`, do cartão "Manutenção programada" e dos nomes no JS; o teste de timer ausente passa a usar `agata-manutencao.timer` (o caso continua coberto).
- `scripts/seth_autodev.py`: o timer sai da lista de unidades.

**Depois de aplicar (runtime):** mover `~/.config/systemd/user/agata-vault-inbox.service` para `~/agata-arquivo/`, `systemctl --user daemon-reload`, restart do painel.

**Fica:** a menção histórica na tabela da spec da nova_versao (editar exigiria refazer o drift; texto, sem efeito).

**Medido:** `bash scripts/ci_sdd_local.sh` → CI LOCAL: TUDO OK; `git apply --check` em cópia limpa → OK.

**Reversão:** `git apply -R propostas/aplicadas/vault-inbox-sai-23-11b.diff`.

Assinatura: bash scripts/aprovar.sh vault-inbox-sai-23-11b

**Por que "b":** a primeira versão (vault-inbox-sai-23-11, assinada às 12:31) gerou o diff com detecção de renomeação; o P-8 só aceita apagar arquivo de comportamento quando o diff mostra a deleção explícita (`--no-renames`, armadilha medida em 09/09/2026). O commit de aplicação foi barrado pelo pre-commit, nada entrou. Erro meu. Conteúdo idêntico; só o formato do diff muda.
