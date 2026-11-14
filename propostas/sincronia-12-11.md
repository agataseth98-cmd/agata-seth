# Sincronia: fonte única, porquês, início de sessão e maxTurns (`sincronia-12-11`)

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
