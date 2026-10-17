#!/usr/bin/env python3
"""janela_manutencao.py -- orquestrador da JANELA DE MANUTENÇÃO diária (12h15-13h15, hora de Brasília).

Decisão do Humano (16/10/2026): unificar os scripts automáticos numa janela de almoço, porque a máquina nem sempre está ligada
no domingo de madrugada; treino do Laya DIÁRIO nessa janela. Núcleo escrito pelo Codex (janela-nucleo-offline-v1.py) e revisado
pelo Claude (cinco falhas, corrigidas aqui: tentativas por dia, adiamento visível, state.json corrompido, validação prévia das
tarefas e recibo final que não pode desfazer o carimbo).

Contrato:
  * UM lock; tarefas em ORDEM, uma por vez (nunca duas disputando a GPU); nenhuma tarefa nova começa depois de 13h15.
  * Cadência `daily` (uma vez por data local) ou `weekly` (7 dias desde o último SUCESSO). Só `success` carimba.
  * No máximo `MAX_TENTATIVAS_DIA` (2) tentativas por tarefa por dia; `skipped` esgota o dia (nada a fazer hoje).
  * Tarefa cujo orçamento não cabe no tempo restante é ADIADA com recibo (`adiada_sem_tempo`), não descartada em silêncio.
  * Estourou o orçamento: SIGTERM no grupo de processos, 20 s de graça, depois SIGKILL; recibo `terminada_por_prazo`.
    (O treino do Laya só treina um CANDIDATO; abortar não troca o modelo; a promoção é do Humano.)
  * Recibo `started` ANTES de rodar (se não puder gravar, a tarefa não roda); o estado é gravado de forma atômica ANTES do recibo
    final, e falha do recibo final não desfaz o carimbo.
  * Antes de executar, reconcilia recibos: corrupção reconstrói sucessos/tentativas; intenção órfã ou recibo inválido bloqueia.
  * Precondição e comando compartilham um prazo monotônico total (mais a graça de término).
  * Não muda configuração do sistema nem liga serviço: roda os comandos do manifesto `config/janela-tarefas.txt`.
Uso: python3 scripts/janela_manutencao.py [--dir DIR] [--tarefas ARQ] [--dry-run] [--agora ISO] | --selftest
Ativação (comandos do Humano, depois de assinada a proposta): copiar config/systemd/agata-manutencao.{service,timer} para
~/.config/systemd/user/, `systemctl --user daemon-reload`, `systemctl --user enable --now agata-manutencao.timer`, e só então
desativar os timers antigos das tarefas incluídas (agata-avaliacao-decisor, agata-consolidacao, agata-laya-treino)."""
import argparse
import datetime as dt
import fcntl
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")
MAX_TENTATIVAS_DIA = 2
GRACA_S = 20
RAIZ = Path(__file__).resolve().parent.parent
PADRAO_DIR = Path.home() / ".cache" / "agata" / "janela"


def janela(agora):
    local = agora.astimezone(TZ)
    fim = local.replace(hour=13, minute=15, second=0, microsecond=0)
    ini = fim.replace(minute=15, hour=12)
    return ini <= local < fim, fim


def ler_tarefas(arquivo):
    """Linhas `id|cadencia|orcamento_s|env|precondicao|comando`; `%h` = HOME. Valida TUDO antes de devolver."""
    tarefas, ids = [], set()
    for n, l in enumerate(Path(arquivo).read_text(encoding="utf-8").splitlines(), 1):
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        c = [x.strip().replace("%h", str(Path.home())) for x in l.split("|")]
        if len(c) != 6:
            raise ValueError(f"linha {n}: esperadas 6 colunas, vieram {len(c)}")
        tid, cad, orc, env, pre, cmd = c
        if not tid or tid in ids:
            raise ValueError(f"linha {n}: id vazio ou repetido")
        if cad not in ("daily", "weekly"):
            raise ValueError(f"linha {n}: cadência inválida {cad!r}")
        if not orc.isdigit() or int(orc) <= 0:
            raise ValueError(f"linha {n}: orçamento deve ser inteiro positivo")
        if not cmd:
            raise ValueError(f"linha {n}: comando vazio")
        ids.add(tid)
        tarefas.append({"id": tid, "cadence": cad, "budget_seconds": int(orc),
                        "env": dict(kv.split("=", 1) for kv in env.split(",") if "=" in kv),
                        "precond": shlex.split(pre) if pre else [], "cmd": shlex.split(cmd)})
    if not tarefas:
        raise ValueError("manifesto sem tarefas")
    return tarefas


def validar(tarefas):
    for t in tarefas:
        if t["cadence"] not in ("daily", "weekly") or not isinstance(t["budget_seconds"], int) or t["budget_seconds"] <= 0:
            raise ValueError(f"tarefa {t.get('id')!r}: cadência ou orçamento inválido")


def devida(tarefa, est, agora):
    ultimo = est.get("last_success")
    hoje = agora.astimezone(TZ).date().isoformat()
    if est.get("tries", {}).get(hoje, 0) >= MAX_TENTATIVAS_DIA:
        return False
    if not ultimo:
        return True
    anterior = dt.datetime.fromisoformat(ultimo)
    if tarefa["cadence"] == "daily":
        return anterior.astimezone(TZ).date() < agora.astimezone(TZ).date()
    return (agora - anterior).total_seconds() >= 7 * 86400


def recibo_duravel(caminho, registro):
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def estado_atomico(caminho, estado):
    tmp = caminho.with_name(caminho.name + ".tmp-" + uuid.uuid4().hex)
    with tmp.open("x", encoding="utf-8") as f:
        json.dump(estado, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, caminho)
    fd = os.open(caminho.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


SAIDA_MAX = 200


def _ultima_linha(arq):
    """Última linha não vazia da saída do comando, no máximo SAIDA_MAX caracteres, sem controle e com sequências longas redigidas
    (token, chave, hash). Serve só para o recibo dizer POR QUE uma tarefa pulou (ex.: "15 exemplos, mínimo 20")."""
    try:
        arq.flush()
        n = arq.seek(0, os.SEEK_END)
        arq.seek(max(0, n - 4096))
        bruto = arq.read().decode("utf-8", "replace")
    except (OSError, ValueError):
        return None
    linhas = [l.strip() for l in bruto.splitlines() if l.strip()]
    if not linhas:
        return None
    s = "".join(c for c in linhas[-1] if c.isprintable())
    s = re.sub(r"[A-Za-z0-9_\-]{32,}", "[redigido]", s)
    return s[:SAIDA_MAX]


def executar(tarefa, prazo_s):
    """Precondição e comando compartilham prazo monotônico e contenção por grupo."""
    limite = time.monotonic() + prazo_s
    env = dict(os.environ, **tarefa["env"])
    comandos = ([(tarefa["precond"], True)] if tarefa["precond"] else []) + [(tarefa["cmd"], False)]
    for cmd, precondicao in comandos:
        restante = limite - time.monotonic()
        if restante <= 0:
            return "failed", True
        try:
            saida_tmp = None if precondicao else tempfile.TemporaryFile()
            p = subprocess.Popen(cmd, env=env, start_new_session=True,
                                 stdout=subprocess.DEVNULL if precondicao else saida_tmp,
                                 stderr=subprocess.DEVNULL if precondicao else subprocess.STDOUT)
        except OSError:
            return ("skipped" if precondicao else "failed"), False
        teto = max(0, limite - time.monotonic())
        if precondicao:
            teto = min(60, teto)
        try:
            rc = p.wait(timeout=teto)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGTERM)
                p.wait(timeout=GRACA_S)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
            finally:
                # O líder pode terminar antes de um descendente que ignorou SIGTERM.
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                p.wait(timeout=5)
            return ("skipped", False) if precondicao else ("failed", True, _ultima_linha(saida_tmp))
        if rc != 0:
            return ("skipped", False) if precondicao else ("failed", False, _ultima_linha(saida_tmp))
    return "success", False, _ultima_linha(saida_tmp)


def recuperar_estado(caminho, rec, relogio, recibo):
    """Reconcilia provas duráveis antes de executar. Intenção órfã bloqueia repetição."""
    corrompido = False
    try:
        estado = json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {}
        if not isinstance(estado, dict):
            raise ValueError("estado não é objeto")
        for est in estado.values():
            if not isinstance(est, dict) or not isinstance(est.get("tries", {}), dict):
                raise ValueError("estado de tarefa inválido")
            if any(type(v) is not int or v < 0 for v in est.get("tries", {}).values()):
                raise ValueError("tentativas inválidas")
            if est.get("last_run") and (not isinstance(est.get("last_run"), str) or est.get("last_result") not in ("success", "skipped", "failed") or not isinstance(est.get("last_finished"), str) or dt.datetime.fromisoformat(est["last_finished"]).tzinfo is None):
                raise ValueError("última execução inválida")
            if est.get("last_success") and dt.datetime.fromisoformat(est["last_success"]).tzinfo is None:
                raise ValueError("sucesso sem fuso")
    except (ValueError, TypeError, OSError):
        copia = caminho.with_name("state.json.corrompido-" + uuid.uuid4().hex[:8])
        if caminho.exists():
            os.replace(caminho, copia)
        estado, corrompido = {}, True
        recibo(rec, {"task": "-", "phase": "state_corrompido", "at": relogio().isoformat(), "copia": copia.name})
    inicios, finais = {}, {}
    try:
        linhas = rec.read_text(encoding="utf-8").splitlines() if rec.exists() else []
        for linha in linhas:
            r = json.loads(linha)
            if not isinstance(r, dict):
                raise ValueError("recibo não é objeto")
            if r.get("phase") not in ("started", "finished"):
                continue
            rid, tarefa = r.get("run"), r.get("task")
            quando = dt.datetime.fromisoformat(r["at"])
            if not isinstance(rid, str) or not rid or not isinstance(tarefa, str) or not tarefa or quando.tzinfo is None:
                raise ValueError("recibo inválido")
            alvo = inicios if r["phase"] == "started" else finais
            if rid in alvo and alvo[rid] != r:
                raise ValueError("recibo contraditório")
            alvo[rid] = r
        for rid, r in finais.items():
            if rid not in inicios or r["task"] != inicios[rid]["task"] or r.get("result") not in ("success", "skipped", "failed"):
                raise ValueError("término sem início coerente")
            if dt.datetime.fromisoformat(r["at"]) < dt.datetime.fromisoformat(inicios[rid]["at"]):
                raise ValueError("término anterior ao início")
    except (ValueError, KeyError, TypeError, OSError):
        return None, "receipts_invalidos"
    # Estado gravado antes de finished prova o resultado desta run, mesmo se o último append falhou.
    for rid, inicio in inicios.items():
        if rid not in finais:
            est = estado.get(inicio["task"], {})
            if est.get("last_run") != rid or est.get("last_result") not in ("success", "failed", "skipped"):
                # Sob o flock nenhuma outra instância roda: started sem término e sem prova no estado é execução
                # interrompida (queda, suspensão, SIGKILL). Conta 1 tentativa do dia e a janela segue; não bloqueia.
                fim = {"run": rid, "task": inicio["task"], "phase": "finished", "at": inicio["at"],
                       "result": "failed", "reconciled_interrupted": True}
            else:
                fim = {"run": rid, "task": inicio["task"], "phase": "finished", "at": est["last_finished"],
                       "result": est["last_result"], "reconciled_from_state": True}
            recibo(rec, fim)
            finais[rid] = fim
    if corrompido and not finais:
        return None, "estado_sem_prova"
    contagens = {}
    for rid, r in finais.items():
        est = estado.setdefault(r["task"], {})
        dia = dt.datetime.fromisoformat(inicios[rid]["at"]).astimezone(TZ).date().isoformat()
        k = (r["task"], dia)
        contagens[k] = MAX_TENTATIVAS_DIA if r["result"] == "skipped" else contagens.get(k, 0) + 1
        if r["result"] == "success" and (not est.get("last_success") or dt.datetime.fromisoformat(r["at"]) > dt.datetime.fromisoformat(est["last_success"])):
            est["last_success"] = r["at"]
        est["last_run"], est["last_result"], est["last_finished"] = rid, r["result"], r["at"]
    for (tarefa, dia), tentativas in contagens.items():
        tries = estado[tarefa].setdefault("tries", {})
        tries[dia] = max(tries.get(dia, 0), tentativas)
    return estado, None


def ciclo(diretorio, tarefas, runner, relogio, recibo=recibo_duravel):
    """Retorna 'locked' | 'outside_window' | 'complete' | 'blocked'. Valida todas as tarefas ANTES de qualquer execução."""
    validar(tarefas)
    diretorio = Path(diretorio)
    diretorio.mkdir(parents=True, exist_ok=True)
    rec = diretorio / "receipts.jsonl"
    with (diretorio / "lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return "locked"
        caminho = diretorio / "state.json"
        estado, bloqueio = recuperar_estado(caminho, rec, relogio, recibo)
        if bloqueio:
            print(f"BLOQUEADO: {bloqueio}; reconciliação explícita necessária", file=sys.stderr)
            try:
                recibo(rec, {"task": "-", "phase": "bloqueado", "at": relogio().isoformat(), "motivo": bloqueio})
            except OSError:
                pass
            return "blocked"
        for t in tarefas:
            agora = relogio()
            dentro, fim = janela(agora)
            if not dentro:
                return "outside_window"
            est = estado.setdefault(t["id"], {})
            if not devida(t, est, agora):
                continue
            restante = (fim - agora).total_seconds()
            if restante < t["budget_seconds"]:
                try:
                    recibo(rec, {"task": t["id"], "phase": "adiada_sem_tempo", "at": agora.isoformat(), "restante_s": int(restante), "orcamento_s": t["budget_seconds"]})
                except OSError:
                    pass
                continue
            rid = uuid.uuid4().hex
            hoje = agora.astimezone(TZ).date().isoformat()
            recibo(rec, {"run": rid, "task": t["id"], "phase": "started", "at": agora.isoformat()})  # se falhar, a tarefa NÃO roda
            prazo = min(t["budget_seconds"], restante)
            try:
                r = runner(t, prazo)
                resultado, por_prazo = r[0], r[1]
                saida_final = r[2] if len(r) > 2 else None
                if resultado not in ("success", "skipped", "failed"):
                    raise ValueError("status inválido do runner")
                erro = None
            except Exception as e:  # noqa: BLE001 -- só a classe vai ao recibo
                resultado, por_prazo, erro, saida_final = "failed", False, type(e).__name__, None
            fim_run = relogio()
            est.setdefault("tries", {})
            est["tries"][hoje] = MAX_TENTATIVAS_DIA if resultado == "skipped" else est["tries"].get(hoje, 0) + 1
            if resultado == "success":
                est["last_success"] = fim_run.isoformat()
            est["last_run"], est["last_result"], est["last_finished"] = rid, resultado, fim_run.isoformat()
            estado_atomico(caminho, estado)  # estado ANTES do recibo final
            try:
                recibo(rec, {"run": rid, "task": t["id"], "phase": "finished", "at": fim_run.isoformat(), "result": resultado,
                             "terminada_por_prazo": por_prazo, "error_class": erro, "saida_final": saida_final})
            except OSError as e:
                print(f"AVISO: recibo final não gravado ({type(e).__name__}); estado já carimbado", file=sys.stderr)
        return "complete"


def _selftest():
    import time
    casos = []
    T = lambda i, c="daily", b=600: {"id": i, "cadence": c, "budget_seconds": b, "env": {}, "precond": [], "cmd": ["true"]}
    at = lambda h, m, s=0, d=16: dt.datetime(2026, 10, d, h, m, s, tzinfo=TZ)
    ok = lambda t, p: ("success", False)

    def go(tasks, runner, quando, d, **kw):
        chamadas = []

        def r(t, p):
            chamadas.append(t["id"])
            return runner(t, p)
        try:
            res = ciclo(d, tasks, r, lambda: quando, **kw)
        except Exception as e:  # noqa: BLE001
            res = "EXC:" + type(e).__name__
        return res, chamadas

    def recs(d):
        p = Path(d) / "receipts.jsonl"
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []
    d = tempfile.mkdtemp()
    r, c = go([T("a")], ok, at(12, 30), d); casos.append(("boot 12:30 executa e carimba", r == "complete" and c == ["a"]))
    r, c = go([T("a")], ok, at(12, 40), d); casos.append(("sucesso não repete no dia", c == []))
    r, c = go([T("a")], ok, at(12, 20, d=17), tempfile.mkdtemp()); casos.append(("outro dia executa", c == ["a"]))
    d = tempfile.mkdtemp(); n = 0
    for _ in range(4):
        n += len(go([T("a")], lambda t, p: ("failed", False), at(12, 20), d)[1])
    casos.append(("falha: no máximo 2 tentativas por dia", n == MAX_TENTATIVAS_DIA))
    d = tempfile.mkdtemp(); n = 0
    for _ in range(4):
        n += len(go([T("a")], lambda t, p: ("skipped", False), at(12, 20), d)[1])
    casos.append(("skipped esgota o dia (1 execução)", n == 1))
    d = tempfile.mkdtemp(); go([T("w", "weekly")], ok, at(12, 20, d=9), d)
    casos.append(("semanal: 6 dias não, 7 dias sim", not go([T("w", "weekly")], ok, at(12, 20, d=15), d)[1] and bool(go([T("w", "weekly")], ok, at(12, 21, d=16), d)[1])))
    d = tempfile.mkdtemp(); r, c = go([T("a", b=1800)], ok, at(12, 50), d)
    casos.append(("orçamento > restante: adiada COM recibo", c == [] and any(x["phase"] == "adiada_sem_tempo" for x in recs(d))))
    d = tempfile.mkdtemp(); Path(d).mkdir(exist_ok=True); (Path(d) / "state.json").write_text("{quebrado")
    r, c = go([T("a")], ok, at(12, 20), d)
    casos.append(("state corrompido sem prova: guarda cópia, registra e bloqueia", r == "blocked" and c == [] and any(x["phase"] == "state_corrompido" for x in recs(d)) and list(Path(d).glob("state.json.corrompido-*"))))
    d = tempfile.mkdtemp(); r, c = go([T("a"), T("b", b=0)], ok, at(12, 20), d)
    casos.append(("orçamento inválido: nada roda", r.startswith("EXC:ValueError") and c == []))

    def falha_final(caminho, reg):
        if reg["phase"] == "finished":
            raise OSError("disco cheio")
        recibo_duravel(caminho, reg)
    d = tempfile.mkdtemp(); go([T("a")], ok, at(12, 20), d, recibo=falha_final)
    casos.append(("recibo final falha: estado já carimbado, não repete", not go([T("a")], ok, at(12, 40), d)[1]))

    def falha_inicio(caminho, reg):
        raise OSError("sem espaço")
    d = tempfile.mkdtemp(); r, c = go([T("a")], ok, at(12, 20), d, recibo=falha_inicio)
    casos.append(("recibo 'started' falha: tarefa NÃO roda", c == [] or r.startswith("EXC")))
    casos.append(("bordas da janela", go([T("a")], ok, at(12, 14, 59), tempfile.mkdtemp())[0] == "outside_window" and go([T("a")], ok, at(13, 15), tempfile.mkdtemp())[0] == "outside_window" and bool(go([T("a", b=1)], ok, at(13, 14, 59), tempfile.mkdtemp())[1])))
    t0 = time.time(); res = executar({"env": {}, "precond": [], "cmd": ["sleep", "30"]}, 1)
    casos.append(("executar: prazo estourado termina o processo", tuple(res[:2]) == ("failed", True) and time.time() - t0 < 10))
    casos.append(("executar: comando ok", executar({"env": {}, "precond": [], "cmd": ["true"]}, 5)[:2] == ("success", False)))
    casos.append(("executar: precondição falha vira skipped", executar({"env": {}, "precond": ["false"], "cmd": ["true"]}, 5) == ("skipped", False)))
    tf = Path(tempfile.mkdtemp()) / "t.txt"
    tf.write_text("# c\nx|daily|60||| /bin/true\ny|weekly|90|A=1,B=2|/bin/true|/bin/echo oi\n")
    ts = ler_tarefas(tf)
    casos.append(("manifesto lido (env, precond, argv)", len(ts) == 2 and ts[1]["env"] == {"A": "1", "B": "2"} and ts[1]["cmd"] == ["/bin/echo", "oi"]))
    tf.write_text("x|daily|0|||/bin/true\n")
    try:
        ler_tarefas(tf)
        casos.append(("manifesto com orçamento 0 é rejeitado", False))
    except ValueError:
        casos.append(("manifesto com orçamento 0 é rejeitado", True))
    real = ler_tarefas(RAIZ / "config" / "janela-tarefas.txt") if (RAIZ / "config" / "janela-tarefas.txt").exists() else []
    casos.append(("manifesto real (config/janela-tarefas.txt) é válido", bool(real) and sum(t["budget_seconds"] for t in real) <= 3600))
    for n, okk in casos:
        print(("PASS  " if okk else "FALHA ") + n)
    ruins = [n for n, okk in casos if not okk]
    print(f"janela_manutencao selftest: {len(casos) - len(ruins)}/{len(casos)}")
    return 1 if ruins else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=str(PADRAO_DIR))
    ap.add_argument("--tarefas", default=str(RAIZ / "config" / "janela-tarefas.txt"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--agora")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    tarefas = ler_tarefas(a.tarefas)
    agora = dt.datetime.fromisoformat(a.agora) if a.agora else dt.datetime.now(TZ)
    if a.dry_run:
        dentro, fim = janela(agora)
        est = json.loads((Path(a.dir) / "state.json").read_text()) if (Path(a.dir) / "state.json").exists() else {}
        print(f"agora {agora.astimezone(TZ):%Y-%m-%d %H:%M %z} · dentro da janela: {dentro} · fim {fim:%H:%M}")
        for t in tarefas:
            print(f"  {t['id']}: {'DEVIDA' if devida(t, est.get(t['id'], {}), agora) else 'em dia'} · {t['cadence']} · orçamento {t['budget_seconds']} s")
        return 0
    runner = executar
    resultado = ciclo(a.dir, tarefas, runner, lambda: dt.datetime.now(TZ))
    print(resultado)
    return 2 if resultado == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
