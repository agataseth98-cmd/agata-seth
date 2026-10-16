# Agata

Sistema de trabalho com modelos de linguagem, feito para um operador único: **memória verificável**, **trabalho prático local** e **controle** (evidência antes de afirmar; autorização humana antes de mudar o que muda comportamento).

Este repositório é o *canon* do sistema, em Markdown e Git. A história é só de acrescentar: correção é entrada nova, nunca edição do que foi escrito.

## Por onde ler

| Arquivo | O que é |
|---|---|
| `REGRAS.md` | As regras que valem sempre |
| `PROTOCOLOS.md` | Como executar (carregar, citar, pedir segunda opinião) |
| `FALHAS.md` | Catálogo de falhas conhecidas |
| `PROJETO.md` | Arquitetura e estado vigente |
| `MEMÓRIAS.md` | Registro append-only das decisões |
| `ONDE_ESTAMOS.md` | Resumo curto do estado atual |
| `AGENTS.md` | Diretrizes para qualquer modelo que opere aqui |

## Como uma mudança entra

Mudança que altera comportamento (regras, `scripts/`, `config/`, `.githooks/`, `redesign/`) só entra com um `.diff` em `propostas/` e um `APROVADO-<nome>` assinado pela chave do Humano (`scripts/aprovar.sh`; modelos nunca o executam). O hook de commit e o fiscal de PR no GitHub conferem o par. Detalhes: `propostas/README.md`.

## Verificação

`bash scripts/perimetro.sh` roda os controles (P-1 a P-23). `bash scripts/testar_perimetro.sh` roda a suíte adversarial dos próprios controles, a mesma do CI.

Segurança: ver `SECURITY.md`. Licença: Apache-2.0 (`LICENSE`), escolha do autor em 16/10/2026.
