# Proposta `nova-versao-lote5-20261105`: fecha as lacunas da nova versão (um lote)

**O que é, em português comum:** é o lote que faz a nova versão do Agata sair da sombra para o que a pasta do experimento pede. Entra a entrada controlada de fontes externas (upload pelo painel, pasta e URL), com quarentena e decisão sua; a pesquisa externa como evidência descartável; ciclo de skills com revogação; papéis e redundância testados por capacidade; orçamento por turno; revisão de suporte; a avaliação com troca de LLM, restauração, rubrica às cegas e seleção de skill medida; e as novidades da Seth atrás de flags desligadas.

**Decisões suas (05/11/2026):**
- o reservado novo foi escrito por mim (60 tarefas), e você revisa pelo terminal (`revisar.py`); as rotas da família Claude não contam para o veredito;
- a entrada de fontes é pasta, URL e upload pelo painel, e a decisão de direitos é sua, caso a caso;
- o teto de POST sobe para 64 KB em todas as rotas gerais ("aumenta tudo");
- um lote, uma assinatura;
- as novidades da Seth ligam só no seu teste final.

## O que entra (68 arquivos, cerca de 3.600 linhas)

- **Alexandria:** `cadastro.py` (fonte de verdade dos externos), `aquisicao.py` (três entradas, um caminho, quarentena, parse isolado), `correcoes.py` (definição única de CORREÇÃO), `externa.py` (pesquisa externa efêmera), `ciclo_skills.py` (rascunho → quarentena → em-teste → elegível → revogada). Suficiência em `acervo.py`. Índice de schema 2.
- **Nova versão:** `caminhos.py` (confinamento de nomes), `papeis.py` + `config/papeis.json`, `redundancia.py`, `orcamento_turno.py`, `nv.py sincronizar` (as sete palavras ligadas ao ledger).
- **Avaliação:** `conjunto.py` com o split `teste2`, `_contaminado` por família, validações, critérios `rubrica` e mecânico de restauração; `avaliar.py` com troca de LLM, teto de tokens de verdade, paralelo, condições `alexandria_externa` e `alexandria_guarda`; `revisoes.py` e `revisar.py` (rubrica às cegas e revisão do reservado pelo terminal); `registro_medidor.py`; medição de seleção de skill em `recuperacao.py`.
- **Metacognição:** `revisao_suporte.py` (verificação mecânica e revisor de outra família, proporcional ao risco); `posterior` marca `parcial` com orçamento esgotado.
- **Sentidos:** `visao.py` (descrição de imagem pelo lfm3-vl).
- **Painel:** página **Acervo e fontes** (upload, pasta, URL, quarentena, decisões), rota `POST /api/nova-versao/upload`, teto de POST de 64 KB, correção do temporário que ficava na pasta depois de recusa (agora limpa antes de responder).
- **Gateway (atrás de flags desligadas por padrão):** saúde na linha de estado (`SETH_SAUDE_NO_ESTADO`), skills sugeridas (`SETH_SKILLS_SUGERE`), guarda que troca eco de segredo por recusa (`SETH_GUARDA_BLOQUEIA`; nunca mexe em resposta com `tool_calls`).
- **Medidores antigos:** `teste_portugues.py`, `medir_contexto_efetivo.py` e `seth_autodev.py` ganham `--registro`. Sem a flag, nada muda.
- **Correções de segurança e de confiabilidade achadas no caminho:** o sandbox de `redesign/grafo/sandbox.py` lançava exceção em timeout (`stderr` em bytes) e capturava saída sem teto; agora a saída é cortada pelo kernel (2 MB) e há limite de CPU e memória. `politica_egress.buscar_seguro` ganha `max_bytes` opcional (quem já chama não muda).
- **Specs e aceite:** `alexandria`, `avaliacao`, `nova_versao`, `metacognicao`, `sentidos` e `painel_operacional` têm novas seções "Lote 5", critérios e comandos de aceite. `PROJETO_REFERENCIA.md` ganha o resumo do lote. `PROJETO.md` não muda (47.929 de 48.000 bytes).

## Escopo P-8 (precisa do par assinado)

Arquivos em quarentena do perímetro: `scripts/politica_egress.py`, `scripts/medir_contexto_efetivo.py`, `scripts/seth_autodev.py`, `scripts/teste_portugues.py`, `config/papeis.json`, `redesign/router/seth_gateway.py`, `redesign/grafo/sandbox.py`. Os demais são do painel e da avaliação. `scripts/perimetro.sh` não muda.

## Evidência (05/11/2026, worktree)

- **Testes:** 254 verdes nos componentes da CI (inclui painel, avaliação, Alexandria, nova versão, metacognição, sentidos e conexões).
- **Selftests:** gateway, sombra, `medir_recuperacao`, `medir_contexto_efetivo`, `teste_portugues` e `seth_autodev` (com `-I`, como no CI) e `politica_egress`.
- **Perímetro:** 61 casos, 0 falhas.
- **Âncora e critérios:** âncora OK; critérios de aceite dos seis componentes passam e não há drift.
- **Navegador (painel do worktree, dados em diretório temporário):** a página Acervo carregou; um arquivo `.md` real foi enviado pelo campo de arquivo, entrou como `recebido`, foi analisado, teve direitos e revisão decididos pela tela e apareceu na busca com o caminho `ext:<hash>`. O arquivo ficou com permissão 0600 e nenhum temporário sobrou.
- **Achado no caminho:** o temporário do upload ficava na pasta quando a resposta já tinha saído; corrigido e coberto por teste.

## Não medido / limites

- **A busca externa** não tem fornecedor configurado: sem ele, o estado é "indisponível". A pesquisa de leitura pelo navegador é outra ferramenta, fora deste processo.
- **Reservado v2:** os vereditos com 60 tarefas ainda não existem; eles dependem da sua revisão pelo `revisar.py` e da política fixada.
- **Gateway com as flags ligadas:** não medido ainda; é o seu teste final.
- **`nv.py sincronizar`:** roda sobre as propostas reais só depois da aplicação (não rodei no repositório real, para não gravar histórico de centenas de propostas antigas de uma vez).
- **Sem fornecedor de busca, a condição `alexandria_externa`** só usa o acervo.
- **Correção de CORREÇÃO** ainda é heurística (a primeira citação do cabeçalho); foi a regra escolhida para não marcar entradas apenas mencionadas.

## Depois de aplicar

Reiniciar o painel (`systemctl --user restart painel-operacional.service`). Reindexar a Alexandria pela página Acervo (o índice de schema 1 é recusado). O teste final (voz, gateway com flags, skills, páginas) fica com você.

## Reversão

Revert do PR. Os dados ficam em `~/.local/share/agata/nova-versao/` e podem ser apagados sem efeito no repositório.
