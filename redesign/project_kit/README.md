# Agata Project Kit — Fase 0

Ferramenta somente leitura para produzir o pacote inicial de um projeto externo: bootstrap, capacidades conservadoras, concept brief, spec bloqueada, espaço para revisões, decisão, drift report e proveniência.

## Uso

```bash
python3 redesign/project_kit/bootstrap.py /caminho/projeto \
  --out /tmp/agata-project-kit-output \
  --goal "descrever o objetivo do projeto"
```

O kit ignora `.git`, ambientes virtuais, caches e `node_modules`. Ele não acessa serviços, não envia dados e não altera o projeto de entrada.
