# Proposta `alexandria-curadoria-20261105`: correções da Alexandria achadas pela avaliação

**O que é, em português comum:** a avaliação de 05/11 mostrou dois defeitos da Alexandria e um do verificador.
- A Alexandria entregava autoridade, data e origem das fontes só como dado solto, e os modelos ignoravam: pegaram o número de um fórum anônimo, chamaram de independentes duas cópias do mesmo comunicado e usaram uma medição velha.
- Uma entrada já corrigida por uma CORREÇÃO posterior aparecia sem aviso.
- O verificador não reconhecia "Não encontrou nas fontes" como recusa.

**Decisão do Humano (05/11/2026):** "já aproveite e conserte os erros encontrados em alexandria".

## O que entra

- **`redesign/alexandria/curadoria.py`** (novo): antes de chegar ao modelo, as fontes vêm em ordem. Primeiro as com autoridade (canon, medição, decisão do Humano, spec), depois as vigentes antes das superadas, depois a mais recente. Cada fonte recebe aviso escrito quando for cópia (texto idêntico ou mesma origem declarada), correção explícita, fonte sem autoridade ou medição anterior. É mecânico e sem modelo: ordena e avisa, não decide.
- **`acervo.consultar`**: a entrada citada primeiro no cabeçalho de uma `(M) CORREÇÃO` sai com `corrigida_por`. São 39 entradas do acervo; por exemplo, (927) aparece corrigida por (928). A regra lê só a primeira citação, porque a versão que lia todas marcava também entradas apenas mencionadas, como (829) e (832) na (834).
- **Avaliação, rubrica v2:**
  - a abstenção passa a reconhecer a 3ª pessoa;
  - o prompt pede, em todas as condições, para pesar autoridade, data e notas;
  - a condição `alexandria` passa pela curadoria;
  - o pacote do repo leva o aviso de correção.
- **Painel:** o resultado da consulta mostra o selo "corrigida por (M)".
- **Specs e testes:** 3 testes novos e critérios de aceite novos em `alexandria` e `avaliacao`.

## Evidência (worktree, 05/11/2026)

- 162 testes verdes na suíte da CI, ANCHOR OK, sem drift. O `.diff` aplica limpo sobre o `main` (`0e9f9da2`).
- **Conjunto reservado, rodada `r-20261105-085539-6c774d`** (com este código, 62 chamadas locais):
  - **Placar:** com a Alexandria, os três modelos foram 10 pontos melhores que a busca de hoje. O veredito é inconclusivo, porque são 10 pares.
  - **Falha crítica (dado privado):** zero com a Alexandria, contra uma por modelo com a busca de hoje.
  - **Por modelo:** lfm3:1.7b 70%, lumi-4b 80% e qwen3-30b 60%.
- **Antes da curadoria** (`r-20261105-082629-26a56b`): a Alexandria empatava com a busca de hoje no qwen3-30b.
- **Conjunto de desenvolvimento** (`r-20261105-084641-4e6d6a`): lfm3:1.7b com 83% usando a Alexandria, contra 58% com a busca de hoje.

## Limites e não medido

- **Reservado gasto:** a curadoria nasceu das falhas vistas nele, então ele não mede mais este mecanismo sem viés. A spec registra isso. O próximo passo é um reservado novo, escrito por outra família de modelo ou pelo Humano.
- **Não resolvido:** os modelos ainda erram "estado atrasado" e "fonte suficiente" sobre a (670). A resistência ao e-mail com autoridade forjada continua com o lote 4 (metacognição).
- **Heurística:** a regra de "corrigida por" pode errar quando o cabeçalho cita primeiro uma entrada que não é a corrigida.

## Depois de aplicar

Reiniciar o painel. Não precisa reindexar: a marcação é feita na consulta.

## Reversão

Revert do PR. Nada no canon muda.
