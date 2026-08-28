# Plano de execução — backlog de propostas abertas

**Rascunho versionável. SEM `APROVADO-`.** Não autoriza nada por si — cada mudança
estrutural ainda passa pelo portão das três perguntas, pela cadeia de auditoria em
camadas e por `APROVADO-<nome>` do Humano.

- Base: canon HEAD `018b40a`, 28/08/2026.
- Origem: levantamento do executor (Claude Sonnet 5, na Máquina) + ORIENTAÇÃO AO
  EXECUTOR da auditoria em nuvem (Claude Opus 5), autorizada pelo Humano, 28/08 14:36 -03.
- Citações de canon por **nome de seção**, nunca por número de linha (offset é foto,
  não âncora durável — MEMÓRIAS (96)/(97)).

---

## 1. Inventário — propostas abertas (verificado contra HEAD 018b40a)

| # | Item | Fonte (seção) | Estado real |
|---|---|---|---|
| **A** | TES-001 não fechado | PROJETO.md "Estado dos bugs e dos testes" | 3 rodadas adversas + rodada 4 limpa (MEMÓRIAS (243)). Falta N sessões consecutivas independentes; N ainda não definido. |
| **B** | Silos por modelo (`.hermes-<modelo>.md`) | PROJETO.md "Memória e hidratação"; Fase 2 | `.githooks/gerar-hermes-md.sh` é arquivo único, sem filtro por `modelo-alvo`. Confirmado no hook. |
| **C** | Eco pós-carregar mecanizado | Fase 2; REGRAS.md "Continuidade mecânica (TES)" | Protocolo existe em texto (≤5 linhas, Humano confirma). Sem mecanismo. |
| **D** | TES-002 restaurado com nonce novo | PROJETO.md "Estado dos bugs e dos testes"; Fase 2 | Formalmente inativo até B existir. Nonce `e1d1a` aposentado (MEMÓRIAS (90)). |
| **E** | Asserção byte-a-byte de entrega (harness A1) | PROJETO.md "Estado dos bugs e dos testes" | Destravado em MEMÓRIAS (159). Hook (~20 linhas) não escrito. **Assinatura já confirmada pós-0.20.1** — vendored ainda em `1f8fdc7b`/`0.20.1`, sem `hermes update` depois de (159). |
| **F** | Roteamento por complexidade | PROJETO.md "Cérebro"; MEMÓRIAS (64) | Aprovado, não implementado. Pressuposto (Gemini principal) vencido pela inversão de MEMÓRIAS (140). Sentido do roteamento precisa ser redefinido antes do código. |
| **G** | P-7 — destravar manualmente citação marcada errada | PROJETO.md "Conselho Remoto — Fase 1"; parecer GLM MEMÓRIAS (225) | Ressalva aberta do parecer. Sem mecanismo. |
| **H** | Proposta 001 — resto: manifesto de consulta + política de acesso por modelo | MEMÓRIAS (293) | Camada de leitura construída (289)-(291); índice derivado (296)-(301). Manifesto + política em stand-by. |
| **I** | Ativar skill `note-taking/obsidian` (+ `systematic-debugging`, `requesting-code-review`) | extras/BACKLOG-skills.md | Nenhuma ativada. `note-taking/obsidian` não está em `disabled` no `config.yaml` (MEMÓRIAS (291)). |
| **J** | 11 pares de proposta já aplicados, não movidos p/ `aplicadas/` | `propostas/` raiz | `263`-`270` (8) + `regra-1-1-endpoint-v1-unix` + `regra-1-1-script-universal` (2) + `ajuste-regra-1-1-timeapi` (1) = **11**. Todos no canon (verificado: 263-270 presentes; timeapi fechado por MEMÓRIAS (275)). `ajuste-regra-1-1-timeapi` é par **`.md`**, não `.diff`. |
| **K** | Texto desatualizado em PROJETO.md "Índice derivado do canon público e export pro Drive": "Um passo no post-commit fica como P-8 futura" | PROJETO.md, mesma seção | MEMÓRIAS (301) já implementou o passo. |
| **L** | `ONDE_ESTAMOS.md` fora do teto "uma tela" | REGRAS.md Regra 4; MEMÓRIAS (293) | 702 linhas / ~41 KB. |
| **N** | `PROMPT_CARREGAMENTO.md`: detector de âncora velha é falso positivo | PROMPT_CARREGAMENTO.md, bloco após ANCORA-SHA | Verificado: âncora aponta `810a3b6`, HEAD `018b40a` é filho direto — âncora exatamente 1 commit atrás, hook funcionando. O texto manda tratar isso como suspeito e cair nas URLs `/main/` (CDN, classe de risco de MEMÓRIAS (248)-(252)). Dois incidentes reais relatados hoje (não verificáveis da Máquina: `lacuna`). **FORA da quarentena P-8.** |
| **O** | Duas costuras em REGRAS.md | REGRAS.md "Carregar e formatos" vs "Regra 1.1" | (a) `(informado pela interface)` é selo de 1ª classe em "Carregar e formatos" e 3º nível com outro nome ("horário informado pelo Humano") em "Regra 1.1". (b) "Última entrada: (n)" pede afirmação seca mesmo sob `sync: não verificado` — encosta na falha de MEMÓRIAS (73). **REGRAS = "Mudança estrutural": segunda opinião OU risco assumido por escrito. Não implementar por conta.** |
| **P** | Estado de sincronia NTP da Predator | Regra 1.1 | `timedatectl status` 28/08 14:38: `System clock synchronized: yes`, `NTP service: active`. Às 13:46 do mesmo dia: `no` (máquina retomada de reboot recente, timesyncd ainda não tinha sincronizado). Selo `(relógio da Máquina)` válido a partir do momento em que sincronizou; medir sempre antes de selar. |

### Correções de forma sobre o inventário anterior do executor

- Item J: eram **11**, não 9 (a própria enumeração do texto anterior já somava 11).
- Item E: motivo da reconferência **vencido** — (159) veio depois de (150)/(0.20.1) e
  confirmou a assinatura no vendored; sem `hermes update` desde então (verificado na
  Máquina hoje).
- Item H: fonte é MEMÓRIAS (293), não a nota do vault em PROJETO_REFERENCIA.md.
- Item M (curador da sucessão): fica só em "Fora do plano / permanentes".
- Header do executor usou `(relógio do sistema, não sincronizado)` sem re-medir para o
  segundo cabeçalho — erro de Regra 1.1 (medir antes de selar, não herdar). Corrigido.

## 2. Fora do plano

- **Permanentes (não são passos):** reverificar patch 429 após todo `hermes update`;
  bundle `memoria/missoes` → HD externo quando `AgataBkup01` montar (hoje pendente,
  HD desconectado); vaga de **curador da sucessão** (`lacuna`, Humano operador local
  enquanto vago) — decisão do Humano, sem gate.
- **Horizonte — Fase 3+ (bússola, não backlog; REGRAS.md "Contenção de escopo" — só
  entra sob ordem explícita do Humano):**
  - Fase 3: GLM membro pleno (MOD-002); válvula de discordância sintética.
  - Fase 4: MEMÓRIAS hot/warm/cold por período; congelar ~500 linhas com `git tag` +
    SHA-256; `selar.sh --check` no fluxo; Capivara com consentimento por trecho.
  - Fase 5: espelho IPFS; curador nomeado; DAO.
- **Não repropor (PROJETO_REFERENCIA.md "Fronteira de recusas"):** vector store /
  GraphRAG como camada de memória, RLM auto-treino sem humano no loop, conformidade
  EU AI Act, Agent Reach, troca do modelo principal (bancada de 6 fechada), descarte
  de fato por valor, reconsolidação por reescrita, reflections agendadas escrevendo
  memória.
- **Já decididos (apareceram como abertos em memória de sessão desatualizada):**
  segunda opinião da "regra 3X" → FECHADO, virou Regra 8 (25/08). bg-review /
  auto-treino de memória → desligado por decisão (`nudge_interval: 0`), consequência
  aceita.

## 3. Interconexão (o que destrava o quê)

- **B (silos) é a espinha.** Destrava **D** (TES-002 exige silo) e o uso pleno de
  blocos MOD em produção. **C** (eco) encosta em B; quase independente.
- **E, F, G, H, I** são fracamente acoplados — cada um sob seu gate, podem correr em
  paralelo.
- **F** e **H** exigem decisão de desenho por **Regra 8** (três passadas
  independentes, sem oráculo de Máquina) antes de qualquer código.
- **J, K, L** são higiene — baixo risco, primeiro, deixam o terreno limpo.
- **A** é teste, não mudança de comportamento — corre sozinho, a Máquina arbitra.
- **N** está causando dano agora e é independente de tudo — vai antes da auditoria.
- **O** e **P** são achados que viram itens próprios de auditoria (0.10, 0.11).

## 4. Plano de execução

### BLOCO 0.0 — Correção urgente, antes de tudo (item N)

`PROMPT_CARREGAMENTO.md`: substituir o detector "compare `Escrito em:` com a hora
medida" pela comparação **URL pinada × URL `/main/`** (sem hash, sem
`api.github.com`), proibir `Escrito em:` como detector, acrescentar `parents[0].sha`
e `git ls-remote`.

- **Fora da quarentena P-8** (PROMPT_CARREGAMENTO.md não está no grupo "muda
  comportamento"). Não precisa de par `.diff`/`APROVADO-`.
- Precisa de: `git apply` do `.diff`, entrada em MEMÓRIAS, `ONDE_ESTAMOS.md` no mesmo
  commit.
- Verificação obrigatória pós-aplicação: `sha256sum` do resultado == valor-alvo do
  `.diff` fornecido pela auditoria; bloco entre marcadores `ANCORA-SHA` **intacto**
  (é conteúdo de máquina, gerado pelo `pre-commit`).
- **BLOQUEIO ATUAL:** o `.diff` / arquivo novo descrito pela ORIENTAÇÃO **não está no
  disco** desta Máquina. A orientação dá `sha256` alvo (`5e6baa3c16dbcc58`, `.diff`
  `f0d6228a4698b425`, 7.676 B) e a descrição, mas não o conteúdo. Não dá para aplicar
  um diff que não se tem, nem reconstruí-lo às cegas e alegar que bate com o hash.
  **Ação: o Humano fornece o `.diff` (ou o conteúdo do arquivo novo); só então 0.0
  executa.** Alternativa: o executor redige a correção a partir da descrição, e ela
  passa pela cadeia de auditoria como proposta normal — mais lento, perde o "custo de
  um commit".

### BLOCO 0 — Auditoria (só leitura, zero escrita em canon)

Entregável: tabela de backlog auditada + uma entrada em MEMÓRIAS registrando o
levantamento. Cada achado que virar mudança estrutural passa depois pela cadeia de
auditoria em camadas (A propõe → B audita → C verifica na Máquina → Humano autoriza).

- **0.1** Reconciliar PROJETO.md com a realidade (item K + varrer o resto por
  defasagem desde (301)). Incorpora as correções A1-A5.
- **0.2** Conferir os 11 pares de `propostas/` raiz contra o canon, um a um
  (`git log -S` / diff de blob); listar os que movem para `aplicadas/` (item J).
  Atenção: `ajuste-regra-1-1-timeapi` é `.md`. P-8 valida por hash de blob, não por
  path (MEMÓRIAS (295)) — provável que passe, **confirmar não presumir**.
- **0.3** TES-001: definir **N** e o harness exato (modelos, transporte —
  `conselho_remoto.py` p/ nuvem independente + qwen local contexto novo —, roteiro de
  relato). **Regra 8 se aplica** (escolha sem oráculo de Máquina): três passadas
  independentes no modelo local, hidratações distintas; divergência = `lacuna` que
  sobe pro Humano. A isenção de Regra 8 que vale para 2.1 **não** se estende a 0.3.
- **0.4** Silos: ler `.githooks/gerar-hermes-md.sh` inteiro; mapear onde entra o
  filtro por `modelo-alvo`; listar os modelos-alvo reais; dimensionar o
  `.hermes-<modelo>.md`.
- **0.5** Harness A1: **reduzido** — confirmar só o formato do selo de `scripts/selar.sh`
  (a assinatura do hook em `conversation_loop.py` já está confirmada pós-0.20.1;
  reconferir apenas se houver `hermes update` antes de 4.1).
- **0.6** Roteamento: reler MEMÓRIAS (64); escrever o que "sentido invertido"
  significa com qwen principal / Gemini fallback.
- **0.7** P-7: ler o checador de citação; dimensionar o destravamento manual
  (arquivo de exceção? flag? entrada em MEMÓRIAS?).
- **0.8** Proposta 001 resto: fixar o que "manifesto de consulta" e "política de
  acesso por modelo" significam concretamente, à luz de (289)-(301).
- **0.9** Skills: confirmar escopo só-leitura possível para `note-taking/obsidian` no
  Hermes + o reteste de tool-calling que a lição da Fase 2 exige.
- **0.10** (item P) Rodar `timedatectl status`, registrar. Se a máquina estiver
  mesmo fora de sincronia, vira item próprio com prioridade **acima de higiene**
  (enfraquece todo selo `(relógio da Máquina)` e todo carimbo de commit). Se estava
  sincronizada e o selo anterior foi precaução, é `lacuna` de medição da Regra 1.1 —
  conserto é medir antes de selar, sempre. *(Medido 28/08 14:38: `synchronized: yes`.
  Item resolvido como lacuna de medição; sem trabalho estrutural.)*
- **0.11** (item O) Redigir as duas emendas de REGRAS.md e escolher o caminho:
  segunda opinião de outro modelo OU risco assumido por escrito pelo Humano. Não
  implementar nesta passada.

### BLOCO 1 — Higiene (baixo risco)

- **1.1** Mover os 11 pares aplicados p/ `propostas/aplicadas/` (item J). Toca só
  `propostas/` — **não é P-8**. Entrada em MEMÓRIAS.
- **1.2** Corrigir o texto desatualizado de PROJETO.md (item K + o que 0.1 achar).
  **É P-8:** `.diff` congelado por `sha256sum` → `APROVADO-` do Humano →
  `perimetro.sh` verde → move do par no mesmo commit → entrada + `ONDE_ESTAMOS.md`.
- **1.3** Encolher `ONDE_ESTAMOS.md` p/ uma tela (item L). **Não é P-8** (arquivo de
  registro). Teste de aceite = leitura do Humano. Entrada em MEMÓRIAS.

### BLOCO 2 — Fechar Fase 0

- **2.1** Rodar a bateria TES-001 com o harness de 0.3 (item A). **Sem P-8, sem
  Regra 8** — é teste, a Máquina arbitra. Resultado → MEMÓRIAS. Fechou → Fase 0 fecha.

### BLOCO 3 — Fase 2 (a espinha)

- **3.1** Silos por modelo (item B): alterar `.githooks/gerar-hermes-md.sh` p/ emitir
  `.hermes-<modelo>.md` por modelo-alvo, filtrando blocos MOD. **P-8** (toca
  `.githooks/*`) + **cadeia de auditoria em camadas** (muda o que chega a cada
  modelo). Reteste de tool-calling depois — lição da Fase 2. **Destrava 3.3 e blocos
  MOD em produção.**
- **3.2** Eco pós-carregar mecanizado (item C): entra junto ou logo depois de 3.1.
  Pequeno.
- **3.3** TES-002 restaurado (item D): nonce novo por `openssl rand` na Máquina, fora
  do canon, nunca commitado, entregue à mão pelo Humano ao modelo-alvo. Depende de
  3.1.
- Fim do bloco = Fase 2 fechada.

### BLOCO 4 — Fracamente acoplados (paralelos, cada um sob seu gate; prioridade decrescente)

- **4.1** Harness A1 (item E): escrever o hook (~20 linhas) a partir de 0.5. **P-8**
  se cair em `scripts/`/`.githooks/`. Fecha uma classe de teto silencioso.
- **4.2** P-7 destravamento manual (item G): implementar o de 0.7. **P-8** (script).
- **4.3** Proposta 001 resto (item H): decisão de desenho por **Regra 8** → texto em
  PROJETO.md sob **P-8**.
- **4.4** Ativar `note-taking/obsidian` só-leitura (item I): config **fora do repo**,
  não passa por P-8 — **registrar explicitamente na entrada** que é a mesma classe de
  buraco que a P-8 existe pra fechar, coberta aqui só por decisão do Humano. Uma skill
  por vez, reteste de tool-calling após cada. Entrada em MEMÓRIAS.
- **4.5** Roteamento por complexidade (item F): decisão de sentido por **Regra 8** →
  implementação **P-8**. Prioridade mais baixa (aprovado, mas com pressuposto
  vencido).

## 5. Ordem recomendada, com alternativas e riscos

**Recomendada:** 0.0 → 0 (com 0.1..0.11) → 1 → (2 e 3 intercalam; 2.1 não bloqueia
3.1) → 4 em prioridade decrescente. Nada de 3/4 começa antes de 0 dimensionar o item
correspondente.

| Ponto de decisão | Alternativa | Risco de cada caminho |
|---|---|---|
| 0.0 antes da auditoria | Fazer 0.0 dentro do BLOCO 1 (higiene) | Adiar: toda sessão em nuvem que carregar hoje pode chegar a canon velho sem sinal (2 incidentes já hoje). Antecipar: custo de um commit, fora de P-8 — risco baixo, **desde que o `.diff` correto exista** (hoje não está no disco). |
| 2 e 3 intercalados | Fechar Fase 0 (2.1) inteiro antes de tocar Fase 2 | Serial: Fase 2 espera N sessões independentes de TES-001, que levam dias. Intercalado: 3.1 é P-8 + cadeia de auditoria e não depende de 2.1 — ganha tempo sem perder gate. |
| 3.1 (silos) via hook | Manter arquivo único e silo "norma, não mecanismo" | Manter: MOD sensível não pode entrar em MEMÓRIAS de produção (vaza no system prompt) — trava D e Fase 3. Implementar: risco de regressão de tool-calling (mitigado pelo reteste da lição da Fase 2). |
| 4.4 (skills) fora de P-8 | Não ativar skill nenhuma até haver P-8 para `config.yaml` | Não ativar: `note-taking/obsidian` é a ponte nativa pro vault que (290)-(292) construíram; sem ela a navegação é manual. Ativar: muda comportamento sem o gate — coberto só por decisão do Humano, registrado na entrada. |
| O (costuras REGRAS) agora | Deixar como `lacuna` registrada até haver outra mudança em REGRAS | Agora: consome uma rodada de segunda opinião. Depois: o bloco de prontidão continua com dois textos que se contradizem, e o campo "Última entrada" sob sync não verificado continua encostando na falha de (73). |

**Regra 3:** isto é proposta e traz recomendação **com** alternativas e riscos — não
há declaração de "não opino". O Humano decide o quê, em que ordem, e cada mudança
estrutural ainda passa pelo portão das três perguntas e pela cadeia de auditoria
antes de virar `APROVADO-`.
