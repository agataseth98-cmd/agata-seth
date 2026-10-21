# Cabeçalho: quem usa `agata-seth` e quem usa `agata · MODELO REAL`

Estado: **rascunho de regra, sem efeito no comportamento**. A mudança em PROTOCOLOS ("Carregar e formatos") depende de `.diff` + assinatura (P-8).

## Ditado do Humano (20/10/2026)
- Só modelos que **passam pelo sistema da Seth** (gateway e escriba) usam `agata-seth · <modelo> · t=<n> · <data e hora>`.
- Modelos **em nuvem**, ou em **app próprio** que não passa pelo sistema da Seth, usam `agata · <MODELO REAL> · t=<n> · <data e hora>`.

## Motivo
Em 20/10/2026 uma sessão no app Codex (modelo real: GPT-6 Luna) escreveu `agata-seth · ministral-14b-latest`. O cabeçalho declarou um modelo e uma identidade que não eram os da sessão.

## Regras
1. Antes de escrever o cabeçalho, perguntar: esta resposta passou pelo gateway/escriba da Seth? Sim → `agata-seth`. Não → `agata`.
2. Nunca usar o nome de outro modelo.
3. O modelo é o real, lido do indicador do app ou da configuração da sessão, não de memória.

## Em aberto
- Como o próprio sistema confere o cabeçalho (medição mecânica, como o P-7 faz com as citações), se o Humano quiser.

## Formalização (20/10/2026, 21h)

Confirmado pelo Humano: a regra vale para **todos** os modelos que não passam pelo sistema da Seth, inclusive o Codex e o Claude Code.

- Passa pela Seth (gateway e escriba): `agata-seth · <modelo> · t=<n> · <data e hora>`.
- Não passa pela Seth (Claude Code, Codex, nuvem, app próprio): `agata · <MODELO REAL> · t=<n> · <data e hora>`.
- Exemplo do erro corrigido: uma sessão do Claude Code usava `agata-seth`, e uma do app Codex escrevia `agata-seth · ministral-14b-latest` com modelo real GPT-6 Luna. Ambos foram corrigidos.
