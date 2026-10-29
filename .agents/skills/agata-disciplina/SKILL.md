---
name: agata-disciplina
description: Disciplina obrigatória de qualquer modelo no sistema Agata — cabeçalho em toda resposta com hora medida, modo conciso, aviso antes de ação externa, consulta antes de mexer em trabalho alheio, checagem de dependências antes de reiniciar serviço, e leitura declarada com precisão. Use em toda sessão do repositório agata, sem exceção.
---

# Disciplina Agata

Por quê: três falhas reais em 28/10/2026 vieram de esquecer regras que já existiam. Esta skill junta as regras num lugar só, para que o modelo as carregue antes de agir. Ela não cria regra nova. Ela aponta as regras do canon (REGRAS.md, AGENTS.md, PROTOCOLOS.md) e exige a checagem.

## 1. Cabeçalho em toda resposta

Toda resposta começa com uma linha:

`agata · <modelo real> · t=<n> (contado no contexto) · <data e hora> (<selo de origem>)`

- **Hora:** meça de novo a cada resposta com `date '+%d/%m/%Y %H:%M %Z'`. Nunca copie a hora da resposta anterior.
- **Modelo:** o nome vem do indicador da sessão, não de memória.
- **Selo:** `(relógio da Máquina)` quando medido. `(informado pela interface)` quando não verificável.
- **Sem cabeçalho = resposta inválida.** Se esqueceu, corrija na resposta seguinte, em uma linha, sem pedir desculpa longa.

## 2. Modo conciso

- Traga o resultado. Não narre o processo ("vou verificar", "agora li", "rodei").
- Erro de processo aparece em uma linha, só quando constatado.
- Pedido de "modo explicativo" liga o modo longo. "Modo conciso" desliga.

## 3. Aviso antes de ação externa

Antes de qualquer coisa que saia da Máquina ou altere estado compartilhado, diga o que vai acontecer e espere o "sim". Inclui:
- `git push`, abrir ou mergear PR;
- envio a Drive, Discord, Gmail ou qualquer serviço externo;
- hooks que enviem dados para fora (inclusive o pós-commit que envia o índice ao Drive);
- reinício de navegador ou serviço compartilhado.

"Pode seguir" dado antes da ação vale só para aquela ação.

## 4. Consultar antes de mexer em trabalho alheio

Antes de criar, mover ou editar arquivo em pasta de outro modelo ou pessoa, confira quem é o dono (`ONDE_ESTAMOS.md`, `cache_conselho.py ler`). Se for de outro, pergunte antes. Rascunho próprio vai numa pasta sua e aponta para a pasta alheia só se for pedido.

## 5. Checar dependências antes de reiniciar

Antes de encerrar um processo, leia o launcher e confirme as variáveis e caminhos que ele usa por padrão (ex.: `AGATA_RELAY_EXTENSION`). Só então encerre. Depois de subir, verifique a porta, o processo e o endpoint. Se o reinício falhar, diga o que falhou e o tempo que o serviço ficou fora.

## 6. Leitura declarada com precisão

Quando disser que leu um arquivo do canon, diga **quais partes** leu, com as linhas. "Li REGRAS.md linhas 75-82 e 191-210" é verdade. "Li o REGRAS" é falso se foi parcial.

## 7. Verificação antes de entregar

Antes de entregar texto com afirmação verificável, rode:

`python3 redesign/router/auditoria_turno.py --verificar < arquivo`

Corrija o que ela apontar. Se ela apontar um número de entrada que não existe no MEMÓRIAS, não invente fonte: escreva "não encontrei".

## Teste da skill

Ao final de cada tarefa, responda mentalmente:
- [ ] Cabeçalho presente com hora medida agora?
- [ ] Resposta sem narração de processo?
- [ ] Algum envio externo ou reinício foi avisado antes?
- [ ] Mexi em pasta de outro sem consultar?
- [ ] Declarei leitura parcial como parcial?

Se a resposta for "não" em qualquer item, corrija antes de entregar.
