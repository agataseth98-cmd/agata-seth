import socket
import sys
import unittest
from pathlib import Path
from unittest import mock

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent.parent.parent / "scripts"))
import politica_egress  # noqa: E402


class UserinfoTests(unittest.TestCase):
    """Os dois primeiros casos param antes do DNS. O terceiro simula o DNS, para não usar rede."""

    def test_url_com_usuario_e_senha_e_recusada_antes_do_dns(self):
        with mock.patch("socket.getaddrinfo") as dns:
            _h, _p, _ips, motivo = politica_egress._resolver_destino("https://user:senha@exemplo.invalid/p")
        self.assertEqual(motivo, "URL com credenciais (userinfo) recusada")
        dns.assert_not_called()

    def test_url_so_com_usuario_tambem_e_recusada_antes_do_dns(self):
        with mock.patch("socket.getaddrinfo") as dns:
            _h, _p, _ips, motivo = politica_egress._resolver_destino("https://token@exemplo.invalid/")
        self.assertEqual(motivo, "URL com credenciais (userinfo) recusada")
        dns.assert_not_called()

    def test_url_sem_userinfo_segue_para_o_dns(self):
        with mock.patch("socket.getaddrinfo", side_effect=socket.gaierror("simulado")) as dns:
            _h, _p, _ips, motivo = politica_egress._resolver_destino("https://exemplo.invalid/p")
        dns.assert_called_once()
        self.assertIn("DNS não resolveu", motivo)


if __name__ == "__main__":
    unittest.main()
