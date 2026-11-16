# Painel funcional 16/11: painel sem o chat antigo, estados honestos e estilo consolidado (`painel-funcional-16-11`)

Classe: Comportamento (código e spec do painel em `redesign/painel_operacional/`; sem canon).

Proposta P-8 de `painel-funcional-16-11`. Diff: `propostas/painel-funcional-16-11.diff` (18 arquivos, 1624 linhas inseridas, 2242 removidas; sha256 `d1ca2f716e058e109f312458474c850efe8b235809467fbadac928cbae828b5c`). Base: `origin/main` (d7f27ccf).

Decisão do Humano (16/11/2026, 10:46): eleve o painel ao estado 100% funcional e estado da arte de design.

O que muda:
1. O chat antigo sai do painel. A sonda da porta antiga vira leitura do gateway da Seth. O alvo antigo de `/api/abrir` é recusado.
2. `/api/status` traz as fontes sem leitura.
3. Unidade inexistente no escopo do usuário vira estado próprio, distinto de parada e de sem leitura.
4. Falha na leitura dos modelos locais deixa de virar lista vazia.
5. O painel passa a observar a si mesmo e a vigia do Claude.
6. Cache curto, com trava por rota, em capacidades e lacunas.
7. Página sem texto fixo de estado; Panorama sem repetição; Integrações com leitura por unidade; estados vazios; cabeçalho no Conselho; atalhos de vault num lugar só.
8. Estilo: 40 tokens de cor semânticos por tema (`--luz-*`) no lugar dos nomeados por valor; 9 tamanhos de fonte (`--fs-1` a `--fs-9`); 5 raios (`--r-1` a `--r-4` e `--r-pill`); conteúdo alinhado no topo; Operator Console na mesma linguagem; celular com busca inteira e navegação em faixa.
9. Spec com oito seções e 20 critérios de aceite novos (129 para 149).

Medido em 16/11/2026 (worktree a partir de `origin/main`):
- CI local: `CI LOCAL: TUDO OK` (59 passos OK, nenhum FALHA; pytest 9.2.0). Log: `/home/orusoua/agata-arquivo/auditoria-conceito-16-11/painel/ci-local-2.log`.
- Suíte do painel, pytest 9.2.0 sobre `redesign/painel_operacional`: `539 passed, 326 subtests passed in 33.93s`. Log: `/home/orusoua/agata-arquivo/auditoria-conceito-16-11/painel/pytest-painel-2.log`.
- Cópia limpa de `origin/main`: `git apply --check` retorna APLICA; `git apply` do `.diff` deixa a árvore do painel igual à da worktree (`diff -rq` sem diferença).
- Critérios de aceite: 129 em `origin/main`, 149 na worktree (`spec/acceptance.json`).
- Tokens em `prototipo.css`: 40 `--luz-*` distintos, 9 `--fs-*`, 5 raios.
- Fotos antes e depois em `/home/orusoua/agata-arquivo/auditoria-conceito-16-11/painel/`: pasta `antes` (9 arquivos) e pasta `depois` (16 arquivos).

Não medido:
- Contraste mínimo de 4,85:1: valor informado, sem arquivo de medição encontrado nas pastas lidas. Não conta como medido.
- Tema claro em tela; cliques, hover e foco; aba Integrações em foto; navegador real na porta 20146 (só depois de aplicar e reiniciar).

Limites e pendências para o lote seguinte:
- Listas repetidas: capacidades e integrações; provedores em quatro lugares; recuperação com dois caminhos.
- Telas ausentes: equipe, perímetro, CI, backup e saída de rede em Rust.
- Quatro tokens `--luz-*` ainda nomeados por cor. Número a confirmar: a lista de `prototipo.css` mostra mais nomes de cor (blue, gold, green, lime, orange, rose, teal, violet e outros).
- No celular, os atalhos Obsidian e OmniRoute da lateral ficam ocultos.

Apetite (R2, medição): 18 arquivos (`git diff --cached --stat`: 1624 inserções, 2242 remoções). O relato falava em 19: o 19º é `redesign/nova_versao/spec/evidence.json`, gerado pelo ciclo e fora do lote. Horas de agente: cerca de 3, informado, não medido.

Captura de tela: fotos antes e depois listadas acima.

Aplicação: só depois da assinatura do Humano (`bash scripts/aprovar.sh painel-funcional-16-11`). Esta PR só abre a proposta com o `.diff` e este registro. O `main` não muda com ela.

Depois de aplicar: reiniciar `painel-operacional.service` (`systemctl --user restart painel-operacional.service`) e medir a página real.

Reversão: `git apply -R propostas/aplicadas/painel-funcional-16-11.diff` em worktree, por proposta, e `systemctl --user restart painel-operacional.service`.

Comando de assinatura: bash scripts/aprovar.sh painel-funcional-16-11

Modelos: Claude Fable 5.2 coordenou; agentes Claude Haiku 5.5 implementaram, rodaram o CI e revisaram (designação do coordenador).

Definição de pronto (R3):
- [x] CI local com `CI LOCAL: TUDO OK` (saída acima)
- [ ] run verde no GitHub no `headSha` do PR (fica no registro do PR)
- [x] captura de tela: fotos antes e depois
- [x] sem emoji
- [x] testes medidos, o que não foi medido e a reversão (acima)
- [x] nenhuma falha pré-existente: o CI local não teve falha
- [x] texto de MEMÓRIAS sem citação `caminho:número` (conferido com grep depois de escrever)
