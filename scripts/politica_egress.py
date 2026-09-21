#!/usr/bin/env python3
"""Política de egress/anti-SSRF compartilhada -- fase A do plano de mitigação
da auditoria externa do Marcos (item 1; MEMÓRIAS (437)).

Consumida por dois lados hoje: `redesign/mcp/navegador/servidor.py` (Python,
import direto) e `scripts/ler_pagina.sh` (bash, via `--checar <url>` na CLI
deste arquivo).

Bloqueia por padrão: loopback, link-local (inclui o endereço clássico de
metadado de nuvem, 169.254.169.254 -- irrelevante nesta Máquina hoje, mas
sem custo bloquear), RFC1918, esquema fora de http/https. Resolve o DNS de
verdade e recheca o(s) IP(s) resultante(s) -- checar só o hostname da URL
não pega DNS rebinding nem redirecionamento público->privado.

Isto é política de CANAL (pra onde a requisição vai), não de conteúdo --
mesma família de defesa do `_schema_pede_titulo` de MEMÓRIAS (432)/(433):
dado externo não tem como forjar isto, porque não decide olhando o que a
página diz, decide olhando pra onde o socket abriria.

NÃO substitui a allowlist de domínio do navegador (clicar/preencher,
`~/.config/agata/navegador-dominios-permitidos.txt`) -- aquela é sobre QUEM
pode receber escrita; esta é sobre ONDE qualquer leitura pode alcançar.
"""
from __future__ import annotations

import ipaddress
import os
import socket
import subprocess
import sys
import urllib.parse

_ESQUEMAS_PERMITIDOS = ("http", "https")
_MAX_REDIRECTS = 10


def _ip_bloqueado(ip_str: str) -> str | None:
    """Motivo do bloqueio, ou None se o IP for público comum."""
    ip = ipaddress.ip_address(ip_str)
    if ip.is_loopback:
        return "loopback"
    if ip.is_link_local:
        return "link-local (inclui endereço de metadado de nuvem)"
    if ip.is_private:
        return "RFC1918 (rede privada)"
    if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return "endereço reservado/especial"
    return None


def destino_permitido(url: str) -> tuple[bool, str]:
    """(True, "") se a requisição pode sair; (False, motivo) senão.
    Resolve DNS de verdade -- nunca confia só no hostname escrito na URL."""
    try:
        partes = urllib.parse.urlsplit(url)
    except ValueError as e:
        return False, f"URL malformada: {e}"
    if partes.scheme not in _ESQUEMAS_PERMITIDOS:
        return False, f"esquema '{partes.scheme}' fora de {_ESQUEMAS_PERMITIDOS}"
    host = partes.hostname
    if not host:
        return False, "sem host na URL"
    try:
        enderecos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        return False, f"DNS não resolveu '{host}': {e}"
    ips = {info[4][0] for info in enderecos}
    if not ips:
        return False, f"DNS não devolveu endereço pra '{host}'"
    for ip_str in ips:
        motivo = _ip_bloqueado(ip_str)
        if motivo:
            return False, f"'{host}' resolve para {ip_str} ({motivo})"
    return True, ""


def buscar_seguro(
    url: str, destino: str, ua: str = "Mozilla/5.0", timeout_s: int = 20
) -> tuple[bool, int, str, str]:
    """Busca `url` salvando o corpo em `destino`, checando a política de
    egress a CADA salto de redirecionamento -- não só na URL inicial.

    Item 2 do plano de ação da auditoria do Marcos (MEMÓRIAS (500), NET-01):
    `curl -sSL` sozinho valida a URL uma vez e depois segue redirect por
    conta própria, sem re-checar; um destino público que redireciona pra
    loopback/RFC1918 (ou um TOCTOU de DNS entre a checagem e a conexão)
    passava batido. Aqui cada `Location` de 3xx é validado de novo, com o
    mesmo `destino_permitido()` -- inclusive resolvendo o DNS de novo, não
    reaproveitando o resultado do salto anterior.

    `curl -sS` (SEM -L) por salto -- é o próprio Python que decide se segue,
    não o curl. `--max-redirs` do curl não ajudaria aqui: ele conta saltos,
    não valida destino algum.

    Retorna (ok, status_http, url_final, motivo_se_bloqueado).
    """
    atual = url
    for _ in range(_MAX_REDIRECTS + 1):
        permitido, motivo = destino_permitido(atual)
        if not permitido:
            return False, 0, atual, motivo
        r = subprocess.run(
            [
                "curl", "-sS", "-A", ua, "--max-time", str(timeout_s),
                "-D", "-", "-o", destino, "-w", "%{http_code}", atual,
            ],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            return False, 0, atual, f"curl falhou (rc={r.returncode}): {r.stderr.strip()}"
        # curl -D - normaliza pra "\n\n" na saída (mesmo quando o servidor manda
        # "\r\n\r\n" na rede) -- achado testando de verdade, não suposto: o
        # rpartition original ("\r\n\r\n") nunca casava e o cabeçalho inteiro
        # caía no campo de status. Normaliza os dois jeitos antes de partir.
        cabecalho, _, corpo_status = r.stdout.replace("\r\n", "\n").rpartition("\n\n")
        status_str = corpo_status.strip() or r.stdout.strip()[-3:]
        try:
            status = int(status_str)
        except ValueError:
            return False, 0, atual, f"código HTTP ilegível na saída do curl: {status_str!r}"
        if status not in (301, 302, 303, 307, 308):
            return True, status, atual, ""
        localizacao = None
        for linha in cabecalho.splitlines():
            if linha.lower().startswith("location:"):
                localizacao = linha.split(":", 1)[1].strip()
        if not localizacao:
            return False, status, atual, f"redirect {status} sem cabeçalho Location"
        atual = urllib.parse.urljoin(atual, localizacao)
    return False, 0, atual, f"mais de {_MAX_REDIRECTS} redirecionamentos -- parado por segurança"


def _selftest_buscar_seguro() -> bool:
    """Testa `buscar_seguro` de ponta a ponta: segue redirect permitido,
    bloqueia redirect pra destino da lista de bloqueio -- com servidores
    HTTP descartáveis reais, não mock de rede. Os servidores de teste
    nascem em loopback (única forma viável sem depender de internet); por
    isso, só PRA ESTE TESTE, `destino_permitido` é trocado por uma versão
    que trata loopback como permitido -- a lógica de bloqueio em si (usada
    pro destino do REDIRECT, no 3º caso) continua sendo a função real,
    sem substituição, porque é justamente o que este teste verifica."""
    import http.server
    import threading

    global destino_permitido
    _original = destino_permitido

    def _permitir_loopback_para_teste(url: str) -> tuple[bool, str]:
        permitido, motivo = _original(url)
        if not permitido and "loopback" in motivo:
            return True, ""
        return permitido, motivo

    class _OK(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            corpo = b"conteudo de teste"
            self.send_response(200)
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

    def _porta_livre() -> int:
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        p = s.getsockname()[1]
        s.close()
        return p

    porta_ok = _porta_livre()
    srv_ok = http.server.HTTPServer(("127.0.0.1", porta_ok), _OK)
    threading.Thread(target=srv_ok.serve_forever, daemon=True).start()

    class _RedirectPermitido(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{porta_ok}/")
            self.end_headers()

    porta_redir_ok = _porta_livre()
    srv_redir_ok = http.server.HTTPServer(("127.0.0.1", porta_redir_ok), _RedirectPermitido)
    threading.Thread(target=srv_redir_ok.serve_forever, daemon=True).start()

    class _RedirectBloqueado(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", "http://169.254.169.254/latest/meta-data/")
            self.end_headers()

    porta_redir_ruim = _porta_livre()
    srv_redir_ruim = http.server.HTTPServer(("127.0.0.1", porta_redir_ruim), _RedirectBloqueado)
    threading.Thread(target=srv_redir_ruim.serve_forever, daemon=True).start()

    ok = True
    try:
        destino_permitido = _permitir_loopback_para_teste

        dest1 = "/tmp/_selftest_egress_1.html"
        ok1, status1, url1, _ = buscar_seguro(f"http://127.0.0.1:{porta_ok}/", dest1)
        cond1 = ok1 and status1 == 200 and open(dest1, "rb").read() == b"conteudo de teste"
        print(f"{'PASS' if cond1 else 'FALHA'}  busca direta, sem redirect (status={status1}, ok={ok1})")
        ok = ok and cond1

        dest2 = "/tmp/_selftest_egress_2.html"
        ok2, status2, url2, _ = buscar_seguro(f"http://127.0.0.1:{porta_redir_ok}/", dest2)
        cond2 = ok2 and status2 == 200 and url2 == f"http://127.0.0.1:{porta_ok}/"
        print(f"{'PASS' if cond2 else 'FALHA'}  segue 1 redirect pra destino permitido "
              f"(status={status2}, url_final={url2})")
        ok = ok and cond2

        ok3, status3, url3, motivo3 = buscar_seguro(f"http://127.0.0.1:{porta_redir_ruim}/",
                                                      "/tmp/_selftest_egress_3.html")
        cond3 = (not ok3) and "169.254.169.254" in url3 and "link-local" in motivo3
        print(f"{'PASS' if cond3 else 'FALHA'}  BLOQUEIA redirect pra destino da lista de bloqueio "
              f"(ok={ok3}, url_final={url3}, motivo={motivo3!r})")
        ok = ok and cond3
    finally:
        destino_permitido = _original
        srv_ok.shutdown()
        srv_redir_ok.shutdown()
        srv_redir_ruim.shutdown()
        for f in ("/tmp/_selftest_egress_1.html", "/tmp/_selftest_egress_2.html",
                  "/tmp/_selftest_egress_3.html"):
            try:
                os.remove(f)
            except OSError:
                pass
    return ok


def _selftest() -> int:
    casos = [
        ("http://127.0.0.1:20126/", False),
        ("http://localhost/", False),
        ("http://169.254.169.254/latest/meta-data/", False),
        ("http://192.168.1.1/", False),
        ("http://10.0.0.5/", False),
        ("ftp://example.com/", False),
        ("file:///etc/passwd", False),
        ("https://example.com/", True),
    ]
    ok = True
    for url, esperado in casos:
        permitido, motivo = destino_permitido(url)
        if permitido == esperado:
            print(f"PASS  {url} -> permitido={permitido} ({motivo or 'ok'})")
        else:
            print(f"FALHA {url} -> permitido={permitido}, esperado {esperado} ({motivo})")
            ok = False

    ok = _selftest_buscar_seguro() and ok

    print("\nSELFTEST OK" if ok else "\nSELFTEST FALHOU")
    return 0 if ok else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--selftest":
        sys.exit(_selftest())
    if a and a[0] == "--checar" and len(a) >= 2:
        permitido, motivo = destino_permitido(a[1])
        print("permitido" if permitido else f"bloqueado: {motivo}")
        sys.exit(0 if permitido else 1)
    if a and a[0] == "--buscar" and len(a) >= 3:
        ok, status, url_final, motivo = buscar_seguro(a[1], a[2])
        if ok:
            print(f"{status} {url_final}")
            sys.exit(0)
        print(f"bloqueado: {motivo} (parado em {url_final})", file=sys.stderr)
        sys.exit(1)
    print("uso: politica_egress.py --checar <url> | --buscar <url> <arquivo-destino> | --selftest",
          file=sys.stderr)
    sys.exit(2)
