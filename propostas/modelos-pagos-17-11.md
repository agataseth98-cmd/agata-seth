# Modelos pagos pelo Agata em um comando (`modelos-pagos-17-11`)

Classe: Comportamento (`redesign/conexoes`).

Proposta P-8. Diff: `propostas/modelos-pagos-17-11.diff` (5 arquivos). Base: `origin/main` (62f2185d).

Decisão do Humano (17/11/2026): "temos que conseguir usar todos os modelos por dentro do sistema agata obedecendo as mesmas regras, inclusive os pagos e deve ser fácil configurar o sistema."

## O que muda

- `redesign/conexoes/configurar.py` (novo): `listar [--json]` (chave só pelo nome da variável) e `adicionar --id --base-url --chave-env --modelos [--formato] [--tarifa-entrada --tarifa-saida --cambio --tarifa-fonte --tarifa-data]`. Toda chamada passa por `adaptadores.chamar()`: orçamento, privacidade, custo e cofre valem igual.
- Recusa: id repetido, chave crua, base_url fora de https ou do gateway local, host ou porta inválidos; não ecoa valor recusado. Trava flock cobre catálogo e tarifa; rollback desfaz só o id adicionado.
- 22 testes novos em `tests/test_configurar.py`; spec e acceptance com 11 critérios; README com o passo a passo.

## Medido (17/11/2026)

- `pytest redesign/conexoes`: 36 passed. Gate de sincronia: 0 falha. `git apply --check` em cópia limpa: APLICA.
- Codex: r1 a r3 reprovaram com achados, todos corrigidos; r4 apontou o rollback que apagava gravação do painel, corrigido; o veredito da r4 não saiu (cota do Codex esgotada até 18/11 01:01). Revisão final pelo agata-revisor (Claude Sonnet 5.5): "Veredito: aprovar". Textos em `/home/orusoua/agata-arquivo/roteador-capacidade-17-11/codex-review-l5*.txt`.

## Não medido

- Chamada real a provedor pago; se o OmniRoute aceita a chave vinda do cofre; corrida real entre CLI e painel (o painel grava sem a trava).

## Reversão

`git apply -R` do diff. Provedor adicionado sai pelo painel ou removendo o bloco em `provedores.json`.

## Comando de assinatura

Depois do merge deste PR, no terminal, sem `!`:

bash scripts/aprovar.sh modelos-pagos-17-11

## Modelos

Claude Opus 5.5 orquestrou e conferiu; agata-dev (Claude Haiku 5.5) implementou; Codex e agata-revisor revisaram.
