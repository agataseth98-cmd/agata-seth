# Proposta `alexandria-hierarquia-20261106`: hierarquia de buscas, escolhida caso a caso (lote 9)

**Pedido do Humano (06/11/2026):** a função da Alexandria é organizar a hierarquia de buscas e o conhecimento. Todas as formas de pesquisa devem estar disponíveis e ser escolhidas caso a caso.

**O que muda:**
- `redesign/alexandria/pesquisa.py` (novo): três formas de pesquisa, cada uma disponível:
  - `lexico`: texto no acervo, com relações;
  - `semantica`: sentido, ferramenta secundária (decisão (327));
  - `externa`: evidência efêmera, que nunca entra no índice.
- Modos:
  - `auto`: começa pelo léxico. Só acrescenta a semântica se a suficiência (C2) não bastar, e a externa se ainda faltar e estiver configurada. Cada etapa registra o motivo.
  - `lexico`, `semantica`, `externa`: só o que foi pedido.
  - `todos`: roda tudo, para comparar.
- Spec e critérios de aceite da Alexandria atualizados (seção "Lote 9"), e o novo arquivo listado em "Código", para a âncora.

**Medido:** 83 testes verdes em `redesign/alexandria` e `redesign/nova_versao/tests` (incluindo 5 novos). A âncora da Alexandria está OK.

**Não medido:** a qualidade da escolha automática em consultas reais. Isso depende de medir com perguntas do acervo.

**Ainda não ligado:** a interface no painel, e a externa real (sem fornecedor configurado, o modo externo fica indisponível).

**Reversão:** remover `pesquisa.py`, seus testes e a seção do spec.
