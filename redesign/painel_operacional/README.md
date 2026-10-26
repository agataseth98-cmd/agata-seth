# Painel operacional local

Interface dinâmica somente de leitura para quatro unidades de usuário e o estado local do Git, consultados pelo seth-verificador.
Inclui busca do wiki sob demanda, usando somente os comandos fixos `busca_texto` e `busca_semantica` do mesmo verificador. As fontes são `memoria/obsidian/` e `extras/`, conforme as implementações versionadas; o índice por sentido é local.

## Executar

Na raiz do repositório:

~~~sh
python3 redesign/painel_operacional/server.py
~~~

Abra http://127.0.0.1:20146/. O servidor encerra com Ctrl-C. Ele não instala nem inicia unidade systemd.

## Escopo

- Consulta somente as quatro unidades fixas em server.py, pelo comando allowlisted unidade do seth-verificador.
- Lê branch, HEAD e quantidade de alterações por git_status e git_log do seth-verificador; não envia nomes de arquivo ao navegador.
- Atualiza a cada 60 segundos e pelo botão da página; pausa em aba oculta.
- Deduplica GETs sequenciais por 3 segundos e registra observação/validade ao concluir cada fonte.
- Entrega origem, referência e horário por unidade; Git traz origem, referência local, commit e validade próprios.
- O sinal geral considera apenas unidades systemd. Git permanece separado; árvore modificada não é falha de serviço.
- Usa desconhecido quando não há leitura válida e desatualizado para valor anterior que venceu; preserva a última leitura no navegador após falha.
- A região acessível anuncia apenas mudança, expiração ou falha, sem reler o painel inteiro a cada minuto.
- Verifica Host e rejeita requisições à API marcadas como cross-site ou com Origin alheira. É defesa adicional; loopback não autentica o solicitante.
- Não aceita comandos livres, escrita, assinatura ou acesso ao /live-ws. O único POST permitido envia uma consulta de busca local ao verificador.
- A busca do wiki aceita apenas texto de até 200 caracteres e os modos texto, sentido ou ambos; a consulta é dado de comandos allowlisted, sem execução livre, histórico ou persistência. Cada resultado é limitado a 12.000 caracteres e sinaliza total e corte.
- O resultado de busca é guia de navegação, não evidência final. Confirme o conteúdo no canon antes de citar; a interface apresenta fonte e hora de observação.
- Escuta apenas em 127.0.0.1; serve apenas três arquivos fixos da própria pasta.

A página não instala o protótipo da Área de trabalho nem seus assets. Essa cópia permanece independente e estática.

## Limites desta primeira fatia

O sinal não representa todos os serviços da Agata. Não inclui containers, timers, propostas ou saúde dos modelos. A comparação de Git usa apenas a referência local do último fetch; não consulta a rede. O relógio exibido vem do relógio local. O prazo de frescor de 60 segundos é inicial e ainda não foi ajustado por medição de carga.

A tela não altera o vault nem escreve no canon. A esfera pessoal não está na busca. A exposição permanente via systemd ou acesso remoto fica fora deste recorte e exige proposta própria pelo fluxo de mudança segura.
