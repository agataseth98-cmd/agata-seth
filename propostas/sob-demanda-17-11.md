# Laya e Jev sob demanda: sobem na primeira chamada e caem após 15 min ociosos (`sob-demanda-17-11`)

Classe: Comportamento (runtime: unidades systemd, perímetro e testes).

Proposta P-8 de `sob-demanda-17-11`. Diff: `propostas/sob-demanda-17-11.diff` (14 arquivos). Base: `origin/main` (c296f8ca). O diff não traz registro nem `ONDE_ESTAMOS.md`. `ESTADO.md` é regenerado pelo pre-commit na aplicação.

Decisão do Humano (17/11/2026, 18:28): "tudo no sistema deve ser subido de acordo com a necessidade e derrubado após um tempo seguro pré determinado".

## O que muda

1. `config/laya-roteador.socket` e `config/ollaya.socket` (novos): escutam as portas públicas 11436 e 11435, ligados pelo `agata.target` (nada no boot, decisão de 29/10).
2. `config/laya-roteador-proxy.service` e `config/ollaya-proxy.service` (novos): `systemd-socket-proxyd --exit-idle-time=15min` para as portas internas 11446 e 11445.
3. `config/laya-roteador.service` e `config/ollaya.service`: porta interna, `StopWhenUnneeded=yes`, sem `[Install]`, `ExecStartPost` com espera de prontidão de até 60 s (`timeout 60`), `TimeoutStartSec=90`; no Ollaya, `ExecStopPost` idempotente que para o contêiner.
4. Perímetro: `config/portas-agata.txt` ganha as portas internas; `config/servicos-agata.txt` declara socket (p9=sim) e proxy/backend (p9=nao) e corrige a origem do Laya; `scripts/perimetro/p09_servicos_declarados.sh` passa a avisar socket inativo com o sistema ligado e unidade p9=nao em `failed` (parada em repouso não avisa); `scripts/gerar_estado.py` ajusta a frase do P-9.
5. `scripts/avaliar_decisor.py`: o `disable --now` inclui sockets e proxies.
6. Testes: `scripts/testar_sob_demanda.py` (novo, 14 testes) e `scripts/testar_cobertura_servicos.py` (22 casos); passo novo no `scripts/ci_sdd_local.sh`.

## Medido (17/11/2026)

- CI local (pytest 9.2.0): `CI LOCAL: TUDO OK`, com o passo "sob demanda". Log: `/home/orusoua/agata-arquivo/roteador-capacidade-17-11/ci-sob-demanda.log` (rodada anterior às correções; o executor relatou TUDO OK depois delas, 89 OK).
- `testar_sob_demanda.py`: 14 OK. `testar_cobertura_servicos.py`: 22/22. `systemd-analyze verify` nas unidades (em cópia): sem saída, exit 0 (relato do executor).
- Cópia limpa a partir de `origin/main` (c296f8ca): `git apply --check` APLICA; testes OK na cópia (conferido pelo orquestrador).
- Revisão independente do Codex: "aprovar com correções" (4 achados: links antigos no target, P-9 sem `failed`, limpeza do contêiner, prazo); as 4 entraram. Texto: `/home/orusoua/agata-arquivo/roteador-capacidade-17-11/codex-review-l7.txt`.

## Não medido

- Tempo real de subida do Laya e do Ollaya contra o prazo de 60 s; parada efetiva após 15 min; comportamento com conexão persistente (impede a parada, por desenho do proxy).
- A 1ª chamada após ociosidade: o gateway espera o Laya 1,5 s e cai na heurística (fail-soft); o Jev em sombra não afeta a rota.

## Instalação na Máquina (depois da aplicação; ordem importa)

```
mkdir -p ~/agata-arquivo/sob-demanda-17-11 && cp -L ~/.config/systemd/user/laya-roteador.service ~/.config/systemd/user/ollaya.service ~/agata-arquivo/sob-demanda-17-11/
systemctl --user stop laya-roteador.service ollaya.service
systemctl --user disable laya-roteador.service ollaya.service   # com o arquivo antigo, que ainda tem [Install]
cd ~/agata && git pull
for u in laya-roteador.socket laya-roteador-proxy.service ollaya.socket ollaya-proxy.service; do ln -sfn ~/agata/config/$u ~/.config/systemd/user/$u; done
systemctl --user daemon-reload && systemctl --user enable --now laya-roteador.socket ollaya.socket
```

## Reversão

`systemctl --user disable --now laya-roteador.socket ollaya.socket`, parar proxies e backends, `git apply -R` do diff por proposta, `unlink` dos 4 links novos, `daemon-reload`, `enable --now laya-roteador.service ollaya.service`.

## Comando de assinatura

Depois do merge deste PR, no terminal, sem `!`:

bash scripts/aprovar.sh sob-demanda-17-11

## Modelos

Claude Opus 5.5 orquestrou e conferiu; agente agata-dev (Claude Haiku 5.5) implementou; Codex revisou.
