# Proposta rotas-nuvem-19-11 — dois modelos NVIDIA gratuitos entram na rota da Seth, só para pedidos públicos

Ordens do Humano: 18/11 16:09 "habilite todos dentro da política do roteador já"; 19/11 08:19 "libere os três úteis no painel"; 19/11 09:06 aceita o uso possível dos pedidos públicos para treino pela NVIDIA; 19/11 10:18 "pode revisar vc mesmo seguindo as regras que estabelecemos".

**O quê:**
- `config/rotas-ficha.json` (D5): `nvidia-nemotron-3.5-super-vl` (conversa) e `nvidia-nemotron-3.5-bolt` (código e json), `categoria=gratuito`, `classes_permitidas=["publico"]`, `cota_medida=false`, `treina_com_prompts="nao_conferido_aceito_pelo_humano"`, teto de entrada 6000 tokens. `nvidia-laguna-xs` catalogada sem tipo: a faixa pública retira as ferramentas, e ela foi útil justamente em ferramenta.
- `redesign/rotas/ficha.py`: aceita `tipos` em rota gratuita só com classe pública; pessoal ou pago em nuvem continua erro.
- `redesign/router/rotas_locais.py`: `escolher_nuvem` (recusa segredo; ficha manda; painel só tira), cache por mtime.
- `redesign/router/seth_gateway.py`: só na faixa pública (`seth-livre` com cabeçalho public ou `seth-public`), depois de retirar ferramentas e canon; prazo ABSOLUTO de 30 s desde antes do pedido (headers, 1º conteúdo SSE e corpo JSON); qualquer falha cai na fila de sempre sem resposta duplicada; GET e HEAD zeram o estado.
- Nenhuma rota atual sai. Desliga com `SETH_ROTAS_NUVEM=0`.

**Prova:** NVIDIA 18–19/11, porta de entrada (`~/agata-arquivo/catalogo-modelos-18-11/prova-nvidia/comparacao-19-11.txt`): super-vl útil em conversa (p50 6,5 s), bolt útil em código e json (p50 1,6 s).

**Medido:** 294 testes (router, rotas, sentidos); na revisão final, 92 testes e selftest do gateway rodados pelo Opus; FICHA OK; CI local TUDO OK.

**Revisão:** Codex r1 e r2 reprovaram (prazo, keep-alive, testes integrados), agata-revisor r3 reprovou (JSON lento sem `_derrubar`), tudo corrigido; revisão final pelo Opus 5.5 com autorização do Humano (Codex sem cota).

**Não medido:** chamada real à NVIDIA pelo OmniRoute com esses ids; cota da conta.

**Reversão:** `git revert` do commit de aplicação, ou `SETH_ROTAS_NUVEM=0`.

**Modelo:** Sonnet 5.5 (implementação) orquestrado pelo Opus 5.5.
