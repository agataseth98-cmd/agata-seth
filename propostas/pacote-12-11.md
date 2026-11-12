# Pacote 12/11: seis propostas e a nota da História numa assinatura (`pacote-12-11`)

Proposta P-8 de `pacote-12-11`. Diff: `propostas/pacote-12-11.diff` (25 arquivos de código: 22 alterados e 3 novos; sha256 `f7adcaa35cfdc53f497ce95485df6b22b13a1c04c6378568d551d76f9234df5e`). Base: `origin/main` `3f1e9055` (já tem o PR #973, pacote-11-11 aplicado, e o PR #974, chat-voz-11-11, só como proposta). Assinatura do Humano, uma vez, depois do merge deste PR de proposta.

Pedido do Humano em 12/11/2026, 08:45: "ok a todas", com a montagem do pacote-12-11 com uma só assinatura. Nome final: `pacote-12-11`, pela data do pacote. Regra correspondente na skill: "Pacote de assinatura (Humano, 11/11)", em `.agents/skills/agata-processo-lote/SKILL.md`.

Classe (P4): Canon e Comportamento, em mistura. Canon: `AGENTS.md`, `PROJETO.md`, skills e `historia/`. Comportamento: `redesign/systemd/*`, `scripts/perimetro.sh`, `scripts/equipe/*`, `scripts/p8_verificar.sh`, `redesign/router/auditoria_turno.py`, `.github/workflows/perimetro.yml`. Veja a decisão 1 abaixo sobre a falta de spec.

## Em resumo (para o Humano)

- Junta seis propostas que mexiam nos mesmos arquivos de atalho, canon e skill, mais a nota de canonização do Texto 1 da História, numa só assinatura.
- Tira o LibreChat dos atalhos e do P-9; tira o Ollama do boot no canon; põe o OpenCode no lugar do Goose no terminal (agente, docs e skills); faz `--verificar` deixar um rastro de metadado; e acrescenta à skill de processo só as lições que não repetem o que ela já diz (12 entraram, 3 caíram por repetição).
- Duas partes foram refeitas, porque o `AGENTS.md` mudou desde a proposta: docs-opencode e verificar-rastro. A regra primordial de voz do pacote-11-11 foi preservada.
- Testado inteiro sobre `origin/main` `3f1e9055`: unittest do painel com 454 testes OK; `scripts/ci_sdd_local.sh` com `CI LOCAL: TUDO OK` (35 passos); gate de spec sem falha; lint de skills sem problema.
- Assinar, depois do merge: `bash scripts/aprovar.sh pacote-12-11 "<motivo>"`.
- Três decisões do Humano antes ou depois da assinatura estão listadas adiante (spec das partes de comportamento, testes do LibreChat fora do CI, aba História lendo o frontmatter).

## Ordem de aplicação

1. `tira-librechat-07-11`: `redesign/systemd/seth`, `redesign/systemd/seth-parar`, `scripts/perimetro.sh`, `scripts/testar_cobertura_servicos.py` e `scripts/testar_tira_librechat.py` (novo). `git apply` limpo, sobre `9b27c1b4` e sobre `3f1e9055`.
2. `canon-boot-07-11`: `PROJETO.md` e `scripts/perimetro.sh`. `git apply` limpo depois da 1.
3. `agente-opencode-07-11`: `.github/workflows/perimetro.yml`, `redesign/systemd/seth-agente`, `scripts/equipe/equipe.py`, `scripts/equipe/inicio.sh`, `scripts/p8_verificar.sh` e `scripts/testar_sem_goose_ativo.py` (novo). `git apply` limpo.
4. `docs-opencode-07-11` (refeita, ver conflitos): `AGENTS.md` e `PROJETO.md` à mão; o resto aplicou com `git apply --exclude`.
5. `verificar-rastro-20261106` (refeita em `AGENTS.md`): `redesign/router/auditoria_turno.py` aplicou limpo; `AGENTS.md` à mão.
6. `skill-processo-lessons-07-11` (refeita por item): `.agents/skills/agata-processo-lote/SKILL.md`, seção "Lições medidas em 07/11/2026", ao fim da skill.
7. Nota de canonização do Texto 1: `historia/registro-de-canonizacao.md` (novo, na raiz de `historia/`) e uma linha em `historia/README.md`. O texto `historia/tomo-01/01-a-casa-propria-da-conversa.md` não foi tocado.

Arquivos de código do pacote, sem contar os de registro: `.agents/skills/agata-aplicar-proposta/SKILL.md`, `.agents/skills/agata-conversar-com-seth/SKILL.md`, `.agents/skills/agata-fluxo-equipe/SKILL.md`, `.agents/skills/agata-processo-lote/SKILL.md`, `.github/workflows/perimetro.yml`, `AGENTS.md`, `PROJETO.md`, `config/modelos-gratuitos.md`, `ferramentas/indice.json`, `historia/README.md`, `historia/registro-de-canonizacao.md`, `redesign/librechat/README.md`, `redesign/mcp/README.md`, `redesign/router/auditoria_turno.py`, `redesign/router/goose.md`, `redesign/systemd/seth`, `redesign/systemd/seth-agente`, `redesign/systemd/seth-parar`, `scripts/equipe/equipe.py`, `scripts/equipe/inicio.sh`, `scripts/p8_verificar.sh`, `scripts/perimetro.sh`, `scripts/testar_cobertura_servicos.py`, `scripts/testar_sem_goose_ativo.py`, `scripts/testar_tira_librechat.py`.

## Conflitos e como foram resolvidos

- **Base nova (`9b27c1b4` para `3f1e9055`).** O PR #974 entrou no `origin/main` depois de a rodada começar. Ele mexe em `MEMÓRIAS.md`, `REGRAS.md`, `PROMPT_CARREGAMENTO.md`, `.hidrata.md`, `INDICE_MEMORIAS*.md` e no bloco de máquina ANCORA-SHA de `PROJETO.md`, e cria `propostas/chat-voz-11-11.*`. Em `PROJETO.md`, a mudança do PR #974 é só o bloco de máquina ANCORA-SHA, que o pacote não toca. O diff foi refeito sobre `3f1e9055` e os testes rodaram de novo.
- **Parte 4, `AGENTS.md` (falhou no contexto).** Refeita à mão sobre o `AGENTS.md` atual: "Cursor, Goose" virou "Cursor, OpenCode"; "LibreChat, Goose, modo de permissão" virou "LibreChat, OpenCode"; "Seth, Goose, Conselho" virou "Seth, OpenCode, Conselho". Na linha da memória comum: "Quem passa pelo `seth_gateway` (Seth) já recebe as duas; o OpenCode entra nesse caminho só depois de medido. Quem não passa (Claude Code, Codex, Gemini, OpenCode e outros na CLI)". A linha da voz primordial do pacote-11-11 ("fale" ou "leia para eu compreender") não foi tocada.
- **Parte 4, `PROJETO.md` (falhou depois da 2).** `git apply --reject` aplicou dois trechos (o bullet "Seth (conversa e agente)" e o bullet "Todos os modelos (686)") e rejeitou dois. Os dois rejeitados foram feitos à mão: a linha "Frentes" (que já trazia o "em substituição" do LibreChat, de 07/11) e o bloco Goose, Portas e Atalhos, que virou OpenCode.
- **Parte 5, `AGENTS.md` (falhou no contexto).** Refeita sobre a mesma linha da memória comum que a parte 4 já tinha alterado: o comando passa a ser `--verificar --cliente <nome> < arquivo`, com a nota de que grava um registro de metadado, sem texto, no log da auditoria.
- **Parte 6 (falhou no contexto).** A skill mudou em 11/11 (seções "Fluxo e pronto" e "Pacote de assinatura"). Refeita por item, como abaixo.
- **Parte 7.** A nota não foi posta em `historia/tomo-01/00-registro-de-canonizacao.md`, como sugeria o briefing. Motivo medido: o painel (`historia_painel.py`) lista como texto todo `NN-titulo.md` dentro de tomo, e o regex `\d{2}-[a-z0-9][a-z0-9-]*` casa `00-registro-de-canonizacao`. O teste `test_historia.py` afirma que a lista de textos do tomo 1 é só `[TEXTO_REAL]`, então quebraria. O registro foi para a raiz de `historia/`, fora dos tomos, que o painel não lê.
- **Painel da História, aba "canônico".** Não foi feito: ligar o painel ao registro não é simples (o `estado` vem do frontmatter, que é append-only, e o painel não lê o registro). Ficou só a nota, como pede o briefing para o caso de não ser simples.

## O que caiu da parte 6 (skill-processo-lessons-07-11)

Comparei item por item com a skill de processo atual (`origin/main` `3f1e9055`). Entraram 12, caíram 3.

Entraram (letras da proposta original): **a** (ler código não é medição; rotular "lido"), **b** (defeito medido se corrige numa proposta, na mesma rodada), **c** (teste de migração e importação sobre cópia com hash), **d** (teste de navegador e HTTP só com GET), **f** (trabalho durável não fica em `/tmp`), **i** (decisão do Humano que só existe em mensagem vira proposta ou registro), **j** (antes de remover serviço ou dado, verificar a cópia), **k** (limiar de corte pela quebra medida), **l** (número sai com rótulo: medido, inferido ou não medido), **m** (perguntas numeradas), **n** (sem sudo; comando ao Humano sem o prefixo `!`), **o** (estado real antes de afirmar, com comando e saída).

Caíram por repetição:
- **e (nunca rm).** A skill já tem a remoção só com ordem do Humano (regra 5), "Nunca `rm -rf`" (armadilha "Arquivos gerados pelo ciclo SDD") e a lista de proibições de git (`rm -rf`, em "Regras de segurança"). Ficou de fora o resíduo "nem `rm -f`, nem em arquivo temporário; use `mv`". Se o Humano quiser essa linha, ela vira item próprio.
- **g (canon não se commita antes da assinatura).** A regra 2 da skill já diz que o P-8 recusa commit direto, e o passo 4 já manda conferir em cópia limpa.
- **h (o pre-commit regrava âncoras e hidratação).** A armadilha "Conflito de âncora" e o passo 10 já dizem isso.

Observações, sem mudar nada: **c** e **j** se sobrepõem (cópia com hash); mantive as duas, e o Humano decide se funde. **k** é regra de medição, não de processo de lote; entrou porque o critério era só não repetir a skill, mas pode ser movida para outro lugar. Os "Achados em regras existentes" da proposta original (por exemplo, a frase "`.agents/` não verificado no P-8", que hoje está verificada em `scripts/perimetro/p08_quarentena.sh`) não foram alterados, porque não são lições.

## Testes medidos

Todos sobre `origin/main` `3f1e9055` com o pacote aplicado na worktree `worktree-agent-ab841c7fb6eb42df2`, branch `proposta/pacote-12-11`:

- Unittest do painel (`cd redesign/painel_operacional && uv run --offline --with pytest python3 -m unittest discover -s . -p "test_*.py"`): 454 testes, OK (15,7 s).
- CI local (`uv run --offline --with pytest bash scripts/ci_sdd_local.sh`): `CI LOCAL: TUDO OK`, 35 passos OK, saída 0. Na base antiga (`9b27c1b4`), a mesma rodada também deu `TUDO OK`.
- Gate de spec (`python3 -I scripts/gate_spec_sync.py`): 12 componentes, 1 aviso (dívida conhecida da alexandria), 0 falha.
- Lint de skills (`python3 redesign/painel_operacional/qualidade_llm.py`): 21 skills, nenhum problema; `agata-processo-lote` com 209 linhas e nenhum aviso.
- `ferramentas/test_ferramentas.py` mais `scripts/testar_tira_librechat.py`: 10 testes OK.
- `scripts/testar_sem_goose_ativo.py -v`: 6 de 6 OK.
- `scripts/testar_cobertura_servicos.py`: `COBERTURA SERVICOS OK -- 11/11`.
- `scripts/testar_p9.sh`: `P-9: OK`.
- `bash -n` em `redesign/systemd/seth`, `seth-parar`, `seth-agente`, `scripts/perimetro.sh`, `scripts/p8_verificar.sh` e `scripts/equipe/inicio.sh`: OK. O YAML de `.github/workflows/perimetro.yml` faz parse.
- `redesign/router/auditoria_turno.py --selftest` (como o workflow chama, sem `-I`): `SELFTEST OK`.
- `ferramentas/ferramentas.py reindexar`: mudou só dois resumos de `ferramentas/indice.json`, Goose para OpenCode, que é o que as skills do pacote dizem. Incluído no diff.
- Diff aplica limpo sobre uma cópia limpa de `origin/main` `3f1e9055` (`git archive`, `git apply --check`).
- Reversão medida na cópia: aplica, `git apply -R --check` OK, reverte, e os três arquivos novos saem.
- Atalhos: `seth` sobe a espinha, o gateway, a voz e o painel, sem LibreChat. `seth-parar` para as mesmas unidades e não cita LibreChat. `seth-agente` abre o OpenCode e, sem binário, sai com mensagem. Unidades em `seth` e `seth-parar`: as do repositório existem em `redesign/systemd/`; as de sistema e as de usuário fora do repositório (`ollama.service`, `omniroute.service`, `laya-roteador.service` e outras) não foram conferidas no sistema.

## Não medido

- Run verde no GitHub no `headSha` do PR: depois do push.
- `scripts/testar_perimetro.sh`: roda só no CI do GitHub (`perimetro.yml`), não no CI local.
- Revisão independente (`agata-revisor`, modo "contra a spec"): não feita nesta rodada.
- Aplicação real: `p8_verificar.sh` depois da assinatura, e o `git apply` em `aplica-pacote-12-11`.
- OpenCode: "fora do PATH" e o binário em `~/.opencode/bin/opencode` foram conferidos em 12/11. A versão 1.0.180 e a falta de modelo configurado são de 07/11 e não foram medidas de novo.
- Capturas de tela: não se aplica, nenhuma tela mudou.
- Uso real dos atalhos `seth` e `seth-parar` no sistema do Humano: não rodados.

## Decisões pendentes do Humano

1. **Spec das partes de comportamento.** As partes 1 e 3 mudam o que `seth`, `seth-parar`, `seth-agente`, `perimetro.sh`, `p8_verificar.sh` e `equipe.py` fazem, e não têm `spec.md` nem `acceptance.json`. A regra P4 é de 11/11, depois dessas propostas. Opções: (a) aceitar a exceção, registrada aqui; (b) pedir spec em proposta própria, assinada à parte (a armadilha "Spec é P-8" exige isso). Não fiz spec nesta rodada, para não mudar `redesign/*/spec/` dentro do pacote.
2. **Testes do LibreChat fora do CI.** `scripts/testar_tira_librechat.py` e `scripts/testar_cobertura_servicos.py` não estão no `perimetro.yml`; só `scripts/testar_sem_goose_ativo.py` está. Ligar os dois exige mudar o `perimetro.yml`, que é canon: teria de entrar no pacote antes da assinatura.
3. **Aba História.** O `estado` mostrado continua o do frontmatter ("rascunho para proposta P-8"), até um painel ler `historia/registro-de-canonizacao.md`. Isso é proposta própria.
4. **Lições da skill.** Manter ou fundir **c** e **j**; manter **k** na skill ou mover; pedir a linha **e** do resíduo (`rm -f`, temporário, `mv`) como item próprio.
5. **Falha pré-existente sem dono.** `python3 -I redesign/router/auditoria_turno.py --selftest` falha com `ModuleNotFoundError: detector_estado_sem_prova`. A importação do módulo irmão (linha 53) já existe no `origin/main` e o CI chama sem `-I`, então não é regressão deste pacote. Dono: a definir pelo Humano. Desde 12/11/2026 (medido nesta rodada).

## Lista de conferência de pronto (R3)

- [x] CI local `TUDO OK` (35 passos), na rodada final sobre `3f1e9055`.
- [ ] Run verde no GitHub no `headSha` do PR: preenchido depois do push.
- [x] Captura de tela: não se aplica (nenhuma tela mudou).
- [x] Sem emoji (E-2): conferido no diff, sem emoji nas linhas novas.
- [x] `.md` com testes medidos, o que não foi medido e a reversão.
- [x] Nenhuma falha "pré-existente" sem dono e data: a do `-I` no selftest tem data (12/11/2026); dono a definir pelo Humano (decisão 5).
- [ ] Texto de MEMÓRIAS sem citação `caminho:número`: o P-19 (só aviso) aponta a frase do diff citado na entrada (996) como citação `arquivo:linha`. É falso positivo: o caminho do diff seguido de dois-pontos e número. A tentativa de trocar a frase foi recusada pelo P-5, porque a entrada (996) já estava commitada e é append-only; por isso o aviso fica registrado.
- [x] Texto 1 da História sem alteração, conferido por sha256 `fe79c529046075dcf03f713eec10b91d7f9b13936cd4c561122408d68eb9906a`.
- [x] Apetite (R2) declarado: até 40 arquivos e 2 h de agente. Medido: 25 arquivos de código; o trabalho (de 08:47 até o fechamento deste `.md`) ficou dentro do apetite, com as duas rodadas de CI local incluídas.

## Reversão

- `git apply -R propostas/pacote-12-11.diff` na árvore com o pacote reverte as sete partes juntas. Medido na cópia limpa: `git apply -R --check` OK, e os arquivos novos saem (`historia/registro-de-canonizacao.md`, `scripts/testar_sem_goose_ativo.py`, `scripts/testar_tira_librechat.py`).
- O `indice.json` volta aos resumos anteriores com a reversão.
- Reverter só uma parte exige proposta própria, assinada à parte, porque as partes se encadeiam: a 2 mexe no `perimetro.sh` que a 1 já mudou; a 4 e a 5 mexem na mesma linha do `AGENTS.md`.
- Registro (`MEMÓRIAS.md`, `ONDE_ESTAMOS.md`, `propostas/superadas/`): entradas são append-only; a reversão do registro é entrada nova. Os seis pares e o da sombra voltam com `git mv` de volta para `propostas/`.

## Movimentos e registro fora do diff

- `propostas/superadas/`: 15 arquivos movidos com `git mv`: `sombra-orcamento-20261106` (`.diff`, `.md` e `.registro.txt`, "superada pela spec v2"), e as partes `tira-librechat-07-11`, `canon-boot-07-11`, `agente-opencode-07-11`, `docs-opencode-07-11`, `verificar-rastro-20261106` e `skill-processo-lessons-07-11` (`.diff` e `.md` cada uma, "incluída em pacote-12-11"). Linhas novas em `propostas/superadas/LEIA-ME.md`.
- `MEMÓRIAS.md`: entrada (996), logo abaixo do marcador. `ONDE_ESTAMOS.md`: as partes marcadas como incluídas, o pacote-11-11 marcado como aplicado, e a linha do pacote-12-11.
- `nucleo-desenvolvimento-07-11` e `nova-versao-lote2-20261106` ficam onde estão (decisão do Humano de 12/11).
- Nenhum desses arquivos está no P-8 (`scripts/perimetro/p08_quarentena.sh` não protege registro).

## Assinatura

Depois do merge deste PR de proposta, o Humano roda:

```
bash scripts/aprovar.sh pacote-12-11 "<motivo>"
```

Verificação depois da assinatura, no checkout vivo, com `git rev-parse HEAD` igual a `origin/main`:

```
bash scripts/p8_verificar.sh pacote-12-11
```
