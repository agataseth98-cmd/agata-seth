# Desenho: vault por projeto e modos do instalador

Estado: desenho documental; não altera código nem escolhe valores ainda reservados ao Humano. Base: `propostas/desenho-modo-projeto-20261020.md`, decisões das seções 7–9 e 11.

## Decisões já tomadas

- A instância mãe mantém `MEMÓRIAS.md` como fonte oficial. Cada projeto não mãe tem seu próprio vault Obsidian, nomeado pelo projeto; o vault é a fonte das memórias e `MEMÓRIAS.md` é derivado.
- O escriba grava diretamente na pasta do vault; a API do Obsidian fica para leitura. Cada gravação gera commit no repositório local do vault.
- Todo vault é um repositório Git local; `origin` é opcional. Backup do modo local continua necessário.
- A hidratação escolhe a instância por `AGATA_PROJETO_RAIZ`, sem fallback.

## Opções que o instalador precisa representar

| Modo | Repositório da instância | Remoto | Backup |
|---|---|---|---|
| `local` | Git local, sem `origin` | nenhum | snapshot local |
| `git` | Git com `origin` configurado | obrigatório | remoto e bundle |
| `ambos` | começa Git local e pode receber `origin` depois | opcional até ser configurado | conforme remoto disponível e snapshot local |

O modo pertence à instância, não à máquina. Framework e dados da instância permanecem separados; atualização do framework é seletiva. P-8 continua obrigatório sem remoto; PR e push não são pré-requisitos da assinatura local.

## Sequência proposta para implementação futura

1. Preparar seleção explícita da raiz, diretório de vault próprio e geração do `MEMÓRIAS.md` derivado.
2. Adaptar aprovação/aplicação para modo local sem `origin`, sem remover assinatura P-8.
3. Suportar configuração posterior de `origin` para o modo `ambos`, preservando histórico.
4. Ensaiar os três modos em clones descartáveis e verificar backup e isolamento entre projetos antes de ligar o bootstrap.

## Decisões ainda abertas

Este desenho não escolhe o modo padrão do instalador, o comando/nome da interface, nem opções C1/C2. Também não define como tokens e limpeza de segredos serão provisionados; isso pertence à proposta de código do Escriba.
