# Painel operacional local

O painel serve estado local da Agata e, na rota `/conselho-rede`, o Conselho de Modelos em Rede. A página de conversa, a API e a fila de aprovação usam o mesmo processo HTTP do painel em `127.0.0.1:20146`; não há serviço separado para o Conselho. O pacote `relay-extension-v2/` consulta a fila e automatiza interações nas abas de chat Chromium depois da aprovação humana.

## Executar

Na raiz do repositório:

```sh
python3 redesign/painel_operacional/server.py
```

Abra `http://127.0.0.1:20146/prototipo`. A tela tem oito seções, escolhidas pelo menu lateral ou pelo hash: `#panorama`, `#conversa`, `#conselho`, `#sistema`, `#conhecimento`, `#historia`, `#custos` e `#qualidade`. Hash desconhecido abre o Panorama. Links antigos (`/`, `/index.html`, `/frentes`, `/operator_console`, `/conselho-rede`) redirecionam para a seção certa. Instale/atualize `redesign/painel_operacional/relay-extension-v2/` como extensão não empacotada no Chromium e habilite-a. O painel e a extensão devem pertencer à mesma versão da entrega. Para encerrar uma execução manual, use Ctrl-C no terminal em que ela foi iniciada.

## Telas do /prototipo

- Cada tela antiga virou um subpainel (`sub-<nome>`) dentro de uma seção. A tabela de funções está em `spec/spec.md` (seção Mapeamento de funções).
- A busca única de Conhecimento serve à Alexandria (escopo `dentro`), ao Acervo com busca externa (escopo `fora`) e à documentação da Agata (escopo `documentacao`).
- Estado carregando, vazio e erro aparecem em cada seção que consome API. Erro é "não medido"; valor antigo, se houver, sai com a hora dele.
- Conversa com a Seth (16/11/2026): o menu lateral é a única lista de conversas, em grupos por data, com um menu de ações por item. Arquivadas, Lixeira, Organizar conversas e Serviços ficam no rodapé do menu. A tela da conversa não repete a lista; o cabeçalho tem o seletor de modelo, a Temporária e o menu Mais.
- Conhecimento numa tela só (16/11/2026): os cinco blocos (Memória e mapas, Grafo do vault, Documentação viva, Alexandria e Acervo e fontes) aparecem juntos, sem abas; as âncoras no topo levam a cada um.
- Gaveta em tela estreita (até 1023 px): o botão Menu abre; Fechar, Esc, clique fora ou a escolha de uma seção ou conversa fecham. Dentro da gaveta, a lista de conversas tem rolagem própria e o rodapé fica fixo.
- O estilo é um arquivo só, `prototipo.css`, com tokens em `:root`. Cada cor hexadecimal ou rgb virou token nomeado pelo valor (`--cor-...`); não há cor literal fora de `:root`.
- Os scripts ficam em IIFE. O único nome global é `window.AgataPainel`, usado por `nova_versao.js` para falar com o `prototipo.js`.

## Telas de operação (lote 2b, 17/11/2026)

- Listas únicas: "O que posso fazer" e Integrações são uma lista só, em Sistema > Integrações. Provedores aparecem numa tabela só (Sistema > Conexões). Timers e tarefas ficam só em Manutenção. Lacunas ficam só em Qualidade > Lacunas. A Visão do sistema tem só números e atalhos.
- Sistema > Equipe (`/api/equipe`): sessão, presentes e ausentes, divergências em destaque, itens por estado, vigias e eventos. Sessão sem lista de esperados: a tela diz "sessão sem lista de esperados".
- Sistema > Backup (`/api/backup` e `/api/perimetro`): primeiro o veredito do P-12 do último perímetro gravado, com a data; depois HD e repositório; por último o registro de cobertura (última verificação anotada), com a régua dele, que não é o veredito do P-12. Sem `ultimo.json` do perímetro, "P-12: sem leitura".
- Sistema > Saída de rede (`/api/egress`): binários egress e egress-socks5 em dia pelo mtime; navegador usa Rust; paridade.
- Qualidade > Perímetro (`/api/perimetro`) e Qualidade > CI (`/api/ci`): último resultado gravado por `scripts/perimetro.sh` e `scripts/ci_sdd_local.sh`, com head, idade e contagens; no CI, falhas primeiro.
- Qualidade > Qualidade de LLM (`/api/qualidade-llm`): a recuperação é um indicador com as duas leituras (corpus do vault e conjunto da avaliação), cada uma com valor, estado, fonte e `medido_em`. Medição ocupada responde HTTP 429 com `motivo`, e o botão mostra o motivo.
- Fonte única de provedores: `/api/provedores` responde `items` e `total`; os botões do Conselho e a tabela saem dela.
- Contrato das rotas de leitura: `schema_version` 1, `state`, `source`, `observed_at` e `fresh_until`; sem leitura, `state` `sem_leitura` com `motivo`. Campos por rota na seção Contrato da spec ("Lote 2b").
- O painel não executa `scripts/perimetro.sh` nem `scripts/ci_sdd_local.sh`. As rotas só leem o arquivo gravado por eles (`ultimo.json`); a tela diz "O painel não roda o perímetro; mostra o último resultado gravado."

## Conselho em Rede

- A página prepara prompts individuais, debates, cadeias e baterias de ensaio. O roster experimental contém nove chats: DeepSeek, Gemini, Z.ai, ChatGPT, Claude, Grok, Qwen, Mistral e Kimi. Só IDs detectados em abas abertas aparecem como destinos; a detecção não comprova login nem prontidão. Preparar uma rodada apenas cria pedidos pendentes; cada prompt, continuação e síntese precisa de aprovação humana separada.
- O painel inclui o manifesto de ferramentas no prompt aprovado. Respostas de modelos são dados não confiáveis. Tags completas em linha própria podem criar pedidos de ferramenta, que aparecem numa fila distinta e também exigem aprovação humana antes da execução.
- A lista permitida de ferramentas é `SEARCH`, `STATE`, `CACHE`, `AUDIT`, `RELAY` e `DELIVER`. Buscas e leituras são locais e limitadas; `DELIVER` prepara texto para revisão. Uma ferramenta não recebe comandos arbitrários nem executa código.
- A extensão detecta abas por host permitido, consulta `/api/relay-council/tasks` e executa a tarefa aprovada na aba correspondente. Ela pode focar temporariamente a aba para modelos que exigem visibilidade e tenta restaurar a visualização anterior. Não cria abas ausentes e não tem permissão para ler cookies. O resultado volta por `/api/relay-council/result`, validado por lease e ID do provedor. Timeout ou reinício não provoca reenvio automático; o estado incerto fica visível para decisão humana.
- A fila e o histórico novo ficam em SQLite sob `~/.local/share/agata/painel-conselho/official/`. O histórico anterior em `~/.local/share/agata/painel-conselho/history.jsonl` é lido somente para exibição; não é movido nem reescrito.
- O transporte local usa HTTP em loopback; prompts vão às páginas de chat por interação DOM da extensão. A extensão só recebe host permissions para os chats listados e o painel local, sem permissão `cookies`; ainda assim, o adaptador lê e altera o DOM dessas páginas. Não contorna CAPTCHAs, limites, login ou controles do provedor. O painel não lê `.env` nem guarda credenciais. Adaptadores não testados em cada site permanecem experimentais.
- A rota `/api/relay-council/catalog` continua servindo o roster tipado. O endpoint legado `/api/relay-council/evaluations` permanece para compatibilidade do registro manual, sujeito ao contrato e à sanitização existentes.

## Restante do painel

- `/api/status` consulta unidades, Git, timers, tarefas, propostas locais e o catálogo de capacidades, com origem, horário e validade para as leituras.
- `/api/details` consulta sob demanda integrações e contagem de notas do vault derivado. Unidade ativa não prova funcionamento completo da integração.
- `/api/wiki/search` usa o verificador local, limita consulta e retorno e não guarda histórico.
- A leitura `/api/seth/conversa?id=` valida o arquivo e devolve `schema_version` e `id` esperados pelo cliente; mensagens importadas de até 65536 caracteres podem ser reabertas e salvas.
- Conversas (09/11/2026): apagar move a conversa para `~/.cache/agata/painel-conversas/.lixeira/`, de onde ela volta com `restaurar`; apagar de vez é pedido manual, com confirmação. Toda escrita de conversa exige origem do painel (`Origin` igual ou `Sec-Fetch-Site: same-origin`; sem cabeçalho, 403) e gera uma linha em `.registro.jsonl`, sem conteúdo. Arquivo de conversa que não pode ser lido é contado na tela e não é apagado.
- `/api/conselho/memoria?n=40` (aba Conselho > Memória compartilhada, pedida em 07/11/2026) lê só o cache do Conselho: `n` de 1 a 200, mais recentes primeiro, com o mesmo filtro de dado pessoal e segredo da gravação. Não escreve no cache e não aceita caminho do cliente.
- A interface pausa consultas quando oculta e conserva última leitura válida como vencida se uma coleta falha. Ausência de resultado não prova ausência no canon.
- Sob demanda e recarga (23/11/2026): unidade parada de propósito (lista fixa em `SOB_DEMANDA_FIXA`, decisão de 29/10/2026, ou socket de mesmo nome escutando) sai como `sob_demanda` com o motivo, e não como aviso. Unidade em `failed` sai como `erro`. A mesma regra vale em `/api/lacunas` (parada de propósito não é lacuna) e em `/api/capacidades` (capacidade `sob_demanda`, como o timer de manutenção). A sub-tela visível de leitura recarrega a cada 60 s, sem recarregar com a página oculta nem com edição em curso. Detalhes em `spec/spec.md`, "Sob demanda e recarga".

- Importantes (11/11/2026, pedido do Humano): aba Importantes dentro de Panorama, com cartão "Importantes: N abertos" no próprio Panorama. A lista fica em `~/.cache/agata/painel-importantes.json`, fora do repositório. Criar, marcar feito, descartar, reabrir e editar não apagam nada: descartado fica guardado. `POST /api/importantes/trazer` lê o cache do Conselho (sem escrever nele) e traz as entradas cujo texto começa com `IMPORTANTE`, sem repetir; texto com segredo não é trazido. Toda escrita exige origem do painel e gera uma linha em `painel-importantes.registro.jsonl`, sem texto.

## Verificar em cópia isolada

```sh
python3 redesign/painel_operacional/server.py --selftest
python3 -m unittest discover -s redesign/painel_operacional -p 'test_*.py'
# suíte do painel (inclui test_painel_unificado.py; o teste de globais usa node)
pytest -q redesign/painel_operacional
node --check redesign/painel_operacional/prototipo.js
```

Os testes do Conselho usam respostas e endpoints simulados; não autenticam nem enviam prompts a provedores reais. A integração em runtime só deve ser ligada após a proposta P-8 assinada e aplicada.

## Fronteiras

O servidor permanece preso a loopback. As rotas mutáveis exigem origem local, token CSRF e payload limitado. O identificador público da extensão não autentica outros processos locais; loopback também não é autenticação. Isso não substitui a aprovação do Humano. O painel não assina nem aplica propostas, não altera arquivos canônicos e não recebe credenciais.
