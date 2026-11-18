# Proposta rotas-novas-18-11 — a Seth passa a usar o modelo local que provou ser melhor, e o Ollama sobe e desce com o sistema

Ordens do Humano em 18/11/2026: "habilite todos dentro da política do roteador já"; "ligar a decisão do painel às rotas: autorizado"; "quero a Seth já funcionando pelas novas regras de roteamento, garanta isso"; "[o Ollama] tem que estar ligado quando o sistema for ligado e desligado quando o sistema for desligado"; prazo = "maior tempo de resposta com sucesso + 30 s".

**Rotas (`config/rotas-ficha.json`, `redesign/rotas/ficha.py`, `redesign/router/rotas_locais.py`, `seth_gateway.py`)**
- Só `seth-livre`, fora da faixa pública: JSON, código e contexto longo (> 6000 tokens) vão para `qwen3-30b-a3b-64k` (local). Melhor nos três pela prova e pela auditoria de conteúdo de 18/11. Conversa e ferramenta: regra de hoje.
- lfm3:1.7b, rlm-qwen3-8b-teste e lumi-4b ficam na ficha com `tipos: []` (catalogados, não roteados; o Humano tem planos para eles). qwen3.5-9b-64k segue como reserva. Nada removido.
- Política: local atende classe pessoal; **segredo nunca vai a rota nenhuma**; nuvem nunca ganha tipo (o validador recusa).
- Painel só restringe: modelo cuja última decisão é "standby" sai da rota na hora; "liberado" não acrescenta nada além da ficha assinada.
- Queda segura: Ollama fora (teste de porta), HTTP ≥ 400, resposta vazia, corpo cortado, erro de conexão ou prazo estourado → o pedido volta à fila de sempre, sem erro ao usuário. Só POST; GET nunca é reenviado.
- Prazo da rota local: 100,5 s (maior sucesso medido do qwen3-30b, 70,5 s, + 30 s), `SETH_ROTA_LOCAL_MS`. Desliga tudo: `SETH_ROTAS_LOCAIS=0`.

**Ollama com o sistema (`redesign/systemd/ollama-agata.service`, `seth`, `seth-parar`, README, `config/servicos-agata.txt`)**
- Unit de usuário presa ao `agata.target`; `seth` sobe e `seth-parar` descarrega os modelos e desce.
- Migração única com sudo (no README): desabilitar a unit do sistema, copiar os modelos para `~/.local/share/ollama/models`, habilitar a unit de usuário.

**Medido:** 188 testes (router + rotas), selftest do gateway OK, CI local TUDO OK, `systemd-analyze --user verify` da unit OK. Inclui keep-alive real na mesma conexão (lição do incidente de 18/11), quedas por 500, vazio, corpo cortado, conexão e prazo, segredo com a injeção real, gates de faixa.

**Revisão:** agata-revisor r1 reprovou (14 achados, um alto de keep-alive), r2 reprovou (pontos médios); todos corrigidos com teste. Codex sem cota até 20:04.

**Não medido:** carga a frio do qwen3-30b no Ollama de usuário; a unit em execução real (depende da migração).

**Reversão:** `git revert` do commit de aplicação, ou `SETH_ROTAS_LOCAIS=0` sem revert.

**Modelo:** Sonnet 5.5 (implementação) orquestrado pelo Opus 5.5; revisão agata-revisor (Haiku).
