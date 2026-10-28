---
name: agata-fluxo
description: Fluxo único de trabalho no sistema Agata para qualquer LLM (Claude, Codex, Seth ou outro) que atue numa tarefa. Usar ao começar uma sessão, ao dividir trabalho com outro modelo, antes de propor ou aplicar mudança, e ao registrar resultado.
---

# Fluxo Agata (universal)

Vale para qualquer modelo da Confederação. Use o cabeçalho exato de `PROTOCOLOS.md`: `agata-seth · <modelo> · t=<n> (<origem da contagem>) · <data e hora local + selo>`. O modelo específico só entra se estiver verificado; caso contrário, diga isso no campo.

## Escolha a skill necessária
- Sessão nova ou sem bloco de estado: `agata-carregar`.
- Proposta ou aplicação protegida por P-8: `agata-aplicar-proposta`.
- Trabalho com Claude/Codex em pistas separadas: `agata-fluxo-equipe`.
- Mudança em serviço, container, rede, energia ou boot: `agata-mudanca-segura`.
- Leitura ou contato com a Seth, quando solicitado: `agata-conversar-com-seth`.

Use as skills necessárias ao tipo de tarefa. Se ela envolver, por exemplo, runtime e arquivos P-8, use as duas skills correspondentes. Este fluxo define as regras comuns; cada skill especializada define só seu procedimento próprio.

Quando a tarefa pedir auditoria ou melhoria das skills Agata, inventarie as skills compartilhadas em `.agents/skills/`, procure duplicações e conflitos e proponha alterações que modelos locais menores consigam seguir: gatilho, pré-requisitos, passos curtos, condições de parada e resultado esperado. Preserve skills com responsabilidades distintas; consolide só procedimentos realmente duplicados. Faça revisão cruzada com `agata-fluxo-equipe` e entregue um `.diff` P-8. Não altere a skill instalada nem a publique antes da assinatura e integração; depois de integrada e sincronizada, ela fica disponível aos membros que carregam as skills deste repositório.

## 0. Antes de qualquer ação
1. **Medir o estado**, nunca supor: `git fetch -q && git status -sb`, `gh pr list --state open`,
   `python3 scripts/equipe/equipe.py status`. Sem medição, escrever "não medido".
2. **Canal**: `python3 scripts/equipe/equipe.py presente --agente <eu>`; ler o canal com
   `python3 scripts/equipe/equipe.py ler --agente <eu>`. Responder com `dizer --assunto ... --texto "$(cat arq)"`.
3. **Não tocar** no checkout compartilhado. Trabalhar em worktree própria a partir de `origin/main`.

## 1. Divisão de trabalho entre modelos
- Quem propõe redige a mudança em `propostas/<nome>.diff`; quem audita **executa** os comandos citados
  e reporta a saída literal. Quem audita não aprova.
- Dois modelos não editam o mesmo arquivo ao mesmo tempo (matriz de propriedade do `equipe.py`).
- Trabalho caro em tokens (suíte completa, varreduras longas) vai para o modelo com mais folga; o relato
  volta pelo canal, sem colar relatório inteiro.

## 2. Mudança protegida
Use `agata-aplicar-proposta` para criar, testar e aplicar uma proposta P-8. Em trabalho conjunto, some a revisão cruzada de `agata-fluxo-equipe`.

Regras que sempre valem: proposta em worktree própria baseada em `origin/main`; `.diff` verificável e testado; proposta e aplicação são etapas separadas; só o Humano assina; nenhum modelo roda `aprovar.sh`, usa `sudo` ou abre segredo. Não avance com teste ou assinatura ausente.

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
  `agata-aplicar-proposta` (aplicação P-8), `agata-fluxo-equipe` (detalhe do canal e da vigia).

## 8. Comandos padrão (para o Humano colar; todo modelo entrega neste formato)
Atualizar a checkout principal sem perder nada. Guarda qualquer arquivo rastreado modificado antes de devolvê-lo ao repositório:

```bash
bash -c 'R=$HOME/agata; B=$HOME/.agata-backup-staging/alteracoes-$(date +%Y%m%d-%H%M); M=$(git -C "$R" diff --name-only); if [ -n "$M" ]; then mkdir -p "$B" && for f in $M; do mkdir -p "$B/$(dirname "$f")" && cp "$R/$f" "$B/$f"; done && echo "Alterações guardadas em: $B"; git -C "$R" checkout -- $M; fi && git -C "$R" pull --ff-only && echo "Pronto: main atualizado"'
```

Assinar uma proposta (o Humano cola no próprio terminal, uma vez por proposta):

```bash
bash scripts/aprovar.sh <nome-da-proposta>
```

Regra: `<nome-da-proposta>` é o nome do arquivo `.diff` em `propostas/`, sem a extensão. Antes de assinar, confirme que o arquivo existe (`ls propostas/<nome>.diff`); se não existir, atualize a checkout com o comando acima.
