# Proposta voz-conta-turno-19-11 — fala transcrita conta como turno do Humano

Falha achada pelo Humano em 19/11/2026 18:58 (voz): falas do canal de voz chegavam ao modelo como notificação e o contador `scripts/turno.py` não avançava (~20 falas não contadas). Conselho n=588.

**O quê:** `redesign/sentidos/canal_voz.py` ganha `contar_turno()`: cada fala transcrita efetivamente entregue ao modelo roda `turno.py proximo --sessao <AGATA_CANAL_VOZ_SESSAO>` uma vez e a linha de cabeçalho acompanha a fala. Fala vazia, eco da própria voz, sem palavra de vez ou pedido de efeito não contam. `turno.py` ausente ou falhando só avisa. Sem a variável de sessão, desligado.

**Medido:** 79 testes de redesign/sentidos (8 novos) rodados pelo Opus; CI local TUDO OK (agente).

**Não medido:** canal real com sessão e turno.py reais; o lançador ainda não exporta `AGATA_CANAL_VOZ_SESSAO` (próximo passo, junto com o agata-run).

**Reversão:** `git revert`, ou não definir a variável.

**Modelo:** Codex designado (sem cota até 24/11); implementação Sonnet 5.5; revisão Opus 5.5.
