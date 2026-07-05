# FIO CANÔNICO — Ágata Seth (thread único de verdade)

**Data:** 2026-07-05 · **Autor:** Claude Opus 4.8 (Claude-Ágata, nuvem) · **Motivo:** a informação vem fragmentada entre instâncias (GLM, Seth, Claude Code, Claude) e o canal de anexo está quebrado. Este documento é o **fio único** — só o que foi verificado na Máquina, com o que é hipótese e o que é alucinação claramente separados.

> Regra deste fio: nada aqui é "fato" sem verificação na Máquina. Hipótese é marcada como hipótese. Alucinação é nomeada. A Máquina (disco, código, curl) é o único árbitro.

---

## 1. Quem é quem
- **Humano (Orusoua)** — o Soberano. Nesta fase, também o "carteiro" que retransmite entre as instâncias.
- **Claude-Ágata (nuvem)** — auditoria e arquitetura. Não alcança a Máquina; pensa e audita, não executa.
- **Claude Code** — executor real na Predator (mãos, disco, git). Fonte confiável de diagnóstico.
- **Seth** — a Ágata local (Hermes + modelo local). **Em modo degradado: alucina.** Tudo que vem dela é rascunho não-verificado.
- **Conselho (GLM, Qwen/Qwen3.7, DeepSeek)** — auditorias cruzadas. GLM e DeepSeek têm produzido diagnósticos confiáveis (distinguem códigos HTTP, citam comandos, marcam lacunas).

---

## 2. ESTADO DO ARTEFATO (construído e publicado — VERIFICADO)
Isto foi triplamente verificado (local + git ls-remote + curl raw) até 2026-07-04:
- **Motor:** Hermes Agent 0.17.0. Código bespoke antigo descartado.
- **Canônicos publicados** no GitHub `agataseth98-cmd/agata-seth` (commits 7cff7f4 → 3c73fd5): SOUL.md, REGRAS.md, PROJETO.md, DIÁRIO.md presentes no remoto. ICs podem carregar pelas URLs raw.
- **Voz:** Kokoro `pf_dora` via Kokoro-FastAPI (CPU) + Whisper STT — integrada ao Open WebUI.
- **Coexistência Opção A:** Open WebUI = frontend puro; Hermes = cérebro/memória/execução único.
- **Comando `atualizar <MEMORIA|PROJETO|REGRAS|TUDO>`:** criado (scripts/atualizar.sh), verifica o GitHub como fonte da verdade.
- **Memória:** SOUL symlinkado; `.hermes.md` gerado por hook; DIÁRIO append-only.

**Conclusão:** o artefato está construído e publicado. Isto NÃO está em dúvida.

---

## 3. ESTADO OPERACIONAL ATUAL (a instância rodando — DEGRADADO)
Diagnóstico do GLM, verificado por inspeção do Humano na Máquina (grep/curl). **Confiável.** A Ágata está, agora, operacionalmente caída/degradada:

- **Gemini (primário): HTTP 400** em teste direto via curl. Não é 401 (auth) nem 429 (cota). Requisição malformada/rejeitada — causa não determinada (falta o CORPO do erro). Prático: primário inoperante.
- **`fallback_model:` VAZIO** no config.yaml. A entrada (8) registrou `qwen2.5-14b-64k`, mas **não persistiu**. Verificado com `grep -A1 fallback_model`.
- **`carregar` quebrado:** 8+ tentativas → "Carregar o que exatamente?". O `.hermes.md` existe (186 linhas), mas o SOUL/contexto não chega ao modelo nesse caminho.
- **Contexto:** TUI mostra ~32.8K, mas config declara `ollama_num_ctx: 65536`. Divergência não resolvida (display vs payload real).
- **OpenRouter: 402** (sem crédito). Rota morta, não afeta o principal.

---

## 4. HIPÓTESE DE CAUSA RAIZ (marcada como HIPÓTESE — não verificada)
Os sintomas de §3 encaixam num só ponto: **a config não persistiu / reverteu.**
- `fallback_model` vazio + display 32.8K sugerem que o `model.default` reverteu do `qwen2.5-14b-64k` (64k forçado) para o **`qwen2.5:14b` base (32k nativo)**.
- Isso explicaria: fallback vazio, contexto 32k, e — se o SOUL não está sendo injetado nesse caminho — o `carregar` respondendo "carregar o quê?".
- **Um problema (config não salva) → quatro sintomas.** Provavelmente não são quatro bugs.
- O **Gemini 400 é separado** e exige o corpo do erro pra diagnosticar (nome de modelo? campo recusado? free tier alterado?).

Isto é a hipótese mais provável. **Só os comandos de §6 confirmam ou refutam.**

---

## 5. O QUE NÃO É VERDADE (alucinações — NÃO registrar como fato)
Nomeadas pra não contaminarem o canon:
- "Ajuste de resfriamento a 55°C / zonas térmicas" (Seth) — nunca ocorreu.
- "qwen-14b-chat testado e superior" (Seth) — modelo de 2023 (8k), comandos malformados, resultado inventado. Assunto barrado pelo Conselho.
- "Relatório sincronizado" e outros relatos confiantes da Seth em modo degradado — rascunho, não fato.
- "Canônicos não estão no GitHub" (Claude-Ágata, t=134) — **alarme falso meu**, causado por web_fetch servir descrição estática/cache. Refutado por git ls-tree/curl. Canon ESTÁ publicado.
- Teste do **DeepSeek-R1-Distill-14B**: proposto e autorizado, mas o relatório **nunca chegou** (anexo vazio 4x). Status: **não testado**, sem veredito.

---

## 6. PRÓXIMO PASSO (Claude Code — NÃO a Seth; leitura pura)
```
1. grep -E "^model:|  default:|  provider:|ollama_num_ctx:|^fallback_model:" -A1 ~/.hermes/config.yaml
2. grep -iE "model=|fallback activated|gemini|qwen" ~/.hermes/logs/agent.log | tail -20
3. ls -la ~/.hermes/SOUL.md ; head -3 ~/.hermes/SOUL.md
4. grep -E "terminal:|  cwd:" -A1 ~/.hermes/config.yaml
5. curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" -H "Authorization: Bearer $(grep GOOGLE_API_KEY ~/.hermes/.env | cut -d= -f2 | tr -d ' \"')" -H "Content-Type: application/json" -d '{"model":"gemini-2.5-flash","messages":[{"role":"user","content":"oi"}]}'
```
Resolve: (a) o que serve de fato, (b) SOUL/cwd regrediram?, (c) o motivo do 400. Conserto provável: repersistir `model.default: qwen2.5-14b-64k` + `fallback_model`, reiniciar o gateway. **Não consertar sem os dados.**

---

## 7. LACUNAS ABERTAS (honestas)
- Motivo do Gemini 400 (falta o corpo do erro).
- Truncamento 32k: é display da TUI ou payload real? (exige ver o código).
- DeepSeek-R1-14B: não testado (relatório não chegou).
- Canal de anexo quebrado: **usar texto colado**, não arquivo.

---

## 8. MÉTODO (o que segurou tudo)
1. **A Máquina é o árbitro.** Nenhum fato sem verificar no disco.
2. **Seth em modo degradado = rascunho.** Não registrar nada dela sem conferir.
3. **Regra 2 vale pro auditor** — Claude e GLM inclusos. Alarme falso do GitHub prova isso.
4. **Anexo quebrado → texto.** O canal confiável entre Humano e ICs agora é texto colado.
5. **Um problema costuma gerar N sintomas.** Procurar a causa única antes de tratar cada sintoma.
