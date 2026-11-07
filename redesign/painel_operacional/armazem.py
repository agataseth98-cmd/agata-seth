"""Armazém local do painel: itens do vault (só leitura, lista fechada) e conversas salvas.

Saiu de server.py em 03/11/2026 sem mudar comportamento; o servidor importa estes nomes.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from relogio import _reading_window

ROOT = Path(__file__).resolve().parents[2]


VAULT_ITENS = {"inicio": "INICIO.md", "timeline": "timeline.md", "estado": "estado.md",
               "mapa": "mapa-do-sistema.canvas", "memorias": "memorias.base", "moc-projeto": "moc-projeto.md",
               "moc-memoria": "moc-memoria.md", "moc-documentos": "moc-documentos.md", "moc-scripts": "moc-scripts.md"}
VAULT_LIMITE = 65536


def _vault_item(item_id: str) -> dict:
    """Um item do vault, só leitura, de uma lista fechada. Texto cru; canvas também vira lista de nós."""
    observed_at, fresh_until = _reading_window()
    nome = VAULT_ITENS[item_id]
    arq = ROOT / "memoria/obsidian" / nome
    base = {"schema_version": 1, "id": item_id, "fonte": "memoria/obsidian/" + nome,
            "observed_at": observed_at, "fresh_until": fresh_until}
    if not arq.is_file():
        return {**base, "state": "unknown", "titulo": nome, "motivo": "arquivo ausente no vault"}
    st = arq.stat()
    with arq.open("rb") as f:
        bruto = f.read(VAULT_LIMITE)
    texto = bruto.decode("utf-8", errors="replace")
    titulo = next((l[2:].strip() for l in texto.splitlines() if l.startswith("# ")), nome)
    out = {**base, "state": "ok", "titulo": titulo, "texto": texto, "tamanho": st.st_size,
           "truncado": st.st_size > VAULT_LIMITE,
           "modificado": datetime.fromtimestamp(st.st_mtime, ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds")}
    if nome.endswith(".canvas") and not out["truncado"]:
        try:
            dados = json.loads(texto)
            out["canvas"] = {"nos": [{"tipo": n.get("type", ""), "texto": str(n.get("text") or n.get("file") or "")[:200]}
                                     for n in dados.get("nodes", [])[:200]],
                             "arestas": len(dados.get("edges", []))}
        except ValueError:
            out["canvas"] = None
    return out


def _vault_caminho(caminho: str) -> dict | None:
    """Nota .md do vault pelo caminho relativo, só leitura. Recusa tudo que sair de memoria/obsidian."""
    if not re.fullmatch(r"[^\x00-\x1f\\]{1,200}\.md", caminho) or caminho.startswith("/") or ".." in caminho.split("/"):
        return None
    raiz = (ROOT / "memoria/obsidian").resolve()
    arq = (raiz / caminho).resolve()
    if raiz not in arq.parents or not arq.is_file():
        return None
    observed_at, fresh_until = _reading_window()
    st = arq.stat()
    with arq.open("rb") as f:
        texto = f.read(VAULT_LIMITE).decode("utf-8", errors="replace")
    titulo = next((l[2:].strip() for l in texto.splitlines() if l.startswith("# ")), arq.stem)
    return {"schema_version": 1, "id": caminho, "fonte": "memoria/obsidian/" + caminho, "state": "ok",
            "titulo": titulo, "texto": texto, "tamanho": st.st_size, "truncado": st.st_size > VAULT_LIMITE,
            "modificado": datetime.fromtimestamp(st.st_mtime, ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds"),
            "observed_at": observed_at, "fresh_until": fresh_until}


CONVERSAS_DIR = Path.home() / ".cache/agata/painel-conversas"
CONVERSA_ID = re.compile(r"[0-9a-f]{12}")
CONVERSA_LIMITE_BYTES = 262144


def _conversa_caminho(conversa_id: str) -> Path | None:
    if not isinstance(conversa_id, str) or not CONVERSA_ID.fullmatch(conversa_id):
        return None
    return CONVERSAS_DIR / (conversa_id + ".json")


def _conversas_listar() -> dict:
    itens = []
    if CONVERSAS_DIR.is_dir():
        for arq in sorted(CONVERSAS_DIR.glob("*.json"), key=lambda a: a.stat().st_mtime, reverse=True)[:200]:
            if not CONVERSA_ID.fullmatch(arq.stem):
                continue
            try:
                dados = json.loads(arq.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            itens.append({"id": arq.stem, "titulo": dados.get("titulo", "Sem título"),
                          "atualizada": datetime.fromtimestamp(arq.stat().st_mtime, ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds"),
                          "mensagens": len(dados.get("mensagens", []))})
    return {"schema_version": 1, "state": "ok", "items": itens}


def _conversa_validar(dados: dict) -> dict | None:
    if not isinstance(dados, dict):
        return None
    titulo = str(dados.get("titulo") or "").strip()[:80] or "Sem título"
    mensagens = dados.get("mensagens")
    if not isinstance(mensagens, list) or len(mensagens) > 200:
        return None
    limpas = []
    for m in mensagens:
        if not isinstance(m, dict) or m.get("role") not in ("user", "assistant") or not isinstance(m.get("content"), str):
            return None
        if len(m["content"]) > 8000:
            return None
        limpas.append({"role": m["role"], "content": m["content"]})
    return {"titulo": titulo, "mensagens": limpas}


def _conversa_gravar(dados: dict) -> dict | None:
    limpo = _conversa_validar(dados)
    if limpo is None:
        return None
    conversa_id = dados.get("id") or os.urandom(6).hex()
    arq = _conversa_caminho(conversa_id)
    if arq is None:
        return None
    CONVERSAS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps(limpo, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, arq)
    return {"id": conversa_id, **limpo}


def _conversa_apagar(conversa_id: str) -> bool:
    arq = _conversa_caminho(conversa_id)
    if arq is None or not arq.is_file():
        return False
    arq.unlink()
    return True
