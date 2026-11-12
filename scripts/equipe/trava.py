#!/usr/bin/env python3
"""trava.py -- serialização da aplicação de propostas P-8 (12/11/2026).

Regra: enquanto uma aplicação está em curso, nenhuma PROPOSTA que toca o registro (MEMÓRIAS.md,
ONDE_ESTAMOS.md, INDICE_MEMORIAS*.md) entra no main. Motivo: a aplicação fica atrás da base quando
uma proposta mergeia no meio (incidente de 12/11/2026, PR #980 com a proposta #979).

Dois marcadores da mesma trava:
  - local: propostas/.aplicando-<nome> na cópia do Humano, escrito pelo aplicar.py e removido no fim
    (contém o PID; marcador de processo morto é velho e pode ser retirado);
  - remoto (o que o CI enxerga, porque o arquivo local não chega ao runner): uma PR aberta cujo head
    começa com `aplica/`. O fiscal lê isso com `gh pr list`.

Uso (CLI):
  gh pr list --state open --json headRefName | python3 -I scripts/equipe/trava.py --proposta <toca_registro 0|1> <consome_par 0|1>
     exit 0 = pode seguir; 1 = bloqueada (aplicação em curso); 2 = entrada inválida (falha fechada)
  python3 -I scripts/equipe/trava.py --marcar <raiz> <nome>     (exit 1 se já existe marcador vivo)
  python3 -I scripts/equipe/trava.py --soltar <raiz> <nome>
  python3 -I scripts/equipe/trava.py --ativos <raiz>            (lista os marcadores vivos; exit 1 se houver)
  python3 -I scripts/equipe/trava.py --selftest
"""
import json
import os
import sys

REGISTRO = ("MEMÓRIAS.md", "ONDE_ESTAMOS.md", "INDICE_MEMORIAS.md", "INDICE_MEMORIAS_PALAVRAS-CHAVE.md")
PREFIXO_APLICACAO = "aplica/"


def aplicacoes_abertas(heads):
    return [h for h in heads if isinstance(h, str) and h.startswith(PREFIXO_APLICACAO)]


def bloqueia(toca_registro, consome_par, heads_abertas):
    """Lista das aplicações em curso que bloqueiam esta PR. Vazia = pode seguir.
    A própria aplicação (consome par assinado) nunca é bloqueada: ela é a trava."""
    if consome_par or not toca_registro:
        return []
    return aplicacoes_abertas(heads_abertas)


def _caminho(raiz, nome):
    return os.path.join(raiz, "propostas", ".aplicando-" + nome)


def _vivo(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def ativos(raiz):
    """Marcadores locais de processo vivo. Marcador de processo morto é removido (aplicação caiu no meio)."""
    pasta = os.path.join(raiz, "propostas")
    if not os.path.isdir(pasta):
        return []
    vivos = []
    for nome in sorted(os.listdir(pasta)):
        if not nome.startswith(".aplicando-"):
            continue
        p = os.path.join(pasta, nome)
        try:
            pid = int(open(p, encoding="utf-8").read().strip() or "0")
        except (OSError, ValueError):
            pid = 0
        if pid and _vivo(pid):
            vivos.append(nome[len(".aplicando-"):])
        else:
            try:
                os.remove(p)
            except OSError:
                pass
    return vivos


def marcar(raiz, nome):
    """Cria o marcador de forma exclusiva. Erro se já houver aplicação viva."""
    if ativos(raiz):
        raise RuntimeError(f"aplicação em curso: {', '.join(ativos(raiz))}")
    os.makedirs(os.path.join(raiz, "propostas"), exist_ok=True)
    with open(_caminho(raiz, nome), "x", encoding="utf-8") as f:
        f.write(str(os.getpid()))


def soltar(raiz, nome):
    try:
        os.remove(_caminho(raiz, nome))
    except FileNotFoundError:
        pass


def _selftest():
    import tempfile
    falhas = []
    if bloqueia(True, False, [{"x": 1}, "proposta/y"]) != []:
        falhas.append("entrada inválida não pode bloquear")
    if bloqueia(True, False, ["aplica/pacote-x", "proposta/y"]) != ["aplica/pacote-x"]:
        falhas.append("proposta de registro com aplicação aberta deve bloquear")
    if bloqueia(False, False, ["aplica/pacote-x"]) != []:
        falhas.append("proposta que não toca registro não é bloqueada")
    if bloqueia(True, True, ["aplica/pacote-x"]) != []:
        falhas.append("a aplicação (consome par) não se bloqueia")
    with tempfile.TemporaryDirectory() as raiz:
        marcar(raiz, "pacote-x")
        if ativos(raiz) != ["pacote-x"]:
            falhas.append("marcador vivo não listado")
        try:
            marcar(raiz, "outro")
            falhas.append("segunda aplicação deveria ser recusada")
        except RuntimeError:
            pass
        soltar(raiz, "pacote-x")
        if ativos(raiz):
            falhas.append("soltar não removeu")
        # marcador de processo morto: removido na varredura, não trava para sempre
        os.makedirs(os.path.join(raiz, "propostas"), exist_ok=True)
        with open(os.path.join(raiz, "propostas", ".aplicando-velho"), "w") as f:
            f.write("999999999")
        if ativos(raiz) or os.path.exists(os.path.join(raiz, "propostas", ".aplicando-velho")):
            falhas.append("marcador de processo morto deveria sumir")
    if falhas:
        print("SELFTEST FALHOU:\n  " + "\n  ".join(falhas))
        return 1
    print("SELFTEST OK -- 4 regras de bloqueio + marcador (criar, recusar segunda, soltar, morto)")
    return 0


def main(argv):
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    if argv[0] == "--selftest":
        return _selftest()
    if argv[0] == "--marcar" and len(argv) == 3:
        try:
            marcar(argv[1], argv[2])
            return 0
        except RuntimeError as e:
            print(f"ERRO: {e}", file=sys.stderr)
            return 1
    if argv[0] == "--soltar" and len(argv) == 3:
        soltar(argv[1], argv[2])
        return 0
    if argv[0] == "--ativos" and len(argv) == 2:
        vivos = ativos(argv[1])
        print("\n".join(vivos))
        return 1 if vivos else 0
    if argv[0] == "--proposta" and len(argv) == 3 and argv[1] in ("0", "1") and argv[2] in ("0", "1"):
        try:
            dados = json.load(sys.stdin)
            heads = [d.get("headRefName", "") for d in dados]
        except (ValueError, AttributeError, TypeError):
            print("ERRO: entrada da lista de PRs inválida (falha fechada)", file=sys.stderr)
            return 2
        em_curso = bloqueia(argv[1] == "1", argv[2] == "1", heads)
        if em_curso:
            print("aplicação em curso: " + ", ".join(em_curso))
            return 1
        print("OK: nenhuma aplicação em curso")
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
