# Proposta P-8 — contrato seguro do RelayCouncil

## Objetivo

Abrir uma fronteira tipada para resultados do protótipo RelayCouncil sem
incorporar navegador, cookies, sessões, credenciais ou chamadas externas ao
cânone.

## Evidência da prova

- `redesign/router/relay_council_contract.py` valida `task_id`, provedor, site,
  estado, sucesso, texto, erro, latência e timestamp.
- Estados aceitos: `candidate`, `green`, `monitoring`, `provider_busy` e
  `excluded`.
- Campos sensíveis são recusados; campos desconhecidos são descartados.
- Testes locais: 3 testes `unittest`, compilação Python e `git diff --check`
  passaram em 28/10/2026.

## Limites

Esta proposta não conecta o relay ao OmniRoute, não altera o roster, não abre
abas e não promove nenhum provedor. A integração de transporte fica para uma
segunda proposta, depois de o contrato ser aceito e os fixtures serem
reproduzidos no CI.

## Aplicação

O Humano deve revisar `relay-council-contrato-20261028.diff` e, se concordar,
assinar a proposta pelo fluxo P-8. O executor não cria `APROVADO-*` e não
aplica esta proposta.
