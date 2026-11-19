# Spec — Sentidos: ouvido (nova versão, lote 4 item 1; projeto 5 sentidos)

Componente da nova versão. Spec-mãe: `redesign/nova_versao/spec/spec.md`. Decisões do Humano em 05/11/2026 (item 2: "vamos já deixar a conversa natural disponivel no librechat"):
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
- `servidor_ouvido.py` serve `POST /v1/audio/transcriptions` (formato OpenAI: multipart com `file` e `language` opcional) e `GET /health`, só em 127.0.0.1:20137, com limite de 25 MB, sem chave e sem log do texto. Unit `redesign/systemd/ouvido-agata.service`, membro do `agata.target`. O LibreChat chega pelo relé `librechat-ponte-host` (172.29.7.1:20137); a porta entra junto no compose, no `librechat.yaml` (`speech.stt` e `allowedAddresses`), em `config/portas-agata.txt` e numa regra do ufw, que é do Humano.
- O `librechat.yaml` liga a conversa natural por padrão (`speechTab`): transcrição externa em português, envio automático, fala automática pelo piper e `conversationMode`.
- A voz do sistema não muda: continua o piper `pt_BR-agata-last` (`scripts/agata_falar.py`).

## Critérios de aceite

- [ ] o lfm3 recebe a instrução no sistema e o áudio no campo images
- [ ] a reserva só entra se o Whisper já estiver no ar e nenhum serviço é ligado
- [ ] o WER ignora acento, pontuação e caixa
- [ ] a medição grava o registro comum com referência e WER e não toca no alto-falante
- [ ] o servidor aceita o multipart da OpenAI, mapeia o idioma e escuta só em loopback
- [ ] a porta nova está no relé, no librechat.yaml, na lista de portas e na unit juntos
- [ ] a visão descreve imagem com o modelo local e falha vira estado, não exceção

## Lote 5 (05/11/2026)

- `visao.py`: descrição de imagem pelo lfm3-vl (entrada apenas; a imagem não é gravada).

## Desenho e alternativas

Biblioteca e linha de comando (item 1). No item 2, um servidor HTTP mínimo da biblioteca padrão, no formato OpenAI que o LibreChat já fala.
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

## Canal de voz de entrada (fase 1, 18/11/2026)

Decisões do Humano (18/11, "ok para todas"): D1a locutor por ECAPA (fase 2), D2a atalho/botão + VAD, D3a só o vetor (sem áudio), D4a outra voz só metadado, D5a voz só conversa; ação com efeito se confirma na tela. Fase 1, sem instalar nada: captura (`pw-record`, sob demanda), VAD por energia em Python puro, transcrição pelo `ouvido.py`, meia-duplex, resposta pelo gateway local (`127.0.0.1:20126`, modelo `seth-livre`) falada por `scripts/agata_falar.py`, estado em `~/.cache/agata/canal-voz/estado.json`, log de metadados `canal-voz.jsonl` (sem texto, sem áudio), lock contra duas sessões. `locutor.py` é interface e devolve `nao_verificado`: o canal opera só em modo conversa. Fica para a fase 2: locutor real, cadastro, perfil, painel, atalho do desktop, medições com a voz do Humano (WER, aceite e rejeição) e latência real.

Palavra de vez e ciclo de conversa (Humano, 18/11 19:54): a fala só segue com "Agata" no começo (agata, ágata, agatha, "a gata"); sem ela e fora do ciclo é ignorada (só metadado). A palavra abre um ciclo: cada fala seguinte dispensa a palavra, a janela renova a cada troca e fecha após `AGATA_CANAL_VOZ_CICLO_MS` (padrão 30000) sem fala ou com "encerrar", "pode parar", "tchau"; ao fechar fala "Até já.". "Agata" sozinha responde "Pode falar.". O estado mostra `em_conversa` (ciclo aberto) ou `ouvindo`. O histórico das últimas 6 trocas fica só em memória, segue ao gateway para dar contexto e é apagado ao fechar o ciclo. Fim de fala: 2 s de silêncio.

Revisão do Codex (18/11) e decisão A do Humano (19/11): o canal não executa nada. Todo envio ao gateway leva `X-Agata-Nao-Registrar: 1`; o gateway (aceita só de loopback, por pedido, sem herdar em keep-alive) não chama o registro de pedidos e responde `X-Agata-Registro: nao`; sem essa confirmação o canal descarta a resposta, avisa na tela e encerra a sessão. A checagem por processo e a recusa de abrir por `SETH_REGISTRO_PEDIDOS` saíram. O filtro de efeitos (criar, abrir, limpar, "preciso que", "por gentileza", "faça um...") é AVISO DE INTERFACE: pede confirmação pela tela e não é fronteira de segurança, porque o canal não executa nada (a fronteira é o canal só ouvir, perguntar e falar texto). A fala usa TMPDIR próprio removido no fim; sinais interrompem leitura, HTTP e TTS; o lock é `flock` mantido aberto.

Contador de turnos (Humano, 19/11): com `AGATA_CANAL_VOZ_SESSAO=<id>` (modelo em `AGATA_CANAL_VOZ_MODELO_TURNO`), cada fala transcrita entregue ao modelo roda `scripts/turno.py proximo` uma vez; a linha de cabeçalho vai à tela e ao gateway (mensagem de sistema). Fala vazia, descartada, eco rejeitado, sem palavra de vez ou com efeito não contam; sem sessão, ou turno.py ausente/falhando, só aviso.

Uso: `python3 redesign/sentidos/canal_voz.py abrir` (primeiro plano; Ctrl+C ou `fechar` encerra), `fechar`, `estado`, `--selftest`.

### Critérios de aceite do canal de voz

- [ ] o VAD abre ao falar e fecha no silêncio
- [ ] o VAD ignora ruído contínuo e estalo curto
- [ ] fala longa tem teto de trecho
- [ ] silêncio longo fecha a sessão do canal de voz
- [ ] o indicador segue os eventos reais na ordem ouvindo, processando, falando, ouvindo
- [ ] etapa que falha gera estado erro com o nome da etapa
- [ ] microfone morto vira erro, nunca fica em ouvindo
- [ ] meia-duplex: o que soa durante a fala do sistema não entra no VAD
- [ ] a resposta é falada por scripts/agata_falar.py e falha dele vira NÃO falei
- [ ] o canal de voz só fala com destinos locais
- [ ] o lock impede duas sessões do canal de voz
- [ ] fechar a captura encerra o pw-record
- [ ] a latência é registrada por etapa
- [ ] o log não tem texto nem áudio e o diretório é 0700
- [ ] outro locutor não chama o modelo e só deixa metadado
- [ ] pedido com efeito por voz não é executado e pede confirmação na tela
- [ ] a fase 1 devolve nao_verificado e opera só em modo conversa
- [ ] a transcrição entra como dado, nunca como instrução
- [ ] a palavra de vez Agata (normalizada) é lida no começo da fala
- [ ] sem a palavra de vez e fora do ciclo a fala é ignorada, só com metadado no log
- [ ] Agata sozinha responde Pode falar e abre o ciclo de conversa
- [ ] dentro do ciclo a fala segue sem a palavra e leva o histórico ao gateway
- [ ] o histórico do ciclo guarda no máximo 6 trocas
- [ ] encerrar, pode parar e tchau fecham o ciclo, falam Até já e apagam o histórico
- [ ] o ciclo fecha após silêncio e fala Até já
- [ ] o histórico fica só em memória, nunca em disco
- [ ] o histórico vai ao modelo na ordem, antes da fala atual
- [ ] o aviso de sistema pede resposta curta
- [ ] falha do TTS não deixa WAV: o canal usa diretório temporário próprio e o remove
- [ ] SIGTERM solta a captura bloqueada e encerra o pw-record
- [ ] SIGINT interrompe a chamada bloqueada ao modelo
- [ ] o lock é atômico: com 8 processos concorrentes só um abre
- [ ] sinal na abertura da captura ainda chama fechar
- [ ] timeout do TTS remove o WAV e mata o processo filho
- [ ] sinal durante o TTS remove o WAV e mata o processo filho
- [ ] sinal durante a limpeza do áudio fica pendente até a limpeza acabar
- [ ] o filtro pega faça/fazer + objeto e verbo de efeito no início ou após por favor
- [ ] todo envio ao gateway leva X-Agata-Nao-Registrar e exige a confirmação X-Agata-Registro: nao
- [ ] sem a confirmação do gateway o canal descarta a resposta, avisa e encerra a sessão
- [ ] o filtro de efeitos cobre preciso que, por gentileza, abra e limpe
- [ ] a confirmação do gateway é conferida também em HTTP de erro e JSON inválido
- [ ] HTTP 500 sem confirmação encerra a sessão
- [ ] o filtro de efeitos cobre criar, reiniciar, alterar, configurar, instalar, desligar, mover, executar, rodar, mandar
- [ ] cada fala entregue ao modelo avança o contador de turnos uma vez e leva o cabeçalho
- [ ] fala vazia ou eco da própria voz não avança o contador
- [ ] turno.py ausente ou falhando só avisa e não derruba o canal

## Código

- `ouvido.py`
- `medir_ouvido.py`
- `frases_ouvido.txt`
- `servidor_ouvido.py`
- `tests/`
- `visao.py`
- `falha_segura.py`
- `canal_voz.py`
- `captura.py`
- `vad.py`
- `locutor.py`
