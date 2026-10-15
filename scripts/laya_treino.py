#!/usr/bin/env python3
"""Treino contínuo do Laya que escolhe a fila da Seth (MEMÓRIAS (719)).

Decisão do Humano, 15/10/2026: o Laya continua aprendendo com o uso real, mas **cada troca
de modelo é aprovada por ele**. Toda semana (`agata-laya-treino.timer`, domingo 03:30):
  1. junta os dados: os sintéticos de `redesign/laya/dados/treino-v2.jsonl` + o treino real
     (`~/.cache/agata/decisor/laya-treino-real.jsonl`: divergências Laya × Jev que os 2
     juízes julgaram iguais, (719)), o real pesando 3x;
  2. separa 1 em cada 5 exemplos reais (pelo hash do texto, sempre os mesmos) para teste;
  3. treina um CANDIDATO em `~/.local/share/agata-laya/modelos/candidato-<data>`;
  4. compara candidato e modelo atual nos testes fixos (A à mão, B do Gemini) e no real
     separado; relatório em `~/Área de trabalho/laya-treino.md` e notificação.
**Nunca troca o modelo sozinho.** A troca é o Humano rodar `--promover <candidato>`.
Pula a semana sem pelo menos MIN_NOVOS exemplos reais novos, ou com a GPU ocupada.

Roda com o venv do Laya (fora do repo): `~/.local/share/agata-laya/.venv/bin/python`.
Uso:
  laya_treino.py                    rodada semanal
  laya_treino.py --promover <dir>   o Humano troca o modelo da fila pelo candidato
  laya_treino.py --selftest
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "redesign" / "laya"))
LAYA = Path(os.environ.get("AGATA_LAYA_DIR", Path.home() / ".local/share/agata-laya"))
MODELOS = LAYA / "modelos"
ATUAL = MODELOS / "roteador-atual"
REAL = Path(os.environ.get("AGATA_DECISOR_LOG", Path.home() / ".cache/agata/decisor")) / "laya-treino-real.jsonl"
SINTETICOS = RAIZ / "redesign" / "laya" / "dados" / "treino-v2.jsonl"
TESTES = {"A (à mão)": RAIZ / "redesign/laya/dados/teste-claude.jsonl",
          "B (Gemini)": RAIZ / "redesign/laya/dados/teste-gemini.jsonl"}
ESTADO = LAYA / "treino-continuo.json"
_DESKTOP = Path.home() / "Área de trabalho"
RELATORIO = (_DESKTOP if _DESKTOP.is_dir() else LAYA) / "laya-treino.md"
MIN_NOVOS, PESO_REAL, GPU_MAX_MIB, HOLDOUT_MIN = 20, 3, 1500, 10


def _ler(p: Path) -> list[dict]:
    try:
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    except (OSError, ValueError):
        return []


def separado(texto: str) -> bool:
    """1 em cada 5 exemplos reais fica fora do treino, sempre o mesmo (hash do texto)."""
    return int(hashlib.sha1(texto.strip().lower().encode()).hexdigest(), 16) % 5 == 0


def montar(real: list[dict], destino: Path) -> tuple[int, int]:
    """Sintéticos + real (fora o separado) x PESO_REAL. Devolve (n_treino_real, n_total)."""
    reais = [r for r in real if not separado(r["state"])]
    linhas = [l for l in SINTETICOS.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in reais:
        linhas += [json.dumps({"state": r["state"], "gold": r["gold"]}, ensure_ascii=False)] * PESO_REAL
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return len(reais), len(linhas)


def _gpu_livre() -> bool:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=20).stdout
        return int(out.split()[0]) < GPU_MAX_MIB
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return False


def _estado() -> dict:
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"ultimo_n_real": 0, "candidatos": []}


def _relatar(linhas: list[str], resumo: str) -> None:
    RELATORIO.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas))
    try:
        subprocess.run(["notify-send", "-a", "Agata", "Treino do Laya", resumo + f"\nRelatório: {RELATORIO}"],
                       timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def rodar(treinar=None, avaliar=None) -> int:
    hoje = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    real, e = _ler(REAL), _estado()
    novos = len(real) - e.get("ultimo_n_real", 0)
    if novos < MIN_NOVOS:
        print(f"{hoje}: {novos} exemplo(s) real(is) novo(s) (mínimo {MIN_NOVOS}) -- sem treino esta semana")
        return 0
    if not _gpu_livre():
        print(f"{hoje}: GPU ocupada (>= {GPU_MAX_MIB} MiB) -- sem treino esta semana")
        return 0
    if treinar is None or avaliar is None:
        import laya_roteador as lr
        treinar = treinar or lr.treinar
        avaliar = avaliar or (lambda modelo, arq: lr.avaliar(lr.concorrente(str(modelo), "cuda"), str(arq)))
    nome = "candidato-" + dt.datetime.now().strftime("%Y%m%d-%H%M")
    cand = MODELOS / nome
    dados = LAYA / f"{nome}-entrada.jsonl"
    n_real, n_total = montar(real, dados)
    treinar(str(dados), str(cand))
    testes = dict(TESTES)
    sep = [r for r in real if separado(r["state"])]
    if len(sep) >= HOLDOUT_MIN:
        p = LAYA / f"{nome}-real-separado.jsonl"
        p.write_text("".join(json.dumps({"state": r["state"], "gold": r["gold"]}, ensure_ascii=False) + "\n"
                             for r in sep), encoding="utf-8")
        testes[f"real separado ({len(sep)})"] = p
    tabela = ["| teste | atual | candidato |", "|---|---|---|"]
    melhor_em = []
    for rot, arq in testes.items():
        a, c = avaliar(ATUAL, arq), avaliar(cand, arq)
        tabela.append(f"| {rot} | {a['acerto']:.3f} | {c['acerto']:.3f} |")
        melhor_em.append(c["acerto"] >= a["acerto"])
    veredito = ("o candidato não fica pior em nenhum teste" if all(melhor_em)
                else "o candidato fica PIOR em pelo menos um teste -- não recomendo trocar")
    e["ultimo_n_real"] = len(real)
    e["candidatos"].append({"nome": nome, "em": hoje, "n_real": n_real, "n_total": n_total, "sem_piora": all(melhor_em)})
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
    linhas = [f"# Treino do Laya — {hoje}", "",
              f"Candidato `{nome}`: {n_total} exemplos ({n_real} reais x{PESO_REAL}, {novos} novos desde o último).",
              "", *tabela, "", f"**{veredito}.**", "",
              f"Para trocar o modelo que escolhe a fila (decisão sua): "
              f"`~/.local/share/agata-laya/.venv/bin/python ~/agata/scripts/laya_treino.py --promover {cand}`",
              "Sem esse comando, nada muda."]
    _relatar(linhas, f"candidato {nome}: {veredito}")
    return 0


def promover(alvo: str) -> int:
    p = Path(alvo).expanduser().resolve()
    if p.parent != MODELOS.resolve() or not (p / "rl_agent_config.json").exists():
        print(f"recusado: {p} não é um checkpoint em {MODELOS}")
        return 2
    antes = os.readlink(ATUAL) if ATUAL.is_symlink() else None
    tmp = MODELOS / ".roteador-atual.novo"
    if tmp.is_symlink() or tmp.exists():
        tmp.unlink()
    tmp.symlink_to(p)
    tmp.replace(ATUAL)
    with open(LAYA / "promocoes.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"em": dt.datetime.now().isoformat(timespec="seconds"), "de": antes, "para": str(p)}) + "\n")
    r = subprocess.run(["systemctl", "--user", "restart", "laya-roteador.service"], timeout=120)
    print(f"roteador-atual: {antes} -> {p}; laya-roteador reiniciado (saída {r.returncode}).")
    print("Peça a um executor para registrar a troca em MEMÓRIAS. Para voltar: --promover com o anterior.")
    return 0


def _selftest() -> int:
    import tempfile
    global LAYA, MODELOS, ATUAL, REAL, ESTADO, RELATORIO, SINTETICOS, TESTES, _gpu_livre
    t = Path(tempfile.mkdtemp())
    LAYA, MODELOS = t, t / "modelos"
    MODELOS.mkdir()
    ATUAL, REAL, ESTADO, RELATORIO = MODELOS / "roteador-atual", t / "real.jsonl", t / "e.json", t / "r.md"
    SINTETICOS = t / "s.jsonl"
    SINTETICOS.write_text('{"state": "oi", "gold": "rapido"}\n', encoding="utf-8")
    TESTES = {"A": SINTETICOS}
    casos = [("separado é determinístico", separado("Abc ") == separado("abc"))]
    textos = [f"pedido {i}" for i in range(200)]
    frac = sum(separado(x) for x in textos) / len(textos)
    casos.append(("separa ~1 em 5", 0.1 < frac < 0.3))
    REAL.write_text("".join(json.dumps({"state": x, "gold": "livre"}) + "\n" for x in textos[:5]), encoding="utf-8")
    treinou = []
    casos.append(("menos de MIN_NOVOS reais novos -> não treina",
                  rodar(lambda a, b: treinou.append(1), lambda m, a: {}) == 0 and not treinou))
    REAL.write_text("".join(json.dumps({"state": x, "gold": "livre"}) + "\n" for x in textos[:40]), encoding="utf-8")
    _gpu_livre = lambda: True
    feitos = []

    def _treinar(entrada, saida):
        feitos.append(Path(entrada).read_text().splitlines())
        Path(saida).mkdir()
        (Path(saida) / "rl_agent_config.json").write_text("{}")
    rodar(_treinar, lambda m, a: {"acerto": 0.9 if "candidato" in str(m) else 0.8})
    n_sep = sum(separado(x) for x in textos[:40])
    casos.append(("treina com sintéticos + real fora do separado x3, e não troca o modelo",
                  feitos and len(feitos[0]) == 1 + (40 - n_sep) * PESO_REAL and not ATUAL.exists()
                  and "sem piora" not in RELATORIO.read_text() and "não fica pior" in RELATORIO.read_text()))
    casos.append(("promover recusa caminho fora de modelos/", promover(str(t)) == 2))
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]:
        sys.exit(_selftest())
    if len(a) == 2 and a[0] == "--promover":
        sys.exit(promover(a[1]))
    if not a:
        sys.exit(rodar())
    sys.exit(__doc__)
