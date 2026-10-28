import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "router"))
from relay_catalog import PROVIDERS, PROVIDER_BY_ID, snapshot
from relay_council_contract import ALLOWED_PROVIDERS


class RelayCatalogTests(unittest.TestCase):
    def test_roster_has_seventeen_unique_entries_and_no_perplexity(self):
        self.assertEqual(len(PROVIDERS), 17)
        self.assertEqual(len(PROVIDER_BY_ID), 17)
        self.assertEqual(len(snapshot()), 17)
        self.assertNotIn("perplexity", PROVIDER_BY_ID)

    def test_no_provider_is_enabled_for_dom_automation(self):
        self.assertTrue(all(p["access_mode"] != "dom_prototype" for p in PROVIDERS))
        self.assertTrue(all(p["access_mode"] in {"official_api_only", "manual_only"} for p in PROVIDERS))

    def test_candidates_are_not_marked_configured(self):
        in_roster = {p["id"] for p in PROVIDERS if p["availability"] == "in_roster"}
        self.assertEqual(in_roster, {"gemini", "zai", "mistral", "huggingchat", "openrouter"})
        self.assertTrue(all(p["availability"] in {"in_roster", "candidate"} for p in PROVIDERS))

    def test_policy_links_are_https_and_contract_roster_matches(self):
        self.assertTrue(all(
            p["policy_url"].startswith("https://")
            for p in PROVIDERS if "policy_url" in p
        ))
        self.assertEqual(set(PROVIDER_BY_ID), set(ALLOWED_PROVIDERS))


if __name__ == "__main__":
    unittest.main()
