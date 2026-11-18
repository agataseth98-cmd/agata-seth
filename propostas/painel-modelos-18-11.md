# Proposta painel-modelos-18-11 — liberar modelos pelo painel

Decisão do Humano em 18/11/2026: "facilitar o acesso ao cadastro para liberar os modelos para os humanos"; catalogar todos os modelos por capacidade, em standby verificável.

**O quê:** subpainel "Catálogo de modelos" em Sistema.
- `GET /api/modelos` lê o catálogo JSON (`AGATA_CATALOGO_MODELOS`, padrão `~/.local/share/agata/catalogo-modelos/catalogo.json`) e mostra por capacidade, provedor e estado, com o veredito da prova quando houver.
- `POST /api/modelos/decisao`: "liberar para rota" e "voltar ao standby", com confirmação igual ao id. Só acrescenta uma linha em `decisoes.jsonl` (quem, quando, de, para, nota). Leitura, validação e gravação sob a mesma trava (flock). Não altera rotas nem o OmniRoute.
- Recusas: `proibido_pela_regra` e `indisponivel` (409), sem confirmação (400), tipo inválido (400), id fora do catálogo (404), origem alheia (403), corpo > 2 KiB (413).
- Botão "Cadastrar provedor e chave" leva às "Conexões de modelos" que já existem (chave em campo de senha, sem eco).
- JS externo só com `textContent`; CSP sem inline; responsivo (medido em 1440 e 360 px).

**Medido:** 24 testes da página; suíte do painel 753 com 1 falha antiga (`test_sdd_painel`, que falha igual no main limpo); CI local TUDO OK; âncora OK. Revisão Codex: r1 reprovou (2 médios), r2 aprovou.

**Depois de aplicar:** copiar o catálogo para o caminho padrão e reiniciar `painel-operacional.service`.

**Reversão:** `git revert` do commit de aplicação.

**Modelo:** Sonnet 5.5 (implementação) orquestrado pelo Opus 5.5; revisão Codex.
