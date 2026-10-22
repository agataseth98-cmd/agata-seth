# Decisão registrada: dupla universal pela persona da Seth (para depois)

Data: 22/10/2026. Decidido pelo Humano. Registro de intenção: não é implementação e não muda canon.

## Decisão

A capacidade de comunicação da dupla (hoje Claude × Codex, pelo `scripts/dupla/dupla.py`) será integrada ao fluxo de forma universal: **todos os modelos do conselho** poderão se comunicar **através da persona da Seth**. A dupla deixa de ser um canal exclusivo de dois agentes.

## Estado atual (medido em 22/10/2026)

- O `dupla.py` conhece só `claude` e `codex`.
- A Seth não participa do canal; o verificador (`:20141`) e o gateway (`:20126`) são pontos de acesso, não participantes.

## O que isto NÃO é

- Não há implementação agora. Qualquer mudança em `scripts/*` segue P-8, com `.diff` e assinatura do Humano.
- Não altera a hidratação, os serviços nem a classificação de dados.

## Quando retomar

Depois de o fluxo de D4 e do P-12 estarem fechados. A primeira proposta deve definir: quem da Seth lê e escreve no canal, quais comandos são permitidos e como a classificação de dados se aplica a mensagens entre modelos.
