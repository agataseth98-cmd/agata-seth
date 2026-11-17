# Atualiza 17/11: auditoria do sistema, listas únicas no painel e telas de operação (`atualiza-17-11`)

Classe: Comportamento (painel, scripts de controle, config).

Proposta P-8 de `atualiza-17-11`. Diff: `propostas/atualiza-17-11.diff` (29 arquivos, 4376 linhas). Base: `origin/main` (ac08bf4f). O diff não traz registro, derivados nem `ONDE_ESTAMOS.md`; esses entram no PR de proposta, fora do diff assinado.

Decisão do Humano (17/11/2026, 08:24): "inventarie, audite e atualize o sistema e depois aplique tudo que vc sugeriu para o painel a luz do que for encontrado depois atualize o agata-conceito-16-11-2026, na área de trabalho para refletir o estado atual."

## O que muda

1. Painel, listas únicas: "O que posso fazer" e "Integrações" viram uma lista em Sistema > Integrações; provedores vêm de uma fonte (catálogo do Conselho) numa tabela em Conexões, com tarifa; timers e tarefas só em Manutenção; lacunas só em Qualidade; recuperação num indicador com as duas leituras rotuladas e trava comum.
2. Telas novas de leitura: Equipe, Backup e Saída de rede (Sistema), Perímetro e CI (Qualidade). Rotas GET novas que leem arquivos locais, sem parâmetro do cliente; nunca executam perímetro, CI, equipe.py ou restic. Resultado com mais de 24 h aparece como atenção, com a idade.
3. Perímetro e CI local gravam o último resultado em `~/.cache/agata/perimetro/ultimo.json` e `~/.cache/agata/ci/ultimo.json`, sem mudar veredito nem código de saída.
4. `/api/status` deixa de pôr unidade ausente na lista de sem leitura.
5. Sistema: perfil da Capivara regenerado (mesmos 11 modelos; só datas); primeira linha dos README históricos do chat antigo e do Goose; descrição em `config/portas-de-entrada.txt`; motivo na lista do teste sem-Goose; skill do painel (`.agents/skills/agata-painel/SKILL.md`) com as rotas novas; o script do CI local deixa de alterar o shell de quem o carrega com `source`.

Feito fora do repositório na mesma auditoria (só registro): snapshots restic dos dois modelos Whisper (a4a91ded, 7ffe63d5) e P-12 OK; 107 worktrees antigas removidas por ordem do Humano, com patches e não rastreados guardados em `~/agata-arquivo/worktrees-removidas-17-11/`.

Achados que ficam abertos (fora deste diff):
- divergência de texto entre a spec-mãe e a spec de conexões; o verificador de sincronia recusa mudança só de texto em spec; mudar o verificador foi barrado pelo classificador de permissões e fica para decisão do Humano;
- a entrada (1003) duplicada em `MEMÓRIAS.md` (append-only);
- codex ausente no arquivo da equipe e presente na sessão;
- o painel dispara `POST /api/abrir` ao entrar em Conselho (comportamento anterior a este pacote);
- o registro de cobertura do backup (`p12-cobertura.json`) não tem escritor no repositório.

## Medido (17/11/2026)

- CI local (`scripts/ci_sdd_local.sh`, com `PYTEST` do cache do uv, `pytest 9.2.0` confirmado por `--version` antes da rodada): última linha `CI LOCAL: TUDO OK`; 88 linhas `OK`, 0 `FALHA`; rc=0. Log: `/home/orusoua/agata-arquivo/atualiza-17-11/ci-local.log`. Registro do script: `~/.cache/agata/ci/ultimo.json` (head `ac08bf4f`, 88 ok, 0 falha).
- Cópia limpa de `origin/main` (worktree `check-atualiza-17-11`): `git apply --check` retorna APLICA; `git apply` roda sem erro.
- Na cópia limpa, com o diff aplicado:
  - `scripts/gate_spec_sync.py`: rc=0; 16 componentes, 0 falha; 1 aviso (`alexandria`, dívida conhecida: 5 critérios do acceptance.json sem linha no spec.md).
  - `redesign/sdd_flow/anchor.py . redesign/painel_operacional`: `ANCHOR: OK`, rc=0.
  - `scripts/testar_sem_goose_ativo.py`: `OK`, rc=0.
  - `scripts/testar_perimetro.sh`: `SUITE OK -- 62 caso(s), 0 falha(s)`, rc=0.
  - Suíte do painel (`unittest discover`, 729 testes): `OK`, rc=0.
- Relatado pelo coordenador, não reconferido por mim: `scripts/perimetro.sh` OK (22 OK, 2 SKIP, 2 PARCIAL, 0 FALHA); 0 de 40 combinações de largura e seção com rolagem horizontal; revisão independente sem bloqueio, com correções feitas.

## Não medido

- Leitor de tela.
- Toque.
- Contraste das classes novas.
- Navegador real na porta 20146 (só depois de aplicar e reiniciar o painel).
- Horas de agente: não informado pelo coordenador.

## Apetite

Os caminhos do lote (29 arquivos, 4376 linhas no diff). Horas de agente: não informado pelo coordenador.

## Reversão

`git apply -R propostas/aplicadas/atualiza-17-11.diff` numa worktree, por proposta; depois reiniciar `painel-operacional.service`. Os arquivos `~/.cache/agata/{perimetro,ci}/ultimo.json` podem ficar.

## Comando de assinatura

Depois do merge deste PR, no terminal, sem `!`:

bash scripts/aprovar.sh atualiza-17-11

## Modelos

Claude Opus 5.5 coordenou; agentes Claude Haiku 5.5 auditaram, implementaram e revisaram.

## Definição de pronto (R3)

- [x] CI local com `CI LOCAL: TUDO OK` (log acima)
- [ ] run verde no GitHub no `headSha` do PR (fica no registro do PR)
- [x] captura de tela: pastas `fotos`, `fotos-antes-rodada2` e `fotos-interacao` em `~/agata-arquivo/atualiza-17-11/` (existência conferida por listagem; as imagens não foram reabertas)
- [x] sem emoji no `.md` (conferido com grep depois de escrever)
- [x] testes medidos, o que não foi medido e a reversão (acima)
- [x] nenhuma falha pré-existente sem dono e data (nenhuma falha no CI local nem na cópia limpa)
- [x] texto da entrada de MEMÓRIAS sem citação `caminho:número` (conferido com grep depois de escrever)
