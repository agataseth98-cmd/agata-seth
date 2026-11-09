# Proposta lote2b — processo de lote, time de inovação e correções da revisão (v2)

**Nome para assinatura:** `lote2b-processo-20261106`
**Substitui:** `lote2-processo-20261106` (v1, no main sem assinatura). A v1 não deve ser assinada. Registro em MEMÓRIAS (correção por entrada nova).

## O que entra
- Skill `agata-processo-lote` (`.agents/skills/`), revisada por agente e pelo modelo gpt-6-luna (Codex, somente leitura). Correções aplicadas: restauração de gerados só depois de conferir o diff; condição de parada na segunda verificação P-8; delegação condicionada à sessão.
- Skill `agata-time-inovacao` (`.agents/skills/`): ciclo SDD para propor melhorias (pesquisa, spec, revisão independente, decisão humana, proposta P-8).
- Agentes em `.claude/agents/`: `agata-dev`, `agata-revisor`, `agata-spec`, `agata-ci` e o time de inovação `agata-inov-pesquisa`, `agata-inov-arquiteto`, `agata-inov-critico`. Não reconhecidos na sessão que os criou: valem em sessão nova.
- `scripts/ci_sdd_local.sh`: reproduz o job sdd (passou por completo, nesta versão).
- `.github/workflows/sdd.yml`: filtro de paths inclui as pastas confiabilidade, rotas e mvp_autoaprimoramento (achado do Codex).
- Rust egress, camada 2: `seguir_redirects_com_ips` devolve, por salto, a URL e os IPs validados, para conexão sem nova resolução (correção do achado de DNS rebinding). Dois testes novos: 15 testes na camada 2 e 19 na camada 1, todos passando.
- Página de frentes, chat com stream e regra D3 no Conselho (já no lote 2 v1).
- Índice de ferramentas regenerado (419 peças).

## Decisões que ficam com o Humano
- **D3, ordem do aviso:** o aviso de cota compartilhada sai depois da chamada. A decisão D3 diz "sem teto, com os avisos previstos", sem fixar a ordem. Mantido como está. Melhoria registrada para o time de inovação: aviso antes da chamada com a cota atual.
- **Merge de PR de aplicação:** `AGENTS.md` diz que o PR que aplica código assinado fica com o Humano; as aplicações anteriores (PR 913, 915, 917) foram juntadas pelo agente. Vai ser perguntado.

## Limites
- Página de frentes e chat não testados em navegador.
- Rust camada 2: sem teste de NXDOMAIN real nem de IPv6 que resolve só AAAA; sem TLS nem cliente HTTP.
- OpenCode (P8): instalado e verificado por SHA-256; sem modelo configurado. Não entra neste diff.

## Evidência
- `git apply --check` passa em cópia limpa do `origin/main`.
- `scripts/ci_sdd_local.sh`: TUDO OK (passo a passo, mesma árvore do diff).
- Lint de skills: sem problemas nem avisos.
- Rust: 15 + 19 testes passando (`cargo test --offline`).

## Assinatura
`bash scripts/aprovar.sh lote2b-processo-20261106`
