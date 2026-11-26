# Spec: ferramentas-unificadas-26-11

Contrato. Decisões: [D1]–[D6] (coordenador, a partir de H1–H4), [A1]–[A4] (ajustes do especificador), [C1]–[C2] (conflitos). Tudo em decision.md. Nada implementado. Critérios em acceptance.json.

## 1. Jornadas
- J1 Instalar: `instalar.py mcp <nome> --params k=v` grava o overlay e roda o sync; `listar.py` mostra nas três CLIs. Sem o "sim" do Humano, nada é gravado [C1].
- J2 Repetir: sync sem mudança não altera arquivo nativo.
- J3 Primeira sessão: SessionStart lê `agata-arranque` [H2, C2].
- J4 Promover: `promover.py` gera `propostas/<nome>.diff`; o Humano assina.
- J5 Reverter: seção 6.

## 2. Contrato
- Fonte única (P-8): `config/ferramentas/{mcp,skills,agentes}.yml`. Hooks e comandos: lote 2 [D3]. YAML, pois `yaml` importa aqui (medido).
- Overlay: `~/agata-local/ferramentas.yml`, mesmo schema; sobrepõe por nome [D1].
- MCP: `nome`, `transporte` (stdio ou http), `comando` e `args` ou `url`, `env` só como nomes (`${VAR}`), `clis`. Valor de segredo nunca entra no yml.
- Skill: `nome`, `origem` (em `.agents/skills/`), `clis`. Agente: `nome`, `origem`, `clis`, `adotar` (padrão false).
- Comandos (Python, stdlib e PyYAML):
  - `instalar.py <tipo> <nome> [--params k=v]`, tipo `mcp|skill|agente`. Grava o overlay e chama o sync. Código 2 se o schema falha; 3 sem confirmação do Humano.
  - `sincronizar.py [--dry-run] [--cli C]`: canônico ∪ overlay vira MCP por comando nativo, skill por ponteiro, agente por arquivo. Código 2 se uma config nativa não lê; nada é escrito.
  - `listar.py [--tipo T] [--cli C]`: só leitura; nome, tipo, CLI, origem, estado; sem valores.
  - `promover.py <nome>`: gera o diff; não aplica.
  - `reverter.py <ts> | --listar | --dry-run`: seção 6.
- Nativos (escrita medida na ajuda; efeito não medido):
  - Claude Code: `~/.claude.json` por `claude mcp add -s user`. Skill: ponteiro `~/.claude/skills/agata-arranque` para `~/agata/.agents/skills/agata-arranque` (checkout principal, não a worktree).
  - Codex: `~/.codex/config.toml` por `codex mcp add`. Skill em `~/.codex/skills/agata-arranque`; formato não medido.
  - OpenCode: `~/.config/opencode/opencode.jsonc` por `opencode mcp add` (sem prompt: não medido). Skill: L2. Agentes: `.opencode/agent/*.md`, formato medido.
- Manifest [A2]: `~/.local/share/agata/ferramentas/gerenciado.json`, com CLI, tipo, nome, hash pós-sync e caminho do backup. Sem valores.
- Memória comum [H4]: o cache continua em `redesign/router/cache_conselho.py`; a skill aponta para o comando.

## 3. Critérios
`acceptance.json`: AC-01 a AC-15, cada um com o nome do teste que o prova. Lacunas L1–L6, sem teste, marcadas.

## 4. Desenho e alternativas
Menor mecanismo: MCP pelos comandos nativos das três CLIs, que já escrevem e removem entradas [A1]. Skill por ponteiro para `.agents/skills/`; nada copiado [H4]. Subagentes: gerador só para OpenCode, formato medido [D3]; Claude e Codex: L4.

Escolhas:
- Overlay mais canônico [D1]: instalar não vira proposta; o canônico recebe só o que `promover.py` gera.
- Merge pelo manifest [D5, A2]: o sync mexe só nos nomes que declara ou que estão no manifest.
- Adoção [D5]: mesmo nome fora do manifest não é adotado sem `adotar: true`. Medido: `github-pat` está nos nativos de Claude e Codex e em nenhuma fonte; fica intacto.
- Config inválida [D5]: aborta antes da primeira escrita.

Descartadas:
- JSON, TOML ou JSONC à mão: `tomllib` só lê (medido); um dump perde os comentários do `opencode.jsonc`; `~/.claude.json` muda na sessão. Substituída por [A1].
- Restaurar o backup inteiro (D6 literal): desfaz o que a CLI gravou depois do sync. Substituída por [A3].
- Tudo no canônico, sem overlay: cada ferramenta nova virava proposta assinada, contra [H3] e [D1].
- Cópia da skill em cada CLI: as cópias divergem; [H4] pede fonte única.

Skill `agata-arranque` [D4], conteúdo:
- Cabeçalho da Regra 1 com hora medida por `date`; link a `PROTOCOLOS.md`.
- Voz `pt_BR-agata-last` (piper-tts local), por `scripts/agata_falar.py`; nenhum modelo usa outra voz.
- Memória: `cache_conselho.py ler --n 20` ao começar; `anotar` com `--tipo`.
- Skills: `.agents/skills/INDICE.md`; entrada `agata-fluxo`.
- P-8: worktree em `.claude/worktrees/<nome>` a partir de origin/main; `.diff` e registro; `scripts/ci_sdd_local.sh`; só o Humano assina.
- `agata-mapear-humano` ao começar; link a `AGENTS.md`.
- Problemas recorrentes (de `agata-fluxo`, seção 1): cabeçalho sem hora medida; narrar o processo; ação externa sem aviso; mexer em pasta alheia; leitura declarada de forma vaga; citação inventada; sudo, `aprovar.sh` ou segredo; afirmar sem medir.

## 5. Implementação e testes
Tocados (tudo por diff P-8):
- `config/ferramentas/{mcp,skills,agentes}.yml` (novos).
- `scripts/ferramentas/{instalar,sincronizar,listar,promover,reverter,schema}.py` e `test_ferramentas.py` (novos).
- `.agents/skills/agata-arranque/SKILL.md` (novo); uma linha em `.agents/skills/INDICE.md`.
- `AGENTS.md` e `CLAUDE.md`: só a citação da skill.
- `propostas/ferramentas-unificadas-26-11.diff` e o registro.

Fora do repo: `~/agata-local/ferramentas.yml`, `~/.local/share/agata/ferramentas/` e os nativos da seção 2.
Fora de escopo: `REGRAS.md`, `PROTOCOLOS.md`, `MEMÓRIAS.md`, `PROJETO.md` (outro lote).
Testes: unittest com HOME temporário; não tocam o ambiente real.

## 6. Migração e reversão
Migração (primeira rodada): dry-run, sem remover entrada não gerenciada; backup 600 em `~/.local/share/agata/ferramentas/backup/<ts>/` [A4]; escrita nativa e manifest com hash; `listar.py` confirma `github-pat` intacto.

Reversão, passo a passo:
1. `reverter.py --listar`; depois `reverter.py <ts> --dry-run`.
2. Claude e Codex: `claude mcp remove <nome>` e `codex mcp remove <nome>` para as entradas do manifest. Entrada ausente é registrada, sem falhar.
3. OpenCode (sem `remove` medido): se o hash do `opencode.jsonc` bate com o do manifest, restaura do backup; senão, para e pede ao Humano [A3].
4. Ponteiros de skill e overlay: `mv` para `~/agata-arquivo/ferramentas-<ts>/`. Nunca `rm` [agata-fluxo, seção 0].
5. `listar.py` confere que só ficou o que existia antes.

Não quebra o que funciona: nada sai sem estar no manifest; nada volta se a CLI mudou o arquivo depois do sync.

## 7. Riscos
- C1 e C2: decisão antes da implementação.
- R1 corrida com CLI aberta (L5): sync usa comando nativo e confere hash.
- R2 segredo: `github-pat` tem valores que esta análise não leu. Backup 600, fora do repo; `listar.py` só mostra nomes.
- R3 OpenCode: `remove` não medido; JSONC com comentários (L6).
- R4 Gemini CLI: lote 2 [D2].
- R5 Subagentes Claude e Codex: pastas ausentes; formato não medido (L4).
- Dependências: um diff P-8 por parte; `scripts/ci_sdd_local.sh`; PyYAML (medido). Nenhuma dependência nova.
