# Proposta placar-qualidade-19-11 — o placar passa a medir a qualidade do conteúdo

Frente 3 das três escolhidas com o Humano por voz (19/11 23:25): "o placar com a qualidade do conteúdo, antes de deixar ele escolher quem trabalha".

**O quê:** `redesign/rotas/placar.py` ganha um sinal de conteúdo por modelo (o pior de três): bloqueios do gateway (`--bloqueios`, export do journal ou jsonl), vereditos manuais, experimentos de escrita. Nota final = 0,5 mecânica + 0,5 conteúdo; sem sinal = "conteúdo não medido" e teto 0,9; conteúdo < 0,5 = "ruim", sempre atrás em `melhores`. Schema 2; placar antigo lê como "não medido".

**Medido:** 23 testes de redesign/rotas (Opus); CI local TUDO OK (agente). Real: lfm3 passa de 1.00 a 0.90 "conteúdo não medido".

**Limite:** o gateway não grava bloqueios em arquivo (só journal); exportar para `~/.local/share/agata/placar/bloqueios.jsonl` é o próximo passo. Limiares (5 bloqueios, 0,5, 0,9) são ajustáveis.

**Reversão:** git revert. **Modelo:** Sonnet 5.5 (código), Opus 5.5 (revisão).
