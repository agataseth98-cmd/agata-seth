# Proposta lote3 — processo de lote, time de inovação e correções da revisão (v3)

**Nome para assinatura:** `lote3-processo-20261106`
**Substitui:** `lote2b-processo-20261106` (assinada, mas o diff trazia registros e blocos de âncora, e não aplica no main). A lote2b não deve ser aplicada. Ver MEMÓRIAS (967).

## Diff
Só código: skills, agentes em `.claude/agents/`, workflow `sdd.yml`, `scripts/ci_sdd_local.sh`, índice de ferramentas (regenerado), painel (servidor, frentes, chat), spec do painel, Conselho e Rust egress (camada 2). Nenhum arquivo de registro (MEMÓRIAS, ONDE_ESTAMOS, âncoras, propostas) entra no diff.

## Mudanças em relação à lote2b
- D3 no Conselho: o aviso de cota compartilhada sai antes da primeira chamada (decisão do Humano, 06/11).
- Rust egress camada 2: `seguir_redirects_com_ips` devolve, por salto, os IPs validados para conexão pinada (correção de DNS rebinding apontada pelo Codex).
- Workflow sdd.yml: o filtro de paths inclui as pastas confiabilidade, rotas e mvp_autoaprimoramento.
- Skill agata-processo-lote: restauração de gerados só depois de conferir o diff; parada explícita na segunda verificação P-8; lição do diff com registro.

## Evidência
- `git apply --check` do diff passa em cópia limpa do `origin/main`.
- `scripts/ci_sdd_local.sh`: TUDO OK (na árvore de onde o diff saiu; o main mudou só em registros desde então).
- Testes do Conselho: 17 OK. Rust camada 2: 15 OK; camada 1: 19 OK.
- Lint de skills: sem problemas nem avisos.

## Limites
- Os agentes em `.claude/agents/` valem em sessão nova.
- Página de frentes e chat não testados num navegador.
- Rust camada 2: sem NXDOMAIN real, sem IPv6 só-AAAA, sem TLS nem cliente HTTP.

## Assinatura
`bash scripts/aprovar.sh lote3-processo-20261106`
