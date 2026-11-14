# Spec — PROJETO.md como índice (projeto-indice)

Componente: `redesign/projeto_indice/`. Escrita antes do código (SDD, classe P4: comportamento e canon).
Origem: decisões do Humano em 12/11/2026, entrevista de 10:12, registradas no cache do Conselho (entrada 522) e na ordem da entrada 521: (1) o PROJETO.md vira índice curto (quem é o Agata, princípios, onde está cada coisa); (2) o estado vivo vira arquivo gerado pela Máquina, hidratado aos modelos e fora do canon; (3) o teto vira bloqueio mecânico no commit; (4) a nuvem lê só o índice e o estado gerado, com orientação de onde achar cada informação; (5) o histórico que sai vai para `extras/arquivo/`.

## Jornadas críticas

1. Um modelo em terminal, nuvem ou gateway abre o `PROJETO.md` e recebe em poucas linhas o que é o Agata, os princípios e, para cada pergunta, o arquivo que responde (tabela "Onde encontrar").
2. O Humano, ao ler o `ESTADO.md`, vê portas, serviços declarados, modelos que responderam, propostas abertas e bugs, todos de fontes reais, sem data nem SHA.
3. Um commit que faz o `PROJETO.md` passar do teto é recusado pelo pre-commit, com a mensagem dizendo para onde vai cada tipo de conteúdo.
4. Nenhuma decisão do Humano que estava no `PROJETO.md` antigo se perde: cada parágrafo que saiu existe, verbatim, no destino declarado, e o texto antigo inteiro está em `extras/arquivo/projeto-ate-2026-11-12.md` (sha256 registrado).

## Contrato

**Papéis depois da mudança.**

| Arquivo | Papel | Quem lê |
|---|---|---|
| `PROJETO.md` | índice: quem é, princípios, "Onde encontrar", referência | todos; a nuvem lê este e o ESTADO |
| `ESTADO.md` | estado vivo e mapa de PROTOCOLOS, gerados por `scripts/gerar_estado.py` de fontes reais; versionado; sem data e sem SHA | hidratação (`.hidrata.md`, `.hidrata-seth.md`), SessionStart, painel, nuvem |
| `PROTOCOLOS.md` | o como: mecanismos, quarentena P-8, sudo, hidratação, personalidade, Conselho, decisor, memória | o mapa das seções entra na hidratação (dentro do ESTADO); o texto de uma seção se busca pelo título; a seção "Carregar e formatos" é lida antes de responder |
| `extras/projeto-detalhe/estado-de-fundo-12-11.md` | prosa de estado (Máquinas, Cérebro, Serviços, Interface, bugs, plano vigente) que o gerador não reproduz | sob demanda |
| `extras/arquivo/projeto-ate-2026-11-12.md` | PROJETO.md anterior, byte a byte | sob demanda, histórico |

**Por que ESTADO.md é versionado.** A nuvem lê o repositório por URL (PROMPT_CARREGAMENTO.md); um arquivo só em cache da Máquina não chega lá. O `pre-commit` o regenera a cada commit, antes da hidratação, e o CI roda `gerar_estado.py --verificar`. Sem data e sem SHA no conteúdo, a mesma fonte dá o mesmo arquivo: uma diferença entre duas gerações é sempre mudança de fonte.

**Fontes do ESTADO.md.** `config/portas-agata.txt` (portas); `config/modelos-gratuitos.md`, seção "Confirmado funcionando", linhas sem `~~`; `config/servicos-agata.txt` (serviços declarados, fonte do P-9); `redesign/systemd/*.service|*.timer` com `WantedBy`/`PartOf` de `agata.target` (conferência com o manifesto); `propostas/*.diff` sem `APROVADO-` e `propostas/aplicadas/`; seção "Bugs e testes abertos" de `ONDE_ESTAMOS.md`, se existir. Hoje essa seção não existe; o ESTADO aponta para a prosa que guarda os bugs. Criar a seção é registro (fora deste lote).

**Destino de cada seção do PROJETO antigo.** `redesign/projeto_indice/destinos.json`: por seção, `padrao` (arquivo onde o texto que sai precisa existir, verbatim), `manter` (prefixos de parágrafos que ficam no índice) e `excecoes` (prefixo de parágrafo que vai para outro destino). `verificar_destinos.py` confere: (a) o histórico tem o sha256 registrado; (b) toda seção antiga está mapeada e nenhuma entrada sobra; (c) todo parágrafo que saiu aparece, normalizado (espaços colapsados), no destino; (d) todo parágrafo mantido aparece no índice.

**Teto.** `redesign/projeto_indice/teto.py`: `TETO_BYTES = 6000`. O `pre-commit` confere o `PROJETO.md` em staging (`git show :PROJETO.md`) e recusa o commit acima do teto, dizendo para onde vai cada conteúdo. O aviso de 48.000 B do `gerar-hidratacao.sh` sai. Por que 6.000: topo da faixa-alvo (3 a 6 KB). O índice medido tem 5.229 bytes; a folga cobre o bloco `ANCORA-SHA` (cerca de 1.200 B, reescrito a cada commit).

**Ponteiros.** Todo `PROJETO.md, "<seção>"` em arquivo vivo aponta para o arquivo onde a seção está agora (reapontamento mecânico, sem mudar o título). `test_nenhum_ponteiro_vivo_para_secao_que_saiu` falha se sobrar ponteiro para seção que saiu. Ficam de fora: histórico (MEMÓRIAS, morno, LOG, extras/, propostas/), o texto movido (verbatim), o bloco `ANCORA-SHA` e os dois geradores de âncora (texto que o P-8 integral reconhece).

**Manifesto de serviços (P-9).** `config/servicos-agata.txt`, formato `unidade|escopo|porta|p9|origem`. `scripts/perimetro/p09_servicos_declarados.sh` (`p9_carregar_fonte`) carrega as três listas do P-9 a partir dele, no carregamento do `perimetro.sh`. O gerador usa o mesmo arquivo. Unidade do repo com `agata.target` fora do manifesto aparece como AVISO no ESTADO.

**Painel.** `_lacunas_snapshot` lê a seção `## Serviços (boot)` do `ESTADO.md`. Unidade `oneshot` não é lacuna (mesma regra do P-9).

**Hidratação e SessionStart.** `gerar-hidratacao.sh` embute o `ESTADO.md` depois do mapa do PROJETO. O `ESTADO.md` traz o mapa das seções de `PROTOCOLOS.md` (gerado por `gerar_mapa_projeto.py`, com orientação de onde buscar o texto). O `PROTOCOLOS.md` não entra inteiro na hidratação (decisão do Humano, 12/11/2026, 16h00). `sessao_claude_contexto.sh` inclui o ESTADO no contexto de início de sessão. Gateway (`.hidrata-seth.md`) e nuvem (`PROMPT_CARREGAMENTO.md`) recebem o mesmo mapa.

**Não muda.** `ONDE_ESTAMOS.md` (registro; não recebe seção nova neste lote). `scripts/perimetro-sombra-referencia.sh` (monolito congelado de comparação do modo sombra; mexer nele anula o propósito, MEMÓRIAS, entrada de 12/11/2026 sobre a sombra). O bloco `ANCORA-SHA` e o texto dos geradores de âncora. `Nome do sistema:` continua no índice (P-21, gerador de hidratação e gerador de índice derivado leem essa linha).

## Critérios de aceite

Um teste pytest por critério, em `tests/test_projeto_indice.py` (comando em `acceptance.json`). Os que leem o índice e o ESTADO passam no estado aplicado.

- [ ] o índice tem até 6.000 bytes (teto)
- [ ] acima do teto, o pre-commit recusa o commit e diz para onde vai o conteúdo
- [ ] todo caminho citado em 'Onde encontrar' existe
- [ ] todo parágrafo que saiu do índice existe no destino declarado
- [ ] o arquivo de histórico tem o sha256 do PROJETO.md anterior
- [ ] toda seção do PROJETO anterior tem destino, e nenhum destino aponta para seção inexistente
- [ ] cada título movido existe como seção no destino (ponteiros resolvem)
- [ ] o gerador do ESTADO é determinístico: duas execuções dão o mesmo arquivo, e ESTADO.md está em dia
- [ ] o ESTADO não tem data de geração nem SHA de commit
- [ ] o ESTADO traz as portas do manifesto e os modelos da seção Confirmado funcionando, com a nota da tabela
- [ ] o ESTADO lista cada serviço do manifesto com a porta, na seção Serviços (boot)
- [ ] unidade do repo com agata.target fora do manifesto é acusada
- [ ] o ESTADO traz bugs abertos da ONDE_ESTAMOS ou aponta para a prosa que os guarda
- [ ] o P-9 carrega as listas de unidades do config/servicos-agata.txt
- [ ] o painel lê os serviços declarados do ESTADO.md, não do PROJETO.md, e oneshot não vira lacuna
- [ ] o prompt de nuvem manda ler o índice e o ESTADO, não o PROJETO inteiro
- [ ] REGRAS.md não cita critério de reabilitação inexistente como se existisse
- [ ] a hidratação traz o mapa de PROTOCOLOS (dentro do ESTADO), não o texto inteiro
- [ ] a hidratação inclui o ESTADO.md
- [ ] o SessionStart mostra o ESTADO.md
- [ ] a auditoria de turno conta como entrada conhecida o número citado no histórico movido
- [ ] nenhum ponteiro vivo cita seção que saiu do índice

## Código

- `redesign/projeto_indice/teto.py`, `verificar_destinos.py`, `destinos.json`, `tests/test_projeto_indice.py`
- `scripts/gerar_estado.py`, `config/servicos-agata.txt`, `ESTADO.md` (gerado)
- `scripts/gerar_mapa_projeto.py` (alterado: o nome do arquivo-fonte vai para o rótulo; a saída do PROJETO não muda)
- `extras/projeto-detalhe/estado-de-fundo-12-11.md`, `extras/arquivo/projeto-ate-2026-11-12.md`

Alterações em código existente: `scripts/perimetro.sh`, `scripts/perimetro/p09_servicos_declarados.sh`, `scripts/perimetro/p22_derivados_drift.sh`, `redesign/painel_operacional/server.py`, `redesign/router/auditoria_turno.py`, `scripts/testar_pacote2.py`, `scripts/sessao_claude_contexto.sh`, `scripts/gerar_indice_derivado.py` (docstring), `.githooks/pre-commit`, `.githooks/gerar-hidratacao.sh`, `scripts/ci_sdd_local.sh`, `.github/workflows/sdd.yml`, `config/caminhos-framework.txt`, `PROMPT_CARREGAMENTO.md`, `REGRAS.md` (linha 6 do bloco de MOD), `PROTOCOLOS.md` (texto movido no fim), `PROJETO.md`, e os ponteiros reapontados listados na proposta.

## Verificação antes de propor

`bash scripts/ci_sdd_local.sh` (inclui os passos do componente), `python3 scripts/gate_spec_sync.py`, `python3 redesign/projeto_indice/verificar_destinos.py`, `python3 redesign/projeto_indice/teto.py`, `python3 scripts/gerar_estado.py --verificar`.

## Migração e reversão

- Migração: cópia byte a byte do PROJETO anterior para `extras/arquivo/projeto-ate-2026-11-12.md`; seções movidas verbatim para o destino; índice reescrito.
- Reversão: `git revert` do commit de aplicação. O histórico e as seções de destino ficam (são aditivos); o `PROJETO.md` volta a ser o anterior. Nada se apaga.

## Riscos e dependências

- Hidratação medida em bytes: `.hidrata.md` 59.969 B, contra 67.182 B do HEAD (`.hidrata-seth.md`: 60.121 B). Tokens não medidos.
- O pacote mecânico e as skills (`pacote-mecanico-skills-12-11`) estão aplicados na base desta proposta. Esta proposta é sobre `main` + esse pacote.
- O teto é número, não medida de utilidade. A utilidade do índice é o que o critério "Onde encontrar" testa.
