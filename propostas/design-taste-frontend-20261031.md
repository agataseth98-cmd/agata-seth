# Decreto: aceitar a skill design-taste-frontend (31/10/2026)

Decisão do Humano em 31/10/2026 (opção 2): aceitar a skill `design-taste-frontend` (tasteskill v2, github.com/Leonxlnx/taste-skill), que estava solta e sem commit em `.agents/skills/`. Entra com 39 arquivos (2,4 MB), nenhum executável, o link em `.claude/skills/` e uma linha no `INDICE.md` das skills. A caixa de ferramentas é reindexada junto (tema `agata` sobe para 12).

Riscos apontados (a decisão é do Humano; nada foi bloqueado):
- `scripts/*.mjs` abrem um Chrome/Chromium headless (`lib/cdp.mjs`, `spawn`) e apagam o diretório temporário que criam.
- `assets.mjs` acessa a rede (coleções abertas de imagens, `--get` baixa arquivos); `library/photos.json` aponta para picsum.photos. Sem rede, a skill manda desenhar as imagens.
- `draw.mjs` e `lib/app-draw.mjs` gravam o histórico em `~/.taste-skill/history.json`, fora da pasta do sistema. Para manter tudo dentro do repositório, defina `TASTE_SKILL_HISTORY` apontando para um caminho do repositório ao usar.
- O pacote não traz arquivo de licença próprio (só cita as das imagens). Verificar a licença na fonte antes de redistribuir.
- Não tem hooks nem instalador; os scripts só rodam se alguém os chamar.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh design-taste-frontend-20261031 "aprovo: skill design-taste-frontend"`.
