---
name: agata-aplicar-proposta
description: Aplicar uma proposta P-8 que o Humano assinou ("feito", "assinei", "aprovei", bash scripts/aprovar.sh <nome>). Verifica assinatura, aplica, move o par, registra em MEMÓRIAS e ONDE_ESTAMOS, comita num branch e abre PR. Também serve pra CRIAR uma proposta nova.
---

# Proposta P-8: criar, verificar, aplicar

Por quê: REGRAS, PROJETO, `scripts/`, `.githooks/`, `config/`, `redesign/` e `.agents/` mudam
comportamento — só entram com `.diff` assinado pela chave do Humano (PROJETO, "Quarentena estrutural").
Você **nunca** roda `scripts/aprovar.sh` (a chave é do Humano) e **nunca** usa `write`/`edit` em canon.

## Criar uma proposta
1. Branch: `git checkout -b proposta/<nome>` a partir de `main` atualizado (`git pull --ff-only`).
2. Faça a mudança nos arquivos, gere o diff e **desfaça** a mudança na árvore:
   `git diff <arquivos> > propostas/<nome>.diff && git checkout <arquivos>`
   (arquivo novo: `git add -N <arq>` antes do `git diff`, depois `git rm --cached` e apague a cópia).
3. `git apply --check propostas/<nome>.diff` — tem de passar.
4. Teste o efeito numa cópia descartável (`git worktree add --detach <dir> HEAD`), nunca só lendo.
5. Entrada nova em MEMÓRIAS (ver "Registrar") + ONDE_ESTAMOS; commit; push; PR. O merge é do Humano.
6. Diga ao Humano o comando exato, **sem ponto no fim**: `bash scripts/aprovar.sh <nome>`

## Aplicar (depois de "feito")
1. `gh pr view <n> --json state` → MERGED; `git checkout main && git pull --ff-only`.
2. `bash scripts/p8_verificar.sh <nome>` — tem de terminar em `PODE APLICAR`. Qualquer FALHA: pare e
   mostre a saída ao Humano. Não "conserte" assinatura nem hash.
3. `git checkout -b aplica/<nome>`; `git apply propostas/<nome>.diff`;
   `git mv propostas/<nome>.diff propostas/aplicadas/`; `mv propostas/APROVADO-<nome> propostas/aplicadas/`.
4. Se a mudança vale fora do repo (unit em `~/.config/systemd/user`, compose em `~/librechat`, config do
   Goose): backup do runtime, copie, `cmp` runtime × repo, recarregue, e **prove pelo caminho real**.
5. Registre (abaixo), `git add` só os arquivos certos, commit, push, PR.

## Registrar em MEMÓRIAS
- Entrada nova **logo abaixo** de `<!-- ENTRADAS-NOVAS:AQUI -->`, número = topo + 1, data do commit.
  Formato: `(<n>) DIÁRIO — dd/mm/aaaa · **<conclusão em 1-2 frases>**`, corpo curto, e fecho
  `Modelo: <nome> (<cliente>, na Máquina) · vetor: <o que foi medido> · Autorização: Humano — "<citação>"`.
- Pelo MCP `canon` → `memoria_acrescentar` (append-only, o escriba numera); ou, no shell, com um script
  python que insere após o marcador — **nunca** `write`/`edit` no arquivo (já apagou a história, (516)).
- `ONDE_ESTAMOS.md`: bloco novo no topo da data, português simples, sem jargão, no mesmo commit.

## Armadilhas já pagas
- **P-8 confere uma proposta por vez contra HEAD.** Duas propostas no mesmo arquivo = dois commits (539).
- `git stash` sem `--index` perde o que estava staged; o guarda de âncora do pre-commit bloqueia commit
  com REGRAS/PROJETO/MEMÓRIAS sujos fora do index — guarde com `git stash push --keep-index -u` e devolva
  com `git stash pop` depois do commit.
- O hook pode rodar a suíte de controles (P-16, 1-2 min): não mate o commit por timeout.
- Um controle que barra o commit (P-4, P-8, P-10) está certo até prova em contrário: leia o SUSPEITO.
