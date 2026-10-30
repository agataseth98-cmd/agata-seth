---
name: agata-ferramentas
description: Abre a caixa de ferramentas do Agata por tema (skills e agentes do ECC, do superpowers e as próprias). Use quando a tarefa pedir uma prática específica (testes, segurança, revisão, banco, frontend, planejamento) e você não souber qual skill existe.
---

# Caixa de ferramentas do Agata

1. Leia só `ferramentas/INDICE.md` (11 temas, poucas linhas).
2. Escolha o tema da tarefa: `python3 -I ferramentas/ferramentas.py tema <tema>`.
3. Leia só as peças necessárias: `python3 -I ferramentas/ferramentas.py ver <nome>`.

Regras (o Humano decide; você propõe):
- Tema `quarentena`: só leitura. Aprendizado automático, memória paralela e laços autônomos não carregam nem rodam sem decisão do Humano.
- Hooks do ECC ficam em `ferramentas/fontes/ecc/hooks-inativos/`: desligados. Ligar um hook é mudança de comportamento e exige Decreto assinado.
- Nada em `ferramentas/fontes/` é executado a partir daqui; são cópias presas a commit (`COMMIT`) com a licença original (`LICENSE`, MIT).
- Se uma peça da caixa repetir uma skill `agata-*`, vale a do Agata.
- Para atualizar uma fonte: novo commit em `COMMIT`, `reindexar`, Decreto.
