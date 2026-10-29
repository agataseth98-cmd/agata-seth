# Proposta: o sistema Agata liga e desliga pelos atalhos (29/10/2026)

Esta proposta **substitui** `seth-sob-demanda-20261029` (ainda sem assinatura). Assine só esta.

## Em uma frase

Clicar em **Seth** liga tudo que o sistema precisa. Clicar em **parar Seth** desliga tudo. Nada sobe sozinho quando o computador liga.

## O que acontece ao clicar em Seth

1. Liga a espinha do sistema (os serviços de apoio).
2. Liga o LibreChat, a voz, o painel e o Obsidian.
3. Liga as duas vigias da Equipe (Claude e Codex). A vigia é um aviso que anota o que acontece no sistema.
4. Abre o navegador do sistema (Chromium, perfil "Sistema Agata").
5. Se o navegador já estiver aberto, abre só as abas que faltam. Nada aparece duplicado.

## O que acontece ao clicar em parar Seth

1. Para as vigias.
2. Fecha o Obsidian.
3. Fecha o navegador do sistema (ele é só do sistema Agata).
4. Para o LibreChat e os serviços, e libera a memória da placa de vídeo e dos modelos.

## O que muda na vigia

Antes, a vigia só avisava de três coisas: mensagem nova na Equipe, aprovação assinada e novo código no GitHub. Agora ela anota também:

- serviço do sistema que ligou, caiu ou mudou de estado;
- quantos provedores de IA estão conectados no navegador;
- se o LibreChat está saudável ou não.

Tudo vai para um diário simples: `~/.cache/agata/sincronia/eventos.log`. Uma linha por evento, com a hora.

## Como a Seth lê os eventos

O painel passa a ter `GET /api/eventos`. Ele mostra as últimas 60 linhas do diário, em texto. É só leitura, e o endereço não aceita caminho de arquivo escolhido pelo cliente.

## O que não muda

- O boot. Nada do sistema sobe sozinho ao ligar o computador. O único serviço que ainda sobe no login é o `psd` (sincronia do navegador), que não é deste sistema.
- O navegador pessoal. O Chromium do sistema é separado; se você usar outro navegador, ele não é tocado.

## Arquivos que a proposta altera

- `redesign/systemd/seth` e `seth-parar`: os atalhos.
- `redesign/systemd/agata-vigia@.service`: nova unidade versionada. Ela não tem mais ligação com o boot e reinicia só se travar (não quando você para de propósito).
- `scripts/equipe/vigia.sh`: a vigia com os novos eventos.
- `redesign/painel_operacional/server.py`: o endereço `/api/eventos`.

## O que ainda não foi testado

- Não liguei nem desliguei o sistema pelos atalhos. Isso só acontece depois da aplicação.
- A parte de serviços da vigia não foi testada com um serviço caindo de verdade. Testei só a parte de mensagens da Equipe, e ela funcionou.
- O navegador é aberto com o endereço do painel e com as LLMs. A detecção de abas depende da extensão do Conselho estar instalada no perfil. Isso já está feito.

## Aplicação

Depois da assinatura (`bash scripts/aprovar.sh sistema-sob-demanda-20261029`), eu aplico e copio os atalhos para `~/.local/bin`.
