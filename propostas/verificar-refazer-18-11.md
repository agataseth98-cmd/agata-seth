# Verificar e refazer antes de entregar (`verificar-refazer-18-11`)

Classe: Comportamento (runtime: `seth_gateway.py`).

Proposta P-8 de `verificar-refazer-18-11`. Diff: `propostas/verificar-refazer-18-11.diff` (3 arquivos: `redesign/router/seth_gateway.py`, `redesign/router/spec/spec.md`, `redesign/router/test_verificar_refazer.py`). Base: `origin/main` (5a88cb18). O diff não traz registro nem `ONDE_ESTAMOS.md`.

Origem: decisão do Humano em 17/11/2026, sobre a Seth: a checagem de fatos e as correções devem acontecer antes de a resposta chegar ao Humano.

Decisão do Humano (17/11): "os mecanismos de checagem de fatos e correções devem agir antes de a resposta do modelo ser apresentada, o que pode ser refeito embaixo do capô quantas vezes forem necessárias até a resposta ser confiável".

## O que muda

1. Auditoria antes da entrega: a resposta do modelo passa pela auditoria mecânica do turno (`auditoria_turno`) antes de sair para o cliente.
2. Nova tentativa com os achados: se a auditoria aponta achado, o gateway chama o upstream de novo com o mesmo pedido, a resposta ruim e uma nota com os achados (sanitizados, sem segredo nem dado pessoal).
3. Escalada de fila a cada tentativa, pelo mapa `_SUBIR_FILA`: `seth-rapido` -> `seth-livre` -> `seth-pesado` (o pesado volta ao livre).
4. Tetos, todos por variável de ambiente:
   - `SETH_REFAZER_MAX=2`: novas tentativas por resposta.
   - `SETH_REFAZER_SEG=60`: teto, em segundos, para as novas tentativas.
   - `SETH_REFAZER_1A_SEG=180`: prazo para a 1ª resposta chegar inteira; passou, segue sem refazer.
   - `SETH_REFAZER_BYTES=4MiB`: teto de bytes por coleta de resposta; passou, segue sem refazer.
5. Escolha da entrega: entrega a tentativa com menos achados. Se ainda sobrar achado, entrega com o bloco "Verificação da Máquina" como aviso.
6. Ativação: só com `SETH_REFAZER=1` ou com canário `SETH_ROTEADOR=capacidade:N` (N% dos pedidos). `SETH_REFAZER=0` desliga sempre. O caminho legado fica como estava.
7. Testes: `redesign/router/test_verificar_refazer.py` e a linha correspondente na `spec.md`.

## Medido (18/11/2026)

- Na worktree de lote, `pytest redesign/router`: 104 passed, 10 subtests passed (medido nesta rodada).
- Na worktree de lote, `seth_gateway.py --selftest`: SELFTEST OK, 89 PASS, 0 FAIL (medido nesta rodada).
- Testes de mutação: relato do executor, não reexecutados nesta rodada.
- `git apply --check` de `propostas/verificar-refazer-18-11.diff` em cópia limpa de `origin/main` (5a88cb18): APLICA (medido nesta rodada).
- Revisão independente do Codex: r1 a r4 reprovaram com achados, todos corrigidos. r5 não deu veredito: a cota de uso acabou ("usage limit"). Textos: `/home/orusoua/agata-arquivo/roteador-capacidade-17-11/codex-review-l2*.txt`.
- Revisão do agata-revisor (Claude Sonnet 5.5): aprovou e confirmou que o caminho legado é idêntico ao de `origin/main`.
- fixture de teste montada em pedaços para o P-1 (sem mudança de comportamento; após as revisões).

## Não medido

- Latência com upstream real: o primeiro byte só sai depois da checagem completa, e o custo de tempo do refazer não foi medido com provedor real.
- Taxa de achado e de acerto do refazer no tráfego real.
- `up.read()` do JSON, sem teto de bytes, no caminho legado (já existia em `origin/main`; achado BAIXO, fora do escopo desta proposta).
- Veredito do Codex na r5 (sem resposta por cota).

## Reversão

`SETH_REFAZER=0` desliga o refazer (reiniciar o gateway); ou `git apply -R` do diff e reiniciar o gateway.

## Comando de assinatura

Depois do merge deste PR, no terminal, sem `!`:

bash scripts/aprovar.sh verificar-refazer-18-11

## Modelos

Claude Opus 5.5 orquestrou; agente agata-dev (Claude Haiku 5.5) implementou; Codex e agata-revisor (Claude Sonnet 5.5) revisaram.
