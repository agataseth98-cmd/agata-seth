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
import socket
import sys
import urllib.parse

_ESQUEMAS_PERMITIDOS = ("http", "https")


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
    print("uso: politica_egress.py --checar <url> | --selftest", file=sys.stderr)
    sys.exit(2)
