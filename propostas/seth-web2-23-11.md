# Proposta seth-web2-23-11 — busca melhor e cabeçalho único no painel (uma assinatura)

Origem: conversa de auditoria com a Seth no painel, 23/11 08:12–08:15, pedida pelo Humano ("converse de verdade com a Seth a procura de melhorias e erros").

**1. Cabeçalho único por resposta** (`ferramentas_seth.laco`). A cada rodada de ferramenta o painel devolvia ao gateway o assistant com `content` vazio; o gateway (`_em_andamento` vazio) repunha o cabeçalho da Máquina. Medido na conversa: 2 cabeçalhos nas respostas 1 e 2. Agora o texto já mostrado na rodada volta no `content`. Teste confere o content e a condição do gateway (`auditoria_turno._em_andamento` não vazio). A Seth sugeriu "não escrever cabeçalho"; errado, quem escreve é a Máquina.

**2. Busca** (`redesign/mcp/navegador/`). Medido: o RSS do Bing casa só a 1ª palavra ("capital da Mongólia" → corretoras e rádio; "data de lançamento…" → relógios). Entra a API de busca da Wikipedia (pt e en, 3 de cada, 8 s, User-Agent próprio sem dado pessoal; 429 ignorado), no máximo 3 no topo; filtro por termos sem acento (Wikipedia metade, Bing 2/3); busca vazia leva à Seth o aviso do que tentar. Funções puras em `busca_filtro.py`, testadas no CI. Ao vivo: "Python 3.14 release date" → History of Python 1º; "capital da Mongólia" → Mongólia, Ulaanbaatar. Limite: "data de lançamento do Python 3.14" ainda traz ruído; fato preciso pede `ler_pagina` na fonte oficial.

**Revisão independente (agata-revisor):** 8 achados; corrigidos 2–6 e 8 (teste da condição do gateway, módulo testável no CI, teto da Wikipedia, timeout 8 s, `relacionado` sem acento, destino nomeado no risco). Não medidos e declarados na spec: cópia do cabeçalho pelo modelo na rodada 2; efeito na auditoria de ler o texto das rodadas intermediárias; aceitação duradoura do User-Agent pela Wikimedia.

**Fora:** o "painel escondido" lido pela ferramenta de leitura de página não é defeito (seção com `hidden`).

**Medido:** 52 testes (painel + busca); autoteste offline do navegador; CI local TUDO OK. **Depois de aplicar:** restart navegador-mcp e painel-operacional. **Reversão:** git revert + restart. **Modelo:** Opus 5.5 (código), Haiku 5.5 (revisão).
