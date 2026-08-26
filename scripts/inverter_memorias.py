#!/usr/bin/env python3
"""Migração única (MEMÓRIAS (271)): inverte a ordem de leitura de MEMÓRIAS.md.

Antes: mais antiga primeiro, mais recente acrescentada no fim físico.
Depois: mais recente logo após o marcador ENTRADAS-NOVAS (topo do corpo),
mais antiga no fim físico.

Não edita nem apaga nenhum byte de entrada existente -- só reordena os
blocos (49)..(n) (reversão simples da lista, preserva ordem relativa
correta mesmo com números reaproveitados como (134)/(215)) e reescreve o
cabeçalho de apresentação (permitido por Regra 7 -- forma/apresentação é
livre; conteúdo já registrado, nunca). O bloco "Migrado de DIÁRIO.md" não
muda de posição: já era o conteúdo mais antigo, a convenção nova já o
queria no fim.

Roda uma vez, contra o HEAD atual de MEMÓRIAS.md. Recusa rodar de novo se
o marcador já existir (idempotência). Sempre escreve backup antes de
tocar no arquivo. Depois de rodar, valide com:
  python3 scripts/verificar_migracao_memorias.py <backup> MEMÓRIAS.md

Uso: inverter_memorias.py <caminho MEMÓRIAS.md> <caminho backup>
"""
import re
import sys
from pathlib import Path

MARCADOR_MIGRADO = "## Migrado de DIÁRIO.md"
MARCADOR_ENTRADAS = "<!-- ENTRADAS-NOVAS:AQUI"
PADRAO_ENTRADA = re.compile(
    r"^\(\d+\) (?:DIÁRIO|CONSELHO|MOD[^—]*|CORREÇÃO) — \d{2}/\d{2}/\d{4}",
    re.MULTILINE,
)

NOVO_CABECALHO = """# MEMÓRIAS.md — Sistema Agata

**Você está lendo o arquivo de história. É append-only: nada se apaga, nada se edita — só se acrescenta.**
Desde a entrada (271) (26/08/2026), entrada nova entra logo abaixo do marcador `ENTRADAS-NOVAS` abaixo — mais recente primeiro, pra ler o estado herdado sem varrer a história inteira. Antes de (271) a ordem era o oposto (mais antiga primeiro, mais recente acrescentada no fim físico); motivo, autorização do Humano e portão das três perguntas cumprido: ver a própria entrada (271), logo abaixo do marcador. Correção nunca é edição — é entrada nova apontando a que corrige. Para o estado atual (não o histórico), leia PROJETO.md.

## Como ler este arquivo (para modelos)
- **Não leia tudo.** Leia o TOPO, logo abaixo do marcador — é o estado herdado mais recente. O resto é lastro, consultável por busca quando um número de entrada for citado.
- **Entrada citada por número** — `(n)` — pode ser buscada diretamente **a partir de (49)**. Toda regra e todo bug remetem a um número; é assim que se checa se algo é fato ou lembrança.
- **Cópia recebida pode estar atrás do canon.** Antes de escrever qualquer entrada nova, confira o TOPO do remoto (logo abaixo do marcador — não o fim físico, que agora é a história mais antiga). Se não puder conferir, diga até onde a sua cópia vai e não numere nada.
- **Grafias antigas do nome** (com acento, com "h") aparecem na história migrada. Não se corrigem: história não se edita. A grafia canônica hoje é **Agata**.

## Os quatro tipos de bloco
- `(n) DIÁRIO` — fato coletivo, comum a todos.
- `(n) CONSELHO` — entrada, saída ou discordância de modelo, mais o veredito do Humano.
- `(n) MOD <modelo>` — memória pessoal. **Silo:** cada modelo deveria receber só os MODs com o seu `modelo-alvo`. Consentimento de publicação é por trecho, com data; o default é privado.
  *Hoje o silo é norma, não mecanismo: a hidratação é arquivo único e sem filtro. Recebeu MOD alheio, diga em uma linha e não use o conteúdo.*
- `(n) CORREÇÃO` — corrige uma entrada anterior sem editá-la; aponta o número que corrige.

**Correção sobre este preâmbulo (MEMÓRIAS (109)): a numeração NÃO é única globalmente antes de (49).** História migrada de mais de uma origem reinicia número por número — "(2)" sozinho aparece pelo menos 4 vezes, em datas diferentes. A partir de (49) a numeração é única e contínua; antes disso, cite por número **e data**. O bloco migrado (mais antigo, no fim físico deste arquivo) segue colado verbatim, sem editar uma vírgula — isso não muda; o que mudou nesta migração foi só a posição do corpo (49)+ e a direção de leitura.

---

"""


def dividir(texto: str):
    """Mesma lógica de scripts/verificar_migracao_memorias.py -- posição-
    agnóstica de propósito, pra ler tanto o formato antigo (migrado antes
    das entradas) quanto o novo (migrado depois). Aqui só roda contra o
    arquivo AINDA no formato antigo (é o que esta migração consome), mas
    fica consistente com o verificador em vez de assumir a posição."""
    matches = list(PADRAO_ENTRADA.finditer(texto))
    if not matches:
        raise SystemExit("nenhuma entrada '(n) TIPO — data' encontrada -- formato inesperado, abortando")
    idx_migrado = texto.find(MARCADOR_MIGRADO)
    if idx_migrado == -1:
        raise SystemExit("bloco 'Migrado de DIÁRIO.md' não encontrado -- abortando")
    cortes = sorted({m.start() for m in matches} | {idx_migrado}) + [len(texto)]
    bloco_migrado = None
    entradas = []
    for inicio, fim in zip(cortes, cortes[1:]):
        pedaco = texto[inicio:fim]
        if inicio == idx_migrado:
            bloco_migrado = pedaco
        else:
            entradas.append(pedaco.rstrip("\n"))
    if bloco_migrado is None:
        raise SystemExit("bloco migrado não isolado corretamente -- abortando")
    return bloco_migrado, entradas


def main():
    if len(sys.argv) != 3:
        print("uso: inverter_memorias.py <MEMÓRIAS.md> <caminho backup>", file=sys.stderr)
        sys.exit(2)
    caminho = Path(sys.argv[1])
    caminho_backup = Path(sys.argv[2])

    original = caminho.read_text(encoding="utf-8")

    if MARCADOR_ENTRADAS in original:
        raise SystemExit("marcador ENTRADAS-NOVAS já presente -- arquivo já migrado, não rodo de novo (idempotência)")

    caminho_backup.write_text(original, encoding="utf-8")

    bloco_migrado, entradas = dividir(original)
    entradas_invertidas = list(reversed(entradas))

    corpo = "\n\n".join(entradas_invertidas) + "\n"
    marcador_linha = (
        f"{MARCADOR_ENTRADAS} -- não editar esta linha à mão; ancora o controle P-5 em "
        f"scripts/perimetro.sh; entrada nova sempre logo abaixo dela, nunca acima) -->"
    )

    novo = (
        NOVO_CABECALHO
        + marcador_linha
        + "\n\n"
        + corpo
        + "\n---\n\n"
        + bloco_migrado
    )

    caminho.write_text(novo, encoding="utf-8")
    print(f"reescrito: {caminho} ({len(entradas)} entradas invertidas, bloco migrado preservado no fim)")
    print(f"backup: {caminho_backup}")
    print("valide agora com: python3 scripts/verificar_migracao_memorias.py "
          f"{caminho_backup} {caminho}")


if __name__ == "__main__":
    main()
