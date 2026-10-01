# PROTOCOLOS.md — Sistema {{NOME_SISTEMA}}

O **como** das regras. `REGRAS.md` diz por quê e o quê; aqui estão comandos, formatos e procedimentos. Cada seção abre com a regra que executa. Procedimentos de contingência ficam recolhidos — abra quando precisar deles.

Se este arquivo e `REGRAS.md` divergirem, vale `REGRAS.md`, e a divergência vira entrada nova em MEMÓRIAS.

---

## Carregar e formatos
*Executa a Regra 1.*

`carregar` é o procedimento de chegar ao estado de hidratação (ver "Glossário"). O mecanismo concreto — arquivo, hook, contador — é deste projeto: `PROJETO.md`, "Memória e hidratação".

A janela mais recente de MEMÓRIAS já está no contexto (topo do corpo, logo após o marcador `ENTRADAS-NOVAS`): não use ferramenta para relê-la. Histórico além da janela: aí sim, ferramenta. Sem MEMÓRIAS na primeira vez: "modo sem memórias", e começa nova quando o Humano autorizar.

**Cabeçalho: uma forma só, nunca as duas.**

Ao `carregar`, bloco de prontidão de 3 linhas:
```
{{NOME_SISTEMA}} · modelo: <nome> · sync: <forma, ver abaixo> · <data e hora local + selo de origem>
Última entrada: (<n>) <título> — <1 linha>
<quebrado: liste em 1 linha. senão: "pronto.">
```

Em qualquer outra resposta, uma linha só:
```
{{NOME_SISTEMA}} · <modelo> · t=<n> (<base: contado no contexto / contador mecânico / prefixo compactado>) · <data e hora local + selo de origem>
```

Misturar as duas formas (`modelo:` junto com `t=`) é erro de formato.

**Data e hora.**
- `<data e hora local>` = ISO (`2026-08-14 16:33 -03`) ou regional (`14/08/2026 16:33 -03`). **Fuso é obrigatório** — sem ele a hora não localiza nada entre sessões paralelas.
- **Selo de origem, obrigatório:** `(relógio da Máquina)` quando medido · `(informado pela interface)` quando não verificável de dentro · `lacuna: sem relógio` quando não há nada a medir. Lista completa e precedência: "Regra 1.1 — Sincronização de horário", abaixo.
- **Hora não herdada.** Meça de novo a cada resposta; nunca copie do cabeçalho anterior. Hora repetida sem nova medição é a mesma falha que hora sem fonte (`FALHAS.md`, SIN-3).

**`sync:` — três formas, nunca uma quarta:**
```
sync: PASS · REGRAS=<hash8> · MEMÓRIAS=<hash8> · HEAD=<commit7>
sync: FALHA · <o que diverge, em 1 linha>
sync: não verificado · lacuna: <motivo>
```
- `<hash8>` = 8 primeiros caracteres de `sha256sum REGRAS.md` / `sha256sum MEMÓRIAS.md`, rodado agora. `<commit7>` = `git rev-parse --short HEAD`.
- **PASS** exige as três medidas feitas nesta sessão, ao vivo — nunca presumidas de resposta anterior nem copiadas de outra sessão.
- **FALHA** é PASS que falhou a checagem. **Não verificado** é não ter como medir. Não confunda os dois.

**"Última entrada" sob `sync` não verificado.** Só sob `sync: PASS` essa linha afirma o topo do canon. Fora disso, ela é "até onde a minha cópia alcança" — nunca "o canon está em (n)" (`FALHAS.md`, FAB-4). Se a leitura não for óbvia pelo `sync:`, diga qual das duas vale.

**Título de entrada de MEMÓRIAS: data do COMMIT, nunca a de escrita.** É a única data que a Máquina prova (`git log`). Vale desde (200); título antigo não se reescreve (Regra 4).

<details>
<summary>Histórico deste formato</summary>

- O bloco de prontidão tinha 4 linhas até a linha `Nonce:` sair com a aposentadoria do TES-002 — MEMÓRIAS (417).
- `sync:` substituiu o antigo `íntegro? <sim/não/não verificado>`, com a mesma exigência de evidência e um formato que dá para grepar entre sessões. Entradas antigas que citam `íntegro?` continuam válidas como estão (Regra 4).
- A data do commit no título resolveu a lacuna de (178), aberta por divergência de data no título de (177) — MEMÓRIAS (200).
- O caso de hora repetida que motivou "Hora não herdada" foi relatado por outra sessão em 23/08/2026.

</details>

---

## Regra 1.1 — Sincronização de horário
*Executa a Regra 1.*

Meça o horário de Brasília (America/Sao_Paulo) a cada cabeçalho. **Proibido:** herdar hora de cabeçalho anterior, inventar hora, deixar o campo em branco.

| Situação | Fonte | Selo |
|---|---|---|
| Modelo local, NTP sincronizado | `date` com fuso -03 | `(relógio da Máquina)` |
| Modelo local, NTP não sincronizado | `date` | `(relógio do sistema, não sincronizado)` |
| Modelo em nuvem, script funcionou | `scripts/consultar_horario.py` | `(API externa via script)` |
| Script falhou; o Humano informou a hora | a hora do Humano | `(não verificada)` |
| Sem script e sem hora do Humano; a interface mostra uma hora | a hora da interface | `(informado pela interface)` |
| API falhou ou NTP indisponível, e a única hora a medir não vem da interface nem do Humano | essa hora | `(não verificada)` |
| Não há relógio nenhum a medir | — | `lacuna: sem relógio` |

Esta tabela é a lista autoritativa dos selos. Preencher campo que não se pode medir é falha (`FALHAS.md`, FAB-2).

A hora que a interface mostra leva sempre `(informado pela interface)` — decisão do Humano em 01/10/2026, que resolveu a ambiguidade herdada do texto anterior (lá ela aparecia também como `(não verificada)` no fallback universal).

<details>
<summary>Procedimento técnico — modelo local (com shell)</summary>

```sh
timedatectl status | grep synchronized   # "yes" → relógio confiável
TZ=America/Sao_Paulo date '+%d/%m/%Y %H:%M %z'
```

</details>

<details>
<summary>Procedimento técnico — modelo em nuvem (sem shell)</summary>

- `scripts/consultar_horario.py` consulta timeapi.io com cache-busting: um parâmetro força requisição nova e contorna cache de ferramenta de extração web — MEMÓRIAS (264), (272), (273).
- **Sem fallback automático de segunda API.** A única candidata cotada (worldtimeapi.org) foi descontinuada e nunca teria funcionado: a chave de resposta no script original estava errada — corrigido em MEMÓRIAS (275). Não reintroduzir sem antes testar ao vivo a API candidata.

</details>

---

## "sync" tem preço
*Executa as Regras 2 e 4.*

Só diga `sync: PASS` com evidência de Máquina desta sessão: hash real (`sha256sum`), `git rev-parse` / `ls-tree` / `ls-remote`, ou fetch do raw comparado byte a byte — nunca hash citado de memória ou herdado de resposta anterior.

- Coerência interna do texto **não é sincronia** — é leitura atenta, e se chama assim (`FALHAS.md`, FAB-1).
- Uma cópia isolada **não prova append-only**. Isso só se prova contra o histórico do git ou um hash anterior.
- Sem evidência: `sync: não verificado · lacuna: <motivo>`.

## Verificação de canônico — ordem obrigatória
1. Na Máquina: `git ls-remote` / `git ls-tree origin/main` / `curl` do raw. Fonte superior a tudo.
2. Em modelo de nuvem com execução de código: requisição HTTP direta às URLs raw, com hash e comparação byte a byte.
3. Sem execução de código: fetch das mesmas URLs raw.

**Nunca** busca na web indexada, nunca a página HTML do repositório: servem cache e descrição estática, não o estado dos arquivos. Prefira URL pinada em SHA, que é imutável (`FALHAS.md`, SIN-2).

## Fonte canônica
Endereços concretos e o comando `atualizar` são deste projeto: `PROJETO.md`, "Memória e hidratação". A ordem de verificação é a da seção anterior.

---

## Glossário: sincronizar · carregar · hidratação · atualizar
*Quatro palavras que soam parecido e não são a mesma coisa.*

- **Sincronizar** — conferir (ou trazer) a cópia local ou em contexto contra `origin/main`, no início de toda sessão. É sobre **atualidade** da cópia; sozinho, não muda o que está injetado no contexto de nenhum modelo.
- **Hidratação** — o **estado** de ter REGRAS, PROTOCOLOS, FALHAS, PROJETO e a janela mais recente de MEMÓRIAS no contexto de um modelo. Mecanismo atual: `.hidrata.md`, gerado pelo hook pre-commit (`.githooks/gerar-hidratacao.sh`), mais o silo por modelo `.hidrata-<modelo>.md`. Quem injeta é o consumidor da hidratação — hoje o `seth_gateway` (`:20126`), a cada turno. Fora dele não há injeção automática: a sessão precisa `carregar`.
- **`carregar`** — o procedimento de uma sessão sem injeção automática para chegar ao estado de hidratação: buscar o canon pela "Verificação de canônico" e abrir com o bloco de prontidão (ver "Carregar e formatos").
- **`atualizar <REGRAS|PROJETO|MEMÓRIAS|TUDO>`** — `sincronizar` + regenerar a hidratação: `git pull` do alvo, depois `.hidrata.md` e silos de novo. Nunca sobrescreve história; conflito → para e avisa.

Ordem de dependência: sincronizar (repo em dia) → hidratação (canon no contexto) → carregar (como uma sessão chega lá) → atualizar (refaz as duas primeiras quando o canon mudou depois que a sessão começou).

---

## Continuidade entre sessões
*Executa as Regras 1, 2 e 4.*

**Eco pós-carregar:** até 5 linhas resumindo o estado herdado; o Humano confirma antes de o trabalho começar.

Hidratação velha não aparece na própria cópia: quem carregou dias atrás lê um estado coerente e obsoleto (MEMÓRIAS (248)-(252)). Por isso o eco se apoia em **fatos da Máquina**, não na releitura de si mesmo.

<details>
<summary>Procedimento técnico</summary>

- **Com shell:** rode `scripts/estado_para_eco.sh` (somente leitura) e escreva o eco a partir da saída: cite o `HASH-ESTADO` e diga em 1 linha por que o estado é coerente (ex.: o topo bate com o `SYNC`).
- **Sem shell:** declare `sync: não verificado` e não preencha o que não mediu.
- O script imprime fatos; conferir o eco contra eles é do Humano.
- Sinais automáticos que cobrem hidratação velha: `sync: PASS` com hash calculado ao vivo, `HASH-ESTADO`, `IDADE-HIDRATACAO` e, no caminho da Seth, o bloco `SETH:ESTADO-ATUAL` reinjetado a cada turno. Eles substituíram os protocolos TES-001/TES-002, descontinuados em 09/09/2026 (MEMÓRIAS (417)); a detecção de fabricação passou à "Cadeia de auditoria em camadas", ao P-7 e a `FALHAS.md`.

</details>

---

## Citação de MEMÓRIAS — primeira referência
*Executa as Regras 2 e 5.*

Ao citar uma entrada de MEMÓRIAS pela primeira vez numa resposta, acompanhe o número com uma síntese sucinta **dentro dos próprios parênteses**: `(101 - Investigação de crashes locais)`. Uma frase curta, nunca um parágrafo, e nunca o número sozinho. Vale para toda abreviação, anacronismo e referência interna: explicar o que se cita é inegociável.

Exemplo: "MEMÓRIAS (121 - bug de `num_ctx` ignorado pelo endpoint OpenAI do Ollama, fechado em (133)-(135))" em vez de apenas "MEMÓRIAS (121)".

**Aspas exigem cópia literal verificada na Máquina** — `grep`/`sed` contra a fonte (ex.: `grep -F`), nunca confiança na memória. Paráfrase entre aspas é invenção (`FALHAS.md`, CIT-1 e CIT-2).

**Citação dentro de crases (`` `(n - síntese)` ``) é exemplo de formato, não citação real** — a checagem de citação (P-7) pula, nunca alarma. Uma entrada que fala de citação errada precisa poder **mostrar** uma sem virar alarme sobre si mesma (MEMÓRIAS (203), (204)).

---

## Segunda opinião — pedido e parecer
*Executa a Regra 3 e a "Mudança estrutural".*

Quem propõe não opina sobre a própria proposta. O pedido parte do Humano.

**O pedido leva sempre:**
- a proposta isolada, em itens;
- o ponteiro para as objeções conhecidas ("estão em MEMÓRIAS (n), leia antes de opinar") — omitir objeção só cria aparência de manipulação;
- a âncora de versão: última entrada com **número e título**, e **sha256** do arquivo.

**O parecer volta em quatro partes, e nada mais:**
```
0. Origem   — de onde veio o texto que li, e até onde vai.
              Hash, se puder calcular. Se não puder: "lacuna: sem meio de medir".
1. Posição  — sim / não / condicional.
2. Fundamentação — um parágrafo.
3. Redação exata da emenda, se a posição for sim ou condicional.
```

- Parecer fora do formato, ou que entregue outro artefato, não é parecer: devolve-se o pedido **uma vez**, com o formato junto.
- Origem divergente da âncora **não invalida sozinha** — pode significar que o executor está à frente. Divergência é `lacuna` para o Humano arbitrar.
- Concordância pura não fecha nada. Discordância fundamentada é o produto útil.
- Eco do texto do proponente não é parecer — é espelho (`FALHAS.md`, ART-2).

---

## Cadeia de auditoria em camadas (multi-modelo)
*Generaliza a "Segunda opinião" para mudanças sensíveis: decisão sobre outro modelo, mudança em REGRAS/PROJETO, qualquer coisa que vá para o canon. Qualquer LLM ocupa qualquer papel (Regra 6).*

```
Modelo A (proposto/testado)
  → Modelo B (audita A, propõe achados)
    → Modelo C (audita B na Máquina — verifica as alegações de B contra REGRAS/git/hash, não só contra o texto de B)
      → Humano (recebe os pareceres de B e C, autoriza ou não)
        → quem tem acesso à Máquina escreve no canon, comita, empurra
          → qualquer modelo com acesso ao remoto confirma o hash pós-push
```
Nenhum salto é dispensável quando o destino é o canon. Pular um salto é tratar alegação como fato — contra a Regra 2.

**Por que uma camada não basta:** um auditor sozinho pode alegar sem verificar — a mesma falha que ele audita. O antídoto é auditar o auditor. Cada camada reduz a chance de uma alegação falsa sobreviver até o canon; não a zera. Quantas camadas bastam é decisão do Humano (Regra 3).

**O que cada camada entrega, sem exceção:**

| # | Item | Falha se faltar |
|---|---|---|
| 1 | Verificação na Máquina antes de afirmar (hash, git, grep — nunca leitura corrida) | Alegação vira fato sem checagem — Regra 2 |
| 2 | Citação exata do que se cita, nunca paráfrase entre aspas | Paráfrase apresentada como citação é invenção — Regra 2, `FALHAS.md` CIT-1 |
| 3 | Hedge explícito sobre qualquer ambiente que a camada seguinte não pode verificar | "Existe no meu clone" sem hedge vira fato não checável |
| 4 | Autorização explícita do Humano antes de tocar em canônico | Modelo decide sozinho — Regra 3, linha vermelha |
| 5 | Registro do que cada ator acertou, não só do que errou | Registro vira acusação unilateral, deixa de ser auditoria |
| 6 | Confirmação pós-push por quem tem acesso independente ao remoto | Push alegado nunca é cruzado contra o hash real |

**Assinatura não se multiplica por camada.** O bloco `Modelo: ... vetor: ... turno:` no fim de uma entrada é de quem **escreve o registro**, sempre um só. Cada camada se identifica no corpo do achado ("achado por X, confirmado por Y na Máquina").

*Origem:* MEMÓRIAS (143)/(144) — três camadas pegaram falhas em cascata sobre o mesmo teste; sem a terceira, os erros da segunda teriam entrado no canon.

---

## Discordância sintética
*Executa "O Conselho", item 4. Checagem mecânica: `scripts/checar_discordancia.sh` (P-13).*

Quando o relógio de 4 semanas dispara e uma discordância é provocada de propósito, a entrada de MEMÓRIAS que a registra carrega um campo literal, numa linha própria, perto do bloco `Modelo: ... vetor: ...` de fechamento:
```
SINTÉTICO: true
```
- Ausência do campo = discordância espontânea, achada no processo.
- **Nunca** marcar `SINTÉTICO: true` numa discordância que nasceu espontânea só para "contar" para o relógio — isso troca fricção real por teatro de fricção.
- Como provocar uma (o que perguntar, a quem) é julgamento editorial de cada vez; aqui só se define o formato do registro.

---

## Economia de tokens — mecanismo de Regra 7
*Mecanismo da Regra 7, não regra nova. Origem: ordem do Humano, 25/09/2026 — MEMÓRIAS (556).*

**Meios mecânicos** (medíveis, sem depender de ferramenta de um fornecedor — Regra 6):
- Referência já fixada nesta sessão (hash, caminho, número de MEMÓRIAS) substitui reler ou recitar o conteúdo inteiro.
- Leituras independentes se pedem juntas, não uma chamada de ferramenta de cada vez.
- Varredura cujo rastro bruto não precisa sobreviver à decisão roda isolada; só a conclusão volta ao histórico principal.

**Ferramenta cognitiva** (julgamento, não script):
- Resposta do tamanho da pergunta (Regra 5) — detalhe que ninguém pediu é o mesmo desperdício, em texto.
- Medir antes de rodar as três passadas da Regra 8 custa menos e diverge menos do que rodar às cegas.
