# Proposta rea-herdr-integracao-20261106 — REA (Reverse Engineering Anything) em leitura, Herdr mantido

**Nome para assinatura:** `rea-herdr-integracao-20261106`
**Decisão do Humano (06/11):** manter o Herdr (sessão `librechat-paridade` e hooks) e usar o REA em paralelo, com a integração pronta.
**Base:** `origin/main` (52c9636f).

## Conteúdo (só leitura)
- `.agents/skills/agata-engenharia-reversa/SKILL.md`: quando usar, allowlist, lista proibida com motivo, regra do Herdr.
- `scripts/rea_leitura.sh`: wrapper que executa o bin do REA já no cache do npx (sem npx, sem download, sem `setup`). Só aceita a allowlist; recusa `--mcp` e `--update` em qualquer posição.

## Medido (nesta proposta)
- REA 6.8.0 encontrado no cache; `--help` confere 175 subcomandos.
- Allowlist: 14 subcomandos. Recusados: os demais 161 por não estarem na lista, incluindo `setup`, `update`, `uninstall` e todos os de captura de navegador, Android, Frida e GDB.
- `bash scripts/rea_leitura.sh --selftest`: 6 de 6, sem executar o REA.
- O diff aplica limpo no `origin/main`.

## Não medido / limites
- Só `analyze-javascript-application` teve `--help` individual. Os outros 13 da allowlist entraram pela descrição de uma linha do `--help` e pelo doc do pacote. Antes de aplicar, rodar `--help` de cada um.
- `analyze-web-bundle` ficou fora: o `--help` diz "Capture" (abre a página). Decisão do Humano se entra.
- O wrapper não confere o destino de escrita: quem usa a skill confere caminho novo, fora de `~/.claude`, `~/.codex` e `~/.config`.
- `recover-javascript-sources` precisa de Wakaru, que não está instalado.
- Nada instalado; `setup` não foi rodado; o Herdr não foi tocado.

## Assinatura
`bash scripts/aprovar.sh rea-herdr-integracao-20261106`
