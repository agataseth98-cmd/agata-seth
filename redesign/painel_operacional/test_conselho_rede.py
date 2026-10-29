from __future__ import annotations

import json
import tempfile
import threading
import unittest
from unittest import mock
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import server
from conselho_rede import Council, Conflict, PROVIDERS, requests as parse_requests


class CouncilTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.executed = []
        self.council = Council(Path(self.temp.name), clean=lambda text: text,
                               execute=lambda tool, args, text: self.executed.append((tool, args, text)) or "mock-result")
        self.council.set_active_providers(list(PROVIDERS))

    def tearDown(self):
        self.council.db.close()
        self.temp.cleanup()

    def test_send_requires_approval_and_single_lease(self):
        action = self.council.create("send", {"site": "gemini", "text": "mock prompt"})
        self.assertEqual(self.council.claim(), [])
        row = self.council._row(action)
        self.council.decide(action, row["hash"], True)
        task, = self.council.claim()
        self.assertTrue(task["lease"])
        self.assertEqual(self.council.claim(), [])
        self.council.finish(action, {"ok": True, "text": "mock response"}, lease=task["lease"], site="gemini")
        self.assertEqual(self.council._row(action)["status"], "completed")

    def test_all_detected_browser_tabs_accept_mock_roundtrip(self):
        self.assertEqual(len(PROVIDERS), 9)
        for site in PROVIDERS:
            action = self.council.create("send", {"site": site, "text": "mock prompt"})
            row = self.council._row(action)
            self.council.decide(action, row["hash"], True)
            task, = self.council.claim()
            self.assertEqual(task["site"], site)
            self.council.finish(action, {"ok": True, "text": f"mock:{site}"}, lease=task["lease"], site=site)

    def test_each_tool_request_waits_for_human(self):
        action = self.council.create("send", {"site": "chatgpt", "text": "mock"})
        row = self.council._row(action)
        self.council.decide(action, row["hash"], True)
        task, = self.council.claim()
        self.council.finish(action, {"ok": True, "text": "\n<STATE/>\n"}, lease=task["lease"], site="chatgpt")
        pending, = [item for item in self.council.snapshot()["actions"] if item["kind"] == "tool"]
        self.assertEqual(pending["status"], "pending")
        self.assertEqual(self.executed, [])

    def test_rejected_tool_never_executes(self):
        action = self.council.create("tool", {"tool": "STATE", "args": {}, "text": ""})
        row = self.council._row(action)
        self.council.decide(action, row["hash"], False)
        self.assertEqual(self.executed, [])
        with self.assertRaises(Conflict):
            self.council.decide(action, row["hash"], True)

    def test_debate_and_synthesis_are_individually_approved(self):
        group = self.council.group("debate", "mock topic", ["chatgpt", "gemini", "zai"])
        initial = [item for item in self.council.snapshot()["actions"] if item["parent"] == group]
        initial.sort(key=lambda item: item["created"])
        self.assertEqual(len(initial), 3)
        for item in initial:
            self.council.decide(item["id"], item["hash"], True)
        for item in initial:
            task, = self.council.claim()
            self.assertEqual(task["id"], item["id"])
            self.council.finish(item["id"], {"ok": True, "text": "mock"}, lease=task["lease"], site=item["payload"]["site"])
        synthesis, = [item for item in self.council.snapshot()["actions"]
                      if item["parent"] == group and item["payload"]["phase"] == "synthesis"]
        self.assertEqual(synthesis["status"], "pending")
        self.assertEqual(self.council.claim(), [])

    def test_restart_does_not_replay_running_delivery(self):
        action = self.council.create("send", {"site": "gemini", "text": "mock"})
        row = self.council._row(action)
        self.council.decide(action, row["hash"], True)
        self.council.claim()
        self.council.db.close()
        restarted = Council(Path(self.temp.name), clean=lambda value: value, execute=lambda *_: "mock")
        restarted.set_active_providers(list(PROVIDERS))
        self.assertEqual(restarted._row(action)["status"], "unknown")
        self.assertEqual(restarted.claim(), [])
        restarted.db.close()

    def test_browser_result_requires_approved_lease_and_records_once(self):
        action = self.council.create("send", {"site": "gemini", "text": "mock"})
        row = self.council._row(action)
        with self.assertRaises(Conflict):
            self.council.finish_browser(action, "bad-lease", "gemini", {"ok": True, "text": "x"})
        self.council.decide(action, row["hash"], True)
        task, = self.council.claim()
        result = self.council.finish_browser(
            action, task["lease"], "gemini", {"ok": True, "text": "browser mock"}
        )
        self.assertEqual(result, {"duplicate": False})
        self.assertEqual(self.council._row(action)["status"], "completed")

    def test_browser_result_rejects_wrong_site_and_no_automatic_retry(self):
        action = self.council.create("send", {"site": "gemini", "text": "mock"})
        row = self.council._row(action)
        self.council.decide(action, row["hash"], True)
        task, = self.council.claim()
        with self.assertRaises(Conflict):
            self.council.finish_browser(action, task["lease"], "zai", {"ok": True, "text": "wrong"})
        result = self.council.finish_browser(action, task["lease"], "gemini",
                                             {"ok": False, "text": "", "error": "timeout"})
        row = self.council._row(action)
        self.assertEqual(result, {"duplicate": False})
        self.assertEqual(row["status"], "error")
        self.assertEqual(self.council.claim(), [])

    def test_closed_or_stale_tab_is_not_available(self):
        self.council.set_active_providers(["gemini"])
        action = self.council.create("send", {"site": "gemini", "text": "mock"})
        self.council.set_active_providers([])
        row = self.council._row(action)
        self.council.decide(action, row["hash"], True)
        self.assertEqual(self.council.claim(), [])
    def test_tool_requests_require_one_complete_xml_tag_per_line(self):
        parsed = parse_requests('before <STATE/> after\n<SEARCH canon="Agata"/>\n<DELIVER>review</DELIVER>')
        self.assertEqual([item["tool"] for item in parsed], ["SEARCH", "DELIVER"])

    def test_tool_request_parser_handles_repeated_delimiters_without_regex(self):
        self.assertEqual(parse_requests(">" * 60_000), [])
        self.assertEqual(parse_requests("x" * 60_001 + "\n<STATE/>"), [])

    def test_tool_request_parser_rejects_entity_expansion_and_unknown_entities(self):
        self.assertEqual(parse_requests('<SEARCH canon="&boom;"/>'), [])
        self.assertEqual(parse_requests('<SEARCH canon="safe"><!DOCTYPE x></SEARCH>'), [])
        parsed = parse_requests('<SEARCH canon="a&amp;b"/>')
        self.assertEqual(parsed[0]["args"], {"canon": "a&b"})


class CouncilHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = (server.PORT, server.ALLOWED_ORIGIN, server._COUNCIL,
                    server._COUNCIL_DATA_DIR, server._COUNCIL_LEGACY_HISTORY)
        self.httpd = ThreadingHTTPServer((server.BIND, 0), server.Handler)
        server.PORT = self.httpd.server_address[1]
        server.ALLOWED_ORIGIN = f"http://{server.BIND}:{server.PORT}"
        server._COUNCIL_DATA_DIR = Path(self.temp.name) / "db"
        server._COUNCIL_LEGACY_HISTORY = Path(self.temp.name) / "no-history.jsonl"
        server._COUNCIL = Council(server._COUNCIL_DATA_DIR, lambda value: value,
                                  lambda *_: "mock tool response", legacy=server._COUNCIL_LEGACY_HISTORY)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://{server.BIND}:{server.PORT}"

    def tearDown(self):
        self.httpd.shutdown()
        self.thread.join(timeout=2)
        self.httpd.server_close()
        server._COUNCIL.db.close()
        (server.PORT, server.ALLOWED_ORIGIN, server._COUNCIL,
         server._COUNCIL_DATA_DIR, server._COUNCIL_LEGACY_HISTORY) = self.old
        self.temp.cleanup()

    def request(self, path, payload=None, headers=None, method=None):
        data = None if payload is None else json.dumps(payload).encode()
        req = Request(self.base + path, data=data, headers=headers or {}, method=method)
        try:
            with urlopen(req, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            status, body = error.code, error.read().decode("utf-8")
            error.close()
            return status, body

    def test_browser_poll_and_result_require_human_approval_and_lease(self):
        status, state = self.request("/api/relay-council/state")
        self.assertEqual(status, 200)
        poll_headers = {"X-Relay-Client": server.RELAY_CLIENT_ID, "X-Relay-Providers": "gemini"}
        status, tasks = self.request("/api/relay-council/tasks", headers=poll_headers)
        self.assertEqual((status, tasks), (200, []))
        body = {"kind": "send", "payload": {"site": "gemini", "text": "mock"}, "csrf": state["csrf"]}
        status, _ = self.request("/api/relay-council/actions", body, {"Content-Type": "application/json"}, "POST")
        self.assertEqual(status, 403)
        headers = {"Content-Type": "application/json", "Origin": server.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin"}
        status, created = self.request("/api/relay-council/actions", body, headers, "POST")
        self.assertEqual(status, 201)
        extension_headers = poll_headers
        status, tasks = self.request("/api/relay-council/tasks", headers=extension_headers)
        self.assertEqual((status, tasks), (200, []))
        decision = {"id": created["id"], "hash": created["hash"], "approve": True, "csrf": state["csrf"]}
        status, _ = self.request("/api/relay-council/decision", decision, headers, "POST")
        self.assertEqual(status, 201)
        status, tasks = self.request("/api/relay-council/tasks", headers=extension_headers)
        task, = tasks
        self.assertEqual(status, 200)
        report = {"task_id": task["id"], "lease": task["lease"], "site": "gemini",
                  "ok": True, "text": "mock response", "error": ""}
        status, _ = self.request("/api/relay-council/result", report,
                                 {"Content-Type": "application/json", "X-Relay-Client": server.RELAY_CLIENT_ID}, "POST")
        self.assertEqual(status, 200)
        self.assertEqual(server._council_state()._row(task["id"])["status"], "completed")
        status, _ = self.request(
            "/api/relay-council/result", {"task_id": task["id"], "lease": task["lease"],
                                               "site": "gemini", "ok": True, "text": "different"},
            {"Content-Type": "application/json", "X-Relay-Client": server.RELAY_CLIENT_ID},
            "POST",
        )
        self.assertEqual(status, 409)
        self.assertEqual(self.request("/api/relay-council/execute", {},
                                      {"Content-Type": "application/json", "X-Relay-Client": server.RELAY_CLIENT_ID},
                                      "POST")[0], 405)


class ExtensionStabilityTests(unittest.TestCase):
    """F3: a extensão recarrega aba descarregada, limpa a caixa antes de escrever e não reenvia sem leitura."""

    def test_f3_guards_are_present_and_no_cookie_permission(self):
        base = Path(__file__).resolve().parent / "relay-extension-v2"
        background = (base / "background.js").read_text(encoding="utf-8")
        common = (base / "content" / "_common.js").read_text(encoding="utf-8")
        manifest = (base / "manifest.json").read_text(encoding="utf-8")
        self.assertIn("ensureTabLoaded", background)
        self.assertIn("chrome.tabs.reload", background)
        self.assertIn('sendSiteCmd(tabId, site, "clear")', background)
        self.assertIn("composer_nao_limpo", background)
        self.assertIn("sem_leitura", background)
        self.assertIn('case "clear"', common)
        self.assertNotIn('"cookies"', manifest)


class ExtensionContractTests(unittest.TestCase):
    def test_extension_is_scoped_to_open_chat_tabs_and_local_panel(self):
        directory = Path(__file__).resolve().parent / "relay-extension-v2"
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        background = (directory / "background.js").read_text(encoding="utf-8")
        popup = (directory / "popup/popup.html").read_text(encoding="utf-8")
        self.assertIn("http://127.0.0.1:20146/*", manifest["host_permissions"])
        self.assertNotIn("20147", json.dumps(manifest) + background + popup)
        self.assertIn("/api/relay-council/tasks", background)
        self.assertIn("/api/relay-council/result", background)
        self.assertIn("X-Relay-Providers", background)
        self.assertNotIn("chrome.tabs.create", background)
        self.assertNotIn("pinRelayTab", background)
        self.assertNotIn("cookies", json.dumps(manifest).lower())
        self.assertIn("Conselho em Rede", manifest["name"])
        self.assertIn("content_scripts", manifest)
        self.assertEqual(set(manifest["permissions"]), {"alarms", "scripting", "tabs"})
        self.assertEqual(len(PROVIDERS), 9)


if __name__ == "__main__":
    unittest.main()
