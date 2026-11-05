# Proposta `sentidos-conversa-librechat-20261105`: conversa natural por voz no LibreChat

**O que é, em português comum:** no LibreChat, você fala, o ouvido local (lfm3-audio) transcreve, a Seth responde e a voz do sistema (piper `agata-last`) lê a resposta, tudo dentro da Máquina. O modo conversa já vem ligado, com envio e fala automáticos. Para funcionar, você precisa liberar uma porta no firewall (comando abaixo), porque isso pede sudo.

**Decisão do Humano (05/11/2026):** "vamos já deixar a conversa natural disponivel no librechat por enquanto, testarei depois de tudo do experimento implementado."

## O que entra

- **`redesign/sentidos/servidor_ouvido.py`:** transcrição no formato OpenAI (`POST /v1/audio/transcriptions`) só em 127.0.0.1:20137. Usa o ouvido aprovado em `sentidos-ouvido-20261105`. Não pede chave, aceita áudio de até 25 MB, não registra o texto falado em log e apaga o áudio temporário.
- **`redesign/systemd/ouvido-agata.service`:** sobe com o sistema (`agata.target`), como o piper.
- **Relé do LibreChat** (`docker-compose.yml`): o `librechat-ponte-host` passa a encaminhar também a 20137, totalizando 8 portas.
- **`redesign/librechat/librechat.yaml`:**
  - `speech.stt` aponta para o ouvido, com `allowedAddresses`, como já existe para a voz;
  - `speech.speechTab` deixa por padrão a transcrição externa em português, o envio automático, a fala automática pela voz `pt-br` (o piper `agata-last`) e o modo conversa. Isso também resolve a voz em inglês que aparecia quando o motor ficava em "Navegador".
- **`config/portas-agata.txt`:** a 20137 entra na checagem de portas do perímetro.
- **Painel:** a página Sentidos mostra se a conversa do LibreChat está no ar.
- **Testes:** 2 novos (formato OpenAI e as quatro peças da porta declaradas juntas). Spec atualizada.

## Evidência (05/11/2026, worktree)

- Servidor real na porta de teste: um áudio webm/opus, o formato típico do navegador, gerado da voz do sistema, voltou como "Bom dia, Seth. Qual é a previsão do tempo para hoje?", sem erro.
- **Firewall medido de dentro do container `librechat`:** a porta 8890 conecta em 2 ms, e uma porta não liberada dá timeout. Logo, a 20137 precisa da regra do ufw.
- **Testes:** 168 verdes na suíte da CI; a suíte do perímetro deu 61 casos e 0 falhas; âncora OK, sem drift. O `.diff` aplica limpo sobre o `main`.

## Depois de aplicar (eu faço, menos o passo 1)

1. **Você**, no terminal, libera a porta na bridge do LibreChat. Se quiser espelhar o formato das regras existentes, confira antes com `sudo ufw status numbered`:
   `sudo ufw allow in on br-librechat to 172.29.7.1 port 20137 proto tcp comment 'agata ouvido (5 sentidos)'`
2. Eu instalo e ligo a unit `ouvido-agata.service` no `agata.target`.
3. Eu copio o compose e o `librechat.yaml` para `~/librechat/` e recrio o relé e o LibreChat.
4. Eu confiro de dentro do container que a 20137 responde.

## Não medido

- Conversa ponta a ponta no navegador, com microfone. Você vai testar depois, como disse.
- O formato exato que o LibreChat envia. O servidor aceita qualquer formato que o ffmpeg leia.

## Reversão

Revert do PR, `systemctl --user disable --now ouvido-agata.service`, recriar o relé e remover a regra do ufw.
