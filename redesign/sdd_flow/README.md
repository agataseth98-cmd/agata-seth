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
