# Spec — Sentidos: ouvido (nova versão, lote 4 item 1; projeto 5 sentidos)

Componente da nova versão. Spec-mãe: `redesign/nova_versao/spec/spec.md`. Decisões do Humano em 05/11/2026:
- "temos planos de ter conversa por voz, e eles podem adiantar um projeto chamado 5 sentidos";
- "pode fazer os testes sinteticos mesmo, e vamos prosseguir";
- "faça".

## Jornadas críticas

1. Um componente do sistema entrega um áudio e recebe o texto, tudo local, com o motor e o tempo.
2. O Humano mede o ouvido pelo painel (página Sentidos) e vê o erro por palavra e o tempo de cada motor.
3. Com o motor principal fora (Ollama parado ou com erro), o ouvido usa a reserva, se já estiver no ar, ou diz que não ouviu. Nunca inventa texto.

## Contrato

- `ouvido.py transcrever(arquivo, motor=auto|lfm3|whisper, idioma)` converte para wav mono 16 kHz (ffmpeg) e tenta, em ordem:
  1. `lfm3-audio:2b` pelo Ollama: instrução `Perform ASR in <idioma>.` como mensagem de sistema, áudio em base64 no campo `images` da mensagem do usuário;
  2. o Whisper da iGPU (`/transcribe`, porta 20130), pelo caminho permitido `OVW_PASTA_ENTRADA`, só se já estiver no ar.

  Devolve `text`, `motor`, `proc_s`, `audio_s`, `falha_etapa`, `erro` e as `tentativas`. Não liga serviço, não gera fala e não grava nada além do temporário. Aceita até 50 MB.
- `medir_ouvido.py medir(motores)` fala as 20 frases fixas de `frases_ouvido.txt` com a voz do sistema, sem tocar, mistura ruído rosa leve e calcula o WER (sem acento, pontuação e caixa) e o tempo mediano por motor e condição. Motor fora do ar sai `null`, nunca zero. Grava no registro comum (`redesign/avaliacao/registro.py`, medidor `ouvido`), com referência e transcrição.
- O painel tem a página Sentidos: motor principal, reserva, voz, última medição e a ação `medir_ouvido`, em segundo plano e uma por vez com as rodadas de avaliação.
- A voz do sistema não muda: continua o piper `pt_BR-agata-last` (`scripts/agata_falar.py`).

## Critérios de aceite

- [ ] o lfm3 recebe a instrução no sistema e o áudio no campo images
- [ ] a reserva só entra se o Whisper já estiver no ar e nenhum serviço é ligado
- [ ] o WER ignora acento, pontuação e caixa
- [ ] a medição grava o registro comum com referência e WER e não toca no alto-falante

## Desenho e alternativas

Biblioteca e linha de comando, sem servidor novo: hoje nada no sistema chama o ouvido (o LibreChat usa a voz do navegador). O servidor HTTP compatível com `/v1/audio/transcriptions` fica para quando a conversa por voz for ligada, em proposta própria.
- **Descartado:** trocar o modelo do `whisper_server.py` (outra arquitetura) e usar a fala do LFM3. A voz do sistema é decisão do Humano de 03/11 e o LFM3 não clona voz.
- **Descartado:** Whisper maior: não instalado, não medido.

## Implementação e testes

`ouvido.py`, `medir_ouvido.py`, `frases_ouvido.txt`. Testes em `tests/test_sentidos.py`, sem rede: HTTP, voz e motores substituídos. Os que precisam de ffmpeg pulam sem ele.

## Migração e reversão

Nada no canon. Reversão por revert. O modelo `lfm3-audio:2b` sai com `ollama rm`.

## Riscos e dependências

- **Medição (05/11):** lfm3-audio com WER de 3,4 a 5% e 0,14 s; Whisper base com 14 a 18% e 0,7 s. A voz é sintética e o ruído é leve, então não vale para a voz do Humano.
- **GPU:** o lfm3-audio usa 1,7 GB da NVIDIA, a mesma dos modelos de texto. A reserva fica na iGPU.
- **Versão do Ollama:** exige 0.40.13 ou mais novo (a Máquina tem 0.40.14).
- **Nomes próprios:** podem sair trocados ("OmniRoute" virou "Mi Route").

## Código

- `ouvido.py`
- `medir_ouvido.py`
- `frases_ouvido.txt`
- `tests/`
