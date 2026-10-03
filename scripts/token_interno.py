#!/usr/bin/env python3
"""token_interno.py -- o token interno do Agata (cabeçalho X-Agata-Token), lido de UM
arquivo que contém só ele.

Por quê (MEMÓRIAS (629)-(631)): cinco cópias de `_token_interno()` -- seth_gateway,
proxy (sanitizador), grafo, conselho_remoto e pesquisar_modelos_gratuitos -- abriam
`~/.config/agata/.env` INTEIRO, a cada pedido, para pegar uma variável. Qualquer
rastreio do processo via todas as chaves de provedor; foi assim que 9 vazaram. Agora:
  - o token mora em `~/.config/agata/token-interno` (só ele, permissão 0600, do dono);
  - é lido UMA vez por processo e guardado em memória;
  - nenhum desses processos abre o `.env`;
  - arquivo ausente, com permissão larga ou malformado -> "" (falha FECHADA: o
    sanitizador recusa; quem chama recebe 403, nunca passa sem token).

Uso:
  python3 scripts/token_interno.py --gerar       # cria o arquivo com token novo (recusa se já existe)
  python3 scripts/token_interno.py --rotacionar  # troca o token (reinicie sanitizador + gateway juntos)
  python3 scripts/token_interno.py --verificar   # diz se o arquivo está são -- NUNCA imprime o valor
  python3 scripts/token_interno.py --selftest
Só stdlib.
"""
from __future__ import annotations

import os
import secrets
import stat
import sys
import tempfile
import threading
from pathlib import Path

CAMINHO = Path(os.environ.get("AGATA_TOKEN_INTERNO_PATH",
                              str(Path.home() / ".config" / "agata" / "token-interno")))
_MIN_CHARS = 32
# Quem manda o X-Agata-Token (ou o confere). Nenhum deles pode abrir o .env --
# conferido no --selftest; arquivo novo que precise do token entra nesta lista.
CONSUMIDORES = ("redesign/router/seth_gateway.py", "redesign/router/proxy.py",
                "redesign/grafo/grafo.py", "scripts/conselho_remoto.py",
                "scripts/pesquisar_modelos_gratuitos.py")
_cache: dict[str, str] = {}
_lock = threading.Lock()


def diagnostico(caminho: Path | None = None) -> str:
    """'ok' ou o motivo de recusa. Nunca contém o valor do token."""
    p = Path(caminho or CAMINHO)
    try:
        st = os.stat(p, follow_symlinks=False)
    except FileNotFoundError:
        return f"ausente: {p} (crie com: python3 scripts/token_interno.py --gerar)"
    except OSError as e:
        return f"ilegível: {p} ({e.__class__.__name__})"
    if not stat.S_ISREG(st.st_mode):
        return f"não é arquivo comum (symlink/diretório recusado): {p}"
    if st.st_uid != os.getuid():
        return f"dono errado: {p} não pertence ao usuário que roda o serviço"
    if st.st_mode & 0o077:
        return f"permissão larga demais: {oct(st.st_mode & 0o777)} em {p} (use chmod 600)"
    try:
        valor = p.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as e:
        return f"ilegível: {p} ({e.__class__.__name__})"
    if "\n" in valor or "=" in valor or " " in valor:
        return f"formato inválido: {p} deve conter só o token, numa linha (sem NOME=)"
    if len(valor) < _MIN_CHARS:
        return f"token curto demais em {p} (mínimo {_MIN_CHARS} caracteres)"
    return "ok"


def ler(caminho: Path | None = None) -> str:
    """O token, ou "" se o arquivo não está são (falha fechada). Lido uma vez por
    processo e por caminho; depois sai da memória."""
    p = Path(caminho or CAMINHO)
    chave = str(p)
    with _lock:
        if chave in _cache:
            return _cache[chave]
        valor = p.read_text(encoding="utf-8").strip() if diagnostico(p) == "ok" else ""
        if valor:
            _cache[chave] = valor   # não cacheia o vazio: o arquivo pode ser criado depois
        return valor


def _gravar(p: Path, valor: str, substituir: bool) -> None:
    p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if p.exists() and not substituir:
        raise SystemExit(f"{p} já existe -- para trocar o token use --rotacionar")
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".token-interno.")
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, (valor + "\n").encode())
        os.close(fd)
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _selftest() -> int:
    falhas = 0
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "token-interno"

        def caso(nome, ok):
            nonlocal falhas
            print(f"{'PASS' if ok else 'FALHA'}  {nome}")
            falhas += 0 if ok else 1

        caso("ausente -> '' (falha fechada)", ler(p) == "" and diagnostico(p).startswith("ausente"))
        _gravar(p, secrets.token_urlsafe(32), substituir=False)
        caso("gerado 0600 -> ok", diagnostico(p) == "ok" and (os.stat(p).st_mode & 0o777) == 0o600)
        v1 = ler(p)
        caso("lido -> valor com >= 32 chars", len(v1) >= _MIN_CHARS)
        try:
            _gravar(p, "x" * 40, substituir=False)
            caso("--gerar recusa sobrescrever", False)
        except SystemExit:
            caso("--gerar recusa sobrescrever", True)
        os.chmod(p, 0o644)
        caso("permissão 0644 -> recusado", diagnostico(p).startswith("permissão larga"))
        _cache.clear()
        caso("permissão larga -> ler() devolve ''", ler(p) == "")
        os.chmod(p, 0o600)
        p.write_text("AGATA_INTERNAL_TOKEN=" + "y" * 40 + "\n", encoding="utf-8")
        caso("linha NOME=valor (cópia do .env) -> recusada", diagnostico(p).startswith("formato inválido"))
        p.write_text("curto\n", encoding="utf-8")
        caso("token curto -> recusado", diagnostico(p).startswith("token curto"))
        alvo = Path(d) / "alvo"
        alvo.write_text("z" * 40, encoding="utf-8")
        os.chmod(alvo, 0o600)
        p.unlink()
        p.symlink_to(alvo)
        caso("symlink -> recusado", diagnostico(p).startswith("não é arquivo comum"))
        p.unlink()
        _gravar(p, "w" * 40, substituir=True)
        _cache.clear()
        caso("diagnóstico nunca contém o valor", "w" * 40 not in diagnostico(p) and ler(p) == "w" * 40)
    # classe fechada: nenhum dos consumidores do token abre mais o .env
    raiz = Path(__file__).resolve().parent.parent
    alvo_env = "config/agata/" + ".env"          # montado em pedaços: este arquivo não casa consigo
    consumidores = [raiz / c for c in CONSUMIDORES]
    import re
    abre = re.compile(r"(open\(|expanduser\(|Path\()[^)\n]*" + re.escape(alvo_env) + r"|_ENV_PATH\b")
    abrem = [str(c.relative_to(raiz)) for c in consumidores if c.is_file()
             and abre.search(c.read_text(encoding="utf-8"))]
    ausentes = [str(c.relative_to(raiz)) for c in consumidores if not c.is_file()]
    print(f"{'PASS' if not abrem and not ausentes else 'FALHA'}  nenhum consumidor do token abre o .env"
          + (f" -- ainda abrem: {abrem}" if abrem else "") + (f" -- ausentes: {ausentes}" if ausentes else ""))
    falhas += 0 if not abrem and not ausentes else 1
    print(f"\n{'SELFTEST OK' if not falhas else f'SELFTEST FALHOU ({falhas})'}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    if "--gerar" in sys.argv or "--rotacionar" in sys.argv:
        _gravar(CAMINHO, secrets.token_urlsafe(32), substituir="--rotacionar" in sys.argv)
        print(f"ok: token novo gravado em {CAMINHO} (0600). Valor não exibido. "
              "Reinicie juntos: systemctl --user restart omniroute-sanitizer seth-gateway")
        sys.exit(0)
    if "--verificar" in sys.argv:
        d = diagnostico()
        print(d)
        sys.exit(0 if d == "ok" else 1)
    print(__doc__)
    sys.exit(2)
