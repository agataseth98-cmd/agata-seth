# Plano — conversa por voz natural (Agata Voz)

14/10/2026 · MEMÓRIAS (686) · plano, não muda comportamento. Cada fase que tocar o sistema vira proposta P-8 própria, com portão.

## Objetivo
Conversa falada com a Seth com a fluidez do ChatGPT Voice, no hardware que existe: i7-13650HX, 38 GB de RAM, RTX 4060 de 8 GB (a "placa dedicada"), iGPU Intel (Whisper e embeddings).

## Decisão do Humano (14/10/2026)
- A **placa dedicada serve a voz** quando o cérebro está na **nuvem**.
- Quando o cérebro **troca para o modelo local** (que precisa da placa), a Agata **avisa que a voz está desabilitada temporariamente**.

## Por que cascata, e não full-duplex
O ChatGPT Voice de hoje (GPT-Live, jul/2026) é full-duplex: ouve e fala ao mesmo tempo. Os modelos abertos desse tipo (BayLing-Duplex, F-Actor, DuplexCascade) não falam português ou não cabem em 8 GB. A cascata abaixo reproduz a **sensação**: turno decidido pelo sentido, barge-in, primeira palavra rápida. Full-duplex fica como bússola.

## Arquitetura
```
microfone ─► VAD Silero (CPU) ─► Smart Turn v3 (CPU, 8 MB, pt) ─► STT ─► seth_gateway :20126 ─► frases ─► TTS ─► tratamento "sistema" ─► alto-falante
                 ▲                                                         (fila seth-voz: só nuvem, streaming)                        │
                 └──────────────────────────── barge-in: fala do Humano corta o TTS e cancela o stream ◄────────────────────────────────┘
```
- **Turno:** Silero VAD marca início e fim de fala; Smart Turn v3 decide se a frase terminou pelo sentido, não pelo silêncio. Inferência ~12 ms na CPU; português entre as 23 línguas.
- **STT:** hoje, Whisper *base* int8 na iGPU (`:20130`, sem streaming). No modo voz, Whisper maior na 4060 (large-v3-turbo; VRAM a medir).
- **Cérebro:** fila nova `seth-voz` no OmniRoute, **só remotos, sem tier local**. Streaming de tokens. O gateway segue hidratando e auditando, como em todo frontend.
- **TTS, com a placa livre:** Qwen3-TTS com a voz híbrida aprovada (`escolhida.json`), em streaming (~100 ms até o primeiro som, número do relatório técnico, não medido aqui; 4,4 GB de VRAM, medido). **Reserva na CPU:** piper com a voz treinada da Agata (~0,1 s por frase).
- **Tratamento "sistema"** na saída (PROJETO, "Personalidade da Seth"): ffmpeg, o mesmo filtro da amostra aprovada.
- **Espera da nuvem:** enquanto o modelo pensa, uma abertura curta escolhida **por regra, sem modelo** ("Verificando.", "Consultando o canon."). Nunca muleta. A técnica (preface) vem do arXiv 2607.23204.
- **Estilo falado:** a doutrina ganha um modo voz: no máximo 3 frases por vez, sem markdown, números por extenso, resultado primeiro.

## Árbitro da placa (o pedido do Humano)
| estado | placa 4060 | voz | quando |
|---|---|---|---|
| **voz** | STT + TTS da voz; Ollama sem modelo carregado | ligada | a fila `seth-voz` responde |
| **local** | Ollama (cérebro local) | **desligada, com aviso** | todos os remotos da `seth-voz` falharam |

- **Ida para "local":** (1) toca um aviso **pré-gravado** (WAV gerado uma vez, toca sem placa): "Voz desabilitada temporariamente. O cérebro passou para o modelo local; sigo por texto."; (2) descarrega STT e TTS da placa; (3) a conversa segue por texto, na fila normal, que tem o local.
- **Volta para "voz":** checagem leve dos remotos a cada poucos minutos; quando um responde: descarrega o Ollama, recarrega a voz, toca "Voz restabelecida."
- **Por quê:** o Ollama empurrado para a CPU por falta de VRAM já derrubou a Seth para 6,3 tok/s (648). Voz e cérebro local nunca dividem a placa.

## Orquestração
Pipecat, framework aberto que roda local. Licença e versão serão conferidas na instalação. Serviço `agata-voz` de usuário, só em loopback. Áudio bruto nunca vai para o repositório. A trilha de auditoria fica em `~/.cache/agata/`, sem o áudio (Condição 6 do PR #184).

## Fases
0. **Feito:** voz própria treinada (madrugada de 15/10); personalidade canônica (685)/(686).
1. **Protótipo fora do canon:** laço Pipecat + medição. Critérios: os 10 casos do PR #184 (áudio ambíguo, comando parcial, interrupção, negativa, replay, ação destrutiva, rede caída, TTS caído, correção de STT, outro modelo); tempo até a primeira palavra (meta abaixo de 1,5 s com a nuvem rápida); erro de turno; pico de VRAM; **zero comando indevido**.
2. **Proposta P-8:** fila `seth-voz`, árbitro da placa, serviço `agata-voz`, modo voz na doutrina. Passa pelo portão.
3. **Bússola:** full-duplex quando existir modelo aberto em pt-BR que caiba.

## Riscos
- **Disputa da placa:** coberta pelo árbitro. Falha do árbitro = Ollama na CPU (lento, não quebra).
- **Cota da nuvem:** a voz consome mais pedidos. O Gemini já ficou sem cota em (683)/(684).
- **Aviso honesto:** se a voz cair, ela diz. Silêncio não vira "a Seth parou".
- **Privacidade:** STT local, áudio fora do repositório, segredo nunca falado.

## Fontes
Smart Turn: github.com/pipecat-ai/smart-turn · Smart Turn v3: daily.co/blog/announcing-smart-turn-v3-with-cpu-inference-in-just-12ms · Qwen3-TTS: arxiv.org/html/2601.15621 · Preface: arxiv.org/pdf/2607.23204 · DuplexCascade: arxiv.org/abs/2603.09180 · GPT-Live: ud.hk/en/blogs/insight/article/2026-07-10-gpt-live-voice-guide
