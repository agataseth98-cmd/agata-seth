# Registro de fontes da auditoria

Consulta em 04/11/2026. Esta é uma verificação dirigida das referências que sustentam o desenho, não revisão sistemática de toda a literatura de 2026.

N1 = seção pertinente da fonte primária lida; N2 = resumo/página bibliográfica; relato dos autores ou fornecedor permanece atribuído. Nenhum benchmark externo foi reproduzido nesta auditoria.

| Fonte | Versão e leitura | Alcance usado |
|---|---|---|
| [SkillRouter](https://arxiv.org/abs/2603.22455v5) | v5, 20/07/2026; N2, resumo | corpo da skill pode ajudar roteamento em catálogo grande; não prova ganho em catálogo pequeno do Agata |
| [Skill Is Not Document](https://arxiv.org/abs/2606.03565v5) | v5, 04/08/2026; N2, resumo | compatibilidade do conjunto depende da tarefa, além da relevância individual |
| [Toollery](https://arxiv.org/abs/2609.22218v2) | v2, 18/10/2026; N2, resumo | compressão de candidatos e buscas por intenções; benefícios dependem da carga |
| [SkillsBench](https://arxiv.org/abs/2602.12670v4) | v4, 14/06/2026; N2, resumo | avaliação pareada de skills e diferenças por pacote/modelo; não é certificação de uma skill |
| [Agent Skills](https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills) | 16/10/2025, atualização 18/12/2025; N1, anatomia, avaliação e segurança | metadados inicialmente, SKILL completo quando selecionado e referências sob demanda |
| [Memora](https://www.microsoft.com/en-us/research/blog/memora-a-harmonic-memory-representation-balancing-abstraction-and-specificity/) | 29/06/2026; N1, apresentação e mecanismo | autores separam conteúdo de representações de recuperação; blog não foi substituído por reprodução do paper |
| [GraphRAG](https://arxiv.org/abs/2404.16130v2) | v2, 19/02/2025; N2, resumo | resultado sobre síntese global em corpus privado; não demonstra superioridade universal nem revoga recusa local |
| [W3C PROV-O](https://www.w3.org/TR/2013/REC-prov-o-20130430/) | Recommendation, 30/04/2013; N1, resumo e descrição introdutória | modelo interoperável de proveniência; inspira relações entre objetos, atividades e agentes |
| [W3C SKOS](https://www.w3.org/TR/2009/REC-skos-reference-20090818/) | Recommendation, 18/08/2009; N1, resumo e sinopse | vocabulário controlado, rótulos e relações entre conceitos; não é oráculo de verdade |
| [FADGI TCR4CAP](https://www.digitizationguidelines.gov/guidelines/tcr-cap.html) | v0.2, 08/09/2026; N1, página descritiva | rascunho para comentários, não padrão de conformidade aprovado; autenticidade/proveniência em acervos afetados por IA |

## Retificações de uso

As referências SkillRouter, R3 e Toollery existem nas páginas primárias consultadas. Os resumos atuais têm títulos e alguns resultados diferentes das versões mencionadas antes. Fixar versão ao citar números; a conclusão 064 é orientação de desenho, não prova de “maneira mais eficaz” no Agata.

A documentação de Skills usa divulgação progressiva. Isso é compatível com o indexador analisar o corpo para roteamento e o executor ler integralmente o SKILL selecionado. Não exige pôr todos os corpos no prompt.

O desenho de Memora pode atualizar unidades de memória; a disciplina append-only do Agata exige representar tais mudanças por eventos/derivados versionados. Não copiar a atualização destrutiva como política de história.

## Fontes pendentes e limites

A página PREMIS da Library of Congress falhou com timeout e depois 403. O texto de auditoria por afirmação da MDPI citado anteriormente respondeu 429. Não foram usados como prova lida desta revisão. As alegações históricas sobre esses itens precisam de leitura antes de uso formal.

O vídeo da transcrição é divulgação e a captura automática não foi confrontada com todo o áudio. Ele oferece inspiração, não evidência de eficácia clínica ou computacional. Alexandria histórica permanece metáfora cultural; não sustenta requisitos técnicos.

Não foi feita avaliação exaustiva de memória humana, de todos os livros ou de todos os trabalhos publicados em 2026. O estado da arte citado é um recorte pertinente ao projeto.
