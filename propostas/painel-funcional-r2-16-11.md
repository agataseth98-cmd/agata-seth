# Painel funcional r2 16/11: painel sem o chat antigo, estados honestos e estilo consolidado (`painel-funcional-r2-16-11`)

Classe: Comportamento (código e spec do painel em `redesign/painel_operacional/`, mais uma linha de lista no teste `scripts/testar_sem_goose_ativo.py`; sem canon).

Proposta P-8 de `painel-funcional-r2-16-11`. Diff: `propostas/painel-funcional-r2-16-11.diff` (19 arquivos, 1626 linhas inseridas, 2243 removidas; sha256 `df8ee00f470580f23c5dfcdfe579cc2a47c4b0a964732521c7eb60ebd8e96a54`). Base: `origin/main` (d9239cd4). Substitui `painel-funcional-16-11` (movida para `propostas/superadas/`).

Decisão do Humano (16/11/2026, 10:46): eleve o painel ao estado 100% funcional e estado da arte de design.

## Por que r2

A proposta `painel-funcional-16-11` foi assinada pelo Humano, mas não entrou no `main`. No PR de aplicação #1008, o check obrigatório `suite-adversarial` falhou no teste `scripts/testar_sem_goose_ativo.py`. Reproduzi a falha na worktree antes de mexer: duas falhas. A lista de exceções ainda tinha uma entrada para `prototipo.html`, que este lote tirou da página. E dois arquivos do lote passaram a citar a palavra Goose sem estar na lista: `spec/acceptance.json` e `test_painel_unificado.py`, que citam a palavra porque afirmam que ela não está na página. Como `scripts/*` é protegido, a correção só pode entrar junto com o código do lote. Por isso este pacote é uma proposta nova, com uma só assinatura.

O código do painel é idêntico ao já assinado. Prova: as duas pastas `redesign/painel_operacional/` (70 arquivos cada), aplicadas em cópias limpas de `origin/main`, dão `diff -rq` sem diferença. Os 18 blocos do painel dos dois `.diff` são iguais byte a byte. A única diferença entre os pacotes é `scripts/testar_sem_goose_ativo.py`, com três mudanças na lista de exceções:
1. sai a entrada de `redesign/painel_operacional/prototipo.html` (a palavra saiu da página: contagem 1 vira 0);
2. entra `redesign/painel_operacional/spec/acceptance.json`, com contagem 2;
3. entra `redesign/painel_operacional/test_painel_unificado.py`, com contagem 2.

Os outros arquivos do lote foram conferidos: `README.md` e `spec/spec.md` são `.md`, fora do escopo do teste; `test_painel.py` tem zero ocorrências.

Lição: o CI local (`scripts/ci_sdd_local.sh`) não roda a suíte adversarial. Nem ele nem `sdd.yml` citam `testar_perimetro.sh` ou `testar_sem_goose_ativo.py`. Por isso o erro só apareceu no GitHub. Pendência com dono (Claude): uma proposta própria para o CI local incluir essa suíte. Data: a definir pelo Humano.

## Medido em 16/11/2026 (worktree `proposta/painel-funcional-r2-16-11`, a partir de `origin/main` d9239cd4)

- Teste da lista, antes da correção: `python3 scripts/testar_sem_goose_ativo.py -v`: 6 testes, 2 falhas (`test_excecoes_batem_com_a_contagem_atual` em `prototipo.html`; `test_nenhuma_referencia_ativa_fora_das_excecoes` com `acceptance.json` e `test_painel_unificado.py`), rc=1.
- Teste da lista, depois da correção: 6 testes OK, rc=0.
- Suíte adversarial, o que `.github/workflows/perimetro.yml` roda, na worktree e no mesmo ambiente da CI (sem variável de proxy):
  - `bash scripts/testar_perimetro.sh`: `SUITE OK -- 61 caso(s), 0 falha(s)`.
  - 28 testes e selftests Python do job, todos com rc=0 (auditoria do turno, gateway, Conselho, pedidos, roteamento, P-8, painel_estado, emoji, cofre, expurgo, golden, autodev, janela, equipe, memória e escriba, e o teste da lista).
  - Outros testes com lista de exceções ou de ausência: `scripts/gate_spec_sync.py` (selftest 12/12; gate com 0 falha e 1 aviso de `alexandria`, que não é deste lote, rc=0); `scripts/testar_tira_librechat.py` OK.
- CI local: `CI LOCAL: TUDO OK` (59 OK, 0 FALHA; pytest 9.2.0). Log: `/home/orusoua/agata-arquivo/auditoria-conceito-16-11/painel/ci-local-r2.log`.
- Cópia limpa de `origin/main`: `git apply --check` do `.diff` retorna APLICA.
- Tamanho: `git apply --numstat` dá 19 arquivos, 1626 inserções, 2243 remoções. O pacote anterior tinha 18 arquivos, 1624 e 2242. A diferença é só o script.
- Critérios de aceite: 149 em `spec/acceptance.json` (medido na proposta anterior; o código é idêntico).

Não medido:
- Run verde no GitHub no `headSha` do PR novo (ainda não existe no momento da escrita; fica no registro do PR).
- Os selftests e a suíte rodaram na Máquina, não no runner do GitHub.
- A suíte do painel (pytest, 539 passed) foi medida na proposta anterior. Neste pacote o código é o mesmo, e o pytest do painel roda dentro do passo "testes SDD (pytest)" do CI local, sem falha.
- Contraste mínimo de 4,85:1: valor informado, sem arquivo de medição encontrado nas pastas lidas. Não conta como medido.
- Tema claro em tela; cliques, hover e foco; aba Integrações em foto; navegador real na porta 20146 (só depois de aplicar e reiniciar).
- Horas de agente desta rodada: não medidas.

Arquivos gerados pelo ciclo, fora do pacote e sem restauração (sem ordem do Humano): `redesign/nova_versao/spec/evidence.json` (modificado pelo ciclo) e `redesign/sdd_flow/spec/criterion-drift.md` e `evidence.json` (não rastreados).

Apetite (R2, medição): 19 arquivos (`git apply --numstat`: 1626 inserções, 2243 remoções). Horas de agente: não medidas.

Captura de tela: fotos antes e depois da proposta anterior, em `/home/orusoua/agata-arquivo/auditoria-conceito-16-11/painel/` (pastas `antes` e `depois`). Valem para este pacote, porque o código do painel é o mesmo.

Limites e pendências para o lote seguinte:
- Listas repetidas: capacidades e integrações; provedores em quatro lugares; recuperação com dois caminhos.
- Telas ausentes: equipe, perímetro, CI, backup e saída de rede em Rust.
- Quatro tokens `--luz-*` ainda nomeados por cor. Número a confirmar: a lista de `prototipo.css` mostra mais nomes de cor (blue, gold, green, lime, orange, rose, teal, violet e outros).
- No celular, os atalhos Obsidian e OmniRoute da lateral ficam ocultos.
- CI local não roda a suíte adversarial (dono: Claude; data: a definir pelo Humano).

Aplicação: só depois da assinatura do Humano (`bash scripts/aprovar.sh painel-funcional-r2-16-11`). Esta PR só abre a proposta com o `.diff` e este registro. O `main` não muda com ela.

Depois de aplicar: reiniciar `painel-operacional.service` (`systemctl --user restart painel-operacional.service`) e medir a página real.

Reversão: `git apply -R propostas/aplicadas/painel-funcional-r2-16-11.diff` em worktree, por proposta, e `systemctl --user restart painel-operacional.service`.

Comando de assinatura: bash scripts/aprovar.sh painel-funcional-r2-16-11

Modelos: Claude Fable 5.2 coordenou a proposta anterior; este pacote r2 foi executado por agente Claude Haiku 5.5 (subagente), sob designação do coordenador.

Definição de pronto (R3):
- [x] CI local com `CI LOCAL: TUDO OK` (saída acima)
- [ ] run verde no GitHub no `headSha` do PR (fica no registro do PR)
- [x] captura de tela: fotos antes e depois (da proposta anterior; o código é idêntico)
- [x] sem emoji
- [x] testes medidos, o que não foi medido e a reversão (acima)
- [x] nenhuma falha pré-existente sem dono: a falha da suíte adversarial veio deste lote e foi corrigida aqui; a lacuna do CI local tem dono (Claude)
- [x] texto de MEMÓRIAS sem citação `caminho:número` (conferido com grep depois de escrever)
