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
        return {"ativo": r.stdout.strip() == "active", "existe": ex.stdout.strip() != "not-found"}
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
        neg = re.search(r"\b(nao esta ativ|inativ|nao ativo|falh)", r) is not None
        pos = re.search(r"\b(ativo|active|rodando)\b", r) is not None
        nex = re.search(r"(nao existe|inexistente|not-found|nao encontr)", r) is not None
        if not v.get("existe", True):
            crit.append(("diz que a unidade não existe", nex and not (pos and not neg and not nex), "inexistente"))
        else:
            crit.append(("estado do serviço", ((pos and not neg) if v["ativo"] else (neg or not pos)) and not nex, "ativo" if v["ativo"] else "inativo"))
    elif t == "campo":
        crit.append((f"diz {v['valor']}", re.search(rf"\b{re.escape(v['valor'])}\b", resposta) is not None, v["valor"]))
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
    res["serviço ativo: 'está ativo' passa"] = ok(j(c_srv, {"ativo": True}, longo + "O laya-roteador.service está ativo."))
    res["serviço ativo: 'Não' falha (o erro de hoje)"] = not ok(j(c_srv, {"ativo": True}, longo + "Não, o serviço não está ativo; a unidade X falhou."))
    v_per = {"geral": "OK", "ok": 20, "skip": 1, "parcial": 2, "falha": 0, "parciais": ["P-4", "P-12"]}
    res["perímetro certo passa"] = ok(j(c_per, v_per, longo + "Geral OK, 20 OK, 2 PARCIAL: P-4 e P-12."))
    res["perímetro sem o P-12 falha"] = not ok(j(c_per, v_per, longo + "Geral OK, 20 OK, 2 PARCIAL: P-4."))
    c_abs = dict(c_cte, aceita_abstencao=True)
    res["abstenção honesta passa quando o caso a admite"] = ok(j(c_abs, v_cte, longo + 'Não achei a linha das constantes na busca; não medido.'))
    res["abstenção honesta passa mesmo com a linha 'Última entrada: (761)' depois do cabeçalho"] = ok(j(c_abs, v_cte, "agata-seth · m · t=1 · h\nÚltima entrada: (761) DIÁRIO — x\npronto.\n\nNão achei."))
    c_ine = {"tipo": "servico", "param": {"unidade": "agata-consolidacao.timer"}}
    v_ine = verdade(c_ine, raiz)
    res["unidade inexistente: verdade existe=False"] = v_ine == {"ativo": False, "existe": False}
    res["unidade inexistente: 'ativa' reprova"] = not ok(j(c_ine, v_ine, longo + "Ela existe e está ativa."))
    res["unidade inexistente: 'não existe' passa"] = ok(j(c_ine, v_ine, longo + "Não existe: LoadState not-found."))
    c_rev = {"tipo": "campo", "param": {"entrada": 743, "regex": r"Revisor pendente: (\w+)"}}
    v_rev = verdade(c_rev, raiz)
    res["campo: revisor da (743) é Codex"] = v_rev == {"valor": "Codex"}
    res["campo: trocar por Claude reprova"] = not ok(j(c_rev, v_rev, longo + "O revisor pendente é Claude Code."))
    res["campo: Codex passa"] = ok(j(c_rev, v_rev, longo + 'O revisor pendente é Codex.'))
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
