# Proposta csp-prototipo-20261106

## Resumo
O servidor manda a CSP `style-src 'self'`. Com ela, o navegador descarta os atributos `style=` do /prototipo. A correção tira esses atributos de 11 elementos em `redesign/painel_operacional/prototipo.html` e põe classes no lugar. As 9 classes novas entram no fim de `prototipo.css`, com os mesmos valores de antes: grafo-modos, grafo-form, grafo-entrada, grafo-svg, lista-coluna, linha-medicoes, medir-nota, lista-componentes e vault-canvas. Os ids continuam os mesmos.

Diff (`git diff --cached --stat`): 3 arquivos, 203 inserções, 9 remoções.
- prototipo.css: +11
- prototipo.html: 9 linhas trocadas
- test_csp_prototipo.py: novo, 183 linhas

## Testes
- `test_csp_prototipo.py` confere quatro coisas:
  - nenhum `style=` nem `<style>` no HTML;
  - as 9 classes existem;
  - cada id está na tag certa e tem a classe certa;
  - o CSS declara exatamente os valores originais.
- Resultado: 9 testes OK. Os mutantes falham como esperado.
- Esse resultado é da rodada anterior; não o reproduzi para este registro. O agata-ci roda os testes de novo no PR.

## **RESSALVA: NÃO VERIFICADO NO NAVEGADOR**
**O navegador não conectou. Ninguém viu o /prototipo renderizado com a CSP ativa. Os testes leem o HTML e o CSS; não provam a aparência na tela.**

## Limites
- Proposta não aplicada.
- Sem APROVADO.

## Assinatura (só o Humano)
```
bash scripts/aprovar.sh csp-prototipo-20261106
```
