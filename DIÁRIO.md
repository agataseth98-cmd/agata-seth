# DIÁRIO.md — Ágata

História do projeto. **Só se acrescenta, no fim. Nunca edite nem apague** o que já está aqui.
Cada entrada: `data · quem · o que foi decidido/feito`.

## Resumo consolidado (até 04/06/2026)

O que aprendemos e vale para sempre:

1. Memória tem que ser **uma só**. Vários módulos de memória corrompem tudo.
2. **Nunca finja lembrar** (nada de stub). Se corromper, restaure de verdade.
3. Captura de fatos por **regex vem antes** do modelo — rápida e confiável.
4. Separe **REGRAS** (universais) de **PROJETO** (deste projeto). É o que permite reusar em outros projetos.
5. O Humano manda, mas há **linhas vermelhas**: continuidade, história e honestidade não se suspendem.
6. Documento para modelo tem que ser **imperativo, em 2ª pessoa, com blocos de código bem fechados** — senão o modelo lê as regras como "exemplo de saída" e as ignora (foi a causa de modelos não assumirem o comportamento).
7. O DIÁRIO tem que ter **um cabeçalho e uma linha do tempo**. Dois documentos colados confundem o modelo sobre qual é o certo.

**Marcos:** núcleo de memória unificado · extrator imediato · orquestração por papel (deepseek→condução, qwen→auditoria, kimi→validação) · voz local (Kokoro / voz `pf_dora`) · virada para arquitetura MCP (Ágata como servidor central) + OpenClaw + Hermes.

**Histórico detalhado antigo:** arquivado em `MEMORY.md` — não apagar.

---

## Registros

### 2026-06-05 · Orusoua + Claude (Opus 4.8, arquitetura/auditoria)

Redesenho do sistema para ficar mais simples e barato em tokens, mantendo tudo que prometia.

- Renomeado: CORE→**REGRAS**, MANIFESTO→**PROJETO**, MEMORY→**DIÁRIO**. IB→**Humano**, IC→**Modelo**, IL→**Máquina**.
- **15 regras viraram 6.** Cabeçalho cerimonial, quadrantes, protocolo 1-7 e códigos N1-N6 removidos; formato de resposta enxuto. Um comando de carga (`carregar`) no lugar de três.
- **Motivo:** uma carga real com Qwen3.8 falhou — confundiu Máquina com "Inteligência Legada", declarou íntegro com o DIÁRIO defeituoso, não soube explicar a regra de carga segura, e inventou um bloco marcando-o canônico sem ordem. Diagnóstico: o sistema era pesado demais para o modelo que deveria rodá-lo.

**Pendente de decisão do Humano:**
1. Adotar estas versões (REGRAS/PROJETO/DIÁRIO)?
2. Renomear os `.json` de memória para os nomes novos (fatos/conversas/habitos/contexto)?

### 2026-06-05 (2) · Orusoua decidiu · Claude executou

Humano aprovou: `1s2s3n`.

1. **Adotado.** REGRAS/PROJETO/DIÁRIO passam a canônicos. Trio antigo (CORE_FULL, MANIFESTO_ÁGATA, MEMORY) **arquivado, não apagado**.
2. **Nomes novos de memória adotados:** semantic→fatos, episodic→conversas, procedural→habitos, overlay_ontologico→contexto.
3. **Mantidos 3 arquivos** (sem colapsar).

Feito: arquivos .md novos entregues; script `migrar_agata.sh` (backup + cópia com nomes novos, sem apagar nada).

`lacuna:` o código que lê os .json antigos (memory_core.py etc.) ainda aponta para os nomes velhos. Aplicar os nomes novos no servidor MCP em construção **antes** de remover os antigos — senão quebra.

### 2026-07-01 · Orusoua decidiu · Claude auditou

Auditoria do PLANO_AGATA_v1.2 (GLM → Qwen → GLM). Direção e faseamento **aprovados**; implementação como estava **reprovada**.

Achados críticos: Whisper não roda no Ollama (Fase 4 quebraria); MCP/LiteLLM em `0.0.0.0` + permissões por regex de string burláveis (risco de execução remota); VRAM 8GB não comporta 7B + Whisper-large juntos; failover do Syncthing gera split-brain (dois DIÁRIOs); `.git` sincronizado corrompe o repo. Descoberta central: "Hermes" e "OpenClaw" no v1.2 eram scripts caseiros, **não** as ferramentas reais.

**Decisão do Humano (`1-real · 2-sim · 3-s`):**
1. Construir **sobre o Hermes Agent real**, não bespoke.
2. Gerar **PLANO v1.3 corrigido** (só documento, sem código).
3. **Claude Code inventaria a Predator** antes de tudo.

Pendente: rodar o inventário → revisar v1.3 → Fase 0.

### 2026-07-01 (2) · Fase 0 executada (Claude Code na Predator)

- OpenClaw parado + desabilitado (não apagado). Protótipo antigo arquivado em `~/agata/_arquivo_agata_il/` (`semantic.json` preservado byte a byte).
- **Hermes Agent 0.17.0** instalado (Python 3.11 isolado via uv, sem alertas de segurança), `--skip-browser`. Script inspecionado antes do install (limpo).
- Cérebro local: **llama3.1:8b** (128k nativo), via Ollama, `num_ctx 65536`. Motivo: Hermes exige contexto ≥64k; `qwen2.5:7b` (32k) não serve. No 4060 8GB há offload parcial pra CPU (mais lento; tuning de KV cache fica pra depois).
- Config em `~/.hermes/config.yaml` (provider custom, base_url `localhost:11434/v1`).

Pendente: reportar chave útil do OpenClaw (migrar vs purgar); iniciar Fase 1.
