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
     como veio (inclui a linha "Modelo:" dela). Com SETH_ESCRIBA_GIT=1, a entrada
     vai por PR de registro (branch proprio); desligado, fica so no working tree.

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
import secrets
import subprocess
import stat
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

BIND = os.environ.get("SETH_ESCRIBA_BIND", "127.0.0.1:20140")
REPO = Path(os.environ.get("SETH_REPO", str(Path(__file__).resolve().parents[2])))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
from http_seguro import ler_corpo_limitado, ServidorConcorrenciaLimitada  # noqa: E402
from redesign.mcp.capability import PUBLIC_KEY_FILE, NONCE_DB, verificar_capability  # noqa: E402
TZ = ZoneInfo(os.environ.get("SETH_ESCRIBA_TZ", "America/Sao_Paulo"))

MEMORIAS = REPO / "MEMÓRIAS.md"
DIARIO = REPO / "SETH-DIARIO.md"
MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI"  # prefixo; a linha inteira tem mais texto
MAX_CORPO = 20000  # trava de tamanho por acrescimo


def _validar_capability(token: str, tool: str, arguments: dict) -> None:
    verificar_capability(
        token,
        audience="escriba",
        tool=tool,
        arguments=arguments,
        public_key_file=Path(os.environ.get(
            "AGATA_APPROVAL_PUBLIC_KEY_FILE", str(PUBLIC_KEY_FILE))),
        nonce_db=Path(os.environ.get("AGATA_APPROVAL_NONCE_DB", str(NONCE_DB))),
    )

# --- corrida entre chamadas concorrentes (achado 04/09/2026, Camada C) -----
# ThreadingHTTPServer aceita POST /memoria e POST /diario em paralelo. A
# versão anterior lia o arquivo, calculava N, e gravava sem nenhum lock: duas
# chamadas concorrentes podiam ler o mesmo "antes", calcular o mesmo N, e a
# segunda escrita apagava a entrada que a primeira acabara de gravar -- viola
# append-only mesmo com a verificação pós-escrita (que comparava o `depois`
# construído contra si mesmo, nunca relia o disco antes de gravar). Duas
# travas: (1) um lock por processo serializa as duas rotas entre threads
# deste servidor; (2) um flock exclusivo em arquivo .lock ESTÁVEL cobre
# outros processos que adotem o mesmo protocolo. Git e escritores externos
# não são serializados automaticamente. O alvo troca de inode no replace;
# por isso não pode ser o próprio objeto da trava. Escrita é sempre por arquivo-temporário +
# os.replace (atômica no mesmo filesystem) -- nunca write_text direto, que
# pode deixar o arquivo pela metade se o processo morrer no meio.
_LOCK_PROCESSO = threading.Lock()


def _abrir_diretorio_seguro(caminho: Path) -> int:
    """Abre o diretório-pai fixado e rejeita caminho indireto ou gravável por terceiros."""
    absoluto = caminho.absolute()
    resolvido = caminho.parent.resolve(strict=True)
    if resolvido != absoluto.parent:
        raise RuntimeError("diretorio pai nao canonico")
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(str(resolvido), flags)
    st = os.fstat(fd)
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o022:
        os.close(fd)
        raise RuntimeError("diretorio pai inseguro")
    return fd


def _ler_alvo_seguro(caminho: Path) -> str:
    """Lê o alvo como arquivo regular, do owner esperado, sem seguir symlink."""
    dfd = _abrir_diretorio_seguro(caminho)
    try:
        fd = os.open(caminho.name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=dfd)
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_nlink != 1:
            os.close(fd)
            raise RuntimeError("alvo nao e arquivo regular do owner esperado")
        with os.fdopen(fd, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        os.close(dfd)


@contextmanager
def _travar_arquivo(caminho: Path):
    dfd = _abrir_diretorio_seguro(caminho)
    trava_nome = caminho.name + ".lock"
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
    fd = None
    try:
        fd = os.open(trava_nome, flags, 0o600, dir_fd=dfd)
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_nlink != 1:
            raise RuntimeError("objeto de trava inseguro")
        fcntl.flock(fd, fcntl.LOCK_EX)
        atual = os.stat(trava_nome, dir_fd=dfd, follow_symlinks=False)
        if (atual.st_dev, atual.st_ino) != (st.st_dev, st.st_ino):
            raise RuntimeError("objeto de trava substituido durante espera")
        # Preserva bootstrap do diário, que espera alvo vazio na primeira vez.
        # O alvo ainda é reaberto pelos leitores: isto NÃO conclui E3/TOCTOU.
        alvo = os.open(caminho.name, flags, 0o644, dir_fd=dfd)
        try:
            alvo_st = os.fstat(alvo)
            if (not stat.S_ISREG(alvo_st.st_mode) or alvo_st.st_uid != os.getuid()
                    or alvo_st.st_nlink != 1):
                raise RuntimeError("alvo nao e arquivo regular")
        finally:
            os.close(alvo)
        yield
    finally:
        if fd is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
        os.close(dfd)


def _escreve_atomico(caminho: Path, conteudo: str) -> None:
    dfd = _abrir_diretorio_seguro(caminho)
    tmp = f".{caminho.name}.{secrets.token_hex(12)}.tmp"
    fd = None
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                     0o600, dir_fd=dfd)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            fd = None  # fdopen assumiu o descritor
            f.write(conteudo)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, caminho.name, src_dir_fd=dfd, dst_dir_fd=dfd)
    except BaseException:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(tmp, dir_fd=dfd)
        except OSError:
            pass
        raise
    finally:
        os.close(dfd)


def _agora() -> datetime:
    return datetime.now(TZ)


def _proximo_n(texto: str) -> int:
    ns = [int(m) for m in re.findall(r"^\((\d+)\)\s", texto, re.M)]
    return (max(ns) + 1) if ns else 1


def _registrar_git(nome: str, bloco: str) -> dict:
    """Leva a entrada ao histórico por PR de registro (branch próprio; o main não é tocado).

    Desligado por padrão (SETH_ESCRIBA_GIT=1 liga). Aplica o bloco sobre a versão de origin/main,
    commita num branch novo, dá push e abre PR. Falha aqui não desfaz a gravação local: devolve o motivo.
    """
    if os.environ.get("SETH_ESCRIBA_GIT", "0") != "1":
        return {"git": "desligado (SETH_ESCRIBA_GIT=0): gravado só no working tree"}
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="seth-registro-"))
    branch = f"registro/seth-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
    try:
        subprocess.run(["git", "-C", str(REPO), "fetch", "-q", "origin", "main"], check=True, timeout=60)
        subprocess.run(["git", "-C", str(REPO), "worktree", "add", "-q", "-b", branch, str(tmp), "origin/main"],
                       check=True, timeout=60)
        alvo = tmp / nome
        linhas = alvo.read_text(encoding="utf-8").splitlines(keepends=True)
        idx = next(i for i, l in enumerate(linhas) if l.startswith(MARCADOR))
        linhas.insert(idx + 1, bloco if bloco.endswith("\n") else bloco + "\n")
        alvo.write_text("".join(linhas), encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp), "add", nome], check=True, timeout=60)
        subprocess.run(["git", "-C", str(tmp), "commit", "-q", "-m", f"registro: Seth escreveu em {nome} ({branch})"],
                       check=True, timeout=60)
        subprocess.run(["git", "-C", str(tmp), "push", "-q", "-u", "origin", branch], check=True, timeout=120)
        pr = subprocess.run(["gh", "pr", "create", "--base", "main", "--head", branch,
                             "--title", f"registro da Seth: {nome}",
                             "--body", "Entrada escrita pelo escriba. Confira e junte."],
                            capture_output=True, text=True, timeout=120, check=True)
        return {"git": "PR aberto", "branch": branch, "pr": pr.stdout.strip()}
    except Exception as e:  # noqa: BLE001 -- falha aqui não pode derrubar a gravação já feita
        return {"git": f"falhou (gravação local mantida): {type(e).__name__}"}
    finally:
        subprocess.run(["git", "-C", str(REPO), "worktree", "remove", "--force", str(tmp)],
                       capture_output=True, timeout=60)
        subprocess.run(["git", "-C", str(REPO), "worktree", "prune"], capture_output=True, timeout=60)


def _acrescenta_memoria(titulo: str, corpo: str) -> dict:
    if not titulo.strip() or not corpo.strip():
        raise ValueError("titulo e corpo obrigatorios")
    if len(corpo) > MAX_CORPO:
        raise ValueError(f"corpo > {MAX_CORPO} chars")
    with _LOCK_PROCESSO, _travar_arquivo(MEMORIAS):
        # relê AGORA, dentro da trava -- "antes" de fora da trava seria a
        # mesma corrida de novo, só que mascarada
        antes = _ler_alvo_seguro(MEMORIAS)
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
            "nota": "gravado no working tree.", **_registrar_git("MEMÓRIAS.md", bloco)}


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
        if not _ler_alvo_seguro(DIARIO):
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
        antes = _ler_alvo_seguro(DIARIO)
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
            "nota": "inserido logo abaixo do marcador ENTRADAS-NOVAS em SETH-DIARIO.md (working tree).",
            **_registrar_git("SETH-DIARIO.md", bloco)}


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
                _validar_capability(self.headers.get("Authorization", "").removeprefix("Bearer "),
                                    "memoria_acrescentar",
                                    {"titulo": data.get("titulo", ""), "corpo": data.get("corpo", "")})
                return self._j(200, _acrescenta_memoria(data.get("titulo", ""), data.get("corpo", "")))
            if self.path.rstrip("/") == "/diario":
                _validar_capability(self.headers.get("Authorization", "").removeprefix("Bearer "),
                                    "diario_anotar", {"texto": data.get("texto", "")})
                return self._j(200, _anota_diario(data.get("texto", "")))
            return self._j(404, {"error": f"rota {self.path} inexistente"})
        except PermissionError:
            return self._j(403, {"error": "capability de aprovação ausente, inválida ou já consumida"})
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
