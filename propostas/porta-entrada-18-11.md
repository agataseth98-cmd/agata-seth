# Proposta porta-entrada-18-11 — porta de entrada de modelos e adoção de skills de terceiros

Decisões do Humano em 18/11/2026: "esses testes devem servir para incluir modelos novos" (local, pago ou gratuito na nuvem) e "podemos aprender com skills de terceiros [...] as reescrevendo para fazer parte do sistema".

**O quê**
- `scripts/porta_entrada.py comparar --resumo NOVO --base PASTA`: compara o resumo do `benchmark_roteamento` de um modelo com os já medidos, tipo a tipo (código, ferramenta, json, conversa, contexto). Veredito: `util` (ganho estrito em algum tipo contra rival comparável), `dominado`, `inutil` (erro > 50% ou p50 > 120 s) ou `neutro`. Desconta resposta vazia e Python que não passa `ast.parse` (não executa). Avisa "escreveu sem portão" e "raciocínio vazado"; aviso não é veredito. Nuvem compara sem `contexto` (privados não saem da Máquina). Entrada inválida → saída 2.
- `skills_ledger.py`: aceita `--skill terceiro:NOME` (exige `.claude/skills/NOME/SKILL.md`), grava em `terceiros/NOME.jsonl`, sem colidir com skill local; terceiro comprovado (>51%, ≥10 usos conferidos) aparece como `candidata a adoção`.
- Skill `agata-adotar-skill`: licença primeiro; reescrever só o que deu acerto; origem citada; entra por P-8. Índices de skills e ferramentas atualizados.
- Passo novo no CI local: `testar_porta_entrada.py`.

**Medido:** 142 testes (redesign/router + porta_entrada); CI local TUDO OK. Revisão Codex (GPT-6): r1 reprovou (5 achados), r2 reprovou (3 novos), r3 aprovou. Tabela real dos 6 modelos Ollama de 18/11 em `~/agata-arquivo/roteador-capacidade-17-11/`.

**Limite:** a nota é mecânica (forma, vazio, sintaxe); não julga se a resposta está certa. Liberar modelo para rota continua decisão do Humano.

**Reversão:** `git revert` do commit de aplicação.

**Modelo:** Sonnet 5.5 (implementação) orquestrado pelo Opus 5.5; revisão Codex.
