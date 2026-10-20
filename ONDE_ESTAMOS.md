# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 16/10/2026: `extras/arquivo/onde-estamos-ate-2026-10-16.md` (e até 27/09: `extras/arquivo/onde-estamos-ate-2026-09-27.md`).
O registro completo e permanente de tudo é `MEMÓRIAS.md`.

**20/10 — backup em disco novo.** O HD antigo de backup saiu. O backup agora fica numa pasta `AgataBkup01` dentro do disco TI, que tem outros usos e não foi formatado. O caminho fica em `~/.config/agata/hd-backup`. A cópia do backup antigo está em andamento.

**20/10 — backup conferido no disco novo.** O backup antigo voltou inteiro para o disco TI e passou na verificação. Os modelos que precisam de cópia ganharam cópia nova hoje, e o controle de backup está limpo.

## Hoje, 16/10/2026 (atualizado às 20h25)
**Já está valendo (você assinou, eu apliquei, o GitHub conferiu):**
- O GitHub exige a sua assinatura em toda mudança que altera comportamento. Testei o conferente com 15 quebras de propósito: ele pega 12 (os outros 3 não mudam nada na prática).
- Avisos de emoji e de fonte, métricas por rota, e a Seth sem emoji na prosa (o gateway foi reiniciado às 20h20).
- Painel de estado (`python3 scripts/painel_estado.py`), detector de derivados misturados, marcador da consolidação corrigido.
- Cofre de chaves: lista de segredos, verificador e uma cópia de recuperação cifrada para o seu pendrive.
- Janela de manutenção diária 12h15 a 13h15, com o treino do Laya todo dia: o timer está ativo, o primeiro ciclo é amanhã.
- A primeira Skill do sistema (`agata-fluxo-dupla`), licença Apache-2.0 e PROJETO dentro do teto.

**Com você:** nenhuma assinatura pendente. Testar a restauração do cofre com o pendrive (monta só leitura, pede `sudo`); guardar uma segunda cópia da chave; recriar os contêineres do LibreChat para valer as imagens fixadas; desativar os três timers antigos só depois de ver a janela rodar bem.

**Com o Codex (sem cota desde 19h38):** pesquisa de modelos gratuitos, KV cache, licenças dos componentes, tags dos selos.

**Ainda falta:** canais (todos desligados, só os gratuitos), cofre etapa 3, memória por tema, missões M01 a M10. Limites que continuam: a trava do escriba só protege quem passa por ela; as métricas do decisor não medem qualidade da resposta.
