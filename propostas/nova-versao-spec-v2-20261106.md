# Proposta — revisão da spec da nova versão (v2)

**Nome para assinatura:** `nova-versao-spec-v2-20261106`
**Origem:** o mesh de revisão (operador, simplificador, implementador) não aprovou a spec. Decisões do Humano em 06/11/2026, aplicadas aqui.

## Decisões do Humano aplicadas
1. **Orçamento:** valores equilibrados descobertos e aplicados. Quatro categorias (`local`, `gratuito`, `assinatura`, `pago`), iguais às do código. Padrão: 200 chamadas, 2 milhões de tokens, 120 s, R$ 0 (pago desligado). Medido: uma chamada do Conselho usou 11.292 tokens e 19,6 s; 200 × ~11 mil ≈ 2,2 milhões, então 2 milhões é coerente.
2. **Cofre de chaves:** sai do lote 2 como cofre, mas o painel de chaves entra no lote 2: campo só de escrita, gravação atômica em `~/.config/agata/.env` (0600), nada devolve o valor, ledger registra só o nome.
3. **Reversão:** `AGATA_NV_DIR` é arquivado, não apagado; só o cache é removido. Apagar só quando o Humano decidir.
4. **Escopo:** nada é descartado. `metacognicao/`, `corpo/`, `skills.py` e `conselho.py` saem do lote atual e entram no lote 6, com critério antes do código.

## Correções do mesh
- Trava única (`flock` com timeout) e fila de GPU; `eventos.py` vira camada fina sobre o ledger, sem log próprio.
- Ordem entre ação e registro: intenção, ação, confirmação; `sincronizar` reconcilia.
- `orcamento_turno.py` vira escopo dentro de `orcamento.py`.
- Lote de cada item de Código explícito.
- Três critérios novos: valores do orçamento, painel de chaves sem vazamento, reversão sem apagar o ledger.

## O que não foi decidido (fica aberto)
- **Exceção à regra do `.env`:** a rotina do painel lê o arquivo só para trocar a linha da chave. A regra atual não prevê isso. O Humano precisa aprovar na assinatura.
- **Tabela de transições das sete palavras:** continua sem definição no pacote (operador e implementador apontaram). Não entra nesta proposta; fica para o lote 2.
- **Critérios do lote 6:** `metacognicao`, `corpo`, `skills`, `conselho.py` ainda não têm critério.

## Evidência
- O diff aplica limpo num checkout de `origin/main` (`git apply --check`).
- Só `redesign/nova_versao/spec/spec.md` muda; nenhum código.

## Assinatura
`bash scripts/aprovar.sh nova-versao-spec-v2-20261106`
