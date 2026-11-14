# Núcleo de desenvolvimento v2 (Ma'at, Ptah, Thoth) sobre o main de 14/11 (`nucleo-desenvolvimento-v2-14-11`)

Proposta P-8 de `nucleo-desenvolvimento-v2-14-11`. Diff: `propostas/nucleo-desenvolvimento-v2-14-11.diff` (16 arquivos, 1.091 inserções e 14 remoções; sha256 `34588b7f61e3c1f55c590ae4b3d8f017c7e28d9b539f3e086ef4eb9bf8b9ff7f`). Base: `origin/main` `86704396`.

Substitui `nucleo-desenvolvimento-07-11` (do Codex, sobre `619416ed`), que não aplica mais: conflita em 6 arquivos depois da consolidação das skills de 12/11.

## Decisão do Humano (14/11, 19h)

"Refazer v2": manter o `agata-fluxo` consolidado e acrescentar só o que é novo. O teto de 8 KiB da D3 para o guia deixa de valer (o novo teste usa 24 KiB). As decisões D1, D2 e D4 a D10, de 07/11, continuam valendo.

## O que entra

- `.agents/skills/agata-fluxo/SKILL.md` passa de 11.939 para 16.120 bytes. As seções 1 a 5 ficam intactas. Entram:
  - os nomes Ma'at, Ptah e Thoth (D10);
  - o dono (agata-spec) e o revisor (agata-revisor) do guia (D4);
  - um resumo das regras de lote, com os ids de lição e, f, i, l e m;
  - uma seção sobre a Seth;
  - uma seção sobre MEMÓRIAS (D7).

  Também foram corrigidas duas coisas: a frase que dizia que a Seth recebe as skills pela hidratação, e um `git checkout --` na seção de comandos, que restaurava arquivos sem ordem.
- `AGENTS.md`: um ponteiro de 140 bytes para o guia, como parágrafo antes de "Sempre". Não é bullet, porque cada bullet desse bloco é uma regra com porquê obrigatório (`config/porques.json`).
- `.agents/skills/INDICE.md`: a linha do agata-fluxo ganha dono e revisor, e o exemplo de caminho inexistente sai.
- `redesign/router/seth_gateway.py`: a linha `PROCESSO:` vai no estado do turno, só nas faixas internas (D2). `SETH_PROCESSO_HIDRATA=0` desliga a linha, e ela não acumula quando a conversa é hidratada de novo.
- `redesign/nucleo-desenvolvimento/`: spec (acceptance, brainstorm, decision e spec, com a revisão de 14/11 registrada) e seis arquivos de teste.
- CI: no `ci_sdd_local.sh` e no `sdd.yml`, os testes do núcleo, a âncora e o `spec_gate.py check`.

## Testes adaptados (motivo)

- D3: o teto do guia passa de 8 KiB para 24 KiB, por decisão do Humano de 14/11. Um teste novo confere o registro dessa decisão.
- Ponteiro: a constante `_DOUTRINA_FIXA` não existe mais. O teste agora calcula o marcador a partir da seção SETH-GATEWAY e do AGENTS.md, e prova que a linha `PROCESSO:` não está nessas fontes.
- O teste das skills de processo troca `agata-processo-lote`, que não existe mais, por `agata-aplicar-proposta`.

## Medido

- `pytest redesign/nucleo-desenvolvimento/tests`: 23 passaram e 1 foi pulado (o C7 depende de `AGATA_CAMINHOS_RESTRITOS`, que não está configurada).
- `seth_gateway.py --selftest` OK.
- `ci_sdd_local.sh`: TUDO OK.
- `verificar_workflows.py` OK.
- `diff_limpo.py` OK.

## Efeito colateral

O AGENTS.md entra no hash do marcador da Seth. Por isso, as conversas em andamento serão hidratadas de novo uma vez, depois do redeploy.

## Não feito

O núcleo não entrou no loop de drift por critério. As lacunas L1 a L6 da spec continuam abertas.

Reversão: `git revert` do commit de aplicação.
