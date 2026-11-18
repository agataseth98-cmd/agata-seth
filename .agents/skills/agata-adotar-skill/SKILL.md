---
name: agata-adotar-skill
description: Adotar no sistema uma skill de terceiros que resolveu problema real. Use quando o ledger mostrar uma skill de terceiro (terceiro:NOME) como "candidata a adoção" (acima de 51% e pelo menos 10 usos conferidos), ou quando o Humano pedir para aprender uma skill de fora. A skill é reescrita para o Agata, não copiada; sem licença compatível, não se adota.
---

# Adotar uma skill de terceiros (decisão do Humano, 18/11/2026)

Skill de fora pode ser aprendida quando resolveu problema real, reescrita para o sistema. Cópia fixa continua sendo cópia: não vira skill do Agata.

## Quando vira candidata

Registre cada uso da skill de terceiros no ledger, com `--skill terceiro:<nome>` (vale se existir a pasta `.claude/skills/<nome>/` com o `SKILL.md`). O coordenador confere os desfechos. Depois:

```bash
python3 redesign/router/skills_ledger.py recalcular --skill terceiro:<nome>
```

Status `candidata a adoção` quer dizer: taxa de acerto acima de 51% e pelo menos 10 usos conferidos. Qualquer outro status: não adote; mantenha o uso e registre mais.

## Passos

1. Licença primeiro. Leia a licença da fonte (arquivo de licença ao lado da skill, como `.claude/skills/LICENSE-obsidian-skills`, ou o repositório de origem). Sem licença, ou licença que não permita obra derivada com atribuição, pare: não adote e diga o motivo.
2. Releia a skill original e a tabela do ledger. Fique só com os trechos ligados às soluções que deram acerto; o resto não entra.
3. Escreva a skill nova em `.agents/skills/<nome>/SKILL.md`, em português comum, com a voz do sistema (resultado, evidência, próximo passo; frases curtas; sem saudação). Frontmatter só com `name` e `description`; até 500 linhas.
4. Inclua a seção "Recomendação comprovada (L8)", igual à das outras skills do Agata, apontando para o ledger da skill nova.
5. Cite a origem (nome, endereço, versão ou data lida) e a licença no fim do arquivo. Não copie texto longo literal; reescreva.
6. Rode `python3 redesign/painel_operacional/qualidade_llm.py` e corrija os problemas de lint e os caminhos citados.
7. Entra por proposta P-8, com o par `.diff` e `APROVADO-<nome>` (skill `agata-aplicar-proposta`). Quem escreve não assina.

## Recomendação comprovada (L8)

Antes de recomendar uma solução para um erro desta skill, confira o desfecho registrado:

```bash
python3 redesign/router/skills_ledger.py recalcular --skill agata-adotar-skill
```

Procure a linha do erro e da solução na tabela (colunas: skill, erro, solução, usos, acertos, taxa, status). Recomende a solução como comprovada só com status `comprovada`: acertos acima de 51% e pelo menos 10 usos conferidos. Com status `não comprovada`, sem linha ou com código de saída 2, apresente a solução como "não comprovada", com os usos e a taxa quando houver, e não a descarte. Só conta o desfecho que o coordenador conferiu.
