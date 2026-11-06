"""Conselho: convocação de pareceres entre modelos, com regras de classe de dado.

Regras:
- D2: dado pessoal só vai a rota local; segredo nunca sai (é recusado sempre).
- D3: cota gratuita compartilhada com a Seth (rota com compartilhada_com_seth=True
  e categoria "gratuito") é permitida sem teto; gera aviso visível, nunca recusa.
- Uma rota por família; a família não é consultada duas vezes.
- A resposta de cada modelo é DADO: é guardada literal, nunca executada,
  nunca interpretada como instrução.
- Parecer em quatro partes: Origem, Posição, Fundamentação, Emenda.
- Divergência de Posição entre pareceres vira "lacuna"; não há votação.

O transporte é injetado: convocar() não chama provedor nenhum por conta própria.
"""

import re
import sys
import unicodedata

CLASSES = ("publico", "pessoal", "segredo")
PARTES = ("origem", "posicao", "fundamentacao", "emenda")

_RE_INICIO_LINHA = re.compile(r"^[\s#*_>`\-]+")
_RE_POSICAO = re.compile(r"^posicao\b[\s*_:\-—]*(.*)$")


def _norm(texto):
    """Minúsculas e sem acento, para comparar títulos e posições."""
    sem = unicodedata.normalize("NFKD", texto)
    sem = "".join(c for c in sem if not unicodedata.combining(c))
    return sem.casefold()


def _linhas_normalizadas(texto):
    for linha in texto.splitlines():
        yield _norm(_RE_INICIO_LINHA.sub("", linha)).strip()


def _tem_partes(texto):
    linhas = list(_linhas_normalizadas(texto))
    return all(
        any(re.match(re.escape(parte) + r"\b", linha) for linha in linhas)
        for parte in PARTES
    )


def _posicao(texto):
    """Valor da linha que começa com Posição, normalizado; None se não houver."""
    for linha in _linhas_normalizadas(texto):
        m = _RE_POSICAO.match(linha)
        if m:
            return " ".join(m.group(1).split()).strip(" .*_")
    return None


def _elegivel(rota, classe):
    if classe not in rota.get("classes_permitidas", []):
        return False
    if classe == "pessoal" and rota.get("categoria") != "local":
        return False
    return True


def _recusa(motivo):
    aviso = "recusado: " + motivo
    return {
        "pareceres": [],
        "divergencia": False,
        "lacuna": False,
        "aviso": aviso,
        "avisos": [aviso],
    }


def _cota_compartilhada_gratuita(rota):
    """D3: rota gratuita que compartilha cota com a Seth (sem teto, só aviso)."""
    return rota.get("categoria") == "gratuito" and bool(rota.get("compartilhada_com_seth", False))


def convocar(pedido, motivo, quem_convoca, rotas, transporte, classe_dados="publico"):
    """Convoca pareceres de até uma rota por família.

    motivo e quem_convoca são recebidos para a trilha de quem convocou;
    esta função não os grava.
    """
    if not isinstance(pedido, str) or not pedido.strip():
        return _recusa("pedido vazio")
    if classe_dados == "segredo":
        return _recusa("classe segredo nunca sai da Máquina")
    if classe_dados not in CLASSES:
        return _recusa("classe de dado desconhecida: %r" % (classe_dados,))

    escolhidas = []
    familias_vistas = set()
    for rota in rotas:
        if not _elegivel(rota, classe_dados):
            continue
        familia = rota["familia"]
        if familia in familias_vistas:
            continue
        familias_vistas.add(familia)
        escolhidas.append(rota)

    if not escolhidas:
        if classe_dados == "pessoal":
            return _recusa("dado pessoal sem rota local permitida")
        return _recusa("nenhuma rota elegível para a classe %s" % classe_dados)

    # D3 é aviso, não bloqueio. Sai ANTES da primeira chamada: quem decide chamar
    # o conselho já vê que as rotas escolhidas gastam cota compartilhada com a Seth.
    avisos_d3 = [
        "D3: rota %s usa cota compartilhada com a Seth, sem teto" % rota["id"]
        for rota in escolhidas
        if _cota_compartilhada_gratuita(rota)
    ]
    # Decisão do Humano (06/11): o aviso D3 sai em stderr ANTES da primeira chamada.
    # Quem convoca precisa manter o stderr visível; o retorno também traz o aviso.
    for aviso in avisos_d3:
        sys.stderr.write("AVISO D3 (antes da chamada): %s\n" % aviso)
    pareceres = []
    for rota in escolhidas:
        texto = transporte(rota, pedido)
        if not isinstance(texto, str):
            raise TypeError("transporte deve devolver str, não %s" % type(texto).__name__)
        pareceres.append({
            "rota": rota["id"],
            "familia": rota["familia"],
            "texto": texto,
            "formato_ok": _tem_partes(texto),
            "e_dado": True,
        })

    posicoes = {p for p in (_posicao(par["texto"]) for par in pareceres) if p is not None}
    divergencia = len(posicoes) > 1

    avisos = list(avisos_d3)
    if divergencia:
        avisos.append("lacuna: divergência; sem votação.")
    else:
        avisos.append("sem divergência de posição entre famílias.")
    fora = [par["rota"] for par in pareceres if not par["formato_ok"]]
    if fora:
        avisos.append("fora_do_formato: " + ", ".join(fora) + " (não reenviado).")
    return {
        "pareceres": pareceres,
        "divergencia": divergencia,
        "lacuna": divergencia,
        "aviso": " ".join(avisos),
        "avisos": avisos,
    }
