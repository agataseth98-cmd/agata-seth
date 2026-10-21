# Provisionamento do token do projeto (escriba + cliente)

Estado: **procedimento, sem segredo e sem execução.** Só roda após a assinatura do Escriba (PR 417) e a confirmação explícita do Humano.

## 1. Um token, gravado em dois lugares
O escriba (host) e o cliente (container) precisam do **mesmo** valor. Gere uma vez; nunca imprima o valor no terminal nem no chat.

```bash
# gera o token direto no arquivo do escriba, com permissão 0600
install -m 600 /dev/null ~/.config/agata/projetos/<hash>.token
openssl rand -hex 32 > ~/.config/agata/projetos/<hash>.token
```

`<hash>` = `sha256` do caminho absoluto de `AGATA_PROJETO_RAIZ` (sem barra final):

```bash
printf '%s' "$HOME/agata" | sha256sum | cut -d' ' -f1
```

O cliente lê o **mesmo** conteúdo por bind mount. Copie o arquivo, sem abrir:

```bash
install -m 600 ~/.config/agata/projetos/<hash>.token ~/.config/agata/projetos/cliente.token
export AGATA_PROJECT_TOKEN_FILE_HOST=$HOME/.config/agata/projetos/cliente.token
```

Verifique só o tamanho e as permissões, não o conteúdo:

```bash
stat -c '%a %U %s' ~/.config/agata/projetos/<hash>.token
```

Esperado: `600 orusoua 65` (64 hex + quebra de linha).

## 2. Dono do arquivo no container
O cliente recusa o arquivo se o dono não bater com o uid do processo. Confira antes do deploy:

```bash
id -u
docker exec librechat id -u
```

Se forem diferentes, **não** suba o token: o cliente recusa tudo. Ajuste o `user:` do serviço no compose (proposta separada) ou reavalie a checagem de dono.

## 3. Hash do caminho
Se o repositório mudar de pasta, o hash muda e o token deixa de ser encontrado. Antes de mover `~/agata`, copie o token para o novo hash. Não altere `AGATA_PROJETO_RAIZ` sem essa cópia.

## 4. Verificação (sem imprimir segredo)
- `curl` sem token → `403`, nada gravado.
- Com token correto, texto limpo → `200`, gravado e verificado.
- Os 5 casos de `scripts/testar_escriba_http.py` continuam passando.

## 5. Reversão
Remover o arquivo do cliente e do escriba, e definir `AGATA_PROJECT_TOKEN_FILE_HOST` para `/dev/null`. Sem token, o escriba volta a recusar escrita (falha fechada).

## Limites
- Este documento não cria token. A criação é ato do Humano, com confirmação explícita.
- O teste ponta a ponta (LibreChat → escriba) é pré-requisito do deploy; ainda não foi feito.
