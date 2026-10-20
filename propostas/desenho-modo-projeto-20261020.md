# Desenho: modo de projeto (local, git ou ambos) — para o instalador

Estado: **rascunho, sem código**. Não autoriza nada por si (P-8). Base: `propostas/plano-replicabilidade-2026-09-25.md` (seção 0, Fases 2 a 5) e a decisão do Humano de 20/10/2026: o projeto deve ter a opção de uso local, git ou ambos, e tudo deve ficar desenhado para o instalador.

## 1. Os três modos

| Modo | O que tem | Histórico | Remoto | Backup |
|---|---|---|---|---|
| **local** | `PROJETO.md`, `MEMÓRIAS.md`, `memoria/missoes/`, `.env` numa pasta própria | git local sem remoto | nenhum | restic local (P-12) |
| **git** | o mesmo, versionado num remoto do cliente | git com `origin` | `origin` do cliente | o remoto + bundle |
| **ambos** | começa local; o remoto é adicionado depois | git, com ou sem `origin` | opcional | igual ao git |

O modo é propriedade de cada projeto, não da instalação: uma máquina pode ter um projeto local e outro com git.

## 2. Invariantes (valem nos três modos)

1. **Framework separado da instância.** `REGRAS.md`, `scripts/`, `.githooks/`, `redesign/` vêm do framework. `PROJETO.md`, `MEMÓRIAS.md`, `memoria/missoes/`, `.hidrata*.md` e `.env` são da instância. Nada passa de um projeto para outro.
2. **P-8 vale sem remoto.** Mudança de comportamento só entra com `.diff` e `APROVADO-<nome>` assinado. A assinatura é local (`propostas/.allowed_signers`), não depende do GitHub.
3. **Pull request é opcional.** Hoje `scripts/dupla/aplicar.py` e `scripts/aprovar.sh` leem `origin/main` e abrem PR com `gh`. No modo local, a aplicação faz commit direto numa branch local, sem `push` e sem PR. Essa bifurcação é a principal mudança de código do instalador.
4. **Backup independe do modo.** O bundle (`post-commit`) só existe com git. No modo local, o backup é um snapshot restic agendado, com o mesmo controle de idade do P-12.
5. **Nunca herdar história.** A atualização do framework (Fase 5) é seletiva e traz só caminhos de framework.

## 3. O que muda em cada modo

- **local:** `git init` na instância, sem `origin`. `sincronizar-estado.sh` e `aprovar.sh` pulam a checagem de remoto (o `sincronizar-estado.sh` já trata `git remote get-url origin` falhando). Sem PR, sem `ls-remote`.
- **git:** igual ao atual. O instalador pede a URL do remoto e grava em `origin`.
- **ambos:** começa como local. `origin` é adicionado depois com um comando único, e a partir daí os scripts usam o remoto.

## 4. Mecanismo para o instalador (proposta)

Três variáveis por instância, lidas no bootstrap e gravadas em `~/.config/agata/projeto.env`, fora do repositório e sem segredo:

- `AGATA_PROJETO_RAIZ`: pasta da instância.
- `AGATA_PROJETO_MODO`: `local`, `git` ou `ambos`.
- `AGATA_PROJETO_REMOTO`: vazia no modo local.

Credenciais de remoto não entram aqui: ficam no cofre (F3, `systemd-creds`).

## 5. Fora deste desenho (decidido em outro lugar)

- Como a hidratação escolhe o projeto ativo: `AGATA_PROJETO_RAIZ`, sem fallback.
- Identidade (nome, ícone, banco): Fase 2, decisão do Humano pendente.
- Retirada de seções do `PROJETO.md` (`retirada-projeto-2-20261020`, PR 394): só deve ser assinada depois que a hidratação souber ler `extras/projeto-detalhe/` de cada projeto.

## 6. Perguntas para o Humano

1. Modo padrão do instalador: `local` ou `git`? Recomendo `local`, porque funciona sem conta e sem rede.
2. Um projeto pode começar local e depois ganhar remoto (modo "ambos") sem perder histórico? Recomendo sim.
3. No modo local, a assinatura continua obrigatória? Recomendo sim: é a única trava que não depende de remoto.
4. Backup no modo local: restic agendado ou bundle manual? Recomendo restic, que já é o padrão do P-12.

## 7. Ordem para implementar (quando houver instalador)

1. Tornar `aprovar.sh` e `aplicar.py` independentes de `origin`, com caminho de commit direto. Testar num clone sem remoto.
2. Criar as três variáveis e o comando de inicialização (`agata projeto novo --modo ...`).
3. Ensaiar o modo "ambos" (local → remoto) numa VM (Fase 7).
4. Só então integrar ao bootstrap (Fase 3).

## Limites desta análise

- Medido: 21 scripts referenciam `origin` ou `git remote` (`grep`). `aplicar.py` e `aprovar.sh` dependem de `origin/main`. `atualizar_ancora_prompt.py` lê `origin` por `git remote get-url`.
- Não medido: se um clone sem remoto passa pelo `pre-commit` inteiro sem erro. Isso precisa de teste em clone limpo antes do passo 1.

## 8. Decisão do Humano (20/10/2026): memórias de projetos que não são o projeto mãe

- O projeto **mãe** (esta instância, Agata) mantém `MEMÓRIAS.md` como fonte oficial. Nada muda para ele.
- Todo projeto **não mãe** usa o **Obsidian como local oficial** das memórias: o vault dele é a fonte, e `MEMÓRIAS.md` vira um derivado gerado a partir do vault (o caminho inverso do atual).
- Isso resolve a pergunta 1.1 da Fase 4 do plano de replicabilidade para os projetos não mãe. A Fase 4 deixa de ser "decisão pendente" para eles.

Consequências que precisam de desenho antes do código:

1. **Controle P-10** ("vault derivado confere com a fonte em HEAD") hoje assume que o canon é a fonte. Para projeto não mãe, a checagem passa a ser "derivado `MEMÓRIAS.md` confere com o vault".
2. **Escrita:** o `seth_escriba` escreve em `MEMÓRIAS.md`. Em projeto não mãe, a escrita vai para o vault (Obsidian), com o mesmo controle append-only (P-5).
3. **Modo git:** o vault fica versionado no mesmo repositório do projeto. No modo local, o vault vive só na pasta da instância, com backup restic.
4. **Marcador `ENTRADAS-NOVAS:AQUI`:** em projeto não mãe, a numeração das entradas vem do vault, não do arquivo derivado.

Perguntas que continuam abertas para o Humano: (a) o nome do vault é o nome do projeto ou um fixo? (b) o Obsidian precisa estar aberto para a escrita, ou o escriba escreve direto no arquivo do vault?
