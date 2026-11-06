# Experimento GPT — entrada de leitura

**Revisão de auditoria:** 04/11/2026 · GPT-6.1-sol.  
**Direção do Humano:** a arquitetura desenvolvida será a base da nova versão do Agata; Alexandria será um subsistema.

## Memória e ordem de leitura

Primeiro consulte [conclusoes.md](conclusoes.md): é o único diário de conclusões do experimento. Entradas antigas preservam erros e correções; precisam ser lidas com as retificações posteriores. Esta página é índice derivado, não outra memória.

Depois consulte o documento adequado:

| Documento | Responsabilidade |
|---|---|
| [Contrato](contrato-do-agata-rascunho.md) | autoridade, memória e limites do experimento |
| [Alexandria](proposta-tecnica-alexandria-editorial.md) | especificação integrada, interfaces e ciclo de evolução |
| [Avaliação](proposta-implementacao-buracos-experimento.md) | comparação, métricas e critérios de promoção |
| [Metacognição](proposta-tecnica-metacognicao-llm.md) | controle antes, durante e depois da tarefa |
| [Fundamentos](agata-llm-fundamentos-revisada.md) | fronteira técnica entre LLM e memória externa |
| [Inventário](inventario-servicos-agata-2026-11-04.md) | fotografia datada de serviços e modelos |
| [Redundância](matriz-redundancia-agata-2026-11-04.md) | dependências e candidatos; sem presunção de saúde |
| [Skill do experimento](skill-experimento-gpt/SKILL.md) | instruções para continuar este experimento |
| [Briefing](briefing-auditoria-modelo-fronteira.md) | roteiro de revisão futura |
| [Relatório de auditoria](auditoria-2026-11-04/relatorio.md) | achados, provas, correções e limites |
| [Handoff do executor](briefing-executor-nova-versao.md) | ordem de leitura, primeira entrega, limites e critérios de aceite |
| [Fontes](auditoria-2026-11-04/fontes.md) | referências verificadas e nível de leitura |
| [Transcrição](transcricao-etapa-1.txt) | captura automática preservada; fonte de inspiração, não validação científica |

## Precedência

As instruções vigentes do ambiente e o cânone real regem a atuação no Agata. A decisão humana sobre a nova versão aprova a direção do produto. Os documentos desta pasta especificam sua evolução; não constituem assinatura P-8.

Nesta revisão, Alexandria é a fonte do desenho integrado, avaliação define o método e contrato define a governança experimental. Divergência deve gerar correção explícita, sem apagar a memória histórica. O relatório atual retifica as alegações anteriores de auditoria completa e de disponibilidade funcional dos modelos.

## Fases e estados

O plano comum é F0 especificação, F1 piloto em sombra, F2 avaliação e F3 integração protegida. As sete palavras organizam evolução, com Remoção opcional e retornos definidos na proposta Alexandria. Estados editoriais, de execução e de saúde são dimensões diferentes.

## Estado de entrega

A pasta contém especificação e evidência de auditoria. O registro em disco sobrevive à troca de modelo; respostas equivalentes e recuperação correta ainda exigem avaliação. Não houve implantação de Alexandria nem rodada nova de inferência nesta auditoria.

## Entrada do executor

O executor deve começar pelo [handoff](briefing-executor-nova-versao.md), confirmar o estado atual do repositório Agata e produzir primeiro um plano de execução delimitado. A arquitetura aprovada define direção de produto; cada mudança no Agata real continua sujeita ao fluxo protegido, às permissões específicas e aos critérios de avaliação.

Os originais anteriores à revisão estão em [originais.tar.gz](auditoria-2026-11-04/originais.tar.gz). [Evidências iniciais](auditoria-2026-11-04/evidencias-iniciais.json) fixam hashes, horário, HEAD, serviços e catálogos. O [verificador](auditoria-2026-11-04/verificar_pasta.py) confere integridade e estrutura; não certifica verdade semântica.
