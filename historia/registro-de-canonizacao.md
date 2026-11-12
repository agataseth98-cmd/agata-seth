# Registro de canonização da História

Registro, na raiz de `historia/` e fora dos tomos, de quando cada texto ficou canônico. Não é texto da História: o painel lê só `tomo-NN/NN-titulo.md` e não lê este arquivo. Entrada nova para cada canonização; entrada antiga não se edita (Regra 4).

## Tomo I, Texto 1: "A casa própria da conversa" (12/11/2026)

- **Texto:** `historia/tomo-01/01-a-casa-propria-da-conversa.md`. Sem alteração: sha256 `fe79c529046075dcf03f713eec10b91d7f9b13936cd4c561122408d68eb9906a` [medido em 12/11/2026, `sha256sum`].
- **Assinatura:** pacote-11-11, assinado pelo Humano; o par `APROVADO-pacote-11-11` está em `propostas/aplicadas/` [medido].
- **Aplicação:** commit `f181d3d5` ("Aplica pacote-11-11"), no `main` pelo PR #973, merge `9b27c1b4` (12/11/2026, 08:36 -03) [medido por `git log`].
- **Estado no frontmatter:** o texto ainda traz `estado: "rascunho para proposta P-8; não canônico até a assinatura do Humano"`. Ele é append-only, então não é editado. Este registro é a fonte da canonização. A aba História do painel ainda mostra o estado do frontmatter; ligar o painel a este registro não entrou neste pacote (fica como proposta própria).
- **Proposta de origem:** `historia-tomo1-11-11`, depois incluída no pacote-11-11 (PR #972, merge `62323e36`).
