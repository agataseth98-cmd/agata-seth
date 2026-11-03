# Brainstorm

## Usuários

O Humano (assina e decide), os modelos que operam no Agata (propõem e executam) e a CI (confere sem confiar em ninguém).

## Estado que muda

Arquivos do componente `redesign/sdd_flow/`, o `state.json` de cada ciclo e os artefatos `evidence.json` e `criterion-drift.md`. Nada em canon, nada em `scripts/*`.

## Erros e concorrência

Um portão que falha para o ciclo no ponto exato e não grava `complete`. Dois ciclos no mesmo `state.json` não são suportados: um arquivo de estado por ciclo.

## Migração

O desenvolvimento do Agata já existia. O ciclo entra por ancoragem: cada componente existente ganha uma spec que lista o código que possui; componente sem spec continua fora do escopo até ser ancorado, sem bloquear o resto.

## Observabilidade

`status` mostra o histórico de etapas; `evidence.json` guarda comando, retorno e saída de cada critério; `criterion-drift.md` lista cada critério como pass, fail ou unmeasured.

## Reversão

Reverter o commit de aplicação. O componente não toca em estado fora da própria pasta.

## Sucesso

Um ciclo roda ponta a ponta sobre o próprio `sdd_flow` na CI, e todo critério tem evidência executada.
