# Workflow do fiscal com chave repetida, e gate de YAML dos workflows (`fiscal-yaml-12-11`)

Proposta P-8 de `fiscal-yaml-12-11`. Diff: `propostas/fiscal-yaml-12-11.diff` (6 arquivos; sha256 `620ac726bf241410b0c53013c9247ca4784b6f3fe3000fc3700b549a2cae6df7`). Base: `origin/main` `9981cbb8`. Gerado com `git diff --no-renames`.

Classe: comportamento (`.github/workflows/*`, `scripts/*`, `.githooks/*`). Não é canon. Executado por Claude Haiku 5.5 (Claude Code, subagente), a pedido do orquestrador. Não assinado, não aplicado, PR em draft e não juntado.

Urgência: com o `main` nesse estado, nenhum PR fica mergeável. PR #983 está `BLOCKED`.

## Causa

1. **A chave `env:` está duplicada.** `c4c71956` (aplicação de `pacote-mecanico-skills-12-11`, PR #982) acrescentou um segundo `env:` no passo "Fiscalizar (par assinado, consumo integral, raiz da base)" de `.github/workflows/fiscal-p8.yml`, nas linhas 44 e 47 de `origin/main`. O erro já estava no `.diff` aprovado: o trecho `+ env:` foi inserido abaixo do `env:` existente. Medido com `git show c4c71956 -- .github/workflows/fiscal-p8.yml`.
2. **O PyYAML não reclama.** Lido com `yaml.safe_load`, o `env` do passo vira só `{'GH_TOKEN': ...}`: `BASE_SHA` e `HEAD_SHA` somem sem erro. Ou seja, mesmo num parser que aceitasse o arquivo, o `p8_verificar_pr.sh` receberia `"" ""`.
3. **O GitHub recusa o arquivo.** `gh run list --workflow fiscal-p8.yml` mostra execuções com conclusão `failure` no evento `push` para `main` (18:43:49Z, merge de #982) e na branch `proposta/sincronia-12-11` (18:51:13Z). O nome da execução é o próprio caminho do arquivo, sinal de workflow inválido. A execução `pull_request_target` do PR de aplicação passou antes do merge, quando o `main` ainda tinha a versão anterior.
4. **Por que nada pegou antes.** Lido nos três scripts: `ci_sdd_local.sh`, `.githooks/pre-commit` e `p8_verificar.sh` não validavam sintaxe nem chave repetida de workflow. O P-8 (`p08_quarentena.sh`) cobre `.github/*`, mas só exige assinatura, não confere o conteúdo.

## Correção

- `.github/workflows/fiscal-p8.yml`: um único `env:` no passo, com `BASE_SHA`, `HEAD_SHA` e `GH_TOKEN`. É só a remoção de uma linha (`git apply --numstat`: 0 inserções, 1 remoção). O resto do arquivo fica igual, inclusive `pull-requests: read`.

## Mecanismo para não repetir

- **`scripts/verificar_workflows.py`** (novo, 237 linhas). Falha em: YAML com erro de sintaxe; arquivo vazio; raiz que não é mapeamento; **chave repetida em qualquer mapeamento, em qualquer nível**, com a linha das duas ocorrências. Usa PyYAML, que o repo já usa em `scripts/testar_dados_externos.py`; sem PyYAML, falha fechada. Três modos:
  - `--raiz DIR` (padrão: o repo): confere `DIR/.github/workflows/*.yml|*.yaml`.
  - `--diff ARQ.diff`: confere o que o `.diff` produz sobre `HEAD`, só nos caminhos `.github/workflows/` que ele toca. Sem esses caminhos, passa sem ler o resto.
  - `--selftest`: 11 casos. Positivo: o `fiscal-p8.yml` quebrado, com os dois `env:`. Negativo: a correção. Mais YAML inválido, chave repetida na raiz e dentro de item de lista, mesma chave em mapeamentos diferentes (válido), arquivo vazio, raiz em lista, e os três cabeçalhos de diff.
- **Ligado em quatro pontos:**
  - `scripts/ci_sdd_local.sh`: dois passos novos, o selftest e a varredura de `.github/workflows` do repo. Os dois usam `${PY_YAML:-python3}`. **Ver "Ambiente" abaixo.**
  - `.githooks/pre-commit`: se o commit toca `.github/workflows/*.yml`, confere o conteúdo **staged** (exportado do índice com `git checkout-index` para um diretório temporário). Roda depois do `perimetro.sh` e antes da âncora. Só confere quando um workflow muda no commit.
  - `scripts/p8_verificar.sh`: check 6. Diff que toca workflow é conferido sobre `HEAD` antes de aplicar. Roda depois do check 5 (`diff_limpo`).
  - `scripts/aprovar.sh`: gate (3b), antes de assinar. **Além do pedido**: o pedido citava o `p8_verificar.sh`, mas o motivo declarado é "validado antes de assinar", e só `aprovar.sh` assina. Por isso o gate entra nos dois.
- **Não ligado (lacuna declarada):** `.github/workflows/sdd.yml` e `scripts/p8_verificar_pr.sh` (fiscal de PR no CI remoto) não rodam o verificador. Um PR que quebre o YAML de workflow só é barrado pelo gate local, na máquina do Humano. Fechar isso é outra proposta, e exige a mesma assinatura.

## Como destravar (passos do Humano)

Nenhum passo é feito pelo executor. Ordem:

1. **Ler o `.diff`:** 6 arquivos, descritos acima. `git apply --check` sobre `origin/main`: RC 0.
2. **Destravar a proteção do `main`:** tirar `fiscal-p8` da lista de checks obrigatórios por enquanto, ou permitir o merge sem ele. Sem isso, nem esta PR de proposta nem a PR de aplicação juntam, porque o fiscal que roda para elas é o de `main`, que está quebrado (`pull_request_target` executa a versão do `main`).
3. **Juntar a PR de proposta** (`proposta/fiscal-yaml-12-11`, draft) quando o passo 2 estiver feito. Não juntar antes.
4. **Assinar:** `bash scripts/aprovar.sh fiscal-yaml-12-11 "motivo"`, com a passphrase da chave do Humano. Ao assinar, o gate (3b) roda antes; se ele recusar, o `.diff` não é assinado.
5. **Conferir antes de aplicar:** `bash scripts/p8_verificar.sh fiscal-yaml-12-11`. Deve dar `PODE APLICAR`, com o check 6 em `OK 6`.
6. **Aplicar** em `aplica/fiscal-yaml-12-11`, com o par `.diff`/`APROVADO-` movido para `propostas/aplicadas/` no mesmo commit. A PR de aplicação também roda o fiscal de `main`, ainda quebrado: a proteção continua destravada para ela.
7. **Religar:** depois que o `main` tiver o fiscal corrigido e um PR real tiver rodado `fiscal-p8` em verde, o Humano marca `fiscal-p8` de volta como obrigatório. Ato do Humano, conforme PROJETO.md, "Fiscal de PR e consumo integral".

## Testes (cópia com histórico, base `origin/main` `9981cbb8`)

Cópia: `git worktree` detached em `origin/main`, descartável, sem push.

- **Antes da correção**, `verificar_workflows.py --raiz` sobre `origin/main`: FALHA em `.github/workflows/fiscal-p8.yml`, chave `env` repetida em `jobs.fiscal-p8.steps[2]`, linhas 44 e 47. Mesmo achado do orquestrador.
- **Depois da correção:** OK, 3 workflows (`fiscal-p8`, `perimetro`, `sdd`), YAML válido e sem chave repetida.
- `--selftest`: 11 casos OK.
- `--diff` do `.diff` proposto: OK.
- `--diff` de um diff de controle que muda uma linha do `fiscal-p8.yml` e mantém a duplicata: FALHA, com as linhas 44 e 47.
- `diff_limpo.py` no `.diff` proposto: OK (nenhum hunk toca o bloco `ANCORA-SHA`).
- **Bloco do pre-commit**, extraído e rodado contra o índice: workflow quebrado staged (diferente do `HEAD`) bloqueia com exit 1; workflow corrigido passa com exit 0.
- `bash -n` em `pre-commit`, `p8_verificar.sh`, `aprovar.sh` e `ci_sdd_local.sh`: sintaxe OK.
- `uv run --offline --with pytest bash scripts/ci_sdd_local.sh` na cópia com o `.diff` aplicado, **sem** `PY_YAML`: VERMELHO, 43 OK e 2 FALHA. Os dois são os passos do verificador: `PyYAML ausente`. Causa: sob `uv run`, o `python3` é um venv efêmero sem pacotes do sistema, e o cache offline do uv não tem PyYAML (`--with pyyaml --offline` não resolve). Comportamento correto do fail-closed, mas o comando documentado fica vermelho.
- Mesmo comando com `PY_YAML=/usr/bin/python3` (Python 3.14.9 com PyYAML 6.0.3): **`CI LOCAL: TUDO OK`, 45 OK e 0 FALHA**, incluindo os dois passos de workflow.

## Ambiente (decisão para o Humano)

O verificador precisa de PyYAML no interpretador que o roda. O comando do orquestrador (`uv run --offline --with pytest`) não tem PyYAML. Duas saídas:

- **A (proposta atual):** `PY_YAML=/usr/bin/python3 uv run --offline --with pytest bash scripts/ci_sdd_local.sh`. Mantém o PyYAML, que lê YAML de verdade. Exige o nome do interpretador no comando.
- **B:** trocar PyYAML por um leitor próprio de YAML. Não recomendado: um parser caseiro lê menos YAML que o GitHub e perderia a checagem de sintaxe.

Hoje o padrão é `python3`, então sem `PY_YAML` o passo falha fechado. Isso é de propósito.

**Não medido:**

- Assinatura real e o gate do `p8_verificar.sh` e do `aprovar.sh` de ponta a ponta. Exige a chave do Humano. Não foi gerado nenhum `APROVADO-*`, nem de teste. Os dois pontos foram conferidos pelo comando que chamam.
- O GitHub aceitando o arquivo corrigido. Só se mede depois de juntado, com a proteção destravada.
- O fiscal em PR real, com o `main` corrigido.
- O comportamento do GitHub diante do arquivo quebrado: o diagnóstico "workflow file issue" vem do `gh run list`, não de um parser local.
