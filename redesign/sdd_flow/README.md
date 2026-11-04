# SDD Flow

Coordenador determinístico do ciclo Elephant–Goldfish SDD. Ele encadeia as
etapas mecânicas já existentes e grava estado append-only em JSON. Não inventa
decisão humana, não assina P-8 e não aplica mudanças protegidas.

```bash
python3 redesign/sdd_flow/runner.py work/state.json bootstrap projeto/ work/kit --goal 'objetivo'
python3 redesign/sdd_flow/runner.py work/state.json review work/kit
python3 redesign/sdd_flow/runner.py work/state.json consolidate work/kit
python3 redesign/sdd_flow/runner.py work/state.json decision --accepted
python3 redesign/sdd_flow/runner.py work/state.json implementation /path/to/worktree
python3 redesign/sdd_flow/runner.py work/state.json verify redesign/sdd_flow/tests --pytest-bin /path/to/pytest
python3 redesign/sdd_flow/runner.py work/state.json drift projeto/ work/kit/provenance.json work/drift.md
python3 redesign/sdd_flow/runner.py work/state.json complete
python3 redesign/sdd_flow/runner.py work/state.json status
```

## Ciclo único e âncora

```bash
python3 redesign/sdd_flow/runner.py work/state.json cycle redesign/sdd_flow/spec redesign/sdd_flow/spec/acceptance.json --scope redesign/sdd_flow
python3 redesign/sdd_flow/anchor.py . redesign/sdd_flow
```

`cycle` roda gates de spec, âncora, critérios de aceite e drift por critério, e para no primeiro que falha. `anchor.py` ancora componente existente: a spec (`spec/spec.md` ou `SPEC.md`) lista o código que possui; arquivo-fonte sem dono ou citação de arquivo inexistente falha. O job `sdd` da CI repete isso.

## Projeto SDD declarativo (qualquer projeto, sem escrever nele)

Um descritor JSON diz onde está o projeto e o que conferir; o ciclo roda contra a raiz dele e grava **fora** (padrão `~/.cache/agata/sdd/<nome>/`):

```bash
python3 redesign/sdd_flow/runner.py work/state.json project redesign/sdd_flow/exemplo-projeto.json
```

Passos: gates da spec, âncora (contra a raiz do projeto), critérios de aceite (`pytest` com alvos relativos, no ambiente do descritor), drift por critério e drift de arquivos contra a execução anterior. Cada execução vira uma pasta com `relatorio.md`, `evidence.json` e os drifts, e um evento `pass` ou `fail` no `ledger.jsonl` (encadeado por hash; `python3 redesign/evidence_ledger/ledger.py verify`). Falha também é evidência. Para aparecer na aba SDD do painel, o descritor vai em `config/sdd/<nome>.json` por proposta P-8.

## Proposta e handoff

```bash
python3 redesign/sdd_flow/runner.py work/state.json proposal <nome> /caminho/worktree propostas/<nome>.diff --test redesign/sdd_flow/tests
python3 redesign/sdd_flow/github_flow.py . <nome> --state work/state.json --create
```

`proposal` gera o `.diff` único contra a base, aplica num checkout limpo, confere espaços e roda os testes; só então grava o arquivo. `github_flow.py` recusa o handoff sem `--state` de um ciclo que passou por `cycle`.

## Uma assinatura por implementação

Cada implementação coerente é uma proposta, com uma assinatura P-8 e uma aplicação. Brainstorm, spec, código, testes e CI vão juntos no mesmo `.diff`; não se abrem propostas pequenas em série.
