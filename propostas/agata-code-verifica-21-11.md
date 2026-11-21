# Proposta agata-code-verifica-21-11 — a Seth passa a saber se o Agata Code provou o que disse

Lote 3, primeira parte. Defeito medido em 20/11: o Agata Code respondeu sem usar ferramenta e inventou arquivos e evidência.

**O quê** (`redesign/painel_operacional/`): `ferramentas_seth.py` conta os usos de ferramenta na transcrição do Agata Code e põe um selo no início do que a Seth recebe: "NÃO VERIFICADO: o Agata Code não usou nenhuma ferramenta; trate a resposta como opinião sem prova." / "verificado por: glob×1, read×2" / "sem resposta do Agata Code (timeout)". O bloco da tela mostra o mesmo selo. Teste fixa que o OpenCode roda com stdin em /dev/null.

**Medido (21/11):**
- Diagnóstico da trava: `opencode run` espera o stdin; com stdin aberto trava antes de chamar o gateway (2/2); com /dev/null, 33/33 rodadas sem trava (serial, paralelo, worktree nova). O módulo já usava /dev/null; as travas do coordenador eram do teste dele.
- Gateway direto: nemotron-3.5-bolt chamou a ferramenta em 14/15.
- Pelo Agata Code (N=5): sem trava, 6–9 s; 4/5 sem ferramenta (selo NÃO VERIFICADO correto), 1/5 com glob; acerto 0/5 (o glob é recursivo e o modelo contou 30).
- 34 testes de ferramentas_seth; CI local TUDO OK (agente).

**Limite:** o selo prova que houve ferramenta, não que a resposta esteja certa. O modelo atual não serve para o Agata Code trabalhar de verdade: a escolha de modelo pelo placar e a instrução de uso de ferramenta ficam para a parte 2 do lote 3.

**Reversão:** git revert e reiniciar o painel. **Modelo:** Sonnet 5.5 (diagnóstico e código), Opus 5.5 (revisão).
