# Proposta lote4-processo-20261106 — substitui a lote3 (não assinada)

**Nome para assinatura:** `lote4-processo-20261106`
**Substitui:** `lote3-processo-20261106` (não assinada). Não assinar a lote3: o aviso D3 dela só saía no retorno; nesta, sai em stderr antes da primeira chamada.
**Base:** `origin/main` (ba42a429). O diff aplica limpo nessa base.

## Conteúdo (só código; o código entra só dentro do .diff)
- **Conselho (`redesign/nova_versao/conselho.py`):** aviso D3 em stderr antes da primeira chamada. Teste de ordem: falha sem a emissão, passa com ela (mutação verificada).
- **Rust egress (`redesign/rust/egress/`):** multicast bloqueado em IPv4 (224.0.0.0/4) e IPv6 (ff00::/8), por decisão do Humano (06/11). Motivo: "reservado". Teste de paridade ajustado; divergência deliberada do `is_global` do Python. `seguir_redirects` documentada como não-guarda de conexão (DNS rebinding); a guarda é `seguir_redirects_com_ips`.
- **Skill de processo (`.agents/skills/agata-processo-lote/SKILL.md`):** 24 correções de revisão independente. Destaques: apagar só com ordem explícita; instalação manual exige ordem; falha pré-existente registrada; após merge de main, repetir `p8_verificar`; diff com `grep '^diff --git'` obrigatório; check vermelho = não junta.
- **Portões mecanizados (`scripts/portao_lote.py`):** G1 só código; G2 aplica no `origin/main`; G3 time no main ou criado pelo diff; G4 PYTEST com versão; G5 checks obrigatórios (`suite-adversarial`, `fiscal-p8`, `CodeQL`) com SUCCESS no head do PR (com `--pr`); G6 APROVADO fora do commit. Selftest 11/11.
- **Resto:** painel de frentes e chat, Rust camada 2, CI local, índice de ferramentas regenerado (419 peças).

## Evidência
- `git apply --check` passa num checkout limpo do `origin/main` (G2).
- `scripts/ci_sdd_local.sh`: TUDO OK, depois de reindexar as ferramentas.
- Testes do Conselho: 18 OK. Rust: 15 (camada 2) + 19 (paridade) OK, com caso IPv6 de multicast.
- Lint das skills: sem problemas nem avisos na skill de processo.
- Portões: G1, G2, G3, G4, G6 PASS; G5 aguarda o run do commit do PR.

## Canon no commit de proposta
Os cinco arquivos de canon (`REGRAS.md`, `PROJETO.md`, `PROMPT_CARREGAMENTO.md`, `MEMÓRIAS.md`, `.hidrata.md`) entram no commit só com os blocos `ANCORA-SHA` regenerados pelo pre-commit. Nenhum texto de canon muda. Declarado aqui como exceção (a) da Regra 2 da skill.

## Limites (não medido)
- O time `agata-*` (em `.claude/agents/`) só fica ativo depois de aplicado e de uma sessão nova.
- O aviso D3 é visível só se quem convoca mantiver o stderr; o retorno também traz o aviso.
- Painel de frentes e chat não testados num navegador.
- Multicast: a divergência do Python está registrada; não há teste de rede real.

## Assinatura
`bash scripts/aprovar.sh lote4-processo-20261106`
