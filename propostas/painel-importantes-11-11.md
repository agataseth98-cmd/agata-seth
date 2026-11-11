# Painel: Importantes (11/11/2026) — proposta P-8 sobre origin/main `182310d0`

Pedido do Humano em 11/11/2026: "importantes no painel". Uma lista de ideias e pendências que o Humano manda guardar para depois, dentro do painel. Mudança só em `redesign/painel_operacional/`, mais este `.md` e o `.diff`. Sem commit e sem assinatura nesta rodada.

## O que muda

- Aba **Importantes** dentro da seção Panorama (sete seções mantidas) e cartão **"Importantes: N abertos"** no próprio Panorama, com botão que abre a aba.
- Lista na pasta `~/.cache/agata/`, num arquivo `painel-importantes.json` que nasce no primeiro uso. Fora do repositório. Criar, marcar feito, descartar, reabrir e editar. Nada é apagado de fato: descartado fica guardado e pode ser reaberto.
- **Trazer do Conselho**: lê o cache do Conselho (só leitura) e traz as entradas cujo texto começa com `IMPORTANTE`, com origem `cache` e o número da entrada. Sem repetir, nem a entrada já descartada. Texto com segredo não é trazido.
- Escritas exigem origem do painel (`_escrita_permitida`, a mesma regra das conversas). Cada pedido, inclusive o recusado, gera uma linha em `painel-importantes.registro.jsonl`, com hora, rota, id e status, sem texto.
- Arquivos: `importantes.py` (novo, armazém), `server.py` (rotas), `prototipo.html`, `prototipo.js`, `prototipo.css`, `spec/spec.md` (escopo, contrato, mapeamento, critérios, código), `spec/acceptance.json` (10 critérios novos), `README.md`, `test_importantes.py` e `test_importantes_ui.py` (novos), e `test_painel_unificado.py` (uma entrada na lista de subpainéis do Panorama).

## Decisões para o Humano confirmar

1. **Onde ficou.** Como aba dentro de Panorama, e não como oitava seção. Motivo: a spec fixa sete seções. Se preferir outro lugar, a mudança é de HTML e de uma linha no mapeamento.
2. **Rota nova não pedida na lista da tarefa.** `POST /api/importantes/trazer` (corpo `{}`), para o botão "Trazer do Conselho". As outras três rotas são as pedidas.
3. **Convenção `IMPORTANTE`.** A marca é o início do texto da entrada do cache. Não é campo do esquema. Medido agora no cache real: uma linha contém a palavra `IMPORTANTE` e o texto dela começa com a marca. Com um único exemplo, isso não prova a regra. Não medido como convenção de uso.
4. **Origem `modelo`.** Existe no esquema, mas nenhuma rota a grava. Fica para quando houver um modelo que proponha itens.
5. **Texto digitado pelo Humano não passa por filtro de segredo.** Fica local, como as conversas. Só o texto trazido do cache passa por `cache_conselho.filtrar`.
6. **Uma mudança em teste existente.** `test_painel_unificado.py::TelaUnicaTests::test_cada_tela_antiga_tem_subpainel_na_secao_certa` compara a lista exata de subpainéis de cada seção. Acrescentei `importantes` à lista do Panorama, e só isso. O teste continua checando a lista inteira; a mudança é o contrato novo.

## Testes medidos

- `cd redesign/painel_operacional && python3 -m unittest discover -s . -p "test_*.py"` (python3 puro, com `node` do scratchpad no PATH): **375 testes, 1 falha** (`test_sdd_painel.ProjetosExternosTests`, a falha pré-existente descrita abaixo). Antes da mudança: 323 testes, a mesma falha.
- Mesmo comando com `uv run --offline --with pytest python3 -m unittest discover ...`: **375 testes, OK**. Medido agora.
- `test_importantes.py`: 31 testes OK (armazém e rotas: criar, estado, editar, ordem, ilegível, escrita atômica, lista cheia, trazer com filtro real, origem 403, corpo 413, registro sem texto, 500 do cache).
- `test_importantes_ui.py`: 21 testes OK (aba e cartão em node, com DOM mínimo e fetch roteirizado; e checagens de texto: sem innerHTML, style, on*, emoji, cor literal).
- `test_importantes` + `test_importantes_ui` + `test_painel_unificado`: **76 OK**.
- `node --check prototipo.js`: OK.
- `git apply --check -R propostas/painel-importantes-11-11.diff` na árvore com a mudança: OK. O diff reproduz a árvore exatamente.
- `bash scripts/ci_sdd_local.sh` com `uv run --offline --with pytest`, rodada final sobre este estado: `CI LOCAL: TUDO OK`, código de saída 0.
- Captura em Chromium headless 156, servidor na porta 20254, HOME falso com dados fabricados: quatro PNG (cartão no Panorama; aba; aba com filtro Todos; aba em 390 px). Os passos foram os cliques de um usuário: trazer, guardar, marcar feito, filtrar.

## Não medido

- Navegadores além do Chromium headless. O Brave do Humano não foi usado.
- Uso real, com a lista do Humano e o cache real do Conselho. Não rodei "Trazer do Conselho" sobre o cache real.
- Lista perto do limite de 2000 itens; dois usuários ou abas escrevendo ao mesmo tempo.
- Run verde no GitHub: depende de push, que não foi feito nesta rodada.
- Verificação visual pelo Humano: as capturas são minhas, não aceite visual.

## Falha pré-existente

- Teste: arquivo `redesign/painel_operacional/test_sdd_painel.py`, classe `ProjetosExternosTests`, método `test_executar_projeto_roda_o_ciclo_e_recusa_o_que_nao_esta_em_config_sdd`.
- Causa medida: o teste roda o comando `pytest` pelo PATH. Com `python3` puro (sem `pytest` no PATH), falha. Com `uv run --with pytest`, passa (8 testes OK no arquivo, e 375 OK na suíte). O CI local passa porque roda com o `pytest` do `uv`. Esta mudança não toca o SDD.
- **Dono: a definir pelo Humano. Desde: 09/11/2026**, conforme o pedido desta rodada. A proposta `processo-agil-11-11.md`, que está no `main`, diz "conhecida desde a aplicação de 11/11". Não resolvi essa divergência de data.

## Apetite (R2, declarado)

- Arquivos de código: **11** (8 alterados, 3 novos). Mais este `.md` e o `.diff`.
- Horas de agente: medidas com `date`, de 19:20 a 19:42, cerca de 22 min de relógio.
- Apetite declarado: até **12 arquivos** e **2 horas** de agente. Declarado **depois** do trabalho; não foi fixado antes de começar.
- Passou do apetite? **Não.** Medido: 11 arquivos e cerca de 22 min.

## Checklist de pronto (R3)

- [x] CI local `TUDO OK` (rodada final, código de saída 0).
- [ ] Run verde no GitHub no `headSha` do PR: não medido, sem push.
- [x] Captura de tela: quatro PNG (ver "Testes medidos").
- [x] Sem emoji: o teste `test_sem_emoji_nos_arquivos_da_entrega` cobre a tela, o módulo, os testes e o spec; no `.diff`, 0 emoji em 1517 linhas adicionadas.
- [x] `.md` com testes medidos, não medido e reversão.
- [ ] Falha pré-existente com dono e data: data desde 09/11, dono "a definir pelo Humano". Pendente o Humano definir o dono.
- [x] Texto de MEMÓRIAS sem `caminho:número`: não se aplica; esta proposta não acrescenta entrada de MEMÓRIAS.

## Reversão

Aplicar o `.diff` ao contrário (`git apply -R`) numa proposta própria, assinada à parte, porque o componente está no caminho protegido. O arquivo `painel-importantes.json` e o registro, na pasta `~/.cache/agata/`, ficam no disco. Apagá-los perde a lista; isso só se o Humano quiser.

## Registro fora do diff

Nenhum. Esta rodada não acrescenta entrada em MEMÓRIAS nem altera `ONDE_ESTAMOS.md`, porque estão fora da lista da tarefa.

## Assinatura

Depois do merge deste PR de proposta, o Humano roda:

```
bash scripts/aprovar.sh painel-importantes-11-11 "<motivo>"
```

Verificação depois da assinatura, com `git rev-parse HEAD` igual a `origin/main`:

```
bash scripts/p8_verificar.sh painel-importantes-11-11
```
