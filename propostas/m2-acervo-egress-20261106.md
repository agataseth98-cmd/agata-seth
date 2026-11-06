# Proposta M2 — Acervo com erro visível, egress sem userinfo

**Nome para assinatura:** `m2-acervo-egress-20261106`

## Mudança
- `redesign/alexandria/cadastro.py`: `listar_com_falhas()` devolve cadastros legíveis e a contagem de ilegíveis; `listar()` continua igual.
- `redesign/painel_operacional/nova_versao_painel.py`: `acervo_listar` devolve `estado` (ok, vazio, parcial, erro) e `ilegiveis`.
- `redesign/painel_operacional/nova_versao.js`: o título e a mensagem vazia mostram erro e contagem.
- `scripts/politica_egress.py`: URL com `@` no endereço (usuário ou senha) é recusada antes do DNS.
- Testes: `redesign/alexandria/tests/test_egress_userinfo.py` (novo) e dois casos em `test_nova_versao_painel.py`.

## Fora desta proposta
- Allowlist por destinatário (decisão do Humano).
- Rótulo "SOMENTE LEITURA" (não decidido qual tela está errada).

## Evidência
Aplicada numa cópia limpa do `origin/main` (8d097152): `git apply --check` passa; suíte da Alexandria passa; suíte do painel tem 1 falha que também existe sem o patch (`test_sdd_painel`).
