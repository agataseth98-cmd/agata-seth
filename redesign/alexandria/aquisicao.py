"""Aquisição de fontes externas da Alexandria, em quarentena (lote 5, pacote C4).

Três entradas, um só caminho: upload pelo painel, pasta de entrada (`<dados>/alexandria/entrada/`) e URL colada
(egresso por `scripts/politica_egress.buscar_seguro`). Todas passam por `guardar_arquivo`: tamanho (25 MiB),
extensão (md, txt, html, pdf), assinatura do conteúdo, cota da pasta (500 MB), sha256 e nome `<sha>.<ext>`.
Depois, `processar` faz o parse isolado (texto puro no stdlib; PDF só no sandbox bwrap, sem rede) e a análise
de quarentena. Nada aqui chega ao índice pesquisável: isso exige `revisado`, decidido pelo Humano no painel.
"""
from __future__ import annotations

import fcntl
import hashlib
import html.parser
import os
import re
import shutil
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (AQUI, RAIZ / "redesign" / "nova_versao", RAIZ / "redesign" / "grafo", RAIZ / "redesign" / "metacognicao",
           RAIZ / "redesign" / "router", RAIZ / "scripts"):
    sys.path.insert(0, str(_p))
import caminhos  # noqa: E402
import cadastro  # noqa: E402
import eventos  # noqa: E402

MAX_BYTES = 25 * 1024 * 1024
COTA_BYTES = 500 * 1024 * 1024
MAX_TEXTO = 2_000_000
EXTENSOES = ("md", "txt", "html", "pdf")
ASSINATURAS_PROIBIDAS = (b"\x7fELF", b"MZ", b"PK\x03\x04", b"#!")


def entrada() -> Path:
    p = eventos.dados() / "alexandria" / "entrada"
    p.mkdir(parents=True, exist_ok=True)
    os.chmod(p, 0o700)
    return p


def _motivo_conteudo(ext: str, cabeca: bytes) -> str | None:
    if any(cabeca.startswith(a) for a in ASSINATURAS_PROIBIDAS):
        return "assinatura de executável ou script: recusado"
    if ext == "pdf":
        return None if cabeca.startswith(b"%PDF-") else "não é PDF (cabeçalho errado)"
    if b"\x00" in cabeca:
        return "binário onde se esperava texto"
    try:
        cabeca.decode("utf-8")
    except UnicodeDecodeError as e:
        if e.start < len(cabeca) - 4:   # corte no meio de caractere no fim da leitura é normal
            return "texto não é UTF-8"
    return None


def _cota_usada() -> int:
    return sum(f.stat().st_size for f in entrada().iterdir() if f.is_file() and not f.is_symlink())


def guardar_arquivo(tmp: Path, extensao: str, rotulo: str, *, origem_tipo: str, origem_uri: str | None = None) -> dict:
    """Recebe um arquivo já escrito num temporário da pasta de entrada e o põe sob o próprio sha256."""
    if extensao not in EXTENSOES:
        raise ValueError("extensão fora da lista")
    tmp = Path(tmp)
    if tmp.is_symlink() or not tmp.is_file():
        raise ValueError("arquivo irregular")
    tamanho = tmp.stat().st_size
    if tamanho == 0 or tamanho > MAX_BYTES:
        raise ValueError("tamanho fora do limite (até 25 MiB)")
    with tmp.open("rb") as f:
        cabeca = f.read(4096)
    motivo = _motivo_conteudo(extensao, cabeca)
    if motivo:
        raise ValueError(motivo)
    h = hashlib.sha256()
    with tmp.open("rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    sha = h.hexdigest()
    with open(entrada() / ".lock", "w") as trava:
        fcntl.flock(trava, fcntl.LOCK_EX)
        try:
            if cadastro.ler(sha) is not None:
                tmp.unlink(missing_ok=True)
                return {"cadastro": cadastro.ler(sha), "duplicado": True}
            if _cota_usada() + tamanho > COTA_BYTES:
                tmp.unlink(missing_ok=True)
                raise ValueError("cota da pasta de entrada cheia (500 MB)")
            destino = caminhos.arquivo_do_acervo(entrada(), sha, extensao)
            os.replace(tmp, destino)
            os.chmod(destino, 0o600)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
    obj = cadastro.criar(sha, extensao, rotulo or tmp.name, origem_uri=origem_uri, tamanho=tamanho,
                         origem_tipo=origem_tipo)
    return {"cadastro": obj, "duplicado": False}


def importar_pasta() -> list[dict]:
    """Arquivos soltos na pasta de entrada (o Humano copia para lá): entram pelo mesmo caminho, sem symlink."""
    out = []
    for arq in sorted(entrada().iterdir()):
        if arq.is_symlink() or not arq.is_file() or arq.name.startswith("."):
            continue
        ext = arq.suffix.lower().lstrip(".")
        if ext not in EXTENSOES:
            out.append({"arquivo": arq.name, "erro": "extensão fora da lista"})
            continue
        try:
            r = guardar_arquivo(arq, ext, arq.name, origem_tipo="pasta")
            out.append({"arquivo": arq.name, "sha256": r["cadastro"]["sha256"], "duplicado": r["duplicado"]})
        except ValueError as e:
            out.append({"arquivo": arq.name, "erro": str(e)})
    return out


def receber_url(url: str, buscar=None) -> dict:
    """URL colada: egresso seguro (cada salto validado), teto de 25 MiB, só status 200."""
    limpa = cadastro.sanear_uri(url)
    if buscar is None:
        import politica_egress  # noqa: E402
        buscar = politica_egress.buscar_seguro
    tmp = entrada() / f".url-{os.getpid()}-{time.monotonic_ns()}.tmp"
    ok, status, final, motivo = buscar(limpa, str(tmp), max_bytes=MAX_BYTES)
    if not ok or status != 200:
        tmp.unlink(missing_ok=True)
        raise ValueError(f"não baixado: {motivo or f'status {status}'}")
    with tmp.open("rb") as f:
        cabeca = f.read(4096)
    if cabeca.startswith(b"%PDF-"):
        ext = "pdf"
    elif cabeca.lstrip()[:1] == b"<":
        ext = "html"
    else:
        ext = "md" if limpa.lower().endswith(".md") else "txt"
    return guardar_arquivo(tmp, ext, limpa.rsplit("/", 1)[-1] or "pagina", origem_tipo="url", origem_uri=limpa)


class _TextoHTML(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.partes, self._pular = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._pular += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._pular:
            self._pular -= 1

    def handle_data(self, data):
        if not self._pular:
            self.partes.append(data)


def _texto_de(path: Path, ext: str) -> tuple[str | None, str | None]:
    """(texto, motivo_de_rejeição). PDF só pelo sandbox, sem rede e com limite de saída."""
    if ext in ("md", "txt"):
        return path.read_text(encoding="utf-8", errors="replace"), None
    if ext == "html":
        p = _TextoHTML()
        p.feed(path.read_text(encoding="utf-8", errors="replace"))
        return " ".join(" ".join(p.partes).split()), None
    if ext == "pdf":
        import sandbox  # noqa: E402
        if not sandbox.disponivel():
            return None, "sem sandbox bwrap: PDF não é lido fora do isolamento"
        if shutil.which("pdftotext"):
            r = sandbox.run_sandboxed(["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"], ro=[str(path)],
                                      net=False, timeout=60)
            if r["exit_code"] != 0:
                return None, f"parser de PDF falhou (rc {r['exit_code']})"
            return r["stdout"], None
        venv = eventos.dados() / "alexandria" / "ferramentas" / "pdf-venv"
        py = venv / "bin" / "python"
        if py.exists():   # alternativa gratuita: pypdf num venv de usuário, dentro do mesmo sandbox
            script = AQUI / "extrair_pdf.py"
            r = sandbox.run_sandboxed([str(py), str(script), str(path)], ro=[str(venv), str(script), str(path)],
                                      net=False, timeout=60)
            if r["exit_code"] != 0:
                return None, f"parser de PDF (pypdf) falhou: {r['stderr'].strip()[:120]}"
            return r["stdout"], None
        return None, "sem parser de PDF (instale pdftotext ou o venv pypdf)"
    return None, "extensão sem parser"


def processar(sha: str) -> dict:
    """Quarentena: recebido -> quarentena -> catalogado | restrito | rejeitado. Só a máquina, sem decidir direitos."""
    obj = cadastro.ler(sha)
    if obj is None:
        raise ValueError("objeto não cadastrado")
    if obj["editorial_status"] != "recebido":
        return obj
    cadastro.transicionar(sha, "quarentena", "maquina", "entrou em quarentena")
    arq = caminhos.arquivo_do_acervo(entrada(), sha, obj["extensao"])
    texto, motivo = _texto_de(arq, obj["extensao"])
    if motivo:
        cadastro.anotar(sha, parse="falhou", motivo=motivo)
        return cadastro.transicionar(sha, "rejeitado", "maquina", motivo)
    if len(texto) > MAX_TEXTO:
        cadastro.anotar(sha, parse="grande demais")
        return cadastro.transicionar(sha, "rejeitado", "maquina", "texto acima de 2 M caracteres")
    import guarda  # noqa: E402
    import sanitizar  # noqa: E402
    g = guarda.marcar(texto)
    pessoal = sanitizar.varrer_pessoal(texto, sanitizar._nomes_projeto())
    segredos = sanitizar.varrer(texto)
    texto_path = cadastro.texto_path(sha)
    texto_path.parent.mkdir(parents=True, exist_ok=True)
    texto_path.write_text(texto, encoding="utf-8")
    os.chmod(texto_path, 0o600)
    sinais = {"autoridade_alegada": g["autoridade"], "instrucao_embutida": g["instrucao"],
              "dado_pessoal": len(pessoal), "segredos": len(segredos), "caracteres": len(texto)}
    cadastro.anotar(sha, parse="ok", sinais=sinais)
    if pessoal or segredos:
        # dado pessoal ou segredo: fica restrito (nunca consultável sem decisão explícita do Humano)
        return cadastro.transicionar(sha, "restrito", "maquina", "dado pessoal ou segredo detectado (contagem)")
    return cadastro.transicionar(sha, "catalogado", "maquina", "análise de quarentena sem sinais de restrição")


def processar_pendentes() -> list[dict]:
    return [processar(c["sha256"]) for c in cadastro.listar() if c["editorial_status"] == "recebido"]
