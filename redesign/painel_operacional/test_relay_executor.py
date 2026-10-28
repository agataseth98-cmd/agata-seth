from __future__ import annotations

import sys
import types
import unittest
from unittest import mock

import relay_executor
import relay_catalog
from conselho_rede import PROVIDERS


class RelayExecutorTests(unittest.TestCase):
    def test_api_mapping_matches_council_allowlist_and_active_roster(self):
        root = __import__("pathlib").Path(__file__).resolve().parents[2]
        scripts = str(root / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        import conselho_remoto
        self.assertEqual(set(relay_executor.API_MODELS), set(PROVIDERS))
        self.assertEqual(set(relay_executor.API_MODELS.values()), set(conselho_remoto.ROSTER))

    def test_calls_only_mapped_active_model_with_system_context(self):
        response = {"choices": [{"message": {"content": "ok"}}]}
        remote = types.SimpleNamespace(
            ROSTER=list(relay_executor.API_MODELS.values()),
            enviar_omniroute=mock.Mock(return_value=response),
        )
        with mock.patch.dict(sys.modules, {"conselho_remoto": remote}):
            result = relay_executor.send("gemini", "prompt", "system")
        self.assertEqual(result, "ok")
        remote.enviar_omniroute.assert_called_once_with(
            "prompt", relay_executor.API_MODELS["gemini"], system_prompt="system"
        )

    def test_rejects_provider_without_official_mapping_before_call(self):
        with self.assertRaises(relay_executor.RelayAPIError):
            relay_executor.send("claude", "prompt", "system")

    def test_rejects_candidate_even_if_model_is_in_mapping(self):
        response = {"choices": [{"message": {"content": "should not call"}}]}
        remote = types.SimpleNamespace(
            ROSTER=list(relay_executor.API_MODELS.values()),
            enviar_omniroute=mock.Mock(return_value=response),
        )
        with mock.patch.dict(sys.modules, {"conselho_remoto": remote}), \
             mock.patch.dict(relay_catalog.PROVIDER_BY_ID, {"gemini": {
                 "id": "gemini", "access_mode": "official_api_only", "availability": "candidate"
             }}):
            with self.assertRaises(relay_executor.RelayAPIError):
                relay_executor.send("gemini", "prompt", "system")
        remote.enviar_omniroute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
