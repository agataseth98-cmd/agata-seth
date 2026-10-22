#!/usr/bin/env node
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const client = path.join(root, "redesign/librechat/canon-mcp.mjs");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "agata-escriba-client-"));
const tokenFile = path.join(tmp, "project.token");
const fakeToken = "fake-project-token-for-client-test-only-0123456789";
fs.writeFileSync(tokenFile, `${fakeToken}\n`, { mode: 0o600 });
let requests = 0;
const server = http.createServer((req, res) => {
  requests++;
  assert.equal(req.headers["x-agata-project-token"], fakeToken);
  assert.equal(req.headers.authorization, "Bearer fake-capability");
  req.resume();
  req.on("end", () => {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ bytes_add: 6, nota: "fixture" }));
  });
});

function call(tokenPath) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [client], {
      env: { ...process.env, SETH_ESCRIBA: `http://127.0.0.1:${server.address().port}`,
        AGATA_PROJECT_TOKEN_FILE: tokenPath },
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "", stderr = "";
    child.stdout.setEncoding("utf8").on("data", (v) => { stdout += v; });
    child.stderr.setEncoding("utf8").on("data", (v) => { stderr += v; });
    child.on("error", reject);
    child.on("close", (code) => {
      try {
        const line = stdout.trim().split("\n").at(-1);
        resolve({ code, response: JSON.parse(line), stderr });
      } catch (error) { reject(error); }
    });
    child.stdin.end(JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call",
      params: { name: "diario_anotar", arguments: { texto: "fixture", agata_capability: "fake-capability" } } }) + "\n");
  });
}

try {
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const good = await call(tokenFile);
  assert.equal(good.code, 0);
  assert.equal(good.response.result.content[0].text, "anotado (6 bytes). fixture");
  assert.equal(requests, 1);
  const absent = await call(path.join(tmp, "missing.token"));
  assert.equal(absent.code, 0);
  assert.match(absent.response.error.message, /token do projeto ausente ou inseguro/);
  assert.equal(requests, 1, "token ausente não pode abrir conexão com o Escriba");
  console.log("Escriba MCP project-token forwarding PASS (valid header; missing token fails closed)");
} finally {
  await new Promise((resolve) => server.close(resolve));
  fs.rmSync(tmp, { recursive: true, force: true });
}
