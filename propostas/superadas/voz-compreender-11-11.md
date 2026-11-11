# Voz: falar para compreender (primordial, 11/11/2026)

Proposta P-8 sobre `origin/main` `182310d0`. Assinatura do Humano, uma vez, depois do merge deste PR de proposta.

## O que muda

- `AGENTS.md`, bullet "Voz do sistema, sem negociação": uma frase nova. "fale" ou "leia para eu compreender" aciona o comportamento em qualquer modelo, sempre. Sem áudio, o modelo entrega o texto falável e diz que NÃO falou.
- `.agents/skills/agata-voz/SKILL.md`: seção nova no início, "Falar para compreender (primordial, Humano 11/11)". Passo a passo: reescrever a última resposta para ouvido; não falar se houver segredo; salvar o texto no scratchpad; falar com `scripts/agata_falar.py --arquivo`; relatar em uma linha; anotar no cache do Conselho para medir. O resto da skill não muda.
- Sem script novo, sem teste novo. Registro fora do diff: nenhum neste PR (o pedido listou só o `.diff` e o `.md`). Entrada em MEMÓRIAS, se o Humano quiser, é entrada nova.

## Por que

Pedido do Humano em 11/11/2026, 19:35: "transforme esse comportamento em uma skill primordial do agata". O comportamento: ao ouvir "fale a última resposta para me ajudar a compreender", o modelo reescreve a resposta para ouvido (sem tabela, símbolo, caminho nem bloco de código; listas viram frases) e fala com o script. A skill atual descreve o script e a voz, mas não diz como transformar a resposta em texto falável (medido: leitura da skill em 11/11). Os exemplos desta sessão que a seção descreve: `fala-melhores.txt` e `fala-p1p4.txt` no scratchpad.

## Fatos medidos no código (`scripts/agata_falar.py`)

- Saída 0 só quando falou. Saídas 2, 3 e 4 são NÃO falou.
- A saída 2 também vem de texto vazio, de texto acima de 12.000 caracteres e de arquivo que não pôde ser lido. A linha antiga da skill ("Com 3 ou 4 o modelo diz que NÃO falou") não cita o 2. A seção nova cita. A linha antiga não foi mexida, por causa de "mantenha o resto".
- `main` não devolve saída 1 no uso real (só o selftest devolve).

## Como medir (14 dias, até 25/11/2026)

- Nº de pedidos "fale" atendidos com texto adaptado: contar as anotações `fala: texto adaptado, saída <n>` no cache do Conselho (`python3 redesign/router/cache_conselho.py ler --n 200`). Meta: uma anotação por pedido atendido.
- O próprio `--help` do `cache_conselho.py` diz que o cache reinicia a cada 15 dias (M4). A contagem tem de ser feita antes do reinício.
- Pedidos em que o modelo leu a tela literal: sem medida automática. O Humano aponta a partir das conversas.
- Não medido: quantos pedidos "fale" há por semana (não havia contador antes desta proposta).

Critério para manter ou reverter: **proposto, o Humano decide** em 25/11/2026. Proposta deste autor: manter se cada pedido "fale" do período tiver anotação e o Humano não tiver reclamado de leitura literal da tela; senão, reverter ou ajustar a skill.

## Apetite (R2, declarado)

- Arquivos de código e de canon: 2 (`AGENTS.md` e `.agents/skills/agata-voz/SKILL.md`). Scripts: 0.
- Horas de agente: 1 h (estimativa). Medido com `date`: de 19:35 a 19:42 até o diff e a CI local. Não passou do apetite.

## Testes medidos

- `git apply --check` do `.diff` contra `origin/main` `182310d0`: passou. `git apply --stat`: `AGENTS.md | 2 +-`, `.agents/skills/agata-voz/SKILL.md | 13 +++`.
- Cópia de `182310d0` (clone em scratchpad), diff aplicado com `git apply`, conferido com `cmp` contra o `.diff`. `uv run --offline --with pytest bash scripts/ci_sdd_local.sh`: 33 passos OK, código de saída 0, última linha `CI LOCAL: TUDO OK`. Inclui `voz do sistema (selftest)`.
- Lint de skill (`redesign/painel_operacional/qualidade_llm.py`): `agata-voz` com `linhas` de 26 para 39, `problemas: []`, `avisos: []`.
- Sem emoji: conferido no diff e neste texto (códigos Unicode de símbolos e emoji).

## Conflitos com propostas abertas (medido)

`AGENTS.md` é tocado por três propostas abertas. Medido com `git apply` numa cópia, nas duas ordens:

- `verificar-rastro-20261106`: conflita nas duas ordens.
- `docs-opencode-07-11`: conflita nas duas ordens.
- `nucleo-desenvolvimento-07-11`: este diff aplica depois dele; ele conflita se vier depois deste diff.

Ordem sugerida: a que for aplicada primeiro vence; quem vier depois refaz o diff sobre o `main` no momento da aplicação. Nenhuma das três foi aplicada.

## Riscos

- "fale" é palavra comum. "fale com a Seth" ou "fale sobre X" não é este pedido: a cláusula "sem outro alvo" existe por isso. Não medido se o modelo respeita a cláusula em pedidos reais.
- Segredo: a skill manda não falar se a resposta trouxer senha, token ou dado pessoal.
- O script não ouve o resultado. O modelo diz isso no relato.

## Não medido

- Se a fala sai bem: só o Humano ouve. O script não mede a qualidade da fala (regra 2 da skill).
- Quantos pedidos "fale" há por semana.
- A falha `test_sdd_painel` da suíte unittest do painel (citada na proposta da #966) não está no CI local e não foi rodada aqui. Dono e data não registrados; é pendência para o Humano.

## Lista de conferência de pronto (R3)

- [x] CI local `TUDO OK` (saída acima, na cópia com o diff aplicado).
- [ ] Run verde no GitHub no `headSha` do PR: preenchido depois do push, com `gh run list --branch proposta/voz-compreender-11-11 --json headSha`.
- [x] Captura de tela: não se aplica (sem interface).
- [x] Sem emoji: conferido.
- [x] `.md` com testes medidos, o que não foi medido e a reversão.
- [x] Nenhuma falha desta proposta. A falha `test_sdd_painel` fica em "Não medido", com dono e data pendentes.
- [x] Entrada de MEMÓRIAS sem `caminho:número`: não se aplica (este PR não acrescenta entrada de MEMÓRIAS).

## Reversão

Proposta própria que aplica `propostas/aplicadas/voz-compreender-11-11.diff` ao contrário (`git apply -R`), assinada à parte, porque `AGENTS.md` e a skill estão no caminho protegido. Sem reescrever histórico: a reversão é entrada nova (Regra 4).

## Assinatura

Depois do merge deste PR, o Humano roda:

```
bash scripts/aprovar.sh voz-compreender-11-11 "<motivo>"
```

Verificação depois da assinatura, com HEAD em `origin/main`:

```
bash scripts/p8_verificar.sh voz-compreender-11-11
```
