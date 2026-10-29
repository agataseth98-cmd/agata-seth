import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "router"))
from relay_catalog import PROVIDERS, PROVIDER_BY_ID, snapshot
from relay_council_contract import ALLOWED_PROVIDERS


class RelayCatalogTests(unittest.TestCase):
    def test_roster_has_nine_unique_chat_tabs_and_no_perplexity(self):
        self.assertEqual(len(PROVIDERS), 9)
        self.assertEqual(len(PROVIDER_BY_ID), 9)
        self.assertEqual(len(snapshot()), 9)
        self.assertNotIn("perplexity", PROVIDER_BY_ID)

    def test_roster_is_explicitly_experimental_browser_tabs(self):
        self.assertTrue(all(p["access_mode"] == "browser_tab_only" for p in PROVIDERS))
        self.assertTrue(all(p["adapter_state"] == "experimental" for p in PROVIDERS))
        self.assertTrue(all(not p["tab_open"] for p in snapshot()))
        self.assertEqual({p["id"] for p in snapshot(["gemini"]) if p["tab_open"]}, {"gemini"})

    def test_contract_roster_matches_catalog(self):
        self.assertEqual(set(PROVIDER_BY_ID), set(ALLOWED_PROVIDERS))


if __name__ == "__main__":
    unittest.main()
