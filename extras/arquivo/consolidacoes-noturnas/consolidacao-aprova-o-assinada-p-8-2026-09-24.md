# Proposta de consolidacao — aprovação assinada P-8

_Gerada por redesign/grafo/flows/consolidacao.py em 2026-09-24. NAO e' canon. O Humano decide (P-8). Se aprovada, vira ENTRADA NOVA em MEMORIAS (append-only), nunca edicao. Passou no portao mecanico de (371)._

**Refs:** (223), (224), (284), (301), (318), (351), (359), (364), (365), (366), (367), (368), (375), (378), (379)

Estado consolidado: Aprovação P-8 exige assinatura SSH humana, validação de quarentena e cobertura de arquivos específicos, substituindo criação manual direta.
(223) limita ACB; (224) define perímetro commit/P-7/P-8; (284) move par para aplicadas/; (301) regenera índice derivado post-commit.
(318) fecha buraco redesign/router com autoaprovação; (351) cobre lacunas em grafo/*.py e *.yml; (359) atualiza fila de aderência PROJETO.md.
(364) registra criação manual sem mintar; (365) permite script bash para aprovação; (366) introduz chave SSH pública em .allowed_signers.
(367) coloca raiz de confiança em quarentena P-8; (368) sanitiza scripts/* e lotes noturna nunca aprovado; (375) valida assinatura contra allowed_signers.
(378) define APORVADO-ancora-sha-canon; (379) adiciona fallbacks com chaves Huggingface.
Obsolescência: (364) evolui para (365/366), mas persiste registro manual; (284)/(301) complementam fluxo, sem obsolescência clara entre si.
Títulos truncados mantidos conforme original.
