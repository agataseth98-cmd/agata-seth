# Proposta nova-versao-spec-v2-unificada-09-11 — spec v2 unificada (união dos PRs #923 e #941)

**Nome para assinatura:** `nova-versao-spec-v2-unificada-09-11`
**Base:** `origin/main` (089a0d76).
**Arquivos que o diff altera:** `redesign/nova_versao/spec/spec.md`, `redesign/nova_versao/spec/acceptance.json`, `redesign/nova_versao/tests/test_nova_versao.py`. Nenhum código de produção.

**Diff:** `propostas/nova-versao-spec-v2-unificada-09-11.diff`
**sha256 do diff:** `e4fed3c98c8edb8c671b96321dd1e7dafbaeff025d0dec730ca9d3c1bc93db18`

**Substitui:** PR #923 (`proposta/nova-versao-spec-v2-20261106-diff`) e PR #941 (`proposta/nova-versao-spec-v2-refeita-07-11`). Os dois serão fechados com comentário apontando para este PR, depois do merge. Os branches de origem não são apagados.

## Decisão

Decisão do Humano, 09/11/2026: juntar #923 e #941 numa proposta só, sem perder nada de nenhuma.

## Conferência (medida em 09/11/2026)

- Varredura automática: cada linha acrescentada por #923 e #941 em `spec.md`, `acceptance.json` e no arquivo de testes foi procurada literalmente na união. Ausentes: só as duas checkboxes do #923 (viraram bullets com o mesmo texto, conflito 2) e o texto do critério de orçamento do #941 (trocado pelo do #923, conflito 1).
- `git apply --check` e `git apply` do diff contra `origin/main` (089a0d76), em worktree git temporária: passou.
- `scripts/ci_sdd_local.sh` na worktree temporária, com o diff aplicado: `CI LOCAL: TUDO OK`, 33 passos OK, pytest 9.2.0 (venv de scratch). Inclui testes SDD, ciclo SDD da nova versão, âncora dos componentes e critérios e drift de `nova_versao`.
- `pytest redesign/nova_versao/tests`: 41 passed (inclui o teste novo).
- Mutação: `max_chamadas` 200 para 201 numa cópia. O teste novo falha com `(201, 2000000, 120, 0.0) != (200, 2000000, 120, 0.0)`. Restaurado, passa.
- Critérios: 12 entradas em `acceptance.json` e 12 checkboxes `- [ ]` em `spec.md`, com o mesmo texto. O drift por critério passa.
- `git diff --check`: sem erro de espaço.
- Cópia sem `.git` (`git archive`) falha em um teste: `redesign/confiabilidade/tests/test_gates.py::test_todos_pass`, gate `rastreabilidade`. Causa: o gate chama `git rev-parse HEAD` (`redesign/mvp_autoaprimoramento/mvp.py`, `head_git`). Não tem relação com o conteúdo. Com `.git`, passa.
- Efeito do CI local, fora deste commit: `redesign/nova_versao/spec/evidence.json` e `criterion-drift.md` (rastreados) são regravados, e `redesign/sdd_flow/spec/evidence.json` e `criterion-drift.md` aparecem. Nada disso entra no commit.
- Valores citados na spec (justificativa do orçamento): `memoria/missoes/conselho-remoto/20261106-142748-glm-4.7-flash.json` existe na checkout principal (pasta fora do git) e traz `tokens_total` 11292 e `duracao_s` 19.6.

## Origem, item por item

### Do #923 (`spec.md` e registro `propostas/nova-versao-spec-v2-20261106.{diff,md}`)

| # | Parte do #923 | Onde está na união | Estado |
|---|---|---|---|
| A1 | Contrato, C7: sai "cofre de chaves"; entra "painel de chaves (ver Painel de chaves)" | `spec.md`, linha C7 | igual |
| A2 | Estados separados: execução só com os estados que uma jornada consome; saúde e saída do turno no lote 5 | `spec.md`, "Estados separados" | igual |
| A3 | Concorrência: trava única (`flock` com timeout); fila de GPU; `eventos.py` como camada fina; intenção, ação, confirmação com `nv.py sincronizar`; índice no mesmo sistema de arquivos; sombra conta o pulo; timeout de busca definido no lote 5 | `spec.md`, "Concorrência e falha" | igual |
| A4 | Orçamento: quatro categorias (`local`, `gratuito`, `assinatura`, `pago`); valores 200 chamadas, 2 milhões de tokens, 120 s, R$ 0; justificativa medida; escopos turno, tarefa e global; `orcamento_turno.py` sai | `spec.md`, "Orçamento" | igual |
| A5 | Critério "o orçamento padrão tem 200 chamadas, 2 milhões de tokens, 120 s e R$ 0, e `orcamento.py` usa as mesmas quatro categorias da spec" | checkbox em `spec.md` e entrada em `acceptance.json` | texto do #923, teste do #941 (conflito 1) |
| A6 | Critério "o painel de chaves grava a chave sem devolvê-la, e o valor não aparece em resposta HTTP, log ou ledger" | `spec.md`, bloco "Sem teste ainda" | texto igual; fora de checkbox (conflito 2) |
| A7 | Critério "a reversão não apaga `AGATA_NV_DIR`; só remove o cache" | `spec.md`, bloco "Sem teste ainda" | texto igual; fora de checkbox (conflito 2) |
| A8 | Lote 5: orçamento do turno vira escopo `turno` em `orcamento.py`, sem módulo separado | `spec.md`, "Lote 5 (05/11/2026)" | igual |
| A9 | Seção "Painel de chaves (lote 2, decisão do Humano, 06/11)": escrita atômica em 0600; só a rotina de gravação lê o arquivo; resposta sem o valor; ledger só com o nome; modelos, pedidos e sombra não leem; exceção à regra do `.env` pede aprovação na assinatura | `spec.md`, nova seção | igual |
| A10 | Seção "Lotes seguintes (decisão do Humano, 06/11)": metacognição, corpo, skills da Alexandria e `conselho.py` vão para o lote 6, com critério antes do código | `spec.md`, nova seção | igual |
| A11 | Migração e reversão: `AGATA_NV_DIR` é arquivado num pacote datado, nunca apagado sozinho; só o cache sai | `spec.md`, "Migração e reversão" | igual |
| A12 | Código: lote explícito em cada item; painel e lote 6 sem crase até existir | `spec.md`, "Código" | igual |
| A13 | Registro do #923, decisões 1 a 4 de 06/11 (orçamento, cofre para painel, reversão, escopo) | A4, A6, A7, A9, A10, A11 | igual |
| A14 | Registro do #923, correções do mesh (5 itens: trava única, `eventos.py` fino, ordem intenção-ação, `orcamento_turno` como escopo, lote explícito em Código) e os três critérios novos | A3, A8, A12; os três critérios: A5 (com teste), A6 e A7 (sem teste) | igual |
| A15 | Registro do #923, "O que não foi decidido" (3 itens) | "Pendências para a assinatura", abaixo | igual |
| A16 | Registro do #923, "Evidência" ("diff aplica limpo"; "só spec.md muda") | "Conferência", acima | superada: agora também mudam `acceptance.json` e o teste (conflito 6) |
| A17 | Arquivos `propostas/nova-versao-spec-v2-20261106.diff` (+105 linhas) e `.md` (+29 linhas) | não entram como arquivo; conteúdo em A1 a A16 | originais ficam no branch do #923 |
| A18 | Linhas de âncora de SHA (`.hidrata.md`, `MEMÓRIAS.md`, `PROJETO.md`, `PROMPT_CARREGAMENTO.md`, `REGRAS.md`) | não são conteúdo; o pre-commit regrava no commit | — |

### Do #941 (`propostas/nova-versao-spec-v2-refeita-07-11.{diff,md}` e corpo do PR)

| # | Parte do #941 | Onde está na união | Estado |
|---|---|---|---|
| B1 | `acceptance.json`: +1 entrada (9 linhas), comando `pytest` do teste novo | `acceptance.json`, depois de "o orçamento padrão é só local e pago sem teto não gasta" | comando igual; texto do critério do #923 (conflito 1) |
| B2 | `test_nova_versao.py`: `OrcamentoTests::test_valores_de_fabrica_e_quatro_categorias_da_spec` (+7 linhas) | `test_nova_versao.py` | igual, linha por linha |
| B3 | `spec.md`: +1 checkbox do critério de orçamento, logo após o critério de orçamento padrão | `spec.md` | texto do #923 (conflito 1); posição do #941 (conflito 3) |
| B4 | Valores de fábrica conferidos no código (`PADRAO`, `PROVEDORES`) | coberto pelo teste B2 | igual |
| B5 | "Fora desta proposta": critérios de painel de chaves e de reversão "sem teste, não entram aqui" | agora entram como texto em "Sem teste ainda" (A6, A7) | superada por decisão desta união |
| B6 | "Fora desta proposta": demais mudanças da spec v2 "não entram aqui" | agora entram (A1 a A13) | superada por decisão desta união |
| B7 | "Fora desta proposta": `evidence.json` e `criterion-drift.md` não regenerados | não entram no commit | igual |
| B8 | Evidência: `git apply --check`, apply em checkout limpo, `git diff --check` | "Conferência", acima | refeita |
| B9 | Evidência: `unittest` com 41 OK | `pytest` com 41 passed | refeita com pytest |
| B10 | Evidência: mutação de `max_chamadas` falha o teste | "Conferência", acima | refeita |
| B11 | Evidência: `anchor.py` com ANCHOR OK e `spec_gate.py check` com SPEC GATES OK | CI local: âncora e ciclo OK | refeita |
| B12 | Evidência: 12 checkboxes e 12 critérios, mesmo texto e ordem | "Conferência", acima | refeita (12 e 12) |
| B13 | "Não medido": pytest não instalado; drift por critério sem evidência | pytest 9.2.0 em venv de scratch; ciclo, âncora e drift rodaram | medido agora |
| B14 | Corpo do PR #941: âncoras de SHA regravadas pelo hook; sha256 do diff antigo | hook normal; sha256 novo acima | atualizado |

## Conflitos e como foram resolvidos

1. **Texto do critério de orçamento.** #923: "...e `orcamento.py` usa as mesmas quatro categorias da spec". #941: "...e as quatro categorias da spec". Ficou o do #923, ligado ao teste do #941 (`test_valores_de_fabrica_e_quatro_categorias_da_spec`, que confere `PROVEDORES` com as quatro categorias). Checkbox e `acceptance.json` usam o mesmo texto, como exige o drift.
2. **Dois critérios do #923 sem teste.** `criterion_drift.py` acusa "critério sem evidência" para todo `- [ ]` que não tenha entrada em `acceptance.json` com comando que passe. Como checkbox, o CI ficaria vermelho. Por isso o texto ficou preservado, sem `- [ ]`, no bloco "Sem teste ainda". Quando ganharem comando, viram checkbox com entrada em `acceptance.json`. Escrever o teste agora ficaria fora desta união.
3. **Posição do critério de orçamento.** O #941 pôs logo depois de "o orçamento padrão é só local…"; o #923 pôs no fim. Ficou a do #941, na mesma ordem em `spec.md` e em `acceptance.json`.
4. **Registros dos PRs.** Os `.diff` e `.md` do #923 e do #941 não entram como arquivos, para não duplicar o mesmo assunto em `propostas/`. O conteúdo está aqui, e os originais continuam nos branches de origem.
5. **Âncoras de SHA.** Não são conteúdo. O pre-commit regrava as cinco linhas.
6. **Escopo do diff.** O #923 dizia "só `spec.md` muda". A união muda também `acceptance.json` e o arquivo de testes, por causa do #941.
7. **Commit.** O commit desta proposta traz só os arquivos de proposta (`.diff` e este `.md`) mais as âncoras que o hook regrava. Os arquivos de spec e teste ficam dentro do `.diff`, não aplicados no branch, como em #944.

## Pendências para a assinatura

1. **Exceção à regra do `.env`.** A rotina do painel de chaves lê `~/.config/agata/.env` só para trocar a linha do provedor. A regra "nenhuma peça lê `.env`" não prevê isso. O Humano confirma na assinatura (texto em "Painel de chaves").
2. **Forma dos dois critérios sem teste** (A6 e A7): seguem como texto até ter comando, ou o Humano pede o teste no lote 2.
3. **Tabela de transições das sete palavras:** continua sem definição (operador e implementador apontaram). Não entra nesta proposta; fica para o lote 2.
4. **Critérios do lote 6** (metacognição, corpo, skills, `conselho.py`): sem critério ainda, como diz o texto.

## Checklist de fechamento

- [x] #923: A1 a A18 presentes na união, ou com status explicado (A16 superada, A17 e A18 fora do conteúdo).
- [x] #941: B1 a B14 presentes na união, ou superados por decisão desta união (B5 e B6), ou refeitos com medição nova (B8 a B13).
- [x] Conflitos 1 a 7 resolvidos e registrados acima.
- [x] Pendências 1 a 4 registradas para o Humano.

## Assinatura

Depois do merge, o Humano assina com `bash scripts/aprovar.sh nova-versao-spec-v2-unificada-09-11`. A assinatura fica amarrada ao sha256 acima. O executor não assina e não aplica.
