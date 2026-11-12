---
name: agata-fluxo
description: >-
  Ponto de entrada do sistema Agata para qualquer modelo (Claude Code, Codex, Gemini, OpenCode, Seth ou outro).
  Use ao começar uma sessão ou tarefa neste repositório: medir o estado, escolher a skill certa, conduta que o
  modelo costuma esquecer, mudança no runtime da Máquina, afirmar com prova e registrar.
---

# Fluxo Agata (entrada única)

Vale para qualquer modelo da Confederação. Cabeçalho, formatos e voz estão no canon (`AGENTS.md`, `PROTOCOLOS.md`, "Carregar e formatos"). Esta skill guarda só o procedimento e as correções que já custaram tempo.

## 0. Antes de qualquer ação: medir o estado

Nunca suponha o estado. Sem medição, escreva "não medido".

1. `bash scripts/estado_para_eco.sh`. Não escreve no repo. Dá HEAD, topo de MEMÓRIAS, `sync:`, idade da hidratação, propostas abertas, hora da Máquina e `HASH-ESTADO`.
2. Se `sync:` não for `PASS`: `git -C ~/agata fetch -q` e `git -C ~/agata status -sb`. Nunca descarte mudança local (`checkout --`, `reset`, `restore`, `stash`) para "consertar" sync: pode ser aplicação assinada em andamento. Mostre `git diff --stat` e pergunte ao Humano. (MEMÓRIAS (248)-(252))
3. Leia o topo de `MEMÓRIAS.md`, logo abaixo de `ENTRADAS-NOVAS:AQUI`: número e título.
4. `quebrado:` = itens abertos nas entradas recentes e propostas com `.diff` sem `APROVADO-`.
5. Responda com o bloco de "Carregar e formatos" (`PROTOCOLOS.md`), nada antes. Depois, eco de até 5 linhas citando o `HASH-ESTADO`. O Humano confirma antes do trabalho começar.
6. Sem o bloco de estado injetado, rode os mesmos comandos à mão. O hook `SessionStart` do projeto (`.claude/settings.json`, `scripts/sessao_claude_contexto.sh`) já entrega estado, últimas entradas do cache do Conselho e estado da equipe.

Carregar não autoriza nem aplica mudança.

## 1. Conduta (o que o modelo costuma esquecer)

- **Cabeçalho em toda resposta**, com a hora medida agora (`date`), nunca copiada da resposta anterior. Sem cabeçalho a resposta é inválida: corrija na seguinte, em uma linha. Formato no canon (`PROTOCOLOS.md`, selo de origem obrigatório). O turno é contado no contexto; sem contador, declare a base. O nome do modelo só entra se estiver verificado; senão, diga isso no campo.
- **Modo conciso** é o padrão: resultado primeiro. Processo só para constatar erro, em uma linha. "Modo explicativo" liga o longo; "modo conciso" desliga. (`REGRAS.md`, NPR)
- **Aviso antes de ação externa.** Antes de `git push`, abrir ou juntar PR, envio a Drive, Discord, Gmail ou outro serviço externo, hook que envie dados para fora (inclusive o pós-commit que manda o índice ao Drive), ou reinício de navegador ou serviço compartilhado: diga o que vai acontecer e espere o "sim". "Pode seguir" vale só para aquela ação.
- **Consulte antes de mexer em trabalho alheio.** Antes de criar, mover ou editar arquivo em pasta de outro modelo ou pessoa, confira o dono (`ONDE_ESTAMOS.md`, `cache_conselho.py ler`). Se for de outro, pergunte. Rascunho próprio vai numa pasta sua. (compromissos de 22/10/2026)
- **Antes de encerrar ou reiniciar um processo**, leia o launcher e confirme as variáveis e caminhos que ele usa por padrão (ex.: `AGATA_RELAY_EXTENSION`). Depois de subir, verifique porta, processo e endpoint. Se falhar, diga o que falhou e quanto tempo o serviço ficou fora. (três falhas de 28/10/2026)
- **Leitura declarada com precisão.** Diga quais partes leu, com as linhas. "Li REGRAS.md linhas 75-82" é verdade. "Li o REGRAS" é falso se a leitura foi parcial.
- **Citação inventada se expurga.** Ao registrar o erro, não repita o literal. Troque por `[citação inventada, expurgada em DATA por ordem do Humano]` (`AGENTS.md`).
- **Nada de sudo, nada de `aprovar.sh`, nada de segredo.** Quem assina é o Humano. (`AGENTS.md`)

## 2. Escolha a skill da tarefa

| Tarefa | Skill |
|---|---|
| Proposta ou aplicação P-8, lote, CI local, PR de proposta | `agata-aplicar-proposta` |
| Trabalho em Equipe (dois ou mais membros), canal MSG, vigia, papéis, fila | `agata-equipe` |
| Mudança no runtime da Máquina (unit, container, firewall, rede, energia, boot) | seção 4 deste arquivo |
| Painel operacional (porta 20146): textos, cores, popups, medições | `agata-painel` |
| Voz, ler em voz alta, conversa falada, debate com a Seth | `agata-voz` |
| Conversar com a Seth, acompanhar a conversa dela | `agata-conversar-com-seth` |
| Adaptadores de chats web (Relay) | `agata-relay-provedores` |
| Melhoria nova com SDD: pesquisa, spec, revisão, decisão | `agata-time-inovacao` |
| Engenharia reversa de app ou bundle (REA) | `agata-engenharia-reversa` |
| Como a LLM falha; custo, contexto, alucinação; rodada de experimento | `agata-llm-fundamentos` |
| Prática específica (testes, segurança, revisão, banco, frontend) | `python3 -I ferramentas/ferramentas.py tema <tema>`, depois `ver <nome>` |

- Se a tarefa mistura runtime e P-8, use as duas skills.
- Caixa de ferramentas: tema `quarentena` só se lê, nunca se carrega sem decisão do Humano. Hooks do ECC ficam em `ferramentas/fontes/ecc/hooks-inativos/`, desligados; ligar um exige decreto assinado. Nada em `ferramentas/fontes/` é executado daqui. Se uma peça repetir skill `agata-*`, vale a do Agata. Atualizar uma fonte: novo `COMMIT`, `reindexar`, decreto.
- Auditoria ou melhoria das skills Agata: inventarie `.agents/skills/`, ache duplicação e conflito, proponha `.diff` P-8 com revisão cruzada (`agata-equipe`). Não altere a skill instalada antes da assinatura.

## 3. Mudança protegida e divisão entre modelos

- Mudança em arquivo protegido (lista em `propostas/README.md`; `.agents/` tratado como protegido) só entra no `main` por proposta P-8 assinada pelo Humano. Use `agata-aplicar-proposta`. Nunca use `write` ou `edit` em canon.
- Trabalho em worktree própria a partir de `origin/main`. Não toque no checkout compartilhado. Não use `git stash` nele (é compartilhado entre worktrees): guarde trabalho com commit WIP ou `git stash push -u -m <tag>`, conforme o ambiente. Se for indispensável preservar alteração local, faça backup fora do repositório e confira o hash antes de qualquer atualização. Nunca descarte arquivo local sem decisão do Humano.
- A Seth recebe as skills pela hidratação quando a tarefa envolve mudança no sistema. Ela não assina, não aplica e não envia nada para fora.
- Quem propõe redige `propostas/<nome>.diff`. Quem audita executa os comandos citados e reporta a saída literal; não aprova.
- Dois modelos não editam o mesmo arquivo ao mesmo tempo (matriz de propriedade do `equipe.py`).
- Trabalho caro em tokens (suíte completa, varredura longa) vai para o modelo com mais folga. O relato volta pelo canal, sem colar o relatório inteiro.
- Subagente só quando a sessão permitir e o Humano pedir.

## 4. Mudança no runtime da Máquina

Use antes de alterar algo que roda: unit systemd, container, firewall, config de serviço, rede, energia ou boot. Se a mudança também toca arquivo protegido do repo, siga `agata-aplicar-proposta`; esta seção cobre o efeito no runtime.

O sistema quebra nas fronteiras que ele não modela (bússola T1, `extras/bussola/`). Motivo: em 24/09/2026 tirar uma linha de uma unit consertou o Hyprland e, em silêncio, desligou a contenção de suspensão e o fechamento do Obsidian (MEMÓRIAS (536), (539), (540)). Nenhum sensor pegou. Só o teste real.

1. **Portão das três perguntas** (`REGRAS.md`, "Mudança estrutural"), respondidas por escrito antes:
   - Desfaço sozinho, ou preciso de alguém? Escreva o comando de volta e faça o backup antes.
   - O que mais isto toca? Responda com os comandos do item 2, não de cabeça.
   - Eu saberia se quebrasse? Diga qual comando ou log mostra a quebra. Se nenhum, a mudança precisa de um.
2. **Acoplamentos implícitos**, conferidos na Máquina:
   - systemd: `systemctl --user list-dependencies --reverse <unit|target>` e o inverso; `grep -r` por `Wants|Requires|PartOf|BindsTo|WantedBy` em `~/.config/systemd/user/` e `/etc/systemd/`. Target com `StopWhenUnneeded` para sozinho.
   - App Flatpak roda em `app-flatpak-*.scope` próprio (`PartOf=graphical-session.target`): parar o serviço que o lançou não o fecha.
   - Portas: `config/portas-agata.txt` (P-4) e `ss -tlnH`. Firewall: `ufw status numbered`.
   - Serviços vigiados: lista do P-9 em `PROJETO.md`, "Serviços (boot)". Inibidores: `systemd-inhibit --list`.
   - `bash scripts/perimetro.sh` antes e depois. Diferença de veredito = acoplamento.
3. **Prova pelo caminho real.** Exercite o que o Humano usa (botão, atalho `seth` ou `seth-parar`, login, boot quando possível) e leia o log do instante (`journalctl --since`). Teste também o lado negativo: o que devia continuar bloqueado continua bloqueado? Evento que só se prova no próximo boot: diga isso e deixe como pendente, com dono.
4. **Registro.** O que mudou fora do repo (runtime, `/etc`, `~/.config`) vai na entrada de MEMÓRIAS, com o comando de desfazer. Efeito colateral achado depois vira entrada nova, com o "erro meu" dito sem suavizar.

## 5. Afirmar com prova e registrar

- "Medido" é medido. "Deve funcionar" não é prova. Sem medição, a frase começa com "não medido". Sem percentual de confiança.
- "endereçado", "fechado", "confirmado" só com PR, commit, caminho ou saída de comando no mesmo parágrafo.
- Afirmação agregada ("todos", "5 de 7") exige tabela por item.
- Componente removido só se citado com a entrada de remoção.
- Fato do sistema: busque antes. Prioridade 1 é o vault (`python3 scripts/busca_semantica.py "frase"` ou `python3 scripts/busca_texto.py`). Depois confirme no canon e cite caminho e linha.
- Antes de dizer "assinado", confira se `propostas/APROVADO-<nome>` existe. Um "ok" do Humano não cria o arquivo.
- Conversa com outro modelo não é fonte. Só entra o que tiver PR, commit ou medição (M7, entrada 791).
- Antes de entregar texto com afirmação verificável, rode `python3 redesign/router/auditoria_turno.py --verificar < arquivo` (mecânico: Jev sem consulta, P-n, entrada e caminho inexistentes, citação inventada). Corrija o que apontar. Se um número de entrada não existe, escreva "não encontrei".
- Memória comum do Conselho: ao começar, `python3 redesign/router/cache_conselho.py ler --n 20`. Ao fechar trabalho relevante, `python3 redesign/router/cache_conselho.py anotar --autor "<modelo real>" --tipo fato|decisao|pendencia|nota "<texto>"`. Não é canon. Segredo é recusado; dado pessoal vira marca. Fato medido leva comando e hora; pendência leva quem deve agir.
- Resultado vai para `MEMÓRIAS.md` só por PR, em entrada nova logo abaixo de `ENTRADAS-NOVAS:AQUI`. Nunca edite entrada antiga (P-5). Correção é entrada nova.

## 6. Quando parar

- O Humano decide quando parar. Modelo que não se julga apto (erro de medição recorrente, afirmação sem prova, perda de contexto) diz isso e pede substituição (entrada 789).

## 7. Comandos padrão (para o Humano colar)

Atualizar o checkout principal sem perder nada. Guarda qualquer arquivo rastreado modificado antes de devolvê-lo ao repositório:

```bash
bash -c 'R=$HOME/agata; B=$HOME/.agata-backup-staging/alteracoes-$(date +%Y%m%d-%H%M); M=$(git -C "$R" diff --name-only); if [ -n "$M" ]; then mkdir -p "$B" && for f in $M; do mkdir -p "$B/$(dirname "$f")" && cp "$R/$f" "$B/$f"; done && echo "Alterações guardadas em: $B"; git -C "$R" checkout -- $M; fi && git -C "$R" pull --ff-only && echo "Pronto: main atualizado"'
```

Assinar uma proposta (o Humano cola no próprio terminal, uma vez por proposta):

```bash
bash scripts/aprovar.sh <nome-da-proposta>
```

`<nome-da-proposta>` é o nome do `.diff` em `propostas/`, sem extensão. Antes, confirme que o arquivo existe (`ls propostas/<nome>.diff`). Se não existir, atualize o checkout com o comando acima.
