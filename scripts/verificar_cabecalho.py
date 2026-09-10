#!/usr/bin/env python3
"""Verifica se uma resposta cumpre o formato de cabeçalho da Regra 1 (REGRAS.md).
Uso: python3 scripts/verificar_cabecalho.py < resposta.txt
     echo "$RESPOSTA" | python3 scripts/verificar_cabecalho.py
     python3 scripts/verificar_cabecalho.py --max-entrada 156 < resposta.txt
Sem --max-entrada, tenta ler o número da última entrada em MEMÓRIAS.md (raiz do repo).
Saída: uma linha por falha achada, exit 1. Sem falhas: "OK", exit 0.
"""
import re
import sys
from pathlib import Path

def ultima_entrada_local() -> int | None:
    caminho = Path(__file__).resolve().parent.parent / "MEMÓRIAS.md"
    if not caminho.exists():
        return None
    numeros = re.findall(r"^\((\d+)\)", caminho.read_text(encoding="utf-8"), re.MULTILINE)
    # max(), não numeros[-1]: desde MEMÓRIAS (271) o arquivo cresce pelo
    # topo, então o último match físico passou a ser a entrada mais ANTIGA,
    # não a mais recente. max() é correto nos dois sentidos de leitura.
    return max((int(n) for n in numeros), default=None)

def verificar(texto: str, max_entrada_conhecida: int | None = None) -> list[str]:
    falhas = []

    # Âncora do bloco de prontidão = `modelo:`, não mais `Nonce:`.
    # A linha `Nonce:` SAIU do bloco em MEMÓRIAS (417) (TES-002 aposentado),
    # e este detector ficou para trás: medido em 09/09/2026, o bloco de 3
    # linhas CANÔNICO DE HOJE reprovava ("falta t=<n>") e o formato APOSENTADO
    # passava. Um linter que valida o formato morto e rejeita o vivo é pior
    # que linter nenhum -- e este roda em dois caminhos vivos
    # (redesign/mcp/servidor.py, tool `lint_header`, e redesign/grafo/tools.py).
    # `modelo:` é a âncora certa por texto de REGRAS, não por escolha minha:
    # REGRAS.md, "Carregar e formatos", diz literalmente "Misturar as duas
    # formas (`modelo:` junto com `t=`) é erro de formato" -- é o próprio
    # discriminador que as REGRAS nomeiam. Sobrevive à saída do Nonce e
    # mantém `Última entrada:`/`pronto.` como checagens de verdade (usar
    # `Última entrada:` como detector as tornaria vazias).
    # A âncora aceita as TRÊS formas que a Regra 1 autoriza, não só a primeira.
    # Achado em 10/09/2026 auditando um cabeçalho real da Seth: ela abriu com
    # `Agata · modelo não verificado · ...` -- forma LEGÍTIMA (Regra 1: "os dois
    # recursos de honestidade continuam: `família <X>, versão não verificada`
    # ou `modelo não verificado`") -- e a âncora, que eu tinha estreitado no dia
    # anterior para `Agata · modelo:`, não casou. O bloco caiu no ramo de
    # linha-de-turno e TRÊS violações de prontidão passaram ilesas.
    # Consertei o linter para o formato aposentado e o quebrei para dois
    # formatos vivos. Quem expôs isso foi o modelo auditado, não o auditor.
    tem_prontidao = bool(re.search(
        r"^\s*Agata\s*·\s*(?:modelo\s*:"
        r"|modelo\s+n[ãa]o\s+verificado"
        r"|fam[íi]lia\s+[^·]+?,\s*vers[ãa]o\s+n[ãa]o\s+verificada)",
        texto, re.MULTILINE | re.IGNORECASE))
    tem_t = re.search(r"t\s*[=≥]\s*\d+", texto)

    # Citação por SEÇÃO, não por número de linha: o "REGRAS.md:110" que estava
    # aqui já tinha apodrecido (a frase mora hoje noutra linha). Número de
    # linha envelhece em silêncio; nome de seção, não.
    if tem_prontidao and tem_t:
        falhas.append("mistura bloco de prontidão (modelo:) com t=<n> — REGRAS.md, 'Carregar e formatos': 'Misturar as duas formas (modelo: junto com t=) é erro de formato'")

    if tem_prontidao:
        if not re.search(r"última entrada\s*:", texto, re.IGNORECASE):
            falhas.append("bloco de prontidão sem 'Última entrada:'")
        if not re.search(r"\bpronto\.?\b|\bquebrado\s*:", texto, re.IGNORECASE):
            falhas.append("bloco de prontidão sem 'pronto.' ou 'quebrado: <o quê>'")

    # `sync: PASS` NU é o erro mais caro desta família, e passava aqui.
    # REGRAS, "'sync' tem preço": PASS exige as três medidas feitas ao vivo --
    # `sync: PASS · REGRAS=<hash8> · MEMÓRIAS=<hash8> · HEAD=<commit7>`.
    # Sem elas, "PASS" é afirmação, não verificação: quem lê o cabeçalho não
    # tem como conferir nada. Medido em 10/09/2026 num cabeçalho real da Seth:
    # a Máquina entregou a linha inteira no bloco de estado e ela copiou só a
    # palavra `PASS`, descartando a evidência -- e este linter deu OK.
    # FALHA e não AVISO de propósito: é exatamente a falha catalogada
    # "Dizer 'íntegro' por coerência de texto" ((66),(69)), com nome novo.
    m_sync = re.search(r"sync\s*:\s*([A-Za-zÀ-ÿ ]+)", texto, re.IGNORECASE)
    if m_sync:
        forma = m_sync.group(1).strip().lower()
        if forma.startswith("pass"):
            faltando = [c for c in ("REGRAS=", "MEMÓRIAS=", "HEAD=") if c not in texto]
            if faltando:
                falhas.append(
                    "sync: PASS sem as medidas que o PASS exige (falta "
                    + ", ".join(faltando)
                    + ") — REGRAS.md, \"'sync' tem preço\": PASS pede "
                    "`REGRAS=<hash8> · MEMÓRIAS=<hash8> · HEAD=<commit7>` medidos ao vivo. "
                    "Sem eles é `sync: não verificado`, não PASS."
                )
        elif forma.startswith("falha"):
            # Exigir só "algo depois do ·" era fraco demais: no cabeçalho de
            # uma linha o que vem depois costuma ser a DATA, e a checagem
            # passava sem motivo nenhum. Achado pelo próprio selftest ao
            # nascer. Agora: se o que segue `FALHA ·` começa com data/hora,
            # não é motivo -- é o resto do cabeçalho.
            m = re.search(r"sync\s*:\s*FALHA\s*·\s*(.{0,40})", texto, re.IGNORECASE | re.DOTALL)
            depois = (m.group(1).strip() if m else "")
            parece_data = bool(re.match(r"^(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{1,2}:\d{2})", depois))
            if not depois or parece_data:
                falhas.append("sync: FALHA sem dizer o que diverge em 1 linha (REGRAS, 'Carregar e formatos') — o que vem depois do `·` é a data, não o motivo")
        elif "não verificado" in forma or "nao verificado" in forma:
            if not re.search(r"lacuna\s*:", texto, re.IGNORECASE):
                falhas.append("sync: não verificado sem `lacuna: <motivo>` (REGRAS, 'Carregar e formatos')")
    else:
        if not tem_t:
            falhas.append("falta t=<n> (ou t≥<n>) no cabeçalho")
        else:
            janela = texto[tem_t.end():tem_t.end() + 60]
            if not re.search(r"contado no contexto|prefixo compactado|contador mecânico", janela):
                falhas.append("t=<n> sem qualificador de contagem (contado no contexto / contador mecânico / prefixo compactado)")

    m_entrada = re.search(
        r"última entrada[^(]{0,20}\((\d+)\)|MEMÓRIAS\s*\((\d+)\)|\((\d+)\)\s*DIÁRIO",
        texto, re.IGNORECASE,
    )
    if not m_entrada:
        falhas.append("não cita a última entrada de MEMÓRIAS (número + referência)")
    elif max_entrada_conhecida is not None:
        n = int(next(g for g in m_entrada.groups() if g))
        if n > max_entrada_conhecida:
            falhas.append(
                f"entrada citada como última é ({n}), maior que a última real conhecida ({max_entrada_conhecida}) "
                f"— implausível, confira antes de aceitar (MEMÓRIAS (157))"
            )

    return falhas


# --- selftest ---------------------------------------------------------------
# Este linter já esteve errado DUAS vezes em dois dias: em (421) a âncora ficou
# no `Nonce:` aposentado (reprovava o formato vivo, aprovava o morto), e em
# (422) a âncora nova ficou cega a `modelo não verificado`, que a Regra 1
# autoriza. As duas vezes quem descobriu foi um humano ou o modelo auditado,
# nunca um teste -- porque não havia teste. Agora há. MEMÓRIAS (424).
_CASOS = [
    # (nome, texto, deve_passar)
    ("prontidão completa",
     "Agata · modelo: X · sync: PASS · REGRAS=aaaaaaaa · MEMÓRIAS=bbbbbbbb · HEAD=ccccccc · "
     "2026-01-01 10:00 -03 (relógio da Máquina)\nÚltima entrada: (423) t\npronto.\n", True),
    ("prontidão com modelo não verificado",
     "Agata · modelo não verificado · sync: PASS · REGRAS=aaaaaaaa · MEMÓRIAS=bbbbbbbb · HEAD=ccccccc · "
     "2026-01-01 10:00 -03\nÚltima entrada: (423) t\npronto.\n", True),
    ("prontidão com família não verificada",
     "Agata · família gemini, versão não verificada · sync: PASS · REGRAS=aaaaaaaa · "
     "MEMÓRIAS=bbbbbbbb · HEAD=ccccccc · 2026-01-01 10:00 -03\nÚltima entrada: (423) t\npronto.\n", True),
    ("linha de turno legítima",
     "Agata · X · t=7 (contado no contexto) · 2026-01-01 10:00 -03 · MEMÓRIAS (423)\n", True),
    ("REGRESSAO (424): sync PASS nu",
     "Agata · modelo: X · sync: PASS · 2026-01-01 10:00 -03\nÚltima entrada: (423) t\npronto.\n", False),
    ("sync FALHA sem motivo",
     "Agata · modelo: X · sync: FALHA · 2026-01-01 10:00 -03\nÚltima entrada: (423) t\npronto.\n", False),
    ("sync não verificado sem lacuna",
     "Agata · modelo: X · sync: não verificado · 2026-01-01 10:00 -03\nÚltima entrada: (423) t\npronto.\n", False),
    ("REGRESSAO (422): mistura as duas formas",
     "Agata · modelo: X · t=2 · sync: PASS · REGRAS=aaaaaaaa · MEMÓRIAS=bbbbbbbb · HEAD=ccccccc\n"
     "Última entrada: (423) t\npronto.\n", False),
    ("prontidão sem pronto./quebrado:",
     "Agata · modelo: X · sync: PASS · REGRAS=aaaaaaaa · MEMÓRIAS=bbbbbbbb · HEAD=ccccccc\n"
     "Última entrada: (423) t\n", False),
    ("t= sem qualificador",
     "Agata · X · t=7 · 2026-01-01 10:00 -03 · MEMÓRIAS (423)\n", False),
    ("entrada implausível (maior que a real)",
     "Agata · X · t=7 (contado no contexto) · MEMÓRIAS (99999)\n", False),
]


def _selftest() -> int:
    ok = 0
    for nome, texto, deve_passar in _CASOS:
        falhas = verificar(texto, 500)
        passou = (not falhas) == deve_passar
        ok += passou
        marca = "PASS " if passou else "FALHA"
        extra = "" if passou else f"   -> {falhas or ['(passou, mas devia reprovar)']}"
        print(f"{marca} {nome}{extra}")
    print(f"\nSELFTEST {'OK' if ok == len(_CASOS) else 'FALHOU'} -- {ok}/{len(_CASOS)}")
    return 0 if ok == len(_CASOS) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())

    max_entrada = ultima_entrada_local()
    if "--max-entrada" in sys.argv:
        i = sys.argv.index("--max-entrada")
        max_entrada = int(sys.argv[i + 1])

    texto = sys.stdin.read()
    falhas = verificar(texto, max_entrada)
    if not falhas:
        print("OK")
        sys.exit(0)
    for f in falhas:
        print(f"FALHA: {f}")
    sys.exit(1)
