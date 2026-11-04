# Pesquisa SDD e LLM e teste de português (03 e 04/11/2026)

Autor: Claude Sonnet 5.5 (Claude Code). Notas de estudo, **não canônicas**; o canon é `REGRAS.md`, `PROTOCOLOS.md`, `FALHAS.md`, `PROJETO.md` e `MEMÓRIAS.md`. Movido da Área de trabalho do Humano para o repositório em 04/11/2026.

## Onde está o que vale
- Teste de português: `scripts/teste_portugues.py` (o protótipo antigo não veio para cá).
- Perfil de capacidades por modelo: `config/capacidades_modelos.json`.
- Propostas assinadas: `propostas/aplicadas/`; diário: `MEMÓRIAS.md`, entradas (933) a (938).

## Conteúdo
- `pesquisa/`: falhas de LLM e SDD (`pesquisa-llm-agata.md`, `mapa-falha-mecanismo-agata.md`), dossiê do Lumi (`lumi-ceia-ufg.md`), adaptação da saída de áudio, erros encontrados e **`oportunidades-em-aberto.md`** (seções 10 e 11: dúvidas em aberto de 04/11).
- `teste-portugues/`: `RESULTADO.md` (relatório, com a rodada completa e a correção) e os resultados em JSON (1ª rodada, v2 e completa, 360 execuções).

## Em aberto (detalhe em `teste-portugues/RESULTADO.md`)
Causa da piora do 9b no harness completo · T5 do `qwen3:4b` · T4 do Lumi · perfil circular · T6, T7, T9 não discriminam · qualidade de português não medida · efeito isolado da retentativa · temperatura 0 contra 0,3 · termos da licença do Lumi não lidos (risco assumido pelo Humano) · o roteador ainda não lê o perfil.

## Não incluído de propósito
O texto extraído do artigo arXiv de referência do SDD (cópia de terceiros, repositório público) e os logs brutos de execução (os JSON têm os mesmos dados).
