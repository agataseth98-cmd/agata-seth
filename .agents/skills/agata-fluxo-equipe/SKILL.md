---
name: agata-fluxo-equipe
description: Trabalhar em EQUIPE no Agata — qualquer membro do Conselho (Claude Code, Codex, Gemini, Goose, Seth...), dois ou mais ao mesmo tempo: partida conjunta, fila, vigia sem timer, proposta → revisão cruzada → assinatura → aplicação → merge, fallback quando um cai e economia de cota. Use ao abrir ou retomar uma sessão conjunta, antes de publicar uma proposta, ao aplicar uma proposta assinada, ao entregar o comando de assinatura ao Humano, ou quando um membro some.
---

# Fluxo da Equipe (primeira Skill do sistema Agata)

Por quê: em 16/10/2026 a dupla Claude × Codex (nome antigo da Equipe, até 28/10/2026) entregou ~20 mudanças assinadas num dia, e gastou cota e errou nas fronteiras que não
modelava (MEMÓRIAS (732): timer de 2 min, mensagens de estado, crase executada pelo shell, número (729) repetido 14 vezes,
vigia vencido). Esta Skill é o que ficou de pé. As ferramentas moram em `scripts/equipe/` (estado fora do repo, em `~/.cache/agata/sincronia/equipe/`).

Membro = nome curto em minúsculas (`claude`, `codex`, `gemini`, `goose`, `seth`...). Nenhum nome é fixo no código: quem chega entra com `--agente <nome>`; `iniciar --com a,b,c` diz quem a partida espera (sem a lista, quaisquer dois abrem). Linha nova na matriz só entra com o aceite de TODOS os outros presentes.

> Protocolo MSG, memória do Conselho e auditoria: ver `agata-conselho-memoria`. Painel: ver `agata-painel`.

## 0. Antes de tudo
- Cabeçalho da Regra 1 em TODA resposta, mesmo em NPR: siga `PROTOCOLOS.md`, "Carregar e formatos" e "Regra 1.1". Não crie um formato próprio para o fluxo em equipe.
- Conte o turno com o contador disponível; sem contador ou prefixo completo, declare a base conforme a Regra 1. Não copie hora ou turno de resposta anterior.
- Você NUNCA roda `scripts/aprovar.sh`, nunca usa `sudo`, nunca abre segredo. Só o Humano assina.
- Texto longo para o canal vai por ARQUIVO: `equipe.py dizer ... --texto "$(cat arq.txt)"`. Nunca crase dentro de aspas duplas.

## 1. Partida e retomada
`python3 scripts/equipe/equipe.py status` → se "divergente/aguardando": `iniciar --agente <eu> --nova-base --aceitar-matriz <hash da matriz>`.
`python3 scripts/painel_estado.py` mostra HEAD, serviços, propostas sem assinatura válida e o comando de assinatura. Fila: `~/.cache/agata/sincronia/fila.md`.
`equipe.py estado --agente <eu> --item <nome> --estado <em_andamento|em_revisao|pronto|bloqueado>` mantém o quadro (`quadro`). Dois itens ativos por agente.

## 2. Esperar sem gastar: vigia sem timer
- **Permanente (decisão do Humano, 16/10/2026):** a vigia roda sempre para todos os modelos, como unit `agata-vigia@<agente>` (`config/systemd/agata-vigia@.service`); eventos em `~/.cache/agata/sincronia/vigia-<agente>.log`. Quem tem Monitor só acompanha: `tail -n0 -F` nesse arquivo. Não precisa rearmar nem rodar `vigia.sh` à mão.
- Segundo plano (Claude, com Monitor): `bash scripts/equipe/vigia.sh <eu> 20`. Avisa mensagem de outro membro, `APROVADO-` novo, `main` andou e pedido parado ("DEVO RESPOSTA" ≥ 8 min; "SEM RESPOSTA: <membro>" ≥ 15 min).
- Bloqueante (Codex, e quem não acorda por stdout): `bash scripts/equipe/vigia.sh <eu> 20 --uma 600` — sai no primeiro evento ou imprime "SEM EVENTO em 600s". Chame de novo sem texto. Sem timer de 2 min.
- Monitores têm prazo (30 min): ao notificar a expiração, REARME. Ler o canal: `equipe.py ler --agente <eu>` (mostra só o novo).
- Mensagens: uma por ENTREGA ou BLOQUEIO, agrupada, com caminho + sha; nunca resposta só de estado; não copiar relatório para o canal.

## 3. Mudança protegida em equipe
Use `agata-aplicar-proposta` para o ciclo P-8. Esta skill acrescenta a coordenação entre modelos:
1. Autor e revisor são pessoas/modelos diferentes; não editam o mesmo arquivo ao mesmo tempo.
2. O revisor escolhe e registra os casos antes de ver os resultados, executa-os e devolve o parecer no formato de quatro partes.
3. O autor abre a proposta contra `origin/main` e só a junta após os checks exigidos passarem. O Humano assina depois que a proposta estiver em `main`.
4. A aplicação é um PR separado, em worktree própria; um PR de aplicação por vez. O Humano junta esse PR.
5. Na divergência ou conflito, pare e reporte evidência; não force merge nem refaça a assinatura.

## 4. O comando de assinatura (Humano, Fish, uma linha)
Gere pelo painel (`python3 scripts/painel_estado.py`) ou monte: confere o hash de CADA proposta antes de assinar qualquer uma, com bandeira `ok` (um `false` dentro do `for` seria sobrescrito) e igualdade positiva (arquivo ausente conta como divergência). Antes de entregar: a proposta TEM que estar em `origin/main` (`ls propostas/`) e o hash vem do arquivo, nunca da memória.

## 5. Fallback (quando um cai, os outros tocam)
- `equipe.py ausente --agente <quem> --motivo ... [--ate HH:MM]` só com CONFIRMAÇÃO (Humano ou o próprio agente); silêncio NÃO prova cota esgotada. `presente --agente <quem>` encerra.
- Ausente: os outros presentes cobrem trabalho INDEPENDENTE na pista dele (aparece como ASSUMIDA em `equipe.py verificar`) e o titular revisa ao voltar.
- NÃO cai no fallback: assinar, `aprovar.sh`, `sudo`, configuração do GitHub, instalar/reiniciar serviço, abrir segredo.

## 6. Economia de cota (regra do Humano: "sem desperdício")
Despertar começa por checagem em shell (`git ls-remote origin main`, `ls propostas/APROVADO-*`, contagem de blocos novos); sem mudança: encerrar sem texto. Fila longa: itens de ≥ 10 min; terminou um, abra o próximo sem esperar mensagem. Não repetir prova verde.

## 7. Armadilhas já pagas
Crase em texto de argumento executa comando · `pkill -f` com o padrão na própria linha mata o seu shell (use PID) · número de MEMÓRIAS: `aplicar.py` aceita qualquer palavra após o número · comando de assinatura antes de a proposta chegar ao `main` · `fiscal-p8` obrigatório sem testar com o hook ligado (barrava todo PR) · afirmar comportamento de código só pela descrição da unit · hora herdada do cabeçalho anterior.

## 8. Devolutiva final para CODE
- Toda resposta final de entrega termina com `Devolutiva para CODE` e a Skill mais indicada para a continuação.
- Seja sucinta sem perder o necessário para retomar: resultado e estado; arquivos/PR e SHA quando houver; testes e placar; pendências, limites e confirmação humana exigida.
- Diferencie proposta, diff, assinatura, aplicação e merge. Não diga que algo foi publicado ou aplicado quando não foi.
- A devolutiva é texto no fim da resposta; não envie mensagem para outro agente ou serviço sem autorização explícita.
