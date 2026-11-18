# Agentes permanentes e skills que só recomendam o comprovado (`agentes-skills-18-11`)

Classe: Comportamento (`redesign/router/`, `.claude/agents/`; sem canon).

Proposta P-8 de `agentes-skills-18-11`. Diff: `propostas/agentes-skills-18-11.diff` (13 arquivos: 10 definições em `.claude/agents/`, `redesign/router/skills_ledger.py`, `redesign/router/test_skills_ledger.py` e duas linhas em `redesign/router/spec/spec.md`). Base: `origin/main` (5b1761e0). O diff não traz registro; a entrada (1044) de MEMÓRIAS.md vai no mesmo PR.

Origem: decisão do Humano em 17/11/2026, e aprovação em 18/11/2026, 09:32.

Pedido original (17/11): "nenhum agente criado a partir de agora deve ser descartável, e todos devem ficar disponíveis para o sistema seguindo em seu micro universo as regras do sistema e aprendendo durante suas tarefas, o mesmo vale para as skills devem apontar apenas soluções para erros de suas naturezas que 51%".

Aprovação (18/11, 09:32): "ok para os 4", sobre as quatro recomendações em `~/agata-arquivo/roteador-capacidade-17-11/l8-agentes-skills/decision.md`. O Humano não recordou o sentido de "51%"; o limiar que vale é o do ponto 1:

1. Limiar: a skill recomenda solução só com taxa de acerto acima de 51% e pelo menos 10 usos conferidos. Abaixo disso, a solução aparece como "não comprovada" e não some.
2. Escopo: os 10 agentes de `.claude/agents/` e todos os criados daqui para frente.
3. Quem grava: o agente anota o desfecho ao terminar a tarefa; o coordenador confere. Sem conferência, não conta.
4. Memória: o aprendizado de cada agente fica guardado à parte e não se apaga com o reinício de 15 dias do cache do Conselho.

## O que muda

1. **Memória por agente.** As 10 definições em `.claude/agents/` ganham a seção "Memória e desfecho (L8, 18/11/2026)". A memória de cada agente fica em `~/.local/share/agata/agentes/<agente>/memoria.jsonl`, pelo `AGATA_CACHE_CONSELHO` do `cache_conselho.py`. Esse caminho fica fora de `~/.local/share/agata/cache-conselho/`, a pasta que reinicia em 15 dias.
2. **Ledger de desfechos.** `redesign/router/skills_ledger.py` com `registrar`, `conferir` e `recalcular`. O arquivo é `~/.local/share/agata/skills-ledger/<skill>.jsonl` (pasta 0700, arquivo 0600), fora do repositório. É só de acréscimo, com trava `flock`, e guarda só slugs, ids e marcas de tempo (sem texto livre, por isso não passa pelo sanitizador). Desfecho nasce pendente e só conta depois de conferido. Linha inválida: `registrar`, `conferir` e `recalcular` recusam (código 2) e não gravam sobre o ledger ruim.
3. **Agentes só de leitura.** Seis agentes não gravam nada: `agata-revisor`, `agata-inov-critico`, `agata-inov-pesquisa`, `agata-pesq-painel`, `agata-pesq-processo` e `agata-pesq-rea`. O coordenador registra e confere em nome deles (`--por coordenador`).
4. **Testes.** `redesign/router/test_skills_ledger.py`, 13 testes: memória fora da pasta do cache, reinício simulado do cache, caminho por variável, segredo recusado, definições dos 10 agentes, limiar de 51% e n >= 10, solução "não comprovada" continua na tabela, linha inválida recusada, e concorrência (8 processos, 40 registros, nenhuma linha perdida).

## O que não muda

- As skills (`.agents/skills/*/SKILL.md`) não mudam. Nenhuma skill ainda consulta o ledger para deixar de recomendar solução não comprovada. Isso é a lacuna L1, para proposta futura.
- O caminho do gateway e do roteador não muda.

## Medido (18/11/2026)

- `pytest redesign/router` na worktree de lote (base 5a88cb18, com o diff aplicado): 77 passed, 33 subtests passed (medido nesta rodada).
- Cópia limpa (`git archive origin/main` em pasta temporária, depois `git apply` do diff): aplica; `pytest redesign/router`: 77 passed, 33 subtests passed; `python3 scripts/testar_sincronia.py`: 25 testes, OK (medido nesta rodada).
- `pytest redesign/router/test_skills_ledger.py --collect-only`: 13 testes (medido nesta rodada).
- `git apply --check` do diff em `origin/main` (5b1761e0): APLICA (medido nesta rodada).
- agata-revisor (Claude Sonnet 5.5): "conforme 13, desvio 0", veredito aprovar. Relatado pelo coordenador; não reexecutado nesta rodada.

## Não medido

- Uso real: nenhuma tarefa real gravou desfecho ainda. Taxa e n reais não existem.
- Revisão do Codex: não feita, sem cota até 14:18 (relatado pelo coordenador).
- Slug sem sanitizador (BAIXO): o ledger aceita só slugs (`[a-z0-9][a-z0-9._-]{0,63}`), validados por regex, sem passar pelo sanitizador. Risco baixo, porque não há texto livre; fora do escopo desta proposta.

## Desvio registrado

O agente executor (agata-dev) usou `rm -rf` numa HOME temporária própria durante os testes; a regra do projeto proíbe `rm`. Relato do executor: a remoção foi só nessa HOME temporária, não no repositório nem em `~/.local/share/agata`.

## Reversão

`git apply -R propostas/agentes-skills-18-11.diff` (ou reverter o commit de aplicação). Os dados em `~/.local/share/agata/` não são tocados pela reversão; para guardá-los ou descartá-los, mover com `mv`.

## Comando de assinatura

Depois do merge deste PR, no terminal, sem `!`:

bash scripts/aprovar.sh agentes-skills-18-11

## Modelos

Claude Opus 5.5 orquestrou; agata-inov-arquiteto e agata-dev (Claude Haiku 5.5) desenharam e implementaram; agata-revisor (Claude Sonnet 5.5) revisou.
