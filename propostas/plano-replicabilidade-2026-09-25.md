# Plano — replicabilidade do Agata em outra Máquina (B-REPL)

> **Não é canon. Rascunho pra decisão do Humano antes de qualquer `.diff`.**
> REGRAS, "Mudança estrutural": item grande em PROJETO/scripts exige **segunda
> opinião de outro modelo OU o Humano assumir o risco por escrito** antes de
> tocar canon. Este plano é pra revisão; nada de código foi escrito ainda.
>
> Origem: ordem do Humano, 25/09/2026 — "padronizar o sistema para replicar em
> produção assistida em outro notebook, seguindo as diretrizes do sistema e o
> estado da arte em 2026 de replicabilidade de sistemas", refinada em:
> "deve ser fácil de replicar, e iniciar seu próprio projeto; quando não for
> nesta máquina o sistema de memórias deve utilizar o Obsidian; o Agata dos
> cabeçalhos nos clones deve ser trocado por um nome que o cliente decidir;
> o sistema clone deve ter um mecanismo de atualização a partir do
> repositório oficial; antes, durante e depois da instalação o sistema deve
> auxiliar o novo usuário a criar seu projeto; deve guardar as memórias no
> vault; nunca acessar o projeto original nem as memórias originais."

---

## 0. O corte conceitual que organiza tudo o resto

Hoje `agataseth98-cmd/agata-seth` é uma coisa só: **framework + instância**,
misturados no mesmo repositório. `REGRAS.md` é doutrina universal (Regra 6:
"nada preso a um modelo" já assume isso). `PROJETO.md`/`MEMÓRIAS.md` são o
estado e a história **desta** instância — hardware desta Predator, decisões
deste Humano, 551 entradas da vida real dele com a Agata.

Replicar "fácil, com projeto próprio, nunca acessando o original" exige
separar os dois, pela primeira vez de propósito:

| Camada | O que é | Vai pro clone? |
|---|---|---|
| **Framework** | `REGRAS.md` (universal, já é isso hoje) · `scripts/*` · `.githooks/*` · `redesign/{grafo,router,mcp,librechat,systemd}` · o mecanismo de quarentena P-8, os controles do perímetro, a doutrina de hidratação | **Sim** — é o produto. |
| **Template de PROJETO/MEMÓRIAS** | A FORMA de `PROJETO.md` (seções, convenções) e o preâmbulo/mecanismo de `MEMÓRIAS.md` (marcador, fases, camadas) — sem conteúdo desta instância | **Sim, vazio** — nasce com a entrada (1) do cliente novo, não com (551) desta. |
| **Instância** | Conteúdo real de `PROJETO.md`/`MEMÓRIAS.md` desta Predator, `memoria/missoes/`, `memoria/frio/`, `.hidrata*.md`, `~/.config/agata/.env`, os 15 modelos calibrados pro hardware desta máquina | **Nunca.** É exatamente o que o Humano marcou como "nunca acessar". |
| **Identidade** | A palavra "Agata" — hoje hardcoded em ~40+ arquivos (REGRAS, PROJETO, todo script, unit systemd, o ícone, o nome do banco Mongo) | **Vira variável** — o cliente escolhe o nome na instalação. |

Sem esse corte, qualquer bootstrap "clona o repo e roda" traria a história,
a memória e a identidade **desta** Agata pro clone — o oposto do pedido.

## 1. O que já está certo, sem mexer (achado na varredura de hoje)

`memoria/missoes/` já é "LOCAL por desenho... nunca em hidratação"
(PROJETO.md, "Memória e hidratação") — um clone nasce com `missoes/` vazia
por arquitetura, não por trabalho novo. `extras/arquivo*` é história desta
instância, fica pra trás com o mesmo motivo que `MEMÓRIAS.md` fica. Isso já
reduz o problema — a maior parte da "instância" já está isolada da parte que
seria "framework"; falta principalmente **PROJETO.md, MEMÓRIAS.md, o nome
"Agata", os segredos, e ter um instalador de verdade**.

## 2. Fases

### Fase 0 — feito hoje, fora deste plano
Limpeza de 4,7 GB (`memoria/missoes/rlm-3caminhos/modelo/*.gguf`, spike
encerrado, hash idêntico ao blob que o Ollama já guarda por conta própria,
conferido ao vivo antes de apagar). Sem relação direta com replicação, mas
tirou ruído do caminho.

### Fase 1 — Segredo fora do repo, com template (baixo custo, sem risco)
**[IMPLEMENTADO 25/09/2026]** `CHAVES.env.exemplo` (raiz do repo, mesmo
padrão já usado em `redesign/librechat/env.exemplo`) documenta a FORMA de
`~/.config/agata/.env` — nome de cada variável + link de onde tirar a chave
—, nunca um valor real. `CHAVES.md` ganhou a seção "Checklist: testar que
uma chave funcionou, e como rotacionar", com um comando real por segredo (8
linhas: 1 por família de provedor de modelo + Discord + restic + Obsidian +
Google OAuth + OmniRoute + LibreChat). Hoje era prosa espalhada; virou
checklist executável. **Nenhum segredo real tocado** — conferido pelo
próprio P-1 do perímetro antes de comitar (varredura de segredo limpa nos
dois arquivos). `CHAVES.md`/`CHAVES.env.exemplo` não são "muda
comportamento" — fora do escopo do P-8 (nenhum script lê o `.exemplo` em
runtime), então esta entrada não precisou de proposta assinada.

### Fase 2 — Identidade parametrizada
Levantamento de todo lugar que hardcoda "Agata"/"Seth" (nome, ícone, banco
Mongo, `customWelcome` do LibreChat, unit systemd, o próprio nome do
repositório). Decisão de mecanismo: variável de ambiente lida no bootstrap
(`AGATA_NOME_INSTANCIA=Marcos` → o instalador troca nos arquivos que
precisam, não em tudo — REGRAS.md continua "REGRAS.md", só o nome falado
muda) vs. find-replace de instalação. **Decisão do Humano antes de escrever
código** — os dois têm trade-off de manutenção diferente.

**Resposta à pergunta "como funciona o carregamento pra LLM na nuvem, num
clone?" (25/09/2026):** hoje `PROMPT_CARREGAMENTO.md` funciona porque é
canônico DENTRO do repositório (decisão de 20/08/2026) — um LLM em nuvem sem
Máquina lê ele e as URLs `raw.githubusercontent.com/agataseth98-cmd/
agata-seth/...` que ele mesmo cita, incluindo o bloco `ANCORA-SHA` que o
`.githooks/pre-commit` reescreve a cada commit. Nada disso quebra num
clone — o MECANISMO é genérico — mas duas coisas estão HARDCODED no texto
gerado e no gerador:
1. `scripts/atualizar_ancora_prompt.py` escreve as URLs com
   `agataseth98-cmd/agata-seth` literal. Precisa passar a ler
   `git remote get-url origin` e montar a URL do repo REAL do cliente — sem
   isso, o `PROMPT_CARREGAMENTO.md` de um clone apontaria pro repositório
   OFICIAL, e um LLM na nuvem carregaria REGRAS/PROJETO/MEMÓRIAS da Agata
   original, não do clone. Seria o vazamento exato que o Humano pediu pra
   evitar, só que pela porta de trás (LLM em nuvem, não Máquina).
2. O texto fixo ("você está entrando como um dos modelos do Conselho do
   sistema **Agata**") usa o nome hardcoded — mesma variável da Fase 2,
   mesmo mecanismo de troca.

Os dois consertos são pequenos e vivem dentro desta fase (não é fase nova):
o gerador de âncora já roda a cada commit, só precisa deixar de hardcodar o
`owner/repo`; o texto fixo do prompt já vira variável junto com todo o
resto que a Fase 2 levanta. **Nenhum LLM em nuvem precisa de credencial nem
acesso especial pra isso** — ele já lê `raw.githubusercontent.com` de um
repositório PÚBLICO, seja o oficial ou o do cliente; a única mudança é QUAL
URL o texto aponta.

### Fase 3 — Bootstrap executável único
Um `bootstrap.sh` (ou `agata init`, comando novo no CLI já existente,
`redesign/grafo/cli.py`) que, numa Máquina limpa: instala dependências
(Ollama, Docker, systemd units), gera o `.env` a partir do template
perguntando as chaves, roda `git init` do canon do cliente (não um clone do
histórico desta Agata — um repo NOVO, com REGRAS.md copiado do framework e
PROJETO.md/MEMÓRIAS.md vazios/gerados do zero), sobe os serviços, confere com
`perimetro.sh` que subiu certo. Idempotente (rodar de novo não duplica nem
quebra).

### Fase 4 — Memória em Obsidian como vault PRIMÁRIO do clone
**Decidido 25/09/2026 (ordem do Humano: "fase 4, fazer a recomendada"):
Obsidian como camada de leitura/escrita do cliente, `MEMÓRIAS.md` como o
registro mecânico por baixo.** Preserva P-5/P-7/P-14/assinatura tal como já
existem — nenhuma garantia mecânica precisou ser reaberta.

**Primeiro passo, implementado e testado nesta mesma data:**
`scripts/vault_importar_inbox.py`. Mecanismo: o cliente escreve uma nota
solta em `memoria/obsidian-inbox/` (pasta NOVA, irmã de `memoria/obsidian/`,
nunca dentro dela — achado testando de verdade: `gerar_obsidian.py` faz
`shutil.rmtree()` do vault a cada regeneração, e um inbox dentro dele seria
apagado antes de ser lido). O script lê a nota (frontmatter `titulo:` ou
1ª linha como título, resto como corpo), chama `POST /memoria` do
`seth_escriba` — **o MESMO caminho hardened que a Seth já usa pra escrever**,
zero lógica de escrita nova, zero superfície de ataque nova — e apaga a nota
de origem só se a escrita confirmar sucesso. Testado: 9/9 selftest (parsing
de nota, nota sem conteúdo não gera entrada vazia, falha de rede não apaga a
nota) + uma rodada real contra o `seth_escriba` de produção (criou uma
entrada de teste real, revertida do working tree antes do commit) + prova
de que o inbox sobrevive a uma regeneração real do vault.

**O que este primeiro passo NÃO faz ainda, de propósito (seguem fases
futuras, não deste commit):** não roda sozinho (precisa ser chamado — virar
timer é trabalho de bootstrap, Fase 3); não tem UI amigável no Obsidian pra
"criar nota nova aqui" (é só uma pasta hoje); não sabe distinguir
CORREÇÃO/CONSELHO/MOD (só escreve DIÁRIO, mesma limitação que a própria
Seth já tem por desenho).

### Fase 5 — Mecanismo de atualização a partir do oficial
O clone precisa buscar melhoria do framework sem herdar a história/memória
do repositório oficial. Padrão candidato: o clone tem DOIS remotos git —
`origin` (o repo do cliente, dele) e `upstream` (o `agata-seth` oficial,
read-only) — e um comando (`agata atualizar-framework`) que faz `merge`
seletivo só dos caminhos "framework" (tabela da seção 0), nunca de
`PROJETO.md`/`MEMÓRIAS.md` do cliente. Mecanismo real de open-source
(mesmo padrão que forks usam pra puxar upstream), não invenção nova.

**Resposta à pergunta "não herdar as rotinas automatizadas, mas receber
benefício/ferramenta/política nova, como fazer?" (25/09/2026):** o corte de
paths (seção 0) já resolve o CÓDIGO do mecanismo (um timer novo, um comando
novo do CLI, um controle novo do perímetro — tudo em `scripts/`,
`.githooks/`, `redesign/*` — flui do `upstream`). O que faltava nomear é o
**ESTADO de execução**, que é outra categoria, nunca deveria fluir:
`~/.cache/agata/*` (checkpoints, `pesquisa-modelos/ultimo.json`,
`perimetro-sombra.log`, o backoff do Conselho Remoto), o histórico de
`propostas/aplicadas/` desta instância, e o AGENDAMENTO em si de um timer
systemd (quando ele rodou pela última vez) — isso é sempre local, nunca
versionado, então nunca está no `git merge` pra começo de conversa. Um
clone que recebe `agata-pesquisa-modelos.timer` novo do `upstream` ganha o
MECANISMO (a ferramenta), mas o timer começa a contar do zero, sem
histórico prévio de execuções — exatamente "receber o benefício sem herdar
a rotina já em andamento". A única disciplina nova que este mecanismo exige
(e que HOJE não existe, porque só há uma instância): o merge seletivo
precisa recusar qualquer caminho fora da tabela da seção 0 mesmo que o
`upstream` um dia tente empurrar algo em `PROJETO.md`/`MEMÓRIAS.md` por
engano — mesma disciplina de allowlist que o P-8 já aplica a `git add -A`,
aplicada agora à direção de entrada, não só à de saída.

### Fase 6 — Onboarding assistido
Antes/durante/depois da instalação, um fluxo conversacional (rodando o
próprio modelo local ou um fallback, já que nesse ponto a infraestrutura
plena ainda não subiu) que pergunta o nome da instância, ajuda a escrever a
primeira entrada de PROJETO.md ("o que é este projeto"), confere que os
serviços essenciais responderam, e SÓ ENTÃO entrega o sistema pronto. Depende
das Fases 3 e 4 estarem prontas.

### Fase 7 — Testado de verdade, não só escrito
Rodar o bootstrap inteiro num container/VM descartável, do zero, e provar
vermelho/verde (mesma disciplina de `testar_perimetro.sh`): sobe limpo,
`perimetro.sh` sai OK, a Seth responde, a atualização do framework não
vaza história da Agata original. Sem isto o bootstrap é só um script que
"parece" funcionar — mesma lição já registrada no catálogo de falhas
(REGRAS): "coerência interna do texto não é sincronia".

## 3. O que fica de fora, de propósito (documentar no PROJETO.md quando a Fase 1 aplicar)

`memoria/missoes/*`, `extras/arquivo*`, `memoria/frio/*` desta instância,
`.hidrata*.md`, ajustes de hardware específicos desta Predator (VRAM,
`mem_sleep_default`, o notebook do Marcos), qualquer segredo real. Um clone
que "puxasse" qualquer um desses estaria quebrando exatamente a garantia que
o Humano pediu ("nunca acessar o projeto original nem as memórias
originais").

**Estado de execução (categoria à parte, nomeada em 25/09/2026 — ver Fase
5):** `~/.cache/agata/*` inteiro (checkpoints, cache de pesquisa de modelos,
log do modo sombra, backoff do Conselho Remoto), o histórico de
`propostas/aplicadas/` desta instância, e o "quando rodou da última vez" de
todo timer systemd. Isto nunca é versionado hoje (já fora do git por
desenho), então a atualização por `merge` da Fase 5 nunca o toca — mas vale
nomear aqui, junto do resto, porque é a resposta direta a "não herdar a
rotina automatizada".

## 4. Ordem recomendada e porquê

Fases 1→2→3 são baixo risco, incrementais, testáveis isoladas, e destravam
a 7 (testar em VM) cedo — quanto antes um bootstrap mínimo roda numa VM,
antes de ter Obsidian-como-vault ou onboarding, mais cedo o "vermelho/verde"
real começa a proteger o resto do trabalho. A Fase 4 (Obsidian primário) é a
mais arquitetural e a única que eu recomendo não começar sem uma decisão
explícita do Humano sobre a pergunta feita nela. Fase 5 e 6 dependem de 3/4
prontas. Fase 0 já está feita.

## 5. Portão das três perguntas (REGRAS, antes de qualquer Fase virar `.diff`)

1. **Desfaço sozinho, ou preciso de alguém de fora?** Fases 1-3, 5, 7: eu
   desfaço (é tudo reversível, testável em clone descartável antes). Fase 4:
   depende da resposta arquitetural — se vira fonte-de-verdade nova, não é
   trivialmente reversível depois que um cliente real gravar memória nela.
2. **O que mais isto toca, além do que pretendo mudar?** Toda a superfície
   hoje hardcoded com "Agata"/caminho fixo de repo (~40 arquivos, levantamento
   ainda não feito byte a byte — primeiro passo real da Fase 2).
3. **Eu saberia se quebrasse, ou só descubro quando for tarde?** Só saberia
   cedo se a Fase 7 (teste em VM) rodar ANTES de qualquer cliente real usar —
   por isso ela entra na ordem recomendada assim que houver bootstrap mínimo,
   não só no fim.
