# Dossiê S1 — Dimensionamento da Fase 2 (Passo 0.4 do roteiro)

**Read-only. Não decide nada. Insumo da Camada A.**

- Sessão S1 autorizada pelo Humano, 31/08/2026 ("S1 autorizado").
- Base: canon HEAD `f8195f3`; vendored `~/.hermes/hermes-agent/` (fora do repo, sem backup — mesma classe do patch 429).
- Método: leitura de código e de MEMÓRIAS na Máquina. Zero escrita fora deste arquivo.

---

## Achado 1 — como o Hermes injeta o `.hermes.md` (e como o silo pega carona nisso)

`agent/prompt_builder.py`:
- `_HERMES_MD_NAMES = (".hermes.md", "HERMES.md")` — **nome fixo**, sem env var, sem chave de config para trocar (procurei: `HERMES_MD`/`HERMES_CONTEXT` não existem; só `HERMES_HOME`, e esse é do `SOUL.md`).
- `_find_hermes_md(cwd)` procura a partir do **cwd**, subindo até a raiz do git, e devolve o primeiro match.
- Truncamento: `_get_context_file_max_chars` — `context_file_max_chars` explícito no `config.yaml` vence. Está em **150000**. Acima disso, trunca e emite aviso no build.

`agent/runtime_cwd.py` — **o gancho que torna o silo viável sem patch vendored:**
- `_SESSION_CWD` (ContextVar) + `set_session_cwd()`. `resolve_context_cwd()` — usada pela descoberta de context-file — **checa `_SESSION_CWD` primeiro**, antes de `TERMINAL_CWD`/launch dir.
- Quem chama `set_session_cwd`: `gateway/session_context.py:280`, `cron/scheduler.py`, `acp_adapter/server.py`. **As sessões do Agata rodam pelo gateway** (`hermes-gateway.service`).

**Consequência:** se o gateway apontar a sessão de cada modelo para um diretório próprio
(ex: `~/agata/silos/<modelo>/`, cada um com o seu `.hermes.md`), o Hermes injeta o
arquivo certo **sem tocar o código vendored**. O silo por modelo não precisa de
`.hermes-<modelo>.md` com nome especial — precisa de **um `.hermes.md` por diretório**
e do gateway roteando a sessão pelo `modelo-alvo`.

**Pergunta que sobe pra Camada A:** o mapeamento sessão→cwd do gateway
(`gateway/session_context.py`, fora do repo) suporta rota por modelo? Onde se
configura? (S1 não mexeu nesse arquivo — é investigação da Camada A ou de um S1-b.)

---

## Achado 2 — onde entra o filtro em `.githooks/gerar-hermes-md.sh`

O hook gera **um** `.hermes.md` = REGRAS.md + PROJETO.md + `janela_memorias()` + `INDICE_MEMORIAS.md`.

- `janela_memorias()` (linhas ~93-121 no formato novo, ~125-143 no antigo): casa
  cabeçalho `^\([0-9]+\) (DI[AÁ]RIO|CONSELHO|MOD|CORRE[CÇ][AÃ]O)` e caminha
  cabeçalho-a-cabeçalho. **Já reconhece `MOD`; não olha o corpo.** O filtro de silo
  precisa, ao montar o arquivo de um `<modelo>`, **entrar no corpo do bloco `MOD`**,
  ler a linha `modelo-alvo:` e **pular o bloco se o alvo for outro**.
- `gerar_indice()` / `gerar_indice_palavras_chave()` (linhas ~72/78 e ~183/190):
  as linhas de índice de entradas `MOD` teriam o mesmo tratamento — ou filtrar por
  consistência, ou marcar "MOD alheio" sem corpo.
- Estrutura nova exigida: um laço `for modelo in $ALVOS; do OUT=".hermes.md" dentro
  de silos/<modelo>/ ...; done`, mais um arquivo **comum** para modelo sem silo próprio.

Isto tudo é `.githooks/*` → **P-8** + cadeia de auditoria em camadas.

---

## Achado 3 — `modelo-alvo` reais e quantos arquivos

- **No canon hoje: um só bloco MOD** — `(51) MOD claude — 26/07/2026`,
  `modelo-alvo: claude` (string não verificada), nenhum trecho liberado.
- Alvos previsíveis (config + história): `claude`; `seth`/`qwen` (`qwen3.5-9b-64k`,
  principal desde (140)); `gemini` (`gemini-2.5-flash`, fallback); `glm` (Conselho
  Remoto, Fase 3). → **~4 silos**.
- **Efeito prático hoje ≈ nulo:** o filtro removeria um bloco de ~15 linhas de 3 dos
  4 arquivos. O valor do silo **não é economia de token** (ver Achado 4) — é a
  **fronteira de confidencialidade** que destrava MOD sensível em MEMÓRIAS de
  produção (hoje proibido, REGRAS "O Conselho").

---

## Achado 4 — tamanho, teto e o número de (3626) que envelheceu

- `.hermes.md` atual: **142.129 bytes** (última geração do hook). `context_file_max_chars`
  = 150000. **Folga de ~8 KB — 95% do teto.**
- MEMÓRIAS (3626 - dimensionamento pra Fase 2) registrou "`.hermes.md` = 11.595 tokens
  = 18,1% do piso de 64k". Aquele arquivo tinha ~46 KB. O de hoje é **~3× maior**
  (REGRAS + PROJETO cresceram, janela de 25k de MEMÓRIAS, índice). **O 18,1% está
  velho — remedir antes de citar.** Estimativa grosseira atual: ~35-40k tokens, na
  casa de 55-60% do piso de 64k, consumidos antes da primeira palavra do Humano.
- **O grosso do peso é REGRAS.md + PROJETO.md verbatim + a janela de MEMÓRIAS** —
  não os blocos MOD. Filtrar MOD (Achado 3) quase não move o tamanho. Se a Fase 2
  quiser também atacar o custo de contexto, é outro item (janela por modelo,
  inclusão parcial de PROJETO) — não o filtro de silo.
- Risco a registrar: com MOD sensível entrando em produção pós-3.1, o arquivo
  cresce e cruza 150000 → truncamento. 3.1 deve decidir: subir o teto, ou cortar
  a janela por modelo.

---

## Achado 5 — a "lição da Fase 2" (o reteste que roda depois de 3.1)

Não é uma frase; é um padrão documentado do modelo local, em MEMÓRIAS (119)/(138)/(139):

- **(119):** qwen sob tool-calling **com 1 ferramenta** "passa" — mas produção expõe
  **12 de 18** ferramentas, e a precisão cai com o número de ferramentas
  (Ollama issue #14745). "Passa" ≠ validação completa.
- **(138)/(139) e o achado de (3059):** uma chamada real da ferramenta `memory`
  "completou" (0,01s) **sem escrever nada**, e o modelo **narrou em detalhe uma
  ação de gestão de cota que nunca aconteceu** (conferido na Máquina: `mtime`
  intacto). Não é fingir a chamada — a chamada ocorreu; o **relato do que ela fez**
  foi fabricado.
- **(3051):** cuidado de método — arquivo auto-injetado (SOUL.md, `.hermes.md`)
  faz o modelo **responder sem chamar ferramenta**. O reteste tem que separar
  "respondeu do contexto injetado" de "chamou a ferramenta de verdade".

**Desenho do reteste pós-3.1 (para a Camada A detalhar):** rodar tool-calling com
as 12 ferramentas de produção **contra cada `.hermes.md` de silo**, mais o teste
de fabricação deliberada, mais a checagem de "respondeu sem chamar". Comparar
contra a baseline do arquivo único. Regressão = 3.1 não entra.

---

## Perguntas sem oráculo de Máquina → Regra 8 dentro da Camada A

1. **Mecanismo do silo:** rota por cwd no gateway (Achado 1) vs. patch vendored do
   `_find_hermes_md` vs. symlink swap. O primeiro parece o mais limpo — confirmar
   que o gateway roteia por modelo.
2. **O que o filtro exclui exatamente:** só `MOD` com `modelo-alvo` diferente?
   `MOD` sem `modelo-alvo`? `CONSELHO` fica comum a todos? (provável que sim.)
3. **Orçamento de janela por modelo:** 25.000 fixo, ou calibrado por piso de
   contexto de cada modelo?
4. **Fallback:** modelo sem silo próprio recebe o arquivo comum — o que ele contém
   (nenhum MOD? só MOD sem alvo?).
5. **Teto de 150000:** subir, ou cortar janela, quando MOD sensível entrar?

---

## O que S1 NÃO fez (de propósito)

- Não abriu `gateway/session_context.py` nem mexeu em config do gateway — fora do
  repo, e é investigação da Camada A / de um S1-b se o Humano quiser.
- Não propôs `.diff` nenhum. Dossiê é insumo; a proposta é da Camada A.
- Não remediu o token count de (3626) com precisão — só sinalizou que está velho.

**Próximo passo do roteiro:** Camada A de 3.1 parte deste dossiê. Sessão separada.
