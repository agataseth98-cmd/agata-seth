# PROJETO.md — Agata (estado corrente)

Este arquivo é o **agora**. É editável e trocável sem mexer nas REGRAS.
Se algo aqui contradisser MEMÓRIAS, MEMÓRIAS ganha: lá está o que aconteceu, aqui está o que vale hoje.
Se algo aqui contradisser a Máquina, a Máquina ganha — e a correção vira entrada nova em MEMÓRIAS.

## O que é
Assistente pessoal do Orusoua, local-first e grátis por padrão, sobre **Hermes Agent** (Nous Research).
Agata = Hermes + governança canônica (REGRAS / PROJETO / MEMÓRIAS) + Conselho Federado de modelos.
Acesso multi-dispositivo por Open WebUI sobre Tailscale, nunca internet pública.

Grafia canônica do nome: **Agata** — sem acento, sem "h". A história migrada usa grafias antigas; não se corrige história.

## Máquinas
- **Predator** (master — CachyOS, fish, i7-13650HX, 40GB RAM, RTX 4060 8GB): Hermes, Ollama, git, Obsidian, web.
- **Orusoua** (réplica Windows 11, leitura/failover) — *planejado*.

## Cérebro
- **Principal:** `gemini-2.5-flash` (Google API, grátis). Teto do free tier ~20 requisições/dia — estourar gera 429.
- **Fallback:** `qwen3-14b-64k` local (Ollama). Contexto 64k por override durável em `custom_providers`; tool-calling **e** raciocínio visível. Adotado exatamente por expor o raciocínio, o que permite pegar fabricação antes da ação em vez de auditar depois.
- **Roteamento por complexidade — aprovado, NÃO implementado** (MEMÓRIAS (64)): o Hermes estima a complexidade antes de escolher cérebro; tarefa simples resolve no qwen local, só escala para o Gemini acima do limite. `lacuna`: limite não definido nem medido. Executor: Claude Code na Máquina, com prova antes/depois.
- **Último recurso manual:** `llama3.1:8b` — sem tool-calling, fora da cadeia.
- **Barreira dura:** o Hermes exige contexto ≥64k (constante de produto, não derivada do payload). Skills 12 ativas / 56 off; tools 12 de 18; payload ~12,6k tokens.
- **Padrão de alucinação** documentado é do antecessor `qwen2.5-14b-64k` (inventava entradas e datas). O qwen3 não tem incidente registrado. A suspensão de MOD é do **papel** "fallback", não da versão — o contador de sessões limpas conta a partir da troca para o qwen3.

## Serviços (boot)
`ollama.service` · Docker `open-webui` + `kokoro-tts` · `hermes-gateway.service` (user unit, linger, porta 8642) · `agata-consolidacao.timer`.
Leftovers pré-Hermes purgados (`agata-rest`, `agata.service`, `agatha.service`) — **não recriar**.

## Memória e hidratação
- Canônicos em `~/agata`. O repositório git é também o cofre Obsidian. Memória nativa do Hermes symlinkada em `~/agata/memoria/` — o arquivo real é o canônico; quem é link é o lado do Hermes.
- **MEMÓRIAS.md** é o terceiro canônico: DIÁRIO coletivo + blocos MOD por modelo + registro do Conselho, tudo append-only num arquivo só.
- **Hidratação real hoje:** `.hermes.md` único, gerado por hook pre-commit, sem filtro por modelo. Injeta REGRAS + PROJETO + fim de MEMÓRIAS.
- **Silos por modelo (Fase 2, ainda NÃO construídos):** o hook passará a gerar `.hermes-<modelo>.md`, cada um com REGRAS + PROJETO + fim de MEMÓRIAS filtrando só o MOD do modelo-alvo. Arquivo único foi rejeitado em auditoria: vaza MOD entre modelos via system prompt. Até lá, silo é disciplina do carteiro, não mecanismo.
- **A janela de injeção é de 30 linhas** do fim de MEMÓRIAS. Entradas longas não chegam inteiras ao contexto — escreva contando com isso.
- RAG só no Open WebUI e só em sessões Gemini — mantido por prudência (janela maior), não pela justificativa antiga de "qwen 32k estoura", que está desatualizada.

## Interface
Hermes CLI/TUI na Máquina. Open WebUI como frontend puro: tools, memória e search nativos desligados — o executor e a memória são únicos, e são do Hermes.
Voz: Kokoro-FastAPI (`pf_dora`, CPU) + Whisper STT. Remoto exige HTTPS via Tailscale.

## Segurança
Serviços em `127.0.0.1`. Sandbox sempre. Segredos só em `~/.hermes/.env`, fora do repo.
**O api_server executa terminal: nunca expor** — nem ele, nem o Open WebUI — fora de Tailscale com dupla autenticação. É a única superfície capaz de dano real.
Ao rotacionar chave, atualize **todos** os consumidores no mesmo passo. Rotação parcial dá 401 silencioso.

## Estado dos bugs e dos testes
- **Gemini 429 ("perdi a conexão"):** causa raiz achada e corrigida. `_summarize_api_error` lia `.text` de uma resposta em streaming não lida, mascarando o 429 como crash de stream e impedindo o fallback de ser acionado. Patch aplicado e verificado por mock do cenário exato.
  **Risco residual, não bug ativo:** o patch vive no `hermes-agent` vendored, fora do repo canônico, sem backup. Um `hermes update` pode descartá-lo em silêncio. **Reverificar após qualquer atualização do Hermes.**
- **`carregar` no fallback:** nenhum bug confirmado com esse nome na história real. Não carregar adiante como fato. Se reaparecer, o protocolo é: curl na 8642 forçando fallback com `carregar`, capturar o system prompt efetivo no Ollama, e testar em ordem — (a) hidratação não injetada, (b) injetada mas truncada, (c) recebida e ignorada.
- **TES-001:** não fechado. Três rodadas executadas com resultado adverso documentado (MEMÓRIAS (66), (69), (73)). Exige sessões genuinamente independentes.
- **TES-002:** **não operante.** O nonce vigente está queimado — repositório público mais hidratação sem filtro tornam o segredo legível por qualquer modelo. Proposta em aberto: gerar novo nonce fora da hidratação, aposentar o antigo por entrada nova, e declarar o teste inativo enquanto não houver silo. Ver MEMÓRIAS (70).
- **Segunda opinião sobre a regra 3X:** pendente desde MEMÓRIAS (68). O executor designado devolveu eco do texto do proponente, não parecer. Encaminhamento recomendado: GLM, auditor ativo desde (44).

## Plano vigente (v1.1 — Fases 0–2 são compromisso; 3+ é bússola)
- **Fase 0 — Saneamento (agora):** publicar no remoto as entradas acumuladas · fechar TES-001 · reverificar o patch do 429 após qualquer `hermes update` · resolver o nonce queimado.
- **Fase 1:** blocos Conselho/MOD em MEMÓRIAS · REGRAS/PROJETO atualizados com segunda opinião ou risco assumido · rascunhos históricos → `docs/`.
- **Fase 2:** hook com silos por modelo · eco pós-carregar · TES-002 restaurado com nonce novo.
- **Fase 3:** GLM membro pleno (MOD-002) · válvula de discordância sintética.
- **Fase 4:** MEMÓRIAS por período (hot/warm/cold) · congelar a ~500 linhas com `git tag` + SHA-256 · `selar.sh --check` · Capivara com consentimento por trecho.
- **Fase 5 (sem prazo):** espelho IPFS, curador nomeado, DAO.

**Curador da sucessão:** `lacuna` — enquanto vago, o Humano operador local. Regras de curador nas REGRAS.

## Estado de publicação
O remoto público (`agataseth98-cmd/agata-seth`) está **em dia** — publicado em `main`, confirmado por `git fetch` sem divergência em nenhum sentido (MEMÓRIAS (85)). Se voltar a ficar atrás por acúmulo de sessões sem Máquina, o executor trabalha com os arquivos entregues pelo Humano, não com o GitHub, e declara a origem, como manda a seção de segunda opinião nas REGRAS.
Repositório **é público** por decisão registrada do Humano. Isso é o que queimou o nonce; não é acidente, é consequência conhecida.

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

## Memória em duas camadas
**Camada local** — Obsidian sobre o próprio repositório git: offline, privada, é **FATO**.
**Camada nuvem** — NotebookLM e afins, pesquisa em andamento: cruzamento de dados, é **RELATO/projeção**. Mão única: lê, nunca escreve fato de volta. Só o não-sensível sobe; segredo, chave e canon nunca.

**bg-review do Hermes Gateway está desligado** (`nudge_interval: 0` em `~/.hermes/config.yaml`, fora do repo). Era um mecanismo que reescrevia sozinho o MEMORY.md nativo — mesmo inode do canônico — e chegou a **apagar identidade e história** para caber num teto de caracteres, sem humano no loop. Consequência aceita: sem auto-captura de fatos; a memória muda só por edição deliberada, por MEMÓRIAS, ou sob comando explícito.

## Riscos conhecidos (limitações, não pendências)
- O Gemini pode deixar de ser grátis. Plano B: pesquisar alternativas gratuitas quando doer.
- Silo é disciplina, não mecanismo, até a Fase 2.
- O patch do handler de 429 vive em repositório vendored sem backup — reverificar após todo `hermes update`.
- Desconfiança permanente tem custo. O overhead é campo opcional em MEMÓRIAS, sem automação; silêncio também é dado.
- Modelo local como classe é limitado neste hardware: o teto é ~14b/9GB. Assunto encerrado sem hardware novo.
- Fricções entre modelos de fornecedores diferentes são característica do período; registram-se quando surgem, não se resolvem por regra.
- **Sucessão do operador Humano é ponto único de falha.** O sistema trata sucessão de modelo com cuidado (Regra 6, silos, MOD), mas não tem plano pra sucessão do operador — só aparece em Fase 5, sem prazo. Se o Humano ficar indisponível, não há segundo operador definido.
- **Exposição do conteúdo do próprio DIÁRIO, não só do nonce.** A avaliação de risco do repositório público (MEMÓRIAS (62)/(70)) cobriu o nonce queimado, nunca o conteúdo do DIÁRIO coletivo em si — que já registra hábitos, hardware e rotina do Humano, e é público por decisão. Vale revisão futura sobre o que mover pra camada privada, sem editar história existente.

## Diagnóstico
`hermes doctor` / `hermes status`. Prontidão da Agata: definida nas REGRAS.
