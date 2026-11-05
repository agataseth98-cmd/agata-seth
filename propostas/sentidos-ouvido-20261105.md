# Proposta `sentidos-ouvido-20261105`: o ouvido do Agata (5 sentidos, lote 4 item 1)

**O que é, em português comum:** o Agata ganha um ouvido local melhor. A fala vira texto pelo lfm3-audio, um modelo de 2B da Liquid AI que roda na Máquina, e o Whisper atual fica de reserva. A voz do sistema não muda: continua o piper `agata-last`. É a primeira peça do projeto 5 sentidos e da conversa por voz.

**Decisão do Humano (05/11/2026):**
- "quero testar todos os modelos da familia já, mesmo por que temos planos de ter conversa por voz, e eles podem adiantar um projeto chamado 5 sentidos";
- "pode fazer os testes sinteticos mesmo, e vamos prosseguir";
- "faça".

## O que entra

- **`redesign/sentidos/ouvido.py`**: `transcrever(arquivo)` converte o áudio para 16 kHz e tenta primeiro o `lfm3-audio:2b` pelo Ollama local, depois o Whisper da iGPU, mas só se ele já estiver no ar. Nunca liga serviço e nunca gera fala. Devolve o texto, o motor, o tempo e, se nenhum motor transcrever, o motivo. Tem linha de comando e `--selftest`.
- **`redesign/sentidos/medir_ouvido.py`** e **`frases_ouvido.txt`**: as 20 frases fixas são faladas pela voz do sistema (sem tocar), ganham uma versão com ruído leve, e cada motor é medido em erro por palavra e tempo. O resultado vai para o registro comum da avaliação.
- **Painel:** página nova "Sentidos" no grupo Nova versão, com motor, reserva, voz, última medição e o botão "Medir o ouvido". A Avaliação passa a listar só as próprias rodadas.
- **Specs, CI** (`sdd.yml`), **`redesign/README.md`** e uma linha em **`PROJETO_REFERENCIA.md`**.

## Evidência (05/11/2026)

- **Medição pelo próprio código** (`medir_ouvido.py`, 80 transcrições), com voz sintética:
  - lfm3-audio: 4% de erro por palavra com áudio limpo e 5% com ruído, 15 e 13 frases perfeitas de 20, 0,15 s por frase;
  - Whisper base (iGPU): 14% e 14%, 6 frases perfeitas de 20, 0,72 s por frase.
- **Medição anterior, por script avulso:** lfm3-audio com 3,4% e Whisper com 18%. A variação vem da síntese da voz.
- **Testes:** 166 verdes na suíte da CI, âncora OK, sem drift. O `.diff` aplica limpo sobre o `main` (`1b9b0d88`). A página Sentidos foi conferida no navegador.
- **Achado de passagem:** a instrução de transcrever precisa ir como mensagem de sistema. Na mensagem do usuário, o modelo entra em laço e o Ollama aborta.

## Limites e não medido

- **A sua voz não foi medida:** só voz sintética e ruído leve.
- **Nomes próprios** saem trocados às vezes ("OmniRoute" virou "Mi Route").
- **Placa de vídeo:** o lfm3-audio usa 1,7 GB da NVIDIA e disputa com os modelos de texto.
- **Ainda não conversa:** nenhum consumidor está ligado. A conversa por voz (LibreChat ou servidor `/v1/audio/transcriptions`) fica numa proposta própria.

## Reversão

Revert do PR. O modelo sai com `ollama rm lfm3-audio:2b`. Nada no canon muda além de uma linha em `PROJETO_REFERENCIA.md`.
