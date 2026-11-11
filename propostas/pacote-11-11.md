# Pacote 11/11: seis propostas numa assinatura (`pacote-11-11`)

Proposta P-8 de `pacote-11-11`. Diff: `propostas/pacote-11-11.diff` (32 arquivos de código; sha256 `6e319f65a60e91cbf6a87f907baa9cfcb1f428c3455c6daffc51768f07029345`). Base: `origin/main` `21095eaf` (já inclui `historia-tomo1-11-11`, PR #971). Assinatura do Humano, uma vez, depois do merge deste PR de proposta.

Pedido do Humano em 11/11/2026, 20:02: "me apresente apenas uma assinatura; se der certo, oficialize". Regra correspondente na skill: "Pacote de assinatura (Humano, 11/11)", em `.agents/skills/agata-processo-lote/SKILL.md`.

## Em resumo (para o Humano)

- Junta seis propostas que mexiam nos mesmos arquivos do painel e da skill do processo numa só assinatura: chat-lote4, processo-agil, spec-primeiro, voz-compreender, painel-importantes e historia-tomo1.
- Cada parte foi aplicada na ordem abaixo. Os cinco conflitos e o que foi feito estão listados. Nenhuma intenção de nenhuma parte foi perdida.
- Testado inteiro: unittest do painel com 454 testes OK; `scripts/ci_sdd_local.sh` com TUDO OK; gate de spec sem falha; lint de skills OK.
- Assinar: `bash scripts/aprovar.sh pacote-11-11 "<motivo>"`.
- Pendência da História: o botão Ouvir lê o texto inteiro de uma vez (pode levar ~10 min) e não tem Parar. Proposta futura de fala em partes.

## Ordem de aplicação

1. `chat-lote4-09-11`: base `d782dad0`. `git apply` limpo.
2. `processo-agil-11-11`: skill `agata-processo-lote`. `git apply` limpo.
3. `spec-primeiro-11-11`: depende de 2 (mesmo arquivo de skill; o `index` do diff é o blob `24fc9e2d`). Aplicado depois de 2, `git apply --check` limpo. Inclui o drift regenerado de `nova_versao`.
4. `voz-compreender-11-11`: `AGENTS.md` e skill `agata-voz`. `git apply --check` limpo.
5. `painel-importantes-11-11`: quatro trechos em conflito (abaixo). Os outros arquivos aplicaram limpo.
6. `historia-tomo1-11-11`: por último. Seis trechos em conflito (abaixo). O texto de `historia/tomo-01/` é a cópia do original, conferida por sha256 `fe79c529046075dcf03f713eec10b91d7f9b13936cd4c561122408d68eb9906a`.

Cada parte foi aplicada com `git apply` ou, nos trechos em conflito, com `--reject` seguido de encaixe manual pela âncora de texto atual (nunca por número de linha). Nenhum diff foi reescrito.

## Conflitos e como foram resolvidos

### Parte 5 (painel-importantes-11-11), sobre o lote 4

- `redesign/painel_operacional/prototipo.css`: o bloco de CSS foi colocado depois de `.oc-cabecalho .oc-lede`, a mesma âncora da proposta. As regras do lote 4 continuam no arquivo, sem perda.
- `redesign/painel_operacional/prototipo.js`: o bloco "Importantes" foi colocado antes do comentário "Entrada: a seção vem do hash". A entrada `importantes` em `CARREGAR_SUB` aplicou com deslocamento.
- `redesign/painel_operacional/spec/acceptance.json`: os dez critérios novos foram anexados depois do último critério do lote 4.
- `redesign/painel_operacional/spec/spec.md`: cinco trechos inseridos por âncora de texto: bullet de escopo (depois do bullet do lote 4); dez critérios (depois do último critério do lote 4); linha de reversão (depois da linha do lote 4); risco (depois de "`pytest` precisa estar disponível"); arquivos de código (depois de "`test_frentes.py`").

### Parte 6 (historia-tomo1-11-11), sobre o lote 4 e o painel-importantes

- `redesign/painel_operacional/prototipo.js`: a entrada `historia` em `CARREGAR_SUB` foi colocada depois de `conselho-memoria`.
- `redesign/painel_operacional/prototipo.css`: o bloco da História foi colocado depois do bloco de Importantes.
- `redesign/painel_operacional/server.py`: `import historia_painel` depois de `import chat_stream`. Os métodos `_historia_listar`, `_historia_texto` e `_historia_ouvir` foram colocados antes de `_grafo`. As rotas `/api/historia*` e o ativo `/historia.js` aplicaram limpos.
- `redesign/painel_operacional/test_painel_unificado.py`: `SCRIPTS` ganha `historia.js`; `SECOES` passa a ter oito seções, com `historia`. A linha do Panorama com `importantes` (da parte 5) foi mantida.
- `redesign/painel_operacional/spec/spec.md`: bullet de escopo depois do bullet de Importantes; bloco de rotas da História antes de "### Ativos servidos", com `/historia.js` na linha "Ficam"; três arquivos novos na seção Código, depois de `test_importantes_ui.py`.
- `redesign/painel_operacional/spec/acceptance.json`: os quinze critérios novos foram anexados depois do último critério de Importantes. A troca de "sete seções" por "oito seções" aplicou limpa.

### Incidente de processo (registrado, corrigido antes da proposta)

Depois do primeiro CI local, os artefatos regerados (`redesign/nova_versao/spec/criterion-drift.md`, `evidence.json`, e `redesign/sdd_flow/spec/criterion-drift.md`, `evidence.json`) foram limpos. Ao limpar, o drift de `nova_versao` da spec-primeiro foi revertido por engano. O CI seguinte falhou só no gate de sincronia, por isso. Foi restaurado com `git apply --include` a partir de `propostas/spec-primeiro-11-11.diff`. O CI final passou sem falha. Os artefatos que o CI regera e que não fazem parte do pacote foram removidos, e não estão no diff.

## Testes medidos

- Unittest do painel (`cd redesign/painel_operacional && python3 -m unittest discover -s . -p "test_*.py"`, com `uv run --offline --with pytest` e o node do scratchpad no PATH):
  - depois das partes 1 a 5: 435 testes, OK (19 s);
  - depois da parte 6: 454 testes, OK (20 s);
  - final, com a regra da skill e o drift restaurado: 454 testes, OK (23 s).
- CI local `uv run --offline --with pytest bash scripts/ci_sdd_local.sh`:
  - depois das partes 1 a 5: `CI LOCAL: TUDO OK` (35 passos OK);
  - depois da parte 6: 1 passo falhou (gate, pelo incidente acima);
  - final: `CI LOCAL: TUDO OK`, 35 passos OK e 0 falha.
- Gate de spec (`python3 -I scripts/gate_spec_sync.py`): 12 componentes, 1 aviso (dívida conhecida da alexandria, em `EXCECOES`), 0 falha.
- Lint de skills (passo "skills sem problema de lint" do CI): OK.
- Reversão: `git apply --check` do diff sobre `origin/main` limpo; aplicado na árvore, `git apply -R --check` OK; revertido em seguida, com a árvore voltando ao `origin/main` mais o registro.
- Captura no Chromium headless 156, servidor na porta 20256, HOME falso com dados fabricados, 1440 px. Dois PNG fora do repositório: `/tmp/claude-1000/-home-orusoua-agata/634b0edc-ec9d-4b4f-92bb-7fb16f4d2c75/scratchpad/pacote-conversa-ramos.png` (conversa com ramos, seletor `<2/2>`) e `/tmp/claude-1000/-home-orusoua-agata/634b0edc-ec9d-4b4f-92bb-7fb16f4d2c75/scratchpad/pacote-importantes.png` (aba Importantes com três abertos e o cartão do Panorama).

## Não medido

- Run verde no GitHub no `headSha` do PR: depois do push.
- Fala real do botão Ouvir: não disparada. Testada só por HTTP com voz falsa, na parte 6.
- Navegadores além do Chromium headless. O Brave do Humano não foi usado.
- Uso real com os dados do Humano: as capturas usam dados fabricados.
- Lista de Importantes perto do limite de 2000 itens, e dois usuários escrevendo ao mesmo tempo.
- Efeito da quarentena de `historia/` no fluxo de propostas: a primeira assinatura medirá.
- O gate com `criterion-drift.md` de `nova_versao` depende de a spec-primeiro e de este pacote entrarem juntos. Medido só localmente.

## Decisões pendentes de cada parte (copiadas dos `.md` originais)

### chat-lote4-09-11

Para o Humano confirmar, oito decisões do agente:

1. Trocar de versão segue a resposta mais nova de cada passo seguinte (a última criada em cada ramo).
2. Parar sem texto grava uma resposta vazia marcada como interrompida; essa resposta não vai ao gateway.
3. Erro no meio do stream também mantém o texto parcial marcado (decisão D3 aplicada a erro).
4. Continuar usa o modelo escolhido na hora e atualiza o modelo que respondeu; o campo `modelo` da primeira parte não muda.
5. Feedback: trocar de "Útil" para "Não útil" mantém o motivo já escrito.
6. Ramificar inclui a mensagem clicada e usa o mesmo título da conversa de origem.
7. Com resposta em curso, a troca de conversa fica bloqueada pela trava única da proteção (aviso na tela).
8. A nota gravada continua `bom` (útil) e `ruim` (não útil); só o rótulo mudou, por decisão E-2 (sem emoji).

Pendência: Parar com o gateway real depende da proposta `chat-stream-verificar-depois-09-11`, ainda sem `.diff` nem commit em `propostas/`. Até lá, o botão corta a espera e o texto que já chegou. O campo `interrompida: true` e o estado `verificacao.estado = interrompida` precisam ser unificados na aplicação da proposta de verificação.

### processo-agil-11-11

- Medição R1, R3, R5 e R2 por 14 dias, até 25/11/2026. Critério para manter ou reverter: proposto, o Humano decide em 25/11/2026. Proposta do autor: manter se nenhum componente passar de 2 propostas abertas e as propostas sem assinatura caírem para até 5; senão, reverter R1 e rever a medição.

### spec-primeiro-11-11

- Medição de P1 a P4, prazo sugerido de 14 dias (até 25/11/2026). O Humano decide o prazo.
- Dívida da alexandria: cinco critérios sem linha no `spec.md`, em `EXCECOES` de `scripts/gate_spec_sync.py`, como AVISO. A correção (cinco linhas no `spec.md`) fica para proposta própria.
- Onze specs sem `criterion-drift.md`: o item de drift não roda nelas. Gerar snapshot para todas é decisão do Humano.

### voz-compreender-11-11

- Medição: pedidos "fale" atendidos com texto adaptado, por anotação `fala: texto adaptado, saída <n>` no cache do Conselho. Critério para manter ou reverter: proposto, o Humano decide em 25/11/2026.
- Riscos: "fale" é palavra comum (a cláusula "sem outro alvo" existe por isso; não medido se o modelo a respeita). Segredo: a skill manda não falar se a resposta trouxer senha, token ou dado pessoal. O script não ouve o resultado.
- Conflitos com propostas abertas, medidos com `git apply` numa cópia: `AGENTS.md` conflita com `verificar-rastro-20261106` e `docs-opencode-07-11` nas duas ordens; `nucleo-desenvolvimento-07-11` conflita se vier depois deste diff. Essas três continuam abertas, fora deste pacote.

### painel-importantes-11-11

1. Onde ficou: aba dentro de Panorama, e não oitava seção (a spec fixa sete seções; a História fez oito, em parte 6).
2. Rota nova não pedida na lista da tarefa: `POST /api/importantes/trazer`, para o botão "Trazer do Conselho".
3. Convenção `IMPORTANTE`: a marca é o início do texto da entrada do cache, não campo do esquema. Não medido como convenção de uso.
4. Origem `modelo`: existe no esquema, mas nenhuma rota a grava.
5. Texto digitado pelo Humano não passa por filtro de segredo (fica local, como as conversas). Só o texto trazido do cache passa por `cache_conselho.filtrar`.
6. Uma mudança em teste existente: `test_cada_tela_antiga_tem_subpainel_na_secao_certa` ganhou `importantes` na lista do Panorama.
- Falha pré-existente: `test_sdd_painel.ProjetosExternosTests` falha com `python3` puro (sem `pytest` no PATH) e passa com `uv run --with pytest`. **Dono: a definir pelo Humano. Desde 09/11/2026.**

### historia-tomo1-11-11

- Quarentena de `historia/` (linha `historia/*` em `scripts/perimetro/p08_quarentena.sh`): pedido direto do Humano, para que nenhum modelo mude a História sem assinatura. Pela regra antiga, a quarentena cobre comportamento, e texto de canon não é código. Se o Humano não quiser, a linha sai e o diff fica menor.
- Pendência (pedido do coordenador, 11/11): o botão Ouvir lê o texto inteiro de uma vez, com a voz do sistema (`scripts/agata_falar.py`). Pode levar ~10 min, e não há botão Parar. Proposta futura: fala em partes, com Parar.
- Limite R1 (duas propostas abertas por componente): medido em `origin/main` `d782dad0`, com três propostas abertas no painel. Com este pacote, as seis saem da fila.

## Lista de conferência de pronto (R3)

- [x] CI local `TUDO OK` (35 passos), na rodada final.
- [ ] Run verde no GitHub no `headSha` do PR: preenchido depois do push.
- [x] Captura de tela: dois PNG, em 1440 px.
- [x] Sem emoji: testes de emoji dos arquivos novos passam (`test_sem_emoji_na_historia`, `test_sem_emoji_nos_arquivos_da_entrega`).
- [x] `.md` com testes medidos, o que não foi medido e a reversão.
- [ ] Falha pré-existente com dono e data: `test_sdd_painel`, dono a definir pelo Humano (desde 09/11/2026).
- [x] Texto do Tomo I sem alteração, conferido por sha256.
- [x] Texto de MEMÓRIAS sem citação em formato caminho:número.
- [x] Apetite (R2) declarado depois do trabalho, como nas propostas anteriores: até 40 arquivos e 2 h de agente. Medido com `date`: 32 arquivos de código, de 20:03 a 20:21 (relógio, incluindo as esperas do CI local). Dentro do apetite.

## Reversão

- `git apply -R propostas/pacote-11-11.diff` na árvore com o pacote reverte as seis partes juntas, na ordem inversa. Medido: `git apply -R --check` OK na árvore aplicada.
- Os arquivos novos (`historia/`, `historia_painel.py`, `historia.js`, `importantes.py`, `gate_spec_sync.py` e os testes novos) saem com a reversão.
- O drift de `nova_versao` que veio com a spec-primeiro volta ao estado anterior com a reversão.
- Entradas de MEMÓRIAS são append-only: a reversão do registro é entrada nova.
- Reverter só uma parte exige proposta própria, assinada à parte, porque as partes se encadeiam (a 6 usa âncoras da 5, e a 3 depende da 2).

## Movimentos e registro fora do diff

- `propostas/superadas/`: seis pares movidos com `git mv` (`.diff` e `.md`): `chat-lote4-09-11`, `processo-agil-11-11`, `spec-primeiro-11-11`, `voz-compreender-11-11`, `painel-importantes-11-11` e `historia-tomo1-11-11`. Linha "incluída em pacote-11-11" em `propostas/superadas/LEIA-ME.md`.
- `MEMÓRIAS.md`: entrada (993), abaixo do marcador. `ONDE_ESTAMOS.md`: uma linha para o pacote e as seis partes marcadas como incluídas.
- Nenhum desses arquivos está no P-8 (`scripts/perimetro/p08_quarentena.sh` não protege registro).

## Assinatura

Depois do merge deste PR de proposta, o Humano roda:

```
bash scripts/aprovar.sh pacote-11-11 "<motivo>"
```

Verificação depois da assinatura, no checkout vivo, com `git rev-parse HEAD` igual a `origin/main`:

```
bash scripts/p8_verificar.sh pacote-11-11
```
