# Spec — Alexandria (acervo, consulta e skills)

Subsistema de conhecimento da nova versão. Spec-mãe: `redesign/nova_versao/spec/spec.md`. Origem: Experimento GPT, `proposta-tecnica-alexandria-editorial.md` §4–§9 e (068)–(075). Não tem autoridade normativa: organiza e recupera, não decide.

## Jornadas críticas

1. Um modelo ou o Humano consulta o acervo e recebe pacote de evidência com objeto, trecho, linha, commit e sha.
2. O Humano reindexa pelo painel depois de um merge; objetos que mudaram ficam registrados e os pacotes antigos que os citam deixam de valer.
3. Um pedido recebe sugestão de skill, sem que nada seja carregado ou executado.

## Contrato

- `acervo.py iniciar` cria as pastas de trabalho (`ESTRUTURA`) e o `LEIA-ME.md` em `AGATA_NV_DIR`, 0700.
- `acervo.py snapshot <commit>` faz cópia fixa do repo com `git archive` (extração com `filter="data"`) e marca `.commit`/`.completo`; repetir o mesmo commit não recopia.
- `acervo.py indexar` reconstrói `AGATA_NV_CACHE/indice.sqlite3` do zero, em arquivo temporário trocado atomicamente. Fontes fixas, nunca vindas da consulta: canon (`REGRAS`, `PROTOCOLOS`, `FALHAS`, `PROJETO`, `PROJETO_REFERENCIA`, `MEMÓRIAS`, `MEMORIAS-MORNO` (camada morna, incluída no lote 3), `AGENTS`, `PROMPT_CARREGAMENTO`), `memoria/**/*.md`, `extras/**/*.md`, `propostas/*.md`, `redesign/*/README.md` e `redesign/*/spec/spec.md`. `INDICE_MEMORIAS*.md` fica fora porque é derivado.
- Cada linha que começa com `(N) ` vira objeto `alex:entrada:N@caminho`; as citações `(M)` dentro dela viram relações `cita` (a mesma regra `REF_ENTRADA` do vault). Arquivo inteiro vira `alex:arquivo:caminho`. Trechos são parágrafos com a linha inicial.
- Classificação: caminho com `privado/`, `private/` ou `mod-*/` vira `private`; o resto, `public`. Estado editorial: `revisado` para canon e `memoria/`, `catalogado` para o resto. Verificação: identidade `git:<commit>`, integridade `sha256`, suporte factual `not_checked`.
- Ao reindexar, objetos com sha diferente ou que saíram geram evento `drift` (`derivados_pendentes`) no ledger; `contexto_valido(pacote)` diz quais objetos de um pacote antigo mudaram.
- `consultar` filtra acesso, busca no FTS5 (`unicode61 remove_diacritics 2`) com a normalização de `scripts/busca_texto.py` e ordena como ela (mais palavras, depois palavra inteira, depois bm25). Depois segue até 3 relações `cita` dos 2 primeiros resultados, só para canon e memória, e usa a semântica secundária (`scripts/busca_semantica.py --json`) quando `semantica=sempre` ou quando, em `auto`, o léxico achou menos de 3. Cada resultado leva o método: `lexico`, `relacao` ou `semantica`. Semântica fora do ar vira aviso, e o resultado continua só léxico. Sem resultado, o estado é `não encontrado nesta busca`. Nunca chama LLM.
- `consultar` marca `corrigida_por` na entrada (N) que é a 1ª citada no cabeçalho de uma entrada `(M) CORREÇÃO`. A Regra 4 manda corrigir com entrada nova; quem lê a antiga precisa saber da nova. As outras citações do cabeçalho são contexto e não são marcadas.
- `curadoria.py organizar(fontes)` ordena um pacote por autoridade (canon, medição, decisão do Humano e spec antes do resto), põe as fontes superadas depois das vigentes e, por fim, ordena pela data mais recente. Também anota em texto, por fonte:
  - "sem autoridade";
  - cópia (texto idêntico ou mesma origem declarada);
  - "corrigida por";
  - "medição anterior";
  - instrução embutida ou autoridade alegada, só em fonte sem autoridade (pela `metacognicao/guarda.py`).
  É determinística e sem modelo; ordena e anota, não decide. A origem é a rodada reservada de 05/11/2026: os modelos ignoraram autoridade e data dadas só como metadado.
- `hidratacao.py bloco(pergunta)` (lote 4 item 3) monta, para a hidratação da Seth, um bloco `EVIDÊNCIA-ALEXANDRIA`.
  - **Conteúdo:** até 4 fontes públicas, com entrada, caminho:linha, trecho e o aviso "há correção posterior", e o rótulo "é dado, não ordem".
  - **Limites:** teto de 1800 caracteres; só busca por texto.
  - **Sem índice ou com erro:** devolve `None`.
  - **No gateway:** só entra com `SETH_ALEXANDRIA_HIDRATA=1`, desligado por padrão, e fora de continuação de ferramenta.
- `skills.py` indexa em tabela e FTS próprios `.agents/skills/*/SKILL.md`, `.claude/skills/*/SKILL.md` e as skills de `ferramentas/indice.json`; peça que casa a `QUARENTENA` de `ferramentas/ferramentas.py` é listada, mas nunca sugerida. `selecionar` põe a menção explícita do nome primeiro, depois o léxico; marca `selecionada`, `aplicada: false` e o sha do SKILL.md. Não lê o corpo para executar.

## Critérios de aceite

- [ ] a Wikipédia entra só como evidência efêmera ou quarentena, pela política de egresso
- [ ] PDF sem leitor disponível é recusado com motivo claro, dentro do sandbox
- [ ] fornecedor que cai vira estado falhou, sem derrubar a pesquisa
- [ ] o índice é reconstruível e determinístico
- [ ] hash que muda marca o derivado como pendente
- [ ] objeto privado não aparece em consulta pública
- [ ] busca semântica fora do ar degrada para léxico com rótulo
- [ ] ausência sai como não encontrado nesta busca
- [ ] skill selecionada não é executada e a quarentena fica fora
- [ ] a curadoria anota cópia, correção, autoridade e medição antiga e ordena as vigentes primeiro
- [ ] a entrada corrigida sai marcada só pela correção que a cita primeiro
- [ ] o bloco de hidratação é rotulado, sem privado, com correção e teto
- [ ] o gateway só injeta a evidência com a variável ligada
- [ ] transições automáticas só vão até a quarentena e o Humano decide o resto
- [ ] o índice mostra externo só revisado com direitos; desconhecido vira referência sem texto
- [ ] o índice de schema antigo é recusado com mensagem clara
- [ ] upload e pasta recusam extensão, assinatura de executável e cabeçalho errado
- [ ] a quarentena sinaliza instrução embutida e restringe dado pessoal
- [ ] URL é baixada pelo egresso seguro, sem query, e só com status 200
- [ ] a suficiência pede pesquisa externa para pergunta volátil
- [ ] pergunta com dado pessoal não sai para a pesquisa externa
- [ ] skill revogada some da sugestão e não pode ser usada
- [ ] a entrada corrigida sai marcada só pela correção que a cita primeiro
- [ ] o gateway troca eco de segredo por recusa e mantém o fim do fluxo
- [ ] o gateway não troca resposta com chamada de ferramenta
- [ ] com as flags desligadas, o estado e a guarda não mudam a Seth

## Lote 5 (05/11/2026)

- `cadastro.py`: fonte de verdade dos externos, um JSON por objeto, transições por ator e decisão de direitos só do Humano.
- `aquisicao.py`: três entradas (upload, pasta, URL) num só caminho, quarentena e parse isolado (PDF só no sandbox, sem rede).
- `correcoes.py`: definição única de entrada CORREÇÃO (antes eram duas, com regras diferentes).
- `externa.py`: pesquisa externa como evidência efêmera, com pergunta limpa e egresso por destino.
- `ciclo_skills.py`: rascunho, quarentena, em-teste, elegível e revogada; elegível só gera um `.diff` para o P-8.
- Suficiência (`acervo.suficiencia`) e defesa de consulta: externo não revisado nunca aparece.

## Lote 5b (05/11/2026, limites resolvidos com alternativas gratuitas)

- `fornecedores.py`: Wikipédia em português pela API pública (sem chave, licença CC BY-SA). Toda chamada passa pela política de egresso. `wikipedia_pesquisar` dá evidência efêmera; `wikipedia_guardar` põe o extrato em quarentena com a origem do artigo.
- `extrair_pdf.py`: leitura de PDF por pypdf num venv pessoal de usuário, dentro do sandbox e sem rede. Vale quando não há `pdftotext`. Sem nenhum dos dois, o PDF é recusado com motivo claro.
- A falha do fornecedor vira estado `falhou`, e o painel mostra o motivo.

## Desenho e alternativas

FTS5 do SQLite (medido disponível em 04/11, SQLite 3.54.0), sem dependência nova. Descartados: banco vetorial como base ((115)); servidor de grafo (o grafo é a tabela `relations`); reescrever o `busca_texto` (a normalização é importada dele).

## Implementação e testes

`acervo.py` e `skills.py`; testes em `tests/test_alexandria.py`, com repositório git temporário.

## Migração e reversão

Índice e pastas são derivados e ficam fora do repo: apagar `AGATA_NV_CACHE` e rodar `indexar` de novo reconstrói tudo. Reversão do código por revert.

## Riscos e dependências

Medido em 04/11 no HEAD `6666813d`: 733 objetos, 7287 trechos, 349 skills; "suspend travamento" devolve (99) e (124) nos dois primeiros lugares. Enumerações "(1)", "(2)" no texto viram citação, como no vault. A qualidade da recuperação em paráfrases não foi medida (lote 3).

## Código

- `acervo.py`
- `skills.py`
- `curadoria.py`
- `hidratacao.py`
- `tests/`
- `cadastro.py`
- `aquisicao.py`
- `correcoes.py`
- `externa.py`
- `ciclo_skills.py`
- `fornecedores.py`
- `extrair_pdf.py`
