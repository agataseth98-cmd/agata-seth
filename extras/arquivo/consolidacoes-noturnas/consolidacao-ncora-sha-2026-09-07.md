# Proposta de consolidacao — âncora sha

_Gerada por redesign/grafo/flows/consolidacao.py em 2026-09-07. NAO e' canon. O Humano decide (P-8). Se aprovada, vira ENTRADA NOVA em MEMORIAS (append-only), nunca edicao._

**Refs:** (72), (96), (97), (113), (115), (149), (166), (168), (211), (212), (213), (217), (223), (226), (253)

(1) A âncora sha256 evoluiu de uma referência estática para uma auto-referência dinâmica no prompt de carregamento para garantir sincronização e integridade.

(2) Adiciona a definição correta de âncora como "offset e marcadores de conteúdo" em (96) e a prova de verificabilidade por máquina em (113); corrige o uso da referência a (212) como guia de sincronização e integra a nova âncora automática em (226); cita a necessidade de verificação de íntegridade em (166).

(3) O título (72) torna-se insuficiente ao surgir a necessidade de sincronização real definida por commits em (113) e automação em (226).
