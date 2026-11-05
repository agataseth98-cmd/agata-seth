# Proposta `nova-versao-lote5b-20261105`: limites do lote 5 resolvidos com alternativas gratuitas, e correção do CI

**O que é, em português comum:** duas coisas. Primeiro, o CI de hoje ficou vermelho (check `sdd`) depois do lote 5: a varredura de segredo procurava o repositório em `~/agata`, e no CI o checkout fica em outro lugar. A correção deriva a raiz do próprio arquivo. Segundo, os limites que eu tinha listado no lote 5 ganham a melhor alternativa gratuita disponível aqui:
- **Pesquisa externa:** a Wikipédia em português pela API pública (sem chave, sem custo). O resultado é evidência só de leitura; para entrar no acervo, você guarda e decide no painel.
- **PDF:** `pdftotext` quando existe; se não, `pypdf` num venv pessoal de usuário, sempre dentro do sandbox e sem rede. Sem nenhum dos dois, o PDF é recusado com motivo claro.
- **Falha do fornecedor:** vira estado `falhou`, com o motivo, sem derrubar a pesquisa.
- **Sete palavras ligadas às propostas reais:** `nv.py sincronizar` (63 objetos, as 50 aplicadas mais recentes, idempotente).

**Decisão sua (05/11/2026):** "resolva os Limites usando as melhores alternativas gratuitas possiveis, assinado."

## O que entra (19 arquivos, 626 linhas do diff)

- **Correção do CI (escopo P-8):** `redesign/router/sanitizar.py`, `redesign/router/seth_gateway.py`, `redesign/router/seth_verificador.py`. A raiz do checkout passa a ser `Path(__file__).resolve().parents[2]`, com `SETH_REPO` como sobrescrita. Na casa do Humano o valor não muda; no CI deixa de quebrar.
- **Alexandria:** `fornecedores.py` (Wikipédia, pela política de egresso), `extrair_pdf.py` (pypdf, dentro do sandbox), `aquisicao.py` (cadeia de leitura de PDF), `externa.py` (falha do fornecedor vira estado).
- **Avaliação:** a condição `alexandria_externa` usa a Wikipédia só quando `AGATA_EXTERNA_FORNECEDOR=wikipedia` está definido. Os testes automáticos continuam sem rede.
- **Nova versão:** `nv.py sincronizar` com limite de 50 propostas aplicadas no retroativo.
- **Painel:** na página Acervo, busca na Wikipédia e botão "Guardar no acervo (quarentena)"; ações `acervo_externa_pesquisar` e `acervo_externa_guardar`.
- **Testes e specs:** testes novos de PDF (pdftotext e venv), da Wikipédia (resposta simulada) e da falha do fornecedor; critérios e código listados na spec da Alexandria.
- **Referência:** `PROJETO_REFERENCIA.md` ganha o resumo do lote 5b.

## Ferramenta instalada fora do repositório (sem sudo)

Venv pessoal em `~/.local/share/agata/nova-versao/ferramentas/pdf-venv` com `pypdf` 6.21.4, instalado do PyPI. Nada é instalado no sistema nem no repositório. Pode ser removido sem efeito no código.

## Evidência (05/11/2026)

- **Pesquisa real:** "horta urbana compostagem" devolveu "Compostagem", "Horto Municipal de Teresópolis" e "Jardim Botânico de Santos", com endereços limpos (`pt.wikipedia.org`).
- **Testes num `HOME` vazio, como no CI:** 261 passam, 1 pulado (o teste do venv, que só existe na sua máquina).
- **Aceite por componente, num `HOME` vazio:** todos os componentes passam (project_kit, review_mesh, evidence_ledger, painel_operacional, nova_versao, alexandria, metacognicao, corpo, conexoes, avaliacao e sentidos). Âncora OK.
- **Selftests:** gateway com as flags da Seth ligadas e desligadas, ambos OK.
- **Sete palavras no repositório real:** 63 objetos, 0 erros; uma segunda rodada não grava nada novo.

## Não medido / limites que continuam

- **Vereditos do reservado v2:** dependem da sua revisão pelo `revisar.py`.
- **Gateway com as flags ligadas em produção:** é o seu teste final; eu só medi o selftest.
- **Sua voz no ouvido:** só medida com voz sintética.
- **Busca externa:** a Wikipédia cobre conteúdo enciclopédico, não notícias nem atualidade. Para atualidade, a pesquisa externa continua fraca; a suficiência já sinaliza isso.
- **Cobertura da busca:** a API devolve poucos resultados por consulta (limite de 5).

## Depois de aplicar

Reiniciar o painel. Confirmar que o check `sdd` do `main` fica verde. O `sincronizar` já foi executado no repositório real (é dado, não repositório).

## Reversão

Revert do PR. A correção do caminho de `SETH_REPO` continua igual na sua máquina.
