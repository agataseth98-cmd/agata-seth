# Proposta canal-voz-18-11 — canal de voz local com a Seth, e o gateway aprende a não gravar um pedido

Ordens do Humano em 18/11/2026: 19:19 "crie um canal de alta qualidade para abrir o microfone gravando e vc identificar a minha voz e responder como já sabemos"; 19:23 "ok para todas" (ECAPA na fase 2; atalho ou botão com VAD; só o vetor da voz; outra voz só metadado; voz só conversa, ação confirmada na tela); 19:51 "espere dois segundos e responda"; 19:54 "crie ciclo de conversa"; 19/11 08:21 opção "A" (o gateway aceita "não grave este pedido").

**Canal (`redesign/sentidos/`: `canal_voz.py`, `captura.py`, `vad.py`, `locutor.py`, testes):**
- Captura sob demanda com `pw-record --raw` (sem `--raw` o stdout vem em Sun AU big-endian e vira chiado; medido em 18/11: RMS 19 mil contra 644 real), nada de áudio em disco.
- VAD por energia com piso calibrado nos 300 ms iniciais; fecha após 2 s de silêncio.
- Palavra de vez "Agata" e ciclo de conversa: depois do chamado, segue sem repetir até 30 s de silêncio ou "encerrar"; histórico curto só em memória.
- Transcrição local (`ouvido.py`), resposta da Seth pelo gateway, fala pela voz do sistema; meia-duplex.
- Lock por `flock`; sinais interrompem captura, HTTP e fala; diretório temporário próprio limpo em `finally`.
- Filtro de pedidos com efeito: aviso de interface (o canal não executa nada); a ação se confirma na tela.
- Fase 1: sem verificação de locutor (`locutor.py` devolve "nao_verificado"); ECAPA fica para a fase 2.

**Gateway (`redesign/router/seth_gateway.py`):** `X-Agata-Nao-Registrar: 1`, só de loopback, faz o registro de pedidos não gravar pergunta nem resposta e devolve `X-Agata-Registro: nao`. O canal sempre envia e encerra a sessão se a confirmação não vier, em qualquer resposta, inclusive erro. Atributo por pedido; GET e HEAD zeram (teste de keep-alive na mesma conexão).

**Medido:** 259 testes (router + sentidos) e depois 71 em sentidos; selftests do gateway e do canal OK; CI local TUDO OK. Uso real pelo Humano em 18/11 (protótipo equivalente): transcrição 0,55 s; do fim da fala à voz cerca de 9,7 s.

**Revisão Codex:** r1 reprovou (4 altas), r2 (3), r3 (2), r4 aprovou o gateway e apontou 1 ponto no canal, corrigido com teste.

**Depois de aplicar:** reiniciar `seth-gateway.service`.

**Reversão:** `git revert` do commit de aplicação.

**Modelo:** Sonnet 5.5 (implementação) orquestrado pelo Opus 5.5; revisão Codex (GPT-6).
