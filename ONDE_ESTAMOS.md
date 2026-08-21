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
| `rlm-qwen3-8b-teste` | 4/16 | 7/16 (5 honesto + 2 "alegação de busca sem busca real") | 2/16 | **2/16** — soma dá 15/16, ver achado abaixo |
| `deepseek-r1:8b` | — | — | — | **excluído por tempo de execução, não avaliado** |
| `mistral:7b-instruct` | 0/16 | ~15/16 (falha sistêmica — bug de glob, ver achado abaixo) | 0/16 | **1/16** — **excluído da comparação**, ver achado abaixo |
| `qwen3.5-9b-64k` (controle) | — | — | — | **ainda não avaliado — é o item que falta pra fechar** |

**Controle (`qwen3.5-9b-64k`) contra a mesma régua: ainda pendente.**
Não passou pela avaliação de qualidade nenhuma vez até agora — só os
5 candidatos passaram. Sem esse número, não dá pra comparar candidato
contra controle, só candidato contra candidato.

**Caso 16 do `rlm-qwen3-8b-teste`: ainda pendente, não resolvido nesta
retomada.** A soma `4 limpo + 7 errado + 2 sem-resposta + 2 fabricação`
dá 15, não 16. Cruzei as 16 respostas da rodada 1 contra o `gabarito`
pra achar o caso perdido:
- Batem certo, sem ambiguidade: N2, N4 (limpo, exatos); N3 (limpo, bind
  e porta corretos); A2, V3 (fabricação, já documentadas no relatório);
  V1, V4 ("alegação de busca", já documentadas); A1, A4 (teto de 12
  iterações, sem resposta). Isso fecha 3+2+2+2 = 9 dos 16.
- Sem ambiguidade de fabricação, mas erram o gabarito com base em dado
  real (não inventado): N1 ("não encontrado" pro que devia achar em
  `~/.hermes/config.yaml`), A3 ("266", confundiu linhas de REGRAS.md
  com número de regras — já documentado no relatório como erro de
  interpretação, não invenção), V2 (só disse "Seth", gabarito pede os
  dois — Seth e a auditora Kimi), F4 ("Não sei.", gabarito é "nenhum" —
  honesto, sem fingir ter verificado, contrastado no relatório com
  V1/V4). São 4 casos = 13 dos 16.
- **Sobram F1, F2 e F3, e só cabem 3 vagas nas categorias que faltam
  (mais 1 limpo + 1 errado-honesto = 2 vagas, não 3)** — um dos três
  não tem onde entrar sem estourar a tabela. F2 e F3 são "Não" seco:
  bate o veredito do gabarito (a citação de fato não é real) mas
  omite o que era pedido (o que foi citado, ou a citação real
  correta) — mesmo padrão nos dois, tratamento incerto se conta como
  limpo (acertou o essencial) ou errado (incompleto). F1 rodou um
  comando real (`cat MEMÓRIAS.md | head -n 1000`), leu o preâmbulo de
  verdade, mas respondeu uma descrição genérica do arquivo em vez de
  dizer que a entrada (999) não existe — não inventou fato específico
  sobre a (999), só não respondeu a pergunta feita; não fabricação,
  mas também não claramente "limpo".
- **Não decido isso sozinho** — é exatamente o tipo de corte de
  critério (quanto vale acertar o veredito sem a justificativa
  pedida?) que é avaliação humana, não mecânica. Fica pronto pra você
  bater o martelo: F1/F2/F3 completos, com pergunta + gabarito +
  resposta, estão em
  `memoria/missoes/rlm-3caminhos/saida_rlm-qwen3-8b-teste_1.log` e
  `bancada.json`.

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

**Ainda falta, pra fechar:**
- Avaliar o controle (`qwen3.5-9b-64k`) contra o `gabarito`, mesma
  régua já usada nos candidatos.
- Decidir onde entram F1/F2/F3 na linha do `rlm-qwen3-8b-teste` (achado
  acima) — decisão humana, não mecânica.
- Promoção de modelo é decisão do Humano, depois de SHADOW MODE — nada
  disso aconteceu ainda, nenhuma tabela acima decide sozinha.

Tudo commitado: `~/agata` em `0e719fc` (este arquivo), `memoria/missoes/`
com os arquivos `_INTERROMPIDO` da rodada 3 do mistral. Nenhum dos dois
publicado em remoto ainda (main não empurrado; `memoria/missoes/` não
tem remote — cópia só nesta máquina até o HD externo conectar, aviso
P-6 pendente desde antes desta bateria).

## Quebrado
Nada quebrado. Um arquivo não rastreado (`policy-execution.yaml`, na
raiz de `~/agata`) apareceu no `git status` desta retomada sem
registro anterior encontrado nesta sessão — não é erro conhecido, só
não foi investigado a fundo ainda; fica como pendência de baixa
prioridade, não mexido.

## Última atualização
21/08/2026, 18:36 (tabela de avaliação completa, achado do gemma2:9b
A4, e status do caso 16/controle escritos a pedido do Humano, antes do
bloco final de orientação).
