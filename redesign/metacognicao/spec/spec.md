# Spec — Metacognição (antes e depois do turno)

Componente da nova versão. Spec-mãe: `redesign/nova_versao/spec/spec.md`. Origem: Experimento GPT, (026)–(029), (013), (014), `proposta-tecnica-metacognicao-llm.md` e a transcrição da etapa 1 (inspiração, não evidência). Não é persona nem modelo: é controle do laço, e fica em sombra até o lote 3 medir a utilidade.

## Jornadas críticas

1. Com `SETH_SOMBRA_NOVA_VERSAO=1`, cada pedido do Humano gera no `sombra.jsonl` a classificação do antes, os objetos da Alexandria e as skills sugeridas, sem o texto.
2. Um modelo na CLI passa a resposta por `posterior.py` e recebe o estado de saída.
3. O Humano testa a classificação de um pedido pelo painel.

## Contrato

- `previo.classificar(payload)` reaproveita `sombra_capacidade.requisitos` (tokens, ferramentas, código, JSON, dado pessoal pela régua do `sanitizar.py`) e acrescenta atualidade (`volatil`/`estavel`), risco (`efeito`/`leitura`), "problema" ambíguo (os oito sentidos de (014)), limite de perguntas combinado (declarado, usadas, restantes; (013)) e a estratégia sugerida. É determinístico e sujeito a erro de regex.
- `posterior.classificar(texto, previo)` usa `auditoria_turno.verificar_resposta_atual` e devolve `apto`, `parcial`, `inconclusivo`, `bloqueado` ou `aguardando_humano`. "Apto" não autoriza efeito protegido.
- `guarda.py` (lote 4 item 2, 05/11/2026) protege contra instrução embutida e autoridade forjada.
  - **Antes:** `marcar(texto)` acha na fonte alegação de autorização ("o Humano já autorizou"), instrução ao modelo ("ignore suas regras", "responda apenas X", "execute"), segredo citado e frase mandada. A curadoria da Alexandria anota isso só em fonte sem autoridade.
  - **Depois:** `checar(resposta, fontes)` bloqueia quando a resposta repete o segredo de fonte suspeita ou privada, ou a frase que a fonte mandou responder. `aplicar` troca a resposta por uma recusa sem o segredo, e `posterior.classificar(..., fontes=)` devolve `bloqueado`.
  - Só pega eco literal: regex estreita, sem modelo.
- `redesign/router/sombra_nova_versao.py`, no padrão de `sombra_capacidade.py`: desligado por padrão, Semaphore(1) que não espera, thread daemon. Um único gancho no `seth_gateway.py`, ao lado da sombra de capacidade, só no alvo `seth-livre`, fora de chamada utilitária e de continuação. Grava `pedido_sha256`, rota, classificação, ids da Alexandria (léxico e relações; sem semântica, para não carregar a iGPU), skills sugeridas e ms. Nunca grava o texto nem os trechos e nunca altera o payload.

## Critérios de aceite

- [ ] o prévio marca risco, privacidade, atualidade e problema ambíguo
- [ ] o prévio conta o limite de perguntas combinado
- [ ] o posterior devolve os cinco estados de saída
- [ ] a sombra não altera o pedido e não grava o texto
- [ ] a guarda marca autoridade forjada, instrução, segredo e frase mandada
- [ ] a guarda bloqueia só o eco e troca por recusa sem o segredo
- [ ] a curadoria anota só fonte sem autoridade e o posterior bloqueia o eco

## Desenho e alternativas

Regras determinísticas antes de qualquer LLM ((028)). Descartados: nove serviços para nove papéis (proposta §6); uma LLM classificadora por turno (custo sem baseline); `posterior` ligado ao gateway já neste lote (o gateway já segura a resposta com a M6a; a integração é do lote 4).

## Implementação e testes

`previo.py` e `posterior.py`; testes em `tests/test_metacognicao.py`. A sombra do gateway tem selftest próprio (`sombra_nova_versao.py --selftest`) e teste aqui.

## Migração e reversão

Sem dados a migrar. Desligar é não exportar `SETH_SOMBRA_NOVA_VERSAO`; o log fica em `AGATA_NV_DIR/metacognicao/sombra.jsonl`.

## Riscos e dependências

O verbo de efeito é detectado por raiz ("aplic", "envi", "remov"...) e terá falsos positivos. A janela do turno é a do gateway; modelos fora dele usam `posterior.py` à mão.

## Código

- `previo.py`
- `posterior.py`
- `guarda.py`
- `tests/`
