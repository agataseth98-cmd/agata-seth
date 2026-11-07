# Proposta: usar Piper local nas chamadas com voz nativa

## Problema

Em chamada de voz, o aplicativo pode continuar lendo as respostas com a própria voz enquanto o modelo tenta reproduzir a voz local do Agata. O modelo não controla a voz nativa do aplicativo; quando não há controle de interface disponível, também não pode afirmar que silenciou a chamada.

## Mudança proposta

Acrescentar à skill compartilhada `agata-voz` um procedimento para separar a saída nativa do aplicativo da reprodução local via `scripts/agata_falar.py`. O Humano silencia somente o áudio do aplicativo quando a interface não estiver acessível. O modelo mantém respostas e atualizações curtas em texto e fala apenas o texto final pelo Piper local. A skill explicita limites de autorização, resultado do player e não exposição de raciocínio interno.

## Critérios de aceite

- A skill distingue a voz nativa do app do Piper local e não promete trocar uma pela outra.
- A orientação silencia somente o áudio da chamada atual; não recomenda silenciar o sistema operacional nem o volume global.
- Sem controle de interface, o modelo pede ao Humano que silencie o app, espera confirmação antes de iniciar o Piper e não afirma ter feito isso.
- O modelo fala somente o texto final pelo Piper e não expõe raciocínio interno.
- O pedido explícito de fala não é repetidamente tratado como falta de autorização; aprovações exigidas pelo ambiente continuam obrigatórias e não podem ser contornadas.
- O código de saída é descrito com precisão: numa reprodução normal, sem `--preparar` nem `--sem-tocar`, `0` confirma síntese e player sem erro, não a percepção auditiva do Humano; com essas opções, `0` não confirma reprodução; `3` e `4` significam que não falou.
- A documentação deixa claro que o áudio local não é injetado de volta na chamada e que o app precisa estar silenciado para evitar duas saídas audíveis.

## Verificação e reversão

Mudança documental apenas. `git apply --check` passou em cópia limpa da base `83334fde`. A revisão independente do diff e dos critérios não apontou problemas.

**CI local:** não terminou em `CI LOCAL: TUDO OK`. Na cópia limpa do `main` e numa cópia limpa do mesmo commit com este diff aplicado, ocorreram as mesmas seis falhas preexistentes:
- pytest: 4 falhas, 323 passaram, 48 erros e 77 subtestes passaram; as quatro falhas nomeadas são os testes do painel SDD;
- critérios de aceitação: `painel_operacional`, `avaliacao` e `sentidos`;
- selftests de contexto e de voz: bloqueados ao abrir socket (`PermissionError: [Errno 1] Operation not permitted`).

Os dois ciclos SDD passaram nas cópias graváveis, com e sem o diff. Na worktree gerenciada do Codex, que é somente leitura, os ciclos falharam ao tentar gravar `spec/evidence.json`; essa execução não representa o resultado do código. O mesmo conjunto de seis falhas foi reproduzido com e sem a proposta, portanto está documentado como falha preexistente conforme a exceção do passo 3 de `agata-processo-lote`. Os checks obrigatórios do PR ainda precisam passar. Reversão: remover a seção nova de `.agents/skills/agata-voz/SKILL.md`.

## Governança

Proposta local, ainda não enviada a PR e sem assinatura. Nenhum modelo assina nem roda `scripts/aprovar.sh`. Após integração da proposta em `main` e confirmação dos checks obrigatórios, o Humano pode assinar com `bash scripts/aprovar.sh agata-voz-piper-chamada-20261107`. O código da skill não deve ser aplicado antes da assinatura e da etapa própria de aplicação.
