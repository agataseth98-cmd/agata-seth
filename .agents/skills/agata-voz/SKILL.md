---
name: agata-voz
description: >-
  Faz um modelo falar com a voz do sistema Agata (piper-tts local, modelo pt_BR-agata-last) e orienta
  quem não consegue emitir áudio a escrever para ser falado nessa voz. Use quando o Humano pedir para
  ler em voz alta, falar, narrar, dizer em voz alta, ouvir uma resposta, voz do Agata, voz do sistema,
  áudio, TTS ou modo de voz, e em qualquer momento em que um modelo for produzir fala.
---

# Voz do sistema (decisão do Humano, 03/11/2026, sem negociação)

Quando um modelo fala, a voz é a do sistema. Nenhum modelo usa outra voz nem serviço externo de voz, e texto do Agata nunca sai da Máquina para virar áudio.

## Quem tem como falar (shell na Máquina)

```bash
python3 scripts/agata_falar.py --texto "frase" ; python3 scripts/agata_falar.py --arquivo resposta.md ; echo "texto" | python3 scripts/agata_falar.py
```

O script prepara o texto (tira código, tabela, caminho, URL e marcação; soletra siglas), liga o `piper-tts.service` se estiver parado, pede o áudio por parágrafo, toca com `mpv`, `paplay`, `pw-play`, `aplay` ou `ffplay` e desliga o serviço se foi ele que ligou. Outras opções: `--preparar` (mostra o texto que seria falado), `--sem-tocar`, `--salvar-wav DIR`, `--manter-servico`.

Saídas: 0 falou; 2 uso; 3 a voz do sistema não está disponível; 4 sem player. **Com 3 ou 4 o modelo diz que NÃO falou.** O script recusa até falar com o modelo de reserva (`pt_BR-faber-medium`): falar com outra voz é pior que não falar.

## Quem não consegue emitir áudio

Mimetiza a voz do sistema: escreve para ser falado, na voz comum ((685)/(686): resultado primeiro, evidência, próximo passo; frases curtas; sem saudação, muleta, emoji nem exclamação), sem tabela, caminho ou bloco de código dentro do trecho falado, siglas soletradas e números por extenso quando soar melhor. Entrega o texto falável e diz que não falou. Havendo shell em qualquer ponto da conversa, usa o script acima.

## Regras

1. Falar sai da tela e vai ao ambiente do Humano: só quando ele pede ou o modo de voz está ativo; o texto lido é o que ele pediu, nunca segredo.
2. Não ouço o resultado: só confirmo que o serviço respondeu e o player terminou sem erro; não afirmo qualidade da fala.
3. Texto falado com mais de 12.000 caracteres: fale o resumo e diga que é resumo.
4. O serviço sobe e desce por conta de quem fala (o sistema é sob demanda); medição e voz não ficam ligadas à toa.
5. Mudar esta skill ou o script passa por proposta P-8.
