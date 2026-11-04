# Mapa falha → mecanismo do Agata

Autor: Claude Sonnet 5.5 (Claude Code). Data: 03/11/2026, 15:55 (medido com `date`). Rascunho para revisão do Humano; nada aqui é canônico.

Base: a revisão de fontes em `pesquisa-llm-agata.md` (mesma pasta) e a leitura do repositório em `main` (HEAD `1fc323e8` ao iniciar o levantamento; o `main` remoto seguiu à frente depois).

**Como ler.** "Existe" = li o arquivo ou rodei a medição. "Não encontrado nesta busca" = busca por texto em `redesign/`, `scripts/` e `config/`, excluindo testes, bibliotecas de terceiros, `propostas/` e a memória derivada; prova só isso, nunca que não existe. Não rodei nenhum dos mecanismos abaixo, exceto o que está marcado como medido.

## Resumo

Das 11 falhas levantadas, 3 têm cobertura forte (alucinação de estado, atualidade do sistema, segurança do MCP), 6 têm cobertura parcial com lacuna medível e 2 não têm mecanismo encontrado (esforço de raciocínio por tarefa, exemplos que viram regra). O Agata já tem o motor mais caro de construir: avaliação com resposta calculada na hora, pontuação sem modelo e comparação antes/depois (`seth_golden.py`, `seth_autodev.py`). A maior parte do que falta é alimentar esse motor com mais casos e novas medições, não construir outro.

## Mapa

| # | Falha (fonte) | O que existe | Lacuna |
|---|---|---|---|
| 1 | Alucinação: o modelo escolhe o provável (vídeo; Kalai et al. 2025) | Regra 2 (não minta, meça). `FALHAS.md`: 8 entradas de fabricação (FAB), 3 de citação (CIT), 1 de medição recusada (MED). `auditoria_turno.py` (1.537 linhas): ferramenta alegada sem chamada, estado desatualizado, citação inventada, afirmação já desmentida. P-7 e P-19 (citação; P-19 só avisa). Expurgo de citação inventada. `seth_golden.py`: 7 casos de ouro, 1 com `aceita_abstencao` | Abstenção existe em 1 de 7 casos e sem penalidade graduada (a regra do paper: erro confiante custa t/(1−t)). Sem abstenção calibrada por concordância entre amostras |
| 2 | Custo de tokens; saída mais cara que entrada (vídeo; docs de preços) | Regra 7 e o mecanismo em `PROTOCOLOS.md`. Hidratação medida: `.hidrata.md` 66.545 bytes. `medir_hidratacao.py`. P-24 avisa: `MEMÓRIAS.md` com 130.216 caracteres contra orçamento de 25.000, escalada para FALHA ainda não implementada | Uso de cache de prompt ou prefixo estável: não encontrado nesta busca. Custo por turno e por modelo: não encontrado |
| 3 | Esforço de raciocínio alto em tarefa simples (vídeo; docs de effort) | Só `reasoning_effort="none"` fixo em `memoria_semanal.py` e a nota em `seth_gateway.py:886` (sem raciocínio, o modelo parou de chamar a ferramenta e inventou) | Não há tabela de esforço por tipo de tarefa. Para o Opus 5.5 o padrão é medium e o raciocínio adaptativo fica sempre ligado (docs) |
| 4 | Corte de conhecimento e atualidade (vídeo; FreshLLMs) | `FALHAS.md` SIN (4 entradas). `estado_para_eco.sh` mede HEAD, hora e sincronia. Cabeçalho com hora medida. Pesquisa na web liberada pelas diretrizes | Sem gatilho automático "pergunta sensível ao tempo → buscar fonte e citar" |
| 5 | Context rot e janela efetiva menor que a declarada (Chroma; RULER; Lost in the Middle) | Orçamento de hidratação, memória em camadas (quente, morno, frio), mapa do PROJETO na hidratação (124 mil → 88 mil caracteres, segundo `ONDE_ESTAMOS`), `MEMÓRIAS` selada em chunks frios | Nenhum teste de comprimento efetivo nos modelos locais (por exemplo `qwen3.5-9b-64k`). P-24 só avisa |
| 6 | Exemplo vira regra (vídeo; Min et al. 2022) | Nada sobre few-shot encontrado nesta busca. As ocorrências de "exemplos" são do treino do Laya | Não verificado nos prompts de `config/`; baixa prioridade |
| 7 | RAG com busca errada, resposta com cara de certa (vídeo; Contextual Retrieval) | `busca_semantica.py` (e5-small local), grep e índice primeiro, vault. A decisão (115)/(293) mantém vetor como camada secundária. O spike RLM mediu embedding pior que grep puro (3/13 contra 9/14) | Sem métrica de recuperação (1 − recall@k) encontrada nesta busca. `seth_golden` mede a resposta, não a recuperação. Sem reranking nem contexto por trecho |
| 8 | Multiagente gasta 4x a 15x (Anthropic, 2025) | Conselho de 9 conselheiros via navegador. `seth_autodev` com teto de chamadas por rodada e aborto após 3 erros de infraestrutura. Regra 8 (verificação tripla) usa multi-modelo de propósito | Sem medição de tokens por agente ou por rodada do Conselho encontrada |
| 9 | MCP é execução de código; envenenamento de ferramenta (spec; Invariant Labs) | Servidores MCP próprios e locais (`canon-mcp.mjs`, escriba, navegador). Autodev restrito a 4 ferramentas de leitura. Capability de uso único ligada à chamada exata aprovada, com teste. `librechat.yaml` permite só 127.0.0.1 e 172.29.7.1 (SSRF). Escriba exige token por projeto e recusa segredo. P-4 e egress | Fixação por hash das descrições de ferramenta: não encontrada. O risco hoje é baixo porque os servidores são locais e próprios; sobe se entrar servidor de terceiros |
| 10 | Skills: custo, curadoria, limites (Anthropic; SkillsBench) | 18 skills com `SKILL.md`, mais `INDICE.md`. Medido: nomes de 8 a 24 caracteres (limite 64); descrições de 138 a 467 caracteres nas 17 de uma linha (limite 1.024); só `design-taste-frontend` tem descrição em bloco e fica com 542 linhas (recomendação: abaixo de 500); `obsidian-bases` tem 499. `skills-lock.json` fixa 1 skill por hash | Sem protocolo A/B de skills. O motor de A/B existe em `seth_autodev`. `BACKLOG-skills.md` é lista antiga de candidatas, sem decisão |
| 11 | O Agata saber como uma LLM funciona (pedido do Humano) | Conhecimento espalhado em `PROJETO.md`, notas e decisões | Não há referência única, carregada sob demanda |

## Prioridade proposta (ordem por evidência e custo)

1. **Skill `llm-como-funciona` mais a pesquisa em `extras/`** (falha 11). Custo baixo, sem risco, carregada sob demanda para não pesar a hidratação.
2. **Ampliar o conjunto de ouro com pontuação de abstenção graduada** (falha 1). Reaproveita `seth_golden` e `seth_autodev`; precisa de casos novos, mantidos reservados.
3. **Medir antes de mudar:** comprimento efetivo dos modelos locais (5), 1 − recall@k da busca atual (7), taxa de acerto de cache e custo por modelo (2 e 8). Cada medição é leitura e vira indicador no painel.
4. **Tabela de esforço por tarefa** (3), depois de medir qualidade contra custo com o próprio autodev.
5. **Protocolo A/B de skills** (10), com `design-taste-frontend` partido em módulos focados se a medição mostrar ganho.
6. **Aba no painel** (diretriz "tudo no painel") para ver e rodar as medições acima.

Itens 4 e 5 só entram depois de haver medição que os justifique. O item 6 mexe em `server.py`, `prototipo.html` e `abrir.js`; o Codex foi avisado na nota 278 do Conselho e não respondeu até agora.

## Limites

- Busca por texto, não leitura integral: o que está como "não encontrado" pode existir sob outro nome.
- Não li `config/capivara/capacidades.json` por inteiro; ele guarda protocolos de ensaio de modelos e pode cobrir parte das falhas 3 e 5.
- Não conferi o conteúdo dos 7 casos de ouro, só a contagem.
- Os números de bytes e linhas foram medidos em 03/11/2026; o resto vem do texto dos arquivos.
