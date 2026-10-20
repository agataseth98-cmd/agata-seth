"""SOCKS5 local de saída: resolve, valida e conecta ao mesmo IP validado."""
from __future__ import annotations

import ipaddress
import socket
import socketserver
import struct
import threading


def _enderecos_publicos(host: str, port: int) -> list[str]:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    ips = sorted({i[4][0].split("%", 1)[0] for i in infos})
    if not ips:
        raise OSError("DNS não devolveu endereços")
    for raw in ips:
        ip = ipaddress.ip_address(raw)
        if not ip.is_global:
            raise PermissionError(f"destino bloqueado: {raw}")
    return ips


def _ler(sock: socket.socket, n: int) -> bytes:
    partes = bytearray()
    while len(partes) < n:
        b = sock.recv(n - len(partes))
        if not b:
            raise ConnectionError("cliente encerrou SOCKS")
        partes.extend(b)
    return bytes(partes)


class _Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.resolved_connect = lambda host, port: self._connect(host, port)

    @staticmethod
    def _connect(host: str, port: int) -> socket.socket:
        # Revalida a cada conexão e conecta ao literal IP retornado, sem uma
        # segunda resolução pelo cliente TCP.
        ips = _enderecos_publicos(host, port)
        erro = None
        for ip in ips:
            try:
                return socket.create_connection((ip, port), timeout=15)
            except OSError as e:
                erro = e
        raise OSError(f"nenhum IP validado aceitou conexão: {erro}")


class _Handler(socketserver.BaseRequestHandler):
    def handle(self):
        cliente = self.request
        remoto = None
        try:
            versao, nmetodos = _ler(cliente, 2)
            metodos = _ler(cliente, nmetodos)
            if versao != 5 or 0 not in metodos:
                cliente.sendall(b"\x05\xff")
                return
            cliente.sendall(b"\x05\x00")
            versao, comando, _reservado, tipo = _ler(cliente, 4)
            if versao != 5 or comando != 1:
                self._responder(cliente, 7)
                return
            if tipo == 1:
                host = socket.inet_ntop(socket.AF_INET, _ler(cliente, 4))
            elif tipo == 4:
                host = socket.inet_ntop(socket.AF_INET6, _ler(cliente, 16))
            elif tipo == 3:
                n = _ler(cliente, 1)[0]
                host = _ler(cliente, n).decode("idna")
            else:
                self._responder(cliente, 8)
                return
            port = struct.unpack("!H", _ler(cliente, 2))[0]
            try:
                remoto = self.server.resolved_connect(host, port)
            except PermissionError:
                self._responder(cliente, 2)
                return
            except OSError:
                self._responder(cliente, 5)
                return
            self._responder(cliente, 0)
            self._relay(cliente, remoto)
        except (OSError, ConnectionError, UnicodeError, struct.error):
            return
        finally:
            if remoto is not None:
                remoto.close()

    @staticmethod
    def _responder(sock: socket.socket, status: int):
        sock.sendall(b"\x05" + bytes([status]) + b"\x00\x01\x00\x00\x00\x00\x00\x00")

    @staticmethod
    def _relay(a: socket.socket, b: socket.socket):
        while True:
            legiveis, _, _ = __import__("select").select([a, b], [], [], 30)
            if not legiveis:
                return
            for origem in legiveis:
                bloco = origem.recv(65536)
                if not bloco:
                    return
                (b if origem is a else a).sendall(bloco)


class EgressProxy:
    """Servidor SOCKS5 em loopback, gerido pelo ciclo de vida do navegador."""
    def __init__(self):
        self._server = _Servidor(("127.0.0.1", 0), _Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True,
                                        name="agata-egress-proxy")

    @property
    def url(self) -> str:
        host, port = self._server.server_address
        return f"socks5://{host}:{port}"

    def start(self) -> "EgressProxy":
        self._thread.start()
        return self

    def close(self):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)
