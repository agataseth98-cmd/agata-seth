#!/usr/bin/env python3
"""Avaliação em produção do decisor local (PROJETO.md, "Decisor local").

Decisão do Humano, 13/10/2026 (MEMÓRIAS (655)): os 4 usos entram com o risco
assumido por escrito, e o sistema avisa se valeu a pena até ele mandar aprovar
ou remover de vez. Roda todo dia pelo `agata-avaliacao-decisor.timer`.

Por uso, um veredito -- VALE / NÃO VALE / INCONCLUSIVO -- com o motivo e os
números, pelos critérios abaixo (constantes, revisáveis):
- roteador: falha demais -> não vale; concorda com a regra em >=95% -> não vale
  (só gasta CPU); senão decide o rótulo do Humano nas divergências.
- inbox: nota barrada como rascunho que depois foi EDITADA = acerto; importada
  intocada pela regra das 24 h = erro. Medido sozinho, sem rótulo.
- p20 e consolidação: rótulo do Humano (acertou/errou) nos avisos e reprovações.
Alarme imediato: o serviço reiniciou 3+ vezes, ou mais da metade das decisões
das últimas 24 h falhou.

Avisa por notificação na área de trabalho e reescreve o relatório em
`~/Área de trabalho/avaliacao-decisor.md`: no 3º dia, no 7º, depois a cada 7,
e na hora em caso de alarme. Para de avisar depois de `--encerrar`.

Uso:
  avaliar_decisor.py              relatório + aviso, se for dia de avisar
  avaliar_decisor.py --rotular    o Humano julga os casos pendentes (terminal)
  avaliar_decisor.py --encerrar aprovado|removido
  avaliar_decisor.py --selftest
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "redesign" / "router"))
import decisor  # noqa: E402

LOG = decisor.LOG_DIR
ESTADO = LOG / "avaliacao.json"
ROTULOS = LOG / "rotulos.jsonl"
_DESKTOP = Path.home() / "Área de trabalho"
RELATORIO = (_DESKTOP if _DESKTOP.is_dir() else LOG) / "avaliacao-decisor.md"

ROT_N_MIN, ROT_ERRO_MAX, ROT_CONCORDA_MAX = 30, 0.20, 0.95
ROTULOS_MIN = {"roteador": 10, "p20": 3, "consolidacao": 3}
INBOX_BLOQ_MIN = 3
ACERTO_MIN = 0.60
LIMIAR_P20, LIMIAR_UTIL, LIMIAR_INBOX = 0.7, 1.5, 0.7
AVISAR_DIAS = (3, 7)


def _ler(nome: str) -> list[dict]:
    try:
        return [json.loads(l) for l in (LOG / nome).read_text(encoding="utf-8").splitlines() if l.strip()]
    except (OSError, ValueError):
        return []


def _estado() -> dict:
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        e = {"inicio": dt.date.today().isoformat(), "encerrado": None, "avisos": []}
        _gravar_estado(e)
        return e


def _gravar_estado(e: dict) -> None:
    LOG.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")


def _rotulos() -> dict[tuple[str, str], str]:
    return {(r["uso"], r["ts"]): r["veredito"] for r in _ler("rotulos.jsonl")}


def _pendentes() -> list[dict]:
    """Casos que só o Humano julga: divergência do roteador, aviso do P-20,
    reprovação da consolidação."""
    casos = [{"uso": "roteador", **c} for c in _ler("roteador-avaliacao.jsonl")]
    for d in _ler("p20.jsonl"):
        p = decisor.probabilidade(d.get("respostas"), "pessoal")
        if p is not None and p >= LIMIAR_P20:
            casos.append({"uso": "p20", "ts": d["ts"], "arquivo": d.get("arquivo"), "p": p})
    for d in _ler("consolidacao.jsonl"):
        n = decisor.nota(d.get("respostas"), "util")
        if n is not None and n < LIMIAR_UTIL:
            casos.append({"uso": "consolidacao", "ts": d["ts"], "tema": d.get("tema"), "nota": n})
    feitos = _rotulos()
    return [c for c in casos if (c["uso"], c["ts"]) not in feitos]


def _por_rotulo(uso: str) -> tuple[str, str]:
    vs = [v for (u, _), v in _rotulos().items() if u == uso and v in ("modelo", "regra")]
    certos = vs.count("modelo")
    if len(vs) < ROTULOS_MIN[uso]:
        return "INCONCLUSIVO", (f"{len(vs)} de {ROTULOS_MIN[uso]} casos julgados -- rode "
                                f"`python3 ~/agata/scripts/avaliar_decisor.py --rotular`")
    taxa = certos / len(vs)
    return ("VALE" if taxa >= ACERTO_MIN else "NÃO VALE",
            f"o modelo acertou {certos} de {len(vs)} casos julgados ({taxa:.0%}; mínimo {ACERTO_MIN:.0%})")


def veredito_roteador() -> tuple[str, str, dict]:
    ds = _ler("roteador.jsonl")
    n = len(ds)
    falhas = sum(1 for d in ds if d.get("respostas") is None)
    ok = n - falhas
    div = len(_ler("roteador-avaliacao.jsonl"))
    ms = sorted(d["ms"] for d in ds if d.get("respostas") is not None)
    num = {"decisões": n, "falhas": falhas, "divergências": div,
           "latência p95 (ms)": ms[int(0.95 * (len(ms) - 1))] if ms else None}
    if n < ROT_N_MIN:
        return "INCONCLUSIVO", f"só {n} decisões (mínimo {ROT_N_MIN})", num
    if falhas / n > ROT_ERRO_MAX:
        return "NÃO VALE", f"falhou em {falhas / n:.0%} das decisões", num
    if ok and 1 - div / ok >= ROT_CONCORDA_MAX:
        return "NÃO VALE", f"concorda com a regra em {1 - div / ok:.0%} -- só gasta CPU", num
    v, m = _por_rotulo("roteador")
    return v, m, num


def veredito_inbox() -> tuple[str, str, dict]:
    bloqueios = {}
    for d in _ler("inbox.jsonl"):
        p = decisor.probabilidade(d.get("respostas"), "concluida")
        if p is not None and p < LIMIAR_INBOX and d.get("nota"):
            bloqueios.setdefault(d["nota"], d.get("chars"))
    certos = errados = 0
    for e in _ler("inbox-avaliacao.jsonl"):
        chars_no_bloqueio = bloqueios.get(e.get("nota"))
        if chars_no_bloqueio is None:
            continue
        if e.get("chars") != chars_no_bloqueio:
            certos += 1          # editada depois do bloqueio: era rascunho mesmo
        elif e.get("via") == "24h":
            errados += 1         # saiu intocada pela regra das 24 h: bloqueio à toa
    num = {"notas barradas": len(bloqueios), "barradas e depois editadas": certos,
           "barradas e importadas intocadas": errados}
    julgados = certos + errados
    if julgados < INBOX_BLOQ_MIN:
        return "INCONCLUSIVO", f"{julgados} bloqueio(s) com desfecho (mínimo {INBOX_BLOQ_MIN})", num
    taxa = certos / julgados
    return ("VALE" if taxa >= ACERTO_MIN else "NÃO VALE",
            f"{certos} de {julgados} notas barradas eram mesmo rascunho ({taxa:.0%})", num)


def veredito_rotulado(uso: str, log: str) -> tuple[str, str, dict]:
    num = {"avaliações": len(_ler(log)),
           "casos para julgar": sum(1 for c in _pendentes() if c["uso"] == uso)}
    v, m = _por_rotulo(uso)
    return v, m, num


def _servico() -> dict:
    try:
        out = subprocess.run(["systemctl", "--user", "show", "ollaya.service",
                              "-p", "ActiveState", "-p", "NRestarts"],
                             capture_output=True, text=True, timeout=10).stdout
        return dict(l.split("=", 1) for l in out.splitlines() if "=" in l)
    except (OSError, subprocess.SubprocessError):
        return {}


def alarmes() -> list[str]:
    a = []
    srv = _servico()
    if int(srv.get("NRestarts", "0") or 0) >= 3:
        a.append(f"o ollaya reiniciou {srv['NRestarts']} vezes (possível falta de memória)")
    limite = (dt.datetime.now().astimezone() - dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S%z")
    recentes = [d for u in ("roteador", "inbox", "p20", "consolidacao")
                for d in _ler(f"{u}.jsonl") if d.get("ts", "") >= limite]
    falhas = sum(1 for d in recentes if d.get("respostas") is None)
    if len(recentes) >= 5 and falhas / len(recentes) > 0.5:
        a.append(f"{falhas} de {len(recentes)} decisões das últimas 24 h falharam")
    return a


def relatorio() -> tuple[str, str]:
    e = _estado()
    dia = (dt.date.today() - dt.date.fromisoformat(e["inicio"])).days + 1
    usos = {"Roteador da Seth (sombra)": veredito_roteador(),
            "Inbox do Obsidian": veredito_inbox(),
            "Aviso de dado pessoal (P-20)": veredito_rotulado("p20", "p20.jsonl"),
            "Consolidação noturna": veredito_rotulado("consolidacao", "consolidacao.jsonl")}
    al = alarmes()
    cont = {v: sum(1 for x in usos.values() if x[0] == v) for v in ("VALE", "NÃO VALE", "INCONCLUSIVO")}
    resumo = (f"Decisor local, dia {dia}: {cont['VALE']} vale, {cont['NÃO VALE']} não vale, "
              f"{cont['INCONCLUSIVO']} inconclusivo" + (f" -- ALARME: {'; '.join(al)}" if al else ""))
    linhas = [f"# Avaliação do decisor local — dia {dia} (desde {e['inicio']})", "",
              f"**{resumo}**", ""]
    if al:
        linhas += ["## Alarme", *[f"- {x}" for x in al], ""]
    for nome, (v, motivo, num) in usos.items():
        linhas += [f"## {nome}: {v}", f"{motivo}.", "",
                   *[f"- {k}: {val}" for k, val in num.items()], ""]
    pend = len(_pendentes())
    linhas += ["## O que fazer",
               f"- Casos esperando seu julgamento: {pend}. Para julgar: "
               "`python3 ~/agata/scripts/avaliar_decisor.py --rotular`" if pend else
               "- Nenhum caso esperando julgamento.",
               "- Para encerrar: diga a um executor \"aprovar o decisor\" ou \"remover o decisor\" "
               "(ele roda `--encerrar` e prepara a proposta P-8 correspondente).", ""]
    return resumo, "\n".join(linhas)


def _notificar(resumo: str) -> None:
    try:
        subprocess.run(["notify-send", "-a", "Agata", "Avaliação do decisor local",
                        resumo + f"\nRelatório: {RELATORIO}"], timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def rodar() -> int:
    e = _estado()
    if e.get("encerrado"):
        print(f"avaliação encerrada ({e['encerrado']}) -- nada a fazer")
        return 0
    resumo, md = relatorio()
    RELATORIO.write_text(md, encoding="utf-8")
    print(md)
    dia = (dt.date.today() - dt.date.fromisoformat(e["inicio"])).days + 1
    marco = dia in AVISAR_DIAS or (dia > AVISAR_DIAS[-1] and (dia - AVISAR_DIAS[-1]) % 7 == 0)
    chave = f"dia-{dia}" if marco else (f"alarme-{dt.date.today()}" if "ALARME" in resumo else None)
    if chave and chave not in e["avisos"]:
        _notificar(resumo)
        e["avisos"].append(chave)
        _gravar_estado(e)
    return 0


def rotular() -> int:
    casos = _pendentes()
    if not casos:
        print("nenhum caso esperando julgamento")
        return 0
    print(f"{len(casos)} caso(s). Para cada um: m = o modelo acertou, r = a regra acertou, "
          "i = tanto faz, Enter = pular, q = sair.\n")
    for c in casos:
        if c["uso"] == "roteador":
            print(f"[roteador] {c['ts']}  regra: {c['heuristica']}  modelo: {c['modelo']} "
                  f"(confiança {c['confianca']:.2f})\n  mensagem: {c['trecho']!r}")
        elif c["uso"] == "p20":
            print(f"[P-20] {c['ts']}  avisou dado pessoal em {c['arquivo']} (p={c['p']:.2f}). "
                  "Lembre do commit dessa hora: tinha mesmo dado pessoal?")
        else:
            print(f"[consolidação] {c['ts']}  reprovou o tema {c['tema']!r} (nota {c['nota']:.2f}). "
                  "Texto em ~/.cache/agata/consolidacao/reprovados.log: a reprovação foi justa?")
        r = input("  > ").strip().lower()
        if r == "q":
            break
        v = {"m": "modelo", "r": "regra", "i": "tanto-faz"}.get(r)
        if v:
            with open(ROTULOS, "a", encoding="utf-8") as f:
                f.write(json.dumps({"uso": c["uso"], "ts": c["ts"], "veredito": v}) + "\n")
    return 0


def encerrar(como: str) -> int:
    if como not in ("aprovado", "removido"):
        print("uso: --encerrar aprovado|removido")
        return 2
    e = _estado()
    e["encerrado"], e["encerrado_em"] = como, dt.date.today().isoformat()
    _gravar_estado(e)
    for f in LOG.glob("*-avaliacao.jsonl"):
        f.unlink()
    print(f"avaliação encerrada: {como}. Trechos de mensagem apagados.")
    if como == "removido":
        subprocess.run(["systemctl", "--user", "disable", "--now", "ollaya.service"])
        print("ollaya parado e desabilitado: todos os usos já caem na regra determinística. "
              "Falta a proposta P-8 que tira o código (o executor prepara).")
    else:
        print("Falta a proposta P-8 que tira o roteador da sombra, se for o caso (o executor prepara).")
    return 0


def _selftest() -> int:
    import tempfile
    global LOG, ESTADO, ROTULOS, RELATORIO
    LOG = Path(tempfile.mkdtemp())
    ESTADO, ROTULOS, RELATORIO = LOG / "avaliacao.json", LOG / "rotulos.jsonl", LOG / "r.md"
    hoje = dt.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

    def grava(nome, linhas):
        (LOG / nome).write_text("".join(json.dumps(l) + "\n" for l in linhas), encoding="utf-8")

    casos = []
    casos.append(("sem dado nenhum -> tudo inconclusivo",
                  all(v[0] == "INCONCLUSIVO" for v in (veredito_roteador(), veredito_inbox()))))
    ok = {"rota": {"choice": "livre", "confidence": 0.9}}
    grava("roteador.jsonl", [{"ts": f"{hoje}{i}", "ms": 4000, "respostas": ok} for i in range(40)])
    casos.append(("roteador concordando sempre -> não vale", veredito_roteador()[0] == "NÃO VALE"))
    grava("roteador-avaliacao.jsonl", [{"ts": f"d{i}", "heuristica": "seth-rapido", "modelo": "seth-pesado",
                                        "confianca": 0.8, "trecho": "x"} for i in range(12)])
    casos.append(("roteador divergindo sem rótulo -> inconclusivo", veredito_roteador()[0] == "INCONCLUSIVO"))
    grava("rotulos.jsonl", [{"uso": "roteador", "ts": f"d{i}", "veredito": "modelo" if i < 9 else "regra"}
                            for i in range(12)])
    casos.append(("9 de 12 divergências com o modelo certo -> vale", veredito_roteador()[0] == "VALE"))
    grava("roteador.jsonl", [{"ts": f"{hoje}{i}", "ms": 0, "respostas": None} for i in range(40)])
    casos.append(("roteador falhando -> não vale", veredito_roteador()[0] == "NÃO VALE"))
    casos.append(("falhas recentes -> alarme", any("falharam" in a for a in alarmes())))
    rasc = {"concluida": {"noul": 0.3}}
    grava("inbox.jsonl", [{"nota": n, "chars": 50, "respostas": rasc} for n in "abcd"])
    grava("inbox-avaliacao.jsonl", [{"evento": "importada", "nota": "a", "chars": 90, "via": "decisor"},
                                    {"evento": "importada", "nota": "b", "chars": 120, "via": "decisor"},
                                    {"evento": "importada", "nota": "c", "chars": 80, "via": "24h"},
                                    {"evento": "importada", "nota": "d", "chars": 50, "via": "24h"}])
    v, m, _ = veredito_inbox()
    casos.append(("inbox: 3 de 4 barradas editadas depois -> vale", v == "VALE" and "3 de 4" in m))
    encerrar("aprovado")
    casos.append(("encerrar apaga os trechos e para de avisar",
                  not list(LOG.glob("*-avaliacao.jsonl")) and _estado()["encerrado"] == "aprovado"))
    for nome, ok_ in casos:
        print(f"{'PASS' if ok_ else 'FALHA'}  {nome}")
    falhas = sum(not ok_ for _, ok_ in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]:
        sys.exit(_selftest())
    if a == ["--rotular"]:
        sys.exit(rotular())
    if len(a) == 2 and a[0] == "--encerrar":
        sys.exit(encerrar(a[1]))
    if not a:
        sys.exit(rodar())
    sys.exit(__doc__)
