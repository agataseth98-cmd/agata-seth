# Proposta caminho-visao-23-11 — primeiro passo do "Caminho até a visão" (uma assinatura)

Ordem do Humano, 23/11: "sem hd por enquanto o restante pode fazer. me entregue apenas assinatura única e utilize as ferramentas do sistema agata"; "aproveite para já aprimorar e resolver tudo que for encontrado no caminho"; e auditar a ideia de skill de adesão trazida da Seth.

Feito por agentes do sistema (agata-dev ×3, agata-spec, agata-revisor; Claude Haiku 5.5), orquestrado e conferido pelo Claude Opus 5.5.

## O que muda
1. **Painel — sob demanda e recarga.** Unidade parada de propósito (socket em escuta, ou lista fixa: whisper, embeddings, obsidian-ro-proxy, obsidian-app, ouvido-agata, timer de manutenção pela decisão de 29/10) aparece como SOB DEMANDA; failed vira ERRO. /api/status, /api/lacunas e /api/capacidades usam a mesma regra (lacunas na Máquina: 6 → 0 falsas, medido). Sub-telas de leitura (equipe, backup, saída de rede, perímetro, CI, memória do Conselho, importantes, lacunas, qualidade, catálogo) recarregam a cada 60 s, só visíveis e sem diálogo aberto ou texto digitado. Painel: 803 → 816 testes.
2. **P-23 verdadeiro para a Seth.** O controle confere a doutrina que o gateway monta (`doutrina_montada`), não o texto do .py. O aviso de 23/11 era falso: a Seth já recebe o AGENTS.md inteiro.
3. **Regra 0 no CI local.** Cada passo anuncia o início (`... [n/total]`) e o fim (`OK [n/total · tempo]`); total contado de verdade.
4. **P-27 novo** (só aviso): atalhos `agata` e `fechar-agata` instalados × fonte versionada. Em 23/11 o fechar-agata estava atrás do repo sem ninguém ver. Nota: a SPEC de Landlock (não implementada) planejava um "P-27"; se sair, renumera.
5. **P-10/P-17.** Em worktree vinculada (sem vault, por desenho) o P-10 dá SKIP isento e não alimenta a série do P-17; isento não zera a série. P-16 passa a cobrir os testes novos.
6. **Skill obrigatória `agata-mapear-humano`** + "Protocolo de inserção humana continuado" no PROTOCOLOS.md + linha no AGENTS.md + índice de skills. Citação do Humano de 18/11 entra aqui pela primeira vez no repositório: **Humano, confira o texto.** Regra acrescentada pelo agente ("saúde, finanças e localização não entram sem ordem explícita"): mantida; corte se não quiser.
7. **Auditoria da ideia "SKILL — Adesão a processos" (vinda da Seth).** Veredito: não vira skill nova. Tudo nela já está no canon (doutrina da Seth no PROTOCOLOS.md, seções conferidas por grep, e AGENTS.md); uma segunda cópia reabriria a deriva que a sincronia-12-11 fechou (fonte única). Duas lições valem para todo modelo e só existiam na doutrina da Seth: "leitura parcial não prova fim" (FAB-6) e "lista de falhas não prova ausência" ((725)); entram na skill agata-fluxo, seção 5.
8. **Achados no caminho.** test_rotas_locais: 2 testes já falhavam no main (a injeção real passou de 6000 tokens estimados; o teto do local-a no teste subiu para 12000; produção usa 48000 e não muda); testar_sincronia 17 → 18 regras; índice de ferramentas reindexado; testes do roteador (test_seth_base, test_rotas_locais) passam a rodar no CI local.

## Revisão independente (agata-revisor)
Bloqueios: (1) testes do roteador fora do CI — corrigido; (2) par de proposta — este. Corrigidos: recarga presa por campo preenchido por script; denominador do Panorama contando sob demanda; CI sem sinal durante o passo; P-16 sem os testes novos. Mantidos com motivo: P-10 isento em worktree (o vault só existe no checkout principal; lá a conferência continua); manutenção como sob demanda (decisão de 29/10). Notas aceitas sem mudança: P-23 em modo full lê o .hidrata-seth.md do checkout principal (produção usa compacto); `.github/workflows/sdd.yml` não recebe os testes do roteador (diff assinado não toca workflows).

## Medido
CI local: `CI LOCAL: TUDO OK` (93 passos). `git apply --check` em cópia limpa do origin/main: OK. Suíte do perímetro: `SUITE OK -- 63 caso(s)`.

## Não medido
Visual na página real (conferir após aplicar, com restart do painel); latência das leituras novas de socket; se um modelo segue a skill nova.

## Depois de aplicar
Restart do painel e do seth-gateway; perímetro no checkout principal; o vault regenera no próximo commit do checkout principal (P-27 novo nos controles).

**Reversão:** `git apply -R propostas/aplicadas/caminho-visao-23-11.diff` e restart dos dois serviços.

Assinatura: bash scripts/aprovar.sh caminho-visao-23-11
