# PROJETO.md — Ágata (implementação atual)

Estado de hoje. Trocável sem mexer nas REGRAS.

## O que é
Assistente pessoal do Orusoua, local-first e grátis por padrão, sobre **Hermes Agent** (Nous Research). Ágata = Hermes + governança canônica (REGRAS/PROJETO/MEMÓRIAS) + Conselho Federado de modelos. Acesso multi-dispositivo via Open WebUI sobre Tailscale, nunca internet pública.

## Máquinas
- **Predator** (master — CachyOS, fish, i7-13650HX, 40GB, RTX 4060 8GB): Hermes, Ollama, git, Obsidian, web.
- **Orusoua** (réplica Windows 11, leitura/failover) — *planejado*.

## Cérebro
- Principal: **gemini-2.5-flash** (Google API, grátis). Bug de 429 mascarado como "conexão perdida": causa raiz achada e patchada — ver "Estado real dos bugs" abaixo (risco residual, não bug aberto).
- Fallback: **qwen3-14b-64k** local (Ollama; contexto 64k via `custom_providers`, durável; tool-calling + thinking; adotado por expor raciocínio, mitigando o risco abaixo). Padrão de alucinação como primário (inventa entradas/datas) é documentado do antecessor **qwen2.5-14b-64k** (fallback até a troca); qwen3 não tem incidente registrado até aqui. Suspensão de MOD é do papel "fallback", não da versão — contador de 20 sessões limpas conta a partir da troca pra qwen3, não do zero histórico do 2.5.
- Último recurso manual: llama3.1:8b (sem tool-calling, fora da cadeia).
- Hermes exige contexto ≥64k. Skills 12 ativas/56 off; tools 12/18 (~12.6k tokens de payload).

## Serviços (boot)
`ollama.service` · Docker `open-webui`+`kokoro-tts` · `hermes-gateway.service` (user, linger, porta 8642) · `agata-consolidacao.timer`. Leftovers pré-Hermes purgados — não recriar.

## Memória e hidratação
- Canônicos em `~/agata` (repo git = cofre Obsidian). Memória nativa do Hermes symlinkada em `~/agata/memoria/`.
- **MEMÓRIAS.md** é o terceiro canônico: DIÁRIO coletivo + blocos MOD por modelo + registro do Conselho, tudo append-only num arquivo só.
- Hidratação por **silos** (Fase 2, ainda NÃO construída): hook pre-commit vai gerar `.hermes-gemini.md` e `.hermes-qwen.md` — cada um com REGRAS + PROJETO + fim de MEMÓRIAS **filtrando só o MOD do modelo-alvo**. Arquivo único foi rejeitado em auditoria: vazaria MOD entre modelos via system prompt. Hoje a hidratação real é `.hermes.md` único, sem filtro — até a Fase 2 existir, o silo é disciplina do carteiro, não mecanismo (ver REGRAS).
- RAG só no Open WebUI e só em sessões Gemini — regra mantida por prudência (janela do Gemini é maior), mas a justificativa antiga ("qwen 32k estoura") está desatualizada: fallback é qwen3-14b-64k com override durável a 64k (ver Cérebro), não 32k nativo.

## Interface
Hermes CLI/TUI na Máquina; Open WebUI como frontend puro (tools/memória/search nativos desligados — executor único é o Hermes). Voz: Kokoro-FastAPI (`pf_dora`, CPU) + Whisper STT; remoto exige HTTPS via Tailscale.

## Segurança
Serviços em `127.0.0.1`; sandbox sempre; segredos só em `~/.hermes/.env`. **O api_server executa terminal: nunca expor** (nem Open WebUI) fora de Tailscale + dupla auth. Única superfície capaz de dano real.

## Plano vigente (v1.1, ratificado — Fases 0–2 são compromisso; 3+ é bússola)
- **Fase 0 — Saneamento (agora):** ratificar em MEMÓRIAS · revisar diff dos 3 commits → push · TES-001 · reverificar patch do 429 após qualquer `hermes update` (risco residual, não bug ativo).
- **Fase 1 (sem. 3–6):** blocos Conselho/MOD em MEMÓRIAS · REGRAS/PROJETO atualizados (segunda opinião GLM ou risco assumido) · rascunhos históricos → `docs/`.
- **Fase 2 (sem. 6–10):** hook com silos por modelo · eco pós-carregar · TES-002 com nonce.
- **Fase 3 (sem. 10–16):** GLM membro pleno (MOD-002) · válvula de discordância sintética.
- **Fase 4 (meses 4–12):** MEMÓRIAS por período (hot/warm/cold: corrente sem compressão; 5–40 anos delta; >40 zstd+índice) · congelar a ~500 linhas → `git tag` + SHA-256 · `selar.sh --check` · Capivara com consentimento por trecho.
- **Fase 5 (sem prazo):** IPFS espelho, curador nomeado, DAO.

**Curador da sucessão:** `lacuna` — enquanto vago, Humano operador local (regras de curador nas REGRAS).

## Estado real dos bugs (corrigido nesta sessão, contra a Máquina — MEMÓRIAS (55))
- **Gemini 429 ("perdi a conexão"):** causa raiz achada e patchada. `_summarize_api_error` lia `.text` de uma resposta em streaming não lida, mascarando o 429 como crash de stream. Patch (try/`.read()`/except) aplicado e verificado (mock do cenário exato, sem crash). **Risco residual, não bug:** o patch vive no `hermes-agent` vendored (fora do repo canônico), sem backup — um `hermes update` pode sobrescrever em silêncio. Reverificar após qualquer atualização do Hermes.
  `lacuna` aberta pro Humano: uma entrada posterior no histórico ainda lista "Gemini 400/429 não reproduzido" como aberto, depois do patch verificado — inconsistência não resolvida sozinho (ver MEMÓRIAS (55) pra decidir se é bookkeeping desatualizado ou uma falha distinta).
- **`carregar` no fallback:** nenhum bug confirmado por esse nome na história real. Não carregar adiante como fato — se reaparecer, protocolo: curl na 8642 forçando fallback com `carregar`, capturar system prompt efetivo no Ollama, testar em ordem (a) hidratação não injetada, (b) injetada mas truncada, (c) recebida e ignorada.
- **TES-001 (bateria de 3 relatos independentes):** confirmado ainda não rodado limpo. Fase 0 segue com este item pendente.

## Ferramenta embutida: selar.sh (Fase 4; salvar em `scripts/selar.sh`)
Testado: sela, verifica (exit 0) e detecta adulteração (exit 1).
```bash
#!/usr/bin/env bash
# Rodar da RAIZ do repo. Uso: bash scripts/selar.sh <arquivo> | --check
set -euo pipefail
SELOS="SELOS.txt"
if [ "${1:-}" = "--check" ]; then
    [ -f "$SELOS" ] || { echo "sem selos registrados ($SELOS ausente)"; exit 1; }
    falha=0
    while read -r hash arquivo data; do
        [ -z "$hash" ] && continue
        atual=$(sha256sum "$arquivo" 2>/dev/null | cut -d' ' -f1 || echo "ARQUIVO_AUSENTE")
        if [ "$atual" = "$hash" ]; then echo "OK      $arquivo (selado em $data)"
        else echo "VIOLADO $arquivo — selo $hash != atual $atual"; falha=1; fi
    done < "$SELOS"
    exit $falha
fi
[ -n "${1:-}" ] || { echo "uso: selar.sh <arquivo> | --check"; exit 1; }
[ -f "$1" ] || { echo "arquivo não existe: $1"; exit 1; }
hash=$(sha256sum "$1" | cut -d' ' -f1); data=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "$hash $1 $data" >> "$SELOS"
echo "selado: $1"; echo "sha256: $hash"
echo "registrado em $SELOS — commite e tag: git tag ${1%.md}-final"
```

## Memória em duas camadas (revelado na migração, MEMÓRIAS histórico)
Camada local (Obsidian sobre o próprio repo git, iniciado): offline, privada, é FATO. Camada nuvem (NotebookLM, pesquisa em andamento): cruzamento de dados, é RELATO/projeção — mão única, nunca escreve fato de volta. Só não-sensível vai pra nuvem; segredo/chave/canon nunca.
**bg-review do Hermes Gateway está desligado** (`nudge_interval: 0` em `~/.hermes/config.yaml`, fora do repo): mecanismo que reescrevia MEMORY.md nativo sozinho (mesmo inode do canônico) chegou a apagar história pra caber num teto de caracteres. Consequência aceita: sem auto-captura de fatos; memória muda só por edição deliberada + MEMÓRIAS, ou sob comando explícito.

## Riscos conhecidos (limitações, não pendências)
Gemini pode deixar de ser grátis (plano B: pesquisar DeepSeek/GLM/Grok grátis quando doer) · silo é disciplina até Fase 2 · fricções de modelos corporados são característica de 2026, registradas quando surgirem · distrust permanente tem custo — overhead é campo opcional em MEMÓRIAS, sem automação; silêncio também é dado · patch do handler de 429 vive em repo vendored sem backup — `hermes update` pode descartá-lo em silêncio, reverificar sempre após atualizar o Hermes.

## Diagnóstico
`hermes doctor` / `hermes status`. Prontidão da Ágata: definida nas REGRAS.
