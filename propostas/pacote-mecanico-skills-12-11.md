# Pacote mecânico e skills, com a fila de aplicação corrigida (`pacote-mecanico-skills-12-11`)

Proposta P-8 de `pacote-mecanico-skills-12-11`. Diff: `propostas/pacote-mecanico-skills-12-11.diff` (77 arquivos, 27 novos e 12 removidos; 422 KB; sha256 `d14e079f40dd1d516e63ab646b4fc7652f36179a38c49690a2a1035df6233946`). Base: `origin/main` `8c13ed78`. Gerado com `git diff --no-renames` (renomeação escondida não passa pelo P-8: ele precisa ver os dois lados).

Substitui `pacote-mecanico-12-11` e `skills-consolidadas-12-11` (movidas para `propostas/superadas/`, com nota). Nenhuma das duas deve ser aplicada. Executado por Claude Haiku 5.5, agente de proposta, a pedido do coordenador, a partir das decisões do Humano de 12/11/2026 (entradas 519 a 523 do cache do Conselho).

Classe (P4): comportamento e canon. Canon: `AGENTS.md`, `REGRAS.md`, `PROTOCOLOS.md`, `PROMPT_CARREGAMENTO.md`, skills. Comportamento: `.claude/settings.json`, `.claude/agents/*.md`, `scripts/*` (incluindo `scripts/equipe/*`), `redesign/router/*`, `config/cli/*`, `.github/workflows/*`.

## Partes

1. **Pacote mecânico** (`pacote-mecanico-12-11`, 31 arquivos): gancho de turno (`scripts/turno.py`, `UserPromptSubmit`), auditoria de cabeçalho (`auditoria_turno.py`, aviso sem bloqueio), verificador dos mecanismos do Conselho, configs de CLI em `config/cli/*` (exemplos; nada lido pelo sistema), spec com 52 critérios.
2. **Skills consolidadas** (`skills-consolidadas-12-11`): 20 skills viram 10, sem perder texto; o que saiu vai para `extras/arquivo-skills-12-11/`. Composta sobre a parte 1 (ver "Causa", item 3).
3. **Correção do processo** (nova):
   - (a) `scripts/equipe/diff_limpo.py`: recusa `.diff` com hunk que toca o bloco `ANCORA-SHA` de REGRAS, PROJETO, MEMÓRIAS e PROMPT_CARREGAMENTO. Chamado por `scripts/aprovar.sh` (não assina), `scripts/p8_verificar.sh` (check 5, não aplica), `scripts/equipe/aplicar.py` (não começa) e `scripts/p8_verificar_pr.sh` (CI, para `.diff` novo ou alterado no PR).
   - (b) trava de aplicação: `scripts/equipe/trava.py`. Enquanto uma aplicação está em curso, PR de proposta que toca o registro (MEMÓRIAS, ONDE_ESTAMOS, INDICE_MEMORIAS*) falha no CI. Local: `propostas/.aplicando-<nome>`, criado pelo `aplicar.py` com o PID e removido no `finally`; marcador de processo morto é retirado. No CI: PR aberta com head `aplica/*` (lida com `gh pr list`); sem essa lista, a PR não passa (falha fechada). `aplicar.py` também recusa começar se houver marcador vivo ou aplicação aberta.
   - (c) número de MEMÓRIAS no último instante: `scripts/equipe/numero_memorias.py`. Renumera só as entradas novas, sobre `origin/main`, na ordem decrescente do registro. Regra em `propostas/README.md`: antes de juntar, renumerar, commit, push, CI de novo, e só então `gh pr merge --match-head-commit`. `aplicar.py` já recalcula o número em todo refazer (`montar`), e agora usa o mesmo `numero_memorias.proximo`.
   - Workflows: `fiscal-p8.yml` ganha `pull-requests: read` e `GH_TOKEN` (só leitura de PRs; nenhum checkout do head). `sdd.yml` e `ci_sdd_local.sh` rodam os três selftests novos.

## Causa da falha de 10:17

Fatos medidos, na ordem:

1. **O `.diff` assinado não tinha bloco ANCORA-SHA.** `grep -c ANCORA` e `grep "Escrito em"` no `pacote-mecanico-12-11.diff`: zero. Único trecho perto dos canônicos é contexto de texto comum (REGRAS `@@ -78`, PROMPT `@@ -98`), longe do bloco (REGRAS linhas 24-33, PROMPT linhas 41-50).
2. **`git apply --check` passa em todas as bases desde a assinatura.** Saída de `git apply --check -v propostas/pacote-mecanico-12-11.diff` sobre `8c13ed78` (RC 0; lista os 31 arquivos "Verificando patch ..." e nenhum erro). Em `04bfe2e4` (base declarada): RC 0. Em `54eb50dd`, `2ec04181` e `ca273af2`: RC 0.
3. **Os blocos ANCORA-SHA apareceram na aplicação, escritos pelo pre-commit.** O commit `d18f7a4d` (aplicação, base `2ec04181`) muda o SHA, a data e as URLs pinadas do bloco em REGRAS, PROMPT, PROJETO e MEMÓRIAS. `atualizar_ancora_prompt.py` reescreve só essas linhas (simulado em cópia: 28 inserções e 28 remoções, todas no bloco). O `.diff` não traz isso; quem traz é o hook, em todo commit.
4. **A fila de números colidiu.** Duas entradas do registro com `(999)`: a da aplicação (`d18f7a4d`, calculada sobre `2ec04181`) e a da proposta de skills (#979, mesclada às 10:09:51 -03, também calculada sobre `2ec04181`). A PR #980 tinha CI verde às 10:11 (fiscal-p8, suite-adversarial, sdd, CodeQL) e ficou atrás da base com o merge de #979. O agente que a fechou às 10:17 escreveu "blocos ANCORA-SHA dentro do diff"; os fatos 1 a 3 mostram que não era isso.
5. **A skills só aplica depois do pacote.** `git apply --check ../skills-consolidadas-12-11.diff` sozinho sobre `8c13ed78`: RC 1 (agata-dev.md, agata-pesq-processo.md, conselho_mecanismos.py e testar_mecanismos.py não batem). Depois de `git apply pacote-mecanico-12-11.diff`: RC 0. O `index` de cada arquivo na skills bate com o `index` novo do pacote (`d8917ad6`, `7bd2f934`, `c1bbb4e4`, `61dc7aaf`). Ou seja: a proposta de skills foi gerada sobre o pacote, e publicada como se fosse independente.

**Causa real (conclusão):** a aplicação foi montada sobre uma base que andou no meio (#979), e o número de MEMÓRIAS foi escolhido na abertura da branch e não no merge. Não foi o `.diff`, nem os blocos gerados dentro dele. O log exato do `aplicar.py` naquele refazer não ficou no repositório; a PR foi fechada antes de o refazer empurrar qualquer commit (`headRefOid` ficou `d18f7a4d`). **Não reproduzido:** a falha exata do refazer. Simulação completa do commit com hook exigiria assinatura de teste; o primeiro passo do perímetro, sem a assinatura, passa em tudo exceto P-8 (esperado).

## Testes (cópia com histórico, `/…/scratchpad/copia`, base `8c13ed78`)

- `git apply --check` do `.diff` do pacote sobre `8c13ed78`: RC 0. Sobre `04bfe2e4`: RC 0.
- Skills sozinha sobre `8c13ed78`: RC 1. Depois do pacote: RC 0.
- **Commit só de âncoras** (H1, `atualizar_ancora_prompt.py` nos 4 canônicos): `git apply --check` do `.diff` combinado: RC 0.
- **Diff com âncora** (gerado H1 vs `8c13ed78`, REGRAS): depois de mais um commit de âncoras (H2), `git apply --check`: RC 1 ("REGRAS.md:22: patch não se aplica"). `diff_limpo.py` marca o mesmo arquivo: RC 1, com as linhas do bloco listadas (até 20).
- `diff_limpo.py --selftest`: 5 casos OK. Nos dois `.diff` assinados: OK.
- `numero_memorias.py --selftest`: 4 casos OK (sem nova; colisão em (999) vira (1000); duas novas com ordem; sem entradas erra).
- `trava.py --selftest`: 4 regras OK (entrada inválida não bloqueia; proposta de registro bloqueada por `aplica/*`; proposta sem registro passa; aplicação não se bloqueia) e marcador (cria, recusa segunda, solta, retira marcador de processo morto).
- Fiscal de PR (`p8_verificar_pr.sh`) sobre base de teste com os scripts novos:
  - PR com um `.diff` de teste contendo hunk ANCORA: FALHA (check 2b).
  - PR que altera MEMÓRIAS, sem aplicação aberta: OK.
  - Mesma PR com `aplica/pacote-x` aberta: FALHA (trava 3b).
  - Sem `GITHUB_REPOSITORY`: FALHA (falha fechada).
  - Com `gh pr list` que não responde: FALHA (falha fechada).
- `aplicar.py`: `ast.parse` OK. **Não testado de ponta a ponta** (exige `gh` e a chave de assinatura).
- `aprovar.sh`: a recusa (a) está inserida antes da assinatura, mas **não foi executada**: o agente não roda `aprovar.sh` (linha vermelha), e a tentativa de testar na cópia foi bloqueada pelo classificador. Fica para o Humano conferir no terminal, ou para um teste de cópia que não exija assinatura.
- `ci_sdd_local.sh` (`uv run --offline --with pytest bash scripts/ci_sdd_local.sh`), `testar_turno.py`, `testar_mecanismos.py`, `conselho_mecanismos.py --verificar`, `gate_spec_sync.py` (selftest e leitura), lint de skills (`qualidade_llm.py`): resultados no fim deste arquivo (seção "Estado de verificação").

## Decisões pendentes (Humano)

1. **Trava no GitHub** (`gh pr list`). A alternativa é só marcador local, mas o runner do CI não enxerga o arquivo local. A troca nos workflows (`pull-requests: read`, `GH_TOKEN` só leitura) é o custo. Confirmar.
2. **Trava de PR de proposta** bloqueia propostas que tocam MEMÓRIAS enquanto houver aplicação aberta. Atrasa, mas evita o `(999)` duplo. Alternativa: só renumerar, sem bloquear.
3. **Desenho fail-open até o código entrar.** Os checks 2b e 3b só valem depois que `scripts/equipe/*` estiver na base. Por isso esta PR de proposta não é bloqueada pelo que ela mesma traz.
4. **Teste do `aprovar.sh`** (recusa de bloco gerado) no terminal do Humano, antes de assinar, ou aceitar o teste do `diff_limpo.py` como cobertura.
5. **Falha pré-existente do selftest com `python3 -I`** (entrada 512): dono ainda a definir. Não tocada por esta proposta.
6. **`git push --force-with-lease`** no refazer de `aplicar.py`: já existia, na branch da própria aplicação. Não mudado. Decidir se fica.

## Definição de pronto (DoD)

- [x] `.diff` sem hunk de bloco gerado (`diff_limpo.py`: OK) e aplica limpo sobre `8c13ed78` e sobre o commit de âncoras (RC 0).
- [x] Causa do 10:17 medida e registrada (fatos 1 a 5 acima); diagnóstico anterior refutado.
- [x] Selftests novos e fiscal de PR testados nos casos de falha e de passagem.
- [x] `ci_sdd_local.sh` completo verde na cópia (43 passos OK; ver "Estado de verificação").
- [ ] PR de proposta com CI verde e merge com `--match-head-commit` no head verificado.
- [ ] Assinatura do Humano no terminal, depois do merge.
- [ ] Aplicação (PR `aplica/*`) passa pelo `diff_limpo` e pela trava.

## Apetite

Uma proposta, uma assinatura. Não entra nada além destes arquivos: sem nova frente, sem skill nova, sem mudança no `PROJETO.md` (fica para `projeto-indice-12-11`).

## Reversão

- Depois da aplicação: `git revert` do commit de aplicação (o `.diff` tem `git apply -R`). Os arquivos de `extras/arquivo-skills-12-11/` voltam para `.agents/skills/` com o mesmo revert.
- Trava: marcador órfão em `propostas/.aplicando-<nome>` se remove à mão (nenhuma aplicação viva). Fiscal: reverter `fiscal-p8.yml` e `p8_verificar_pr.sh`.
- Nada é apagado: as duas propostas superadas ficam em `propostas/superadas/`, com nota.

## Assinatura (depois do merge deste PR, no terminal do Humano)

```
git -C ~/agata pull --ff-only
bash ~/agata/scripts/aprovar.sh pacote-mecanico-skills-12-11 "pacote mecânico e skills com a fila de aplicação corrigida; substitui as duas superadas"
```

Nenhum agente roda `aprovar.sh`. O `APROVADO-` não existe agora.

## Estado de verificação

Cópia com histórico, árvore candidata staged (`git apply` do `.diff` sobre `8c13ed78`, `git add -A`), `uv run --offline --with pytest bash scripts/ci_sdd_local.sh`: **`CI LOCAL: TUDO OK`**, 43 passos OK, 0 falhas. Esta é a versão 2 do `.diff` (sha256 acima): a versão 1 tinha a mensagem "RENUMERADO (1000) -> (1000)" quando nada mudava; corrigida para "OK: nenhuma entrada nova com número ocupado" antes da assinatura. Passos pedidos e presentes na saída: `testes SDD (pytest)`, `gate de sincronia das specs` (selftest e leitura), `ciclo SDD` (sdd_flow e nova_versao), `skills sem problema de lint`, `pacote mecânico: testes do turno`, `selftest do turno`, `selftest da auditoria do turno`, `testes dos mecanismos do Conselho`, `verificador de mecanismos do Conselho` (`conselho_mecanismos.py --verificar`), e os três selftests novos (`diff_limpo`, `numero_memorias`, `trava`).

Observação do caminho: a primeira rodada falhou em `ferramentas/test_ferramentas.py::test_indice_em_dia` (FileNotFoundError em `.agents/skills/agata-carregar/SKILL.md`). Causa: a cópia tinha o índice do git antigo (aplicação sem `git add`), e `git ls-files` ainda listava as skills removidas. Com `git add -A` a árvore ficou coerente e o teste passou. Não é defeito da proposta, mas é o tipo de coisa que o commit real corrige: a aplicação precisa do commit, não só do `git apply`.

Não rodado: `aplicar.py` de ponta a ponta (exige `gh` e a chave de assinatura); `aprovar.sh` (linha vermelha do agente; ver "Testes").
