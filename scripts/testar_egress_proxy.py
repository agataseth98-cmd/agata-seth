"""Testes de rede offline para o SOCKS5 de egresso do navegador."""
import importlib.util
import socket
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ARQ = ROOT / "redesign/mcp/navegador/egress_proxy.py"
spec = importlib.util.spec_from_file_location("agata_egress_proxy", ARQ)
egress_proxy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = egress_proxy
spec.loader.exec_module(egress_proxy)


class EgressProxyTests(unittest.TestCase):
    def test_rejects_mixed_public_and_private_dns_answers(self):
        infos = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ]
        with patch.object(egress_proxy.socket, "getaddrinfo", return_value=infos), \
                patch.object(egress_proxy.socket, "create_connection") as connect:
            with self.assertRaises(PermissionError):
                egress_proxy._Servidor._connect("rebinding.example", 443)
            connect.assert_not_called()

    def test_rejects_shared_carrier_nat_address(self):
        infos = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("100.64.0.1", 443))]
        with patch.object(egress_proxy.socket, "getaddrinfo", return_value=infos), \
                patch.object(egress_proxy.socket, "create_connection") as connect:
            with self.assertRaises(PermissionError):
                egress_proxy._Servidor._connect("carrier-nat.example", 443)
            connect.assert_not_called()

    def test_connects_to_the_validated_literal_ip(self):
        infos = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]
        sentinel = object()
        with patch.object(egress_proxy.socket, "getaddrinfo", return_value=infos), \
                patch.object(egress_proxy.socket, "create_connection", return_value=sentinel) as connect:
            self.assertIs(egress_proxy._Servidor._connect("example.test", 443), sentinel)
            connect.assert_called_once_with(("1.1.1.1", 443), timeout=15)

    def test_proxy_tunnels_only_after_resolving_and_validating(self):
        echo = socket.socket()
        echo.bind(("127.0.0.1", 0))
        echo.listen(1)
        port = echo.getsockname()[1]

        def echo_once():
            conn, _ = echo.accept()
            with conn:
                conn.sendall(conn.recv(4))
            echo.close()

        thread = threading.Thread(target=echo_once, daemon=True)
        thread.start()
        server = egress_proxy._Servidor(("127.0.0.1", 0), egress_proxy._Handler)
        server.resolved_connect = lambda host, p: (
            self.assertEqual((host, p), ("allowed.example", port)),
            socket.create_connection(("127.0.0.1", port), timeout=2),
        )[1]
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        try:
            client = socket.create_connection(server.server_address, timeout=2)
            with client:
                client.sendall(b"\x05\x01\x00")
                self.assertEqual(client.recv(2), b"\x05\x00")
                host = b"allowed.example"
                client.sendall(b"\x05\x01\x00\x03" + bytes([len(host)]) + host + port.to_bytes(2, "big"))
                self.assertEqual(client.recv(10)[:2], b"\x05\x00")
                client.sendall(b"test")
                self.assertEqual(client.recv(4), b"test")
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=2)
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
