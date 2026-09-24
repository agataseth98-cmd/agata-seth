#!/usr/bin/env python3
"""seth_verificador -- canal de VERIFICAÇÃO da Seth (:20141). Read-only.

POR QUE EXISTE (MEMÓRIAS (423)):
Em 10/09/2026 a Seth pediu, com bons argumentos, "um interpretador de código
genérico e sandboxed" com shell arbitrário, git e escrita livre no sistema de
arquivos, para poder auditar o repositório, rodar `perimetro.sh` e verificar o
estado sem depender do Humano. O pedido é legítimo: sem isso ela afirma sobre o
sistema lendo só o que lhe injetam, e a Regra 2 manda medir, não lembrar.

O que ela NÃO pode ganhar é escrita. Hoje o único caminho de escrita da Seth é
o seth_escriba (append-only, verificação pós-escrita), e é isso que faz o P-8,
o P-11 e o sanitizador valerem para ela. Shell aberto dissolve os três de uma
vez: com `sh -c` qualquer um deles se contorna em uma linha.

Este serviço é a resposta: **ela ganha o poder de verificar, não o de mudar.**
Uma lista FECHADA de comandos de verificação, sem shell, sem string do modelo
chegando a um interpretador. Ela consegue quase tudo que pediu; o sistema não
perde nenhuma trava.

DESENHO -- cada trava tem motivo, não é cerimônia:

1. LISTA FECHADA, não comando livre. O corpo traz um NOME de comando; o argv
   real está aqui no código. Nome fora da lista -> 400. Não existe caminho em
   que texto do modelo vire comando.
2. SEM SHELL. `subprocess.run(argv, shell=False)`. Sem `sh -c`, sem `os.system`,
   sem f-string montando linha de comando. Injeção não tem por onde entrar.
3. ARGUMENTO ÚNICO E TIPADO. Só `n` (quantas linhas de log), inteiro, faixa
   fechada. Validado antes de virar argv, e convertido por `int()`, nunca
   interpolado como texto.
4. SAÍDA REDIGIDA pela MESMA régua do P-1 e do sanitizador de egresso
   (`scripts/varredura_segredo.sh`). Motivo concreto: `git diff` da árvore de
   trabalho pode conter um segredo que o Humano colou e ainda não commitou --
   o P-1 só guarda o commit. Sem esta camada, o canal de leitura viraria uma
   porta de vazamento que os outros controles não vigiam.
5. TETO COM TOTAL DECLARADO. Corta a saída, mas diz quantas linhas existiam.
   A própria Seth apontou, no mesmo pedido, que truncamento sem total a força a
   declarar `lacuna: leitura parcial`. Aqui ela recebe o número.
6. TIMEOUT em tudo. Comando pendurado devolve erro, não trava a conversa.
7. BIND em 127.0.0.1. Igual ao resto do sistema.

O QUE ESTE SERVIÇO NÃO FAZ, e não deve passar a fazer sem proposta própria:
escrever, commitar, empurrar, apagar, instalar, reiniciar serviço, ler arquivo
arbitrário, ou aceitar qualquer comando que não esteja na lista abaixo.

Fonte versionada: ~/agata/redesign/router/seth_verificador.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

BIND = os.environ.get("SETH_VERIFICADOR_BIND", "127.0.0.1:20141")
REPO = Path(os.environ.get("SETH_REPO", str(Path.home() / "agata")))
sys.path.insert(0, str(REPO / "scripts"))
from http_seguro import ServidorConcorrenciaLimitada  # noqa: E402
TETO_CHARS = int(os.environ.get("SETH_VERIFICADOR_TETO", "24000"))
CORPO_MAX = 4096  # pedido é minúsculo; corpo grande é erro ou abuso

# --- a lista fechada ------------------------------------------------------
# nome -> (argv, timeout_s, descrição para a Seth)
# argv NUNCA é montado a partir do corpo do pedido. O único ponto variável é
# `n`, tratado à parte em _argv().
COMANDOS: dict[str, tuple[list[str], int, str]] = {
    "perimetro": (
        ["bash", "scripts/perimetro.sh"], 300,
        "Roda os 17 controles do perímetro e devolve o veredito de cada um. "
        "É a verificação mais completa que existe no sistema.",
    ),
    "estado": (
        ["bash", "scripts/estado_para_eco.sh"], 60,
        "Fatos da Máquina agora: HEAD, topo de MEMÓRIAS, sync, hora, HASH-ESTADO.",
    ),
    "git_status": (
        ["git", "status", "--porcelain=v1", "-b"], 30,
        "O que está modificado/staged e a relação com o remoto.",
    ),
    "git_log": (
        ["git", "log", "--oneline", "-n"], 30,
        "Últimos commits (use `n` para quantos; 1 a 50).",
    ),
    "git_diff_stat": (
        ["git", "diff", "--stat", "HEAD"], 30,
        "Resumo do que difere de HEAD, por arquivo. Não mostra conteúdo.",
    ),
    "git_sync": (
        ["git", "ls-remote", "origin", "main"], 60,
        "SHA do remoto, para comparar com HEAD local. É o método 1 de "
        "REGRAS, 'Verificação de canônico'.",
    ),
    "selos": (
        ["bash", "scripts/selar.sh", "--check"], 120,
        "Confere o hash de cada chunk frio selado (P-14).",
    ),
    "suite_controles": (
        ["bash", "scripts/testar_perimetro.sh"], 600,
        "Roda a suíte de regressão dos controles (vermelho/verde, clone "
        "descartável). Demora ~30s.",
    ),
    "servicos": (
        ["systemctl", "--user", "--failed", "--no-pager", "--plain"], 30,
        "Unidades de usuário em FALHA (`systemctl --user --failed`). "
        "'0 loaded units listed' = nenhuma falhando = saudável.",
    ),
}


def _argv(nome: str, n: int | None) -> list[str]:
    """argv final. `n` é o ÚNICO ponto variável, e entra como inteiro."""
    base = list(COMANDOS[nome][0])
    if nome == "git_log":
        if n is None:
            n = 10
        if not isinstance(n, int) or isinstance(n, bool) or not (1 <= n <= 50):
            raise ValueError("n tem de ser inteiro entre 1 e 50")
        base.append(str(int(n)))
    elif n is not None:
        raise ValueError(f"'{nome}' não aceita o parâmetro n")
    return base


# --- redação de segredo, pela régua canônica ------------------------------
def _padroes() -> list[str]:
    """Lê PADROES_SEGREDO de scripts/varredura_segredo.sh -- a MESMA régua do
    P-1 e do sanitizar.py. Três consumidores, uma fonte: padrão novo passa a
    valer aqui de graça, e não há régua paralela para apodrecer.

    FALHA FECHADA: sem conseguir ler os padrões, este serviço não responde.
    Devolver saída não-redigida "porque a régua não carregou" seria abrir
    exatamente o vazamento que a redação existe para fechar.
    """
    sh = REPO / "scripts" / "varredura_segredo.sh"
    r = subprocess.run(
        ["bash", "-c", f'source "$1"; printf "%s\\n" "${{PADROES_SEGREDO[@]}}"', "_", str(sh)],
        capture_output=True, text=True, timeout=30,
    )
    linhas = [x for x in r.stdout.splitlines() if x.strip()]
    if r.returncode != 0 or not linhas:
        raise RuntimeError(f"não consegui ler PADROES_SEGREDO de {sh}")
    return linhas


_RX: list[re.Pattern] | None = None


def _redigir(texto: str) -> tuple[str, int]:
    """Troca cada trecho que casa a régua por marcador. Devolve (texto, n)."""
    global _RX
    if _RX is None:
        traduz = {"[[:space:]]": r"\s", "[[:alnum:]]": r"[A-Za-z0-9]",
                  "[[:digit:]]": r"\d", "[[:alpha:]]": r"[A-Za-z]"}
        compilados = []
        for p in _padroes():
            for posix, py in traduz.items():
                p = p.replace(posix, py)
            try:
                compilados.append(re.compile(p))
            except re.error:
                # Padrão que não traduz não pode virar silêncio: falha fechada.
                raise RuntimeError(f"padrão não compilável na régua: {p!r}")
        _RX = compilados
    n = 0
    for rx in _RX:
        texto, k = rx.subn("[SEGREDO REDIGIDO]", texto)
        n += k
    return texto, n


# --- leitura: o SENTIDO da saída, calculado, não deixado pro modelo adivinhar --
# Achado real, MEMÓRIAS (524)/(525): a Seth recebeu "0 loaded units listed" do
# `servicos` e concluiu "falta de unidades ativas" -- o contrário do fato (zero
# unidades em FALHA = saudável). A descrição dizia "Vazio é bom", mas nunca
# viajava junto com a saída. Aqui: só leitura que dá pra CALCULAR da saída (ou
# de um fato fixo da Máquina), nunca opinião. Sem leitura segura -> None, e o
# modelo fica com a saída + a descrição.
def _leitura(nome: str, texto: str, codigo: int, head_local: str | None = None) -> str | None:
    if nome == "servicos":
        m = re.search(r"(\d+) loaded units? listed", texto)
        if m is None:
            return None
        k = int(m.group(1))
        return ("nenhuma unidade de usuário em falha -- saudável."
                if k == 0 else f"{k} unidade(s) de usuário em FALHA -- listadas abaixo.")
    if nome == "git_status":
        linhas = [x for x in texto.splitlines() if x.strip()]
        ramo = next((x for x in linhas if x.startswith("## ")), None)
        arquivos = [x for x in linhas if not x.startswith("## ")]
        partes = [("árvore limpa (nada modificado nem staged)" if not arquivos
                   else f"{len(arquivos)} arquivo(s) modificado(s)/staged/novo(s)")]
        if ramo:
            ad = re.search(r"ahead (\d+)", ramo); at = re.search(r"behind (\d+)", ramo)
            if ad or at:
                partes.append(f"{ad.group(1) if ad else 0} commit(s) à frente e "
                              f"{at.group(1) if at else 0} atrás do remoto rastreado")
            elif "..." in ramo:
                partes.append("em dia com o remoto rastreado (na última busca local; "
                              "pra medir o remoto AGORA use git_sync)")
        return "; ".join(partes) + "."
    if nome == "git_diff_stat":
        return ("nada difere de HEAD -- a árvore de trabalho é igual ao último commit."
                if not texto.strip() else "há diferença em relação a HEAD -- arquivos listados abaixo.")
    if nome == "git_sync":
        m = re.search(r"\b([0-9a-f]{40})\s+refs/heads/main\b", texto)
        if m is None:
            # Achado na varredura tripla (527): com a rede instável o remoto não
            # respondeu, a saída veio vazia com exit=0 e NENHUMA leitura --
            # silêncio que um modelo pode ler como "tudo certo".
            return (f"o remoto NÃO respondeu com o SHA de main (exit={codigo}) -- "
                    f"sync NÃO verificado. Isto é `lacuna`, não 'sincronizado'.")
        if not head_local:
            return None
        remoto = m.group(1)
        return (f"remoto = HEAD local ({remoto[:7]}) -- sincronizado." if remoto == head_local
                else f"DIFERENTE: HEAD local {head_local[:7]}, remoto {remoto[:7]} -- "
                     f"a cópia local não é o canon publicado.")
    if nome == "perimetro":
        m = re.search(r"^=== RESULTADO GERAL: .*$", texto, re.M)
        return m.group(0).strip("= ").strip() if m else None
    if nome in ("selos", "suite_controles"):
        return ("exit=0 -- passou." if codigo == 0
                else f"exit={codigo} -- FALHOU; o motivo está na saída abaixo.")
    return None


def _executar(nome: str, n: int | None) -> str:
    argv = _argv(nome, n)
    _, timeout, _desc = COMANDOS[nome]
    try:
        r = subprocess.run(argv, cwd=str(REPO), capture_output=True, text=True,
                           timeout=timeout, shell=False)
        bruto = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr.strip() else "")
        codigo = r.returncode
    except subprocess.TimeoutExpired:
        return (f"$ {nome}\n[ERRO] estourou o timeout de {timeout}s -- nada a afirmar "
                f"sobre o resultado. Isto é `lacuna`, não 'passou'.")
    except OSError as e:
        return f"$ {nome}\n[ERRO] não consegui executar: {e}"

    texto, redigidos = _redigir(bruto)
    total_linhas = texto.count("\n") + 1 if texto else 0
    head_local = None
    if nome == "git_sync":
        try:
            head_local = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO),
                                        capture_output=True, text=True, timeout=10,
                                        shell=False).stdout.strip() or None
        except (subprocess.TimeoutExpired, OSError):
            head_local = None
    cabeca = [f"$ {nome}  (exit={codigo})", f"[o que é: {_desc}]"]
    leitura = _leitura(nome, texto, codigo, head_local)
    if leitura:
        cabeca.append(f"[leitura: {leitura}]")
    if redigidos:
        cabeca.append(f"[{redigidos} trecho(s) redigido(s) pela régua de segredo]")
    if len(texto) > TETO_CHARS:
        cortado = texto[:TETO_CHARS]
        linhas_mostradas = cortado.count("\n") + 1
        cabeca.append(
            f"[CORTADO em {TETO_CHARS} chars — mostrando {linhas_mostradas} de "
            f"{total_linhas} linhas. O total está aqui de propósito: com ele "
            f"você SABE o que ficou de fora, e não precisa declarar "
            f"`lacuna: leitura parcial` às cegas.]")
        texto = cortado
    else:
        cabeca.append(f"[{total_linhas} linha(s), completo]")
    return "\n".join(cabeca) + "\n\n" + texto


class _H(BaseHTTPRequestHandler):
    server_version = "seth_verificador/1.0"

    def log_message(self, *a):  # silencioso; o journal do systemd basta
        pass

    def _resp(self, codigo: int, obj: dict):
        corpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path.rstrip("/") in ("", "/comandos"):
            return self._resp(200, {"comandos": {k: v[2] for k, v in COMANDOS.items()}})
        self._resp(404, {"erro": "só GET /comandos e POST /verificar"})

    # Só GET e POST existem. PUT/PATCH/DELETE nem são definidos -> 501 do
    # BaseHTTPRequestHandler. Este canal não escreve, por construção.
    def do_POST(self):
        if self.path.rstrip("/") != "/verificar":
            return self._resp(404, {"erro": "rota desconhecida; use POST /verificar"})
        try:
            tam = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._resp(400, {"erro": "Content-Length inválido"})
        if tam > CORPO_MAX:
            return self._resp(413, {"erro": f"corpo acima de {CORPO_MAX} bytes"})
        try:
            pedido = json.loads(self.rfile.read(tam) or b"{}")
        except ValueError:
            return self._resp(400, {"erro": "corpo não é JSON"})
        if not isinstance(pedido, dict):
            return self._resp(400, {"erro": "corpo tem de ser objeto JSON"})

        nome = pedido.get("comando")
        if nome not in COMANDOS:
            return self._resp(400, {
                "erro": f"comando '{nome}' não está na lista fechada",
                "disponiveis": sorted(COMANDOS),
                "nota": "Este canal não executa comando livre, por desenho. "
                        "Se falta uma verificação, ela entra na lista por proposta "
                        "assinada (P-8), não por parâmetro.",
            })
        try:
            texto = _executar(nome, pedido.get("n"))
        except ValueError as e:
            return self._resp(400, {"erro": str(e)})
        except RuntimeError as e:
            return self._resp(503, {"erro": f"falha fechada: {e}"})
        self._resp(200, {"comando": nome, "saida": texto})


def _selftest() -> int:
    casos, ok = [], 0
    # 1. comando fora da lista não vira argv
    try:
        _argv("rm -rf /", None); casos.append(("comando livre recusado", False))
    except KeyError:
        casos.append(("comando livre recusado", True))
    # 2. n fora da faixa
    for mau in (0, 51, "5; rm -rf /", 3.5, True):
        try:
            _argv("git_log", mau); casos.append((f"n={mau!r} recusado", False))
        except (ValueError, TypeError):
            casos.append((f"n={mau!r} recusado", True))
    # 3. n válido entra como inteiro
    casos.append(("git_log n=5 -> argv", _argv("git_log", 5)[-1] == "5"))
    # 4. comando que não aceita n recusa n
    try:
        _argv("perimetro", 3); casos.append(("perimetro recusa n", False))
    except ValueError:
        casos.append(("perimetro recusa n", True))
    # 5. redação: a régua pega chave montada em pedaços (literal não existe aqui)
    chave = "".join(["sk", "-", "A" * 40])
    red, n = _redigir(f"vazou {chave} aqui")
    casos.append(("segredo redigido", n >= 1 and chave not in red))
    # 6. texto inocente não é tocado
    _, n2 = _redigir("commit dc19621 sha256 8783d29d ok")
    casos.append(("texto limpo intacto", n2 == 0))
    # 7. nenhum argv contém shell
    casos.append(("nenhum argv usa shell",
                  all(a[0] not in ("sh", "-c") and "sh -c" not in " ".join(a)
                      for a, _t, _d in COMANDOS.values())))
    # 8. leitura calculada (MEMÓRIAS (525)) -- o caso real que a Seth leu ao contrário
    vazio = "UNIT LOAD ACTIVE SUB DESCRIPTION\n\n0 loaded units listed.\n"
    casos.append(("servicos 0 -> saudável", "saudável" in (_leitura("servicos", vazio, 0) or "")))
    casos.append(("servicos 2 -> FALHA",
                  "2 unidade(s)" in (_leitura("servicos", "x.service loaded failed failed x\n\n2 loaded units listed.", 0) or "")))
    casos.append(("git_status limpo", "árvore limpa" in (_leitura("git_status", "## main...origin/main\n", 0) or "")))
    casos.append(("git_status sujo+ahead",
                  (lambda r: "1 arquivo" in r and "2 commit(s) à frente" in r)(
                      _leitura("git_status", "## main...origin/main [ahead 2]\n M REGRAS.md\n", 0) or "")))
    casos.append(("git_diff_stat vazio", "nada difere" in (_leitura("git_diff_stat", "", 0) or "")))
    sha = "a" * 40
    casos.append(("git_sync igual", "sincronizado" in (_leitura("git_sync", f"{sha}\trefs/heads/main\n", 0, sha) or "")))
    casos.append(("git_sync diferente", "DIFERENTE" in (_leitura("git_sync", f"{sha}\trefs/heads/main\n", 0, "b" * 40) or "")))
    casos.append(("git_sync sem HEAD local -> sem leitura", _leitura("git_sync", f"{sha}\trefs/heads/main", 0, None) is None))
    casos.append(("git_sync remoto mudo -> lacuna", "NÃO verificado" in (_leitura("git_sync", "", 0, sha) or "")))
    casos.append(("git_sync erro de rede -> lacuna", "exit=128" in (_leitura("git_sync", "fatal: unable to access", 128, sha) or "")))
    casos.append(("perimetro repete RESULTADO",
                  "OK -- 16 OK" in (_leitura("perimetro", "x\n=== RESULTADO GERAL: OK -- 16 OK · 0 FALHA ===\n", 0) or "")))
    casos.append(("selos exit!=0 -> FALHOU", "FALHOU" in (_leitura("selos", "", 1) or "")))
    casos.append(("estado sem leitura inventada", _leitura("estado", "HEAD: x", 0) is None))
    for nome, passou in casos:
        print(("PASS  " if passou else "FALHA ") + nome)
        ok += 1 if passou else 0
    print(f"\nSELFTEST {'OK' if ok == len(casos) else 'FALHOU'} -- {ok}/{len(casos)}")
    return 0 if ok == len(casos) else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return _selftest()
    host, porta = BIND.split(":")
    srv = ServidorConcorrenciaLimitada((host, int(porta)), _H)
    print(f"seth_verificador em {BIND} — read-only, {len(COMANDOS)} comandos na lista fechada",
          flush=True)
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
