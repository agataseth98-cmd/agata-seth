# redesign/laya/ — o Laya que escolhe a fila da Seth (MEMÓRIAS (718)/(719))

Decisão do Humano, 15/10/2026: o `laya-multilingual` (Convai Innovations, Apache-2.0), ajustado
para a pergunta do roteador, escolhe a fila da Seth; o Jev (`winnow:e4b`) fica como sombra dele.

| arquivo | o que é |
|---|---|
| `laya_roteador.py` | a pergunta do roteador, a avaliação e o ajuste fino (precisa do venv do Laya) |
| `gerar_sinteticos.py` | gera pedidos sintéticos pt-BR por classe, pelo sanitizador |
| `juiz.py` | 2 juízes de nuvem julgam as divergências Laya × Jev; só vale quando concordam |
| `dados/treino-v2.jsonl` | 1.917 sintéticos (`ministral-14b`, `nemotron-3-super`) |
| `dados/teste-claude.jsonl` | teste A: 80 escritos à mão (Claude Opus 5.5) |
| `dados/teste-gemini.jsonl` | teste B: 125 do `gemini-3.5-flash-lite` |

Fora do repo, em `~/.local/share/agata-laya/`: o venv (Python 3.12, torch 2.14.1 CUDA, `laya`
0.4.8 do PyPI, extra `serve`), o modelo base (`hf/`) e os checkpoints (`modelos/`, com o link
`roteador-atual`). Serviço: `config/laya-roteador.service`. Treino semanal:
`scripts/laya_treino.py` + `config/agata-laya-treino.timer`. Avaliação diária e juiz:
`scripts/avaliar_decisor.py`.

Recriar o venv:

```fish
uv venv -p 3.12 ~/.local/share/agata-laya/.venv
uv pip install -p ~/.local/share/agata-laya/.venv/bin/python "torch==2.14.1" --index-url https://download.pytorch.org/whl/cu130
uv pip install -p ~/.local/share/agata-laya/.venv/bin/python "laya[serve]==0.4.8"
```
