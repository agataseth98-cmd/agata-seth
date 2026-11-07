# Proposta: troca Goose por OpenCode como agente de terminal

**Nome para assinatura:** `agente-opencode-07-11`
**Decisão do Humano (07/11/2026):** "a goose sai e o open code entra, integrado de forma primeira palavra ao sistema".
**Base:** `origin/main` = `83334fde`. Diff: `propostas/agente-opencode-07-11.diff` (230 linhas).
**sha256 do .diff:** `a37db9d089892350c75a4130655c298a3016b0dae00e48cf209337e00abc55d2`

## O que o diff faz
- **Atalho `seth-agente`** (`redesign/systemd/seth-agente`): o terminal passa a abrir o OpenCode dentro de `~/agata`, em vez de `goose session`. Se `opencode` não está no PATH, usa `~/.opencode/bin/opencode`, onde o binário já existe nesta máquina. Se nenhum dos dois existe, o script para com aviso e não abre terminal.
- **Equipe** (`scripts/equipe/equipe.py`): o membro `opencode` aparece com o nome "OpenCode" no canal; `goose` sai da tabela de nomes. O teste 26 do selftest passa a usar `opencode`.
- **Equipe** (`scripts/equipe/inicio.sh`) e **P-8** (`scripts/p8_verificar.sh`): só comentários trocados.
- **CI** (`.github/workflows/perimetro.yml`): uma linha no bloco "Contratos de memória e escriba", que roda `python3 -I scripts/testar_sem_goose_ativo.py`. Autorizado pelo orquestrador em nome do Humano, no mesmo diff.
- **Teste novo** (`scripts/testar_sem_goose_ativo.py`, 6 casos): varre os arquivos rastreados de código e atalhos (`scripts/`, `redesign/`, `config/`, `redesign/systemd/`) e reprova qualquer referência à palavra goose que não esteja nas 8 exceções listadas no próprio teste. Cada exceção tem contagem exata e motivo. Ele também confere o atalho e o NOMES da equipe.

## O que fica de propósito (exceções do teste)
| Arquivo | Linhas | Por quê |
|---|---|---|
| `scripts/perimetro/p08_quarentena.sh` | 7 | Perímetro protege `redesign/goose/*` enquanto o diretório existe. Comentários são histórico. |
| `redesign/router/seth_gateway.py` | 16 | Detector do payload do Goose (chamada de título). Trocar exige medir antes o payload do OpenCode. P-16 control. |
| `redesign/router/auditoria_turno.py` | 2 | Docstring com a medição do Goose (MEMÓRIAS 662 e 664). |
| `scripts/estado_para_eco.sh` | 1 | Comentário histórico do incidente de write do Goose (MEMÓRIAS 516 e 517). |
| `redesign/mcp/servidor.py` | 1 | Lista de executores do MCP. OpenCode não medido contra o servidor. |
| `config/portas-de-entrada.txt` | 3 | Rotas para `redesign/goose/AGENTS.md`, que fica até a decisão de remoção. |
| `config/agata-identidade.json` | 1 | Proveniência histórica da paleta. |
| `redesign/painel_operacional/prototipo.html` | 1 | Palavra de busca do cartão. O painel tem spec e âncora próprios, fora desta proposta. |

**Decisão sobre `redesign/goose/`:** não mexi no diretório. Ele tem config do Goose (`permission.yaml`, `canon-extension.yaml`, `README.md`) e o `AGENTS.md` com doutrina escrita para o cliente Goose. Não há uso de outra função medido. Ele sai só quando o Humano decidir a remoção dos dados, em proposta própria.

## Arquivos tocados (sha256 do conteúdo final)
| Arquivo | Tipo | sha256 |
|---|---|---|
| `redesign/systemd/seth-agente` | atalho | `42e7e129058638e742dbbb6d37a83b65aa0fb060045bef9178ad2fbb0181554e` |
| `scripts/equipe/equipe.py` | código | `960969d241914f746184b3cf40f4d371cfa22e188db63e8a8a5e6c867f3e4962` |
| `scripts/equipe/inicio.sh` | código (comentário) | `72a9f007ba4ce588ef04abf0a46a61151177a2b2096285cc069f07037b0b78d2` |
| `scripts/p8_verificar.sh` | código (comentário) | `7e21b90b22d04bc3814543cbfaf2aa2a1d2c40fdbc43366c83d4e1fd29a94d08` |
| `.github/workflows/perimetro.yml` | CI (uma linha) | `4c308afb1a2893873f3b1bd0b3c3bbaaf411998252a14e474ecc9c5ae886c430` |
| `scripts/testar_sem_goose_ativo.py` | teste novo | `b5bef5016af76a7463edbf9f4fc8427919be66bd3b1eb522429b69ecb8582d5b` |

## Verificação feita
- `python3 -I scripts/testar_sem_goose_ativo.py -v`: 6 testes OK.
- `yaml.safe_load` do `perimetro.yml` com a linha: OK; o passo "Contratos de memória e escriba" traz os três comandos.
- `bash -n` do atalho, de `inicio.sh` e de `p8_verificar.sh`: sintaxe OK. O atalho não foi executado (inicia serviços e abre terminal).
- `scripts/equipe/equipe.py --selftest` com `EQUIPE_DIR` e `EQUIPE_REPO` apontando para diretórios isolados: 34/34 OK. O estado vivo de sincronia não foi tocado.
- `PYTEST=<pytest 9.2.0> scripts/ci_sdd_local.sh`, rodado duas vezes com as mudanças aplicadas: `CI LOCAL: TUDO OK`, 33 passos OK e 0 FALHA.
- `git apply --check` do diff contra `83334fde`: OK.

## O que falta antes de aplicar (passos do Humano, não automáticos)
1. **Configurar o provedor do OpenCode** (modelo e chave no próprio OpenCode, sem colar a chave aqui). Hoje não há modelo configurado. Sem isso, o terminal abre, mas o OpenCode não responde.
2. **Confirmar o PATH:** o binário está em `~/.opencode/bin/opencode` (OpenCode 1.0.180, medido por `--version`). Não está no PATH deste shell. Não instale nada de novo.
3. **Depois de aplicar**, copiar o atalho para o runtime e comparar: `cp redesign/systemd/seth-agente ~/.local/bin/seth-agente` e `cmp`. Hoje o runtime é cópia idêntica do repositório.
4. **Atalho da área de trabalho** `Seth (agente).desktop` (local, fora do repositório) ainda diz "Goose" no comentário. Edição manual, opcional.
5. **Assinatura:** `bash scripts/aprovar.sh agente-opencode-07-11`

## Fora desta proposta (pendências)
- **Segunda proposta, só docs canon e skills:** `PROJETO.md`, `AGENTS.md`, `config/modelos-gratuitos.md`, `redesign/librechat/README.md`, `redesign/mcp/README.md`, `redesign/router/goose.md`, as skills de `.agents/` que citam o Goose e o índice derivado `ferramentas/`. Preparada depois desta, com os mesmos passos, e sem misturar no mesmo diff.
- **Entrada em MEMÓRIAS e ONDE_ESTAMOS:** vai na segunda proposta.
- **Dados do Goose:** remoção em proposta separada, depois da pergunta do Passo 4 respondida pelo Humano.
