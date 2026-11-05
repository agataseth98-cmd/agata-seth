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
  - "medição anterior".
  É determinística e sem modelo; ordena e anota, não decide. A origem é a rodada reservada de 05/11/2026: os modelos ignoraram autoridade e data dadas só como metadado.
- `skills.py` indexa em tabela e FTS próprios `.agents/skills/*/SKILL.md`, `.claude/skills/*/SKILL.md` e as skills de `ferramentas/indice.json`; peça que casa a `QUARENTENA` de `ferramentas/ferramentas.py` é listada, mas nunca sugerida. `selecionar` põe a menção explícita do nome primeiro, depois o léxico; marca `selecionada`, `aplicada: false` e o sha do SKILL.md. Não lê o corpo para executar.

## Critérios de aceite

- [ ] o índice é reconstruível e determinístico
- [ ] hash que muda marca o derivado como pendente
- [ ] objeto privado não aparece em consulta pública
- [ ] busca semântica fora do ar degrada para léxico com rótulo
- [ ] ausência sai como não encontrado nesta busca
- [ ] skill selecionada não é executada e a quarentena fica fora
- [ ] a curadoria anota cópia, correção, autoridade e medição antiga e ordena as vigentes primeiro
- [ ] a entrada corrigida sai marcada só pela correção que a cita primeiro

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
- `tests/`
