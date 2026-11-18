# Spec — Conexões de modelos e redundância por capacidade (nova versão, lote 2)

Componente da nova versão. Spec-mãe: `redesign/nova_versao/spec/spec.md` (C7). Origem: Experimento GPT, (040), (043)–(047), matriz de redundância. Decisões do Humano em 04/11/2026: "as duas são: Claude e Chat GPT. Devem servir de exemplo para futuros usuarios conseguirem conectar as de sua preferencia"; "todas as opções disponiveis e o preenchimento de API deve ter aba segura de configuração onde fizer mais sentido no painel".

## Jornadas críticas

1. O Humano grava a chave de API de um provedor no painel; a chave fica no cofre e nunca volta à tela.
2. O Humano liga uma categoria no orçamento e manda testar as rotas; vê por capacidade quais rotas passaram e por quê as outras não.
3. Um usuário futuro acrescenta o provedor de sua preferência pelo mesmo formato, pelo painel (API) ou pelo catálogo (CLI).

## Contrato

- `provedores.json`: catálogo versionado com `claude` e `chatgpt` nos três caminhos (`navegador` via `relay_id`, `cli` com `argv`/`argv_modelo`/`saida`, `api` com `formato` `anthropic`|`openai`, `url`, `env`, `prefixo_chave`, `modelo`) e a `categoria_orcamento` de cada caminho (`cli` → `assinatura`, `api` → `pago`).
- `segredos.py`: cofre em `AGATA_CONEXOES_DIR` (padrão `~/.config/agata/conexoes/`, pasta 0700, `<id>.chave` 0600, gravação atômica). Valida id e formato da chave (20–300 caracteres, sem espaço, prefixo do provedor). `estado_de` diz só se existe, desde quando e se a permissão está fechada; `_para_chamada` é o único leitor. Gravar e remover viram evento `private` no ledger, sem valor. Não lê nem escreve `~/.config/agata/.env`.
- `adaptadores.py`: `catalogo()` junta o versionado com `provedores.local.json` (só API, só https, nunca comando) e `ajustes.local.json` (modelo, tarifa com fonte e data). `chamar(pid, modo, prompt)` nunca envia pelo navegador; antes de sair confere orçamento, privacidade (`sanitizar.varrer_pessoal`; sem a régua, trata como privado) e, na API, tarifa e teto em R$ pelo gasto acumulado em `gasto.jsonl`. CLI roda em pasta temporária vazia, com `stdin` fechado. Falha vira `falha_etapa`, nunca exceção.
- `configurar.py` (17/11/2026): `listar` mostra provedores, endpoint e se a chave existe, só pelo nome (`segredos.estado_de`), sem valor. `adicionar --id --base-url --chave-env --modelos [--formato] [--nome]` acrescenta ao `provedores.json` só bloco de API (`categoria_orcamento` `api` → `pago`; sem `cli` nem `navegador`), com `api.modelos` (lista; o primeiro vira `api.modelo`). `--base-url` vira endpoint (`/chat/completions` ou `/messages`) e aceita `https` (host DNS válido, porta 1-65535) ou o gateway `http://127.0.0.1:20127` (sanitizador) e `:20128` (OmniRoute). Recusa id repetido (catálogo e `provedores.local.json`), `--chave-env` que não seja nome de variável e argumento desconhecido, sem repetir o valor digitado. Leitura, checagem, gravação do catálogo e tarifa ficam sob a mesma trava `flock` em `provedores.lock` no cofre; se qualquer passo depois da primeira gravação falhar (inclusive o registro do evento), o catálogo volta e só a chave deste id sai de ajustes; alterações do painel em outros ids sobrevivem. Com `--tarifa-entrada`, `--tarifa-saida`, `--cambio`, `--tarifa-fonte` e `--tarifa-data`, grava por `adaptadores.ajustar` (mesmo formato do painel, em `ajustes.local.json`); tarifa incompleta ou fora do limite é recusada antes de qualquer gravação. Toda chamada do bloco segue por `adaptadores.chamar()`.
- `testar_rotas.py`: rotas permitidas pelo orçamento (`local` = tags do Ollama sem embedding; `gratuito` = modelos `available` do OmniRoute, sem `/auto`; `assinatura` e `pago` = conexões prontas), três provas fixas e mecânicas (conversa, JSON, código), coordenadas por `redesign/nova_versao/tarefas.py` (GPU em fila única, remoto em paralelo, teto de chamadas, cancelamento). Guarda veredito, etapa de falha, latência, uso e independência; nunca guarda a resposta. Não altera filas do OmniRoute.
- O corpo (`redesign/corpo/fotografar.py`) preenche `testado` e `pronto` pelo último teste.

## Critérios de aceite

- [ ] a chave vai para o cofre 0600 e nunca volta em estado, resposta ou ledger
- [ ] orçamento, privacidade e custo barram a chamada antes de sair
- [ ] o programa da assinatura roda em pasta vazia, sem ferramentas e sem sessão
- [ ] provedor novo pelo painel é só API com https e sem id repetido
- [ ] o teste de rotas é por capacidade, descreve a independência e não guarda a resposta
- [ ] adicionar grava um provedor de API pago num comando, sem cli nem navegador
- [ ] o provedor adicionado pela CLI passa pelas mesmas portas de chamada: orçamento, custo e cofre o barram antes de qualquer chamada de rede
- [ ] configurar recusa id repetido, endpoint com esquema, host ou porta inválidos, chave que não seja nome de variável e argumento desconhecido, sem ecoar o valor
- [ ] listar mostra os provedores e se a chave existe só pelo nome, sem imprimir valor
- [ ] adições concorrentes ao catálogo não perdem entrada, com ou sem tarifa: leitura, checagem de id, gravação e tarifa ficam sob trava
- [ ] a tarifa da CLI é gravada no formato do painel, com fonte e data; incompleta ou fora do limite, é recusada antes de gravar; se algum passo falhar, o catálogo volta e só a tarifa deste id sai de ajustes

## Desenho e alternativas

Biblioteca padrão (`urllib`, `subprocess`), sem SDK de provedor. Descartados: chave no `~/.config/agata/.env` (o modelo não pode tocar nesse arquivo; um cofre próprio deixa a escrita com o painel); chave no OmniRoute (fora do repo e sem trilha no ledger); comando de CLI cadastrável pelo painel (execução arbitrária). A API sai direto, sem passar pelo `sanitizar.py` de egresso: neste lote só as provas fixas saem, e a integração com o caminho real (lote 4) precisa passar pelo sanitizador.

## Implementação e testes

`provedores.json`, `segredos.py`, `adaptadores.py`, `testar_rotas.py` e `README.md` (guia para outros usuários). Testes em `tests/test_conexoes.py` e `tests/test_configurar.py`, sem rede: HTTP e programa substituídos; o `configurar.py` roda em catálogo temporário, nunca no `provedores.json` real.

## Migração e reversão

Nada no canon. Reversão por revert; apagar `~/.config/agata/conexoes/` remove chaves e ajustes.

## Riscos e dependências

A trava `provedores.lock` cobre só a CLI; o painel grava `provedores.local.json` e `ajustes.local.json` sem essa trava. Uma gravação do painel no instante entre a leitura e a escrita de `ajustes.local.json` pode se perder (janela curta, não medida em concorrência real). Segredo colocado no caminho da URL (ex.: `/token/...`) ainda passa: a checagem barra usuário, senha, query e fragmento, não o caminho. Pela CLI (17/11), a base `https` vai direto ao provedor e sai sem o sanitizador `:20127`; o gateway local é a rota que passa por ele. Se o Humano quiser o gateway obrigatório para todo modelo, a mudança é em `endereco`/`_url_permitida` do `configurar.py`. Login do CLI só se confirma no primeiro teste (`login: não medido`). O modelo padrão do ChatGPT ficou vazio de propósito: o identificador vigente não foi medido nesta sessão e é escolhido no painel. A tarifa é informada pelo Humano, com fonte; o custo é estimativa e não substitui a fatura.

## Código

- `provedores.json`
- `segredos.py`
- `adaptadores.py`
- `testar_rotas.py`
- `configurar.py`
- `README.md`
- `tests/`
- `tests/test_configurar.py`
