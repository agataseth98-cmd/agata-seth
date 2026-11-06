# Proposta M2b — Acervo com estados explícitos, egress sem userinfo (v2)

**Nome para assinatura:** `m2b-acervo-egress-20261106`
**Substitui:** `m2-acervo-egress-20261106` (PR #911, registro sem assinatura). A v1 não deve ser assinada. Correção é entrada nova: ver MEMÓRIAS (959).

## Mudança
- `redesign/alexandria/cadastro.py`: `listar_com_falhas()` devolve cadastros legíveis e a contagem de ilegíveis; `listar()` continua igual (wrapper).
- `redesign/painel_operacional/nova_versao_painel.py`: `acervo_listar` devolve `estado` e `ilegiveis`; em erro, `_estado_acervo` devolve `estado: "erro"`.
- `redesign/painel_operacional/nova_versao.js`: estados da tabela abaixo; KPIs ocultos em erro; texto fixo, sem nome de exceção.
- `scripts/politica_egress.py`: URL com `@` no endereço (usuário ou senha) é recusada antes do DNS.
- Testes: `redesign/alexandria/tests/test_egress_userinfo.py` (novo; DNS simulado no caso sem userinfo) e casos `ok`, `vazio`, `parcial`, `erro` e regressão de `listar()` em `test_nova_versao_painel.py`.

## Estados do Acervo (precedência: erro > parcial > vazio > ok)

| Estado | Condição | Título | Mensagem vazia | Indicadores (KPIs) |
|---|---|---|---|---|
| ok | ilegíveis = 0 e há fontes | "N fontes · só as revisadas…" | oculta | visíveis |
| vazio | ilegíveis = 0 e não há fontes | "0 fontes · só as revisadas…" | "Nenhuma fonte ainda." | visíveis, com zeros |
| parcial | ilegíveis > 0 | "N fontes · K registro(s) ilegível(is) ficaram de fora" | se N = 0: "Nenhuma fonte legível · K registro(s) ilegível(is) ficaram de fora." | visíveis |
| erro | exceção ao ler o acervo | "Acervo indisponível agora" | "Não foi possível ler o acervo. Nada foi alterado; tente de novo." | ocultos |

## Fora desta proposta
- Allowlist por destinatário (decisão do Humano, D1 do Experimento 2).
- Registro de nome de arquivo ilegível em log (melhoria, não bloqueia).
- Rótulo "SOMENTE LEITURA" (não decidido).
- Teste de renderização do JS: não há navegador no CI; a parte JS fica sem teste automático e a verificação é só de sintaxe (`node --check`).

## Evidência
- `git apply --check` passa em cópia limpa do `origin/main` e o patch aplica.
- Suíte da Alexandria: todos os arquivos passam.
- Suíte do painel: 84 testes; 1 falha (`test_sdd_painel`, projeto externo), que também ocorre no `origin/main` sem o patch.
- Revisão: parecer de três revisores locais (simplificador, operador, implementador), Conselho Remoto (Gemini, Ministral) e Seth; achados descartados e motivos na conciliação v2 (Experimento 2, seção 9).
