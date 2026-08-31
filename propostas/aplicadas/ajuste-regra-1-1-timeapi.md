## Proposta: Ajuste da Regra 1.1 — Remover dependência de APIs HTTP via web_extractor

**Data:** 26/08/2026
**Motivação:** MEMÓRIAS (264) documentou que a API timeapi.io via web_extractor retorna timestamps cacheados (data de ontem), tornando-a não confiável para modelos em nuvem.

**Problema detectado:**
- Ferramenta web_extractor pode cachear respostas HTTP
- APIs de horário retornam timestamps desatualizados
- Modelos em nuvem ficam com hora errada

**Ajuste proposto na Regra 1.1:**

Modelos em nuvem (sem shell):
- ~~API primária: timeapi.io~~ (não confiável via web_extractor)
- Usar hora informada pela interface/sistema com selo (informado pela interface)
- Declarar lacuna: API externa não confiável, ver MEMÓRIAS (264)
- Se curl disponível, usar curl direto em vez de web_extractor

**Impacto:** Modelos em nuvem passam a declarar hora informada em vez de tentar API externa não confiável.
