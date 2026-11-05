"""Confinamento de caminhos da nova versão (lote 5, pacote F1).

Padrão único para qualquer nome vindo de fora (id de tarefa, nome de arquivo, id de objeto):
o nome só entra se casar uma regra fechada e, depois de juntado à pasta-base, o caminho resolvido
continuar dentro da base. É o mesmo cuidado de redesign/conexoes/segredos.py (_arquivo), que o CodeQL
exigiu depois do alerta py/path-injection. Sem `shell=True`, sem concatenação de string com caminho.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

RE_ID_CURTO = re.compile(r"[a-z]{2,4}-[a-z0-9-]{2,40}")         # task_id de conjunto
RE_SHA256 = re.compile(r"[0-9a-f]{64}")
RE_RUN = re.compile(r"r-\d{8}-\d{6}-[0-9a-f]{6}")                  # run_id de registro.py
EXTENSOES_ACEITAS = ("md", "txt", "html", "pdf")


def dentro(base: str | Path, nome: str) -> Path:
    """Caminho de `nome` dentro de `base`, ou ValueError se escapar (../, absoluto, symlink para fora)."""
    if not isinstance(nome, str) or not nome or "\x00" in nome:
        raise ValueError("nome inválido")
    raiz = os.path.realpath(base)
    alvo = os.path.realpath(os.path.join(raiz, nome))   # realpath segue symlinks dentro do caminho (normpath não segue)
    if not alvo.startswith(raiz + os.sep):
        raise ValueError("caminho fora da pasta permitida")
    return Path(alvo)


def id_seguro(valor, padrao: re.Pattern) -> str:
    """Devolve o valor só se casar o padrão inteiro (fullmatch); senão ValueError."""
    if not isinstance(valor, str) or not padrao.fullmatch(valor):
        raise ValueError("identificador inválido")
    return valor


def arquivo_do_acervo(base: str | Path, sha256: str, extensao: str) -> Path:
    """Nome do arquivo guardado = sha256 + extensão da lista branca. O rótulo original nunca vira caminho."""
    id_seguro(sha256, RE_SHA256)
    ext = (extensao or "").lower().lstrip(".")
    if ext not in EXTENSOES_ACEITAS:
        raise ValueError("extensão fora da lista")
    return dentro(base, f"{sha256}.{ext}")
