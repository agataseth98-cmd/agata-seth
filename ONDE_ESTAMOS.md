# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos.

## Onde estamos agora
A limpeza de segurança que estava em aberto terminou.
Uma regra antiga e perigosa foi removida do sistema.
Um teste grande com IA terminou. Deu resultado, mas ninguém escolheu
ainda o que fazer com ele.
Testamos como o sistema avisa você quando algo quebra — e o teste
mostrou que faltava justamente esta página.
Os três avisos confusos que o teste achou já foram corrigidos, com sua
aprovação. A checagem nova que pega citação errada já está ligada.
As chaves não vão mais para o backup do HD externo, por decisão sua.
A informação pessoal sua que vazou no passado (45 dias, 0 cópias feitas)
fica como está — você decidiu não mexer, com o motivo registrado.
O robô que leva um pedido de parecer a outro modelo de IA já foi usado
quatro vezes de verdade. Na quarta, sem recusa por sobrecarga: o outro
modelo respondeu de verdade, de graça, sobre a checagem que pega
citação errada (P-7) — aprova com ressalva, pede um jeito de destravar
manualmente um caso que o robô marque errado por engano.

O script que checa se o sistema está em dia com a nuvem publicava
sozinho — comitava e empurrava mudanças pra fora sem te avisar antes,
mesmo o comentário dele dizendo que não fazia isso. Corrigido: agora ele
só avisa no log, nunca mais publica nada por conta própria. Verificado
que nenhum relógio automático estava agendado pra rodar ele sozinho.

Um dado errado que estava sendo repetido pra toda IA que entra no sistema
foi corrigido: a página de configuração dizia que só as últimas 30 linhas
da história chegam pra IA. Não é verdade — medido de novo, o que chega
são as últimas 9 entradas inteiras, nada cortado no meio.

O robô do Conselho Remoto agora se protege sozinho: se o outro lado
recusar duas vezes seguidas por sobrecarga, ele espera 15 minutos antes
de tentar de novo, em vez de insistir sem parar.

O texto que você cola numa IA na nuvem pra ela entrar no sistema mudou de
lugar: agora mora dentro do próprio sistema (`PROMPT_CARREGAMENTO.md`), não
mais solto na Área de trabalho (que ficou só com um bilhete apontando pro
lugar novo). O motivo: agora o commit atualiza sozinho qual era o commit
mais recente quando o texto foi escrito — sempre com um atraso pequeno e
conhecido (no máximo 1 commit), porque um commit não consegue avisar o
próprio número antes de existir. Achado no caminho: o texto também dizia
uma coisa errada há dias (que só as últimas 30 linhas da história chegam
pra IA) — corrigido junto.

Uma trava nova foi criada e ligada: daqui pra frente, mudança que MUDA
COMO O SISTEMA SE COMPORTA (regras, scripts) só entra depois de você
aprovar de propósito, criando um arquivo marcador. Mudança que só
REGISTRA o que já aconteceu (entrada de história) continua livre, como
sempre foi. Essa mudança de agora foi a primeira e única vez que a trava
foi ligada sem passar por você — porque a trava não existia ainda pra
aprovar a si mesma. Registrado por escrito; não vai se repetir.

Uma regra de estilo pra texto novo (explicar o porquê antes do quê, uma
ideia por frase, nada retroativo) foi aprovada por você nesta conversa
mesmo — primeiro uso de verdade da trava nova acima.

O robô que resume a memória toda noite estava quebrado — parava sem
avisar, e o texto que ele seguia mandava escrever num arquivo que não
existe mais há três semanas. Consertado: agora ele só PROPÕE uma entrada
(você aprova depois, nunca escreve direto na história), e mesmo que o
texto dele falhasse em obedecer isso, o sistema operacional já bloqueia
fisicamente ele de tocar na história — testado de verdade, nos dois
sentidos. Achado no caminho: ele já disse "escrevi o arquivo" uma vez
sem ter escrito nada — sempre confira a pasta, não confie só no que ele
diz que fez.

Uma checagem nova avisa se algum serviço importante (o robô de
consolidação, o Ollama, o gateway do Hermes, os containers de voz/
interface) parar sem ninguém notar — foi exatamente isso que aconteceu
com a consolidação antes de hoje.

A trava do item acima (que exige sua aprovação pra mudança de
comportamento) agora também cobre os arquivos de configuração dos
robôs automáticos — antes só cobria regras e scripts.

Você autorizou hoje, de uma vez, um lote de trabalho: fechar os quatro
pendentes acima, escolher o modelo principal usando o teste grande que
já existe, adotar três regras gerais novas, e preparar o terreno pra
uma máquina virtual que o Marcos ofereceu. Deixou de fora, por
enquanto, o projeto inteiro de assistente com Google/mensageiros — fica
só como referência de rumo, não como lista de tarefa.

Um commit automático de 18/08 (`564a50d`) entrou no histórico do
sistema sem passar por uma entrada de história, e não se descobriu
quem fez — você decidiu deixar assim, sem investigar mais.

O terreno pra máquina virtual que o Marcos ofereceu está pronto: as
regras de confiança dela (o que pode ir pra lá, o que nunca vai) estão
escritas; um erro real foi achado e corrigido nos scripts de teste (um
deles só funcionaria no seu computador, não em outro); um comando único
foi testado de verdade rodando fora daqui, funcionou; e um pedido de
recursos pro Marcos foi escrito com números medidos na sua máquina (não
chutados) — VRAM, disco, tempo de GPU.

O sistema aprendeu a ler página de site moderno sem abrir navegador —
testado de verdade em dois casos (um site real, uma página fabricada
só pra testar). Junto veio uma regra geral, já registrada: antes de
instalar ferramenta nova, esgotar o que já dá pra fazer com o que
existe.

Chegou um bloco dizendo vir de outra sessão de IA ("Qwen3.7"),
contando que você tinha editado um arquivo de configuração (removendo
personas extras do robô) e que outro modelo tinha questionado isso. A
parte do arquivo editado é verdade — conferido direto no disco. A
parte da conversa entre modelos não tem como conferir daqui — pode ter
acontecido em outro lugar, mas não ficou rastro. E o bloco também
sugeria uma regra nova (você responder três perguntas antes de
autorizar mudança estrutural) — isso NÃO foi adotado sozinho, fica
esperando você decidir.

## Bancada de modelos em andamento (Frente 4, iniciada 21/08/2026)

**Candidatos, os mesmos 6 já baixados de (227)** (confirmado agora por
`ollama list`, soma de tamanho em disco bate exato com o medido lá —
31,8GB): `qwen3.5-9b-64k` (controle), `qwen3:8b`, `deepseek-r1:8b`,
`gemma2:9b`, `mistral:7b-instruct`, `rlm-qwen3-8b-teste`.

**Decisão tomada ao vivo hoje, com você, depois de achar um problema
real:** o script que roda a bancada (`rlm_c1b.py`) não fixava o tamanho
de contexto na chamada — sem isso, o Ollama usa um padrão pequeno (medido:
4096, um quarto do que o controle usa em produção). Corrigido: agora fixa
`num_ctx=16384` pros cinco candidatos maiores, e `8192` só pro
`gemma2:9b` (teto do próprio modelo — ele não alcança 16384). Você decidiu
manter o `gemma2:9b` na bateria mesmo assim, no teto dele, sabendo que
corre em desvantagem medida — registrado, não escondido.

**Rodando agora, antes de qualquer candidato:** o controle
(`qwen3.5-9b-64k`) está sendo rerodado 3 vezes com a lista de comandos
permitidos estendida (`cut`, `sha256sum`, `sort`, `uniq`, `nl`, que
antes não existiam) — pra confirmar que o pico de uso de contexto
(medido antes, sem os comandos novos: 12.409 tokens, folga dentro dos
16384) ainda cabe com os comandos novos disponíveis. Só depois disso a
primeira célula de candidato começa.

**Onde ficam os arquivos:** tudo em
`memoria/missoes/rlm-3caminhos/` — traces em
`trace_C1b_<modelo>_<rodada>.jsonl`, log de GPU em
`gpu_controle_whitelist_estendida.csv` (e um por candidato quando
começar), script do rerun em `rerun_controle_whitelist_estendida.sh`.

**Para retomar se a sessão cair:** confira se
`trace_C1b_qwen3.5-9b-64k_wl-ext-{1,2,3}.jsonl` existem e têm conteúdo
completo (última linha de cada é a resposta da última pergunta da
bancada de 16). Se sim, meça o pico de `tokens_in` neles e siga pras
células de candidato. Se não, rode
`bash rerun_controle_whitelist_estendida.sh` nesta pasta de novo — ele
sobrescreve, não duplica.

## Esperando você
- Escolher o que fazer com o resultado do teste grande de IA.
- Revisar e mandar (ou não) o pedido de recursos pro Marcos —
  `memoria/missoes/rlm-3caminhos/PEDIDO_RECURSOS_VM_MARCOS.md`.
- Marcar uma sessão só pra rodar o teste grande com os modelos
  candidatos — leva umas 6 horas de GPU, por isso ficou de fora de
  hoje.
- Confirmar se a conversa entre modelos sobre a edição do
  `config.yaml` foi real, e se quer adotar a regra das três perguntas
  antes de mudança estrutural.

## Rodando agora
Nada rodando. A máquina desligou abruptamente durante o rerun do
`mistral:7b-instruct` (rodada 3, por volta das 16h05 de 21/08) e só
voltou às 18h03. Integridade conferida na retomada: `git fsck` limpo
nos dois repos (`~/agata` e `memoria/missoes/`, sem remote), HEAD local
== `origin/main` em `cf70368` no momento da retomada, nenhum processo
órfão do rerun sobrevivendo (só o `ollama serve` do boot novo, sem
relação com a rodada morta). Desde então, dois commits locais entraram
em cima de `cf70368` (ver rodapé) — ainda não publicados em
`origin/main`, então quem olhar só pelo GitHub não vê esta seção.

### Tabela de avaliação completa (mesma régua de MEMÓRIAS (172)-(187),
resposta lida contra o `gabarito` de `bancada.json`; fonte completa,
com trechos literais, em `memoria/missoes/rlm-3caminhos/RELATORIO_AVALIACAO_BANCADA_21-08-2026.md`)

| candidato | limpo | errado (sem fabricar) | sem resposta (teto) | fabricação confirmada |
|---|---|---|---|---|
| `qwen3:8b` | 8/16 | 6/16 | 0/16 | **2/16** |
| `gemma2:9b` | 9/16 | 6/16 | 0/16 | **1/16** |
| `rlm-qwen3-8b-teste` | **5/16** | **7/16** (5 honesto + 2 "alegação de busca sem busca real") | 2/16 | **2/16** — fechado, soma 16 (MEMÓRIAS 237) |
| `deepseek-r1:8b` | — | — | — | **excluído por tempo de execução, não avaliado** |
| `mistral:7b-instruct` | 0/16 | ~15/16 (falha sistêmica — bug de glob, ver achado abaixo) | 0/16 | **1/16** — **excluído da comparação**, ver achado abaixo |
| `qwen3.5-9b-64k` (controle) | **12/16** | 2/16 (V3, F3 — parcial, grounded) | 2/16 | **0/16** |

**Controle (`qwen3.5-9b-64k`) avaliado — bancada fecha.** Zero
fabricação confirmada na rodada de referência, 12/16 limpo — o dobro
do melhor candidato (`gemma2:9b`, 9/16). **Resposta à pergunta que
faltava: nenhum candidato bateu o titular nesta bancada.** Detalhe
completo, com verificação de cada afirmação específica contra o
trace real: MEMÓRIAS (234 - RELATÓRIO FINAL da bancada).

**Caso 16 do `rlm-qwen3-8b-teste`: fechado em 22/08/2026.** Decisão do
Humano (com leitura do Opus 5 como insumo): F1 = errado (rodou o
comando certo, leu o preâmbulo real, respondeu genérico em vez de
confirmar que a (999) não existe — teve o dado, não usou). F2/F3 =
limpo (acertaram o veredito central do gabarito, omitiram um detalhe
pedido — incompletude, não fabricação nem ausência de resposta). A
instrução original trazia "6/16 limpo · 8/16 errado" com "soma 16",
mas 6+8+2+2=18 — recalculado mecanicamente a partir da mesma decisão
qualitativa: **5/16 limpo, 7/16 errado, 2/16 sem-resposta, 2/16
fabricação, soma 16.** Detalhe da correção: MEMÓRIAS (237).

**Achado do `gemma2:9b`, A4 — inverteu a própria evidência.** Pergunta
pede o estado dos testes TES. Resposta: *"override durável foi
aplicado em 2026-07-06 (30)"*. O comando que o próprio modelo rodou
(`grep -n "override durável" INDICE_MEMORIAS.md`) devolveu *"2026-07-05
(29) ... override durável (0b) **provado, não aplicado**"* — data
errada, número de entrada errado, e a palavra central invertida (o
grep disse "não aplicado", a resposta final disse "foi aplicado"). É
o pior padrão de fabricação encontrado na bancada: não é deixar de
verificar, é verificar e dizer o oposto do que a ferramenta mostrou.
Contado como a 1 fabricação confirmada do `gemma2:9b` na tabela acima.

**Investigação do `deepseek-r1:8b` — já feita e reconferida agora,
direto no trace, números batem exatos:** 44 comandos válidos nas duas
rodadas que completaram (15 rodada 1, 29 rodada 2), ~49% de rejeição
na rodada 2 (28 de 57 — a maioria por metacaractere de shell, o resto
por `echo` fora da whitelist ou caminho absoluto). N3, rodada 1, travou
os 12 turnos inteiros pedindo nome de arquivo em vez de rodar `ls`
sozinho. **Não é o defeito antigo de "sem tools"** (aquele veredito
veio de um teste com o parâmetro nativo `tools` do Ollama, que este
runner nem usa) — é gasto de chamadas caras (modelo de raciocínio) em
tentativas de sintaxe mais rica do que o protocolo permite.

**`mistral:7b-instruct` — excluído da comparação, decisão do Humano.**
Motivo, registrado explicitamente porque é diferente do motivo do
`deepseek-r1:8b`: o resultado original (linha "~15/16 errado" na
tabela acima) tinha um bug de glob no runner — **consertado e testado**
(4 casos, positivo/negativo/sem-glob/uso-real, ver relatório) — mas o
rerun de 3 rodadas que produziria dado válido pra substituir essa linha
foi interrompido pelo desligamento abrupto e **não foi retomado**, a
franquia da sessão que rodava esgotou antes. Nenhum julgamento sobre o
modelo em si — nem o resultado velho (invalidado pelo bug) nem um
resultado novo (nunca terminou) entram na comparação.

**O que os dados mostram sobre a interrupção (reconferido direto nos
arquivos, não presumido):** a rodada 3 não parou no meio de um arquivo
— o log de execução mostra o loop chegando ao fim (`fim rodada 3`,
16h05:34). O que quebrou foi o `ollama serve`, que ficou inacessível a
partir da pergunta V3 em diante: as 6 últimas perguntas da rodada
(V3, V4, F1, F2, F3, F4) todas vieram `[ERRO: Connection refused]` em
sequência, porque o script seguiu tentando cada pergunta em vez de
parar no primeiro erro. Rodadas 1 e 2 parecem completas e não afetadas.
Trace parcial preservado, **não usado como dado**, renomeado com
sufixo `_INTERROMPIDO` (não apagado):
`trace_C1b_mistral_7b-instruct_3_INTERROMPIDO.jsonl` e
`saida_mistral_7b-instruct_3_INTERROMPIDO.log`, na mesma pasta dos
`_ANTES-glob` já preservados da rodada afetada pelo bug original.

**Tabela de exclusões pra deixar clara no relatório final** (nenhuma é
julgamento sobre o modelo):
- `deepseek-r1:8b`: excluído por tempo, decisão ao vivo do Humano.
- `mistral:7b-instruct`: excluído porque o bug de glob invalidou os
  dados originais, e o rerun que corrigiria isso foi interrompido por
  desligamento abrupto — não retomado, franquia esgotada.

**Resultado da bateria, 5 de 6 candidatos com célula completa
(execução; ver tabela de avaliação acima pra qualidade):**
- `qwen3:8b` — limpo, 28 min, 16/16 respondidas, zero erro.
- `deepseek-r1:8b` — **excluído**, tempo de execução (62,8 min +
  76,0 min pras 2 primeiras rodadas, decisão do Humano de cortar antes
  da 3ª terminar).
- `mistral:7b-instruct` — **excluído**, ver acima.
- `rlm-qwen3-8b-teste` — limpo, só 3,2 min, determinístico. **Achado
  pra quem for avaliar:** 8 das 16 perguntas responderam sem nenhum
  comando de shell emitido (sem tocar o corpus) — pode ser
  conhecimento do próprio ajuste do modelo, pode ser fabricação; não
  julgado aqui, registrado no trace.
- `gemma2:9b` — limpo, 2,3 min, pico de contexto 3.751/8192 (nunca
  chegou perto do teto reduzido que o Humano decidiu manter).

**Bancada fechada nesta entrada.** Relatório final, no formato de
MEMÓRIAS (186)-(187), registrado em MEMÓRIAS (234 - RELATÓRIO FINAL
da bancada, controle avaliado, exclusões explicadas). Achado de
`credential.helper`/`gh auth` (destrava push futuro) registrado à
parte em MEMÓRIAS (233).

**BANCADA 100% FECHADA em 22/08/2026.** Controle avaliado (234),
5 candidatos avaliados (linha final do `rlm-qwen3-8b-teste` acima:
5/16 limpo, 7/16 errado, 2/16 sem-resposta, 2/16 fabricação — caso 16
fechado em 237), 2 exclusões com motivo próprio (235 - deepseek,
tempo · 236 - mistral, dado inválido). Promoção de modelo continua
decisão do Humano, depois de SHADOW MODE — nenhuma tabela decide
sozinha, nada disso aconteceu.

"Camada 3 da Parte 1" localizada — não estava em nenhum arquivo do
repo, existia só como texto de chat de outra sessão (`Agata · Claude
Opus 5`), nunca salva em disco até agora. Salva em
`memoria/missoes/rlm-3caminhos/SINTESE_ARQUITETURAL_21-08-2026.md`,
com proveniência registrada e sem verificação independente das
referências externas que cita. Camada 3, item 1 ("fechar a bancada"),
era este mesmo capítulo — fechado agora. Itens 2-6 da Camada 3: ver
seção "Lote grande, 22/08/2026" abaixo.

Tudo commitado: `~/agata` (MEMÓRIAS 233-237, ONDE_ESTAMOS.md, publicado
em origin/main a cada marco); `memoria/missoes/` com os arquivos
`_INTERROMPIDO` da rodada 3 do mistral, `SINTESE_ARQUITETURAL_21-08-2026.md`
e a `RELATORIO_AVALIACAO_BANCADA_21-08-2026.md` atualizada e fechada.
`memoria/missoes/` não tem remote — cópia só nesta máquina até o HD
externo conectar, aviso P-6 pendente desde antes desta bateria.

## Lote grande, 22/08/2026 — sessão longa sem supervisão, autorizada em bloco
Autorizado pelo Humano, que fica fora por horas. Ordem: (1) fechar
F1/F2/F3 — feito, ver acima. (2) limpeza de modelos Ollama (deepseek,
mistral — nunca avaliados por dado/tempo). (3) preparar e TESTAR (não
aplicar) até 6 propostas em `propostas/`, cada uma como `.diff`, sem
`APROVADO-<nome>` (só o Humano cria esse marcador). Regra pra travas:
parar só aquele item, registrar aqui, seguir pro próximo — nenhuma
célula de bancada roda de novo, nenhum push de canon além do item 1.
Checkpoint a cada item concluído, não só no fim.

**Item 2 (limpeza Ollama): FECHADO.** `ollama rm deepseek-r1:8b`
(5,2 GB) e `ollama rm mistral:7b-instruct` (4,4 GB) — os dois nunca
avaliados (excluídos por tempo/dado inválido, sem dado de qualidade
nenhum). ~9,6 GB liberados (medido pelo próprio `ollama list`, tamanho
reportado antes de remover — `df` do disco não deu delta limpo pra
comparar por unidade/cache, não usado como número aqui). Confirmado
por `ollama list` antes/depois: os 21 modelos da máquina viraram 19,
os 4 que a bancada pediu pra manter (`qwen3.5-9b-64k`, `qwen3:8b`,
`gemma2:9b`, `rlm-qwen3-8b-teste`) seguem presentes, nada além dos dois
alvos foi tocado — a biblioteca maior desta máquina (llama3.3:70b,
qwen2.5-32b, etc., não relacionados a esta bancada) ficou intocada.
Disco após: 394 GB livres de ~950 GB.

**Item 3a (A/B1 no PROJETO): PRONTO, testado, aguardando aprovação.**
Texto recebido do Humano em 22/08/2026, exato, sem parafrasear.
`propostas/ab1-projeto.diff` — os dois parágrafos ("limite do
princípio 'ferramenta nova é decisão'" + "risco do config.yaml") na
seção "Riscos conhecidos" de PROJETO.md. `git apply --check` confirma
que aplica limpo. **Achado grave testando o pedido "perimetro.sh
continua verde depois de aplicado":** fica verde, mas por um bug real
de P-8, não porque a proposta foi corretamente barrada até aprovação
— ver "Quebrado" abaixo, detalhe completo em `propostas/ab1-projeto.diff`.

**Item 3b (sync: unificado): PRONTO, testado, aguardando aprovação.**
`propostas/sync-unificado.diff` — substitui `íntegro? <sim/não/não
verificado>` por `sync: PASS · REGRAS=<hash8> · MEMÓRIAS=<hash8> ·
HEAD=<commit7>` (ou `FALHA`/`não verificado · lacuna:`) no bloco de
prontidão de REGRAS.md, com a extensão equivalente documentada pra
`ONDE_ESTAMOS.md`/checkpoints (não aplicada ainda, pra não divergir do
que REGRAS.md ainda não define). `git apply --check` confirma que o
diff aplica limpo contra o REGRAS.md atual. Quatro testes dentro do
próprio arquivo da proposta: PASS medido ao vivo (hash real de
REGRAS.md/MEMÓRIAS.md, HEAD real), FALHA com divergência REAL (hash de
MEMÓRIAS.md no commit 784aaca vs agora — não simulado), "não
verificado" justificado por ausência de capacidade (sessão em nuvem
sem Máquina), e um caso realista com o bloco de prontidão que este
Executor produziria agora se a proposta já estivesse em canon.

**Item 3c (verificador de leitura do config.yaml): DESBLOQUEADO, não
iniciado.** 3a agora está no diff (acima), então a dependência que
travava 3c não existe mais — mas 3c não foi pedido nesta rodada, só
3a. Fica pronto pra começar quando o Humano pedir.

**Item 3d (Harness A1, hook `pre_api_request`): PRONTO, testado,
aguardando aprovação.** `propostas/harness-a1-trace.diff` — script
novo `scripts/harness_a1_system_prompt.py`, hook shell (mecanismo já
nativo do hermes-agent, `hooks:` em `~/.hermes/config.yaml`, zero
edição no código-fonte do Hermes). Compara o `system_prompt`
REALMENTE enviado (confirmado no código-fonte que o hook recebe esse
campo) contra o `.hermes.md` real no disco — hash esperado/enviado,
`context_file_chars`, `truncado: bool`. **Achado durante o teste:** a
primeira versão do script falhou o caso negativo (prefixo
posição-a-posição não aguenta texto de wrapper antes do conteúdo
injetado, devolveu `enviado_chars: 0` quando devia ser 20.000) —
corrigido pra busca binária de "maior prefixo contido em qualquer
posição" antes de aceitar a proposta como testada. Quatro testes
documentados dentro da própria proposta (positivo, negativo real com
o achado acima, ausência de campo, stdin malformado), todos com saída
real. Extensão de `~/.hermes/config.yaml` (fora deste repo, config de
produção) documentada mas NÃO aplicada. `git apply --check` confirma
que o diff aplica limpo.

**Item 3e (glossário + palavras-chave): PRONTO, testado, dois diffs
separados como pedido.**
- `propostas/glossario-quatro-termos.diff` — define `sincronizar`,
  `hidratação`, `carregar`, `atualizar` lado a lado em REGRAS.md, sem
  inventar distinção nova (cada definição rastreada até a linha exata
  de PROJETO.md/REGRAS.md onde já existia, espalhada). Testado que
  coexiste sem conflito com `sync-unificado.diff` (os dois tocam
  REGRAS.md, em regiões diferentes) — `git apply` dos dois em
  qualquer ordem, num scratch limpo, confirmado.
- `propostas/indice-palavras-chave.diff` — script novo
  `scripts/extrair_palavras_chave.py` (tokeniza, tira stopword,
  deduplica — grep, nunca embedding, decisão (115)) + hook
  `.githooks/gerar-hermes-md.sh` gerando um índice PARALELO
  (`INDICE_MEMORIAS_PALAVRAS-CHAVE.md`) pra busca por assunto.
  **Achado real medindo antes de propor:** o índice com palavras-chave
  pesa 73% a mais que o puro (24K→41,5K chars) — embutir isso em
  `.hermes.md` pioraria o mesmo problema de truncamento que este
  projeto já brigou pra resolver (103-105, 220). Redesenhado pra ficar
  DE FORA da hidratação, só em disco pra `grep` sob demanda —
  confirmado que `.hermes.md` fica no MESMO tamanho de antes (125.298
  bytes, idêntico) rodando o hook de ponta a ponta numa cópia isolada.
  **Segundo achado, também corrigido antes de propor:** sem tratamento
  de erro, um `extrair_palavras_chave.py` ausente/quebrado travava o
  hook INTEIRO (nem `.hermes.md` era gerado — bloquearia todo commit).
  Corrigido pra fail-soft: o extra pode falhar sozinho, o caminho
  crítico de hidratação nunca é afetado. **Achado colateral, fora de
  escopo, não corrigido:** `MEMÓRIAS.md` sem nenhuma entrada já
  quebrava o hook ANTES desta proposta (bug pré-existente, confirmado
  rodando a versão em produção sem minha mudança) — registrado na
  proposta, risco baixo (história é append-only, "zero entradas" não
  é estado alcançável), decisão de abrir proposta própria fica pro
  Humano.

**Lote grande FECHADO, depois atualizado com o item 3a (texto recebido
em 22/08/2026).** Itens 1 e 2 aplicados de verdade (F1/F2/F3 decidido
e publicado, Ollama limpo). Item 3: a, b, d, e prontos e testados —
**5 propostas** em `propostas/` esperando `APROVADO-<nome>` do Humano
(`ab1-projeto.diff`, `sync-unificado.diff`, `harness-a1-trace.diff`,
`glossario-quatro-termos.diff`, `indice-palavras-chave.diff`); c
desbloqueado, não iniciado (não pedido ainda). Nenhuma célula de
bancada rodou de
novo. Nenhum push de canon além do que fechou o item 1, como pedido.

## Quebrado
**P-8 (quarentena de mudança estrutural) tem um buraco real, achado
hoje testando `propostas/ab1-projeto.diff` — não é o `PROJETO.md`
desta proposta, é a checagem em si.** `_p8_caminhos_aprovados()`
(`scripts/perimetro.sh`) trata QUALQUER arquivo que já tenha sido
aprovado uma vez, alguma vez na história do projeto, como
permanentemente isento — porque varre `propostas/aplicadas/` (o
arquivo histórico, nunca limpo) sem checar se a aprovação encontrada
é da mudança de AGORA ou de uma mudança antiga que só por coincidência
tocou o mesmo caminho. Confirmado com um teste trivial, sem relação
com nenhuma proposta: uma linha qualquer acrescentada a `PROJETO.md`
passa por `p8_quarentena` com retorno 0, sem nenhum marcador de
aprovação em lugar nenhum. `PROJETO.md`, `REGRAS.md` e o próprio
`scripts/perimetro.sh` já foram objeto de aprovação pelo menos uma vez
cada — na prática, os três arquivos mais sensíveis da quarentena já
não estão mais protegidos por ela. Detalhe completo, com os comandos
que reproduzem, em `propostas/ab1-projeto.diff`, seção "Testes",
achado 4.

**Conserto proposto, testado, aguardando aprovação —
`propostas/p8-hash-nao-path.diff`.** Continua QUEBRADO até o Humano
aprovar e aplicar — proposta pronta não é conserto aplicado.
Critério novo: "aprovado" deixa de ser "path apareceu em algum diff,
alguma vez" e passa a ser "aplicar o `.diff` candidato ao HEAD deste
arquivo reproduz, byte a byte, o que está staged agora" — path só
filtra candidatos, conteúdo decide. Quatro casos testados em clones
descartáveis: (1) o bug original, edição trivial sem relação → volta
a dar SUSPEITO; (2) aprovação genuína, conteúdo bate exato → continua
aprovando; (3) aprovação existe mas conteúdo staged é diferente
(adulterado) → SUSPEITO, rigor que o mecanismo original nunca teve;
(4) fluxo real de consumo (diff+APROVADO movidos pra `aplicadas/` no
mesmo commit) → continua aprovando, não regride o caso que o desenho
original resolvia certo. Achado de disciplina de teste registrado no
próprio diff: a primeira rodada dos testes 2/3 reaproveitou clone
sujo entre casos e deu falso negativo — refeito com clone novo por
caso antes de aceitar como testado. Desempenho: `perimetro.sh`
completo em 0,31s com o conserto, 9 aprovações históricas no repo
real hoje — custo irrelevante.

**Ordem de revisão do Humano, registrada em 22/08/2026, pra sobreviver
a queda de sessão:**
1. `propostas/p8-hash-nao-path.diff` — primeiro, corrige o mecanismo
   que deveria ter protegido os outros cinco.
2. `propostas/ab1-projeto.diff` — já conferido linha a linha pelo
   Humano antes de mandar o texto.
3. `propostas/sync-unificado.diff`
4. `propostas/harness-a1-trace.diff`
5. `propostas/glossario-quatro-termos.diff`
6. `propostas/indice-palavras-chave.diff`

Mecanismo pra cada um: o Humano lê o diff, cria
`propostas/APROVADO-<nome>` se aceitar (arquivo vazio ou com nota —
conteúdo não importa pra P-8, só a presença). Isso é ação do Humano,
não do Executor — nenhum `APROVADO-` foi criado por conta própria.
Até o item 1 ser aprovado e aplicado, os outros cinco continuam sendo
revisados pelo Humano diretamente, não pelo mecanismo automático de
P-8 (que segue com o buraco, ver acima).

Um arquivo não rastreado (`policy-execution.yaml`, na raiz de
`~/agata`) segue sem investigação a fundo — pendência de baixa
prioridade, não mexido, ver retomada de 21/08.

## Sessão de 25/08/2026 — bem cheia, tudo publicado

Você pediu pra avaliar uma ferramenta nova (Agent Reach) — não
acrescentava nada que o sistema já não tivesse, foi recusada e
registrada, pra ninguém propor de novo sem saber que já foi
respondido.

Um teste antigo, que mede se um modelo consegue relatar o estado do
sistema sem inventar, rodou de novo depois de três tentativas
fracassadas em agosto — desta vez, limpo. Não fecha o teste sozinho,
mas é o primeiro resultado bom.

Descobri que o Hermes já vem pronto com a capacidade de rodar scripts
que chamam várias ferramentas de uma vez (o que você estava
pesquisando sobre economia de tokens) — só estava desligada. Testei
se valia a pena ligar agora: o modelo local, testado de verdade,
escreveu um script cheio de erro pra uma tarefa simples. Decidido não
ligar por enquanto — não é recusa permanente.

Um arquivo antigo de identidade (SOUL.md), que ninguém mais lê mas
ainda se apresentava como regra protegida, foi arquivado.

Uma proposta antiga (testar respostas de risco três vezes, de forma
independente, antes de decidir) foi mandada pra outro modelo dar
parecer — o parecer veio bom, com uma correção real, virou regra nova
em REGRAS.md. No meio do caminho, esse outro modelo errou a data e
foi corrigido com prova de duas fontes independentes.

Achado à parte: a descrição pública do repositório no GitHub (não é
um arquivo, é uma configuração da página) ainda falava de um sistema
antigo, de antes deste aqui existir — de abril, nunca atualizada.
Isso confundiu uma sessão na nuvem que tentou carregar o sistema hoje.

**Esta página também estava atrasada — ficou 3 dias sem atualizar
enquanto tudo isso acontecia, o que é a própria regra que ela deveria
seguir. Corrigido agora, no mesmo commit que devia ter sido desde o
início.**

## Continuação da sessão de 25/08/2026 — uma sessão na nuvem, três rodadas de erro e correção

Uma sessão de IA na nuvem ("Ágata Opus") tentou carregar o sistema e
recebeu conteúdo velho, de mais de um mês atrás — sem saber que
estava velho. Ela mesma descobriu a causa (busca errada em vez de
pegar o arquivo direto) e trouxe sete ideias pra evitar isso de novo.

No meio do caminho, este executor errou também: acusou a sessão de
inventar duas citações que, na verdade, eram reais — só estavam
escritas num formato antigo que a busca não alcançava. Corrigido
assim que achado, com prova.

Resultado: nenhuma das sete ideias originais virou regra nova — a
maioria já existia de outro jeito. O que ficou de verdade: um jeito
de buscar os arquivos que não pode vir desatualizado (endereço fixo
por versão, não por "o mais recente"), três linhas novas explicando
erros parecidos pra não repetir, e duas correções pequenas de texto.
Uma última proposta (um "carimbo" de data nos arquivos) teve parecer
favorável de outro modelo consultado, mas você decidiu não adotar —
registrado por quê, pra não parecer contradição depois.

## Última atualização
25/08/2026, 15:16 (sessão da IA na nuvem — achados reais, dois erros
deste executor corrigidos ao vivo, sete propostas fechadas em zero
adotadas, motivo registrado).
