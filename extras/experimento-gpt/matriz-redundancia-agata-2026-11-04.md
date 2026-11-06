# Redundância do Agata — proposta revisada

**Estado:** desenho para a nova versão; candidatos não promovidos a rotas operacionais.  
**Base:** [inventário datado](inventario-servicos-agata-2026-11-04.md) e [evidência](auditoria-2026-11-04/evidencias-iniciais.json).  
**Integração:** [Alexandria](proposta-tecnica-alexandria-editorial.md).

## 1. O que precisa sobreviver

A falha de modelo, cota, rede, serviço ou índice pode ser contida por caminhos alternativos. Precisão e independência factual exigem outro tipo de evidência: dois provedores podem repetir a mesma fonte errada.

Distinguir redundância de processamento, conectividade, conhecimento, memória e autorização. Duas LLMs na mesma GPU compartilham um ponto de falha. Duas cópias na mesma unidade de disco não equivalem a backup restaurável.

## 2. Matriz por capacidade

| Capacidade | Referência atual observada | Alternativa candidata | Situação e fallback |
|---|---|---|---|
| Conversa | combo seth-livre, inicia em Ministral 14B | outros elos já configurados | sucesso não retestado; Qwen local no fundo |
| Resposta breve | seth-rapido | demais elos da fila | testar formato e latência no contexto real |
| Tarefa complexa | seth-pesado | Gemini/Qwen já no combo | não deduzir raciocínio superior pelo tamanho |
| Código | seth-codigo, inicia em Codestral | demais elos configurados | catálogo marcou Codestral false; exige teste antes de depender dele |
| Ferramentas | capacidade a validar por modelo e prompt | ferramenta determinística ou outra rota autorizada | Lumi não é fallback aprovado só por estar instalado |
| Documento privado | rota local elegível | outro local com orçamento compatível | fila na GPU; sem escalada remota do conteúdo |
| Visão | Gemini com flag de catálogo | descrição textual fornecida ou processamento local testado | mesma família/provedor é falha comum; teste funcional pendente |
| Recuperação | lexical/vault e confirmação na fonte | semântica secundária quando serviço disponível | manter lexical se embeddings caírem |
| Embedding da memória real | e5 no serviço local 20134 | nomic é candidato, não substituto direto | mudança requer reindexação, compatibilidade e medição |
| Auditoria | predicados mecânicos + revisão de fonte | teste com oráculo distinto/revisor | repetir script não verifica a lógica independentemente |
| Persistência | fontes e histórico versionados | cópia de segurança autorizada + índice reconstruível | teste de restauração ainda necessário |

Groq, Mistral Large e Devstral podem ser candidatos experimentais quando permitidos. A decisão real que tirou Groq das filas não é revertida por esta matriz. Nenhum papel exige uma LLM fixa.

## 3. Independência e verificação

Registrar por alternativa: modelo/família, provedor, credencial/cota, runtime, hardware, rede, fonte original, dados compartilhados e revisor. A independência pode ser parcial e precisa de descrição, não de rótulo absoluto.

Checksums conferem bytes; testes de restauração conferem recuperação; inspeção de suporte confere relação entre afirmação e trecho. Consenso e número de agentes não substituem esses testes.

## 4. Estados e roteamento

Estado de saúde: normal, pressionado, degradado, isolado ou indisponível. Classificação precisa de indicadores e data; não inferir saúde do hardware apenas pelo inventário de portas.

Fallback preserva privacidade e autorização. Falha registrada conduz à rota permitida; ausência de evidência produz resposta parcial ou abstenção. Nenhuma ação de fallback autoriza reinício ou instalação.

Para paralelismo, usar tarefa e contexto versionados, timeout, limite total de chamadas e fila para recurso compartilhado. Cancelamento impede novos efeitos; escritor único e idempotência evitam duplicação. Conflito substantivo exige revisão.

## 5. Memória e Alexandria

Alexandria é consultada primeiro logicamente. Em atualidade, consulta local e Internet podem iniciar em paralelo, com egresso minimizado e permitido. A fonte recente só corrige uma afirmação após verificação; sua data não revoga uma decisão humana.

Histórico, catálogo, vault e cache têm funções distintas, não são réplicas equivalentes. O catálogo deve apontar para fontes e derivados e permitir reconstrução dos índices.

## 6. Promoção por evidência

Aplicar o ciclo das sete palavras de Alexandria com Remoção opcional. Uma rota só é redundância demonstrada para uma tarefa após teste funcional pertinente, comparação de dependências e ensaio de falha/retorno autorizado.

Plano comum: F0 especificação, F1 sombra, F2 avaliação, F3 integração protegida. Medir serial/paralelo e custo completo antes de criar chamadas especulativas permanentes.
