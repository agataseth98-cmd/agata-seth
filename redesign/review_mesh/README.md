# Review Mesh — fase offline

Prepara pacotes mínimos para revisores independentes e consolida seus relatórios. Não chama modelos, não envia dados e não decide se uma spec está aprovada.

```bash
python3 redesign/review_mesh/mesh.py prepare spec.md reviews/
python3 redesign/review_mesh/mesh.py consolidate reviews/ consolidated.md
```
