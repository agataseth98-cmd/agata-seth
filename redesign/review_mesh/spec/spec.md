# Spec — Review Mesh

## Jornadas críticas

Preparar pacotes isolados para revisores e consolidar os relatórios sem decidir.

## Contrato

- `mesh.py prepare <spec> <pasta>` cria um pacote por papel e recusa sobrescrever.
- `mesh.py consolidate` marca relatório ausente como não medido.

## Critérios de aceite

- [ ] prepare isola os papéis e consolida relatório ausente como não medido
- [ ] prepare recusa sobrescrever e respeita o contrato do pacote

## Desenho e alternativas

Componente existente, ancorado sem reescrever: a spec descreve o que o código já promete e os testes já provam.

## Implementação e testes

Testes em `tests/`; cada critério abaixo aponta o teste que o prova em `acceptance.json`.

## Migração e reversão

Sem migração de dados. Reversão por revert do commit que ancorou o componente.

## Riscos e dependências

A spec descreve o contrato observado em 03/11/2026; comportamento sem teste não está coberto pela âncora.

## Código

- `mesh.py`
- `tests/`
- `README.md`
