# Proposta de consolidacao — âncora sha

_Gerada por redesign/grafo/flows/consolidacao.py em 2026-09-18. NAO e' canon. O Humano decide (P-8). Se aprovada, vira ENTRADA NOVA em MEMORIAS (append-only), nunca edicao. Passou no portao mecanico de (371)._

**Refs:** (96), (97), (149), (166), (168), (211), (213), (217), (223), (226), (253), (281), (302), (378), (458)

O estado consolidado define a âncora SHA como integridade automática, integral ao repo e prompts, substituindo contagem de linha por offsets de conteúdo e verificando hashes completos.
(96) introduz offset/marcadores; (97) corrige (96) sobre offset vs foto e risco de vazamento.
(149) executa emendas Kimi com autocorreção sha256; (166) verifica GGUF Caminho 3.
(168) explica divergência como latência; (211) e (213) documentam tentativas de Conselho Remoto com HTTP 429.
(217) insere SHA no prompt para detectar versão velha; (226) automatiza geração da âncora.
(253) aplica melhorias de URL pinada em SHA; (281) fixa template da âncora honesta.
(302) substitui detector falso positivo por checagem de defasagem v2; (378) carimba SHA em preâmbulos, resolvendo B5.
(458) revela que git add inteiro atualiza a âncora. (96) torna-se obsoleto após correção de (97), mas mantido por histórico.
