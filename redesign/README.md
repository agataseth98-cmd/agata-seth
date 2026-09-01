# redesign/ — redesenho do sistema local Agata

Workspace de desenvolvimento. **NÃO é canon.** Vive no branch `redesign`.
O canon (`REGRAS.md`, `PROJETO.md`, `MEMÓRIAS.md` em `main`) só reflete estas
mudanças na **Fase 8**, pela Cadeia de auditoria em camadas.

## Estado de exceção — leia antes de agir

Autorização do Humano (Orusoua), 01/09/2026, por escrito na sessão de trabalho:
*"estamos em fase de desenvolvimento e eu assumo o risco"*, e *"falso positivo, prossiga"*.

**Os gates de governança do Agata estão SUSPENSOS no branch `redesign`:**
- Quarentena P-8 (pares `propostas/<nome>.diff` + `APROVADO-<nome>`) para arquivos deste branch.
- Cadeia de auditoria em camadas (A→B→C) como gate bloqueante por commit.
- Regra 8 (três passadas independentes no modelo local) como pré-requisito de cada mudança.
- Portão das três perguntas como trava formal por passo.

Isso é decisão do Humano, com risco assumido por escrito. Não é licença para agir
sem cuidado — é remoção da cerimônia, não das proteções abaixo.

**Continua valendo, sem exceção:**
- `MEMÓRIAS.md` nunca se reescreve nem se apaga (Regra 4). Correção é entrada nova.
- Nada de `git push --force` em `main`. Nada de `git reset --hard` / rebase em `main`.
- Segredo (chave, token, `.env`, connection string) nunca é impresso, colado em chat,
  nem commitado. Os ~16 padrões de `scripts/varredura_segredo.sh` continuam a régua.
- Comando destrutivo (`rm -rf`, `dd`, `mkfs`, operação de partição, `git reset --hard`,
  `git clean -fdx`) é mostrado **sozinho**, com aviso em negrito, nunca embutido noutro bloco.
- `main` só muda na **Fase 8**, pelo processo normal. Todo o resto é no branch `redesign`.
- Hermes, Ollama e o `.hermes.md` de produção não são tocados até a Fase 8 (rodam em paralelo).

## Arquivos

| Arquivo | O que é |
|---|---|
| `README.md` | este arquivo — estado de exceção e invariantes |
| `CONTINUIDADE.md` | briefing para o executor fallback (Codex / Qwen Coder) que assume se o primário cair |
| `ROADMAP.md` | as 9 fases (0–8): objetivo, entrega, critério de aceite |
| `PESQUISA.md` | estado da arte por ferramenta + as correções que a pesquisa forçou no plano |
| `STATUS.md` | onde estamos agora, fase atual, quadro de posse de tarefa |
| `LOG.md` | histórico append-only do redesenho |
| `tasks/` | arquivos-tarefa no schema fixo (Objetivo / Pré-requisitos / Arquivos / Passos / Aceite / Rollback / Registro) |
