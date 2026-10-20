# Correção da auditoria de 20/10/2026

Estado: proposta, não aplicada. Autor: Codex (GPT-6). Revisão independente: outro agente Codex (GPT-6), favorável, sem emenda obrigatória.

O diff inclui a porta 11436 do Laya no P-4. O P-9 acompanha a manutenção diária (timer e falha do oneshot), o Laya e o relé do LibreChat, retirando timers antigos. Timers de usuário fora de active passam a gerar aviso; serviços oneshot inativos não geram falso alarme. PROJETO passa a descrever o Laya ativo, o reinício automático dos contêineres e gateway/voz habilitados no boot.

Onze contraprovas offline cobrem binds corretos e expostos, timer failed/inactive/unknown, manutenção e Laya failed, ponte ausente e estado saudável. O teste entra na suíte e na lista do P-16. Revisor também conferiu IPv6 curinga, IP de rede e a regex do P-16 (6/6).

Limites: P-4 continua PARCIAL sem root; serviços de usuário inactive preservam a política anterior; P-9 continua apenas aviso. Nada exige reiniciar serviço. Para desfazer após aplicação: proposta assinada de reversão. Alcance: manifesto, controle P-9, testes e documentação. Falha detectável: contraprovas e perímetro.

Backup: a correção de caminho foi aplicada separadamente no PR 385 e consta na entrada 775. O P-12 agora alcança o disco TI-CSR, mas acusa o snapshot de 21/09 do modelo local. O blob é ilegível ao usuário; foi pedido ao Humano o backup do passo 2b do runbook. Não se alterou data nem tolerância do controle para liberar commit.

Validação final: suíte completa 57/57 (inclui lote de 11 contraprovas), bash -n e git diff --check aprovados. Diff retirado da árvore protegida e git apply --check aprovado contra a base 578d0d3. Perímetro da cópia: bloqueado exclusivamente por P-12; P-4 parcial sem root e P-10 sem vault no clone, declarados.

SHA256 do diff: 5de8479e92dd5aa4fe2a9ded94660fb28c6bf4dac60f34a8604de17bf60cbc07.

Atualização de 20/10 às 09:23: snapshot 56038913 de hoje às 09:07 conferido na listagem restic com as duas tags esperadas. P-12 reexecutado: exit 0 sem saída. Base atualizada para d1e4789; git apply --check continua aprovado. A pendência de backup acima foi resolvida separadamente, conforme entradas 776 e 777.
