# Proposta correcoes-19-11 — reaplicar sandbox-fase2 e assinatura-por-tipo com as correções do CI

As duas foram assinadas em 19/11 20:44, mas a aplicação falhou no CI local, e nada foi forçado:
- **sandbox-fase2-19-11:** com o pytest do venv na frente do PATH (como o CI faz), o filho sob Landlock era o python do venv, fora dos caminhos liberados ("init_import_site"). Correção em `scripts/agata_run.py`: leitura+execução do interpretador do shebang e do prefixo dele (venv e instalação base), nunca `/`, o home nem ~/.config. Teste novo com venv real: o filho roda e o .env continua negado.
- **assinatura-por-tipo-19-11:** `scripts/testar_sincronia.py` fixava 16 regras em AGENTS.md; agora 17 (nenhum teste enfraquecido).

Este .diff é o lote completo das duas (substitui sandbox-fase2-19-11.diff e assinatura-por-tipo-19-11.diff, que ficam sem aplicar).

**Medido (Opus, worktree limpa):** 29 testes do lançador + landlock com o PATH do CI; testar_sincronia 25 OK. CI local TUDO OK nas duas (agente).

**Reversão:** git revert. **Modelo:** Sonnet 5.5 (correção), Opus 5.5 (revisão).
