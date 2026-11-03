# Spec — Evidence Ledger

## Jornadas críticas

Registrar evidência em cadeia de hashes e detectar adulteração.

## Contrato

- `ledger.py` acrescenta eventos encadeados por hash, com trava de escrita (`flock`).
- Adulteração e linha final truncada são detectadas e preservadas, nunca consertadas em silêncio.
- A exportação pública não carrega dado privado.

## Critérios de aceite

- [ ] acrescentar, verificar e exportar publicamente
- [ ] adulteração é detectada
- [ ] escritas concorrentes preservam a cadeia
- [ ] linha final truncada é explícita e preservada

## Desenho e alternativas

Componente existente, ancorado sem reescrever: a spec descreve o que o código já promete e os testes já provam.

## Implementação e testes

Testes em `tests/`; cada critério abaixo aponta o teste que o prova em `acceptance.json`.

## Migração e reversão

Sem migração de dados. Reversão por revert do commit que ancorou o componente.

## Riscos e dependências

A spec descreve o contrato observado em 03/11/2026; comportamento sem teste não está coberto pela âncora.

## Código

- `ledger.py`
- `tests/`
