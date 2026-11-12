#!/usr/bin/env python3
"""Contador mecânico de turno da Agata (decisão do Humano, 12/11/2026, entrevista P1).

Turno = uma resposta do modelo que devolve o controle ao Humano. Chamadas de
ferramenta e subagentes dentro dela não contam. O contador é POR SESSÃO, fica na
Máquina e avança a cada mensagem do Humano: no Claude Code, o gancho
UserPromptSubmit chama `hook` e injeta a linha pronta; nas CLIs sem gancho, o
modelo roda `proximo` no início da resposta. O modelo só copia a linha; não
recalcula o t.

Uso:
  python3 scripts/turno.py proximo --sessao ID [--modelo M]  avança e imprime a linha
  python3 scripts/turno.py atual   --sessao ID [--modelo M]  linha do turno atual, sem avançar
  python3 scripts/turno.py sub     --sessao ID [--modelo M]  subagente: t=<n>.sub, sem avançar
  python3 scripts/turno.py hook                              gancho UserPromptSubmit (JSON na entrada)
  python3 scripts/turno.py --selftest

Estado: $AGATA_TURNOS_DIR ou ~/.cache/agata/turnos/<sessao>.json (modo 0600), com
trava <sessao>.lock (flock) e escrita atômica (arquivo temporário + os.replace).
Arquivo corrompido: `proximo` recomeça em 1 com a marca "contador reiniciado".
Sem dependências além da biblioteca padrão.
Saídas: 0 ok · 1 atual/sub sem contador válido · 2 id inválido ou erro de disco.
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import re
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))
MODELO_PADRAO = "modelo não verificado"
BASE = "contador mecânico"
BASE_REINICIADO = "contador mecânico; contador reiniciado"
PRAZO_TRAVA = 5.0
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_BYTES_TRANSCRIPT = 262144  # só o fim do transcrito: o último modelo do assistente está ali


class ErroSessao(ValueError):
    """Id de sessão fora do formato aceito."""


class SemContador(RuntimeError):
    """atual/sub sem contador válido: sessão sem turno ou arquivo corrompido."""


def diretorio() -> Path:
    return Path(os.environ.get("AGATA_TURNOS_DIR") or "~/.cache/agata/turnos").expanduser()


def _caminhos(sessao) -> tuple[Path, Path]:
    if not isinstance(sessao, str) or not _ID.fullmatch(sessao):
        raise ErroSessao("id de sessão inválido: use letras, números, '.', '_' ou '-' "
                         "(até 128 caracteres, começando por letra ou número)")
    d = diretorio()
    return d / f"{sessao}.json", d / f"{sessao}.lock"


def _hora() -> str:
    # Regional com fuso e selo (PROTOCOLOS.md, Regra 1.1). Sem horário de verão desde 2019: -03 fixo.
    return datetime.now(timezone.utc).astimezone(BRT).strftime("%d/%m/%Y %H:%M") + " -03 (relógio da Máquina)"


def _modelo(m) -> str:
    if not isinstance(m, str):
        return MODELO_PADRAO
    limpo = " ".join(m.replace("·", " ").split())[:80]
    return limpo or MODELO_PADRAO


def linha(modelo, t: int, base: str = BASE) -> str:
    return f"agata · {_modelo(modelo)} · t={t} ({base}) · {_hora()}"


def linha_sub(modelo, t: int) -> str:
    return f"agata · {_modelo(modelo)} · t={t}.sub (contador mecânico, subagente) · {_hora()}"


def _ler(caminho: Path) -> tuple[int | None, bool]:
    """(t, corrompido). Arquivo ausente = (None, False)."""
    try:
        bruto = caminho.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, False
    except (OSError, UnicodeDecodeError):
        return None, True
    try:
        dados = json.loads(bruto)
    except ValueError:
        return None, True
    t = dados.get("t") if isinstance(dados, dict) else None
    if isinstance(t, bool) or not isinstance(t, int) or t < 0:
        return None, True
    return t, False


def _gravar(caminho: Path, sessao: str, t: int) -> None:
    dados = {"versao": 1, "sessao": sessao, "t": t,
             "atualizado": datetime.now(BRT).isoformat(timespec="seconds")}
    fd, tmp = tempfile.mkstemp(dir=str(caminho.parent), prefix=f".{sessao}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, caminho)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


@contextlib.contextmanager
def _trava(caminho: Path, prazo: float = PRAZO_TRAVA):
    # Um fd novo por chamada: o flock conflita entre processos e entre threads.
    fd = os.open(caminho, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        limite = time.monotonic() + prazo
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > limite:
                    raise TimeoutError(f"contador ocupado por outro processo ({prazo:.0f} s)")
                time.sleep(0.01)
        yield
    finally:
        os.close(fd)  # fechar o fd solta o flock


def _avancar(sessao: str, modelo) -> tuple[int, str, str]:
    """(t, base, linha). Leitura e escrita acontecem sob a mesma trava."""
    caminho, trava = _caminhos(sessao)
    caminho.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with _trava(trava):
        t, corrompido = _ler(caminho)
        if corrompido:
            novo, base = 1, BASE_REINICIADO
            print("turno: contador da sessão corrompido; reiniciado em 1 (marca no cabeçalho)",
                  file=sys.stderr)
        elif t is None:
            novo, base = 1, BASE
        else:
            novo, base = t + 1, BASE
        _gravar(caminho, sessao, novo)
    return novo, base, linha(modelo, novo, base)


def proximo(sessao: str, modelo=MODELO_PADRAO) -> str:
    return _avancar(sessao, modelo)[2]


def _t_atual(sessao: str) -> int:
    caminho, _ = _caminhos(sessao)
    t, corrompido = _ler(caminho)
    if corrompido:
        raise SemContador("contador da sessão corrompido: rode proximo (ele reinicia com a marca)")
    if t is None:
        raise SemContador("sessão sem turno: rode proximo antes")
    return t


def atual(sessao: str, modelo=MODELO_PADRAO) -> str:
    return linha(modelo, _t_atual(sessao))


def subagente(sessao: str, modelo=MODELO_PADRAO) -> str:
    """Subagente herda o turno do pai: t=<n>.sub, sem avançar."""
    return linha_sub(modelo, _t_atual(sessao))


def atual_da_sessao(sessao) -> int | None:
    """Para a auditoria: o t do contador, ou None quando não há contador válido (nada a acusar)."""
    try:
        return _t_atual(sessao)
    except (SemContador, ErroSessao, OSError):
        return None


def _modelo_do_transcript(caminho) -> str | None:
    """Último modelo do assistente gravado no transcrito (medido, não lembrado). None se não houver."""
    if not isinstance(caminho, str) or not caminho:
        return None
    try:
        with Path(caminho).expanduser().open("rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - _BYTES_TRANSCRIPT))
            bloco = f.read().decode("utf-8", "replace")
    except (OSError, ValueError):
        return None
    for l in reversed(bloco.splitlines()):
        if '"model"' not in l:
            continue
        try:
            obj = json.loads(l)
        except ValueError:
            continue  # a 1ª linha do bloco pode ter sido cortada
        msg = obj.get("message") if isinstance(obj, dict) else None
        m = msg.get("model") if isinstance(msg, dict) else None
        if isinstance(m, str) and m and m != "<synthetic>":
            return m
    return None


def hook(entrada: str, ambiente=None) -> str:
    """Gancho UserPromptSubmit. Entrada: JSON do Claude Code (session_id; model ou transcript_path).
    Saída: JSON com hookSpecificOutput.additionalContext, ou "" (sem sessão, erro, entrada inválida).
    Nunca levanta exceção: o gancho não pode travar o prompt."""
    ambiente = os.environ if ambiente is None else ambiente
    try:
        dados = json.loads(entrada) if entrada and entrada.strip() else {}
        if not isinstance(dados, dict):
            dados = {}
        sessao = dados.get("session_id") or ambiente.get("CLAUDE_SESSION_ID") or ""
        if not isinstance(sessao, str) or not sessao:
            return ""
        modelo_payload = dados.get("model")
        if isinstance(modelo_payload, str) and modelo_payload.strip():
            modelo = _modelo(modelo_payload)
        else:
            modelo = _modelo(_modelo_do_transcript(dados.get("transcript_path")))
        t, base, cab = _avancar(sessao, modelo)
    except Exception as e:  # noqa: BLE001 -- o gancho nunca derruba o prompt
        print(f"turno: gancho sem linha de turno ({type(e).__name__}: {e})", file=sys.stderr)
        return ""
    if t == 1:
        marca = " Contador reiniciado (arquivo corrompido): t=1." if "reiniciado" in base else ""
        principal = ("Cabeçalho deste turno: 1ª resposta desta sessão. Abra com o bloco de prontidão "
                     "(PROTOCOLOS.md, \"Carregar e formatos\"), sem linha t=." + marca)
    else:
        principal = (f"Cabeçalho deste turno: {cab}\n"
                     "Copie a linha como abertura da resposta (REGRAS.md, Regra 1); não recalcule o t. "
                     f"Subagente: t=<n>.sub com `python3 scripts/turno.py sub --sessao {sessao}`.")
    contexto = (f"{principal}\nSessão para turno.py e auditoria_turno.py --verificar --sessao: {sessao}")
    return json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                              "additionalContext": contexto}}, ensure_ascii=False)


def _selftest() -> int:
    """Checagens rápidas em diretório temporário. Os casos completos estão em scripts/testar_turno.py."""
    antes = os.environ.get("AGATA_TURNOS_DIR")
    res: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["AGATA_TURNOS_DIR"] = tmp
        try:
            res.append(("sessão nova começa em 1", "t=1 (contador mecânico)" in proximo("st-a")))
            res.append(("soma 1 a cada chamada", "t=2 (contador mecânico)" in proximo("st-a")))
            res.append(("sub imprime t=<n>.sub sem avançar",
                        "t=2.sub" in subagente("st-a") and "t=2 (" in atual("st-a")))
            try:
                proximo("../fora")
                res.append(("id com '..' é recusado", False))
            except ErroSessao:
                res.append(("id com '..' é recusado", True))
            Path(tmp, "st-b.json").write_text("{não é json", encoding="utf-8")
            res.append(("arquivo corrompido reinicia com a marca",
                        "t=1 (contador mecânico; contador reiniciado)" in proximo("st-b")))
            ids = []
            ts = [threading.Thread(target=lambda: ids.extend(
                int(re.search(r"t=(\d+)", proximo("st-c")).group(1)) for _ in range(10))) for _ in range(6)]
            [t.start() for t in ts]
            [t.join() for t in ts]
            res.append(("60 chamadas em 6 threads: sem repetir nem pular", sorted(ids) == list(range(1, 61))))
            saida = hook(json.dumps({"session_id": "st-d", "transcript_path": "/nao/existe"}))
            res.append(("gancho injeta Cabeçalho deste turno", "Cabeçalho deste turno:" in saida))
            res.append(("gancho com entrada inválida sai sem saída", hook("{ruim") == ""))
            res.append(("hora regional com fuso -03 e selo", bool(re.search(
                r"\d{2}/\d{2}/\d{4} \d{2}:\d{2} -03 \(relógio da Máquina\)", proximo("st-a")))))
        finally:
            if antes is None:
                os.environ.pop("AGATA_TURNOS_DIR", None)
            else:
                os.environ["AGATA_TURNOS_DIR"] = antes
    for nome, ok in res:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in res)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["--selftest"]:
        return _selftest()
    ap = argparse.ArgumentParser(description="Contador mecânico de turno (ver o cabeçalho do módulo).")
    cmds = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("proximo", "atual", "sub"):
        p = cmds.add_parser(nome)
        p.add_argument("--sessao", required=True)
        p.add_argument("--modelo", default=MODELO_PADRAO)
    cmds.add_parser("hook")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "hook":
            try:
                entrada = sys.stdin.read()
            except (OSError, ValueError):
                entrada = ""
            saida = hook(entrada)
            if saida:
                print(saida)
            return 0
        if args.cmd == "proximo":
            print(proximo(args.sessao, args.modelo))
        elif args.cmd == "atual":
            print(atual(args.sessao, args.modelo))
        else:
            print(subagente(args.sessao, args.modelo))
        return 0
    except ErroSessao as e:
        print(f"turno: {e}", file=sys.stderr)
        return 2
    except SemContador as e:
        print(f"turno: {e}", file=sys.stderr)
        return 1
    except (OSError, TimeoutError) as e:
        print(f"turno: erro do contador ({e}); sem linha de turno", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
