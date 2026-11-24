# Proposta conversa-voz-23-11 — conversa por voz sem cliques no painel (uma assinatura)

Decisões do Humano, 23/11/2026: 20:03 "tem que se antecipar"; 20:04 "tem que ficar 50 vezes na minha frente em jogadas de xadres"; 20:06 "não está automatizado, levante o estado da arte e transcenda"; 20:28 "resolva de forma a que fique mais eficiente para mim, segundo o quê o sistema lembra de mim"; 20:29 "já faça o próximo passo" (interrupção pela voz).

Feito por agentes do sistema (agata-dev, agata-revisor, agata-inov-pesquisa; Claude Haiku 5.5), orquestrado e conferido pelo Claude Opus 5.5.

## Antes (medido em 23/11)
Depois do reboot, o ouvido (`:20137`) estava parado e o ditado só dizia "Ligue o servidor do ouvido". Para falar: Ditar, Parar, revisar, Enviar, e o Modo conversa só lia a resposta, sem voltar a ouvir. Sem interrupção pela voz.

## O que muda
1. **Ditado liga o ouvido sob demanda** (`seth_ditado.py`): conexão recusada ou motor ausente → `systemctl --user start ouvido-agata.service piper-tts.service`, espera até 20 s a porta e repete uma vez. Timeout não reenvia (504). Durante a partida: 503 "ouvido subindo". Só para ouvido local. Boot inalterado (decisão de 29/10).
2. **Conversa por voz** (`prototipo.js/html/css`): botão único ou "fale comigo"; detector de fala no navegador (1,2 s de silêncio fecha o turno; < 0,4 s descarta); envio automático à Seth; resposta falada; volta a ouvir sozinho. Estado sempre visível (Ouvindo, Transcrevendo, Seth pensando, Seth falando). Esc corta a fala; 2º Esc desliga; "encerrar chamado"/"volte ao texto" encerram.
3. **Interrupção pela voz**: na conversa, a fala da Seth é sintetizada pela voz do sistema (`POST /api/seth/voz-audio`, `seth_voz.sintetizar`, pt_BR-agata-last) e tocada no navegador, que cancela o eco; voz sua sustentada ≥ 300 ms corta a fala e já grava. Falha da síntese → fala pela Máquina, meia-duplex, cauda de 800 ms. Nenhum áudio sai da Máquina.
4. **Guardas** (revisão independente): transcrição que repete ≥ 60% da última fala é descartada (eco); 6 turnos seguidos sem tecla/clique pausam a conversa; anexo pendente não vai pela voz; uma síntese por vez; prazos de 130 s (ditado) e 60 s (trecho); AudioContext parado desliga com aviso.
5. **`seth-parar`** também para o ouvido.

## Medido
Testes de voz/ditado: 143 OK. `test_painel`: 81 OK. Critérios do painel: 327/327. CI local: `CI LOCAL: TUDO OK` (93/93). `git apply --check` em cópia limpa: OK. Ditado de ponta a ponta pelo painel no ar (antes do lote, com o ouvido ligado à mão): transcreveu.

## Não medido
Eco real no alto-falante e navegador real; limiares (0,02 fala, 0,08 interrupção, 300 ms, 1,2 s, 60%, 6 turnos, 800 ms) são estimativas a ajustar com a voz do Humano. Tempo real da partida do ouvido pelo painel (ambiente do serviço).

## Fora, decisão do Humano
O piper fica ligado depois da conversa (evita liga-desliga por trecho). Próximo passo sugerido pela pesquisa: fim de turno pelo sentido da frase e palavra "Agata" local antes do STT.

## Depois de aplicar
Restart do painel (`systemctl --user restart painel-operacional`); abrir a conversa por voz e medir eco e cortes com o Humano.

**Reversão:** `git apply -R propostas/aplicadas/conversa-voz-23-11.diff` e restart do painel.

Assinatura: bash scripts/aprovar.sh conversa-voz-23-11
