#!/usr/bin/env python3
"""Nova versão do Agata no painel: Alexandria, skills, metacognição, corpo, orçamento e eventos.

Leitura em `estado()`; execução por lista fechada em `executar()`, uma por vez (lock).
A consulta vem do Humano pelo painel, limitada a 300 caracteres, e só vira pacote de
evidência (nunca comando). O orçamento só aceita os campos e limites de
`redesign/nova_versao/orcamento.py`; cada mudança vira evento no ledger.
Nada aqui escreve no repositório: os dados ficam em ~/.local/share/agata/nova-versao; chaves de API, no
cofre só de escrita de `redesign/conexoes/segredos.py` (~/.config/agata/conexoes/) — a resposta nunca traz a chave.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in ("nova_versao", "alexandria", "corpo", "metacognicao", "conexoes"):
    sys.path.insert(0, str(ROOT / "redesign" / _p))

ACOES = ("iniciar", "indexar", "consultar", "skills", "fotografar", "salvar_orcamento", "classificar",
         "gravar_chave", "remover_chave", "ajustar_conexao", "adicionar_provedor", "testar_rotas", "cancelar_teste")
_TESTE: dict = {"estado": "ocioso"}
_TESTE_LOCK = threading.Lock()
_LOCK = threading.Lock()


def estado() -> dict:
    import nv  # noqa: E402
    import adaptadores  # noqa: E402
    import testar_rotas  # noqa: E402
    import tarefas  # noqa: E402
    with _TESTE_LOCK:
        job = dict(_TESTE)
    ult = testar_rotas.ultimo()
    return {**nv.estado(), "conexoes": adaptadores.estado(), "gasto_reais": adaptadores.gasto_total_reais(),
            "teste_rotas": {"job": job, "ultimo": {k: ult[k] for k in ("run_id", "quando", "estado", "chamadas",
                                                                       "rotas_que_passaram", "obsoleto")} if ult else None,
                            "resultados": (ult or {}).get("resultados", [])[:60]},
            "tarefas": tarefas.listar(5)}


def _rodar_teste(categorias):
    import testar_rotas  # noqa: E402
    try:
        r = testar_rotas.testar(categorias)
        novo = {"estado": r["estado"], "run_id": r["run_id"]}
    except Exception as e:  # noqa: BLE001
        novo = {"estado": "falhou", "detalhe": f"{e.__class__.__name__}: {str(e)[:160]}"}
    with _TESTE_LOCK:
        _TESTE.clear(); _TESTE.update(novo, fim=time.time())


def executar(acao, dados: dict | None = None) -> dict:
    if acao not in ACOES:
        raise ValueError("ação fora da lista")
    dados = dados if isinstance(dados, dict) else {}
    texto = dados.get("consulta")
    if acao in ("consultar", "skills", "classificar"):
        if not isinstance(texto, str) or not texto.strip() or len(texto) > 300:
            raise ValueError("consulta vazia ou longa demais")
    if acao == "testar_rotas":
        cats = dados.get("categorias")
        if cats is not None and (not isinstance(cats, list) or not set(cats) <= {"local", "gratuito", "assinatura", "pago"}):
            raise ValueError("categoria fora da lista")
        with _TESTE_LOCK:
            if _TESTE.get("estado") == "rodando":
                raise RuntimeError("ocupado")
            _TESTE.clear(); _TESTE.update(estado="rodando", inicio=time.time())
        threading.Thread(target=_rodar_teste, args=(set(cats) if cats else None,), daemon=True).start()
        return {"acao": acao, "resultado": {"estado": "rodando"}}
    if acao == "cancelar_teste":
        import tarefas  # noqa: E402
        rodando = [t for t in tarefas.listar(20) if t["estado"] == "em_execucao"]
        for t in rodando:
            tarefas.cancelar(t["task_id"])
        return {"acao": acao, "resultado": {"canceladas": [t["task_id"] for t in rodando]}}
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError("ocupado")
    try:
        if acao == "iniciar":
            import nv  # noqa: E402
            return {"acao": acao, "resultado": nv.iniciar()}
        if acao == "indexar":
            import acervo  # noqa: E402
            return {"acao": acao, "resultado": acervo.indexar(acervo.snapshot("HEAD", ROOT))}
        if acao == "consultar":
            import acervo  # noqa: E402
            sem = dados.get("semantica") if dados.get("semantica") in ("nunca", "auto", "sempre") else "auto"
            return {"acao": acao, "resultado": acervo.consultar(texto, semantica=sem, salvar=True)}
        if acao == "skills":
            import skills  # noqa: E402
            return {"acao": acao, "resultado": skills.selecionar(texto, n=5)}
        if acao == "classificar":
            import previo  # noqa: E402
            return {"acao": acao, "resultado": previo.classificar({"messages": [{"role": "user", "content": texto}]})}
        if acao == "fotografar":
            import fotografar  # noqa: E402
            import saude  # noqa: E402
            f = fotografar.fotografar()
            return {"acao": acao, "resultado": {"quando": f["quando"], **saude.classificar(f)}}
        if acao in ("gravar_chave", "remover_chave", "ajustar_conexao", "adicionar_provedor"):
            import adaptadores  # noqa: E402
            import segredos  # noqa: E402
            pid = dados.get("provedor")
            if acao == "gravar_chave":
                p = adaptadores.provedor(pid)
                if not p.get("api"):
                    raise ValueError("provedor sem modo API")
                segredos.gravar(pid, dados.get("chave"), (p.get("api") or {}).get("prefixo_chave"))
                return {"acao": acao, "resultado": {"provedor": pid, "gravada": True}}   # a chave nunca volta
            if acao == "remover_chave":
                adaptadores.provedor(pid)
                return {"acao": acao, "resultado": {"provedor": pid, **segredos.remover(pid)}}
            if acao == "ajustar_conexao":
                adaptadores.ajustar(pid, api_modelo=dados.get("api_modelo"), cli_modelo=dados.get("cli_modelo"),
                                    tarifa=dados.get("tarifa"))
                return {"acao": acao, "resultado": {"provedor": pid, "ajustado": True}}
            adaptadores.adicionar_local(pid, dados.get("nome"), dados.get("formato"), dados.get("url"),
                                        dados.get("env"), dados.get("api_modelo"))
            return {"acao": acao, "resultado": {"provedor": pid, "adicionado": True}}
        import orcamento  # noqa: E402
        return {"acao": acao, "resultado": orcamento.salvar(dados.get("orcamento") or {})}
    finally:
        _LOCK.release()
