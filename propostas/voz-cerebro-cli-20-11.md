# Proposta voz-cerebro-cli-20-11 — skill de conversa por voz com o modelo da CLI como cérebro

Ordem do Humano por voz, 20/11/2026 ~13:2x: transformar as ferramentas semânticas e os resultados da conversa de 20/11, com ênfase no modo voz, numa skill carregável, servida no menu de skills e sempre aprimorada.

**O quê:** `.agents/skills/agata-voz-cerebro/` (SKILL.md + `scripts/escutar.py` + `scripts/vez.sh`) e uma linha em `.agents/skills/INDICE.md`.
- `escutar.py`: ouve UMA fala (captura + VAD + transcrição local do `redesign/sentidos`) e imprime o texto.
- `vez.sh`: para o som de espera, fala pela voz do sistema (`scripts/agata_falar.py`), ouve, liga o som de espera (tom suave gerado na Máquina, em `$XDG_RUNTIME_DIR`), imprime a transcrição. `--parar` encerra.
- SKILL.md: quando usar (este modelo como cérebro × canal da Seth), o ciclo, as lições medidas em 20/11 (fala cortada, silêncio, nomes trocados pela transcrição, decisão por voz vai ao cache), as ferramentas semânticas para pensar e o registro do que motivou.

**Medido:** o mesmo ciclo rodou ~25 trocas com o Humano em 20/11 (12:58–13:25); verificador de skills do painel sem problema nem aviso (57 linhas, descrição 437); CI local TUDO OK.

**Limite:** o teto do VAD corta falas longas (a skill manda pedir o resto); transcrição sem verificação de locutor, como na fase 1 do canal.

**Reversão:** git revert. **Modelo:** Claude Opus 5.5.
