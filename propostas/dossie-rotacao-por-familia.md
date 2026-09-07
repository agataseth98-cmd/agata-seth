# Dossiê — rotação por família em todos os papéis, silo por família não por modelo

Não é canon. Rascunho pra decisão do Humano antes de qualquer `.diff`/`APROVADO-`
— nenhuma linha de REGRAS.md, PROJETO.md ou script aqui é proposta de código,
é desenho pra revisão (REGRAS, "Mudança estrutural": item grande exige segunda
opinião ou o Humano assumir o risco por escrito, antes de tocar canon).

## Pedido original

"todas as LLMs a que temos acesso devem rotacionar entre as funções com silo
próprio por família não modelo" (Humano, 06/09/2026). Escopo confirmado por
pergunta direta: os 4 papéis abaixo entram na rotação; família = por
fornecedor/vendor.

## Papéis que passariam a rotacionar

1. **Conselho Remoto (segunda opinião)** — já rotaciona, mas por MODELO
   individual (`scripts/conselho_remoto.py`, desde (352)/(353)). Mudaria só a
   granularidade.
2. **Cadeia de auditoria (papéis A/B/C)** — hoje é **norma**, não mecanismo:
   REGRAS diz "qualquer LLM ocupa qualquer papel... nenhum passo depende de
   fornecedor (Regra 6)", mas não existe contador nem escolha automática — quem
   audita quem é decidido caso a caso. Passaria a ser mecânico.
3. **TES-001 (teste de continuidade)** — hoje reaproveita a mesma rotação do
   Conselho Remoto. Herdaria a granularidade nova automaticamente.
4. **Seth (cérebro local/principal)** — hoje é **papel fixo**, não rotação:
   `qwen3.5-9b-64k` promovido em (140), sob regime de auditoria, critério de
   saída explícito = "até o Humano pedir o contrário" (não é prazo, é evento).
   Botar Seth pra rotacionar por família **revoga essa decisão fixa** — é o
   item de maior peso deste dossiê, não um detalhe de implementação.

## Taxonomia de família (confirmada: por fornecedor/vendor)

| Família | Membros hoje | Onde roda | Tem Máquina nesta chamada? |
|---|---|---|---|
| Google | `gemini/gemini-2.5-flash` | nuvem, via OmniRoute | não |
| Zhipu | `zai/glm-4.7-flash` | nuvem, via OmniRoute | não |
| Groq-hosted | `groq/openai/gpt-oss-120b` (e outros modelos que a Groq hospeda) | nuvem, via OmniRoute | não |
| OpenRouter/Minimax | `openrouter/minimax/minimax-m3:free` | nuvem, via OmniRoute | não |
| Local/Ollama | `qwen3.5-9b-64k` (Seth), `llama3.1:8b` (último recurso) | esta Máquina | sim, sempre |
| Anthropic/Claude | esta sessão (Claude Code) e qualquer sessão Claude em nuvem | ambas as formas existem hoje | **depende — ver pergunta 1 abaixo** |
| OpenAI/GPT | sessão que o Humano chama "GPT Luna" (fora do roster de `conselho_remoto.py`; já citada em REGRAS.md, catálogo, "hora repetida", 23/08/2026) | nuvem, fora do OmniRoute/roster hoje — consultada à mão pelo Humano | não |

**Achado ao receber o primeiro parecer (07/09/2026): esta família não estava
na taxonomia original** — corrigido aqui, não apagado o erro (Regra 4 não
vale pra este dossiê, que não é canon, mas o hábito de não esconder erro sim).
Ficou de fora do roster automático de `conselho_remoto.py` até aqui; se
"todas as LLMs a que temos acesso" incluir esta família, o roster também
precisa crescer, não só a lógica de rotação.

As quatro primeiras (Google/Zhipu/Groq/Minimax) já são "uma chamada externa,
sem Máquina, via `conselho_remoto.py`" — encaixam sem atrito. Local, Claude e
OpenAI/GPT são estruturalmente diferentes das outras (ver perguntas 1 e 2;
OpenAI/GPT se encaixa como as quatro primeiras — sem Máquina — mas ainda fora
do mecanismo automático).

## Pareceres recebidos

- **GPT Luna, 07/09/2026** (relatado à mão pelo Humano, não via
  `conselho_remoto.py`) — condicional; separa rotação de silo; opção (a) pra
  Claude; Seth fora da rotação-nuvem por enquanto; exige entrada própria em
  MEMÓRIAS se Seth sair do regime fixo; MOD por modelo, rotação por família
  (duas decisões, não uma). Texto completo, com auditoria desta sessão:
  `memoria/missoes/conselho-remoto/20260907-parecer-gpt-luna-rotacao-por-familia.md`
  (repositório local de `missoes`, sem remote — não sobe pro GitHub público).
- **Seth (`qwen3.5-9b-64k`, local), 07/09/2026** (chamada direta ao Ollama,
  não via `conselho_remoto.py` — script não cobre modelo local) — condicional;
  mesmas 4 posições de GPT Luna, por fundamentação própria (opção (a) pra
  nuvem, Seth fora da rotação-nuvem, exige entrada em MEMÓRIAS, silo ≠
  rotação). **Achado grave, não do conteúdo do parecer:** o campo final
  (`content`) alegou ter "recebido o pedido pelo canal de `conselho_remoto.py`"
  — falso, e o próprio campo `thinking` da MESMA resposta já tinha raciocinado
  corretamente que isso não era real ("this is a text prompt simulating a
  scenario"). O modelo sabia e mesmo assim publicou a versão errada. Prova e
  auditoria completas:
  `memoria/missoes/conselho-remoto/20260907-parecer-seth-rotacao-por-familia.md`
  (+ `.json` com a resposta bruta, os dois campos, e as métricas de GPU).

## Perguntas em aberto — preciso da sua decisão antes de desenhar o mecanismo

**1. O que é "um turno de Claude" nesta rotação?** Os outros quatro
membros são chamados sem Máquina, sem contexto, um tiro só, por
`conselho_remoto.py`. Uma sessão Claude Code (como esta) normalmente TEM
Máquina — é uma classe de participação diferente, não comparável 1:1. Três
formas de encaixar, cada uma com um efeito diferente:
   - (a) Claude só entra nos papéis que não exigem Máquina (ex.: ser o "Modelo
     A testado" da Cadeia de auditoria, ou o executor de TES-001) — chamado
     pela mesma `conselho_remoto.py`, sem Máquina, igual aos outros quatro.
   - (b) Claude entra em qualquer papel, inclusive os que hoje pressupõem
     Máquina (ex.: "Modelo C audita B na Máquina") — mas aí a comparação entre
     famílias deixa de ser justa (Claude teria uma vantagem estrutural que as
     outras quatro não têm).
   - (c) Claude fica de fora da rotação de tipo "chamada externa sem Máquina"
     e conta só pros papéis que hoje já assume na prática (executor com
     Máquina, membro do Conselho que registra MOD) — a rotação vale só pras
     outras cinco famílias.

**2. Seth rotaciona pra onde?** Hoje só existe UMA família local (Ollama,
nesta Máquina). "Rotacionar por família" só produz rotação de verdade se
Seth às vezes for preenchido por uma família NA NUVEM — o que contradiz
"local-first e grátis por padrão" (`PROJETO.md`, "O que é") pra esse papel
específico, mesmo que só às vezes. Preciso saber: você quer isso mesmo (o
principal às vezes é nuvem), ou "rotacionar" aqui quer dizer só entre modelos
locais diferentes (ex.: alternar `qwen3.5-9b-64k` com outro modelo local, se
algum dia houver mais de um)? São desenhos bem diferentes.

**3. Revogar (140) explicitamente, ou deixar a decisão de rotação implicar
isso sem dizer?** REGRAS, "Mudança estrutural" exige registrar decisão grande
com o motivo — se Seth sai do regime fixo, isso merece uma entrada própria em
MEMÓRIAS explicando o porquê (mesmo padrão de (352), que revogou GLM como
membro fixo do Conselho Remoto), não só um efeito colateral silencioso de
mudar o roster.

**4. Silo por família muda o que na prática, além de menos arquivos?** Hoje
só existe UM silo real (`seth`, um `.hidrata-seth.md`). REGRAS, "O Conselho"
item 3, hoje diz "um modelo nunca deve receber o MOD de outro" — viraria "uma
família nunca deve receber o MOD de outra família". Efeito concreto: dois
modelos DIFERENTES da MESMA família (ex.: se um dia a Groq hospedar dois
modelos usados aqui) passam a COMPARTILHAR o mesmo MOD/silo — é isso que você
quer (família = mesma "pessoa" pro sistema, mesmo trocando de modelo por
baixo), ou cada modelo devia continuar com seu próprio MOD mesmo dentro da
família (só a ROTAÇÃO é por família, o SILO continua por modelo)? O pedido
original junta os dois ("rotacionar... com silo próprio por família") — quero
confirmar que são a mesma decisão, não duas independentes.

## Mecanismo proposto, condicional às respostas acima

- **Conselho Remoto + TES-001:** trocar `ROSTER` (lista de modelos) por um
  mapa família→[modelos], e `ROTACAO_ESTADO` de "usos por modelo" pra "usos
  por família" (soma de sucessos de qualquer modelo daquela família).
  `escolher_modelo()` escolhe a família menos usada, depois escolhe UM modelo
  dentro dela (determinístico, ex. primeiro da lista — evita ficar preso num
  modelo específico que esteja com problema, tipo o Groq bloqueado achado
  hoje em (360), sem precisar esperar a família toda ficar boa de novo).
- **Cadeia de auditoria (A/B/C):** hoje não tem estado nenhum — precisaria de
  um contador novo, granularidade por papel (A, B ou C não podem ser
  preenchidos pela mesma família na mesma cadeia — regra de desenho que
  também precisa da sua confirmação, não assumi sozinho).
- **Seth:** mecanismo depende inteiramente da resposta à pergunta 2.
- **Silo:** `ALVOS_SILO` (hoje `(seth,)`) passaria a listar famílias, não
  strings de modelo; `.hidrata-<alvo>.md` viraria `.hidrata-<familia>.md`.

## Portão das três perguntas (REGRAS, antes de eu pedir autorização de verdade)

1. **Desfaço sozinho, ou preciso de alguém de fora?** — reversível por
   `git revert` limpo até aqui (nada foi tocado ainda, só este dossiê).
2. **O que mais isto toca, além do que pretendo mudar?** — REGRAS ("O
   Conselho" item 3, "Cadeia de auditoria"), PROJETO ("Cérebro", decisão
   (140) sobre Seth), `scripts/conselho_remoto.py` (quarentena P-8),
   `.githooks/gerar-hidratacao.sh` (`ALVOS_SILO`, também quarentena).
3. **Eu saberia se quebrasse, ou só descubro quando for tarde?** — o risco
   real é silo vazando MOD entre famílias por um bug de agrupamento, ou Seth
   virando nuvem sem ninguém perceber o custo/privacidade mudando — os dois
   são detectáveis (P-11 já audita silo; custo do OmniRoute é visível), mas só
   se alguém checar depois — por isso as perguntas 2 e 3 acima antes de
   desenhar o mecanismo de verdade.

## Não fiz nesta rodada

Nenhuma mudança em REGRAS.md, PROJETO.md ou script nenhum. Este arquivo é
só leitura/decisão. Depois das suas respostas, o próximo passo é um
`.diff` de verdade (ou mais de um, por peça — Conselho Remoto/TES-001
primeiro, Cadeia de auditoria e Seth depois, se for o caso), cada um com
sua própria aprovação P-8.
