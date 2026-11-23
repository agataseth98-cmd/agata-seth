# Proposta rotas-novas-18-11b — rotas novas da Seth com o Ollama SOB DEMANDA (substitui rotas-novas-18-11)

Correção do Humano em 18/11/2026 18:15: "O que muda no Ollama: passa a ligar e desligar junto com o sistema — negativo, sob demanda." Esta proposta substitui `rotas-novas-18-11` (no main, NÃO assinada; não deve ser assinada).

**Rotas da Seth:** idênticas a `rotas-novas-18-11` (ver `propostas/rotas-novas-18-11.md`): qwen3-30b-a3b local em JSON, código e contexto longo só em `seth-livre`; segredo nunca vai a rota; painel só restringe; queda segura para a fila de sempre (Ollama fora, HTTP ≥ 400, vazio, corpo cortado, conexão, prazo); prazo da rota local 100,5 s; lfm3, rlm e lumi catalogados sem rota; `SETH_ROTAS_LOCAIS=0` desliga.

**Ollama sob demanda** (mesmo padrão do Laya e do Ollaya, lote sob-demanda-17-11):
- `config/ollama-agata.socket` escuta 127.0.0.1:11434 (único no ciclo do `agata.target`).
- `config/ollama-agata-proxy.service`: `systemd-socket-proxyd --exit-idle-time=15min` para a porta interna 11447 (declarada em `config/portas-agata.txt`).
- `config/ollama-agata.service`: o Ollama em :11447, `StopWhenUnneeded`, sobe no 1º pedido e para após 15 min ocioso; espera HTTP antes de liberar.
- `seth-parar` só descarrega modelos se o backend estiver ativo; o P-9 do perímetro não acorda mais o Ollama.
- Partida a frio: coberta pelo prazo da rota local e pela queda segura; tempo real de subir e carregar o qwen3-30b NÃO medido.
- Migração única com sudo no `redesign/systemd/README.md`.

**Medido:** 190 testes (router + rotas), 16 de sob demanda, selftest do gateway OK, `systemd-analyze --user verify` nas 3 units OK, CI local TUDO OK.

**Risco conhecido:** painel e scripts de medição consultam :11434; com a página aberta, podem impedir a parada por ociosidade (frequência não medida).

**Reversão:** `git revert` do commit de aplicação, ou `SETH_ROTAS_LOCAIS=0`.

**Modelo:** Sonnet 5.5 (implementação) orquestrado pelo Opus 5.5; revisão agata-revisor nas rodadas de rotas.
