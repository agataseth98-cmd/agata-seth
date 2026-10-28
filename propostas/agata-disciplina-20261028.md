# Proposta P-8 — skill agata-disciplina

## Objetivo

Juntar, numa skill carregada antes de agir, as regras que já existem no canon e que falharam nesta sessão de 28/10/2026: cabeçalho em toda resposta com hora medida, modo conciso, aviso antes de ação externa, consulta antes de mexer em trabalho de outro, checagem de dependências antes de reiniciar serviço, e leitura declarada com linhas.

## O que muda

- Arquivo novo: `.agents/skills/agata-disciplina/SKILL.md` (ver `agata-disciplina-20261028.diff`).
- Nenhum arquivo existente é alterado. Nenhuma regra nova é criada: a skill aponta REGRAS.md, AGENTS.md e PROTOCOLOS.md.

## Evidência

- `git apply --check` contra `main` em `3b432968`: passa (medido em 28/10/2026, 20:07 -03).
- Frontmatter YAML válido: `name` e `description` lidos com `yaml.safe_load` (medido).
- `auditoria_turno.py --verificar` sobre o SKILL.md: nada a apontar (medido).

## Limites (não medidos)

- A skill **não é obrigatória por si**. Ela só entra no contexto se o modelo a carregar. Obrigatoriedade mecânica exige um controle P-n separado, que ainda não existe e será proposto à parte.
- Não testei se um modelo novo, lendo só esta skill, cumpre o cabeçalho com hora medida. Isso precisa de teste em sessão real.
- O texto cita falhas reais de 28/10/2026, que estão descritas no relatório da sessão, não em MEMÓRIAS.

## Riscos

- Duplicação: se REGRAS mudar e esta skill não, a skill fica desatualizada. Mitigação: a skill aponta o canon, não copia texto dele.
- Pasta `.agents/` muda comportamento de modelos que a leem. Por isso a proposta exige aprovação P-8.

## Reversão

Remover o arquivo `.agents/skills/agata-disciplina/SKILL.md` num commit próprio. Nenhuma outra parte depende dele.

## Aprovação

Esta proposta não está aprovada. O par `APROVADO-agata-disciplina-20261028` só pode ser criado pelo Humano, com `scripts/aprovar.sh`. O executor não o cria.
