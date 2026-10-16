# PROJETO — detalhe movido de PROJETO.md (16/10/2026)

**Status deste arquivo: CONSULTA, não norma.** Está fora do escopo do P-8 (`_p8_eh_comportamento`) e não é de leitura obrigatória no carregamento. Toda obrigação que vale sempre continua no resumo do `PROJETO.md`, em `REGRAS.md` ou em `PROTOCOLOS.md`; em divergência, esses vencem. Mudar uma obrigação aqui não a muda: proponha a mudança no arquivo protegido.

Texto integral, sem alteração, retirado de `PROJETO.md` para o teto de 48.000 B. O que ficou no PROJETO é um resumo com ponteiro para este arquivo. Origem: `PROJETO.md` no commit da7a10ab61980be52c15278f1502e211669e9192.

### Fronteira mecânica — `subir_esfera_projeto.py`
O único cano de código entre o sistema e o Drive. Um arquivo por invocação; não encadeia, não escreve em canon, não decide nada. Aborta na primeira checagem que falhar, nesta ordem:
1. **Caminho** — `realpath` do alvo dentro de `memoria/missoes/agata-sistema/`; symlink para fora é resolvido e barrado.
2. **Esfera pessoal** — `realpath` que toque `memoria/missoes/segunda-camada/` aborta.
3. **Canon** — basename em `{REGRAS.md, PROJETO.md, MEMÓRIAS.md, PROJETO_REFERENCIA.md}` aborta, mesmo sendo cópia.
4. **É arquivo** — não diretório.
5. **Extensão** — só `.md .txt .csv .json .yaml .yml .log`.
6. **Tamanho** — acima de 10 MiB ou 0 byte aborta.
7. **UTF-8** — binário aborta.
8. **Varredura de segredo** — ~16 padrões (credenciais Google/OAuth, PEM, AWS, `sk-…`, tokens GitHub/Slack, connection string com senha, header `Authorization`, par chave/valor genérico, nomes de `*_API_KEY` conhecidos, CPF, CNPJ). Um match aborta — **nada é enviado**.

Só depois das 8: `refresh_token` → access token → pasta `agata-sistema` no Drive (escopo `drive.file`) → upload multipart → `[carimbo] nome drive_id=… tamanho <- caminho` em `memoria/missoes/agata-sistema/upload.log`. **Não é allowlist**; liberar só certos arquivos seria P-8 separada. Limitação assumida (286): formato de segredo que nenhum padrão pega, posto em `agata-sistema/` de propósito e enviado à mão — a varredura é rede contra acidente, não classificador.


### Índice derivado do canon público e export pro Drive
(296)/(298)/(299)/(300). Camada de consulta separada do vault, gerada só do canon público (`REGRAS.md`, `PROTOCOLOS.md`, `FALHAS.md`, `PROJETO.md` e as camadas de MEMÓRIAS), nunca de `memoria/missoes/`.
- `scripts/gerar_indice_derivado.py` → `memoria/missoes/agata-sistema/derivado/{indice.md, manifesto.md}`: as camadas normativas e o PROJETO na íntegra + os títulos das entradas de MEMÓRIAS, mais recente primeiro. Reconstrução byte a byte antes de gravar — um byte fora do boilerplate + canon aborta. `manifesto.md` traz o sha256 das fontes; determinístico (carimbo de commit).
- `scripts/consultar_indice.py <palavras>` extrai trechos do `indice.md` em texto plano, rotulados pela fonte certa (611) — é como o executor local entrega recorte a um modelo em nuvem.
- **Export:** `scripts/preparar_export_indice.py` mascara nomes de variável de ambiente como `[variável de ambiente]` (a varredura de segredo abortaria no nome pelado; o scanner não se afrouxa) e só grava se o resultado passar em todos os padrões de `PADROES_SEGREDO`. Fluxo: `gerar_indice_derivado.py` → `preparar_export_indice.py` → `subir_esfera_projeto.py memoria/missoes/agata-sistema/derivado/indice_export.md` (+ `manifesto.md` como carimbo de proveniência).
- **Automático:** o `.githooks/post-commit` refaz `indice.md`/`manifesto.md` a cada commit (301) e envia ao Drive só quando o sha256 do `indice.md` muda — marcador em `~/.cache/agata/indice-export-ultimo-sha` (457). Fail-soft: falha vira `AVISO`, nunca bloqueia o commit.

