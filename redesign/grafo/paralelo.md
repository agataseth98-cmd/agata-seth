# P8-02 — paralelo Hermes vs. grafo + OmniRoute

Append-only. Um par por linha da tabela. **Não desliga nada** — o Hermes segue sendo o
caminho de fato; cada pedido real também roda pelo grafo, num clone, e a saída dos dois é
comparada.

## Régua (decidida 2026-09-03, chat 6)

- **N = 7 dias**, com **piso de amostragem** — não fechar antes de o log ter, em pares:
  1. ≥ 1 pedido de cada `--tipo`: `trabalho`, `conselho`, `verificacao`;
  2. ≥ 1 evento de **fallback real** (provedor caiu → combo caiu no próximo) observado;
  3. ≥ 1 caso em que o **portão** devia pausar e pausou;
  4. **zero fabricação** nos dois caminhos (cruza com P8-03) — `citacoes_suspeitas: []` e
     nenhuma alegação de entrada de MEMÓRIAS inexistente.
- Se em 7 dias algum piso não foi exercido, **estende só até cobrir** — não trava em
  calendário. Se algo regride, **para** e volta ao branch (não conta como dia gasto).
- **Critério de aprovação (decisão do Humano no fim):** nenhuma regressão de fidelidade ·
  custo ≤ Hermes · portão e fallback funcionando · zero fabricação.

## Harness

Clone persistente (mesma partição que `~/agata` — `git clone --local` puro falha
cross-device para `/tmp`):

```fish
set CLONE $HOME/.cache/agata/paralelo-clone
rm -rf $CLONE; git clone --local --no-hardlinks $HOME/agata $CLONE
git -C $CLONE switch redesign

# por pedido real ao Hermes, rodar o mesmo pelo grafo:
$HOME/agata/redesign/grafo/.venv/bin/python $HOME/agata/redesign/grafo/grafo.py \
  run "<o mesmo pedido>" --repo $CLONE --thread p802-<n> --tipo <trabalho|conselho|verificacao>
$HOME/agata/redesign/grafo/.venv/bin/python $HOME/agata/redesign/grafo/grafo.py \
  resume --thread p802-<n> --repo $CLONE --recusar     # nunca commitar no clone
```
Anotar por par: `rota`, `trabalhar:<Nch>:<modelo>`, `perimetro_exit`, `citacoes_suspeitas`,
latência sentida, custo (`omniroute cost`), e o resultado do Hermes lado a lado.

## Pares

| # | data | pedido (resumo) | tipo | Hermes (resultado / tempo) | novo: rota / modelo / perímetro / fabricação | observação |
|---|---|---|---|---|---|---|
| seed | 2026-09-03 | "Resuma o que o P-12 verifica" | verificacao | — (seed, sem par Hermes) | `cheap` / `minimax/minimax-m3:free` / `perimetro_exit=0` (10 OK · 1 SKIP · 1 PARCIAL) / `citacoes_suspeitas: []` | harness validado: modelo via `:20127` ✓, `verificar` roda ✓, portão pausa ✓, `--recusar` → nada no clone ✓. `cabecalho_ok=false` esperado (pedido cru, sem `--com-envelope`). 1 SKIP = P-10 (vault não gerado no clone). |
| b1 | 2026-09-03 | sintético: changelog p/ fix do P-12 | trabalho | — (bateria sintética, marcada) | `cheap` / `minimax/minimax-m3:free` / `perimetro_exit=0` / `cit=0` / portão pausou → `--recusar` → clone intacto | ✓ tipo `trabalho` |
| b2 | 2026-09-03 | sintético: manter whisper-small? | conselho | — | `conselho` / `gemini-2.5-flash` (alvo do fallback zai→gemini) / `perimetro_exit=0` / `cit=0` / portão pausou → clone intacto | ✓ tipo `conselho`; combo `conselho` landou no alvo do fallback |
| b3 | 2026-09-03 | sintético: P-8 exige .diff+APROVADO? | verificacao | — | `cheap` / `minimax/minimax-m3:free` / `perimetro_exit=0` / `cit=0` / portão pausou → clone intacto | ✓ tipo `verificacao` |
| b4 | 2026-09-03 | sintético: 3 bullets do cutover | trabalho | — | `cheap` / `minimax/minimax-m3:free` (710ch) / `perimetro_exit=0` / `cit=0` / portão pausou → clone intacto | resposta longa OK, sem divergência |

_(threads `seed-*` e `p802-*` no checkpoint `~/.cache/agata/grafo/checkpoints.sqlite` são
de teste — podem ser ignoradas/limpas.)_


## Piso de amostragem — estado (2026-09-03)

| item | estado |
|---|---|
| ≥1 par por `--tipo` | **coberto** (b1/b4 trabalho, b2 conselho, b3 verificacao) — via bateria sintética, marcada |
| ≥1 fallback real | **parcial** — b2 (combo `conselho`) landou em `gemini-2.5-flash`, alvo do fallback `zai→gemini`; mecanismo já provado na Fase 1/3 (`[deepseek 402 → groq/llamacpp]`). Falta um observado em uso real. |
| ≥1 pausa de portão | **coberto** — todos os 5 pares pausaram no portão; `--recusar` → clone nunca recebeu commit |
| zero fabricação | **coberto até aqui** — `citacoes_suspeitas: []` em todos; nenhuma alegação de entrada inexistente |
| divergência caminho novo vs. esperado | **nenhuma** — rota coerente (`cheap` p/ curto/verificação, `conselho` p/ conselho), `verificar` limpo, nada escrito sem aprovação |

**Ainda aberto:** os **7 dias de calendário** com **pedidos reais** do Humano (a bateria
sintética prova o harness e a ausência de divergência nesses inputs, não substitui a
confiança do uso real). Acumula conforme o Humano usa o sistema.
| par-260903-114438 | 2026-09-03 | Em uma linha: para que serve o agata-drain? | verificacao | _(Hermes: preencher)_ | rota=cheap · trabalhar:ok:408ch:minimax/minimax-m3:free · perímetro=OK · fab=0 citacao · portão=pausou | clone @ 217e62f · run: paralelo-runs/par-260903-114438.txt |
