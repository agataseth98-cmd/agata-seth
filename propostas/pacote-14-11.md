# Pacote de 14/11: sincronia, PROJETO índice, correções e reversão da nova versão (`pacote-14-11`)

Proposta P-8 de `pacote-14-11`. Diff: `propostas/pacote-14-11.diff` (840 arquivos, a maioria renomeações do ECC; 809.862 bytes; sha256 `53ac63824e78af92e3954bd2d3d422ac1f69ceaeb85faa9b10aeb87c0eca8b99`). Base: `origin/main` depois de `fiscal-yaml-12-11` aplicada (#986).

O Humano pediu, em 14/11, uma assinatura só no final. Por isso esta proposta junta, num diff único, as quatro propostas preparadas em 12/11 que ainda esperavam assinatura. O conteúdo de cada uma está nas seções abaixo, copiado das propostas originais:

1. `sincronia-12-11`: fonte única da doutrina da Seth no PROTOCOLOS, porquês, gancho de início de sessão e maxTurns. A proposta foi publicada no #985 e não foi aplicada.
2. `projeto-indice-12-11`: PROJETO.md vira índice, com ESTADO.md gerado, mapa do PROTOCOLOS e teto mecânico.
3. `correcoes-12-11`: notificação não conta turno, âncora staged, CI de workflows e ECC arquivado.
4. `nova-versao-lote2-12-11`: `nv.py reverter`. Substitui `nova-versao-lote2-20261106`, que estava quebrada.

## Composição (14/11, Claude Opus 5.5)

As quatro foram aplicadas em sequência sobre o `main` (`git apply --3way` e, no projeto-indice, cherry-pick a partir da base `c4c71956` para que o merge de 3 vias funcionasse). Os conflitos resolvidos à mão foram estes:

- `scripts/ci_sdd_local.sh`, `.github/workflows/sdd.yml` e `.githooks/pre-commit`: os passos de cada proposta entram juntos, sem duplicar o `verificar_workflows.py`.
- `PROTOCOLOS.md`: entram as seções "Seth no gateway" e "Seth pública", da sincronia, e as seções movidas do PROJETO, do projeto-indice. A referência "PROJETO, Personalidade da Seth" dentro da seção SETH-GATEWAY passou a apontar para o PROTOCOLOS, porque a personalidade foi movida para lá.
- `redesign/router/seth_gateway.py`: fica a versão da sincronia, sem `_DOUTRINA_FIXA`. A troca de referência que o projeto-indice fazia dentro dessa cópia foi refeita no PROTOCOLOS, e o comentário "Decisor local" passou a apontar para o PROTOCOLOS.
- `scripts/sessao_claude_contexto.sh`: fica a versão da sincronia, que delega ao `scripts/sessao_contexto.py`. A seção "Estado vivo (ESTADO.md)", do projeto-indice, foi para o `sessao_contexto.py` como ponteiro com o tamanho do arquivo, e não como o arquivo inteiro: o ESTADO.md tem cerca de 20 KB e o limite do contexto de início é de 3.500 caracteres. O selftest passou a exigir essa seção.

A assinatura vale para o pacote inteiro. As decisões padrão de cada parte estão nas seções originais abaixo, e o Humano pode mudar qualquer uma ao assinar.


---

# Parte original: sincronia-12-11


Proposta P-8 de `sincronia-12-11`. Diff: `propostas/sincronia-12-11.diff` (15 arquivos, 1347 inserções e 191 remoções, 97 KB; sha256 `219cf095dffe6a2c00726659045b56035f41d00328aab506d13fae920708c943`). Base: `origin/main` `9981cbb8` (árvore `dfcf086c`), que já tem `pacote-mecanico-skills-12-11` aplicado (commit `c4c71956`, PR #982). A versão anterior desta proposta foi gerada sobre `c8a7c2d7` com o pacote aplicado (árvore `aada6a53`); as duas bases diferem em 9 arquivos (canônicos com bloco ANCORA-SHA e o par do pacote, que foi para `propostas/aplicadas/`). `git apply --check` do `.diff` sobre `9981cbb8`: RC 0. `scripts/equipe/diff_limpo.py`: OK, nenhum hunk toca bloco gerado; RC 0.

Classe (P4): comportamento e canon. Canon: `PROTOCOLOS.md` (seções novas "Seth no gateway" e "Seth pública"). Comportamento: `redesign/router/seth_gateway.py`, `scripts/*`, `.claude/agents/agata-dev.md`, `config/cli/*`, `redesign/sincronia/spec/*`, `.github/workflows/sdd.yml`.

Não aplicada, não assinada. Publicada como proposta (PR contra `main`, branch `proposta/sincronia-12-11`); a assinatura e a aplicação são do Humano. Origem: decisão do Humano de 12/11/2026, 10:00 (cache do Conselho, entrada (521)): sincronia como um relógio, fonte única, cada regra com porquê, gancho de início, maxTurns pelo uso medido. Executado por Claude Haiku 5.5, agente de proposta, a pedido do coordenador. Trabalho parcial do agente `agent-acef3a98078b3ef5f` reaproveitado (porques, gancho, seção do PROTOCOLOS, configs de CLI), revisto e corrigido onde estava em base antiga.

## 1. Fonte única no gateway

Antes: `redesign/router/seth_gateway.py` tinha `_DOUTRINA_FIXA` (cópia de regras e de ferramentas da Seth) e `_DOUTRINA_PUBLICA` (rota sem ferramentas). A hidratação compacta injetava `_DOUTRINA_FIXA` mais o `AGENTS.md` inteiro, então a cópia repetia o canon.

Agora: o texto próprio da Seth vive em `PROTOCOLOS.md`, entre `SETH-GATEWAY:INICIO/FIM` (seção "Seth no gateway") e `SETH-PUBLICA:INICIO/FIM` (seção "Seth pública"). O gateway lê as seções a cada hidratação (cache por mtime). O marcador `SETH:HIDRATADO` é o hash da seção mais o `AGENTS.md`, então muda quando o canon muda.

Falha: sem a seção de Seth, a hidratação injeta `lacuna` (nunca silêncio). Sem a seção pública, a rota pública responde 503 (`_erro(503)`), sem doutrina de reserva no código.

### Comparação linha a linha (cópia da base x canon)

Método: `_DOUTRINA_FIXA` foi lida do fonte por `ast` e dividida em 113 frases. Cada frase foi procurada, por sobreposição de 5-gramas de palavras, nos arquivos operativos (AGENTS, REGRAS, PROTOCOLOS, FALHAS, PROJETO) e no registro (MEMÓRIAS). A medição mecânica não basta (texto parafraseado): a classificação abaixo é por bloco, e cada decisão tem grep de frase-chave no canon. Saída bruta: fora do repositório.

| Bloco da cópia | Achado no canon | Destino |
|---|---|---|
| Identidade "Você é a Seth…", papéis, portão | "portão": REGRAS e PROJETO; "Humano decide": AGENTS | identidade fica em PROTOCOLOS; papéis e portão saem (já no canon) |
| Não bajule, sem emoção simulada, sem afirmar sem fonte | REGRAS e PROJETO ("bajul"); AGENTS (voz, F0) | sai (DUP) |
| Sem saudação (Regra 5), exemplos "Olá" e "Espero ter ajudado", nota "(422)" | REGRAS:114 tem a regra; exemplos e histórico não estão no canon | regra sai (DUP); o aviso "se o Humano cumprimentar…" (700) vai para PROTOCOLOS |
| Personalidade (PROJETO "Personalidade da Seth"; 685, 702) | PROJETO:121-126; AGENTS | referência em PROTOCOLOS; "Sistemas operacionais" e "Bem-vindo de volta" saem (PROJETO) |
| Evidência só do que existe (687, 688, 690) | PROJETO:122-130 | DUP; "PROPOSTAS-PENDENTES" (695) e auditoria vão para PROTOCOLOS |
| Método medido (17/10): estado de unidade, número de entrada, nome de revisor | nenhum canon operativo | SÓ NA CÓPIA: vai para PROTOCOLOS |
| Regra 1 no gateway: cabeçalho da Máquina (705); TOPO-PROPOSTA-JA-APLICADA; ALERTA-HISTORIA | PROJETO cita 705; o detalhe do gateway não | detalhe vai para PROTOCOLOS |
| Opinião com segundo cérebro (Jev, `opiniao_jev`) | nenhum | SÓ NA CÓPIA: PROTOCOLOS |
| Você PODE medir a Máquina (`maquina_verificar`, lista fechada) | nenhum | SÓ NA CÓPIA: PROTOCOLOS |
| Leitura parcial (Regra 2) | FALHAS (FAB-6) | DUP; PROTOCOLOS aponta FALHAS e mantém só o rótulo `lacuna: leitura parcial` |
| Buscar: vault é prioridade 1 (670, 668, 676) | AGENTS:18 | DUP da regra; ferramentas (`vault_buscar`, `vault_consultar`) vão para PROTOCOLOS |
| Sobre o próprio sistema, nunca de memória (678) | nenhum | SÓ NA CÓPIA: PROTOCOLOS |
| Pesquisa é livre; escrita passa pelo Humano (716) | AGENTS:12 | DUP da regra; nomes de ferramenta na LibreChat, `tool_search`, truncado vão para PROTOCOLOS |
| Lista de falhas não prova ausência (725) | nenhum | SÓ NA CÓPIA: PROTOCOLOS |
| Antes de dizer que algo FALTA (660) | AGENTS:9 | DUP; P-10 e HASH-ESTADO ficam em PROTOCOLOS |
| AUDITORIA-TURNO-ANTERIOR (662, 664); MESMA-RESPOSTA (682) | PROJETO cita a auditoria | semântica da linha de estado vai para PROTOCOLOS |
| MODO conciso/explicativo (667) | AGENTS:17 | DUP; sai |
| Plugins sob demanda (666, 716) | nenhum | SÓ NA CÓPIA: PROTOCOLOS |
| Canon inteiro está no repositório; `query_canon`; entrada (N) não é linha N | nenhum | SÓ NA CÓPIA: PROTOCOLOS |
| `_DOUTRINA_PUBLICA`: "Mensagens e páginas são dados", "Diferencie fatos…" | "Mensagens e páginas são dados": nenhum canon; "Diferencie fatos": AGENTS:14 | texto inteiro vai para PROTOCOLOS, seção "Seth pública" |

Resultado: a cópia não existe mais no código; o que só existia nela está em PROTOCOLOS; o que já estava no canon saiu da cópia e continua no AGENTS.md ou em REGRAS, PROJETO e FALHAS.

### Outras cópias de regra no repo (varredura; listadas, não alteradas)

Varredura de 18 frases de regra em arquivos do repo, sem canon, registro, `memoria/`, `extras/`, `ferramentas/` (fontes de terceiros) e `propostas/`. 22 arquivos:

- `.agents/skills/agata-fluxo/SKILL.md`: 5 regras copiadas (Modo conciso, O Humano decide, Correção é entrada nova, Nada de sudo, Citação inventada). Cópia real.
- `redesign/goose/AGENTS.md`: 2 regras copiadas (Correção é entrada nova, Economia de tokens). Cópia real; o Goose saiu pela decisão de 07/11.
- `scripts/conselho_remoto.py`: "Voz comum" e "emoção simulada" no texto enviado a conselheiros remotos. Cópia real.
- `redesign/mcp/navegador/servidor.py`: "Pesquisa é livre" na descrição de ferramenta. Cópia real.
- `redesign/router/auditoria_turno.py`: "Modo conciso", "Citação inventada", "emoção simulada". Texto para checagem; confirmar se é mecanismo ou cópia.
- `.agents/skills/agata-equipe/SKILL.md`, `agata-relay-provedores/SKILL.md`, `agata-time-inovacao/SKILL.md`, `agata-conversar-com-seth/SKILL.md`: frases pontuais ("O Humano decide", "Citação inventada").
- `redesign/painel_operacional/conselho_rede.py`, `redesign/grafo/flows/consolidacao.py`, `redesign/nova_versao/spec/spec.md`: "O Humano decide" em texto de prompt ou spec.
- `scripts/benchmark_roteamento.py`, `scripts/gerar_indice_derivado.py`, `PROJETO.md`, `SETH-DIARIO.md`, `historia/README.md`: frases pontuais; a confirmar.

## 2. Porquês: `scripts/porques.py --verificar`

Cada regra do `AGENTS.md` (bullets "Sempre") e cada skill de `.agents/skills/` precisa de origem rastreável: `MEMÓRIAS (N)` com entrada que existe em `MEMÓRIAS.md`, `MEMORIAS-MORNO.md` ou `memoria/frio/`; `Humano DD/MM/AAAA` com data válida; ou `cache (N)` na forma. A origem pode estar no texto da regra (inline) ou em `config/porques.json` (registro). Na primeira versão é aviso: sai 0. Com `--estrito`, sai 1.

Medido agora: 26 unidades (15 regras do AGENTS.md, 11 skills). 24 com origem. 0 referência sem entrada. 0 registro órfão.

Sem porquê (2), para o Humano decidir:
- `skill:agata-time-inovacao`: candidata MEMÓRIAS (966), de 06/11, que fala de "a skill de inovação e o time de inovação". Não registrada: é inferência, e o Humano confirma.
- `skill:design-taste-frontend`: fonte externa ("tasteskill v2", no frontmatter). Nenhuma decisão do Humano no repo. Manter ou sair.

Origens fracas (contam como OK, mas são "primeira citação", não decisão confirmada): AGENTS "Não minta" (309), AGENTS "Nada de sudo" (986: o próprio registro diz que a decisão original não foi achada), skill `agata-aplicar-proposta` (543), skill `agata-llm-fundamentos` (932), skill `agata-painel` (903).

Limite do verificador: uma regra que cita qualquer entrada existente conta como OK, mesmo que a entrada só a mencione. Por isso as origens fracas aparecem na lista acima.

Registro `config/porques.json`: 18 unidades. Removidas 10 entradas órfãs de skills que a consolidação tirou (agata-carregar, agata-conselho-memoria, agata-disciplina, agata-ferramentas, agata-fluxo-equipe, agata-mudanca-segura, agata-processo-lote, elephant-goldfish-sdd, experimento-agata, morse). Elas estão em `extras/arquivo-skills-12-11/`.

## 3. Gancho de início de sessão

- `scripts/sessao_contexto.py` monta o contexto, em no máximo 3.500 caracteres: (a) estado da Máquina (`estado_para_eco.sh`, 8 linhas); (b) últimas 3 decisões do cache (`cache_conselho.py ler --n 50`, só entradas `decisao`); (c) lotes abertos, lidos da coluna "estado" de `ONDE_ESTAMOS.md`; (d) regras ativas, com os títulos dos bullets "Sempre" do AGENTS.md; (e) sessão conjunta (`equipe.py status`). Saída: `hookSpecificOutput.additionalContext`. Medido agora: 2.923 caracteres.
- `scripts/sessao_claude_contexto.sh` é invólucro: chama o conteúdo comum. `.claude/settings.json` já tinha `SessionStart` apontando para ele; não mudou.
- `config/cli/gemini/settings.json.exemplo` e `config/cli/codex/config.toml.exemplo`: `SessionStart` com o mesmo conteúdo. São exemplos; copiar para `~/.gemini` e `~/.codex` é passo do Humano. As URLs de doc que o verificador cita não foram abertas nesta rodada; a versão instalada não foi medida.
- OpenCode: sem gancho de início (`nao-medido`).
- `scripts/conselho_mecanismos.py`: novo controle "início de sessão" (Claude Code ok-mecanico; Gemini e Codex passo-humano; OpenCode nao-medido). E "fonte única" (ok-mecanico: sem `_DOUTRINA_FIXA` nem `_DOUTRINA_PUBLICA` no gateway, com os quatro marcadores em PROTOCOLOS).

## 4. maxTurns pelo uso medido

Medição disponível: os relatórios desta sessão citam 19 a 232 tool_uses por execução de agente. O repositório não tem medição por tipo de agente, e os relatórios não dizem qual tipo chegou a 232. Por isso o item não foi cumprido por tipo; só o que a faixa prova foi mudado.

| Agente | Antes | Agora | Razão |
|---|---|---|---|
| `agata-dev` | 80 | 300 | Maior uso medido, 232 tool_uses; 80 cortaria esse caso. Margem de ~1,3x. tool_uses >= turnos, então 300 cobre 232 com folga |
| `agata-spec`, `agata-revisor`, `agata-inov-arquiteto` | 40 | 40 | sem medição por tipo |
| `agata-ci`, `agata-inov-pesquisa` | 30 | 30 | sem medição por tipo |
| `agata-pesq-processo`, `agata-pesq-rea`, `agata-pesq-painel`, `agata-inov-critico` | 25 | 25 | sem medição por tipo |

O teste de `maxTurns` agora exige de 10 a 300, e que `agata-dev` tenha pelo menos 232.

## 5. Testes

`uv run --offline --with pytest bash scripts/ci_sdd_local.sh`, numa cópia com histórico da base `9981cbb8` (worktree destacada) com o `.diff` aplicado: `CI LOCAL: TUDO OK`, 49 linhas OK e 0 FALHA. Nessa base, `ferramentas/test_ferramentas.py::FerramentasTests::test_indice_em_dia` passa.

A versão anterior desta seção relatava 1 FALHA (`test_indice_em_dia`) numa árvore com o pacote aplicado e não commitado. Causa daquela falha: `ferramentas.skills_proprias()` usa `git ls-files`, que ainda listava `agata-carregar` (removida no pacote). Com o pacote no commit da base, a falha não ocorre. A falha intermitente anterior (índice zerado durante a suíte completa; hipótese não confirmada: teste que herda `GIT_INDEX_FILE`) não ocorreu nesta rodada.

Quem aplicar roda o CI de novo nessa base; o CI do GitHub roda no PR.

Passos da sincronia, todos OK: gate de specs (sincronia: 25 critérios), critérios e drift da sincronia, `testar_sincronia.py`, selftest do gancho, selftest e verificador de porquês.

Testes específicos (rodados a parte):
- `python3 scripts/testar_sincronia.py`: 25 testes OK (fonte única do gateway, rota pública, marcador, `maxTurns`, porquês, gancho, configs de CLI).
- `python3 scripts/porques.py --selftest`: OK. `python3 -I scripts/sessao_contexto.py --selftest`: OK.
- `python3 -I scripts/gate_spec_sync.py`: 14 componentes, 0 falha, 1 aviso (`alexandria`, dívida já existente).
- `python3 scripts/conselho_mecanismos.py --verificar`: 33 controles; ok-mecanico 21, disciplina 4, FALHA 0.
- Formato: `config/cli/codex/config.toml.exemplo` parseia como TOML; os JSON (`config/cli/gemini/settings.json.exemplo`, `config/porques.json`, `redesign/sincronia/spec/acceptance.json`, `.claude/settings.json`) parseiam.
- `scripts/sessao_claude_contexto.sh` roda e entrega JSON válido.

Correção encontrada na base (`pacote-mecanico-skills-12-11`): o controle "pacote mínimo na skill de equipe" de `conselho_mecanismos.py` apontava para `agata-fluxo-equipe`, skill que a consolidação tirou. Corrigido aqui: aponta para `agata-equipe`, seção 9. Sem essa correção, o verificador marcava FALHA.

Não medido:
- disparo real do `SessionStart` numa sessão aberta do Claude Code, e a ordem com os outros ganchos;
- Gemini CLI e Codex rodando o gancho instalado: só a doc foi lida;
- se a Seth responde igual com o texto novo na hidratação: só conversa real mede isso;
- `maxTurns` por tipo de agente: sem medição por tipo.

## 6. Decisões pendentes (Humano)

Padrões registrados pelo coordenador (12/11/2026). Cada item abaixo diz o padrão que esta proposta adota; o Humano confirma ou muda na assinatura.

1. Confirmar a dedupe da doutrina da Seth (seção "Seth no gateway"): a Seth deixa de receber as regras que já estão no AGENTS.md duas vezes. O texto que sobra é o que só existia no código.
   **Padrão: sim, dedupe.**
2. Rota pública sem a seção `SETH-PUBLICA`: hoje responde 503 (falha fechada). Confirmar, ou aceitar texto de reserva.
   **Padrão: 503 (falha fechada), sem texto de reserva.**
3. `maxTurns`: pedir ao coordenador a tabela de tool_uses por tipo de agente. Só `agata-dev` mudou (80 para 300).
   **Padrão: só `agata-dev` muda por agora; os demais ficam como estão.**
4. Porquês: confirmar a origem de `agata-time-inovacao` (candidata 966) ou tirar; decidir `design-taste-frontend`.
   **Padrão: pergunta aberta ao Humano para as duas skills; nenhuma decisão tomada nesta proposta.** Nesta versão o verificador só avisa (sai 0).
5. Origens fracas (309, 986, 543, 932, 903): confirmar se a entrada decide a regra ou só a menciona.
   **Padrão: aceitas como estão, contando como OK.**
6. Cópias listadas acima (varredura): remover, e em qual proposta. O Goose (`redesign/goose/AGENTS.md`) pode sair junto com o Goose.
   **Padrão: proposta futura, em proposta própria. Nenhuma cópia da varredura é removida nesta.**
7. `ONDE_ESTAMOS.md`: as linhas `pacote-mecanico-12-11` e `skills-consolidadas-12-11` ainda estão como "proposta", e as duas estão superadas.
   **Feito nesta proposta:** linha nova no ONDE_ESTAMOS, com `pacote-mecanico-skills-12-11` aplicado (PR #982) e as duas linhas antigas superadas por ele. As linhas antigas não foram editadas. Consequência medida: `lotes_abertos` conta a coluna `proposta`, então o gancho continua listando as duas como abertas. Trocar essas células é decisão separada.
8. Gemini CLI e Codex: copiar os exemplos para `~/.gemini` e `~/.codex` (passo do Humano). OpenCode sem gancho de início.
9. Ordem: aplicar `pacote-mecanico-skills-12-11` antes desta proposta.
   **Feito:** `pacote-mecanico-skills-12-11` aplicado (commit `c4c71956`, PR #982, assinado pelo Humano em 12/11). Esta proposta é sobre `9981cbb8`.
10. Registro: esta proposta toca `MEMÓRIAS.md` (uma entrada de registro, numerada no merge com `scripts/equipe/numero_memorias.py`) e `ONDE_ESTAMOS.md` (uma linha nova). O código e o canon ficam só no `.diff`; quem aplica faz isso depois da assinatura e da trava.

---

# Parte original: projeto-indice-12-11


Proposta P-8 de `projeto-indice-12-11`. Diff: `propostas/projeto-indice-12-11.diff` (51 arquivos; 1.995 inserções e 310 remoções; 286.569 bytes; sha256 `d26211f5c6eaaca5b63b7af0c320a4f8053db04381ff1c44b479a19ebefc40a1`).

**Base: `origin/main` `9981cbb8`**, com o pacote `pacote-mecanico-skills-12-11` já aplicado (PR #982). Esta proposta exige essa base. O diff foi gerado contra a árvore de `origin/main` por script (formato `git diff --no-renames`), e a conferência de aplicação foi feita com GNU `patch`: `origin/main` + diff reproduz o worktree em 3.144 arquivos, com 0 divergências. O branch do worktree não foi movido e nada foi commitado.

Classe (P4): comportamento e canon. Canon: `PROJETO.md`, `PROTOCOLOS.md`, `REGRAS.md` (uma linha), `PROMPT_CARREGAMENTO.md`, `AGENTS.md` (ponteiro). Comportamento: `.githooks/*`, `.github/workflows/sdd.yml`, `scripts/*`, `redesign/*`, `config/*`. Registro gerado: `ESTADO.md` (fora do P-8, como `.hidrata.md`).

Não toca `MEMÓRIAS.md`, `ONDE_ESTAMOS.md` nem `INDICE_MEMORIAS*`: a trava de aplicação não bloqueia esta proposta.

## Decisões do Humano que esta proposta cumpre

Cache do Conselho, entradas 521 e 522 (12/11/2026, 10h12), e a decisão de 16h00 (mapa do PROTOCOLOS na hidratação):

1. PROJETO.md vira **índice curto**: quem é o Agata, princípios, "Onde encontrar". Atendido: 5.288 bytes (teto 6.000).
2. Estado vivo vira **arquivo gerado** pela Máquina, hidratado aos modelos, fora do canon. Atendido: `ESTADO.md`, gerado por `scripts/gerar_estado.py` de fontes reais; sem data e sem SHA; entra na hidratação (`.hidrata.md`, `.hidrata-seth.md`), no SessionStart, no painel e na nuvem (por URL).
3. Teto vira **bloqueio mecânico** no commit. Atendido: o pre-commit confere `git show :PROJETO.md` com `teto.py` e recusa acima do teto, dizendo para onde vai cada conteúdo.
4. A nuvem lê **o índice e o estado gerado**, com orientação de onde achar cada informação. Atendido: `PROMPT_CARREGAMENTO.md` manda ler PROJETO (a tabela "Onde encontrar" aponta o arquivo de cada resposta) e ESTADO (que traz o mapa de PROTOCOLOS).
5. O histórico que sai vai para **`extras/arquivo/`**. Atendido: `extras/arquivo/projeto-ate-2026-11-12.md` é cópia byte a byte do PROJETO em `c8a7c2d7` (sha256 `adbf50e1c2b9be4fac1b67c3e82b3dca7fb48d1ee60c31324ed4253f47d783d1`).
6. "Como" vai para **PROTOCOLOS.md**, e **na hidratação o PROTOCOLOS entra como mapa + busca, não inteiro** (decisão de 16h00). Atendido: 18 seções movidas por inteiro (12 para o PROTOCOLOS, 6 para o estado de fundo), com o título original (H2) mantido; 2 saem em parte. O mapa das seções é gerado por `gerar_mapa_projeto.py` e vai dentro do `ESTADO.md`.
7. Nenhuma decisão pode se perder: **verificação mecânica** de que cada parágrafo que saiu existe no destino. Atendido: `redesign/projeto_indice/verificar_destinos.py` (regras a, b, c, d) e o teste `test_todo_paragrafo_que_saiu_existe_no_destino`.

## Hidratação (decisão de 16h00)

Medida com `gerar-hidratacao.sh`, em bytes:

| Arquivo | Antes | Depois |
|---|---:|---:|
| `.hidrata.md` no `origin/main` `9981cbb8` (linha de base desta proposta) | 68.950 | — |
| `.hidrata.md` no HEAD antigo `c8a7c2d7` (referência da proposta anterior) | 67.182 | — |
| `.hidrata.md` com esta proposta | — | **59.944** (−9.006 contra `origin/main`; −7.238 contra o HEAD antigo) |
| `.hidrata-seth.md` (gateway/Seth, mesmo template + MOD) | — | 60.096 |

Composição: sai o PROTOCOLOS inteiro da hidratação (era 46.391 B depois da proposta); entra o mapa de PROTOCOLOS, dentro do `ESTADO.md` (12.4 KB com a orientação), e o mapa do PROJETO continua (774 B). O `PROTOCOLOS.md` aparece na hidratação só como mapa: `grep` no `.hidrata.md` dá 0 ocorrências de `# PROTOCOLOS.md` e 1 de "Mapa de PROTOCOLOS".

**Quem recebe o quê:**
- **Gateway/Seth:** o `.hidrata-seth.md` traz o mapa (por ser o mesmo template) e a orientação: "o texto de uma seção não entra nesta hidratação; busque o título (query_canon com doc PROTOCOLOS)", e "leia 'Carregar e formatos' antes de responder".
- **Claude Code (SessionStart):** imprime o ESTADO, que traz o mapa.
- **Nuvem:** `PROMPT_CARREGAMENTO.md` manda ler REGRAS, FALHAS, PROJETO (índice), ESTADO (com o mapa) e a seção "Carregar e formatos" de PROTOCOLOS (raw de `main` já na lista de URLs).

**Risco que o Humano deve olhar:** a forma exata do cabeçalho e da linha de turno estava em PROTOCOLOS e agora só se obtém por busca. Por isso o mapa e o prompt mandam ler "Carregar e formatos" antes de responder. Se um modelo não buscar, ele perde o formato exato. Não medido ainda com modelo real.

## Mapa seção → destino

Tamanhos em bytes do PROJETO anterior (49.326 B).

| Seção do PROJETO anterior | B | Destino |
|---|---:|---|
| (preâmbulo: título, "Como ler") | 2.198 | `extras/arquivo/` (histórico) |
| O que é | 1.929 | índice: Nome, Assistente, Agata=, Executor, Grafia; Frentes e Acesso remoto → estado de fundo; "Fonte única do nome falado" → PROTOCOLOS |
| Máquinas | 1.636 | estado de fundo |
| Ambiente Operacional | 371 | PROTOCOLOS |
| Cérebro | 2.783 | estado de fundo |
| Serviços (boot) | 5.278 | estado de fundo (a lista viva sai do `ESTADO.md`) |
| Memória e hidratação | 4.438 | PROTOCOLOS |
| Interface | 3.771 | estado de fundo |
| Personalidade da Seth | 4.170 | PROTOCOLOS |
| Atualização segura de componentes | 1.203 | PROTOCOLOS |
| Segurança | 1.498 | PROTOCOLOS |
| Conselho Remoto — Fase 1 | 2.370 | PROTOCOLOS |
| Sudo e interação humana | 1.102 | PROTOCOLOS |
| Quarentena estrutural (P-8) | 3.420 | PROTOCOLOS |
| Doutrina de defesa proporcional | 719 | índice "Princípios" (adotada + 5 princípios); o formato de pedido de decisão → PROTOCOLOS |
| Estado dos bugs e dos testes | 1.811 | estado de fundo |
| Decisor local | 3.688 | PROTOCOLOS |
| Plano vigente (v1.1) | 2.273 | estado de fundo |
| Estado de publicação | 372 | PROTOCOLOS |
| Ferramenta embutida: selar.sh | 246 | PROTOCOLOS |
| Memória em duas camadas | 3.821 | PROTOCOLOS |
| Referência | 208 | índice (parágrafo mantido), `PROJETO_REFERENCIA.md` |

Índice (`PROJETO.md`): só o topo muda (título, frase de papel e um parágrafo com ESTADO e teto), nas linhas 1 a 3 e em inserções logo depois; as linhas 4 e 5 do original ficam como estavam; o bloco `ANCORA-SHA` fica byte a byte igual ao do main. Por isso o `diff_limpo` passa.

## Tamanhos antes e depois

| Arquivo | `origin/main` (antes) | Depois |
|---|---:|---:|
| `PROJETO.md` | 49.326 | 5.288 |
| `PROTOCOLOS.md` | 18.301 | 46.391 |
| `extras/projeto-detalhe/estado-de-fundo-12-11.md` | — | 18.817 |
| `extras/arquivo/projeto-ate-2026-11-12.md` | — | 49.326 (cópia) |
| `ESTADO.md` (gerado; inclui o mapa de PROTOCOLOS) | — | 18.751 |
| `scripts/gerar_estado.py` | — | 11.009 |
| `scripts/gerar_mapa_projeto.py` | 4.011 | 4.083 |
| `.githooks/gerar-hidratacao.sh` | 30.666 | 29.820 |
| `REGRAS.md` | 19.523 | 19.772 |
| `PROMPT_CARREGAMENTO.md` | 11.319 | 11.844 |
| `config/servicos-agata.txt` | — | 3.220 |

Hidratação: ver a tabela acima (68.950 em `origin/main`; 59.944 depois).

## Consumidores

| Consumidor | Mudança |
|---|---|
| `scripts/perimetro.sh`, `scripts/perimetro/p09_servicos_declarados.sh` (P-9) | listas carregadas de `config/servicos-agata.txt` (`p9_carregar_fonte`); mesmas unidades e mesma ordem |
| `redesign/painel_operacional/server.py` (`_lacunas_snapshot`) | lê `## Serviços (boot)` do ESTADO.md; unidade `oneshot` não é lacuna (mesma regra do P-9) |
| `redesign/router/auditoria_turno.py` | o conjunto de números de entrada conhecidos inclui o histórico e a prosa movidos (o conjunto não encolhe) |
| `scripts/testar_pacote2.py` | títulos esperados do mapa: "Princípios" e "Onde encontrar" |
| `scripts/gerar_mapa_projeto.py` | **parametrizado pelo arquivo-fonte**: o rótulo usa o nome do arquivo (`PROJETO.md` ou `PROTOCOLOS.md`). A saída do PROJETO não muda (774 B) |
| `scripts/gerar_estado.py` | nova seção "Mapa de PROTOCOLOS": gerada pelo `gerar_mapa_projeto.py`, com orientação de onde buscar o texto |
| `.githooks/gerar-hidratacao.sh` | a camada de PROTOCOLOS sai da hidratação; o ESTADO (com o mapa) entra no lugar; sai o aviso de 48.000 B |
| `.githooks/pre-commit` | teto como bloqueio; regenera o ESTADO antes da hidratação; gatilho de hidratação passa a contar o ESTADO.md |
| `scripts/sessao_claude_contexto.sh` | inclui o ESTADO no SessionStart; selftest confere |
| `scripts/gerar_indice_derivado.py` | só docstring. **Não executado** (escreve em `memoria/missoes/`). O derivado passa a ter o índice; o estado fica fora (decisão a confirmar) |
| `scripts/perimetro/p22_derivados_drift.sh` | ESTADO.md entra nos derivados; config, systemd e propostas entram nas fontes |
| `PROMPT_CARREGAMENTO.md` | nuvem: índice + ESTADO (com o mapa); seção "Carregar e formatos" de PROTOCOLOS; URL raw do PROTOCOLOS e do ESTADO |
| `REGRAS.md` linha 6 | ponteiro morto `(PROJETO)` trocado por lacuna declarada (ver "Desvios") |
| `config/caminhos-framework.txt` | `instancia|ESTADO.md` |
| `scripts/ci_sdd_local.sh`, `.github/workflows/sdd.yml` | testes, destinos, teto e ESTADO em dia |
| Ponteiros `PROJETO.md, "<seção>"` | 29 reapontados em 23 arquivos (só o nome do arquivo; o título fica) |

**Desvios declarados:**

1. `scripts/perimetro-sombra-referencia.sh` **não foi alterado**. É o monolito congelado do modo sombra; a memória do projeto registra que mexer nele anula o propósito. As listas do P-9 dele e seus ponteiros ficam como estão. Se o Humano quiser alinhá-lo ao manifesto, é decisão separada.
2. `ONDE_ESTAMOS.md` **não recebe seção nova**. O gerador lê "Bugs e testes abertos" se existir; hoje não existe, então o ESTADO aponta para a prosa de estado. Criar a seção é registro (outra entrada).
3. Texto **dentro do bloco `ANCORA-SHA`** e nos geradores de âncora (`atualizar_ancora_prompt.py`, `p8_integral.py`) ainda diz `PROJETO.md, "Memória e hidratação"`. Mudar o texto do gerador exige mexer no reconhecedor do P-8 integral. O índice mantém a linha "Memória e hidratação" na tabela, então o ponteiro resolve.
4. Topo do `PROJETO.md`: as mudanças ficam nas linhas 1 a 3 e em inserções logo depois delas. O `diff_limpo` recusa hunk com linha do bloco `ANCORA-SHA` como contexto, e o pre-commit reescreve esse bloco.
5. REGRAS.md linha 6: "critério de reabilitação (PROJETO)" apontava para nada. A busca em MEMÓRIAS, INDICE_MEMORIAS, FALHAS, PROTOCOLOS e PROJETO_REFERENCIA não achou o critério. O texto passa a dizer "lacuna declarada em 12/11/2026". **É alteração de texto normativo**: o Humano decide o critério.
6. Ponteiros que ficam dentro do texto movido (verbatim) continuam como estavam; o teste de ponteiros ignora esse trecho.
7. Mapa de PROTOCOLOS dentro do ESTADO (12.4 KB) é maior que o mapa do PROJETO (774 B), porque o PROTOCOLOS tem mais seções e cada uma traz o primeiro parágrafo. Mesmo gerador; não foi encurtado.

## Verificação feita

- Suíte do componente `redesign/projeto_indice/tests/test_projeto_indice.py`: **24 testes OK** (um por critério, mais ponteiros, título movido, mapa de PROTOCOLOS, mapa do PROJETO com rótulo).
- `ci_sdd_local.sh` (`uv run --offline --with pytest bash scripts/ci_sdd_local.sh`) no worktree rebaseado: **TUDO OK, 47 passos**.
- `gate_spec_sync.py`: 0 falhas (o aviso do alexandria já existia). `conselho_mecanismos.py --verificar` no CI: 0 falhas.
- `verificar_destinos.py`: OK. `teto.py`: 5.288 B, OK. `gerar_estado.py --verificar`: em dia.
- `diff_limpo.py` no diff: OK (nenhum hunk toca o bloco gerado).
- Sabotagens (rodada anterior, mantidas): ponteiro vivo plantado é pego; parágrafo trocado no PROTOCOLOS é pego pelo verificador de destinos; arquivo restaurado e conferido por `cmp`.
- `origin/main` + diff, aplicados com `patch -p1`, reproduzem o worktree em 3.144 arquivos, 0 divergências.

## Definição de pronto

- [x] diff sem bloco gerado (`diff_limpo`: OK)
- [x] base `origin/main` 9981cbb8 + diff reproduz o worktree (3.144 arquivos, 0 divergências)
- [x] CI local completo verde (47 passos), no worktree rebaseado
- [x] parágrafos que saíram conferidos no destino (verbatim)
- [x] teto, ESTADO em dia e ponteiros mecanicamente conferidos
- [x] hidratação abaixo do HEAD antigo (59.944 contra 67.182 B)
- [ ] PR de proposta com CI verde (a fazer por quem propõe, depois da fila)
- [ ] assinatura do Humano no terminal, depois do merge
- [ ] aplicação (PR `aplica/*`) passa pelo `diff_limpo`, pela trava e pela renumeração de MEMÓRIAS (sem entrada nova nesta proposta)

## Apetite

Uma proposta, uma assinatura. Não entra frente nova, nem skill, nem registro em MEMÓRIAS/ONDE_ESTAMOS. Não entra a mudança da sombra do P-9, nem a seção de bugs no ONDE_ESTAMOS, nem encurtar o mapa do PROTOCOLOS.

## Reversão

- Depois da aplicação: `git revert` do commit de aplicação. O `PROJETO.md` volta ao anterior; o histórico em `extras/arquivo/` e as seções de destino ficam (são aditivos). `ESTADO.md` e `config/servicos-agata.txt` saem junto. A hidratação volta a embutir o PROTOCOLOS inteiro.
- P-9: se reverter `scripts/perimetro.sh` e `p09_servicos_declarados.sh`, as listas fixas voltam.
- Nada se apaga.

## Não medido

- Tokens da hidratação (só bytes foram medidos).
- Se um modelo real, na hidratação nova, busca "Carregar e formatos" e usa o formato certo. **Não medido.** É o risco da decisão de 16h00.
- O pre-commit de ponta a ponta (teto bloqueando, ESTADO regenerado num commit real). **Não rodado**: não há commit nesta preparação. O código foi conferido por leitura e pelo `teto.py`.
- Painel: `_lacunas_snapshot` lendo o ESTADO com unidades reais no systemd. Conferido por leitura e por teste de texto; não rodado contra o `systemctl` vivo.
- P-9 com systemd real (`Type=oneshot`) e com as unidades de usuário no ar.
- `gerar_indice_derivado.py` (não executado).
- Leitura pela nuvem: nenhum modelo em nuvem leu o texto novo.
- Gateway/Seth ao vivo com o `.hidrata-seth.md` novo.

## Assinatura (depois do merge, no terminal do Humano)

```
git -C ~/agata pull --ff-only
bash ~/agata/scripts/aprovar.sh projeto-indice-12-11 "PROJETO.md índice; estado gerado; mapa do PROTOCOLOS na hidratação; teto mecânico; histórico em extras/arquivo"
```

O executor não roda `aprovar.sh`. Não existe `APROVADO-projeto-indice-12-11`.

## Ordem na fila

Esta proposta exige `origin/main` 9981cbb8 (com o pacote aplicado) como base. Quando a proposta for aplicada, o pre-commit regenera o `ESTADO.md` e o `.hidrata.md` pelo código aplicado; o ESTADO do diff é gerado sem esta proposta na pasta de propostas, e o do worktree a lista como aberta.

---

# Parte original: correcoes-12-11


Proposta P-8 de `correcoes-12-11`. Diff: `propostas/correcoes-12-11.diff` (sha256 `23e4d4242e871af058f4d76db49b2ac171e4292437d620764257d5cff935faf5`; 406990 bytes; 19 arquivos de código, canon e índice, mais 757 renomeações do ECC sem hunk). Base: `origin/main` `9981cbb8` mais `propostas/fiscal-yaml-12-11.diff` (sha256 `620ac726bf241410b0c53013c9247ca4784b6f3fe3000fc3700b549a2cae6df7`), que tem de ser aplicado antes. Gerado com `git diff -M`: sem `-M` o diff teria 13,5 MB, porque cada um dos 757 arquivos do ECC apareceria duas vezes. Isso é seguro porque nenhum dos 1514 caminhos de renomeação está no escopo do P-8 (`_p8_eh_comportamento`, medido com a função da base).

Executado por Claude Haiku 5.5, agente de proposta, a pedido do coordenador. Não aplica, não assina, não faz commit nem PR. O registro (MEMÓRIAS e ONDE_ESTAMOS) e o número da entrada ficam para quem abrir o PR, no merge (`scripts/equipe/numero_memorias.py`).

## Partes

1. **Notificação não conta turno** (`scripts/turno.py`, `scripts/testar_turno.py`, `redesign/router/spec/`). Se o `prompt` do gancho UserPromptSubmit começa com `[SYSTEM NOTIFICATION`, `<task-notification>`, `Another Claude session sent a message`, `Stop hook feedback` ou `Goal check-in`, o t não avança. O gancho injeta a linha do turno atual com o rótulo `contador mecânico; notificação do sistema, sem avanço`. Sem sessão com turno, não injeta nada. Mensagem do Humano que cita a marca no meio segue contando. Sem `prompt` no payload, conta como antes. Testes: 6 novos em `TestHook` (47 testes no total, todos OK); 3 critérios novos na spec, com o mesmo teste citado no `acceptance.json`.

2. **Âncora staged de commit abortado** (`scripts/equipe/ancora_indice.py`, novo; `.githooks/pre-commit`). Causa, medida num clone de teste (base mais fiscal-yaml):
   - `git commit -m ""` (aborta depois do pre-commit) deixa staged `REGRAS.md`, `PROJETO.md`, `PROMPT_CARREGAMENTO.md`, `MEMÓRIAS.md` e `.hidrata.md`, com o bloco ANCORA-SHA regravado.
   - O commit seguinte, com o hook original, para com `SUSPEITO (P-8)` em `REGRAS.md` e `PROJETO.md`, sem mudança nenhuma do autor.
   - Conserto: antes do perímetro, o pre-commit devolve o bloco ANCORA-SHA do índice ao do HEAD. O resto do staged não é tocado. O passo da âncora regrava o bloco logo depois, neste mesmo commit.
   - Com o conserto, o mesmo commit seguinte passa (rc 0). Selftest do helper: reproduz o SUSPEITO com só a âncora staged, mostra que o P-8 passa depois, e que mudança real do autor fora do bloco continua no índice.
   - Não afrouxa o P-8. A alternativa de deixar o P-8 aceitar qualquer mudança dentro do bloco foi descartada: o bloco é texto que os modelos leem como canon, e a checagem teria de provar que o conteúdo é gerado. O conserto só devolve o índice ao que o HEAD já aprovou.

3. **CI remoto confere os workflows** (`scripts/p8_verificar_pr.sh`, `.github/workflows/sdd.yml`, `.github/workflows/fiscal-p8.yml`).
   - `p8_verificar_pr.sh`, novo bloco 2c: lê os `.github/workflows` do head como dado (`git show`), roda o `scripts/verificar_workflows.py` da base e falha com a linha exata do erro. O verificador vem da base; o head não é executado nem vai para checkout.
   - `sdd.yml`: passo PyYAML fixado em `pyyaml==6.0.3`; selftests do helper e do verificador; `paths` ganha `.github/workflows/**`, `scripts/equipe/**` e `scripts/verificar_workflows.py`.
   - `fiscal-p8.yml`: passo PyYAML fixado, antes do Fiscalizar. Sem PyYAML, o verificador falha fechado, de propósito: sem leitor de YAML não há verificação.
   - Documentado: PyYAML é instalado por `python3 -m pip` nos dois runners (o mesmo caminho que já instala o pytest fixado).

4. **ECC arquivado** (`extras/arquivo-ecc-12-11/`, por `git mv`; `ferramentas/ferramentas.py`, `ferramentas/test_ferramentas.py`, `ferramentas/README.md`, `ferramentas/indice.json`, `ferramentas/INDICE.md`, `.agents/skills/agata-fluxo/SKILL.md`).
   - Medido: `ferramentas/fontes/ecc` tinha 757 arquivos rastreados (620 em skills, 71 agentes, 64 hooks, `COMMIT`, `LICENSE`). São 314 skills (pastas), 71 agentes: 385 peças indexadas, não 314.
   - Referências vivas: a premissa de "0 referências vivas" estava errada. Havia duas: `.agents/skills/agata-fluxo/SKILL.md` (linha 54) e `ferramentas/README.md` (linha 5). As duas foram atualizadas. Fora de escopo, sem tocar: `extras/arquivo-skills-12-11/agata-ferramentas/SKILL.md`, arquivo morto que aponta o caminho antigo.
   - `ALTERACOES.md` tinha só entradas do ECC; foi junto para o arquivo, com os caminhos relativos à pasta.
   - `ferramentas.py`: `FONTES` sem `ecc`. Reindexado: 411 peças viram 26 (11 do Agata, 15 do superpowers).
   - Testes: `test_ecc_fora_da_caixa` novo; `test_quarentena` passa a chamar `tema_de()` (antes dependia de nomes que saíram do índice e ficaria vazio); `test_fontes_presas_a_commit` só o superpowers.
   - `extras/arquivo-ecc-12-11/LEIA-ME.md` novo, no padrão de `extras/arquivo-skills-12-11/`.

5. **ONDE_ESTAMOS: linhas superadas contam como lote aberto** (documentado; nenhum código alterado nesta proposta).
   - `lotes_abertos` não existe no main. Medido com `git log --all -S lotes_abertos`: só o commit `0cc45f7f`, na branch `proposta/sincronia-12-11`, não mesclada.
   - Nele, `lotes_abertos` conta as linhas cujo estado é `proposta`. As linhas `pacote-mecanico-12-11` e `skills-consolidadas-12-11` ainda estão com esse estado; a linha de correção nova não muda o estado das antigas. Hoje as duas são contadas como abertas.
   - Regra proposta, mecânica, sem ler texto livre: lote aberto = estado `proposta` **e** `propostas/<nome>.diff` no topo de `propostas/`. Propostas que foram para `superadas/` ou `aplicadas/` saem sozinhas.
   - Implementar dentro de `sincronia-12-11`, antes da assinatura dela. Nenhuma linha de `ONDE_ESTAMOS.md` foi editada aqui.

## Partes que tocam o P-8 (quarentena)

Caminhos de comportamento neste diff, todos cobertos pelo mesmo `.diff` assinado: `.agents/skills/agata-fluxo/SKILL.md`, `.githooks/pre-commit`, `.github/workflows/fiscal-p8.yml`, `.github/workflows/sdd.yml`, `scripts/ci_sdd_local.sh`, `scripts/equipe/ancora_indice.py`, `scripts/p8_verificar_pr.sh`, `scripts/testar_turno.py`, `scripts/turno.py`, `redesign/router/spec/acceptance.json`, `redesign/router/spec/spec.md`. Fora da quarentena: `ferramentas/*`, `extras/arquivo-ecc-12-11/*`.

## Decisões pendentes (Humano)

1. **Ordem.** Este diff depende de `fiscal-yaml-12-11` aplicado antes: o 2c e o `.github/workflows/fiscal-p8.yml` editado partem do texto que ele cria.
2. **Item 5.** Recomendo a regra entrar na `sincronia-12-11`. A alternativa é esperar essa proposta para o gerador dela.
3. **Marcas de notificação.** Ficou de fora `<system-reminder>`, que a varredura do transcrito (`scripts/equipe/contar_turnos.py`) exclui. Motivo: se um prompt começasse com esse bloco, todo turno do Humano congelaria. Confirmar.
4. **Risco residual do item 1.** Uma mensagem do Humano que comece exatamente com uma das marcas não avança o t, e a auditoria não acusa. Aceito pela mesma regra do começo do texto.
5. **Não medido ao vivo.** O campo `prompt` do payload do UserPromptSubmit segue a documentação de hooks do Claude Code, mas não foi observado nesta sessão. Medir depois de aplicar: uma notificação real de agente não pode mover o t (`python3 scripts/turno.py atual --sessao <id>` antes e depois).
6. **PyYAML 6.0.3 fixado** nos dois workflows. Confirmar a versão.

## Observação de configuração (não alterada)

`core.hooksPath` vem da configuração compartilhada do repositório (`git config --show-origin`: `/home/orusoua/agata/.git/config`) e aponta para `/home/orusoua/agata/.githooks`, a cópia viva. Um commit feito numa worktree roda os hooks da cópia viva, não os desta worktree. Por isso os testes do pre-commit foram feitos num clone de teste, com o hook copiado para `.git/hooks`.

## Definição de pronto (DoD)

- [x] `diff_limpo.py` no `.diff`: OK (nenhum hunk em bloco ANCORA-SHA).
- [x] `verificar_workflows.py --diff` contra a base (com fiscal-yaml): OK, 3 workflows, YAML válido e sem chave repetida.
- [x] `git apply --check` limpo sobre base mais fiscal-yaml; ida e volta: aplicar e regerar `git diff -M` reproduz o `.diff` byte a byte.
- [x] Item 2 reproduzido e consertado ponta a ponta (clone de teste; commit abortado, commit seguinte barrado com o hook original, passa com o conserto).
- [x] Item 3: head com `name:` repetido barrado no 2c com a linha exata; head com comentário passa no 2c.
- [x] Renomeações fora do escopo do P-8 (0 de 1514 caminhos).
- [ ] Suíte local (`uv run --offline --with pytest bash scripts/ci_sdd_local.sh`): ver "Estado de verificação".
- [ ] PR de proposta com CI verde e merge com `--match-head-commit` no head verificado (o registro é escrito aqui, com número no merge).
- [ ] Assinatura do Humano no terminal, depois do merge.
- [ ] Aplicação (PR `aplica/*`) passa pelo `diff_limpo` e pela trava.

## Apetite

Uma proposta, uma assinatura. Nada além destes caminhos: sem skill nova, sem mudança em `PROJETO.md` nem `PROTOCOLOS.md`, sem `ONDE_ESTAMOS.md` (fica para a sincronia).

## Reversão

- Depois da aplicação: `git revert` do commit de aplicação, ou `git apply -R` do `.diff` (as renomeações voltam sozinhas).
- Âncora: remover a linha do `scripts/equipe/ancora_indice.py` em `.githooks/pre-commit`; o resto do hook continua como antes.
- ECC: voltar à caixa exige outra proposta (P-8), não `git mv` por conta própria.

## Assinatura (depois do merge deste PR, no terminal do Humano)

Depois de `fiscal-yaml-12-11` aplicado:

```
git -C ~/agata pull --ff-only
bash ~/agata/scripts/aprovar.sh correcoes-12-11 "correções de 12/11: notificação não conta turno, âncora staged devolvida ao HEAD, CI confere workflows, ECC arquivado"
```

Nenhum agente roda `aprovar.sh`. O `APROVADO-` não existe agora.

## Estado de verificação

Clone de teste, a partir de `origin/main` mais fiscal-yaml (`6955967f`, commit de base do clone): diff aplicado com `git apply`, ida e volta idêntica; `diff_limpo.py` OK; `verificar_workflows.py --diff` OK; `git apply --check` limpo. `p8_verificar.sh` não foi rodado até o fim: exige `APROVADO-`, que não existe nem deve existir antes da assinatura; as etapas 4 a 6 foram feitas à mão.

Suíte local, `PY_YAML=/usr/bin/python3 uv run --offline --with pytest bash scripts/ci_sdd_local.sh` na worktree (com fiscal-yaml aplicado e as correções): **`CI LOCAL: TUDO OK`**, 46 passos OK, 0 falhas, exit 0. Inclui os selftests novos (`ancora_indice.py`, `verificar_workflows.py`) e `testar_turno.py` (47 testes).

Não rodado: `aprovar.sh` (não é do agente) e `aplicar.py` de ponta a ponta (exige `gh` e a chave de assinatura).

---

# Parte original: nova-versao-lote2-12-11


**Nome para assinatura:** `nova-versao-lote2-12-11`
**Base:** `origin/main` (9981cbb8).
**Substitui:** `nova-versao-lote2-20261106`, que está quebrada: `git apply --check` falha em `redesign/nova_versao/tests/test_nova_versao.py:59` (a spec v2 acrescentou um teste nesse trecho) e `reverter` não existia em `nv.py`. Nada do arquivo antigo foi reaproveitado como está.
**Arquivos que o diff altera:** `redesign/nova_versao/nv.py`, `redesign/nova_versao/tests/test_nova_versao.py`, `redesign/nova_versao/spec/spec.md`, `redesign/nova_versao/spec/acceptance.json`, `redesign/nova_versao/spec/criterion-drift.md`, `redesign/nova_versao/spec/evidence.json`.

**Diff:** `propostas/nova-versao-lote2-12-11.diff`
**sha256 do diff:** `281292742e04f76cecb1466d998ccee501220ed0162c21c0a4363ca0f51712fe`

## Resumo

A intenção do lote 2 é a reversão: arquivar os dados da nova versão e remover só o cache. Esta proposta a refaz sobre `origin/main` e a alinha à spec v2 (`nova-versao-spec-v2-unificada-09-11`, aplicada):

- `nv.py reverter [dest]` arquiva `AGATA_NV_DIR` num `.tar.gz` datado, em modo `x` (nunca sobrescreve), e só depois remove o cache derivado (`AGATA_NV_CACHE` ou `~/.cache/agata/nova-versao`). Os dados nunca são apagados por este código.
- Recusas (`ValueError`) antes de qualquer ação: variável vazia; cache que não é pasta derivada isolada; cache que contém o repositório ou o diretório atual; destino dentro dos dados, do cache ou do repositório. A última é nova em relação à proposta de 06/11, porque a spec diz "pacote fora do repo".
- O critério "a reversão não apaga `AGATA_NV_DIR`; só remove o cache" sai do bloco "Sem teste ainda" e vira checkbox, com entrada em `acceptance.json` apontando para o teste.

## Relação com a spec v2

- **A7 (reversão):** sai do bloco "Sem teste ainda" e entra como checkbox com comando. Responde à pendência 2 da spec v2 para este critério.
- **A6 (painel de chaves):** continua em "Sem teste ainda". O código do painel não está nesta proposta: depende da exceção à regra do `.env`, que o Humano aprova na assinatura (pendência 1 da spec v2).
- **"Migração e reversão" da spec:** implementado o que cabe ao `nv.py` (arquivar dados, remover só o cache). O revert do commit de aplicação continua sendo passo à parte, como diz a spec.

## O que muda

- `nv.py` (+57): `CACHE_PADRAO`, `_cache()`, `_dentro_ou_igual()`, `reverter()`; `main` aceita `reverter`; uma linha de uso no docstring.
- `tests/test_nova_versao.py` (+109): classe `ReversaoTests` com 11 testes (1 do critério e 10 de recusa e de caminho). A home é falsa por mock, então nenhum teste toca `~/.cache`. `import nv` fica no topo do módulo, antes do mock, para `CACHE_PADRAO` não capturar a home falsa. O teste `test_valores_de_fabrica_e_quatro_categorias_da_spec` da spec v2 fica intacto.
- `spec/spec.md` (+1 checkbox, −1 linha em "Sem teste ainda"): o texto da checkbox é idêntico ao do `acceptance.json`.
- `spec/acceptance.json` (+9): uma entrada, `ReversaoTests::test_reversao_nao_apaga_dados_so_remove_cache`.
- `spec/criterion-drift.md` e `spec/evidence.json`: regenerados pelo ciclo SDD (`runner.py cycle`). São necessários: o gate de drift falha se `spec.md` mudar e o drift não mudar no mesmo commit, porque o drift não pode ser mais antigo que o spec. Em `evidence.json`, além de tempos e datas, entra a entrada do novo critério (`pass`, `returncode` 0).

Estatística (`git diff --stat`): 6 arquivos, 208 inserções e 18 remoções.

## Definição de pronto (DoD)

- [x] `pytest redesign/nova_versao/tests`: 52 passam (16 em `test_nova_versao.py`, 11 delas de reversão). Medido na worktree e numa cópia de `origin/main` com o diff aplicado por `patch -p1`.
- [x] Mutação: `shutil.rmtree(dados)` inserido antes da remoção do cache faz `test_reversao_nao_apaga_dados_so_remove_cache` falhar. Código restaurado e conferido com `cmp`.
- [x] `uv run --offline --with pytest bash scripts/ci_sdd_local.sh`: "CI LOCAL: TUDO OK", 43 passos OK, 0 falhas.
- [x] `scripts/gate_spec_sync.py`: 0 FALHA. Resta 1 AVISO que já existia (alexandria, dívida conhecida).
- [x] `scripts/equipe/diff_limpo.py` no `.diff`: OK.
- [x] `git apply --check` contra `origin/main` (9981cbb8): sem erro. O diff aplicado numa cópia limpa reproduz os 6 arquivos byte a byte.
- [x] Ciclo SDD da nova versão: `SPEC GATES: OK`, `ANCHOR: OK`.
- [ ] Revisão independente (agata-revisor): não feita.
- [ ] Assinatura do Humano.

## Apetite

Pequeno: um subcomando, uma classe de testes e um critério. Ficam de fora o painel de chaves e o lote 6.

## Reversão

- **Desta proposta:** o `git revert` do commit de aplicação tira `reverter`, os testes e o critério. Este código não roda sozinho: só age quando alguém chama `nv.py reverter`.
- **Da operação `nv.py reverter`:** remove só o cache e arquiva os dados num `.tar.gz` fora do repo. Não apaga nem restaura nada. A ordem é arquivar antes de remover, então, se o arquivamento falhar, o cache continua. Se o `tar` falhar no meio, fica um `.tar.gz` parcial (não testado).

## Não medido

- Revisão independente (agata-revisor): não feita.
- CI no GitHub: não rodou. Só o local, com `uv` offline.
- `nv.py reverter` contra os dados e o cache reais: não rodou. Os testes usam pasta temporária e home falsa. Não foi lido nem tocado nada fora do repo, nem `~/.local/share/agata/nova-versao` nem `~/.cache/agata/nova-versao`.
- Trava: o arquivamento não pega o flock do ledger. Rodar com o sistema parado (sistema sob demanda, decisão de 29/10).
- Falha no meio do `tar`: não testada.
- Evento no ledger para a reversão: não há. Gravar a reversão no ledger seria passo à parte, porque mudaria os dados depois do arquivo.

## Ao aplicar

Recomendação, não feita: depois da aplicação desta proposta, mover `propostas/nova-versao-lote2-20261106.diff` e `propostas/nova-versao-lote2-20261106.md` para `propostas/superadas/`.

## Assinatura (só o Humano)

Depois do merge desta proposta, o Humano assina com `bash scripts/aprovar.sh nova-versao-lote2-12-11`. A assinatura fica amarrada ao sha256 acima. O executor não assina e não aplica.
