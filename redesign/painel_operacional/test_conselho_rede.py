from __future__ import annotations

import json
import tempfile
import threading
import unittest
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

    def test_all_nine_adapters_accept_mock_roundtrip(self):
        self.assertEqual(len(PROVIDERS), 9)
        for site in PROVIDERS:
            action = self.council.create("send", {"site": site, "text": "mock prompt"})
            row = self.council._row(action)
            self.council.decide(action, row["hash"], True)
            task, = self.council.claim()
            self.assertEqual(task["site"], site)
            self.council.finish(action, {"ok": True, "text": f"mock:{site}"}, lease=task["lease"], site=site)

    def test_each_tool_request_waits_for_human(self):
        action = self.council.create("send", {"site": "deepseek", "text": "mock"})
        row = self.council._row(action)
        self.council.decide(action, row["hash"], True)
        task, = self.council.claim()
        self.council.finish(action, {"ok": True, "text": "\n<STATE/>\n"}, lease=task["lease"], site="deepseek")
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
        group = self.council.group("debate", "mock topic", ["deepseek", "gemini", "zai"])
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
        self.assertEqual(restarted._row(action)["status"], "unknown")
        self.assertEqual(restarted.claim(), [])
        restarted.db.close()

    def test_tool_requests_require_one_complete_xml_tag_per_line(self):
        parsed = parse_requests('before <STATE/> after\n<SEARCH canon="Agata"/>\n<DELIVER>review</DELIVER>')
        self.assertEqual([item["tool"] for item in parsed], ["SEARCH", "DELIVER"])

    def test_tool_request_parser_handles_repeated_delimiters_without_regex(self):
        self.assertEqual(parse_requests(">" * 60_000), [])
        self.assertEqual(parse_requests("x" * 60_001 + "\n<STATE/>"), [])


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

    def test_api_origin_csrf_approval_and_result_lease(self):
        status, state = self.request("/api/relay-council/state")
        self.assertEqual(status, 200)
        body = {"kind": "send", "payload": {"site": "gemini", "text": "mock"}, "csrf": state["csrf"]}
        status, _ = self.request("/api/relay-council/actions", body, {"Content-Type": "application/json"}, "POST")
        self.assertEqual(status, 403)
        headers = {"Content-Type": "application/json", "Origin": server.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin"}
        status, created = self.request("/api/relay-council/actions", body, headers, "POST")
        self.assertEqual(status, 201)
        status, tasks = self.request("/api/relay-council/tasks", headers={"X-Relay-Client": server.RELAY_CLIENT_ID})
        self.assertEqual((status, tasks), (200, []))
        decision = {"id": created["id"], "hash": created["hash"], "approve": True, "csrf": state["csrf"]}
        status, _ = self.request("/api/relay-council/decision", decision, headers, "POST")
        self.assertEqual(status, 201)
        status, tasks = self.request("/api/relay-council/tasks", headers={"X-Relay-Client": server.RELAY_CLIENT_ID})
        task, = tasks
        self.assertEqual(status, 200)
        report = {"task_id": task["id"], "site": task["site"], "lease": task["lease"], "ok": True, "text": "mock response"}
        status, _ = self.request("/api/relay-council/result", report,
                                 {"Content-Type": "application/json", "X-Relay-Client": server.RELAY_CLIENT_ID}, "POST")
        self.assertEqual(status, 200)


class ExtensionContractTests(unittest.TestCase):
    def test_extension_matches_official_panel_and_nine_adapters(self):
        directory = Path(__file__).resolve().parent / "relay-extension-v2"
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        background = (directory / "background.js").read_text(encoding="utf-8")
        popup = (directory / "popup/popup.html").read_text(encoding="utf-8")
        self.assertIn("http://127.0.0.1:20146/*", manifest["host_permissions"])
        self.assertNotIn("20147", json.dumps(manifest) + background + popup)
        self.assertIn("/api/relay-council/tasks", background)
        self.assertIn("/api/relay-council/result", background)
        self.assertIn("Conselho em Rede", manifest["name"])
        self.assertEqual(len(PROVIDERS), 9)


if __name__ == "__main__":
    unittest.main()
