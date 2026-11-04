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
- `testar_rotas.py`: rotas permitidas pelo orçamento (`local` = tags do Ollama sem embedding; `gratuito` = modelos `available` do OmniRoute, sem `/auto`; `assinatura` e `pago` = conexões prontas), três provas fixas e mecânicas (conversa, JSON, código), coordenadas por `redesign/nova_versao/tarefas.py` (GPU em fila única, remoto em paralelo, teto de chamadas, cancelamento). Guarda veredito, etapa de falha, latência, uso e independência; nunca guarda a resposta. Não altera filas do OmniRoute.
- O corpo (`redesign/corpo/fotografar.py`) preenche `testado` e `pronto` pelo último teste.

## Critérios de aceite

- [ ] a chave vai para o cofre 0600 e nunca volta em estado, resposta ou ledger
- [ ] orçamento, privacidade e custo barram a chamada antes de sair
- [ ] o programa da assinatura roda em pasta vazia, sem ferramentas e sem sessão
- [ ] provedor novo pelo painel é só API com https e sem id repetido
- [ ] o teste de rotas é por capacidade, descreve a independência e não guarda a resposta

## Desenho e alternativas

Biblioteca padrão (`urllib`, `subprocess`), sem SDK de provedor. Descartados: chave no `~/.config/agata/.env` (o modelo não pode tocar nesse arquivo; um cofre próprio deixa a escrita com o painel); chave no OmniRoute (fora do repo e sem trilha no ledger); comando de CLI cadastrável pelo painel (execução arbitrária). A API sai direto, sem passar pelo `sanitizar.py` de egresso: neste lote só as provas fixas saem, e a integração com o caminho real (lote 4) precisa passar pelo sanitizador.

## Implementação e testes

`provedores.json`, `segredos.py`, `adaptadores.py`, `testar_rotas.py` e `README.md` (guia para outros usuários). Testes em `tests/test_conexoes.py`, sem rede: HTTP e programa substituídos.

## Migração e reversão

Nada no canon. Reversão por revert; apagar `~/.config/agata/conexoes/` remove chaves e ajustes.

## Riscos e dependências

Login do CLI só se confirma no primeiro teste (`login: não medido`). O modelo padrão do ChatGPT ficou vazio de propósito: o identificador vigente não foi medido nesta sessão e é escolhido no painel. A tarifa é informada pelo Humano, com fonte; o custo é estimativa e não substitui a fatura.

## Código

- `provedores.json`
- `segredos.py`
- `adaptadores.py`
- `testar_rotas.py`
- `README.md`
- `tests/`
