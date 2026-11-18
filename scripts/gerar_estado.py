#!/usr/bin/env python3
"""Gera ESTADO.md: o estado vivo do Agata a partir de fontes reais (componente projeto-indice, 12/11/2026).

Decisão do Humano (cache do Conselho, entradas 521 e 522): o estado sai do PROJETO.md e vira arquivo
gerado pela Máquina, hidratado aos modelos, fora do canon. Versionado (a nuvem lê por URL pinada em SHA)
e sem data de geração nem SHA de commit: a mesma fonte dá o mesmo arquivo, então uma diferença entre
duas gerações é sempre mudança de fonte.

Fontes (todas tracked):
  config/portas-agata.txt            portas e bind esperado
  config/modelos-gratuitos.md        seção "Confirmado funcionando" (linhas sem ~~)
  config/servicos-agata.txt          manifesto de serviços (fonte do P-9)
  redesign/systemd/*.service|*.timer unidades com WantedBy/PartOf de agata.target (conferência)
  propostas/*.diff, propostas/APROVADO-*, propostas/aplicadas/   lotes
  ONDE_ESTAMOS.md                    seção "## Bugs e testes abertos" (bugs)

Uso:
  python3 scripts/gerar_estado.py                 gera ESTADO.md na raiz do repositório
  python3 scripts/gerar_estado.py --verificar     código 1 se o ESTADO.md em disco não é o gerado agora
  python3 scripts/gerar_estado.py --raiz CAMINHO  usa outra raiz (testes)
  python3 scripts/gerar_estado.py --imprimir      escreve o resultado na saída padrão
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_SAIDA = "ESTADO.md"
TAMANHO_NOTA = 100
CABECALHO = (
    "# ESTADO (gerado)\n\n"
    "<!-- ARQUIVO GERADO por scripts/gerar_estado.py -- não editar à mão. O pre-commit regenera quando "
    "uma fonte muda. Sem data de geração e sem SHA de commit: a mesma fonte dá o mesmo arquivo. "
    "Fontes: config/portas-agata.txt, config/modelos-gratuitos.md (Confirmado funcionando), "
    "config/servicos-agata.txt, redesign/systemd (WantedBy/PartOf agata.target), propostas/, "
    "ONDE_ESTAMOS.md (Bugs e testes abertos), PROTOCOLOS.md (mapa de seções). Prosa de estado que não sai daqui: "
    "extras/projeto-detalhe/estado-de-fundo-12-11.md. -->\n"
)


def _ler(raiz: Path, rel: str) -> str:
    caminho = raiz / rel
    return caminho.read_text(encoding="utf-8") if caminho.is_file() else ""


def portas(raiz: Path) -> list[tuple[str, str, str]]:
    saida = []
    for linha in _ler(raiz, "config/portas-agata.txt").splitlines():
        if not linha.strip() or linha.lstrip().startswith("#") or linha.count("|") != 2:
            continue
        porta, nome, bind = (campo.strip() for campo in linha.split("|"))
        saida.append((porta, nome, bind))
    return sorted(saida, key=lambda t: int(t[0]))


def modelos_confirmados(raiz: Path) -> list[tuple[str, str]]:
    saida: list[tuple[str, str]] = []
    dentro = False
    for linha in _ler(raiz, "config/modelos-gratuitos.md").splitlines():
        if linha.startswith("## "):
            dentro = linha.startswith("## Confirmado funcionando")
            continue
        if not dentro or not linha.startswith("| `"):
            continue
        celulas = linha.split("|")
        m = re.match(r"^\s*`([^`]+)`\s*$", celulas[1]) if len(celulas) > 3 else None
        if not m:
            continue
        nota = celulas[3].strip() if len(celulas) > 3 else ""
        if len(nota) > TAMANHO_NOTA:
            nota = nota[: TAMANHO_NOTA - 1].rstrip() + "…"
        saida.append((m.group(1), nota))
    return saida


def servicos(raiz: Path) -> list[dict[str, str]]:
    saida = []
    for linha in _ler(raiz, "config/servicos-agata.txt").splitlines():
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        campos = linha.split("|")
        if len(campos) != 5:
            raise ValueError(f"config/servicos-agata.txt: linha com {len(campos)} campos (esperado 5): {linha[:80]!r}")
        unidade, escopo, porta, p9, origem = (c.strip() for c in campos)
        if escopo not in {"usuario", "sistema", "docker"} or p9 not in {"sim", "nao"}:
            raise ValueError(f"config/servicos-agata.txt: escopo ou p9 inválido em {unidade!r}")
        saida.append({"unidade": unidade, "escopo": escopo, "porta": porta, "p9": p9, "origem": origem})
    return saida


def unidades_no_repo(raiz: Path) -> list[str]:
    saida = []
    pasta = raiz / "redesign" / "systemd"
    if not pasta.is_dir():
        return saida
    for arq in sorted(pasta.iterdir()):
        if arq.suffix not in {".service", ".timer"} or not arq.is_file():
            continue
        if any(re.match(r"^(WantedBy|PartOf)=agata\.target\s*$", l) for l in arq.read_text(encoding="utf-8").splitlines()):
            saida.append(arq.name)
    return saida


def propostas(raiz: Path) -> tuple[list[str], int]:
    pasta = raiz / "propostas"
    if not pasta.is_dir():
        return [], 0
    abertas = sorted(
        p.stem for p in pasta.glob("*.diff") if not (pasta / f"APROVADO-{p.stem}").exists()
    )
    aplicadas = len(list((pasta / "aplicadas").glob("*.diff"))) if (pasta / "aplicadas").is_dir() else 0
    return abertas, aplicadas


def bugs(raiz: Path) -> str:
    linhas = _ler(raiz, "ONDE_ESTAMOS.md").splitlines()
    saida: list[str] = []
    dentro = False
    for linha in linhas:
        if linha.startswith("## "):
            if dentro:
                break
            dentro = linha.startswith("## Bugs e testes abertos")
            continue
        if dentro:
            saida.append(linha)
    texto = "\n".join(saida).strip()
    if texto:
        return texto
    # ONDE_ESTAMOS.md não tem essa seção hoje (12/11/2026). Em vez de criar registro novo aqui,
    # aponta para a prosa que guarda os bugs abertos, com a data de cada medição.
    return ("(ONDE_ESTAMOS.md não tem a seção 'Bugs e testes abertos'. Os bugs abertos e os testes "
            "estão em extras/projeto-detalhe/estado-de-fundo-12-11.md, seção 'Estado dos bugs e dos testes'.)")


def mapa_protocolos(raiz: Path) -> str:
    """Mapa das seções de PROTOCOLOS.md, pelo mesmo gerador do mapa do PROJETO (12/11/2026, decisão do Humano:
    PROTOCOLOS entra na hidratação como mapa + busca, não inteiro). Sem data, sem SHA."""
    texto = _ler(raiz, "PROTOCOLOS.md")
    if not texto:
        return "(PROTOCOLOS.md ausente nesta raiz.)"
    spec = importlib.util.spec_from_file_location("gerar_mapa_projeto", RAIZ / "scripts" / "gerar_mapa_projeto.py")
    mapa_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mapa_mod)
    linhas = mapa_mod.gerar(texto, nome="PROTOCOLOS.md").splitlines()
    inicio = next(i for i, l in enumerate(linhas) if l.startswith("## "))
    corpo = ["#" + l if l.startswith(("## ", "### ")) else l for l in linhas[inicio:]]
    orientacao = (
        "Este mapa é o índice de PROTOCOLOS.md, o arquivo do COMO (mecanismos, procedimentos, formatos). "
        "O texto de uma seção não entra nesta hidratação: abra PROTOCOLOS.md no número da linha, ou busque o "
        "título (query_canon com doc PROTOCOLOS e grep pelo título). Antes de responder, leia a seção "
        "\"Carregar e formatos\": ali está a forma exata do cabeçalho e da linha de turno."
    )
    return orientacao + "\n\n" + "\n".join(corpo).rstrip() + "\n"


def conferencia(raiz: Path) -> list[str]:
    declaradas = {s["unidade"] for s in servicos(raiz)}
    return [u for u in unidades_no_repo(raiz) if u not in declaradas]


def renderizar(raiz: Path = RAIZ) -> str:
    partes = [CABECALHO]
    partes.append("## Serviços (boot)\n")
    partes.append("Manifesto: config/servicos-agata.txt. P-9 sim: o perímetro avisa se a unidade cair; P-9 não: listada; avisa só se 'failed'.\n")
    for s in servicos(raiz):
        u, esc, porta, p9, origem = s["unidade"], s["escopo"], s["porta"], s["p9"], s["origem"]
        if porta != "-":
            nome = re.sub(r"\.(service|timer)$", "", u)
            partes.append(f"- `{nome}` (porta :{porta}) — unidade `{u}`, escopo {esc}, P-9 {p9} — origem: {origem}")
        else:
            partes.append(f"- `{u}` — escopo {esc}, P-9 {p9} — origem: {origem}")
    fora = conferencia(raiz)
    partes.append("")
    if fora:
        partes.append("Conferência: unidades do repo com WantedBy/PartOf de agata.target sem linha no manifesto:")
        partes.extend(f"- `{u}` — AVISO: falta linha em config/servicos-agata.txt" for u in fora)
    else:
        partes.append("Conferência: toda unidade do repo com WantedBy/PartOf de agata.target está no manifesto.")
    partes.append("")
    partes.append("## Portas (config/portas-agata.txt)\n")
    partes.extend(f"- `{porta}` {nome} (bind {bind})" for porta, nome, bind in portas(raiz))
    partes.append("")
    partes.append("## Modelos (config/modelos-gratuitos.md, seção Confirmado funcionando)\n")
    partes.append("A nota é a da própria tabela, cortada. A tabela escreve a data de cada medição; esta linha não confirma nada hoje.\n")
    partes.extend(f"- `{mid}` — {nota}" if nota else f"- `{mid}`" for mid, nota in modelos_confirmados(raiz))
    partes.append("")
    abertas, _ = propostas(raiz)
    partes.append("## Propostas (propostas/)\n")
    partes.append(f"Abertas (sem APROVADO-): {len(abertas)}.")
    partes.extend(f"- `{nome}`" for nome in abertas)
    # Sem contagem de aplicadas (estado-aplicadas-14-11): o aplicar.py move a proposta para aplicadas/
    # DEPOIS de o pre-commit gerar este arquivo, e o fiscal-p8 exige o head idêntico ao diff assinado;
    # a contagem ficava um atrás em toda aplicação e o `gerar_estado.py --verificar` do sdd falhava.
    partes.append("Aplicadas: ver propostas/aplicadas/ (sem contagem aqui, de propósito).")
    partes.append("")
    partes.append("## Bugs e testes abertos (ONDE_ESTAMOS.md)\n")
    partes.append(bugs(raiz))
    partes.append("")
    partes.append("## Mapa de PROTOCOLOS (PROTOCOLOS.md, gerado)\n")
    partes.append(mapa_protocolos(raiz))
    return "\n".join(partes).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", type=Path, default=RAIZ)
    ap.add_argument("--verificar", action="store_true", help="falha se o ESTADO.md em disco não for o gerado agora")
    ap.add_argument("--imprimir", action="store_true", help="escreve na saída padrão em vez de gravar")
    args = ap.parse_args(argv)
    texto = renderizar(args.raiz)
    for u in conferencia(args.raiz):
        print(f"AVISO (ESTADO): unidade '{u}' tem WantedBy/PartOf de agata.target e falta em config/servicos-agata.txt", file=sys.stderr)
    alvo = args.raiz / ARQUIVO_SAIDA
    if args.imprimir:
        sys.stdout.write(texto)
        return 0
    if args.verificar:
        atual = alvo.read_text(encoding="utf-8") if alvo.is_file() else ""
        if atual != texto:
            print(f"ESTADO.md desatualizado: rode python3 scripts/gerar_estado.py ({ARQUIVO_SAIDA})", file=sys.stderr)
            return 1
        print(f"ESTADO.md: em dia ({ARQUIVO_SAIDA})")
        return 0
    alvo.write_text(texto, encoding="utf-8")
    print(f"gerado: {alvo} ({len(texto.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
