# Spec — Painel operacional

## Jornadas críticas

1. O Humano abre o painel local e vê, por aba, o que o sistema mede agora; o que não tem medição aparece como não medido.
2. O Humano confere a âncora e roda os critérios de aceite de cada componente na aba SDD, com confirmação em dois cliques.
3. O Humano aprova no painel as ações do Conselho; nada é enviado sem a aprovação explícita.

## Contrato

- O servidor escuta só em 127.0.0.1, recusa `Host` diferente e recusa origem cruzada nas rotas de API (as rotas da extensão são a exceção declarada).
- `Content-Security-Policy` com `script-src 'self'`: todo JavaScript fica em arquivo externo, nunca inline.
- `GET /api/qualidade-llm` devolve indicadores medidos; item sem medição vem como `unknown` e `não medido`.
- `GET /api/sdd/estado` lista os componentes ancorados, seus critérios e o estado da âncora.
- `POST /api/sdd/executar` aceita só `{acao: ancora|criterios, componente}` de componente ancorado, exige JSON, origem igual e roda um por vez; os comandos do manifesto precisam ser `pytest -q redesign/...`.
- `GET /api/medicoes/estado` e `POST /api/medicoes/executar` rodam só `medir_recuperacao.py` (lexical ou `--semantico`) e `medir_contexto_efetivo.py` (tarefa `agulha`, `varias`, `rastreio` ou `agregacao`, de lista fechada, com `raciocinio` `desligado` ou `ligado`), um por vez e em segundo plano; o modelo da medição de contexto precisa estar na lista de tags do Ollama local; resultados ficam fora do repositório (`AGATA_MEDICOES_DIR`).
- `GET /api/nova-versao/estado` e `POST /api/nova-versao/executar` mostram e operam a nova versão (Experimento GPT, lote 1): ações de lista fechada (`iniciar`, `indexar`, `consultar`, `skills`, `classificar`, `fotografar`, `salvar_orcamento`, `gravar_chave`, `remover_chave`, `ajustar_conexao`, `adicionar_provedor`, `testar_rotas`, `cancelar_teste` e, no lote 3, `salvar_politica`, `ver_reservado`, `revisar_reservado`, `rotas_disponiveis`, `avaliar`, `medir_recuperacao`, `cancelar_avaliacao`, `ver_execucao`), uma por vez; a consulta tem até 300 caracteres e só vira pacote de evidência; o orçamento só aceita os campos e limites de `redesign/nova_versao/orcamento.py` e cada mudança vira evento no ledger; dados fora do repositório (`AGATA_NV_DIR`). A chave de API digitada em Conexões vai para o cofre de `redesign/conexoes/segredos.py` e nenhuma resposta do painel a devolve; o campo é `password` e é limpo ao enviar. As páginas da nova versão usam só classes de `nova_versao.css` (a CSP tem `style-src 'self'`, que ignora atributo `style`); a Avaliação recusa o reservado sem revisão do Humano e sem política fixada, e o estado nunca traz o gabarito.
- A navegação lateral agrupa as 23 páginas em Panorama, Conselho e quatro submenus recolhíveis (Sistema, Memória e conhecimento, Qualidade, Nova versão); o submenu da página aberta fica expandido.
- A aba SDD também lista os projetos externos registrados em `config/sdd/*.json` e roda o ciclo deles (`POST /api/sdd/executar` com `acao: projeto`); só nome de descritor existente, e o manifesto do projeto só pode ter `pytest` com alvos relativos.
- Proposta, assinatura, PR e merge não são executados pelo painel.

## Critérios de aceite

- [ ] a página não tem script inline por causa da CSP
- [ ] leituras de API recusam origem cruzada
- [ ] a verificação de proposta é só leitura de origem local
- [ ] o indicador sem medição sai como não medido
- [ ] a execução do SDD recusa ação e componente fora da lista
- [ ] a execução do SDD recusa comando fora do padrão pytest
- [ ] o menu agrupa as páginas em submenus sem perder nenhuma
- [ ] a aba SDD lista e roda projetos externos de config/sdd e recusa o que não está lá
- [ ] a medição recusa ação e modelo fora da lista e roda com argumentos fixos
- [ ] o indicador de recuperação usa a medição salva e volta a não medido sem ela
- [ ] a nova versão recusa ação, consulta e orçamento fora do contrato e registra a mudança de orçamento
- [ ] a chave gravada pelo painel não volta na resposta nem no estado
- [ ] as páginas da nova versão não têm estilo inline porque a CSP o bloqueia
- [ ] a avaliação pelo painel respeita revisão, política e não expõe o gabarito no estado

## Desenho e alternativas

Servidor HTTP da biblioteca padrão com módulos pequenos por assunto (`armazem`, `relogio`, `qualidade_llm`, `sdd_painel`). Alternativa descartada: framework web; aumentaria a superfície sem necessidade. Alternativa descartada: executar `proposal` e o handoff do GitHub pelo painel; são ações externas e ficam com o Humano.

## Implementação e testes

Testes em `test_painel.py`, `test_qualidade_llm.py`, `test_sdd_painel.py`, `test_nova_versao_painel.py`, `test_relay_catalog.py` e `test_conselho_rede.py`. Cada critério acima está ligado a um teste em `spec/acceptance.json`.

## Migração e reversão

Sem migração de dados. Reversão por revert do commit; o painel não guarda estado além do cache em `~/.cache/agata/painel/`.

## Riscos e dependências

O `pytest` precisa estar no PATH do serviço para o painel medir critérios; sem ele a execução devolve não medido, não falha em silêncio. A spec descreve o contrato observado em 03/11/2026.

## Código

- `server.py`
- `armazem.py`
- `relogio.py`
- `conselho_rede.py`
- `relay_catalog.py`
- `qualidade_llm.py`
- `sdd_painel.py`
- `medicoes_painel.py`
- `nova_versao_painel.py`
- `nova_versao.js`
- `nova_versao.css`
- `abrir.js`
- `app.js`
- `prototipo.js`
- `prototipo.html`
- `index.html`
- `prototipo.css`
- `styles.css`
- `README.md`
- `test_painel.py`
- `test_qualidade_llm.py`
- `test_sdd_painel.py`
- `test_menu_painel.py`
- `test_medicoes_painel.py`
- `test_nova_versao_painel.py`
- `test_relay_catalog.py`
- `test_conselho_rede.py`
- `conselho-rede/`
- `relay-extension-v2/`
- `operator_console/`
- `assets/`
