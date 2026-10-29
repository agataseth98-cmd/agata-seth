# Proposta: Fase F1 do Conselho, hidratação de todo envio (29/10/2026)

Todo envio do Conselho (direto, debate, cadeia e síntese) passa a começar pelo `CONTEXT`: manifesto v4, regras de resposta e catálogo de ferramentas. Assim o modelo sabe onde está e pede informação pela tag, em vez de supor.

Mudança em `redesign/painel_operacional/conselho_rede.py` (função `com_contexto`, `_payload` e os três pontos de envio) e teste novo em `test_conselho_rede.py`.

Validado: 15 testes unitários passam, incluindo o novo `test_every_send_carries_system_context_f1`.

Não testado ao vivo: o aceite real (um modelo citar o manifesto sem o prompt pedir) depende de uma rodada aprovada.

Aplicação: depois da assinatura (`bash scripts/aprovar.sh conselho-hidratacao-f1-20261029`).
