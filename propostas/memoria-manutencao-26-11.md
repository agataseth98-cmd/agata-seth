# Proposta memoria-manutencao-26-11 — guarda do selo (1)-(62) e aviso de teto para MORNO

Classe: Canon + Comportamento (toca `PROTOCOLOS.md` e `scripts/perimetro*`).

**Origem:** pedido do Humano via Gemini (cache 965, 26/11/2026 11:14), itens 1 e 2 de `gemini-2026-11-26-5b6c5808`.

## O que era

- **Item 1 — âncora (1)-(62):** `scripts/achar_ancora_1_62.py` varre `MEMÓRIAS.md` por janela de 128.671 B e sha256 `b26ac1…`. O trecho migrou para `memoria/frio/MEMORIAS-FRIO-2026-09-06-com-migrado.md` pela Fase 4 (357), então o script devolve "NENHUM offset bateu" ao rodar hoje. `PROTOCOLOS.md:345` continuava citando o script sem apontar a camada fria nem a guarda oficial.
- **Item 2 — MORNO sem teto:** `MEMORIAS-MORNO.md` cresce sem gatilho de aviso. Medido em `2026-11-26 21:47`: 1.173.260 B, sem congelamento novo desde 23/10/2026 (frios de ~90-110 KB cada). O P-24 cuida só do quente.

## O que muda

- `PROTOCOLOS.md:345`: substitui a linha da âncora (1)-(62). A guarda oficial passa a ser `bash scripts/selar.sh --check` contra o registro em `SELOS.txt` (P-14/P-25, selo já presente na linha `8783d29d…  memoria/frio/MEMORIAS-FRIO-2026-09-06-com-migrado.md`). O script `achar_ancora_1_62.py` fica no repositório como artefato histórico, com nota explicando por que não localiza o trecho no quente.
- `scripts/perimetro/p28_morno_orcamento.sh`: controle novo P-28. Fase atual **AVISO (PARCIAL), nunca FALHA**, padrão herdado do P-24. Limite: 1.024.000 bytes (1.000 KB). Mensagem traz o próximo passo: `migrar_periodo.py` + `selar.sh`. Escalada para FALHA fica para fase seguinte, como no P-24.
- `scripts/perimetro.sh`: `source` do p28 e chamada logo após o P-27, antes do P-17 (para o SKIP crônico cobrir o novo controle também).

## O que **não** muda

- `scripts/achar_ancora_1_62.py` fica intocado (histórico).
- `MEMORIAS-MORNO.md` não é migrado neste lote; o controle só avisa.
- Limite do P-24 e dos outros controles.

## Testado nesta medição

- `bash scripts/perimetro.sh` com o P-28 integrado: emite AVISO com o valor real medido (1.173.260 B > 1.024.000 B) e **RESULTADO GERAL: OK — 21 OK · 2 SKIP · 5 PARCIAL · 0 FALHA**.
- `scripts/ci_sdd_local.sh` com pytest 9.2.0: **94/95 OK**. Única falha: `[1/95] testes SDD (pytest)` → `ModuleNotFoundError: No module named 'yaml'` em `tests/ferramentas_unificadas/ferr_helpers.py`. Falha **pré-existente** no `origin/main` (b32fe9e2), já registrada por Codex no cache do Conselho (964) e reproduzida em worktree limpa. Não causada por este lote.
- `python3 redesign/projeto_indice/verificar_destinos.py`: `destinos: OK (todo parágrafo que saiu do índice está no destino declarado)` — texto original do parágrafo (1)-(62) preservado em PROTOCOLOS.md; a atualização entra como bullet novo logo abaixo, mantendo o snapshot de destinos.
- `pytest redesign/projeto_indice/tests/`: 24/24 OK depois de `python3 scripts/gerar_estado.py` (ESTADO.md é regerado pelo pre-commit no commit real; aqui foi regerado à mão para o pytest ver o estado consistente).
- `grep -F "memoria/frio/MEMORIAS-FRIO-2026-09-06-com-migrado.md" SELOS.txt`: retorna a linha com o sha256 `8783d29d…` selado (guarda oficial validada).

## Reversão

`git apply -R propostas/aplicadas/memoria-manutencao-26-11.diff`.

## Apetite (R2)

Arquivos tocados: 3 (`PROTOCOLOS.md`, `scripts/perimetro.sh`, `scripts/perimetro/p28_morno_orcamento.sh`). Linhas adicionadas: ~25. Dentro do apetite de lote pequeno.

## Pendente deste conjunto

Item 3 de `gemini-2026-11-26-5b6c5808` (busca guiada + cache por SELOS em `gerar_obsidian.py`/`busca_semantica.py`/`gerar_indice_derivado.py`) **fica para lote próprio** — escopo maior, toca 3 scripts de derivação, e não cabe na mesma assinatura por R1.

## Assinatura

`bash scripts/aprovar.sh memoria-manutencao-26-11`
