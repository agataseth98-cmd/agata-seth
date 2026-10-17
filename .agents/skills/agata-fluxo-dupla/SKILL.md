---
name: agata-fluxo-dupla
description: Trabalhar em DUPLA (Claude Code × Codex) no Agata — partida conjunta, fila, vigia sem timer, proposta → revisão cruzada → assinatura → aplicação → merge, fallback mútuo quando um cai e economia de cota. Use ao abrir ou retomar uma sessão conjunta, antes de publicar uma proposta, ao aplicar uma proposta assinada, ao entregar o comando de assinatura ao Humano, ou quando o outro agente some.
---

# Fluxo da dupla (primeira Skill do sistema Agata)

Por quê: em 16/10/2026 a dupla entregou ~20 mudanças assinadas num dia, e gastou cota e errou nas fronteiras que não
modelava (MEMÓRIAS (732): timer de 2 min, mensagens de estado, crase executada pelo shell, número (729) repetido 14 vezes,
vigia vencido). Esta Skill é o que ficou de pé. As ferramentas moram em `scripts/dupla/` (estado fora do repo, em `~/.cache/agata/sincronia/`).

## 0. Antes de tudo
- Cabeçalho da Regra 1 em TODA resposta, mesmo em NPR: `Agata · <modelo> · t=<n> (contador mecânico) · <hora -03> (relógio da Máquina)`;
  hora = `TZ=America/Sao_Paulo date`; t = `python3 scripts/dupla/contar_turnos.py`.
  Padrão = mensagens do Humano (o t= que ele acompanha). `--modo respostas TRANSCRITO` conta respostas do modelo (exige transcrito explícito; o Codex usa o dele). Sem fonte: `t=<n> (contado no contexto)`.
- Você NUNCA roda `scripts/aprovar.sh`, nunca usa `sudo`, nunca abre segredo. Só o Humano assina.
- Texto longo para o canal vai por ARQUIVO: `dupla.py dizer ... --texto "$(cat arq.txt)"`. Nunca crase dentro de aspas duplas.

## 1. Partida e retomada
`python3 scripts/dupla/dupla.py status` → se "divergente/aguardando": `iniciar --agente <eu> --nova-base --aceitar-matriz <hash da matriz>`.
`python3 scripts/painel_estado.py` mostra HEAD, serviços, propostas sem assinatura válida e o comando de assinatura. Fila: `~/.cache/agata/sincronia/fila.md`.
`dupla.py estado --agente <eu> --item <nome> --estado <em_andamento|em_revisao|pronto|bloqueado>` mantém o quadro (`quadro`). Dois itens ativos por agente.

## 2. Esperar sem gastar: vigia sem timer
- **Permanente (decisão do Humano, 16/10/2026):** a vigia roda sempre para todos os modelos, como unit `agata-vigia@<agente>` (`config/systemd/agata-vigia@.service`); eventos em `~/.cache/agata/sincronia/vigia-<agente>.log`. Quem tem Monitor só acompanha: `tail -n0 -F` nesse arquivo. Não precisa rearmar nem rodar `vigia.sh` à mão.
- Segundo plano (Claude, com Monitor): `bash scripts/dupla/vigia.sh <eu> 20`. Avisa mensagem do outro, `APROVADO-` novo, `main` andou e pedido parado ("DEVO RESPOSTA" ≥ 8 min; "PAR SEM RESPOSTA" ≥ 15 min).
- Bloqueante (Codex, e quem não acorda por stdout): `bash scripts/dupla/vigia.sh <eu> 20 --uma 600` — sai no primeiro evento ou imprime "SEM EVENTO em 600s". Chame de novo sem texto. Sem timer de 2 min.
- Monitores têm prazo (30 min): ao notificar a expiração, REARME. Ler o canal: `dupla.py ler --agente <eu>` (mostra só o novo).
- Mensagens: uma por ENTREGA ou BLOQUEIO, agrupada, com caminho + sha; nunca resposta só de estado; não copiar relatório para o canal.

## 3. Uma mudança protegida, do começo ao merge
1. Worktree própria de `origin/main` (`git worktree add -b proposta/<nome> .<agente>/worktrees/<nome> origin/main`). Nunca edite o checkout compartilhado.
2. Faça a mudança; gere SÓ o `.diff` dos protegidos (`git add -N <novos>`; `git diff --binary -- <arquivos> > x.diff`; `git checkout` para desfazer); `git apply --check`.
3. Teste a mudança aplicada numa cópia descartável (`git worktree add --detach`), com o perímetro (`bash scripts/perimetro.sh`) e a suíte (`bash scripts/testar_perimetro.sh`).
4. `propostas/<nome>.diff` em PR de abertura direto contra `main`; junte quando `fiscal-p8` e `suite-adversarial` passarem (merge pinado ao head).
5. REVISÃO CRUZADA: autor ≠ revisor. O revisor roda casos que ELE escolheu, antes de olhar o resultado, e responde com parecer em 4 partes quando for mudança estrutural.
6. Entregue ao Humano o comando de assinatura (§4). Só depois de `APROVADO-<nome>` em `propostas/`:
7. `python3 scripts/dupla/aplicar.py <nome> --registro <texto com {N}> --agente <eu> [--sem-pull]` (worktree própria, verificador da base, aplica, move o par, entrada de MEMÓRIAS, PR, espera os DOIS checks pelo nome, merge pinado). Um PR de aplicação por vez ou em lote único (dois simultâneos conflitam nas âncoras). Se der conflito, feche o PR e rode de novo.

## 4. O comando de assinatura (Humano, Fish, uma linha)
Gere pelo painel (`python3 scripts/painel_estado.py`) ou monte: confere o hash de CADA proposta antes de assinar qualquer uma, com bandeira `ok` (um `false` dentro do `for` seria sobrescrito) e igualdade positiva (arquivo ausente conta como divergência). Antes de entregar: a proposta TEM que estar em `origin/main` (`ls propostas/`) e o hash vem do arquivo, nunca da memória.

## 5. Fallback mútuo (quando um cai, o outro toca)
- `dupla.py ausente --agente <quem> --motivo ... [--ate HH:MM]` só com CONFIRMAÇÃO (Humano ou o próprio agente); silêncio NÃO prova cota esgotada. `presente --agente <quem>` encerra.
- Ausente: o outro cobre trabalho INDEPENDENTE na pista dele (aparece como ASSUMIDA em `dupla.py verificar`) e o titular revisa ao voltar.
- NÃO cai no fallback: assinar, `aprovar.sh`, `sudo`, configuração do GitHub, instalar/reiniciar serviço, abrir segredo.

## 6. Economia de cota (regra do Humano: "sem desperdício")
Despertar começa por checagem em shell (`git ls-remote origin main`, `ls propostas/APROVADO-*`, contagem de blocos novos); sem mudança: encerrar sem texto. Fila longa: itens de ≥ 10 min; terminou um, abra o próximo sem esperar mensagem. Não repetir prova verde.

## 7. Armadilhas já pagas
Crase em texto de argumento executa comando · `pkill -f` com o padrão na própria linha mata o seu shell (use PID) · número de MEMÓRIAS: `aplicar.py` aceita qualquer palavra após o número · comando de assinatura antes de a proposta chegar ao `main` · `fiscal-p8` obrigatório sem testar com o hook ligado (barrava todo PR) · afirmar comportamento de código só pela descrição da unit · hora herdada do cabeçalho anterior.
