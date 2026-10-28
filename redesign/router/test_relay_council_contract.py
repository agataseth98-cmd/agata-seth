import unittest

from relay_council_contract import (
    CONTRACT_VERSION,
    RelayCouncilContractError,
    normalize_evaluation,
)


def valid(**changes):
    payload = {
        "task_id": "task-1",
        "provider": "gemini",
        "site": "gemini",
        "access_mode": "official_api",
        "state": "green",
        "ok": True,
        "text": "resposta formal",
        "latency_ms": 1234,
        "timestamp": "2026-10-28T10:00:00-03:00",
    }
    payload.update(changes)
    return payload


class RelayCouncilContractTests(unittest.TestCase):
    def test_normalizes_and_discards_unknown_fields(self):
        result = normalize_evaluation(valid(unknown_browser_field="discard"))
        self.assertEqual(result["contract"], CONTRACT_VERSION)
        self.assertEqual(result["provider"], "gemini")
        self.assertEqual(result["timestamp"], "2026-10-28T13:00:00+00:00")
        self.assertNotIn("unknown_browser_field", result)

    def test_allows_capacity_failure_without_response_text(self):
        result = normalize_evaluation(valid(
            state="provider_busy", ok=False, text=None,
            error="capacidade temporariamente indisponível",
        ))
        self.assertEqual(result["state"], "provider_busy")
        self.assertIsNone(result["text"])

    def test_rejects_inconsistent_green_state(self):
        with self.assertRaises(RelayCouncilContractError):
            normalize_evaluation(valid(ok=False, text=None, error="timeout"))

    def test_rejects_positive_result_without_text(self):
        with self.assertRaises(RelayCouncilContractError):
            normalize_evaluation(valid(text=" \n "))

    def test_rejects_sensitive_keys_in_snake_or_camel_case(self):
        for key in ("cookie", "sessionId", "apiKey", "auth-token"):
            with self.subTest(key=key), self.assertRaises(RelayCouncilContractError):
                normalize_evaluation(valid(**{key: "must not cross boundary"}))

    def test_rejects_naive_timestamp(self):
        with self.assertRaises(RelayCouncilContractError):
            normalize_evaluation(valid(timestamp="2026-10-28T10:00:00"))

    def test_rejects_non_finite_latency(self):
        for value in (float("nan"), float("inf"), -1, True):
            with self.subTest(value=value), self.assertRaises(RelayCouncilContractError):
                normalize_evaluation(valid(latency_ms=value))

    def test_rejects_oversized_fields(self):
        with self.assertRaises(RelayCouncilContractError):
            normalize_evaluation(valid(text="x" * 60_001))

    def test_rejects_dom_automation_and_unknown_providers(self):
        for changes in ({"access_mode": "browser_dom"}, {"provider": "perplexity"}):
            with self.subTest(changes=changes), self.assertRaises(RelayCouncilContractError):
                normalize_evaluation(valid(**changes))

    def test_requires_explicit_access_mode(self):
        payload = valid()
        payload.pop("access_mode")
        with self.assertRaises(RelayCouncilContractError):
            normalize_evaluation(payload)


if __name__ == "__main__":
    unittest.main()
