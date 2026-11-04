# Spec — Corpo operacional (fotografia e saúde)

Componente da nova versão. Spec-mãe: `redesign/nova_versao/spec/spec.md`. Origem: Experimento GPT, (034)–(036), `inventario-servicos-agata-2026-11-04.md` e `auditoria-2026-11-04/coletar_evidencias.py`, promovido aqui a componente. "Guardião do próprio corpo" quer dizer monitorar e reduzir escopo, nunca autopreservação nem agir sem autorização.

## Jornadas críticas

1. O Humano clica em "Fotografar agora" no painel e vê serviços, recursos e saúde com data e prazo de revalidação.
2. Um modelo consulta a última fotografia antes de escolher rota e não deduz saúde do catálogo.

## Contrato

- `fotografar.fotografar()` só lê: `systemctl --user show` das `UNIDADES`, `ss -ltnH`, `/proc/meminfo`, `os.getloadavg`, `/sys/class/thermal`, `shutil.disk_usage` e GET em Ollama `/api/tags`, OmniRoute `/api/models` e `/api/combos`. Nunca faz POST, nunca reinicia, nunca gera texto.
- A tabela de modelos separa `instalado`, `anunciado`, `elegivel`, `testado`, `em_fila` e `pronto`. `testado`, `elegivel` e `pronto` ficam `null` até haver medição própria (lote 2).
- Cada fotografia tem `quando` e `revalidar_ate` (1 h) e é acrescentada em `AGATA_NV_DIR/corpo/fotografias.jsonl`.
- `saude.classificar(foto)` devolve `normal`, `pressionado`, `degradado`, `isolado` ou `indisponivel`, com motivos. Os limiares (`LIMIARES`) são provisórios e mudá-los é decisão do Humano. Dado ausente vai para `nao_medido`. Unidade sob demanda inativa (decisão de 29/10) não rebaixa o estado.

## Critérios de aceite

- [ ] a fotografia só lê com GET e separa os campos do inventário
- [ ] a saúde tem cinco estados e serviço sob demanda não rebaixa

## Desenho e alternativas

Biblioteca padrão, sem agente nem timer novo: fotografia sob pedido (sistema sob demanda, 29/10). Descartado: monitor contínuo (o inventário datado não é monitor, §5).

## Implementação e testes

`fotografar.py` e `saude.py`; testes em `tests/test_corpo.py`, com `urlopen` e comandos substituídos.

## Migração e reversão

Sem dados a migrar; o JSONL pode ser apagado.

## Riscos e dependências

Temperatura depende de `/sys/class/thermal` e pode faltar (fica não medido). Medido em 04/11 às 16:38: estado `normal`; gateway, verificador, embeddings, Laya e painel inativos (sob demanda).

## Código

- `fotografar.py`
- `saude.py`
- `tests/`
