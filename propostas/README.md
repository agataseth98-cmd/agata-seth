# propostas/ — quarentena de mudança estrutural (P-8)

Mecanismo criado em 20/08/2026 (item 6 do documento do Humano, proposta do Marcos, MEMÓRIAS (218)). Cobre o buraco descrito ali: até então, o executor escrevia em canon, comitava e empurrava — o Humano ficava sabendo depois. Nenhuma checagem do perímetro cobria isso.

## Escopo (proporcional de propósito)

**QUARENTENA OBRIGATÓRIA** — arquivos que MUDAM COMPORTAMENTO:
- `REGRAS.md`
- `PROJETO.md`
- `scripts/*`
- `.githooks/*`
- `config/*` (incluído 20/08/2026, MEMÓRIAS (222) — um prompt que dirige um modelo autônomo contra o canon muda comportamento tanto quanto um script)

**SEM quarentena** — arquivos que só REGISTRAM o que já aconteceu:
- entradas de `MEMÓRIAS.md`
- `ONDE_ESTAMOS.md`
- `INDICE_MEMORIAS.md`
- `.hidrata.md` (gerado)
- `PROMPT_CARREGAMENTO.md` (movido pra dentro do repo 20/08/2026 — dirige um modelo, mas sempre com Humano lendo a resposta antes de agir, ao contrário de `config/agata-consolidacao.prompt.txt`; ver PROJETO.md, "Quarentena estrutural")

Motivo da linha: registro errado se corrige com entrada nova — é pra isso que append-only existe. Comportamento errado, não.

## Mecanismo

1. A mudança proposta vira `propostas/<nome>.diff` (formato `git diff`, com cabeçalhos `--- a/<caminho>` / `+++ b/<caminho>`) e fica aqui, versionado.
2. O Humano aprova, de um destes dois jeitos:
   - **à mão:** cria `propostas/APROVADO-<nome>` (vazio ou com nota) — vale só na janela sem `propostas/.allowed_signers`; depois, P-8 recusa marcador sem assinatura;
   - **pelo terminal (caminho normal):** cola `bash scripts/aprovar.sh <nome> ["motivo"]` depois de ler o `.diff`. Desde MEMÓRIAS (365) o script cria o `APROVADO-<nome>`; desde MEMÓRIAS (366) ele **assina** — com `propostas/.allowed_signers` no repo, `scripts/perimetro.sh` (P-8) exige uma assinatura ssh válida (chave privada em `~/.config/agata/aprovacao_ed25519`, passphrase), amarrada ao `sha256` daquele `.diff`.
   O **executor nunca** roda `scripts/aprovar.sh` — assinar exige a passphrase da chave privada do Humano.
3. `scripts/perimetro.sh`, checagem P-8: FALHA o commit se algum arquivo staged do grupo "muda comportamento" não aparecer nos cabeçalhos de nenhum `.diff` com `APROVADO-` correspondente presente em `propostas/`.
4. Aprovação consumida: ao entrar no canon, quem aplica move o par `<nome>.diff` / `APROVADO-<nome>` para `propostas/aplicadas/` no mesmo commit que aplica a mudança.

## Risco residual (não suavizado)

O marcador de aprovação era um arquivo que o próprio executor tinha permissão técnica de criar. **Desde MEMÓRIAS (366)**, com `propostas/.allowed_signers` no repo, P-8 exige assinatura ssh no `APROVADO-<nome>` — assinar precisa da chave privada do Humano (`~/.config/agata/aprovacao_ed25519`, passphrase), que o executor não produz. Continua aceito, sem suavizar: (i) `propostas/.allowed_signers` (a raiz de confiança) não está sob quarentena — trocá-la aparece no `.diff` que o Humano revisa, mas P-8 não a protege por assinatura ainda; (ii) na janela sem `.allowed_signers`, o modo compat aceita marcador sem assinatura; (iii) chave privada mal guardada quebra tudo. O que P-8 sempre cobriu — automação/desatenção agindo sem ninguém ver (caso de 18/08/2026, MEMÓRIAS (214)) — segue coberto. Custo: o Humano digita a passphrase a cada mudança estrutural.
