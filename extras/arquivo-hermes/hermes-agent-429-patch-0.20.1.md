# Patch do handler de 429, versionado fora do vendorizado

Risco 102 do PROJETO.md ("o patch do handler de 429 vive em repositório
vendored sem backup") já se materializou uma vez, em MEMÓRIAS (150),
quando o update `hermes-agent` 0.18.0→0.20.1 comeu o patch e ele teve que
ser remanejado manualmente. Este arquivo é a cópia reproduzível fora do
diretório que qualquer update futuro sobrescreve.

## Onde vive o original

`~/.hermes/hermes-agent` — checkout git real de `github.com/NousResearch/hermes-agent`,
não cópia solta. Confirmado em MEMÓRIAS (181): `origin` = `https://github.com/NousResearch/hermes-agent.git`.

## Base do patch

- Commit checked out: `1f8fdc7bd824c8d07e3cefe109bd96425ec3171f`
- `pyproject.toml` declara `version = "0.20.1"`
- Único arquivo modificado no working tree: `run_agent.py`
- Regerado em 15/08/2026 (`git diff -- run_agent.py`), idêntico ao lido em (181)

## O patch

Ver `hermes-agent-429-patch-0.20.1.diff` neste diretório. Resumo: no
tratamento de erro de rate limit (429), o handler lia `response.text`
sem antes consumir `response.read()` — em algumas respostas HTTP
streamed isso retornava snippet vazio, escondendo o corpo real do erro
429. O patch consome o stream primeiro, quando o objeto expõe `.read()`.

## Como reaplicar depois de um update que apague o patch

```sh
cd ~/.hermes/hermes-agent
git apply ~/agata/docs/hermes-agent-429-patch-0.20.1.diff
# ou, se o contexto ao redor da linha 2610 tiver mudado no update:
# reaplicar manualmente lendo o diff acima, mesma lógica (response.read()
# antes de response.text), e regerar este arquivo com a nova base.
```

## Como reverificar que ainda está vivo

```sh
cd ~/.hermes/hermes-agent
git status --short          # deve mostrar "M run_agent.py"
git diff -- run_agent.py    # deve bater com o .diff deste diretório
```

sha256 do `.diff` nesta revisão: `2cc4cd5555ace0581782a3795ae73b2e30e87559002105f38f6df16b5fd37594`
