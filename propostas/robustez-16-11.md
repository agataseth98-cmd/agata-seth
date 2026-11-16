# Robustez 16/11: aplicar espera os checks e a compilação Rust pode ser pulada (`robustez-16-11`)

Classe: Comportamento (muda scripts; sem canon).

Proposta P-8 de `robustez-16-11`. Diff: `propostas/robustez-16-11.diff` (7 arquivos, 246 linhas inseridas, 16 removidas; sha256 `7e219c8bd5e3184fd21f2b8ec20367bc5d0ec3e7479ce2c7ea5ca85d953345f0`). Base: `origin/main` (9e4f40e0).

Pedido desta sessão (894c2006, 16/11/2026), em duas correções num só lote, com uma assinatura.

Porquê:
- A Máquina caiu às 08:28 de 16/11/2026 enquanto compilava Rust (relato do pedido; não medido aqui). Por isso nada foi compilado nesta proposta.
- A aplicação do PR #1004 saiu com exit 1 sem juntar. O log diz `CI não passou` com `CodeQL: skipping` e `Analyze (rust): pending`. A decisão foi tomada antes de o check de rust terminar, e `skipping` foi tratado como falha.

O que muda:

A) `scripts/equipe/aplicar.py`. A decisão sobre os checks sai do laço aninhado e vira duas funções puras e testáveis:
1. `veredito_checks(cs)` devolve `esperar`, `juntar` ou `recusar`. Espera enquanto houver check `pending`, obrigatório ausente ou nenhum check. Junta só sem falha, com `fiscal-p8` e `suite-adversarial` em `pass` e pelo menos um `pass`. `skipping` e `neutral` não bloqueiam e não contam como sucesso. Qualquer outro bucket é falha (falha fechada).
2. `esperar_ci(...)` faz a leitura (`ler_checks`, com `gh pr checks`) até o veredito deixar de ser `esperar`, com o mesmo prazo de 25 min.
3. `CodeQL` sai da lista de obrigatórios. Se o CodeQL falhar, o bucket `fail` recusa do mesmo jeito.

B) Compilação Rust:
1. `scripts/instalar_egress_rust.sh` compila com `CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}" nice -n 15 cargo build --release --locked`. Pula a compilação quando `scripts/egress_em_dia.py` diz que está em dia. A instalação roda sempre.
2. `scripts/testar_egress_rust.py` compila com `nice -n 15` e `CARGO_BUILD_JOBS` (padrão 2). Pula a compilação se estiver em dia. O novo `--sem-compilar` nunca compila: usa o binário que existe e falha se faltar.
3. `scripts/egress_em_dia.py` (novo). Em dia = `target/release/egress` e `target/release/egress-socks5` existem e têm mtime estritamente maior que todo arquivo de `src/` (recursivo) e todo `Cargo.*`. `tests/` não entra, porque `cargo build --release` não compila `tests/`. Só lê mtime.
4. `scripts/testar_egress_em_dia.py` (novo). 11 casos com arquivos temporários e mtimes fixos. Não compila nada.
5. `scripts/ci_sdd_local.sh` ganha uma linha para o teste novo (passo "egress: critério de em dia").

Medido em 16/11/2026 (worktree a partir de `origin/main`; nenhum `cargo` rodou):
- `python3 -I scripts/equipe/testar_auxiliares.py`: 25/25 antes; 40/40 com a correção A (15 casos novos, com `gh` falso: a saída do #1004, `fail` com check pendente, obrigatório `skipping`, bucket desconhecido, obrigatório ausente, saída ilegível, lista vazia, `ler_checks`, `veredito_checks`).
- Replay do estado exato da linha de log do #1004, só em Python: a lógica antiga decide na primeira leitura (rust ainda `pending`) e devolve não juntar. A nova devolve `esperar` e, quando rust passa, `juntar`.
- `python3 -I scripts/testar_egress_em_dia.py`: 11/11.
- `python3 -I scripts/egress_em_dia.py redesign/rust/egress` (sem `target/`): sai 1 com `falta binário: egress, egress-socks5`.
- `python3 scripts/testar_egress_rust.py --sem-compilar` (sem binário): `FALHA`, saída 1, sem compilar.
- `bash -n` em `scripts/instalar_egress_rust.sh` e `scripts/ci_sdd_local.sh`: sem erro.
- `PYTEST=/home/orusoua/.local/share/agata-pytest/bin/pytest bash scripts/ci_sdd_local.sh`: `CI LOCAL: TUDO OK` (59 passos OK; pytest 9.2.0). Nenhum passo do CI chama cargo (checado com grep antes de rodar).
- Cópia descartável de `origin/main` (`git archive`), com `git apply --check` e `git apply` do `.diff`: 40/40, 11/11, `bash -n` OK e `--sem-compilar` com saída 1.

Não medido:
- A compilação de verdade (`cargo build` com `nice` e `CARGO_BUILD_JOBS`) e o efeito na carga da Máquina. Proibido nesta sessão após a queda.
- O caminho "pulada porque está em dia" com binários reais em `target/release`.
- A aplicação real contra o GitHub com a nova espera (os testes usam `gh` falso).
- Se um alerta do CodeQL aparece como `skipping` ou como `fail` no GitHub. Com `skipping`, `aplicar.py` não bloqueia por alerta de CodeQL. Isto é um risco residual: a regra do pedido aceita `skipping`, e o alerta de CodeQL alto deixou de ser barreira para a aplicação. Dono: Humano, para decidir se volta a exigir o CodeQL.
- O CI do PR no GitHub: fica no registro do PR (`headSha`).

Captura de tela: não se aplica (sem interface).

Apetite (R2, medição): 7 arquivos, 246 linhas inseridas, 16 removidas (`git diff --stat`). Horas de agente: não medido.

Aplicação: só depois da assinatura do Humano (`bash scripts/aprovar.sh robustez-16-11`). Esta PR só abre a proposta com o `.diff` e este registro. O `main` não muda com ela.

Reversão: `git revert` do commit de aplicação, quando houver. Até lá, nada muda no código.

Definição de pronto (R3):
- [x] CI local com `CI LOCAL: TUDO OK` (saída acima)
- [ ] run verde no GitHub no `headSha` do PR (fica no registro do PR)
- [x] captura de tela: não se aplica
- [x] sem emoji
- [x] testes medidos, o que não foi medido e a reversão (acima)
- [x] nenhuma falha pré-existente: o CI local não teve falha
- [x] texto de MEMÓRIAS: não se aplica (esta proposta não entra com entrada de MEMÓRIAS)
