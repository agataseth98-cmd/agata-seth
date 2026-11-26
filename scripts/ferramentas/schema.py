#!/usr/bin/env python3
"""Schema e carga das fontes de ferramentas (lote ferramentas-unificadas-26-11).

Fonte canônica: config/ferramentas/{mcp,skills,agentes}.yml (sob P-8). Overlay do Humano:
~/agata-local/ferramentas.yml, mesmo schema, sobrepõe por nome. Nenhum campo guarda valor de segredo:
`env` é lista de NOMES de variável, `url` não pode trazer usuário, senha nem query, e `args` passa por
uma checagem de padrões de segredo (heurística, não prova). Erros nomeiam campo e arquivo, nunca valor.
"""
from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import yaml

CLIS = ("claude", "codex", "opencode")
TIPOS = ("mcp", "skills", "agentes")
CATEGORIA = {"mcp": "mcp", "skills": "skill", "agentes": "agente"}
ARQUIVO_CANON = {"mcp": "mcp.yml", "skills": "skills.yml", "agentes": "agentes.yml"}
PREFIXO_ORIGEM = {"skills": ".agents/skills/", "agentes": ".claude/agents/"}
TOPO_CANON = {"mcp": {"mcp"}, "skills": {"skills", "indice"}, "agentes": {"agentes"}}
OBRIGATORIOS = {
    "mcp": {"nome", "transporte", "clis"},
    "skills": {"nome", "origem", "clis"},
    "agentes": {"nome", "origem", "clis"},
}
ESPECIFICOS = {"mcp": {"transporte", "comando", "args", "url", "env"}, "skills": set(), "agentes": set()}
COMUNS = {"adotar", "gerenciado", "motivo", "descricao"}
RE_NOME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
RE_VARIAVEL = re.compile(r"[A-Z_][A-Z0-9_]*")
RE_CAMPO_SEGURO = re.compile(r"[a-z_]{1,32}")
# Heurística: nome=valor de chave conhecida ou prefixo de token conhecido em args.
RE_SEGREDO_ARG = re.compile(
    r"(?i)(token|senha|secret|password|passwd|apikey|api_key)\s*[=:]|\b(ghp_|github_pat_|sk-|xox[bp]-)"
)


class ErroSchema(ValueError):
    """Fonte fora do schema. A mensagem nomeia campo e arquivo; nunca traz valor."""


@dataclass
class Fonte:
    entradas: dict  # tipo -> OrderedDict nome -> entrada normalizada (overlay sobrepõe por nome)
    origem: dict  # tipo -> nome -> "canonico" | "overlay"
    canonico: dict  # tipo -> OrderedDict nome -> entrada (só a fonte canônica)
    indice: str | None


def _erro(onde: str, msg: str) -> ErroSchema:
    return ErroSchema(f"{onde}: {msg}")


def _nomes_seguros(campos) -> str:
    return ", ".join(c if isinstance(c, str) and RE_CAMPO_SEGURO.fullmatch(c) else "[campo não listável]" for c in campos)


def _validar_mcp(dado: dict, onde: str) -> dict:
    transporte = dado["transporte"]
    if transporte not in ("stdio", "http"):
        raise _erro(onde, "transporte tem de ser stdio ou http")
    if transporte == "stdio":
        if "url" in dado:
            raise _erro(onde, "url só vale com transporte http")
        comando = dado.get("comando")
        if not isinstance(comando, str) or not comando.strip():
            raise _erro(onde, "transporte stdio exige comando")
        args = dado.get("args", [])
        if not isinstance(args, list) or not all(isinstance(a, str) and "\n" not in a for a in args):
            raise _erro(onde, "args é lista de texto, uma entrada por argumento")
        for a in args:
            if RE_SEGREDO_ARG.search(a):
                raise _erro(onde, "args parece trazer segredo; passe a variável em env (só o nome)")
        env = dado.get("env", [])
        if not isinstance(env, list):
            raise _erro(onde, "env é lista de nomes de variável")
        for var in env:
            if not isinstance(var, str) or not RE_VARIAVEL.fullmatch(var):
                raise _erro(onde, "env lista só nomes de variável (maiúsculas, números e _); valor não entra na fonte")
        return {"transporte": "stdio", "comando": comando, "args": list(args), "url": None, "env": list(env)}
    for campo in ("comando", "args", "env"):
        if campo in dado:
            raise _erro(onde, f"{campo} só vale com transporte stdio")
    url = dado.get("url")
    if not isinstance(url, str):
        raise _erro(onde, "transporte http exige url")
    p = urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password or p.query or p.fragment:
        raise _erro(onde, "url tem de ser http(s), sem usuário, senha, query ou fragmento")
    return {"transporte": "http", "comando": None, "args": [], "url": url, "env": []}


def validar_entrada(tipo: str, dado, onde: str = "entrada") -> dict:
    """Valida uma entrada de um tipo e devolve a forma normalizada (com padrões preenchidos)."""
    if not isinstance(dado, dict):
        raise _erro(onde, "a entrada tem de ser um mapa")
    permitidos = OBRIGATORIOS[tipo] | ESPECIFICOS[tipo] | COMUNS
    fora = set(dado) - permitidos
    if fora:
        raise _erro(onde, "campo fora do schema: " + _nomes_seguros(sorted(fora, key=str)))
    faltam = OBRIGATORIOS[tipo] - set(dado)
    if faltam:
        raise _erro(onde, "campo obrigatório ausente: " + _nomes_seguros(sorted(faltam)))
    nome = dado["nome"]
    if not isinstance(nome, str) or len(nome) > 64 or not RE_NOME.fullmatch(nome):
        raise _erro(onde, "nome deve ser minúsculas, números e hífen (até 64 caracteres)")
    clis = dado["clis"]
    if not isinstance(clis, list) or not clis or len(set(clis)) != len(clis) or any(c not in CLIS for c in clis):
        raise _erro(onde, "clis é lista não vazia, sem repetição, de: " + ", ".join(CLIS))
    adotar = dado.get("adotar", False)
    gerenciado = dado.get("gerenciado", True)
    if not isinstance(adotar, bool) or not isinstance(gerenciado, bool):
        raise _erro(onde, "adotar e gerenciado são true ou false")
    motivo = dado.get("motivo", "")
    if not isinstance(motivo, str):
        raise _erro(onde, "motivo é texto")
    if not gerenciado and not motivo.strip():
        raise _erro(onde, "gerenciado: false exige motivo")
    descricao = dado.get("descricao", "")
    if not isinstance(descricao, str):
        raise _erro(onde, "descricao é texto")
    saida = {
        "nome": nome,
        "clis": list(clis),
        "adotar": adotar,
        "gerenciado": gerenciado,
        "motivo": motivo,
        "descricao": descricao,
    }
    if tipo == "mcp":
        saida.update(_validar_mcp(dado, onde))
        return saida
    origem = dado["origem"]
    prefixo = PREFIXO_ORIGEM[tipo]
    partes = origem.split("/") if isinstance(origem, str) else []
    if not isinstance(origem, str) or not origem.startswith(prefixo) or ".." in partes or origem.endswith("/"):
        raise _erro(onde, f"origem tem de ficar em {prefixo}, sem '..'")
    base = partes[-1]
    if tipo == "skills" and base != nome:
        raise _erro(onde, "em skills, o último trecho da origem é o nome da skill")
    if tipo == "agentes" and base != nome + ".md":
        raise _erro(onde, "em agentes, a origem é <nome>.md")
    saida["origem"] = origem
    return saida


def _ler_yaml(caminho: Path, obrigatorio: bool) -> dict:
    if not caminho.exists():
        if obrigatorio:
            raise ErroSchema(f"{caminho}: fonte ausente")
        return {}
    try:
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        # só o tipo do erro: a mensagem do PyYAML mostra trechos do arquivo
        raise ErroSchema(f"{caminho}: YAML inválido ({type(e).__name__})") from None
    if not isinstance(dados, dict):
        raise ErroSchema(f"{caminho}: o topo tem de ser um mapa")
    return dados


def _checar_topo(dados: dict, permitidos: set, onde: str) -> None:
    fora = set(dados) - permitidos
    if fora:
        raise _erro(onde, "chave de topo fora do schema: " + _nomes_seguros(sorted(fora, key=str)))


def _lista(tipo: str, bruto, onde: str) -> OrderedDict:
    if bruto is None:
        bruto = []
    if not isinstance(bruto, list):
        raise _erro(onde, f"{tipo} tem de ser lista")
    saida: OrderedDict = OrderedDict()
    for i, item in enumerate(bruto):
        e = validar_entrada(tipo, item, f"{onde} [{tipo}][{i}]")
        if e["nome"] in saida:
            raise _erro(onde, f"nome repetido em {tipo}: {e['nome']}")
        saida[e["nome"]] = e
    return saida


def carregar_overlay(caminho: Path) -> dict:
    """Overlay do Humano como tipo -> OrderedDict nome -> entrada. Arquivo ausente é overlay vazio."""
    dados = _ler_yaml(caminho, obrigatorio=False)
    _checar_topo(dados, set(TIPOS), str(caminho))
    return {tipo: _lista(tipo, dados.get(tipo), str(caminho)) for tipo in TIPOS}


def carregar_canonico(raiz: Path) -> tuple[dict, str | None]:
    """Fonte canônica como tipo -> OrderedDict, e o ponteiro de índice de skills (se houver)."""
    canon, indice = {}, None
    for tipo in TIPOS:
        arq = raiz / "config" / "ferramentas" / ARQUIVO_CANON[tipo]
        dados = _ler_yaml(arq, obrigatorio=True)
        _checar_topo(dados, TOPO_CANON[tipo], str(arq))
        if tipo == "skills":
            indice = dados.get("indice")
            if indice is not None and not isinstance(indice, str):
                raise _erro(str(arq), "indice é um caminho de texto")
        canon[tipo] = _lista(tipo, dados.get(tipo), str(arq))
    return canon, indice


def carregar_fontes(raiz: Path, overlay: Path) -> Fonte:
    """Canônico ∪ overlay; o overlay sobrepõe por nome e a origem de cada entrada fica registrada."""
    canon, indice = carregar_canonico(raiz)
    ov = carregar_overlay(overlay)
    entradas, origem = {}, {}
    for tipo in TIPOS:
        mesclada: OrderedDict = OrderedDict()
        origem_tipo: dict = {}
        for nome, e in canon[tipo].items():
            mesclada[nome] = e
            origem_tipo[nome] = "canonico"
        for nome, e in ov[tipo].items():
            mesclada[nome] = e
            origem_tipo[nome] = "overlay"
        entradas[tipo] = mesclada
        origem[tipo] = origem_tipo
    return Fonte(entradas=entradas, origem=origem, canonico=canon, indice=indice)


def para_yml(tipo: str, e: dict) -> dict:
    """Forma de arquivo (só campos informados, sem padrões) para gravar no overlay ou propor no canônico."""
    d: dict = {"nome": e["nome"]}
    if tipo == "mcp":
        d["transporte"] = e["transporte"]
        if e["transporte"] == "stdio":
            d["comando"] = e["comando"]
            if e["args"]:
                d["args"] = list(e["args"])
            if e["env"]:
                d["env"] = list(e["env"])
        else:
            d["url"] = e["url"]
    else:
        d["origem"] = e["origem"]
    d["clis"] = list(e["clis"])
    if e["adotar"]:
        d["adotar"] = True
    if not e["gerenciado"]:
        d["gerenciado"] = False
        d["motivo"] = e["motivo"]
    if e["descricao"]:
        d["descricao"] = e["descricao"]
    return d


def serializar_overlay(ov: dict) -> dict:
    """Overlay (tipo -> OrderedDict) na forma de arquivo, pronta para yaml.safe_dump."""
    return {tipo: [para_yml(tipo, e) for e in ov[tipo].values()] for tipo in TIPOS}
