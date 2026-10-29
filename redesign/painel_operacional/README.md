# Painel operacional local

O painel serve estado local da Agata e, na rota `/conselho-rede`, o Conselho de Modelos em Rede. A página de conversa, a API e a fila de aprovação usam o mesmo processo HTTP do painel em `127.0.0.1:20146`; não há serviço separado para o Conselho. O pacote `relay-extension-v2/` consulta a fila e automatiza interações nas abas de chat Chromium depois da aprovação humana.

## Executar

Na raiz do repositório:

```sh
python3 redesign/painel_operacional/server.py
```

Abra `http://127.0.0.1:20146/prototipo` e escolha **Conselho de Modelos em Rede**, ou acesse diretamente `http://127.0.0.1:20146/conselho-rede`. Instale/atualize `redesign/painel_operacional/relay-extension-v2/` como extensão não empacotada no Chromium e habilite-a. O painel e a extensão devem pertencer à mesma versão da entrega. Para encerrar uma execução manual, use Ctrl-C no terminal em que ela foi iniciada.

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
- A interface pausa consultas quando oculta e conserva última leitura válida como vencida se uma coleta falha. Ausência de resultado não prova ausência no canon.

## Verificar em cópia isolada

```sh
python3 redesign/painel_operacional/server.py --selftest
python3 -m unittest discover -s redesign/painel_operacional -p 'test_*.py'
node --check redesign/painel_operacional/prototipo.js
```

Os testes do Conselho usam respostas e endpoints simulados; não autenticam nem enviam prompts a provedores reais. A integração em runtime só deve ser ligada após a proposta P-8 assinada e aplicada.

## Fronteiras

O servidor permanece preso a loopback. As rotas mutáveis exigem origem local, token CSRF e payload limitado. O identificador público da extensão não autentica outros processos locais; loopback também não é autenticação. Isso não substitui a aprovação do Humano. O painel não assina nem aplica propostas, não altera arquivos canônicos e não recebe credenciais.
