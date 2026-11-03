# Decreto: primeira divisão do server.py do painel (03/11/2026)

`redesign/painel_operacional/server.py` tinha 1661 linhas. Esta primeira fatia tira dele dois blocos coesos, sem mudar comportamento:
- `armazem.py` (136 linhas): itens do vault (só leitura, lista fechada) e conversas salvas.
- `relogio.py` (20 linhas): `_now`, `_stamp`, `_reading_window` e `FRESH_SECONDS`, que o armazém e o servidor usam.

O `server.py` cai para 1540 linhas e importa os mesmos nomes; as rotas e o `Handler` não mudaram. Os testes que mexiam em `ROOT` e `CONVERSAS_DIR` do servidor passam a mexer no `armazem` (4 linhas em `test_painel.py`).

Medido: 46 testes do painel OK e `--selftest` OK, rodando de dentro da pasta e da raiz do repositório. Um teste pegou um erro meu no meio do caminho (`_reading_window` ficou para trás); corrigido com o módulo do relógio.

Não dividi o bloco de leituras do sistema (git, serviços, timers, propostas) porque os testes trocam `subprocess`, `_verify` e `ROOT` direto no servidor: dividir pede reescrever esses testes e merece Decreto próprio, depois do mapeamento SDD do Codex.

Depois de aplicar, o painel precisa reiniciar para carregar os módulos novos. Faço a reinicialização pelo atalho normal e confiro o HTTP 200.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh painel-armazem-20261103 "aprovo: primeira divisão do server.py"`.
