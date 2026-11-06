"""Hierarquia de buscas da Alexandria: cada forma de pesquisa disponível, escolhida caso a caso.

Formas: `lexico` (texto no acervo, com relações), `semantica` (sentido, ferramenta secundária, (327)) e
`externa` (evidência efêmera, C3). Modos:
- `auto`: começa pelo léxico; se a suficiência (C2) não bastar, acrescenta a semântica; se ainda faltar e a
  pesquisa externa estiver configurada, acrescenta a externa. Cada etapa registra o motivo.
- `lexico`, `semantica`, `externa`: só a forma pedida, sem passos extras.
- `todos`: todas as formas disponíveis, para comparar.

A externa nunca entra no índice nem vira resultado do acervo: volta como `externa` do pacote, rotulada.
Quem decide a ordem é `etapas_para` (pura, testável). A execução só chama `consultar` e `externa.pesquisar`.
"""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
for _p in (AQUI, AQUI.parent / "nova_versao", AQUI.parent / "metacognicao"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

MODOS = ("auto", "lexico", "semantica", "externa", "todos")


def etapas_para(modo: str, *, suficiente: bool | None = None, externa_disponivel: bool = False) -> list[str]:
    """Ordem das etapas. `suficiente` é o resultado da etapa léxica (None = ainda não medido)."""
    if modo not in MODOS:
        raise ValueError(f"modo fora da lista: {modo}")
    if modo == "lexico":
        return ["lexico"]
    if modo == "semantica":
        return ["semantica"]
    if modo == "externa":
        return ["externa"] if externa_disponivel else []
    if modo == "todos":
        return ["lexico", "semantica"] + (["externa"] if externa_disponivel else [])
    # auto
    etapas = ["lexico"]
    if suficiente is True:
        return etapas
    etapas.append("semantica")
    if suficiente is False and externa_disponivel:
        etapas.append("externa")
    return etapas


def pesquisar(consulta: str, *, modo: str = "auto", acesso: str = "public", n: int = 8,
              consultar=None, buscar_externa=None, externa_disponivel: bool | None = None) -> dict:
    """Executa a hierarquia escolhida e devolve o pacote com as etapas registradas."""
    if modo not in MODOS:
        raise ValueError(f"modo fora da lista: {modo}")
    import acervo  # noqa: E402
    import externa  # noqa: E402
    consultar = consultar or acervo.consultar
    if externa_disponivel is None:
        externa_disponivel = buscar_externa is not None
    registro, pacote, ext = [], None, None

    def etapa_lexica_ou(semantica: str):
        return consultar(consulta, acesso=acesso, n=n, semantica=semantica)

    if modo in ("lexico", "semantica", "todos"):
        semantica = "sempre" if modo in ("semantica", "todos") else "nunca"
        pacote = etapa_lexica_ou(semantica)
        registro.append({"etapa": "lexico" if modo == "lexico" else "lexico+semantica",
                         "motivo": "modo pedido", "resultados": len(pacote["resultados"])})
    if modo == "auto":
        pacote = etapa_lexica_ou("nunca")
        suf = pacote["suficiencia"]
        registro.append({"etapa": "lexico", "motivo": "primeira etapa", "suficiente": suf["suficiente"],
                         "cobertura": suf["cobertura"]})
        if not suf["suficiente"]:
            pacote = etapa_lexica_ou("auto")
            registro.append({"etapa": "semantica", "motivo": suf["motivo"],
                             "resultados": len(pacote["resultados"])})
            suf = pacote["suficiencia"]
    if (modo == "externa") or (modo == "todos" and externa_disponivel) or \
       (modo == "auto" and externa_disponivel and pacote and not pacote["suficiencia"]["suficiente"]):
        if pacote is None:
            pacote = etapa_lexica_ou("nunca")
        motivo = "modo pedido" if modo in ("externa", "todos") else pacote["suficiencia"]["motivo"]
        if externa_disponivel:
            ext = externa.pesquisar(consulta, buscar=buscar_externa)
            registro.append({"etapa": "externa", "motivo": motivo, "estado": ext.get("estado"),
                             "resultados": len(ext.get("resultados") or [])})
        else:
            registro.append({"etapa": "externa", "motivo": motivo, "estado": "indisponível"})
    if pacote is None:
        pacote = etapa_lexica_ou("nunca")
    pacote["hierarquia"] = {"modo": modo, "etapas": registro,
                            "previstas": etapas_para(modo, suficiente=pacote["suficiencia"]["suficiente"],
                                                     externa_disponivel=externa_disponivel)}
    pacote["externa"] = externa.para_contexto(ext) if ext else []
    return pacote
