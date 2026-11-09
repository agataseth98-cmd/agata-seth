# Proposta P-8 — Interface do Conselho de Modelos em Rede

**Nome para assinatura:** `relay-council-panel-ui-20261028`  
**Base:** `main` após PR #679 (`a4c6073bfb0473e1058dffed8e70556918175124`).

## Mudança

Adicionar ao painel uma área em português chamada **Conselho de Modelos em Rede**. A tela consulta o catálogo local de 17 provedores e permite registrar manualmente uma resposta ou falha que a pessoa observou. O registro usa o endpoint local existente e acrescenta uma avaliação sanitizada ao cache comum do Conselho.

O formulário deriva o modo de acesso do catálogo, valida os campos, mostra recibo e oferece repetição idempotente quando há falha temporária. A documentação e o estado do projeto passam a refletir essa capacidade limitada.

## Limites

- Não envia prompts nem faz chamadas a provedores.
- Não controla abas, automatiza DOM ou lê cookies, sessões, credenciais ou dados do navegador.
- Não altera canon técnico, não assina, não reinicia serviços e não muda o histórico do painel.
- Para provedores marcados como API oficial, a origem do resultado precisa ser uma chamada externa autorizada, feita fora desta tela.

## Arquivos

- `redesign/painel_operacional/prototipo.html`, `prototipo.js`, `prototipo.css` e `README.md`
- `ONDE_ESTAMOS.md`
- entrada nova (907) em `MEMÓRIAS.md`

## Verificação

- `python3 redesign/painel_operacional/server.py --selftest`
- `python3 -m unittest redesign/painel_operacional/test_painel.py` — 22 testes
- `node --check redesign/painel_operacional/prototipo.js`
- `git diff --check`
- Chromium isolado: catálogo de 17 itens, envio simulado sem gravação, sem overflow em viewport desktop e móvel.

## Assinatura humana

Após este registro entrar em `main` e a revisão estar concluída, assinar com:

```sh
bash scripts/aprovar.sh relay-council-panel-ui-20261028 "aprovo interface manual do Conselho de Modelos em Rede"
```

O executor não executa esse comando. A aplicação do código continua em PR separado após a assinatura.
