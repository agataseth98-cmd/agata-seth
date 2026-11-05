#!/usr/bin/env python3
"""sombra_nova_versao.py — a nova versão (Experimento GPT) observando o gateway, só em SOMBRA.

Mesmo padrão de `sombra_capacidade.py`: desligado por padrão (`SETH_SOMBRA_NOVA_VERSAO=1`
liga), uma por vez (Semaphore), thread daemon, nunca derruba nem altera a resposta.

A cada pedido do Humano (não utilitário, não continuação), registra o que a nova versão
TERIA feito, para a avaliação (lote 3) comparar com o caminho atual:
- metacognição (antes): tipo, atualidade, privacidade, risco, limite combinado;
- Alexandria: os objetos que o pacote de evidência traria (só léxico + relações; a
  semântica fica fora da sombra para não carregar a iGPU a cada turno);
- skills: as candidatas que o seletor sugeriria (nenhuma é carregada);
- hidratação (lote 4): se o bloco de evidência da Alexandria seria entregue e com quantos caracteres;
- guarda (lote 4): se a resposta ANTERIOR da Seth repetiu segredo ou frase mandada por uma ferramenta
  do histórico. Só registra; quem bloqueia fora da sombra é outra proposta.

Grava em `<dados>/metacognicao/sombra.jsonl` o hash do pedido, a classificação e os ids
devolvidos — NUNCA o texto do pedido nem os trechos.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (RAIZ / "redesign" / "nova_versao", RAIZ / "redesign" / "alexandria", RAIZ / "redesign" / "metacognicao", AQUI):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

_TRAVA = threading.Semaphore(1)


def ligado() -> bool:
    return os.environ.get("SETH_SOMBRA_NOVA_VERSAO") == "1"


def log_path() -> Path:
    import eventos  # noqa: E402
    return eventos.dados() / "metacognicao" / "sombra.jsonl"


def _ultima(payload: dict) -> str:
    import previo  # noqa: E402
    msgs = payload.get("messages") or []
    return next((previo._texto(m.get("content")) for m in reversed(msgs)
                 if isinstance(m, dict) and m.get("role") == "user"), "")


def observar(payload: dict, rota: str, varrer_pessoal=None) -> dict:
    """O que a nova versão faria com este pedido. Sem efeito, sem texto no resultado."""
    import previo  # noqa: E402
    t0 = time.monotonic()
    ultima = _ultima(payload)
    linha = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rota": rota,
             "pedido_sha256": hashlib.sha256(ultima.encode()).hexdigest(), "erros": []}
    try:
        p = previo.classificar(payload, varrer_pessoal)
        linha["previo"] = {k: p[k] for k in ("tipo", "tokens_est", "ferramentas", "privado", "atualidade", "risco",
                                              "limite_interacao", "estrategia")}
        linha["previo"]["problema_ambiguo"] = bool(p["problema_ambiguo"])
        linha["previo"]["n_sinais_efeito"] = len(p["sinais_efeito"])
    except Exception as e:  # noqa: BLE001
        linha["erros"].append(f"previo: {e.__class__.__name__}")
    try:
        import acervo  # noqa: E402
        pac = acervo.consultar(ultima, n=5, semantica="nunca")
        linha["alexandria"] = {"estado": pac["estado"], "metodos": pac["metodos"], "commit": (pac["commit"] or "")[:12],
                               "objetos": [r["object_id"] for r in pac["resultados"]]}
    except FileNotFoundError:
        linha["alexandria"] = {"estado": "sem índice"}
    except Exception as e:  # noqa: BLE001
        linha["erros"].append(f"alexandria: {e.__class__.__name__}")
    try:
        import hidratacao  # noqa: E402 — o bloco que a hidratação entregaria (lote 4 item 3)
        _b, meta = hidratacao.bloco(ultima)
        linha["hidratacao"] = {"entregaria": bool(_b), "chars": meta["chars"], "context_id": meta["context_id"],
                               "ligada": os.environ.get("SETH_ALEXANDRIA_HIDRATA") == "1"}
    except Exception as e:  # noqa: BLE001
        linha["erros"].append(f"hidratacao: {e.__class__.__name__}")
    try:
        import guarda  # noqa: E402 — a resposta ANTERIOR da Seth repetiu algo que uma ferramenta trouxe? (só registra)
        msgs = payload.get("messages") or []
        idx = max((i for i, m in enumerate(msgs) if isinstance(m, dict) and m.get("role") == "assistant"), default=None)
        if idx is not None:
            fontes = [{"id": f"t{i}", "texto": previo._texto(m.get("content"))} for i, m in enumerate(msgs[:idx])
                      if isinstance(m, dict) and m.get("role") == "tool"]
            g = guarda.checar(previo._texto(msgs[idx].get("content")), fontes)
            linha["guarda_turno_anterior"] = {"estado": g["estado"], "ecos": [e["eco"] for e in g["ecos"]],
                                              "fontes_ferramenta": len(fontes)}
    except Exception as e:  # noqa: BLE001
        linha["erros"].append(f"guarda: {e.__class__.__name__}")
    try:
        # (lote 6) revisão de suporte MECÂNICA da resposta ANTERIOR: os números que ela afirma aparecem no que as
        # ferramentas e o sistema trouxeram? Só contagens e até 5 números -- nunca o texto. Sem revisor de outra família.
        import re as _re  # noqa: E402
        msgs = payload.get("messages") or []
        idx = max((i for i, m in enumerate(msgs) if isinstance(m, dict) and m.get("role") == "assistant"), default=None)
        if idx is None:
            pass
        else:
            ant = previo._texto(msgs[idx].get("content"))
            base = " ".join(previo._texto(m.get("content")) for m in msgs[:idx]
                            if isinstance(m, dict) and m.get("role") in ("tool", "system"))
            ferramentas = sum(1 for m in msgs[:idx] if isinstance(m, dict) and m.get("role") == "tool")
            if ferramentas == 0:
                linha["suporte_turno_anterior"] = {"estado": "sem_fontes"}
            else:
                nums = sorted({n for n in _re.findall(r"(?<![\w.])\d{2,}(?:[.,]\d+)?(?![\w])", ant) if n not in base})
                linha["suporte_turno_anterior"] = {"estado": "revisar" if nums else "ok", "fontes_ferramenta": ferramentas,
                                                   "numeros_sem_suporte": len(nums), "amostra": nums[:5]}
    except Exception as e:  # noqa: BLE001
        linha["erros"].append(f"suporte: {e.__class__.__name__}")
    try:
        import skills  # noqa: E402
        linha["skills"] = [c["skill_id"] for c in skills.selecionar(ultima, n=3)["candidatos"]]
    except FileNotFoundError:
        linha["skills"] = None
    except Exception as e:  # noqa: BLE001
        linha["erros"].append(f"skills: {e.__class__.__name__}")
    linha["ms"] = round((time.monotonic() - t0) * 1000, 1)
    return linha


def registrar(payload: dict, rota: str) -> None:
    """Dispara a sombra sem esperar; uma por vez. Nunca levanta."""
    if not ligado() or not _TRAVA.acquire(blocking=False):
        return

    def _rodar():
        try:
            linha = observar(payload, rota)
            p = log_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(linha, ensure_ascii=False) + "\n")
        except Exception as e:  # noqa: BLE001
            print(f"sombra_nova_versao: não registrou ({e.__class__.__name__})", file=sys.stderr, flush=True)
        finally:
            _TRAVA.release()
    threading.Thread(target=_rodar, daemon=True).start()


def _caso_suporte() -> bool:
    msgs = [{"role": "user", "content": "qual o preço?"},
            {"role": "tool", "content": "Tabela: preço 47 reais; prazo 9 dias"},
            {"role": "assistant", "content": "Custa 47 reais e leva 365 dias, segundo a segredo-xyz."}]
    linha = observar({"messages": msgs}, "seth-livre", lambda x: [])
    s = linha.get("suporte_turno_anterior", {})
    return s.get("estado") == "revisar" and s.get("amostra") == ["365"] and "segredo-xyz" not in json.dumps(linha)


def _selftest() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        os.environ["AGATA_NV_DIR"] = t
        os.environ["AGATA_NV_CACHE"] = t + "/cache"
        segredo = "frase-que-nao-pode-ir-para-o-log-7781"
        payload = {"messages": [{"role": "user", "content": f"apague o arquivo {segredo} hoje"}]}
        linha = observar(payload, "seth-livre", lambda x: [])
        bruto = json.dumps(linha, ensure_ascii=False)
        casos = [
            ("texto do pedido não vai para o registro", segredo not in bruto and "apague" not in bruto),
            ("hash do pedido registrado", len(linha["pedido_sha256"]) == 64),
            ("prévio marca efeito e atualidade", linha.get("previo", {}).get("risco") == "efeito"
             and linha["previo"]["atualidade"] == "volatil"),
            ("sem índice não quebra", linha.get("alexandria", {}).get("estado") == "sem índice"),
            ("desligado por padrão", os.environ.get("SETH_SOMBRA_NOVA_VERSAO") == "1" or not ligado()),
            ("suporte: número sem fonte aparece, texto não", _caso_suporte()),
        ]
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(_selftest())
    print(__doc__)
    sys.exit(2)
