# Conexões de modelos — como ligar o seu

A nova versão do Agata fala com qualquer modelo pelo mesmo contrato. Claude e ChatGPT são os exemplos preenchidos (decisão do Humano, 04/11/2026). Use-os como molde para o provedor que você preferir.

## Os três caminhos

| Caminho | Como funciona | Quem paga | Quando usar |
|---|---|---|---|
| **navegador** | O Conselho em Rede do painel digita no site do provedor, com a sua sessão aberta no Chromium do projeto. | a sua conta no site | quando você quer aprovar cada envio; o Agata nunca envia sozinho por aqui |
| **programa (CLI)** | Roda o programa da sua assinatura (`claude -p`, `codex exec`) em pasta temporária vazia, sem ferramentas e sem sessão salva. | a cota do seu plano | sem chave de API; categoria `assinatura` no orçamento |
| **API** | HTTP direto, com a chave que você gravou no painel. | por token | o caminho mais portátil; categoria `pago` no orçamento |

## Ligar um provedor pelo painel

1. Abra o painel, grupo **Nova versão** e depois **Orçamento e eventos**. Ligue a categoria (`assinatura` ou `pago`) e defina os tetos. Para `pago`, o teto em R$ precisa ser maior que zero.
2. Vá a **Conexões de modelos**:
   - **programa:** basta o CLI estar instalado e com login feito. O painel mostra "instalado"; o login só se confirma no primeiro teste;
   - **API:** escolha o provedor, informe o modelo e a tarifa (US$ por milhão de tokens de entrada e de saída, câmbio, a página oficial de preços e a data em que você conferiu), e cole a chave. Ela vai para `~/.config/agata/conexoes/<id>.chave` com permissão `0600` e nunca volta para a tela;
   - **outro provedor:** em "Adicionar pelo mesmo formato", informe id, nome, formato (`openai` serve para qualquer API compatível) e a URL `https` do endpoint de chat.
3. Clique em **Testar rotas**. São três provas fixas (conversa, JSON, código), sem nenhum texto seu. O resultado diz qual rota passou em qual capacidade. Só a rota testada conta como redundância.

## Ligar um provedor pelo catálogo (para quem mantém o repo)

Acrescente um bloco em `provedores.json`, copiando o de `claude` ou `chatgpt`:

- `api.formato`: `anthropic` ou `openai`; `api.url`, `api.env` (variável opcional), `api.prefixo_chave` e `api.modelo`;
- `cli.argv`: o comando, com `{prompt}` no fim; `cli.argv_modelo` é o par que escolhe o modelo e entra antes do prompt; `cli.saida` é `json_result` (lê o campo `result`) ou `arquivo` (lê `{saida_arquivo}`);
- `categoria_orcamento`: qual categoria do orçamento cada caminho consome.

Comando de programa **só entra pelo catálogo versionado**, revisado e assinado (P-8). O painel nunca cadastra comando para executar.

## Antes de qualquer chamada sair

1. **Orçamento:** a categoria está ligada e dentro do teto de chamadas.
2. **Privacidade:** texto com dado pessoal, pela régua do `redesign/router/sanitizar.py`, não sai para provedor remoto.
3. **Custo** (API): sem tarifa datada a chamada é recusada; o gasto estimado acumulado (`~/.local/share/agata/nova-versao/conexoes/gasto.jsonl`) não passa do teto em R$.

Falha de qualquer porta vira `falha_etapa` (`orcamento`, `privacidade`, `custo`, `configuracao`, `autorizacao`, `transporte`), nunca uma chamada feita às escondidas.
