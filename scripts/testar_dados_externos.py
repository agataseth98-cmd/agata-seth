#!/usr/bin/env python3
"""Contraprovas da classificação pública no endpoint selecionável e no proxy."""
from pathlib import Path
import sys
import unittest
import socket
import re
import os
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from redesign.router.proxy import validar_egresso_publico  # noqa: E402
from scripts.politica_egress import destino_permitido  # noqa: E402
os.environ["SETH_REPO"] = str(ROOT)
from redesign.router.seth_gateway import _preparar_payload_publico  # noqa: E402


class DadosExternosTests(unittest.TestCase):
    def test_proxy_requires_public_classification_except_local_models(self):
        for payload, classification in (
            ({"model": "mistral/model", "messages": []}, None),
            ({"model": "mistral/model", "messages": []}, "private"),
            ({}, None),  # POST de outro endpoint, não só /chat/completions
            ("texto livre", None),  # qualquer Content-Type não estruturado
        ):
            with self.subTest(payload=payload, classification=classification):
                with self.assertRaises(PermissionError):
                    validar_egresso_publico(payload, classification)
        validar_egresso_publico({"model": "mistral/model"}, "public")
        validar_egresso_publico({"model": "ollama-local/qwen"}, None)

    def test_public_ui_route_is_a_dedicated_custom_endpoint(self):
        config = yaml.safe_load((ROOT / "redesign/librechat/librechat.yaml").read_text())
        spec = next(row for row in config["modelSpecs"]["list"] if row["name"] == "seth-public")
        self.assertEqual(spec["preset"]["endpoint"], "Seth Pública")
        self.assertEqual(spec["preset"]["model"], "seth-public")
        endpoint = next(row for row in config["endpoints"]["custom"]
                        if row["name"] == spec["preset"]["endpoint"])
        self.assertEqual(endpoint["headers"], {"X-Agata-Data-Classification": "public"})
        self.assertFalse(endpoint.get("titleConvo", True))
        self.assertIn("sem ferramentas", spec["label"])

    def test_destination_policy_blocks_non_global_carrier_nat_range(self):
        records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("100.64.0.1", 443))]
        with patch("scripts.politica_egress.socket.getaddrinfo", return_value=records):
            self.assertEqual(destino_permitido("https://carrier-nat.example"),
                             (False, "'carrier-nat.example' resolve para 100.64.0.1 (endereço não global ou reservado/especial)"))

    def test_p16_selects_security_implementations_and_their_tests(self):
        source = (ROOT / "scripts/perimetro.sh").read_text()
        match = re.search(r"^P16_ARQUIVOS_DE_CONTROLE='([^']+)'$", source, re.M)
        self.assertIsNotNone(match)
        selection = re.compile(match.group(1))
        for path in (
            "redesign/mcp/capability.py",
            "redesign/mcp/navegador/servidor.py",
            "redesign/mcp/navegador/egress_proxy.py",
            "redesign/router/proxy.py",
            "redesign/router/seth_gateway.py",
            "redesign/librechat/librechat.yaml",
            "scripts/politica_egress.py",
            "scripts/testar_capability.py",
            "scripts/testar_dados_externos.py",
            "scripts/testar_egress_proxy.py",
            "scripts/testar_net02_compose.py",
        ):
            with self.subTest(path=path):
                self.assertRegex(path, selection)

    def test_public_lane_drops_hidden_system_and_tool_context(self):
        payload = {
            "model": "seth-livre",
            "messages": [
                {"role": "system", "content": "private canon marker"},
                {"role": "user", "content": "pergunta pública"},
                {"role": "tool", "content": "private tool result"},
                {"role": "assistant", "content": "histórico visível"},
            ],
            "tools": [{"name": "memoria_acrescentar"}],
            "tool_choice": "required",
        }
        public = _preparar_payload_publico(payload)
        self.assertNotIn("private canon marker", str(public))
        self.assertNotIn("private tool result", str(public))
        self.assertNotIn("tools", public)
        self.assertNotIn("tool_choice", public)
        self.assertEqual([m["role"] for m in public["messages"]],
                         ["system", "user", "assistant"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
