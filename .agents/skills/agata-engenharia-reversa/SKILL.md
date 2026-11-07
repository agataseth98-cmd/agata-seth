---
name: agata-engenharia-reversa
description: >-
  Analisa por leitura estática um aplicativo web ou bundle JavaScript/Electron que o Agata usa (ex.: LibreChat),
  com o REA (rea-agents 6.8.0) já presente no cache do npx, sem instalar, sem setup e sem enviar teclas ao Herdr.
  Use quando o Humano pedir para entender como uma funcionalidade de um app funciona a partir do código entregue,
  comparar versões de bundle ou rastrear um módulo, e o alvo for pasta, ASAR ou captura salva localmente.
  Só para software que o Humano possui ou está autorizado a examinar.
---

# Engenharia reversa por leitura estática (REA)

## Quando usar

- Aplicativo JavaScript/Electron ou bundle web de que se tem cópia local (pasta extraída ou ASAR), ou captura HAR, SAZ, mitmproxy ou qlog já salva.
- Perguntas como "como esta função desse bundle funciona", "o que mudou entre estas duas versões", "de onde vem este módulo".
- Não usar para: revisar código-fonte de repositório (use as ferramentas normais do repo), observar app rodando, depurar processo, instrumentar, nem nada que abra navegador.

## Como chamar

Sempre pelo wrapper, nunca por `npx` (o `npx` pode baixar pacote e gravar no cache do npm):

```bash
bash scripts/rea_leitura.sh <subcomando> <argumentos>
```

O wrapper executa o entrypoint `rea.mjs` (campo `bin` do pacote) do rea-agents 6.8.0 que já está em `~/.npm/_npx/*/node_modules/rea-agents`. Se o pacote não estiver lá, ele para com exit 3 e não baixa nada: avise o Humano.

Teste sem executar o REA: `bash scripts/rea_leitura.sh --selftest`.

## Subcomandos permitidos

Confirmados pelo `rea --help` 6.8.0 como estáticos ou offline sobre arquivos e capturas já salvos:

- `analyze-javascript-application`: reconstrói uma pasta ou ASAR local, sem execução.
- `recover-javascript-sources`: recupera módulos legíveis. Grava em `output_directory` novo e ausente (ver "Destino de escrita").
- `export-web-scripts`: exporta scripts de captura guardada para diretório novo e ausente.
- `trace-javascript-semantics`: relações semânticas estáticas sobre Evidence já gerado.
- `compare-source-to-bundle`: compara fonte histórica com Evidence de aplicação.
- `compare-application-versions`: compara dois grafos de aplicação já analisados.
- `compare-javascript-export-shapes`: formato de retorno de exports, "sem execução".
- `reconcile-javascript-runtime`: concilia Evidence estático com Evidence passivo já salvo.
- `inspect-web-network-capture`: lê HAR, SAZ, mitmproxy ou qlog salvo, "sem buscar URLs gravadas".
- `compare-web-captures`: compara duas capturas normalizadas já salvas.
- `trace-web-module-imports`: importações de um script capturado.
- `trace-web-source-location`: posição de script num source map local explícito.
- `inspect-analysis-view`: projeção de Evidence JSON concluído.
- `inspect-evidence-bundle`: metadados de um bundle local.

## Subcomandos proibidos

Tudo que não estiver na lista permitida é proibido. Os casos abaixo são os mais prováveis e o motivo de cada um:

- `setup`, `update`, `uninstall`, `doctor`, `mcp`: gravam MCP e instruções nos agentes, baixam ou removem o pacote, ou sondam o ambiente.
- `observe-web-session`, `inspect-web-page`, `capture-browser-scenario`, `inspect-electron-page`: abrem navegador ou página viva e observam o app em execução.
- `observe-javascript-runtime`, `list-javascript-runtime-targets`: anexam ao Inspector de Node ou Electron, ou seja, executam o alvo.
- `analyze-web-bundle`: o `--help` diz "Capture", ou seja, abre a página. Não é leitura estática.
- `instrument-with-frida`, `debug-with-gdb`: injetam código ou depuram processo.
- `install-*`, `push-*`, `start-*`, `stop-*`, `list-adb-*`: mexem em dispositivo ou instalam software.
- `export-evidence-bundle`: grava a sessão completa do REA em caminho escolhido.
- `set-*`: altera configuração do REA.
- `annotate-*`: altera anotações de análise salva.
- Flags `--mcp` e `--update`: sobem servidor MCP ou atualizam o pacote. O wrapper recusa em qualquer posição.

## Destino de escrita

Alguns subcomandos permitidos gravam arquivos: `recover-javascript-sources` e `export-web-scripts` (diretório ausente), e `--evidence_output` em `analyze-javascript-application` (bundle, nunca sobrescreve). O wrapper não confere o destino, então a checagem é sua:

- Use caminho absoluto novo, dentro da pasta de trabalho da tarefa.
- Nunca aponte para `~/.claude`, `~/.codex`, `~/.claude.json` ou `~/.config`.
- Se o caminho já existir, pare e pergunte ao Humano.

## Regra de uso com Herdr

- A sessão Herdr `librechat-paridade` fica viva. Esta skill não a encerra nem a reinicia.
- Na operação em paralelo, o Herdr serve só para observação: ler a saída da sessão.
- Não enviar teclas nem comandos a nenhuma sessão Herdr sem pedido direto e explícito do Humano na conversa.

## Proibido sem exceção

- Instalar software, rodar `setup` ou `update`, gravar em `~/.claude`, `~/.codex`, `~/.claude.json` ou `~/.config`.
- Ler `~/.config/agata/.env`.
- Usar sudo.
- Contornar autenticação, login, DRM ou controle de acesso de qualquer site ou app.

## Disclaimer

Só para software que o Humano possui ou está autorizado a examinar. Análise estática produz evidência com limites: reporte a cobertura, as limitações e o que ficou não medido. Não afirme que uma função roda em produção sem medição de execução.

## Como reportar

- Cada afirmação sobre o alvo cita o Evidence ou o trecho lido, e a limitação correspondente.
- Diferencie evidência, inferência e "não medido". Análise estática não prova execução, alcançabilidade nem política aplicada.
