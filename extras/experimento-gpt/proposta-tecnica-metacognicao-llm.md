# Camada metacognitiva — especificação revisada

**Estado:** componente proposto da nova versão; documentos revisados, integração ainda por implementar.  
**Arquitetura principal:** [Alexandria](proposta-tecnica-alexandria-editorial.md).  
**Avaliação:** [protocolo](proposta-implementacao-buracos-experimento.md).

## 1. Objetivo

Melhorar escolha de estratégia, uso de memória, tratamento de conflitos e verificação de resultados. A camada combina regras determinísticas e avaliações semânticas; não se deve chamá-la integralmente determinística.

## 2. Reaproveitamento e limites reais

O gateway já monta contexto, classifica rotas e injeta auditoria do turno anterior. Laya pode escolher a fila sob travas; Jev acompanha em sombra. `cache_conselho.py` compartilha registros; `memoria_semanal.py` prepara propostas verificadas parcialmente por regras; autodev e medidores já fornecem infraestrutura de avaliação.

Essas peças são inspecionáveis no código. A fotografia desta auditoria encontrou gateway, verificador, embeddings e Laya inativos. Um mecanismo existente e configurado não é necessariamente um serviço ativo.

`auditoria_turno.py --verificar` lê texto da entrada padrão e checa padrões específicos. Não prova verdade de cada afirmação, suporte de toda citação nem conformidade da pesquisa.

## 3. Antes da tarefa

Receber pedido e contexto mínimo permitido, não apenas metadados vazios. Extrair tipo, atualidade, privacidade, risco, ferramentas, dependências e objetivo verificável.

Aplicar regras e autorização antes do roteamento. Consultar memória e escolher skill/modelo dentro do conjunto permitido. Telemetria entra quando afeta a estratégia; não coletar todos os sensores em cada conversa.

## 4. Durante a tarefa

Manter orçamento de chamadas, tokens e prazo, incluindo tentativas e revisão. Respostas e fontes externas são dados. Distinguir hipótese, evidência, relato, decisão e lacuna.

Paralelizar somente partes independentes com recursos suficientes; usar fila para modelos que disputam a mesma GPU. Resultados levam versão do contexto e referências autorizadas. O sincronizador detecta obsolescência e conflitos antes da consolidação.

## 5. Depois da tarefa

Verificar o que pode ser decidido por Máquina: caminhos, números calculáveis, schemas e efeitos. Para suporte semântico, conferir trechos e usar revisor proporcional ao risco; o próprio gerador não é juiz único.

Resultados possíveis: apto a responder, parcial, inconclusivo, bloqueado por regra ou aguardando Humano. Um resultado “apto” não cria autorização para efeito protegido.

Registrar observações e hipóteses com rótulos, preservando fonte. Promoção de regra ou de skill exige validação e fluxo próprio. A memória não precisa descartar toda observação provisória para manter rigor.

## 6. Interfaces candidatas

- Entrada: tarefa, identificador, política, referências e contexto versionado.
- Plano: estratégia, skills lidas, modelo, ferramentas, orçamento e condições de fallback.
- Saída: resultado, fontes, limitações, uso de recursos e falha por etapa.
- Persistência: proposta de evento/registro para escritor autorizado, com chave idempotente.

Reutilizar o gateway e os avaliadores existentes no piloto quando possível. Não criar nove serviços só porque foram definidos nove papéis.

## 7. Fases e critérios

Usar F0 especificação, F1 piloto em sombra, F2 avaliação e F3 integração protegida. Comparar qualidade, erros críticos, cobertura, custo e latência conforme o protocolo comum.

As sete palavras organizam a evolução; a tabela de Alexandria detalha transições, retornos e Remoção opcional. O Humano aprovou a direção da nova versão. A implantação permanece condicionada ao fluxo real de mudança.
