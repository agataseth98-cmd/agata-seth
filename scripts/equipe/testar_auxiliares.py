#!/usr/bin/env python3
"""Testes das ferramentas auxiliares da Equipe (aplicar.py, vigia_par.py, contar_turnos.py, vigia.sh). Só /tmp; sem rede, sem git, sem gh.
Cada caso nasceu de um erro real de 16/10/2026 (MEMÓRIAS (732))."""
import datetime
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))


def carregar(nome):
    s = importlib.util.spec_from_file_location(nome, os.path.join(AQUI, nome + ".py"))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def bloco(autor, minutos, prox):
    t = (datetime.datetime.now().astimezone() - datetime.timedelta(minutes=minutos)).isoformat(timespec="seconds")
    return f"## {autor}-2026-10-28-x\n- Hora: {t}\n- Assunto: a\n\ntexto\n\nPróximo responsável: {prox}\n"


def par(eu, *specs):
    d = tempfile.mkdtemp()
    arq = os.path.join(d, "canal.md")
    blocos = []
    for i, (autor, minutos, prox) in enumerate(specs):
        blocos.append(bloco(autor, minutos, prox).replace(f"{autor}-2026-10-28-x", f"{autor}-2026-10-28-x{i}"))
    open(arq, "w", encoding="utf-8").write("\n".join(blocos))
    return subprocess.run([sys.executable, "-I", os.path.join(AQUI, "vigia_par.py"), eu, arq], capture_output=True, text=True).stdout.strip()


def main():
    casos = []
    ap = carregar("aplicar")
    casos.append(("numeração: título acentuado (DIÁRIO/CORREÇÃO) conta", ap.proximo_numero("(728) CONSELHO — a\n(729) DIÁRIO — b\n(730) CORREÇÃO — c\n") == 731))
    casos.append(("numeração: só o cabeçalho no início da linha", ap.proximo_numero("(5) DIÁRIO — x\ncita (999) no meio da linha\n") == 6))
    try:
        ap.proximo_numero("sem entradas")
        casos.append(("numeração: sem entrada é erro explícito", False))
    except ValueError:
        casos.append(("numeração: sem entrada é erro explícito", True))
    casos.append(("refazer base: PR DIRTY (conflito com o main) refaz", ap.precisa_refazer("DIRTY", "")))
    casos.append(("refazer base: PR BEHIND (main andou) refaz", ap.precisa_refazer("BEHIND", "")))
    casos.append(("refazer base: mensagem 'not up to date' sem estado refaz", ap.precisa_refazer("", "Head branch is not up to date")))
    casos.append(("refazer base: BLOCKED (check vermelho) não refaz", not ap.precisa_refazer("BLOCKED", "Required status check failed")))
    casos.append(("par: pedido do outro há 12 min sem resposta -> DEVO RESPOSTA", par("claude", ("codex", 12, "claude")).startswith("DEVO RESPOSTA")))
    casos.append(("par: pedido recente (2 min) -> silêncio", par("claude", ("codex", 2, "claude")) == ""))
    casos.append(("par: pedido antigo respondido -> silêncio", par("claude", ("codex", 30, "claude"), ("claude", 20, "codex"), ("codex", 3, "humano")) == ""))
    casos.append(("par: dois pedidos, mede pelo MAIS ANTIGO", par("claude", ("codex", 12, "claude"), ("codex", 3, "claude")).startswith("DEVO RESPOSTA")))
    casos.append(("par: meu pedido escondido por mensagem minha seguinte -> SEM RESPOSTA", par("claude", ("claude", 20, "codex"), ("claude", 19, "humano")).startswith("SEM RESPOSTA: codex")))
    casos.append(("par: o alerta não traz contador de minutos (dedup)", "min)" not in par("claude", ("codex", 12, "claude")) and "há " not in par("claude", ("codex", 12, "claude"))))
    ct = os.path.join(AQUI, "contar_turnos.py")
    d = tempfile.mkdtemp()
    arq = os.path.join(d, "s.jsonl")
    reg = [{"type": "user", "message": {"content": "oi"}},
           {"type": "user", "message": {"content": [{"type": "tool_result", "content": "x"}]}},
           {"type": "user", "message": {"content": "<system-reminder>aviso</system-reminder>"}},
           {"type": "user", "message": {"content": [{"type": "text", "text": "[SYSTEM NOTIFICATION - NOT USER INPUT] x"}]}},
           {"type": "user", "message": {"content": [{"type": "text", "text": "segunda fala do humano"}]}},
           {"type": "assistant", "message": {"content": "resposta"}}]
    open(arq, "w", encoding="utf-8").write("\n".join(json.dumps(r) for r in reg))
    casos.append(("t=: conta só as falas do Humano (2 de 6 registros)", subprocess.run([sys.executable, "-I", ct, arq], capture_output=True, text=True).stdout.strip() == "2"))
    contador = carregar("contar_turnos")
    misto = [
        {"type":"assistant","message":{"id":"a","content":[{"type":"thinking","thinking":"x"}]}},
        {"type":"assistant","message":{"id":"b","content":[{"type":"tool_use","name":"x"}]}},
        {"type":"assistant","message":{"id":"c","content":[{"type":"text","text":"um"}]}},
        {"type":"assistant","message":{"id":"c","content":[{"type":"text","text":"um completo"}]}},
        {"type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"dois"}]}},
        {"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"humano"}]}},
    ]
    casos.append(("t=: modo respostas conta 2 (sem tool/thinking/repetição)", contador.contar(map(json.dumps,misto)) == 2))
    try:
        contador.contar(['{incompleto'])
        casos.append(("t=: modo respostas, transcrito truncado falha",False))
    except ValueError:
        casos.append(("t=: modo respostas, transcrito truncado falha",True))
    casos.append(("t=: --modo respostas --proximo soma 1", subprocess.run([sys.executable,"-I",ct,"--modo","respostas","--proximo",arq],capture_output=True,text=True).stdout.strip() == "2"))
    env_ct = {k:v for k,v in os.environ.items() if k != "AGATA_TRANSCRITO"}
    casos.append(("t=: modo respostas sem fonte não escolhe sessão alheia", subprocess.run([sys.executable,"-I",ct,"--modo","respostas"],capture_output=True,text=True,env=env_ct).returncode == 2))
    vg = os.path.join(AQUI, "vigia.sh")
    casos.append(("vigia.sh: sintaxe bash válida", subprocess.run(["bash", "-n", vg]).returncode == 0))
    iso = tempfile.mkdtemp()
    open(os.path.join(iso, "canal.md"), "w").write("")
    ambiente = dict(os.environ, EQUIPE_CANAL=os.path.join(iso, "canal.md"), EQUIPE_REPO=iso, EQUIPE_PARAR=os.path.join(iso, "parar"))
    r = subprocess.run(["bash", vg, "claude", "1", "--uma", "3"], capture_output=True, text=True, timeout=30, env=ambiente)
    casos.append(("vigia.sh --uma: sem evento, sai por tempo com 'SEM EVENTO'", r.returncode == 0 and "SEM EVENTO" in r.stdout))
    casos.append(("equipe: pedido do gemini ao claude há 12 min -> DEVO RESPOSTA a gemini", par("claude", ("gemini", 12, "claude")).startswith("DEVO RESPOSTA a gemini")))
    casos.append(("equipe: membro com hífen (claude-web) é um autor só", par("claude-web", ("codex", 12, "claude-web")).startswith("DEVO RESPOSTA a codex")))
    casos.append(("equipe: pedido ao Humano não vira alerta", par("claude", ("claude", 30, "humano")) == ""))
    casos.append(("equipe: pedidos a dois membros, um respondeu -> só o outro alerta",
                  (lambda o: o.startswith("SEM RESPOSTA: gemini") and "codex" not in o)(
                      par("claude", ("claude", 30, "codex"), ("claude", 29, "gemini"), ("codex", 20, "humano")))))
    # vigia.sh: canal sem bloco de outro membro não pode morrer em aritmética ($'0\n0', achado da auditoria de 28/10)
    iso2 = tempfile.mkdtemp(); open(os.path.join(iso2, "canal.md"), "w").write("## claude-2026-10-28-aaaa\n- Hora: x\n")
    amb2 = dict(os.environ, EQUIPE_CANAL=os.path.join(iso2, "canal.md"), EQUIPE_REPO=iso2, EQUIPE_PARAR=os.path.join(iso2, "parar"))
    r2 = subprocess.run(["bash", vg, "claude", "1", "--uma", "3"], capture_output=True, text=True, timeout=30, env=amb2)
    casos.append(("vigia.sh: canal só com blocos meus não quebra a conta", r2.returncode == 0 and "SEM EVENTO" in r2.stdout and "erro" not in r2.stderr.lower()))
    for n, ok in casos:
        print(("PASS  " if ok else "FALHA ") + n)
    ruins = [n for n, ok in casos if not ok]
    print(f"auxiliares da equipe: {len(casos) - len(ruins)}/{len(casos)}")
    return 1 if ruins else 0


if __name__ == "__main__":
    sys.exit(main())
