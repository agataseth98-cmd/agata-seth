# Decreto: aceitar a skill design-taste-frontend, versão 2 sem o link (31/10/2026)

Substitui `design-taste-frontend-20261031` (assinado, mas não aplicável). Motivo, medido: o hook P-8 do pre-commit não consegue verificar um symlink novo (`git hash-object` segue o link e não bate com o blob staged), então o commit do diff anterior foi bloqueado por `perimetro.sh`. Não contornei o hook. O par assinado antigo fica sem uso em `propostas/`.

Diferença: esta versão **não** inclui `.claude/skills/design-taste-frontend`. O link continua existindo só localmente (já criado nesta máquina); em outro clone, o comando está no `INDICE.md` das skills. O resto é igual: 39 arquivos da skill em `.agents/skills/design-taste-frontend/`, uma linha no `INDICE.md` das skills e a reindexação da caixa de ferramentas (413 peças, tema `agata` com 12).

Riscos apontados (a decisão é do Humano; nada foi bloqueado):
- `scripts/*.mjs` abrem um Chrome/Chromium headless (`lib/cdp.mjs`, `spawn`) e apagam o diretório temporário que criam.
- `assets.mjs` acessa a rede (`--get` baixa arquivos); `library/photos.json` aponta para picsum.photos.
- `draw.mjs` e `lib/app-draw.mjs` gravam o histórico em `~/.taste-skill/history.json`, fora da pasta do sistema; use `TASTE_SKILL_HISTORY` apontando para um caminho do repositório.
- O pacote não traz licença própria; conferir na fonte antes de redistribuir.
- Sem hooks nem instalador.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh design-taste-frontend-v2-20261031 "aprovo: skill design-taste-frontend sem link"`.
