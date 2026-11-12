"""Importantes do painel (11/11/2026, pedido do Humano): ideias e pendências que ele manda guardar para depois.

Tudo local e fora do repositório: ~/.cache/agata/painel-importantes.json, escrito inteiro por troca atômica.
Item não some: "descartado" fica guardado e pode ser reaberto. Cada pedido de escrita, inclusive o recusado,
acrescenta uma linha em painel-importantes.registro.jsonl (hora, rota, id e status; nunca texto).

Trazer do Conselho: só leitura do cache do Conselho (cache_conselho.ler). Traz as entradas cujo texto começa com
IMPORTANTE. Cada uma vira item com origem "cache" e cache_n = número da entrada. Entrada já trazida (mesmo que
descartada depois) não entra de novo. O texto passa pelo mesmo filtro da leitura (cache_conselho.filtrar): segredo
não é trazido; dado pessoal vira marca.

Arquivo ilegível (JSON quebrado, forma errada ou item inválido) não é sobrescrito: a leitura diz "ilegivel" e a
escrita responde 409. Nenhum item é apagado de fato.
"""
from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ARQUIVO = Path.home() / ".cache/agata/painel-importantes.json"
SCHEMA_VERSION = 1
TZ = ZoneInfo("America/Sao_Paulo")
ORIGENS = ("humano", "cache", "modelo")
ESTADOS = ("aberto", "feito", "descartado")
ORDEM_ESTADO = {"aberto": 0, "feito": 1, "descartado": 2}
TEXTO_LIMITE = 4000          # texto digitado pelo Humano (mesmo teto do campo da tela)
TEXTO_LIMITE_ITEM = 6000     # teto de validação do arquivo; o texto trazido do cache cabe com folga
NOTA_LIMITE = 500
ITENS_LIMITE = 2000
LEITURA_CACHE = 100000       # n para cache_conselho.ler: o cache inteiro (ele reinicia a cada 15 dias)
ID = re.compile(r"[0-9a-f]{12}")
MARCA_IMPORTANTE = re.compile(r"\s*IMPORTANTE\b")
CAMPOS_CRIAR = ("texto",)
CAMPOS_ESTADO = ("id", "estado")
CAMPOS_EDITAR = ("id", "texto", "nota")
_TRAVA = threading.Lock()
_REGISTRO_TRAVA = threading.Lock()


class ErroImportantes(Exception):
    """Recusa de uma operação: status HTTP e motivo curto em português, sem o texto do item."""

    def __init__(self, status: int, motivo: str):
        super().__init__(motivo)
        self.status = status
        self.motivo = motivo


def _agora() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def _registro_caminho() -> Path:
    return ARQUIVO.with_name(ARQUIVO.stem + ".registro.jsonl")


def registro_escrever(rota: str, identificador, status: int) -> None:
    """Acrescenta uma linha em painel-importantes.registro.jsonl. Se o arquivo não puder ser escrito, a ação segue."""
    ident = identificador if isinstance(identificador, str) and ID.fullmatch(identificador) else None
    linha = {"hora": _agora(), "rota": rota, "id": ident, "status": status}
    try:
        ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
        with _REGISTRO_TRAVA, _registro_caminho().open("a", encoding="utf-8") as arq:
            arq.write(json.dumps(linha, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _item_valido(e) -> bool:
    return (isinstance(e, dict)
            and isinstance(e.get("id"), str) and ID.fullmatch(e["id"]) is not None
            and isinstance(e.get("texto"), str) and 0 < len(e["texto"]) <= TEXTO_LIMITE_ITEM
            and e.get("origem") in ORIGENS and e.get("estado") in ESTADOS
            and isinstance(e.get("criado_em"), str)
            and (e.get("feito_em") is None or isinstance(e.get("feito_em"), str))
            and isinstance(e.get("nota"), str) and len(e["nota"]) <= NOTA_LIMITE
            and (e.get("cache_n") is None or (isinstance(e.get("cache_n"), int) and not isinstance(e.get("cache_n"), bool))))


def _ler() -> tuple[list, bool]:
    """(itens, legível). Arquivo ausente vale vazio. Qualquer coisa fora do formato devolve legível=False."""
    if not ARQUIVO.is_file():
        return [], True
    try:
        dados = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [], False
    if not isinstance(dados, dict) or dados.get("schema_version") != SCHEMA_VERSION or not isinstance(dados.get("itens"), list):
        return [], False
    itens = dados["itens"]
    if not all(_item_valido(e) for e in itens) or len({e["id"] for e in itens}) != len(itens):
        return [], False
    return itens, True


def _gravar(itens: list) -> None:
    """Escreve o arquivo inteiro: vai para um temporário na mesma pasta, com fsync, e troca por os.replace."""
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ARQUIVO.with_name(ARQUIVO.name + ".tmp")
    corpo = json.dumps({"schema_version": SCHEMA_VERSION, "itens": itens}, ensure_ascii=False, indent=1).encode("utf-8")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as arq:
        arq.write(corpo)
        arq.flush()
        os.fsync(arq.fileno())
    os.replace(tmp, ARQUIVO)


def _mudar(alterar):
    """Lê, altera e grava sob trava. `alterar(itens)` pode recusar com ErroImportantes: então nada é gravado."""
    with _TRAVA:
        itens, legivel = _ler()
        if not legivel:
            raise ErroImportantes(409, "lista de importantes ilegível; nada foi alterado")
        resultado = alterar(itens)
        _gravar(itens)
        return resultado


def _novo(texto: str, origem: str, cache_n=None) -> dict:
    return {"id": uuid.uuid4().hex[:12], "texto": texto, "origem": origem, "criado_em": _agora(),
            "estado": "aberto", "feito_em": None, "nota": "", "cache_n": cache_n}


def _campos(pedido, permitidos) -> dict:
    if not isinstance(pedido, dict):
        raise ErroImportantes(400, "pedido precisa ser um objeto JSON")
    if set(pedido) - set(permitidos):
        raise ErroImportantes(400, "campo desconhecido no pedido")
    return pedido


def _texto(valor, limite: int, rotulo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ErroImportantes(400, f"{rotulo} é obrigatório")
    if len(valor) > limite:
        raise ErroImportantes(400, f"{rotulo} passa de {limite} caracteres")
    if "\x00" in valor:
        raise ErroImportantes(400, f"{rotulo} tem caractere inválido")
    return valor.strip()


def _id(valor) -> str:
    if not isinstance(valor, str) or not ID.fullmatch(valor):
        raise ErroImportantes(400, "id inválido")
    return valor


def _achar(itens: list, ident: str) -> dict:
    for item in itens:
        if item["id"] == ident:
            return item
    raise ErroImportantes(404, "item não encontrado")


def listar() -> dict:
    """Todos os itens: abertos primeiro, depois feitos e descartados; dentro de cada grupo, o mais recente antes."""
    itens, legivel = _ler()
    if not legivel:
        return {"schema_version": SCHEMA_VERSION, "estado": "ilegivel", "itens": [], "contagem": {e: 0 for e in ESTADOS}}
    ordenados = sorted(sorted(itens, key=lambda e: e["criado_em"], reverse=True), key=lambda e: ORDEM_ESTADO[e["estado"]])
    contagem = {estado: sum(1 for e in itens if e["estado"] == estado) for estado in ESTADOS}
    return {"schema_version": SCHEMA_VERSION, "estado": "vazio" if not itens else "ok", "itens": ordenados,
            "contagem": contagem}


def criar(pedido) -> dict:
    pedido = _campos(pedido, CAMPOS_CRIAR)
    texto = _texto(pedido.get("texto"), TEXTO_LIMITE, "texto")

    def alterar(itens):
        if len(itens) >= ITENS_LIMITE:
            raise ErroImportantes(409, "lista cheia; feche ou descarte itens antes de guardar outro")
        item = _novo(texto, "humano")
        itens.append(item)
        return item
    return _mudar(alterar)


def mudar_estado(pedido) -> dict:
    """Marca feito, descarta ou reabre (estado "aberto"). Feito grava a hora; sair de feito a limpa."""
    pedido = _campos(pedido, CAMPOS_ESTADO)
    ident = _id(pedido.get("id"))
    estado = pedido.get("estado")
    if estado not in ESTADOS:
        raise ErroImportantes(400, "estado inválido; use aberto, feito ou descartado")

    def alterar(itens):
        item = _achar(itens, ident)
        if estado == "feito":
            if item["estado"] != "feito":
                item["feito_em"] = _agora()
        else:
            item["feito_em"] = None
        item["estado"] = estado
        return item
    return _mudar(alterar)


def editar(pedido) -> dict:
    """Muda o texto e/ou a nota. Nota vazia limpa a nota."""
    pedido = _campos(pedido, CAMPOS_EDITAR)
    ident = _id(pedido.get("id"))
    mudancas = {}
    if "texto" in pedido:
        mudancas["texto"] = _texto(pedido["texto"], TEXTO_LIMITE, "texto")
    if "nota" in pedido:
        nota = pedido["nota"]
        if not isinstance(nota, str) or len(nota) > NOTA_LIMITE or "\x00" in nota:
            raise ErroImportantes(400, f"nota inválida ou acima de {NOTA_LIMITE} caracteres")
        mudancas["nota"] = nota.strip()
    if not mudancas:
        raise ErroImportantes(400, "nada para editar; informe texto ou nota")

    def alterar(itens):
        item = _achar(itens, ident)
        item.update(mudancas)
        return item
    return _mudar(alterar)


def trazer_do_conselho(cache) -> dict:
    """Traz do cache do Conselho as entradas marcadas IMPORTANTE que ainda não estão aqui. Só lê o cache.
    `cache` é o módulo cache_conselho (ler e filtrar); a rota passa o módulo, os testes passam um substituto."""
    try:
        registros = cache.ler(LEITURA_CACHE)
    except (OSError, ValueError) as erro:
        raise ErroImportantes(500, "cache do Conselho indisponível; nada foi trazido") from erro
    marcadas = [r for r in registros
                if isinstance(r.get("texto"), str) and isinstance(r.get("n"), int) and MARCA_IMPORTANTE.match(r["texto"])]

    def alterar(itens):
        ja = {e["cache_n"] for e in itens if e.get("cache_n") is not None}
        trazidas = ja_estavam = recusadas = 0
        for registro in marcadas:
            if registro["n"] in ja:
                ja_estavam += 1
                continue
            try:
                texto = cache.filtrar(registro["texto"]).strip()
            except ValueError:
                recusadas += 1  # segredo: a entrada não é trazida
                continue
            if not texto or len(texto) > TEXTO_LIMITE_ITEM:
                recusadas += 1
                continue
            if len(itens) >= ITENS_LIMITE:
                raise ErroImportantes(409, "lista cheia; feche ou descarte itens antes de trazer outros")
            itens.append(_novo(texto, "cache", registro["n"]))
            ja.add(registro["n"])
            trazidas += 1
        return {"trazidas": trazidas, "ja_estavam": ja_estavam, "recusadas": recusadas, "lidas": len(registros)}
    return _mudar(alterar)
