# Decreto: refinar os 54 itens genéricos da caixa de ferramentas (03/11/2026)

O tema `negocios-e-nichos` guardava 54 peças que a regra por nome não classificava. Passam a ter tema por nome, numa tabela explícita `AJUSTES` em `ferramentas/ferramentas.py` (nenhuma regra por padrão foi alterada, então nenhuma outra peça muda). Conferido por diff do índice antes e depois: 54 movidas, 0 fora desse grupo, total 413.

Resultado: dois temas novos, `dados-e-ml` (8) e `operacoes-e-dominios` (18: logística, cobrança, saúde, rede, contratos); `frontend-e-design` +5, `planejamento-e-agentes` +12, `banco-e-infra` +4, `revisao-e-git` +3, `contexto-e-custo` +2, `qualidade-de-codigo` +1, `testes` +1. `negocios-e-nichos` fica vazio e some do índice; a regra de captura continua para peças futuras.

Muda `ferramentas/ferramentas.py`, `INDICE.md` e `indice.json`. Os 5 testes da caixa passam.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh ferramentas-refino-20261103 "aprovo: refinar os itens genéricos da caixa"`.
