# Proposta capacidade-producao-23-11 — modelos escolhidos por capacidade, respostas só depois da correção (uma assinatura)

Decisões do Humano, 23/11/2026 (cache do Conselho 720-722): 16:40 "todos os modelos devem ser escolhidos a partir de suas capacidades, se ainda não houverem devem ser colocados em produção seguindo essa regra e suas capivaras puxadas a partir de pesquisa na internet e melhorada com o uso, agata code segue as mesmas regras"; 18:18 "as respostas só saem depois da correção do sistema que deve ser refinado com uso"; 18:34 "não temos pressa e sim um desejo visceral por qualidade".

Feito por agentes do sistema (agata-dev ×2, agata-revisor ×2, Explore; Claude Haiku 5.5), orquestrado e conferido pelo Claude Opus 5.5.

## Antes (medido em 23/11)
Nenhuma porta escolhia modelo por capacidade: Laya escolhe a classe; a fila do OmniRoute decide em ordem manual; Agata Code e agentes do Claude Code fixos. A Capivara só pesava na janela; perfis de 24-25/10 (benchmark local, 6 amostras por tipo) e 2 janelas copiadas à mão; nada da internet, nada do uso. O roteamento por capacidade rodava só em sombra (473 decisões registradas, 137 diferentes do 1º da fila). Verificar-e-refazer existia desde 18/11, desligado por padrão.

## O que muda
1. **Capivara única** (`scripts/capivara_capacidades.py`): um registro com camadas catalogo/declarado/medido/observado, janela e saída por modelo, cada número com origem e data; cobre OmniRoute + catálogo (523 modelos; 109 com janela conhecida, 414 "não medido" — nunca número inventado). O perfil que o gateway lê é derivado dele.
2. **Semeada por pesquisa** (`pesquisar_modelos_gratuitos.py`, já semanal): janela, saída, ferramentas e raciocínio do OmniRoute local e das listas públicas OpenRouter e NVIDIA (GET sem chave, sem dado do usuário). Grava **só no estado** `~/.local/share/agata/capivara/` (o repositório vivo não muda sozinho; `config/capivara/` é o retrato versionado).
3. **Melhorada com o uso**: o gateway grava `~/.local/share/agata/capivara/uso.jsonl` por pedido, SEM texto (modelo servido, tipo, classe de dado, status, barrado, latência, rota e quem decidiu — Laya ou regra — e a confiança do Laya, códigos dos achados da conferência, refações, corrigido). Falhas também. A etapa semanal acumula em `observado` (taxa_ok, taxa_achado, taxa_corrigido, refeito_medio; perfil do próprio Laya por rota; placar das regras da conferência).
4. **Escolha em produção** (`seth_gateway.py`, `sombra_capacidade.py`): depois da classe do Laya, se um modelo tem qualidade medida >= 0,7 com amostra >= 6 para o tipo do pedido, cabe na janela, não está degradado no uso (taxa_ok < 0,8 ou taxa_achado >= 0,3 com n >= 20) e, em stream, começa a responder em menos de 40 s (p95), o gateway pede esse modelo; senão, a fila de sempre. Falha do concreto volta à fila. **Dado pessoal: a escolha só manda a modelo local; sem local qualificado, a fila de sempre** (que, pela decisão relaxa-pessoal de 22/10, pode ser remota — inalterado). Segredo nunca escolhe. Sai pelo mesmo sanitizador. `SETH_ESCOLHA_CAPACIDADE=0` desliga. Simulado com o registro de hoje: público código/JSON → gemini flash-lite; pessoal → qwen3-30b local; conversa → fila.
5. **Agata Code** segue a regra: entra pelo seth-livre e passa pela mesma escolha (tipo código/ferramenta).
6. **Respostas só depois da correção**: verificar-e-refazer passa a padrão (até 2 refações, 180 s), teto total 600 s por pedido (entrega a melhor conferida). `SETH_REFAZER=0` desliga.
7. **Progresso visível (Regra 0)**: em stream, comentário ": agata coletando/conferindo/refazendo · tentativa n/3 · Ns" a cada 10 s; ": agata modelo <id>" e ": agata rota <rota>"; o painel mostra a etapa como estado e mantém o selo de modelos sem repetição.
8. **Comentários corrigidos**: o proxy bloqueia segredo; dado pessoal não é varrido desde 22/10 (os comentários diziam o contrário).

## Revisões independentes (duas)
1ª: bloqueio (texto prometia "pessoal só local" na queda) + 6 correções — feitas. 2ª: bloqueio (sem candidato, a escolha aceitava o 1º da fila, inclusive nuvem com dado pessoal) — corrigido e conferido pelo coordenador (pessoal → local; público → nuvem); exclusão por uso sobre delta → acumulado; erro depois dos cabeçalhos → fecha com evento de erro; teto total; vocabulário único de achados; rota trocada avisada; selo por rodada no painel.

## Medido
CI local: `CI LOCAL: TUDO OK`. Roteador: 404 testes (eram 317). Capivara: 88 testes com mutações pegas. Painel: 819. `git apply --check` em cópia limpa: OK.

## Não medido
Aceitação real do OmniRoute para cada nome concreto (cai na fila se recusar) e latência real da conferência: conferir depois de aplicar, pela Seth. Clientes que não são o painel (OpenCode/Agata Code) com comentários SSE (a especificação manda ignorar). Perda de linhas se o uso.jsonl for rotacionado (hoje nada rotaciona).

## Para o próximo lote ("qualidade sem pressa", decisão de 18:34)
Tirar o filtro de 40 s e esperar o modelo melhor até 5 min com progresso — exige refazer os caminhos de erro depois dos cabeçalhos; a revisão pediu lote próprio.

## Fora, decisão do Humano
Agentes do Claude Code (modelos Claude, fora da Capivara e do OmniRoute); números iniciais 0,7 / 6 / 0,8 / 0,3 / 20; promoção do Laya pelo placar.

## Depois de aplicar
Restart do seth-gateway e do painel; pedidos de teste pela Seth (público e com dado pessoal fictício) conferindo o modelo servido e o uso.jsonl; rodar uma vez a etapa da Capivara para criar o estado.

**Reversão:** `git apply -R propostas/aplicadas/capacidade-producao-23-11.diff` e restart; ou só `SETH_ESCOLHA_CAPACIDADE=0` / `SETH_REFAZER=0` no serviço.

Assinatura: bash scripts/aprovar.sh capacidade-producao-23-11
