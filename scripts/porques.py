#!/usr/bin/env python3
"""Verificador de porquês (sincronia-12-11).

Decisão do Humano (cache do Conselho, entrada (521), 12/11/2026): tudo deve ter um porquê. Cada regra
do AGENTS.md (cada bullet "Sempre") e cada skill de .agents/skills/ precisa de uma origem rastreável:

  - número de entrada de MEMÓRIAS, `MEMÓRIAS (N)`, que existe em MEMÓRIAS.md, MEMORIAS-MORNO.md ou
    memoria/frio/ (linha que começa com "(N) ");
  - decisão do Humano com data DD/MM/AAAA, escrita no próprio texto ou no registro;
  - entrada do cache do Conselho, `cache (N)`, na forma (o cache fica fora do repositório, então a
    existência não é conferida aqui).

Origem inline (no texto da regra ou da skill) ou no registro config/porques.json. O que não tem origem
aparece como SEM-PORQUE, em lista, para o Humano decidir. Na primeira versão é AVISO: sai 0. Com
--estrito, sai 1 se houver SEM-PORQUE ou origem registrada que não confere.

Uso:
  python3 scripts/porques.py --verificar [--estrito] [--raiz CAMINHO]
  python3 scripts/porques.py --regras [--raiz CAMINHO]     (títulos das regras, para o início de sessão)
  python3 scripts/porques.py --selftest
Só lê o repositório.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

RAIZ_PADRAO = Path(__file__).resolve().parents[1]
REGISTRO = Path("config") / "porques.json"
MENOR_NUMERO_ENTRADA = 10  # "(1)", "(2)" são enumerações de lista, não citação de MEMÓRIAS

ENTRADA_LINHA = re.compile(r"^\((\d+)\) ", re.M)
TOKEN_ENTRADA = re.compile(r"\((\d{1,4})\)")
DATA_HUMANO = re.compile(r"Humano[^.;\n]{0,80}?(\d{2}/\d{2}/\d{4})")
REG_MEMORIA = re.compile(r"^MEMÓRIAS \((\d+)\)$")
REG_HUMANO = re.compile(r"^Humano (\d{2}/\d{2}/\d{4})$")
REG_CACHE = re.compile(r"^cache \((\d+)\)$")


@dataclass
class Unidade:
    id: str
    origem: str          # "AGENTS.md" ou "skill"
    titulo: str
    texto: str
    inline: list[str] = field(default_factory=list)     # origem dita no texto (só regra do AGENTS.md)
    registro: list[str] = field(default_factory=list)   # origem registrada em config/porques.json
    citacoes: list[str] = field(default_factory=list)   # entradas citadas no texto de skill (não é origem)
    invalidas: list[str] = field(default_factory=list)  # referência que não confere com as memórias


def slug(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto.lower())
    base = "".join(c for c in base if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def memorias_existentes(raiz: Path) -> set[int]:
    arquivos = [raiz / "MEMÓRIAS.md", raiz / "MEMORIAS-MORNO.md"]
    arquivos += sorted((raiz / "memoria" / "frio").glob("MEMORIAS-FRIO-*.md"))
    nums: set[int] = set()
    for arq in arquivos:
        try:
            nums.update(int(n) for n in ENTRADA_LINHA.findall(arq.read_text(encoding="utf-8")))
        except OSError:
            continue
    return nums


def data_valida(texto: str) -> bool:
    try:
        datetime.strptime(texto, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def unidades_agents(raiz: Path) -> list[Unidade]:
    try:
        linhas = (raiz / "AGENTS.md").read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    saida: list[Unidade] = []
    dentro, atual = False, None
    for ln in linhas:
        if ln.startswith("**Sempre:**"):
            dentro = True
            continue
        if dentro and ln.startswith("## "):
            break
        if not dentro:
            continue
        m = re.match(r"- \*\*(.+?)\*\*", ln)
        if m:
            titulo = m.group(1).strip().rstrip(":").rstrip(".").strip()
            atual = Unidade(id=f"AGENTS:{slug(titulo)}", origem="AGENTS.md", titulo=titulo, texto=ln)
            saida.append(atual)
        elif atual is not None and ln.strip():
            atual.texto += "\n" + ln
    return saida


def unidades_skills(raiz: Path) -> list[Unidade]:
    pasta = raiz / ".agents" / "skills"
    if not pasta.is_dir():
        return []
    saida = []
    for d in sorted(p for p in pasta.iterdir() if p.is_dir()):
        arq = d / "SKILL.md"
        if arq.is_file():
            saida.append(Unidade(id=f"skill:{d.name}", origem="skill", titulo=d.name,
                                 texto=arq.read_text(encoding="utf-8")))
    return saida


def carregar_registro(raiz: Path) -> dict:
    try:
        dados = json.loads((raiz / REGISTRO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return dados.get("unidades", {}) if isinstance(dados, dict) else {}


def avaliar(unidade: Unidade, registro: dict, existentes: set[int]) -> None:
    # Regra do AGENTS.md: o bullet diz a origem no próprio texto, então a citação inline conta.
    # Skill: citar uma entrada no SKILL.md não diz de onde a skill veio; só o registro conta como origem.
    destino = unidade.inline if unidade.origem == "AGENTS.md" else unidade.citacoes
    for n in sorted({int(x) for x in TOKEN_ENTRADA.findall(unidade.texto) if int(x) >= MENOR_NUMERO_ENTRADA}):
        if n in existentes:
            destino.append(f"MEMÓRIAS ({n})")
        else:
            unidade.invalidas.append(f"MEMÓRIAS ({n})")
    for d in sorted(set(DATA_HUMANO.findall(unidade.texto))):
        if data_valida(d):
            destino.append(f"Humano {d}")
        else:
            unidade.invalidas.append(f"Humano {d}")
    for origem in registro.get(unidade.id, {}).get("origens", []):
        if (m := REG_MEMORIA.match(origem)):
            ok = int(m.group(1)) in existentes
        elif (m := REG_HUMANO.match(origem)):
            ok = data_valida(m.group(1))
        elif REG_CACHE.match(origem):
            ok = True  # forma apenas: o cache não está no repositório
        else:
            ok = False
        (unidade.registro if ok else unidade.invalidas).append(origem)


def verificar(raiz: Path = RAIZ_PADRAO) -> tuple[list[Unidade], list[str]]:
    raiz = Path(raiz)
    registro = carregar_registro(raiz)
    existentes = memorias_existentes(raiz)
    unidades = unidades_agents(raiz) + unidades_skills(raiz)
    for u in unidades:
        avaliar(u, registro, existentes)
    ids = {u.id for u in unidades}
    orfaos = sorted(k for k in registro if k not in ids)
    return unidades, orfaos


def regras_curtas(raiz: Path = RAIZ_PADRAO) -> str:
    titulos = [u.titulo for u in unidades_agents(Path(raiz))]
    if not titulos:
        return "Regras ativas: lacuna: AGENTS.md sem bullets 'Sempre' legíveis."
    return f"Regras ativas (AGENTS.md, Sempre, {len(titulos)}): " + " · ".join(titulos)


def _relatorio(unidades: list[Unidade], orfaos: list[str]) -> tuple[list[str], int, int]:
    linhas, sem, invalidas = [], 0, 0
    for u in unidades:
        if u.inline or u.registro:
            fonte = ", ".join((u.inline + u.registro)[:3])
            extra = f" · referência sem entrada: {', '.join(u.invalidas)}" if u.invalidas else ""
            linhas.append(f"OK      {u.id}: {fonte}{extra}")
        else:
            sem += 1
            extra = ""
            if u.citacoes:
                extra += f" (cita {', '.join(u.citacoes[:3])}, mas não é origem registrada)"
            if u.invalidas:
                extra += f" (referência sem entrada: {', '.join(u.invalidas)})"
            linhas.append(f"SEM-PORQUE {u.id}: sem porquê encontrado{extra}")
        invalidas += len(u.invalidas)
    for k in orfaos:
        linhas.append(f"AVISO   registro órfão (sem unidade correspondente): {k}")
    n_ag = sum(1 for u in unidades if u.origem == "AGENTS.md")
    n_sk = len(unidades) - n_ag
    com = len(unidades) - sem
    linhas.append(f"porques: {len(unidades)} unidades ({n_ag} regras do AGENTS.md, {n_sk} skills); "
                  f"com origem {com}; sem porquê {sem}; referências sem entrada {invalidas}; registro órfão {len(orfaos)}")
    return linhas, sem, invalidas


def _selftest() -> int:
    falhas = []
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        (raiz / "MEMÓRIAS.md").write_text("(705) DIÁRIO — x\n(654) DIÁRIO — y\n", encoding="utf-8")
        (raiz / "AGENTS.md").write_text(
            "# A\n\n**Sempre:**\n- **Regra 1:** cabeçalho (654).\n- **Sem origem:** nada aqui.\n"
            "- **Com data:** decisão do Humano, 17/10/2026, regra nova.\n- **Referência morta:** cita (999).\n\n## Outro\n",
            encoding="utf-8")
        (raiz / ".agents" / "skills" / "s1").mkdir(parents=True)
        (raiz / ".agents" / "skills" / "s1" / "SKILL.md").write_text("sem origem nenhuma", encoding="utf-8")
        (raiz / ".agents" / "skills" / "s2").mkdir(parents=True)
        (raiz / ".agents" / "skills" / "s2" / "SKILL.md").write_text("texto", encoding="utf-8")
        (raiz / "config").mkdir()
        (raiz / "config" / "porques.json").write_text(json.dumps({"unidades": {
            "skill:s2": {"origens": ["MEMÓRIAS (705)"]},
            "AGENTS:sem-origem": {"origens": ["MEMÓRIAS (1234)"]},
            "skill:fantasma": {"origens": ["MEMÓRIAS (705)"]},
        }}), encoding="utf-8")
        unidades, orfaos = verificar(raiz)
        mapa = {u.id: u for u in unidades}
        falhas += [] if len(unidades) == 6 else [f"esperava 6 unidades (4 regras + 2 skills), veio {len(unidades)}"]
        falhas += [] if mapa["AGENTS:regra-1"].inline else ["Regra 1 deveria ter origem inline (654)"]
        falhas += [] if not mapa["AGENTS:sem-origem"].inline and not mapa["AGENTS:sem-origem"].registro \
            else ["'Sem origem' não deveria ter origem"]
        falhas += [] if mapa["AGENTS:com-data"].inline == ["Humano 17/10/2026"] else ["data do Humano não reconhecida"]
        falhas += [] if "MEMÓRIAS (999)" in mapa["AGENTS:referencia-morta"].invalidas else ["referência morta não apontada"]
        falhas += [] if mapa["skill:s2"].registro == ["MEMÓRIAS (705)"] else ["registro de skill não lido"]
        falhas += [] if mapa["AGENTS:sem-origem"].invalidas == ["MEMÓRIAS (1234)"] else ["registro inválido não apontado"]
        falhas += [] if orfaos == ["skill:fantasma"] else [f"órfão não apontado: {orfaos}"]
        linhas, sem, _ = _relatorio(unidades, orfaos)
        # sem origem válida: sem-origem (registro inválido), referencia-morta (999 não existe) e s1
        falhas += [] if sem == 3 else [f"esperava 3 SEM-PORQUE, veio {sem}"]
        falhas += [] if regras_curtas(raiz).startswith("Regras ativas (AGENTS.md, Sempre, 4)") else ["regras_curtas"]
    if falhas:
        for f in falhas:
            print("FALHOU", f)
        return 1
    print("SELFTEST OK porques")
    return 0


def _main(argv: list[str]) -> int:
    raiz = RAIZ_PADRAO
    if "--raiz" in argv:
        raiz = Path(argv[argv.index("--raiz") + 1])
    if "--selftest" in argv:
        return _selftest()
    if "--regras" in argv:
        print(regras_curtas(raiz))
        return 0
    if "--verificar" not in argv:
        print(__doc__)
        return 2
    unidades, orfaos = verificar(raiz)
    linhas, sem, invalidas = _relatorio(unidades, orfaos)
    print("\n".join(linhas))
    if "--estrito" in argv and (sem or invalidas or orfaos):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
