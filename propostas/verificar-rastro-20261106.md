# Proposta `verificar-rastro-20261106`: `--verificar` deixa rastro (só metadado) no log da auditoria

**O que muda:**
1. `redesign/router/auditoria_turno.py`: `--verificar [--cliente NOME]` grava um registro `cli-NOME` (`ts`, `cliente`, `n_achados`, `tipos`, `anterior`, `hash`) na mesma cadeia do log (`AGATA_AUDITORIA_LOG`). Sem texto de entrada e sem literal de achado: `tipos` é só o prefixo de cada achado (corta em `:`, aspas, crase, parêntese ou travessão; números viram N; até 32 caracteres). NOME fora de `[a-z0-9-]{1,32}` vira `desconhecido`. Saída e código de saída iguais aos de hoje; falha ao gravar é silenciosa.
2. `AGENTS.md`, linha da (849): o comando passa a levar `--cliente <nome>` e avisa que grava um registro de metadado.

**Medido:** `--selftest` com C1-C9 (log temporário) passou; C9 compara linhas e sha256 do log real antes e depois (iguais); C7 pula se root; o diretório temporário é removido em finally; `scripts/ci_sdd_local.sh`: TUDO OK.

**Não medido:** adesão dos clientes (o rastro prova execução, não obriga). Concorrência de escrita segue sem lock (pré-existente).

**Reversão:** `git revert`; os registros `cli-*` não quebram a cadeia.
