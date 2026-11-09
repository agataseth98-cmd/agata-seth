# Proposta: docs canon e skills, Goose sai e OpenCode entra (segunda proposta)

**Nome para assinatura:** `docs-opencode-07-11`
**Decisão do Humano (07/11/2026):** "a goose sai e o open code entra, integrado de forma primeira palavra ao sistema".
**Base conferida:** `origin/main` = `13c34c1a`. Diff: `propostas/docs-opencode-07-11.diff` (10 arquivos; delta documental/skills para vir depois da aplicação da proposta 1).
**sha256 do .diff:** `96e2cd126889d19851a7f6e5cd224c6ecc39eb1280f342f1ad3b0de57fc0b43d`

**Ordem:** esta é a segunda parte e vem depois de `agente-opencode-07-11` (atalho, equipe, teste e CI). O registro da decisão em MEMÓRIAS/ONDE_ESTAMOS pertence ao diff da primeira parte; removi esses hunks daqui para não repetir a mesma entrada. O texto desta descreve o OpenCode como agente de terminal, o que só vale depois que a primeira for aplicada. Assine a primeira antes.

## O que o diff faz
- **Canon:** `PROJETO.md` (Frentes, combo `seth-codigo`, lista de agentes, atalho "Seth (agente)", voz comum); `AGENTS.md` (lista de ferramentas, aprovação de ferramenta, voz comum, `seth_gateway`).
- **Configuração e docs:** `config/modelos-gratuitos.md` (tier 0 do `seth-codigo` e cabeçalhos; o histórico das decisões antigas fica como está); `redesign/librechat/README.md` (agente de código); `redesign/mcp/README.md` (lista de executores e exemplo de cliente); `redesign/router/goose.md` (banner de histórico no topo, o texto fica).
- **Skills:** `agata-aplicar-proposta` (config do agente no runtime); `agata-conversar-com-seth` (descrição e MCP de navegador); `agata-fluxo-equipe` (descrição e nome do membro `opencode`).
- **Índice derivado:** `ferramentas/indice.json`, regenerado com `python3 -I ferramentas/ferramentas.py reindexar`. O comando mudou só os dois resumos que citam o Goose; `ferramentas/INDICE.md` não mudou.
- **Registro da decisão:** fica no diff da primeira parte; este diff não altera `MEMÓRIAS.md` nem `ONDE_ESTAMOS.md`, para evitar duplicação.

## O que fica de propósito
- O histórico continua: decisões com data (ex.: 13/10 sobre o Groq e o `seth-codigo`), entradas antigas de MEMÓRIAS e `redesign/LOG.md`, fora desta proposta.
- `redesign/goose/` (README e AGENTS) e `config/portas-de-entrada.txt`: ficam até o Humano decidir a remoção dos dados. Estão na lista de exceções do teste da primeira proposta.
- Remoção dos dados e do programa do Goose: pergunta ao Humano, em aberto.

## Arquivos tocados (sha256 do conteúdo final)
| Arquivo | Tipo | sha256 |
|---|---|---|
| `AGENTS.md` | canon | `e8e752931c5570e50db1bb7fd0e506f2dd3e55391175933ea3bc7c602164db17` |
| `PROJETO.md` | canon | `20c7f74128015f28fecd633ba4b7a2573e7d84a2a19f24c690197e1d2c3a47cf` |
| `config/modelos-gratuitos.md` | config | `bdede05c876b1417659b752f4259bfe466ea869229d5c766de4073dddc460b9e` |
| `ferramentas/indice.json` | derivado (reindexar) | `9a324014fec1a2b300448ae727d6bd4f6ff023f50f33931dabcc329846363a99` |
| `redesign/librechat/README.md` | doc | `3b6dd8a6fcf00acc15839126837b36aaa1eaef0f5792c41c6b06705c64ab40d0` |
| `redesign/mcp/README.md` | doc | `2b001c133a9b75d483cb9864de9bc2e4ce8ec603a517b57cbb2c395ec37dbbc9` |
| `redesign/router/goose.md` | doc (banner) | `d06e645fd460ea60c8b3ff45f130d1203c7c7e810e1fe79b1156c6501b0621af` |
| `.agents/skills/agata-aplicar-proposta/SKILL.md` | skill | `e5658bb18ed7724aba5bf50157ab3844e9a192247fbfbc3fe41c2c495585727a` |
| `.agents/skills/agata-conversar-com-seth/SKILL.md` | skill | `774f83cf0de53e68d148f0954b2a56c40c96786eb314e28e99a72256c8e74354` |
| `.agents/skills/agata-fluxo-equipe/SKILL.md` | skill | `019630b0fa7f9673d2c0f7bbfa531f372b2b3606ecad10d6d3726940e5043542` |

## Verificação feita
- `PYTEST=<pytest 9.2.0> scripts/ci_sdd_local.sh` com as mudanças aplicadas na worktree: `CI LOCAL: TUDO OK`, 33 OK e 0 FALHA. Inclui o lint das skills e o selftest de qualidade.
- `git apply --check` do diff contra `13c34c1a`: OK. Também foi conferido em sequência após aplicar o diff da primeira proposta.
- As somas dos arquivos finais foram medidas após aplicar os dois diffs em sequência, sobre `13c34c1a`.
- Reexecução em 09/11/2026 com a primeira proposta e este delta aplicados sequencialmente: `CI LOCAL: TUDO OK`, exit 0.

## O que falta antes de assinar e aplicar
1. **Número da entrada de aplicação:** pertence ao diff da primeira proposta; a numeração final da aplicação deve ser conferida quando o Humano assinar, após a fila de propostas.
2. **Hook de commit:** o pre-commit roda os controles P-1 a P-23 e grava âncoras de SHA em REGRAS, PROJETO, MEMÓRIAS e PROMPT_CARREGAMENTO, o que é normal nas outras propostas. Não rodei o perímetro sobre esta mudança.
3. **Ordem de aplicação:** aplicar `agente-opencode-07-11` antes desta, para o texto ficar verdadeiro.
4. **Passos do Humano:** os mesmos da primeira proposta (modelo do OpenCode configurado e PATH). Sem isso, o texto "OpenCode no terminal" descreve um estado que ainda não existe.

## Assinatura
`bash scripts/aprovar.sh docs-opencode-07-11`
