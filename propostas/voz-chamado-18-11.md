# Proposta voz-chamado-18-11 — "fale comigo" vira o chamado de voz do sistema

Ordem do Humano, 18/11/2026 18:54: "canonize o fale comigo como chamado de voz do sistema". Complementos do Humano no uso real, no mesmo dia: 19:09 "não precisa explicar, faça com que o sistema aja naturalmente a partir da perspectiva humana"; 20:38 "e avisa em voz, justo?".

**O quê** (`AGENTS.md` linha da voz; `.agents/skills/agata-voz/SKILL.md`, seção 0):
- "fale comigo" abre o chamado de voz em qualquer modelo; cada resposta seguinte é falada pela voz do sistema até "encerrar chamado", "volte ao texto" ou "pare de falar".
- Agir naturalmente: a fala é a resposta; não narrar o mecanismo; só avisar quando a voz falhar.
- Toda fala do Humano recebe resposta em voz, nem que seja curta; nunca silêncio.
- Som de espera opcional, gerado na Máquina, com entrada e saída suaves, que para antes da fala.
- Segredo, token ou dado pessoal nunca são falados; sem áudio, diz que NÃO falou e entrega o texto falável.

**Medido:** usado ao vivo em 18/11 (19:07 a 20:41) pelo Claude Code com o Humano; lint de skills e CI local TUDO OK na versão anterior; esta versão só acrescenta dois itens de texto.

**Reversão:** `git revert` do commit de aplicação.

**Modelo:** Opus 5.5.
