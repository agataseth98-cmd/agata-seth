---
name: agata-fluxo
description: Fluxo único de trabalho no sistema Agata para qualquer LLM (Claude, Codex, Seth ou outro) que atue numa tarefa. Usar ao começar uma sessão, ao dividir trabalho com outro modelo, antes de propor ou aplicar mudança, e ao registrar resultado.
---

# Fluxo Agata (universal)

Vale para qualquer modelo. Não depende de qual modelo é. Cada modelo se identifica no cabeçalho como
`agata · <modelo real>`; a Seth, que passa pelo gateway, usa `agata-seth · <modelo>`.

## 0. Antes de qualquer ação
1. **Medir o estado**, nunca supor: `git fetch -q && git status -sb`, `gh pr list --state open`,
   `python3 scripts/dupla/dupla.py status`. Sem medição, escrever "não medido".
2. **Canal**: `python3 scripts/dupla/dupla.py presente --agente <eu>`; ler o canal com
   `python3 scripts/dupla/dupla.py ler --agente <eu>`. Responder com `dizer --assunto ... --texto "$(cat arq)"`.
3. **Não tocar** no checkout compartilhado. Trabalhar em worktree própria a partir de `origin/main`.

## 1. Divisão de trabalho entre modelos
- Quem propõe redige a mudança em `propostas/<nome>.diff`; quem audita **executa** os comandos citados
  e reporta a saída literal. Quem audita não aprova.
- Dois modelos não editam o mesmo arquivo ao mesmo tempo (matriz de propriedade do `dupla.py`).
- Trabalho caro em tokens (suíte completa, varreduras longas) vai para o modelo com mais folga; o relato
  volta pelo canal, sem colar relatório inteiro.

## 2. Mudança protegida (do começo ao merge)
1. Escrever a mudança numa worktree própria; gerar só o `.diff` dos protegidos; `git apply --check`.
2. Testar a mudança aplicada numa cópia descartável (`scripts/testar_perimetro.sh`, esperado 0 falhas).
3. Abrir PR **somente de proposta** contra `origin/main`. Não aplicar.
4. Revisão cruzada: o revisor escolhe casos **antes** de olhar o resultado e responde em 4 partes.
5. Só o Humano assina (`bash scripts/aprovar.sh <nome>`). Nenhum modelo roda `aprovar.sh`, usa `sudo` ou abre segredo.
6. Com assinatura verificada (`bash scripts/p8_verificar.sh <nome>` = `PODE APLICAR`), aplicar com
   `python3 scripts/dupla/aplicar.py <nome> --registro <arquivo>` (o registro começa com `({N}) DIÁRIO — ...`).

## 3. Registro
- Resultado vai para `MEMÓRIAS.md` **só por PR**, em entrada nova logo abaixo de `ENTRADAS-NOVAS:AQUI`.
- Nunca editar entrada antiga (P-5). Correção é entrada nova.
- Conversa com modelo não é fonte: só entra o que tiver PR, commit ou medição (M7, entrada 791).

## 4. Afirmar com prova
- "endereçado", "fechado", "confirmado" só com PR, commit, caminho ou saída de comando no mesmo parágrafo.
- Sem percentual de confiança: usar "medido" ou "não medido".
- Componente removido só se citado com a entrada de remoção.
- Afirmação agregada ("todos", "5 de 7") exige tabela por item.

## 5. Quando parar
- O Humano decide quando parar. Um modelo que não se julga apto (erro de medição recorrente, afirmação sem
  prova, perda de contexto) diz isso e pede substituição (entrada 789).

## 6. Seth
- A Seth carrega esta skill pela hidratação quando a tarefa envolve mudança no sistema. Ela não assina,
  não aplica e não envia nada para fora.

## Relacionadas
- `agata-carregar` (abrir sessão), `agata-mudanca-segura` (mudança na Máquina),
  `agata-aplicar-proposta` (aplicação P-8), `agata-fluxo-dupla` (detalhe do canal e da vigia).
