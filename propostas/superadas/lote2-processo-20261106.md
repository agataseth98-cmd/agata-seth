# Proposta lote2 — processo de lote, agentes especializados e página de frentes

**Nome para assinatura:** `lote2-processo-20261106`
**Escopo:** um diff único (1118 linhas), uma assinatura.

## O que entra
- **Skill `agata-processo-lote`** (`.agents/skills/`): o processo de lote do começo ao fim, com as armadilhas já pagas e um diário de erros e acertos. Revisada por agente independente (13 achados aplicados).
- **Agentes especializados** (`.claude/agents/`): `agata-dev` (implementação com arquivos próprios e testes), `agata-revisor` (somente leitura), `agata-spec` (spec SDD e âncora), `agata-ci` (CI local e diagnóstico). Só valem para sessões que reiniciarem: nesta sessão o tipo não foi reconhecido.
- **CI local** (`scripts/ci_sdd_local.sh`): reproduz os passos do job `sdd`. Corrige o PATH do pytest. Passou por completo nesta worktree.
- **Workflow `sdd.yml`**: as pastas de teste novas (confiabilidade, rotas, mvp_autoaprimoramento) entram no pytest do CI.
- **Página de frentes** (`/frentes`, `/api/frentes`, somente leitura) em `server.py`, `frentes.html`, `frentes.js`, `test_frentes.py`.
- **Chat com stream** no `prototipo.js` (consome `/api/seth/chat/stream`, com fallback), `test_chat_ui.py`.
- **Conselho com regra D3** (`conselho.py`): cota gratuita compartilhada sem teto gera aviso, não recusa.
- **Rust egress, camada 2** (`redesign/rust/egress/src/camada2.rs`): resolução DNS com classificação de todos os IPs, validação de redirecionamento, limite de 10 saltos.
- **Spec do painel** (Código): inclui os arquivos novos.
- **Índice de ferramentas** regenerado (`ferramentas/indice.json`, `INDICE.md`).

## Limites declarados
- Agentes de `.claude/agents/`: não reconhecidos na sessão que os criou; testar em sessão nova.
- Página de frentes e chat: não testados num navegador real (testes são estáticos e do servidor).
- Camada 2 do Rust: sem teste de NXDOMAIN real nem de IPv6 que resolve só AAAA; sem TLS nem cliente HTTP.
- OpenCode (P8): instalado e verificado (SHA-256 do pacote oficial), mas sem modelo configurado; o piloto não produziu resposta. Não entra neste diff.

## Evidência
- `git apply --check` passa em cópia limpa do `origin/main`.
- `scripts/ci_sdd_local.sh` nesta worktree: TUDO OK.
- Lint de skills: sem problemas nem avisos.

## Assinatura
`bash scripts/aprovar.sh lote2-processo-20261106`
