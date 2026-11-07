# Proposta: docs canon e skills, Goose sai e OpenCode entra (segunda proposta)

**Nome para assinatura:** `docs-opencode-07-11`
**Decisão do Humano (07/11/2026):** "a goose sai e o open code entra, integrado de forma primeira palavra ao sistema".
**Base:** `origin/main` = `83334fde`. Diff: `propostas/docs-opencode-07-11.diff` (12 arquivos, sem misturar código).
**sha256 do .diff:** `afb8a9f5813a761105365e1263ba4d2074a5fe806f343abc02eec8aadbdaee6c`

**Ordem:** esta proposta é separada da `agente-opencode-07-11` (atalho, equipe, teste e CI). Não há conflito de arquivo entre as duas. O texto desta descreve o OpenCode como agente de terminal, o que só vale depois que a primeira for aplicada. Assine a primeira antes.

## O que o diff faz
- **Canon:** `PROJETO.md` (Frentes, combo `seth-codigo`, lista de agentes, atalho "Seth (agente)", voz comum); `AGENTS.md` (lista de ferramentas, aprovação de ferramenta, voz comum, `seth_gateway`).
- **Configuração e docs:** `config/modelos-gratuitos.md` (tier 0 do `seth-codigo` e cabeçalhos; o histórico das decisões antigas fica como está); `redesign/librechat/README.md` (agente de código); `redesign/mcp/README.md` (lista de executores e exemplo de cliente); `redesign/router/goose.md` (banner de histórico no topo, o texto fica).
- **Skills:** `agata-aplicar-proposta` (config do agente no runtime); `agata-conversar-com-seth` (descrição e MCP de navegador); `agata-fluxo-equipe` (descrição e nome do membro `opencode`).
- **Índice derivado:** `ferramentas/indice.json`, regenerado com `python3 -I ferramentas/ferramentas.py reindexar`. O comando mudou só os dois resumos que citam o Goose; `ferramentas/INDICE.md` não mudou.
- **Registro:** `MEMÓRIAS.md`, entrada (973), logo abaixo do marcador `ENTRADAS-NOVAS` (5 linhas acrescentadas, nenhuma removida). `ONDE_ESTAMOS.md`, bloco "Hoje, 07/11" no topo e data da página.

## O que fica de propósito
- O histórico continua: decisões com data (ex.: 13/10 sobre o Groq e o `seth-codigo`), entradas antigas de MEMÓRIAS e `redesign/LOG.md`, fora desta proposta.
- `redesign/goose/` (README e AGENTS) e `config/portas-de-entrada.txt`: ficam até o Humano decidir a remoção dos dados. Estão na lista de exceções do teste da primeira proposta.
- Remoção dos dados e do programa do Goose: pergunta ao Humano, em aberto.

## Arquivos tocados (sha256 do conteúdo final)
| Arquivo | Tipo | sha256 |
|---|---|---|
| `AGENTS.md` | canon | `e8e752931c5570e50db1bb7fd0e506f2dd3e55391175933ea3bc7c602164db17` |
| `MEMÓRIAS.md` | canon (append-only) | `d9a595bcc7d613b130b9cc9d90e7dbdefd067bc7cc371e1096dac42bc2fde96d` |
| `ONDE_ESTAMOS.md` | página viva | `f7ef95c2d6e736ced11cec2ed742c214508bbf3c9802eda38484ad0b12ed427b` |
| `PROJETO.md` | canon | `587413fb88211fa6012ced3dac635fa7602b854d83cdd901ed4804cac8810a4d` |
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
- `git apply --check` do diff contra `83334fde`: OK. Aplicado de novo e revertido, para conferir os sha256 acima.
- `MEMÓRIAS.md`: o diff só acrescenta linhas (5 linhas, nenhuma removida), então o P-5 de append-only deve passar.
- Nenhuma citação numerada de MEMÓRIAS nova na entrada (973): o P-7 não tem o que checar além disso. A frase entre aspas é o pedido do Humano, transcrito como recebido; não conferi em canon.

## O que falta antes de assinar e aplicar
1. **Número da entrada:** a (973) assume que a (972) continua no topo. Se outra entrada entrar antes, a numeração é ajustada na entrada seguinte, sem editar esta.
2. **Hook de commit:** o pre-commit roda os controles P-1 a P-23 e grava âncoras de SHA em REGRAS, PROJETO, MEMÓRIAS e PROMPT_CARREGAMENTO, o que é normal nas outras propostas. Não rodei o perímetro sobre esta mudança.
3. **Ordem de aplicação:** aplicar `agente-opencode-07-11` antes desta, para o texto ficar verdadeiro.
4. **Passos do Humano:** os mesmos da primeira proposta (modelo do OpenCode configurado e PATH). Sem isso, o texto "OpenCode no terminal" descreve um estado que ainda não existe.

## Assinatura
`bash scripts/aprovar.sh docs-opencode-07-11`
