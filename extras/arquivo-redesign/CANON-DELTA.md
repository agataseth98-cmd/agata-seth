# CANON-DELTA — o que o redesenho muda no canon (insumo da P8-06)

**Não é canon. Não aplica nada.** É o mapa do que `REGRAS.md` / `PROJETO.md` /
`ONDE_ESTAMOS.md` / `MEMÓRIAS.md` precisam refletir quando a Fase 8 fechar. Cada linha
passa pela **Cadeia de auditoria em camadas** + autorização explícita do Humano (P8-06).
Ordem de leitura para o Humano: esta é a lista de decisões que vêm; não é para aplicar.

## PROJETO.md

| seção | hoje diz | passa a dizer |
|---|---|---|
| abertura (l.8–9) | "sobre **Hermes Agent**"; "Agata = Hermes + governança + Conselho" | Agata = **espinha determinística (git + scripts + verificação) + grafo LangGraph + OmniRoute** + governança + Conselho. Hermes é frontend/voz opcional, não o executor. |
| Serviços (l.34) | `hermes-gateway.service` (8642) no loop; `open-webui` + `kokoro-tts` | `agata.target` puxando `omniroute`(:20128)/`omniroute-sanitizer`(:20127)/`openvino-whisper`(:20130)/`openvino-embeddings`(:20134)/`obsidian-ro-proxy`(:27125)/`agata-drain`; `llamacpp-agata`(:20129) sob demanda; `hermes-gateway` só se OWUI/voz em uso |
| Memória e hidratação (l.47–51) | `.hermes.md` único, hook pre-commit, injeção de janela | hidratação do loop = `estado_para_eco.sh` (mecânica) + `query_canon`/`consulta.py` (profundidade sob demanda, índice-primeiro, zero vector DB); `.hermes.md` segue gerado como referência |
| Barreira dura ≥64k (l.29) | "o Hermes exige contexto ≥64k" | não se aplica ao loop novo; nota histórica |
| Segurança / api_server (l.86) | `api_server` na 8642 com `hermes-gateway` | rever quando o gateway sair; o egresso de modelo agora é sempre pelo `:20127` (sanitiza) |
| P-9 (l.38) | monitora `hermes-gateway`, `open-webui`, `kokoro-tts` | monitora os membros do `agata.target`; ajustar a lista (via `.diff` P-8) |
| Conselho Remoto | `conselho_remoto.py` fala com GLM/Gemini direto, com chave | fala pelo `:20127` → OmniRoute combo `conselho`, sem chave (P1-04; `conselho-remoto-omniroute.diff`) |
| Fase 0 do plano antigo (l.157) | "reverificar o patch do 429 após `hermes update`" | some com o Hermes fora do loop; o 429 é do OmniRoute agora |
| Fronteira de recusas | — | somar: RLM como camada de memória (Fase 5, arquivada — injeção venceu); vector DB (rejeitado, `consulta.py` é índice-primeiro) |
| Estado dos bugs/testes | vários itens Hermes | fechar/arquivar os que o cutover torna sem objeto; abrir "cold start Ollama vs. deadline 15s do OmniRoute" (achado P8-04) |

## REGRAS.md

| tópico | mudança |
|---|---|
| **estado de exceção** | **acaba.** Gates de volta: quarentena P-8, Cadeia A→B→C bloqueante, Regra 8, portão das 3 perguntas. Uma entrada de MEMÓRIAS registra o fim. |
| perímetro | P-10 (vault), P-11 (silo), **P-12 (backup verificável)** passam a ser parte do controle padrão — hoje o texto de REGRAS fala em "P-1..P-9" em vários lugares |
| Regra 1 / turno | o loop novo tem contador mecânico (`estado_para_eco.sh` + o eco do P4/Bloco 3.2); ajustar a redação que assume "conta a própria resposta" como único caminho |
| Cadeia de auditoria | inalterada em doutrina; citar que foi ela que aprovou o cutover |
| §4.2 (armadilha do selo `declarado pela interface`) | **item aberto de (309)** — segue precisando de 2ª opinião; decidir junto |

## ONDE_ESTAMOS.md — reescrito

Mapa do sistema pós-redesenho: `agata.target` + portas; `agata-jogo` (liga/desliga p/
jogo); OmniRoute como gateway único de modelo (combos, fallback, sanitização :20127); iGPU
(display+STT+embeddings fora da 4060); MoE local (`:20129`, `--n-cpu-moe 36`, 31 tok/s);
grafo LangGraph (6 nós, portão, durabilidade A); restic no HD + P-12; Goose = fallback
shell. Quem dirige o loop: **grafo + OmniRoute**, não o Hermes.

## MEMÓRIAS.md — uma entrada DIÁRIO por fase (append-only, no topo)

Provável **(310)–(318)**: Fase 0 (rede de segurança), 1 (router), 2 (iGPU), 3 (modelos),
4 (grafo), 5 (spike RLM — arquivado, com números), 6 (Obsidian), 7 (liga/desliga + backup),
8 (cutover + fim do estado de exceção). Cada uma: entrega, aceite cumprido, commit do
branch, `.diff`/`APROVADO-` quando houve. Conferir o topo do remoto antes de numerar.

## Arquivos `scripts/*` que entram em `main` (par P-8)

- `scripts/perimetro.sh` ← `p12-backup-verificavel.diff` + `APROVADO-` ✓ (+ ajuste do P-9 se P8-05 mexer)
- `scripts/cifrar_env.sh` ← `cifrar-env.diff` + `APROVADO-` ✓
- `scripts/conselho_remoto.py` ← `conselho-remoto-omniroute.diff` + `APROVADO-` (aguarda Cadeia B/C — `RELAY-conselho-remoto.md`)
