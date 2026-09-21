#!/usr/bin/env python3
"""seth_escriba.py — caminho de escrita APPEND-ONLY da Seth.

A Seth (LibreChat) so tem tools de LEITURA (canon-mcp -> :27125 read-only).
Este servico e' o unico jeito dela ACRESCENTAR — e so acrescentar. Nunca
apaga, nunca sobrescreve linha existente. Autorizado pelo Humano:
"corte os acessos dela, menos a memoria e obsidian; append only; assumo o risco."

Escuta 127.0.0.1:20140. Duas rotas, as duas com verificacao pos-escrita que
ABORTA (e nao grava) se a operacao nao for um insert/append puro:

  POST /memoria   {"titulo": str, "corpo": str}
     Insere um bloco novo em MEMORIAS.md LOGO ABAIXO do marcador
     <!-- ENTRADAS-NOVAS:AQUI -->. O numero (NNN) e a data sao do relogio da
     Maquina — a Seth NAO os fornece (nao tem como fabricar). `corpo` entra
     como veio (inclui a linha "Modelo:" dela). NAO faz git add nem commit —
     a mudanca fica no working tree pro Humano revisar e commitar.

  POST /diario    {"texto": str}
     Insere um bloco novo em SETH-DIARIO.md (arquivo proprio da Seth, fora do
     vault derivado, nao policiado pelo P-10) LOGO ABAIXO do marcador
     <!-- ENTRADAS-NOVAS:AQUI -->, mesmo mecanismo de /memoria -- mais
     recente primeiro, espelhando MEMORIAS.md. Ate 20/09/2026 anexava no FIM
     (mais antigo no topo); trocado por pedido do Humano, mesmo padrao dos
     dois arquivos (MEMORIAS (472)/(473)).

Verificacao (a trava do "nao pode apagar"):
  memoria, diario -> depois == antes com exatamente um bloco inserido no
             offset do marcador; todo byte anterior e posterior identico
             (nada apagado, nada reescrito). Senao: 409.

Nao tem rota de PUT/PATCH/DELETE. So stdlib. Nao le segredo nenhum.

Env: SETH_ESCRIBA_BIND (default 127.0.0.1:20140), SETH_REPO (default ~/agata),
     SETH_ESCRIBA_TZ (default America/Sao_Paulo).
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

BIND = os.environ.get("SETH_ESCRIBA_BIND", "127.0.0.1:20140")
REPO = Path(os.environ.get("SETH_REPO", str(Path.home() / "agata")))
sys.path.insert(0, str(REPO / "scripts"))
from http_seguro import ler_corpo_limitado, ServidorConcorrenciaLimitada  # noqa: E402
TZ = ZoneInfo(os.environ.get("SETH_ESCRIBA_TZ", "America/Sao_Paulo"))

MEMORIAS = REPO / "MEMÓRIAS.md"
DIARIO = REPO / "SETH-DIARIO.md"
MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI"  # prefixo; a linha inteira tem mais texto
MAX_CORPO = 20000  # trava de tamanho por acrescimo

# --- corrida entre chamadas concorrentes (achado 04/09/2026, Camada C) -----
# ThreadingHTTPServer aceita POST /memoria e POST /diario em paralelo. A
# versão anterior lia o arquivo, calculava N, e gravava sem nenhum lock: duas
# chamadas concorrentes podiam ler o mesmo "antes", calcular o mesmo N, e a
# segunda escrita apagava a entrada que a primeira acabara de gravar -- viola
# append-only mesmo com a verificação pós-escrita (que comparava o `depois`
# construído contra si mesmo, nunca relia o disco antes de gravar). Duas
# travas: (1) um lock por processo serializa as duas rotas entre threads
# deste servidor; (2) um flock exclusivo no PRÓPRIO arquivo alvo cobre o caso
# de outro processo (ex.: um commit manual do Humano no mesmo instante)
# tocando o arquivo ao mesmo tempo. Escrita é sempre por arquivo-temporário +
# os.replace (atômica no mesmo filesystem) -- nunca write_text direto, que
# pode deixar o arquivo pela metade se o processo morrer no meio.
_LOCK_PROCESSO = threading.Lock()


@contextmanager
def _travar_arquivo(caminho: Path):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(caminho), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _escreve_atomico(caminho: Path, conteudo: str) -> None:
    d = caminho.parent
    fd, tmp = tempfile.mkstemp(prefix=f".{caminho.name}.", dir=str(d))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(conteudo)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, caminho)  # atômico no mesmo filesystem
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _agora() -> datetime:
    return datetime.now(TZ)


def _proximo_n(texto: str) -> int:
    ns = [int(m) for m in re.findall(r"^\((\d+)\)\s", texto, re.M)]
    return (max(ns) + 1) if ns else 1


def _acrescenta_memoria(titulo: str, corpo: str) -> dict:
    if not titulo.strip() or not corpo.strip():
        raise ValueError("titulo e corpo obrigatorios")
    if len(corpo) > MAX_CORPO:
        raise ValueError(f"corpo > {MAX_CORPO} chars")
    with _LOCK_PROCESSO, _travar_arquivo(MEMORIAS):
        # relê AGORA, dentro da trava -- "antes" de fora da trava seria a
        # mesma corrida de novo, só que mascarada
        antes = MEMORIAS.read_text(encoding="utf-8")
        linha_marcador = next((l for l in antes.splitlines() if l.startswith(MARCADOR)), None)
        if linha_marcador is None:
            raise RuntimeError("marcador ENTRADAS-NOVAS nao encontrado em MEMORIAS.md")
        n = _proximo_n(antes)
        data = _agora().strftime("%d/%m/%Y")
        header = f"({n}) DIÁRIO — {data} · {titulo.strip()}"
        bloco = f"\n{header}\n\n{corpo.strip()}\n"

        corte = antes.index(linha_marcador) + len(linha_marcador) + 1  # +1 = o \n da linha do marcador
        depois = antes[:corte] + bloco + antes[corte:]

        # --- trava de conteúdo: so um insert no offset do marcador, nada mais mudou ---
        if depois[:corte] != antes[:corte]:
            raise RuntimeError("verificacao falhou: conteudo antes do marcador mudou")
        if depois[corte + len(bloco):] != antes[corte:]:
            raise RuntimeError("verificacao falhou: conteudo depois do ponto de insercao mudou")
        if len(depois) != len(antes) + len(bloco):
            raise RuntimeError("verificacao falhou: tamanho inconsistente")

        _escreve_atomico(MEMORIAS, depois)
    return {"ok": True, "entrada": n, "header": header,
            "nota": "gravado no working tree; NAO commitado. Humano: 'git diff MEMÓRIAS.md' e commite quando quiser."}


def _anota_diario(texto: str) -> dict:
    if not texto.strip():
        raise ValueError("texto obrigatorio")
    if len(texto) > MAX_CORPO:
        raise ValueError(f"texto > {MAX_CORPO} chars")
    with _LOCK_PROCESSO, _travar_arquivo(DIARIO):
        # `_travar_arquivo` abre com O_CREAT -- o arquivo já "existe" (vazio)
        # quando chegamos aqui, mesmo na primeira vez. `exists()` nunca
        # dispararia o bootstrap; o teste certo é tamanho zero. Achado
        # testando esta mudança (MEMÓRIAS (472)), bug preexistente, nunca
        # se manifestou porque a versão antiga não dependia de marcador.
        if DIARIO.stat().st_size == 0:
            _escreve_atomico(
                DIARIO,
                "# Diário da Seth\n\n"
                "Espaço próprio da Seth, append-only. Fora do vault derivado (o P-10 não\n"
                "policia este arquivo) e fora de MEMÓRIAS. Escrito só via `POST /diario`\n"
                "do seth_escriba; nunca editado nem apagado por ela. Autorizado pelo\n"
                "Humano: \"append only... quero ver como ela se desenvolve. Eu assumo o risco.\"\n\n"
                f"{MARCADOR} -- não editar esta linha à mão; entrada nova sempre logo "
                "abaixo dela, nunca acima; espelha o mesmo marcador de MEMÓRIAS.md -->\n")
        # relê AGORA, dentro da trava -- mesmo motivo de _acrescenta_memoria:
        # "antes" lido fora da trava seria a mesma corrida, só mascarada.
        antes = DIARIO.read_text(encoding="utf-8")
        linha_marcador = next((l for l in antes.splitlines() if l.startswith(MARCADOR)), None)
        if linha_marcador is None:
            raise RuntimeError("marcador ENTRADAS-NOVAS nao encontrado em SETH-DIARIO.md")
        ts = _agora().strftime("%Y-%m-%d %H:%M %z")
        # mesmo ponto de inserção de _acrescenta_memoria: logo após a própria
        # linha do marcador (+1 = o \n dela). O bloco começa com "\n" pra
        # abrir a linha em branco depois do marcador -- funciona igual com
        # ou sem entrada existente logo abaixo (arquivo novo: antes[corte:]
        # é vazio; arquivo com histórico: antes[corte:] já começa com
        # "\n---\n**entrada antiga**...", e as duas quebras de linha do fim
        # do bloco mais essa reproduzem a mesma linha dupla em branco que já
        # separa as entradas existentes entre si).
        corte = antes.index(linha_marcador) + len(linha_marcador) + 1
        bloco = f"\n---\n**{ts} (relógio da Máquina)**\n\n{texto.strip()}\n\n"
        depois = antes[:corte] + bloco + antes[corte:]

        # --- trava de conteúdo: so um insert no offset do marcador, nada mais mudou ---
        if depois[:corte] != antes[:corte]:
            raise RuntimeError("verificacao falhou: conteudo antes do marcador mudou")
        if depois[corte + len(bloco):] != antes[corte:]:
            raise RuntimeError("verificacao falhou: conteudo depois do ponto de insercao mudou")
        if len(depois) != len(antes) + len(bloco):
            raise RuntimeError("verificacao falhou: tamanho inconsistente")

        _escreve_atomico(DIARIO, depois)
    return {"ok": True, "bytes_add": len(bloco),
            "nota": "inserido logo abaixo do marcador ENTRADAS-NOVAS em SETH-DIARIO.md (working tree; nao commitado)."}


class _H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _j(self, code: int, obj: dict):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/health":
            return self._j(200, {"ok": True, "repo": str(REPO),
                                 "memorias_existe": MEMORIAS.exists()})
        self._j(404, {"error": "so POST /memoria e POST /diario"})

    def do_POST(self):
        raw = ler_corpo_limitado(self)
        if raw is None:
            return
        try:
            data = json.loads(raw or b"{}")
        except ValueError:
            return self._j(400, {"error": "corpo nao e' JSON"})
        try:
            if self.path.rstrip("/") == "/memoria":
                return self._j(200, _acrescenta_memoria(data.get("titulo", ""), data.get("corpo", "")))
            if self.path.rstrip("/") == "/diario":
                return self._j(200, _anota_diario(data.get("texto", "")))
            return self._j(404, {"error": f"rota {self.path} inexistente"})
        except ValueError as e:
            return self._j(400, {"error": str(e)})
        except RuntimeError as e:
            return self._j(409, {"error": f"gravacao abortada: {e}"})
        except Exception as e:  # noqa: BLE001
            return self._j(500, {"error": repr(e)})

    def do_PUT(self):  self._j(405, {"error": "escrita destrutiva bloqueada (append-only)"})
    do_PATCH = do_PUT
    do_DELETE = do_PUT


def main():
    host, port = BIND.split(":")
    if not MEMORIAS.exists():
        raise SystemExit(f"seth_escriba: {MEMORIAS} nao existe — SETH_REPO errado?")
    srv = ServidorConcorrenciaLimitada((host, int(port)), _H)
    print(f"seth_escriba em http://{host}:{port}  (repo {REPO})  append-only: /memoria /diario")
    srv.serve_forever()


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        # sandbox: repo falso em /tmp
        import tempfile
        d = Path(tempfile.mkdtemp())
        (d / "MEMÓRIAS.md").write_text(
            "topo\n<!-- ENTRADAS-NOVAS:AQUI -- nao editar -->\n\n(9) DIÁRIO — velho\n\nfim\n",
            encoding="utf-8")
        os.environ["SETH_REPO"] = str(d)
        REPO = d; MEMORIAS = d / "MEMÓRIAS.md"; DIARIO = d / "SETH-DIARIO.md"
        antes = MEMORIAS.read_text(encoding="utf-8")
        r = _acrescenta_memoria("teste", "corpo de teste\n\nModelo: Seth")
        depois = MEMORIAS.read_text(encoding="utf-8")
        ok1 = r["entrada"] == 10 and "(10) DIÁRIO" in depois and "(9) DIÁRIO — velho" in depois
        ok2 = depois.startswith("topo\n<!-- ENTRADAS-NOVAS:AQUI") and depois.rstrip().endswith("fim")
        ok3 = all(l in depois for l in antes.splitlines())  # nenhuma linha antiga sumiu
        _anota_diario("primeira nota")
        _anota_diario("segunda nota")
        dv = DIARIO.read_text(encoding="utf-8")
        ok4 = dv.count("---") >= 2 and "primeira nota" in dv and "segunda nota" in dv
        # a mais recente ("segunda") tem que aparecer ANTES da mais antiga
        # ("primeira") -- é o próprio ponto da mudança de 20/09/2026
        # (MEMÓRIAS (472)): mais recente primeiro, não mais anexado no fim.
        ok5 = dv.index("segunda nota") < dv.index("primeira nota")
        print("SELFTEST", "OK" if all([ok1, ok2, ok3, ok4, ok5]) else f"FALHA {ok1=} {ok2=} {ok3=} {ok4=} {ok5=}")
        raise SystemExit(0 if all([ok1, ok2, ok3, ok4, ok5]) else 1)
    main()
