# Spec — Project Kit

## Jornadas críticas

Gerar o pacote inicial de um projeto externo e medir o drift depois.

## Contrato

- `bootstrap.py <projeto> --out <pasta> --goal <texto>` grava pacote com proveniência, sem escrever no projeto.
- Omite nomes de segredo e links simbólicos externos; ignora `.venv`.
- `--drift-against` compara hashes de arquivos entre dois pacotes.

## Critérios de aceite

- [ ] bootstrap ignora venv e grava o contrato
- [ ] drift detecta arquivo adicionado, removido e alterado
- [ ] bootstrap omite nomes de segredo e link simbólico externo

## Desenho e alternativas

Componente existente, ancorado sem reescrever: a spec descreve o que o código já promete e os testes já provam.

## Implementação e testes

Testes em `tests/`; cada critério abaixo aponta o teste que o prova em `acceptance.json`.

## Migração e reversão

Sem migração de dados. Reversão por revert do commit que ancorou o componente.

## Riscos e dependências

A spec descreve o contrato observado em 03/11/2026; comportamento sem teste não está coberto pela âncora.

## Código

- `bootstrap.py`
- `tests/`
- `README.md`
