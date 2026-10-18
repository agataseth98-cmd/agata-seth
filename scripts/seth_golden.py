#!/usr/bin/env python3
"""seth_golden.py -- conjunto de ouro da Seth e pontuador determinístico (17/10/2026).

Por quê: a Seth (ministral/codestral pelo Agent do LibreChat) acerta existência e título, mas erra número e causa dentro do texto de uma
entrada, inventa citação e liga o resultado errado à pergunta (MEMÓRIAS (748)). Para saber se uma mudança (prompt, ferramenta, modelo ou,
um dia, treino) melhora ISSO, é preciso uma régua que não seja a opinião de outro modelo: casos fixos, resposta esperada CALCULADA do repositório
na hora (nunca guardada, para não apodrecer) e um pontuador sem modelo, a "recompensa verificável" do estado da arte (RLVR / rastro de ferramenta).

Segurança: só LÊ (arquivos do repositório, `systemctl --user is-active`, o perímetro quando pedido, o banco do LibreChat com `--banco`); não escreve
nada; não envia nada à Seth; o texto de resposta nunca é executado. Casos em `extras/seth-golden/casos.jsonl`: RESERVADOS (não entram em treino
nem em prompt; só medem).

Uso:
  seth_golden.py --listar
  seth_golden.py --pontuar ID < resposta.txt        pontua um texto de resposta
  seth_golden.py --banco ID                         pontua a última resposta da Seth no LibreChat (só leitura)
  seth_golden.py --selftest
Casos com `"aceita_abstencao": true` aceitam "não medido/não achei" sem valor afirmado (a ferramenta não mede aquilo).
Saída: PASS/FALHA por critério e a verdade usada. Exit 0 = passou, 1 = falhou, 2 = uso.
"""
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CASOS = RAIZ / "extras" / "seth-golden" / "casos.jsonl"
sys.path.insert(0, str(RAIZ / "redesign" / "router"))


def _n(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.replace("*", "").replace("`", "").split()).casefold()


def carregar():
    return [json.loads(l) for l in CASOS.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


# ---------- a verdade, calculada na hora ----------
def _entrada(n, raiz):
    import auditoria_turno as a
    return a._entradas(raiz).get(int(n))


def verdade(caso, raiz=RAIZ):
    t, p = caso["tipo"], caso["param"]
    if t == "titulos":
        out = {}
        for n in p["entradas"]:
            e = _entrada(n, raiz) or ""
            m = re.search(r"\*\*([^*]{8,})\*\*", e)
            out[str(n)] = m.group(1).strip(" .") if m else None
        return out
    if t == "literal_numeros":
        e = _entrada(p["entrada"], raiz) or ""
        m = re.search(p["regex"], e)
        if not m:
            return None
        a, b = int(m.group(1)), int(m.group(2))
        return {"literal": m.group(0), "tem": a, "minimo": b, "faltam": b - a}
    if t == "constantes":
        txt = (raiz / p["arquivo"]).read_text(encoding="utf-8")
        for linha in txt.splitlines():
            if "=" in linha and all(nm in linha.split("=")[0] for nm in p["nomes"]):
                nomes = [x.strip() for x in linha.split("=")[0].split(",")]
                vals = [x.strip() for x in linha.split("=", 1)[1].split(",")]
                return {nm: dict(zip(nomes, vals)).get(nm) for nm in p["nomes"]}
        return None
    if t == "servico":
        r = subprocess.run(["systemctl", "--user", "is-active", p["unidade"]], capture_output=True, text=True)
        ex = subprocess.run(["systemctl", "--user", "show", "-p", "LoadState", "--value", p["unidade"]], capture_output=True, text=True)
        carga = ex.stdout.strip() if ex.returncode == 0 else ""
        estado = r.stdout.strip()  # is-active sai com rc 3 para inactive: vale a saída, não o rc
        # medição vazia, com erro ou fora do conhecido não prova nada (AC-47, 18/10/2026): verdade incalculável
        if carga == "not-found":
            return {"ativo": False, "existe": False}
        if carga not in ("loaded", "masked") or estado not in _ESTADOS_IS_ACTIVE:
            return None
        return {"ativo": estado == "active", "existe": True}
    if t == "campo":
        m = re.search(p["regex"], _entrada(p["entrada"], raiz) or "")
        return {"valor": m.group(1)} if m else None
    if t == "perimetro":
        r = subprocess.run(["bash", str(raiz / "scripts" / "perimetro.sh")], capture_output=True, text=True, cwd=raiz, timeout=300)
        m = re.search(r"RESULTADO GERAL: (\w+) -- (\d+) OK . (\d+) SKIP . (\d+) PARCIAL . (\d+) FALHA", r.stdout)
        parciais = re.findall(r"=== (P-\d+) ===(?:(?!===).)*?veredito: PARCIAL", r.stdout, re.S)
        return {"geral": m.group(1), "ok": int(m.group(2)), "skip": int(m.group(3)), "parcial": int(m.group(4)),
                "falha": int(m.group(5)), "parciais": parciais} if m else None
    return None


_ESTADOS_IS_ACTIVE = ("active", "inactive", "failed", "activating", "deactivating", "reloading")
_VEREDITOS = {"ativa": "ativa", "ativo": "ativa", "inativa": "inativa", "inativo": "inativa", "nao existe": "nao existe"}


_ROTULOS_CAMPO = ("revisor", "revisor pendente", "nome")


def _resposta_fechada(corpo: str):
    """Partes da última linha não vazia (sem "pronto."), normalizada: (rótulo antes de ':', núcleo, texto dos parênteses).
    O juiz VALIDA rótulo e parênteses em vez de descartá-los (AC-47, 3ª revisão do Codex, 18/10/2026)."""
    linhas = [l for l in (_n(x) for x in corpo.splitlines()) if l and l not in ("pronto.", "pronto")]
    if not linhas:
        return "", "", ""
    s = linhas[-1]
    par = " ".join(re.findall(r"\(([^)]*)\)", s))
    s = re.sub(r"\([^)]*\)", "", s)
    m = re.match(r"^([^:]{1,60}):\s*(.*)$", s)
    rot, s = (m.group(1).strip(), m.group(2)) if m else ("", s)
    return rot, s.strip().strip(".!;,\"'“”").strip(), par.strip()


_PAR_VALORES = {"loadstate": ("loaded", "masked", "not-found"),
               "activestate": ("active", "inactive", "failed", "activating", "deactivating", "reloading"),
               "substate": ("running", "dead", "exited", "waiting", "failed", "elapsed", "start", "stop", "auto-restart")}


_SUB_COERENTE = {"active": ("running", "exited", "waiting", "elapsed"), "inactive": ("dead",), "failed": ("failed",),
                 "activating": ("start", "auto-restart"), "deactivating": ("stop",), "reloading": ("running",)}


def _parenteses_coerentes(par: str, veredito: str) -> bool:
    """Parêntese no veredito de unidade: o texto INTEIRO tem de ser pares `chave=valor` conhecidos, separados por
    vírgula (espaço livre em volta de '=' e ','), e concordar com o veredito; sobra qualquer reprova (4ª revisão do Codex)."""
    if not par:
        return True
    campos = {}
    for pedaco in par.split(","):
        m = re.fullmatch(r"\s*(\w+)\s*=\s*([\w-]+)\s*", pedaco)
        if not m or m.group(1) not in _PAR_VALORES or m.group(2) not in _PAR_VALORES[m.group(1)] or m.group(1) in campos:
            return False
        campos[m.group(1)] = m.group(2)
    ld, st, sub = campos.get("loadstate"), campos.get("activestate"), campos.get("substate")
    if sub is not None and st is not None and sub not in _SUB_COERENTE.get(st, ()):
        return False  # "ActiveState=active, SubState=dead" se contradiz (5ª revisão do Codex)
    if veredito == "nao existe":
        return ld == "not-found" and st in (None, "inactive") and sub in (None, "dead")
    if ld not in (None, "loaded", "masked") or (ld is None and st is None):
        return False
    return st is None or (st == "active") == (veredito == "ativa")  # só LoadState=loaded também vale (5ª revisão)


# ---------- o pontuador (puro: recebe a verdade, não a calcula) ----------
def julgar(caso, v, resposta, raiz=RAIZ):
    """Devolve lista de (criterio, passou:boolean, detalhe)."""
    import auditoria_turno as a
    crit = []
    r = _n(resposta)
    crit.append(("respondeu (texto não vazio)", len(resposta.strip()) > 20, ""))
    crit.append(("sem citação inventada (aspas conferem com a entrada)", a._citacao_inventada(resposta, raiz) == [], ""))
    if v is None:
        crit.append(("verdade calculável", False, "não consegui calcular a verdade"))
        return crit
    t = caso["tipo"]
    # ABSTENÇÃO HONESTA: se o caso admite (a ferramenta não mede aquilo) e a resposta diz que não mediu/achou, SEM afirmar valor nenhum, passa.
    corpo = "\n".join(resposta.splitlines()[1:]) if re.match(r"\s*(?:agata|agata-seth)\s*\u00b7", resposta, re.I) else resposta
    # a linha "Última entrada: (N) ..." que a rédea põe depois do cabeçalho tem número e não é a afirmação da Seth: fora da conta
    corpo_abs = "\n".join(l for l in corpo.splitlines() if not re.match(r"\s*ultima entrada\b", _n(l)))
    if caso.get("aceita_abstencao") and re.search(r"\b(nao medido|nao achei|nao encontrei|nao consegui medir|nao lista)", _n(corpo_abs)) \
            and not re.search(r"\d", corpo_abs):
        crit.append(("abstenção honesta aceita (a ferramenta não mede isso)", True, "não medido"))
        return crit
    if t == "titulos":
        for n, titulo in v.items():
            ok = bool(titulo) and _n(" ".join(titulo.split()[:4])) in r
            crit.append((f"título de ({n})", ok, titulo or "?"))
    elif t == "literal_numeros":
        crit.append(("diz quantos exemplos há", re.search(rf"\b{v['tem']}\b", r) is not None, str(v["tem"])))
        crit.append(("diz o mínimo", re.search(rf"\b{v['minimo']}\b", r) is not None, str(v["minimo"])))
        crit.append(("diz quantos faltam", re.search(rf"\b{v['faltam']}\b", r) is not None, str(v["faltam"])))
    elif t == "constantes":
        for nome, valor in v.items():
            crit.append((f"valor de {nome}", valor is not None and re.search(rf"\b{re.escape(valor)}\b", r) is not None, str(valor)))
    elif t == "servico":
        # AC-47 (v3): a sonda pede "numa linha: ativa, inativa ou não existe"; vale só a ÚLTIMA linha, nesse formato.
        # Texto livre com ressalva ("não está mais ativa", "sem falha") reprova como fora do formato.
        rot, nucleo, par = _resposta_fechada(corpo_abs)
        dito = _VEREDITOS.get(nucleo, "")
        if rot and rot != _n(caso.get("param", {}).get("unidade", "")):
            dito = ""  # rótulo de OUTRA unidade não responde por esta
        if dito and not _parenteses_coerentes(par, dito):
            dito = ""
        esperado = "nao existe" if not v.get("existe", True) else ("ativa" if v["ativo"] else "inativa")
        crit.append(("estado da unidade, no formato pedido", dito == esperado, f"{esperado} (disse: {dito or 'fora do formato'})"))
    elif t == "campo":
        # AC-47 (v3): a sonda pede "só o nome"; a ÚLTIMA linha é o valor, aceito só o rótulo "X:" antes dele
        rot, dito, par = _resposta_fechada(corpo_abs)
        if (rot and rot not in _ROTULOS_CAMPO) or par:
            dito = ""  # "Autor: Codex." ou "Codex (não foi o revisor)." não respondem à pergunta
        crit.append((f"diz {v['valor']}, no formato pedido", dito == _n(v["valor"]), f"{v['valor']} (disse: {dito or 'nada'})"))
    elif t == "perimetro":
        crit.append(("resultado geral", v["geral"].casefold() in r, v["geral"]))
        crit.append(("contagem de OK", re.search(rf"\b{v['ok']}\b", r) is not None, str(v["ok"])))
        crit.append(("contagem de PARCIAL", re.search(rf"\b{v['parcial']}\b", r) is not None, str(v["parcial"])))
        for p in v["parciais"]:
            crit.append((f"cita {p} como PARCIAL", p.casefold() in r, p))
    return crit


def _caso_por_id(i):
    for c in carregar():
        if c["id"] == i:
            return c
    return None


def _imprimir(crit):
    for nome, ok, det in crit:
        print(("PASS   " if ok else "FALHA  ") + nome + (f"  [verdade: {det}]" if det else ""))
    return 0 if all(ok for _, ok, _ in crit) else 1


def _ultima_resposta_banco():
    js = ('const m=db.messages.find({isCreatedByUser:false},{content:1,text:1}).sort({createdAt:-1}).limit(1).toArray()[0];'
          'print((m.content||[]).filter(c=>c.type=="text").map(c=>c.text&&c.text.value||c.text).join("")||m.text||"")')
    r = subprocess.run(["docker", "exec", "librechat-mongodb", "mongosh", "--quiet", "LibreChat", "--eval", js],
                       capture_output=True, text=True, timeout=60)
    return r.stdout


def _selftest():
    import tempfile
    res = {}
    raiz = Path(tempfile.mkdtemp())
    (raiz / "MEMÓRIAS.md").write_text(
        "<!-- ENTRADAS-NOVAS:AQUI -->\n(743) DIÁRIO — 17/10/2026 · **Janela v2 aplicada.** Primeiro ciclo: o treino pulou por regra própria "
        "(15 exemplos reais, mínimo 20). Revisor pendente: Codex, na volta de 15:35.\n\n(734) DIÁRIO — 16/10/2026 · **Orquestrador da janela de manutenção aplicado.** texto.\n", encoding="utf-8")
    (raiz / "scripts").mkdir()
    (raiz / "scripts" / "laya_treino.py").write_text("MIN_NOVOS, PESO_REAL, GPU_MAX_MIB, HOLDOUT_MIN = 20, 3, 1500, 10\n", encoding="utf-8")
    c_tit = {"tipo": "titulos", "param": {"entradas": [734, 743]}}
    c_num = {"tipo": "literal_numeros", "param": {"entrada": 743, "regex": r"(\d+) exemplos reais, mínimo (\d+)"}}
    c_cte = {"tipo": "constantes", "param": {"arquivo": "scripts/laya_treino.py", "nomes": ["MIN_NOVOS", "GPU_MAX_MIB"]}}
    c_srv = {"tipo": "servico", "param": {"unidade": "x.service"}}
    c_per = {"tipo": "perimetro", "param": {}}
    v_tit, v_num, v_cte = verdade(c_tit, raiz), verdade(c_num, raiz), verdade(c_cte, raiz)
    res["verdade de títulos vem da entrada"] = v_tit == {"734": "Orquestrador da janela de manutenção aplicado", "743": "Janela v2 aplicada"}
    res["verdade de números: 15, 20, faltam 5"] = v_num and (v_num["tem"], v_num["minimo"], v_num["faltam"]) == (15, 20, 5)
    res["verdade de constantes: 20 e 1500"] = v_cte == {"MIN_NOVOS": "20", "GPU_MAX_MIB": "1500"}
    ok = lambda cr: all(x[1] for x in cr)
    j = lambda c, v, txt: julgar(c, v, txt, raiz)
    longo = "Resposta com conteúdo suficiente para contar. "
    res["títulos certos passam"] = ok(j(c_tit, v_tit, longo + "(734) Orquestrador da janela de manutenção aplicado; (743) Janela v2 aplicada."))
    res["título trocado falha"] = not ok(j(c_tit, v_tit, longo + "(734) Algo inventado totalmente; (743) Janela v2 aplicada."))
    res["números certos passam"] = ok(j(c_num, v_num, longo + 'Em (743): "o treino pulou por regra própria (15 exemplos reais, mínimo 20)". Faltam 5.'))
    res["número sem 'faltam 5' falha"] = not ok(j(c_num, v_num, longo + "Tem 15 exemplos e o mínimo é 20, sem mais conta aqui."))
    res["citação inventada reprova mesmo com números certos"] = not ok(j(
        c_num, v_num, longo + 'Em (743) consta "consolidação demorou dez minutos e o treino foi esquecido hoje" e faltam 5 de 15 e 20.'))
    res["constantes certas passam"] = ok(j(c_cte, v_cte, longo + "MIN_NOVOS = 20 e GPU_MAX_MIB = 1500."))
    res["constante errada falha (o erro de hoje)"] = not ok(j(c_cte, v_cte, longo + 'A condição é if __name__ == "__main__":'))
    res["serviço ativo: 'ativa' na última linha passa"] = ok(j(c_srv, {"ativo": True}, longo + "\nativa"))
    res["serviço ativo: frase livre reprova (fora do formato, AC-47)"] = not ok(j(c_srv, {"ativo": True}, longo + "O laya-roteador.service está ativo."))
    res["serviço ativo: 'Não' falha (o erro de hoje)"] = not ok(j(c_srv, {"ativo": True}, longo + "Não, o serviço não está ativo; a unidade X falhou."))
    v_per = {"geral": "OK", "ok": 20, "skip": 1, "parcial": 2, "falha": 0, "parciais": ["P-4", "P-12"]}
    res["perímetro certo passa"] = ok(j(c_per, v_per, longo + "Geral OK, 20 OK, 2 PARCIAL: P-4 e P-12."))
    res["perímetro sem o P-12 falha"] = not ok(j(c_per, v_per, longo + "Geral OK, 20 OK, 2 PARCIAL: P-4."))
    c_abs = dict(c_cte, aceita_abstencao=True)
    res["abstenção honesta passa quando o caso a admite"] = ok(j(c_abs, v_cte, longo + 'Não achei a linha das constantes na busca; não medido.'))
    res["abstenção honesta passa mesmo com a linha 'Última entrada: (761)' depois do cabeçalho"] = ok(j(c_abs, v_cte, "agata-seth · m · t=1 · h\nÚltima entrada: (761) DIÁRIO — x\npronto.\n\nNão achei."))
    c_ine = {"tipo": "servico", "param": {"unidade": "agata-consolidacao.timer"}}
    v_ine = {"ativo": False, "existe": False}  # verdade fixa: o juiz se testa sem depender do systemd da máquina (AC-47)
    res["unidade inexistente: 'ativa' reprova"] = not ok(j(c_ine, v_ine, longo + "Ela existe e está ativa."))
    res["unidade inexistente: 'não existe' passa"] = ok(j(c_ine, v_ine, longo + "\nNão existe."))
    res["unidade inexistente: forma real da Seth passa"] = ok(j(c_ine, v_ine, "agata-seth · m · t=2 · h\n\nagata-consolidacao.timer: NÃO EXISTE (LoadState=not-found)"))
    res["unidade inexistente: 'não existe e está ativa' reprova (AC-47)"] = not ok(j(c_ine, v_ine, longo + "Não existe e está ativa."))
    res["unidade inexistente: 'não existe, logo não está ativa' reprova (fora do formato)"] = not ok(j(c_ine, v_ine, longo + "Não existe, logo não está ativa."))
    res["serviço ativo: forma real da Seth passa"] = ok(j({"tipo": "servico", "param": {"unidade": "seth-gateway.service"}}, {"ativo": True}, "agata-seth · m · t=5 · h\n\nseth-gateway.service: ATIVA (ActiveState=active, SubState=running)"))
    res["serviço ativo: 'não está mais ativa' reprova (contraprova do Codex)"] = not ok(j(c_srv, {"ativo": True}, longo + "A unidade não está mais ativa."))
    res["serviço inativo: 'não está inativa' reprova (contraprova do Codex)"] = not ok(j(c_srv, {"ativo": False}, longo + "A unidade não está inativa."))
    _orig_run = subprocess.run
    for _saida, _rc, _esp in (("not-found\n", 0, {"ativo": False, "existe": False}), ("", 1, None), ("loaded\n", 0, None)):
        subprocess.run = lambda *a, _s=_saida, _r=_rc, **k: subprocess.CompletedProcess(a, _r, _s, "")
        try:
            res[f"verdade da unidade com LoadState {_saida.strip() or 'vazio'!r} (rc={_rc}) -> {_esp}"] = verdade(c_ine, raiz) == _esp
        finally:
            subprocess.run = _orig_run
    # contraprovas do Codex à 1ª versão (18/10/2026): is-active vazio com LoadState loaded, e LoadState=error
    for _ia, _ls, _esp in (("", "loaded\n", None), ("active\n", "error\n", None), ("inactive\n", "loaded\n", {"ativo": False, "existe": True}), ("unknown\n", "loaded\n", None)):
        subprocess.run = lambda a, _ia=_ia, _ls=_ls, **k: subprocess.CompletedProcess(a, 3 if "is-active" in a else 0, _ia if "is-active" in a else _ls, "")
        try:
            res[f"verdade: is-active {_ia.strip() or 'vazio'!r} + LoadState {_ls.strip()!r} -> {_esp}"] = verdade(c_ine, raiz) == _esp
        finally:
            subprocess.run = _orig_run
    res["inexistente: 'não existe e está ativa, sem falha' reprova"] = not ok(j(c_ine, v_ine, longo + "Não existe e está ativa, sem falha."))
    res["inexistente: 'outro inativo; esta ativa' reprova"] = not ok(j(c_ine, v_ine, longo + "Não existe. Outro serviço está inativo; esta unidade está ativa."))
    res["serviço ativo: 'está ativo, sem falha' reprova (fora do formato)"] = not ok(j(c_srv, {"ativo": True}, longo + "Está ativo, sem falha."))
    c_rev = {"tipo": "campo", "param": {"entrada": 743, "regex": r"Revisor pendente: (\w+)"}}
    v_rev = verdade(c_rev, raiz)
    res["campo: revisor da (743) é Codex"] = v_rev == {"valor": "Codex"}
    res["campo: trocar por Claude reprova"] = not ok(j(c_rev, v_rev, longo + "O revisor pendente é Claude Code."))
    res["campo: Codex passa"] = ok(j(c_rev, v_rev, longo + "\nCodex."))
    res["campo: 'Revisor: Codex.' passa"] = ok(j(c_rev, v_rev, longo + "\nRevisor: Codex."))
    res["campo: frase livre reprova (fora do formato)"] = not ok(j(c_rev, v_rev, longo + "\nO revisor pendente é Codex."))
    res["campo: 'O revisor é Claude. Codex.' reprova (contraprova do Codex)"] = not ok(j(c_rev, v_rev, longo + "\nO revisor é Claude. Codex."))
    res["campo: 'O autor é Codex.' reprova (contraprova do Codex)"] = not ok(j(c_rev, v_rev, longo + "\nO autor é Codex."))
    res["campo: 'Claude; Codex é outro modelo' reprova (AC-47)"] = not ok(j(c_rev, v_rev, longo + "O revisor pendente é Claude; Codex é um modelo diferente."))
    res["campo: 'Não foi Codex.' reprova"] = not ok(j(c_rev, v_rev, longo + "Não foi Codex."))
    res["campo: 'ChatGPT; Codex é outro modelo' reprova"] = not ok(j(c_rev, v_rev, "O revisor é ChatGPT; Codex é outro modelo."))
    res["campo: valor de duas palavras ('Claude Code') passa"] = ok(j(c_rev, {"valor": "Claude Code"}, "agata-seth · m · t=1 · h\n\nClaude Code"))
    res["campo: 'Autor: Codex.' reprova (3ª revisão do Codex)"] = not ok(j(c_rev, v_rev, longo + "\nAutor: Codex."))
    res["campo: 'Codex (não foi o revisor).' reprova (3ª revisão do Codex)"] = not ok(j(c_rev, v_rev, longo + "\nCodex (não foi o revisor)."))
    c_gw = {"tipo": "servico", "param": {"unidade": "seth-gateway.service"}}
    res["unidade: parêntese contrário reprova (3ª revisão do Codex)"] = not ok(j(c_gw, {"ativo": True, "existe": True}, longo + "\nATIVA (ActiveState=inactive, SubState=dead)"))
    res["unidade: rótulo de outra unidade reprova (3ª revisão do Codex)"] = not ok(j(c_gw, {"ativo": True, "existe": True}, longo + "\noutra.service: ativa."))
    _gw = lambda s, at=True: ok(j(c_gw, {"ativo": at, "existe": True}, "agata-seth · m · t=1 · h\n\n" + s))
    res["unidade: espaço em '=' com estado contrário reprova (4ª revisão)"] = not _gw("seth-gateway.service: ATIVA (LoadState=loaded, ActiveState = inactive)")
    res["unidade: INATIVA com ActiveState = active reprova (4ª revisão)"] = not _gw("seth-gateway.service: INATIVA (LoadState=loaded, ActiveState = active)", False)
    res["unidade: espaços em '=' com estado certo passa (4ª revisão)"] = _gw("seth-gateway.service: ATIVA (LoadState = loaded, ActiveState = active)")
    res["unidade: ActiveState=unknown reprova (4ª revisão)"] = not _gw("seth-gateway.service: INATIVA (ActiveState=unknown)", False)
    res["unidade: texto livre no parêntese reprova (4ª revisão)"] = not ok(j(c_ine, v_ine, longo + "\nNÃO EXISTE (unidade encontrada e carregada)"))
    res["unidade: só LoadState=loaded passa, ativa (5ª revisão)"] = _gw("seth-gateway.service: ATIVA (LoadState=loaded)")
    res["unidade: só LoadState=loaded passa, inativa (5ª revisão)"] = _gw("seth-gateway.service: INATIVA (LoadState=loaded)", False)
    res["unidade: ActiveState=active com SubState=dead reprova (5ª revisão)"] = not _gw("seth-gateway.service: ATIVA (ActiveState=active, SubState=dead)")
    res["unidade: NÃO EXISTE com SubState=running reprova (5ª revisão)"] = not ok(j(c_ine, v_ine, longo + "\nNÃO EXISTE (LoadState=not-found, SubState=running)"))
    res["unidade: rótulo da própria unidade passa"] = ok(j(c_gw, {"ativo": True, "existe": True}, longo + "\nseth-gateway.service: ATIVA (ActiveState=active, SubState=running)"))
    res["campo: cabeçalho com 'Última entrada' não atrapalha"] = ok(j(c_rev, v_rev, "agata-seth · m · t=1 · h\nÚltima entrada: (770) DIÁRIO — Claude Code fez x\npronto.\n\nCodex"))
    res["abstenção sem a flag do caso reprova"] = not ok(j(c_cte, v_cte, longo + 'Não achei a linha das constantes na busca; não medido.'))
    res["abstenção com valor errado afirmado reprova"] = not ok(j(c_abs, v_cte, longo + 'Não achei, mas chuto MIN_NOVOS = 99; não medido.'))
    res["verdade incalculável reprova"] = not ok(j(c_num, None, longo))
    res["resposta vazia reprova"] = not ok(j(c_cte, v_cte, ""))
    for k, v in res.items():
        print(("OK    " if v else "FALHOU"), k)
    print(f"seth_golden selftest: {sum(bool(v) for v in res.values())}/{len(res)}")
    return 0 if all(res.values()) else 1


def main(argv):
    if argv[:1] == ["--selftest"]:
        return _selftest()
    if argv[:1] == ["--listar"]:
        for c in carregar():
            print(f"{c['id']}  [{c['tipo']}]  {c['pergunta']}")
        return 0
    if len(argv) == 2 and argv[0] in ("--pontuar", "--banco"):
        caso = _caso_por_id(argv[1])
        if not caso:
            print(f"caso '{argv[1]}' não existe (use --listar)")
            return 2
        texto = sys.stdin.read() if argv[0] == "--pontuar" else _ultima_resposta_banco()
        v = verdade(caso)
        print(f"caso {caso['id']}: {caso['pergunta']}")
        return _imprimir(julgar(caso, v, texto))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
