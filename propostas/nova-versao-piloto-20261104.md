# Proposta `nova-versao-piloto-20261104` — nova versão do Agata (Experimento GPT), lote 1

**O que é, em português comum:** primeiro passo da nova versão que você aprovou ((077), "Essa será a nova versão do agata ok"). Esta proposta põe por escrito o desenho inteiro, com nove componentes, e liga em sombra os que não gastam inferência:
- **Alexandria:** acervo do repositório com origem e hash, consulta com evidência e sugestão de skills;
- **metacognição:** o antes e o depois de cada turno;
- **corpo operacional:** fotografia da Máquina e saúde.

Tudo aparece no painel, num grupo novo, "Nova versão", com quatro páginas. Nada muda na resposta da Seth. A sombra do gateway nasce desligada. Nenhum serviço, porta ou timer novo.

**Origem:** leitura integral de `~/Área de trabalho/Experimento GPT/`: diário `conclusoes.md` 001–080, Alexandria, metacognição, avaliação, contrato, fundamentos, inventário, matriz de redundância, skill, briefings, fontes, transcrição e scripts da auditoria. Plano aprovado pelo Humano em 04/11/2026, com estas decisões:
- acervo só do repo, com pastas de trabalho próprias;
- orçamento configurável pelo painel;
- F0 e F1 numa assinatura.

## O que entra

| Arquivo | O quê |
|---|---|
| `redesign/nova_versao/` | spec-mãe (`spec/spec.md`, `brainstorm.md`, `decision.md`, `acceptance.json`), `eventos.py` (ledger único sobre o `evidence_ledger`, chave idempotente, transição das sete palavras), `orcamento.py` (provedores e tetos; padrão só local), `nv.py` (CLI e selftest), testes |
| `redesign/alexandria/` | `acervo.py`: pastas de trabalho, snapshot por commit, índice SQLite/FTS5 derivado, consulta com pacote de evidência, drift por hash. `skills.py`: índice de skills separado, seleção que não executa. Spec e testes |
| `redesign/metacognicao/` | `previo.py`: tipo, atualidade, privacidade, risco, "problema" ambíguo (014) e limite de perguntas (013). `posterior.py`: apto, parcial, inconclusivo, bloqueado ou aguardando o Humano. Spec e testes |
| `redesign/corpo/` | `fotografar.py`: só GET e leitura; separa instalado, anunciado, elegível, testado, em fila e pronto. `saude.py`: cinco estados. Spec e testes |
| `redesign/router/sombra_nova_versao.py` + 4 linhas em `seth_gateway.py` | sombra no padrão de `sombra_capacidade.py`, com `SETH_SOMBRA_NOVA_VERSAO=1`; grava hash, nunca o texto |
| `redesign/painel_operacional/` | `nova_versao_painel.py`, `nova_versao.js` (externo, CSP), quatro páginas em `prototipo.html`, rotas `GET /api/nova-versao/estado` e `POST /api/nova-versao/executar`, spec e teste |
| `scripts/busca_texto.py` | `--json` aditivo (baseline léxico com sha), selftest ampliado |
| `ferramentas/indice.json`, `ferramentas/INDICE.md` | regenerados por `ferramentas.py reindexar`. Estavam defasados: faltavam `agata-llm-fundamentos` e `design-taste-frontend`. O `test_ferramentas.py` pegou o defeito e passa a rodar na CI |
| `.agents/skills/agata-carregar/SKILL.md` | achado 3 da conclusão (021): o texto chamava de read-only um script que grava cache do `ls-remote` em `~/.cache/agata/` |
| `.github/workflows/sdd.yml`, `perimetro.yml` | testes, âncora, critérios e ciclo SDD dos componentes novos; selftests da sombra, do `nv.py` e do `busca_texto` |
| `PROJETO_REFERENCIA.md`, `redesign/README.md` | seção "Nova versão (Experimento GPT)" e linhas da tabela. `PROJETO.md` fica intacto: 47.929 de 48.000 bytes de teto |

## Lote 0: achados da conclusão (021), conferidos hoje

1. Instruções de assinatura divergentes: **não reproduzido**. `propostas/README.md` e `AGENTS.md` coincidem.
2. Atualização que descarta mudanças se o backup falhar: **não reproduzido**. `scripts/atualizar.sh` recusa árvore suja e manda usar `git revert`.
3. `agata-carregar` com descrição errada: **confirmado**, corrigido neste lote.

## Evidência (medida no worktree, 04/11/2026)

- **Testes:** pytest com 138 testes verdes. São os suítes atuais da CI mais os componentes novos e `ferramentas/test_ferramentas.py`. Depois de aplicar este `.diff` sobre `origin/main`, 95 testes dos componentes e do painel continuam verdes.
- **SDD:** âncora OK nos 10 componentes. Critérios: 27/27 `pass`, sem drift. O ciclo SDD completo da spec-mãe terminou com código de saída 0.
- **Selftests:** gateway, `sombra_nova_versao`, `nv.py`, `busca_texto` e `sombra_capacidade`, todos OK.
- **Acervo real:** HEAD `6666813d`, com 733 objetos, 7287 trechos e 349 skills. Indexar leva cerca de 0,2 s. "suspend travamento" devolve (99) e (124) nos dois primeiros lugares, com commit e sha. Com o e5 fora do ar, a busca semântica degrada para léxico e o aviso aparece.
- **Painel no navegador:** as quatro páginas carregaram, a consulta e a classificação rodaram e o console ficou sem erro.
- **Corpo:** estado `normal`. Gateway, verificador, embeddings, Laya e painel estavam inativos, por estarem sob demanda.

## Não medido

- O ganho da nova versão contra o caminho atual: isso é o lote 3, com split reservado.
- A sombra ligada no gateway vivo. O gateway está inativo; a sombra está coberta por teste de unidade e selftest.
- A qualidade da recuperação em paráfrases.
- Falsos positivos do prévio, que funciona por regex.

## Achado sem mudança neste lote

A nota de `PROJETO_REFERENCIA.md`, na Fronteira de recusas, diz que o vault "não tem embedding". Hoje `parecidas`/`afinidade` vêm do índice semântico ((670)). Fica registrado para uma correção própria.

## Próximos lotes, cada um com assinatura própria

- **Lote 2:** redundância por capacidade (teste funcional por rota, dentro do orçamento do painel) e coordenação (`task_id`, cancelamento, fila de GPU).
- **Lote 3:** avaliação: 30 tarefas, 12 casos obrigatórios, gabarito revisado por você e registro por execução comum aos medidores.
- **Lote 4:** integração protegida, item por item, só com ganho medido.

## Reversão

Revert do commit de aplicação e remoção de `~/.local/share/agata/nova-versao` e `~/.cache/agata/nova-versao`.
