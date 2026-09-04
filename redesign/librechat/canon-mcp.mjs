#!/usr/bin/env node
// canon-mcp.mjs — servidor MCP (stdio, JSON-RPC newline-delimited) read-only
// sobre o vault do Agata. Bate no proxy read-only :27125 (obsidian-local-rest-api,
// que ja injeta o bearer e bloqueia escrita). Zero dependencias — so `fetch` do Node.
//
// Exposto a Seth pelo LibreChat: ~/librechat/librechat.yaml -> mcpServers.canon
//
// Tools:
//   query_canon      lê um doc de canon (REGRAS/PROJETO/MEMÓRIAS/...), com grep/linhas opcionais
//   vault_consultar  lê ou lista uma nota DERIVADA sob memoria/obsidian/
//
// Trava de acesso (alem do proxy ser read-only):
//   - whitelist: só os docs de canon nomeados + tudo sob memoria/obsidian/
//   - denylist de sufixos de segredo (.secret .token .pass .key .gpg .env .pem)
//   - sem "..", sem path absoluto
//
// Fonte versionada: ~/agata/redesign/librechat/canon-mcp.mjs

const PROXY = (process.env.CANON_PROXY || "http://127.0.0.1:27125").replace(/\/$/, "");
const MAX = 40000; // teto de chars por resposta, p/ nao estourar contexto

const CANON = {
  REGRAS: "REGRAS.md", PROJETO: "PROJETO.md",
  "MEMÓRIAS": "MEMÓRIAS.md", MEMORIAS: "MEMÓRIAS.md",
  ONDE_ESTAMOS: "ONDE_ESTAMOS.md", CHAVES: "CHAVES.md",
  PROJETO_REFERENCIA: "PROJETO_REFERENCIA.md", ROADMAP: "ROADMAP.md",
  PROMPT_CARREGAMENTO: "PROMPT_CARREGAMENTO.md",
  PROCEDIMENTO_LOGIN: "PROCEDIMENTO_LOGIN.md",
  INDICE_MEMORIAS: "INDICE_MEMORIAS.md",
  "INDICE_MEMORIAS_PALAVRAS-CHAVE": "INDICE_MEMORIAS_PALAVRAS-CHAVE.md",
};
const DENY = /\.(secret|token|pass|key|gpg|env|pem)$/i;

function pathOk(p) {
  if (!p || p.includes("..") || p.startsWith("/") || DENY.test(p)) return false;
  if (p.startsWith("memoria/obsidian/")) return true;
  return Object.values(CANON).includes(p);
}

async function vaultGet(rel) {
  if (!pathOk(rel)) throw new Error(`caminho fora da whitelist: ${rel}`);
  const url = `${PROXY}/vault/` + rel.split("/").map(encodeURIComponent).join("/");
  const r = await fetch(url, { headers: { Accept: "application/json, text/markdown, */*" } });
  if (r.status === 404) throw new Error(`não encontrado: ${rel}`);
  if (!r.ok) throw new Error(`:27125 GET /vault/${rel} -> HTTP ${r.status}`);
  const ct = r.headers.get("content-type") || "";
  return { ct, body: await r.text() };
}

function clamp(s, nota) {
  if (s.length <= MAX) return s;
  return s.slice(0, MAX) + `\n\n[...cortado em ${MAX} chars${nota ? " — " + nota : ""}]`;
}

// ---- query_canon -------------------------------------------------------------
async function queryCanon(a) {
  const key = String(a.doc || "").trim();
  const file = CANON[key] || (Object.values(CANON).includes(key) ? key : null);
  if (!file) throw new Error(`doc desconhecido: "${key}". Válidos: ${Object.keys(CANON).join(", ")}`);
  const { body } = await vaultGet(file);
  const linhas = body.split("\n");

  if (a.grep) {
    const re = new RegExp(a.grep, "i");
    const ctx = Math.max(0, Math.min(20, a.contexto ?? 3));
    const hits = [];
    linhas.forEach((ln, i) => { if (re.test(ln)) hits.push(i); });
    if (!hits.length) return `(${file}) sem linha casando /${a.grep}/i`;
    const want = new Set();
    hits.forEach((i) => { for (let j = i - ctx; j <= i + ctx; j++) if (j >= 0 && j < linhas.length) want.add(j); });
    const ordered = [...want].sort((x, y) => x - y);
    let out = `(${file}) — ${hits.length} trecho(s) casando /${a.grep}/i:\n`;
    let prev = -2;
    for (const i of ordered) {
      if (i !== prev + 1) out += "  --\n";
      out += `${String(i + 1).padStart(6)}  ${linhas[i]}\n`;
      prev = i;
    }
    return clamp(out, "refine o grep");
  }

  if (a.linhas) {
    const m = String(a.linhas).match(/^(\d+)\s*-\s*(\d+)$/);
    if (!m) throw new Error(`linhas deve ser "N-M", recebi "${a.linhas}"`);
    const [x, y] = [+m[1], +m[2]];
    const slice = linhas.slice(x - 1, y).map((ln, k) => `${String(x + k).padStart(6)}  ${ln}`).join("\n");
    return clamp(`(${file}) linhas ${x}-${y} de ${linhas.length}:\n${slice}`, "peça outro intervalo");
  }

  // sem grep/linhas: MEMÓRIAS é grande demais p/ despejar — devolve a janela do topo
  if (file === "MEMÓRIAS.md") {
    const mark = linhas.findIndex((l) => l.includes("ENTRADAS-NOVAS:AQUI"));
    const janela = linhas.slice(mark >= 0 ? mark : 0, (mark >= 0 ? mark : 0) + 220).join("\n");
    return clamp(
      `(MEMÓRIAS.md) tem ${linhas.length} linhas — grande p/ despejar inteiro.\n` +
      `Use { grep: "(293)" } ou { linhas: "1-120" } p/ um trecho. Janela do topo (a partir do marcador):\n\n` +
      janela, "use grep/linhas");
  }
  return clamp(`(${file}) — ${linhas.length} linhas:\n\n${body}`, "use grep/linhas");
}

// ---- vault_consultar -------------------------------------------------------
async function vaultConsultar(a) {
  let p = String(a.caminho || "").trim().replace(/^\/+/, "");
  if (p && !p.startsWith("memoria/obsidian/")) p = "memoria/obsidian/" + p;
  if (!p) p = "memoria/obsidian/";
  const { ct, body } = await vaultGet(p);
  if (ct.includes("application/json")) {
    try {
      const j = JSON.parse(body);
      if (Array.isArray(j.files)) return `${p} (diretório):\n` + j.files.map((f) => "  " + f).join("\n");
    } catch { /* cai no texto cru */ }
  }
  return clamp(`${p}:\n\n${body}`, "abra um arquivo específico");
}

const TOOLS = [
  {
    name: "query_canon",
    description:
      "Lê um documento do canon do Agata direto da fonte (REGRAS, PROJETO, MEMÓRIAS, " +
      "ONDE_ESTAMOS, CHAVES, PROJETO_REFERENCIA, ROADMAP, PROMPT_CARREGAMENTO, INDICE_MEMORIAS). " +
      "Use SEMPRE antes de afirmar qualquer coisa sobre regra, estado ou histórico — não confie na memória. " +
      "Sem grep/linhas devolve o doc inteiro (MEMÓRIAS só a janela do topo).",
    inputSchema: {
      type: "object",
      properties: {
        doc: { type: "string", description: "REGRAS | PROJETO | MEMÓRIAS | ONDE_ESTAMOS | CHAVES | PROJETO_REFERENCIA | ROADMAP | PROMPT_CARREGAMENTO | PROCEDIMENTO_LOGIN | INDICE_MEMORIAS" },
        grep: { type: "string", description: "regex (case-insensitive); devolve só os trechos casando com contexto" },
        contexto: { type: "number", description: "linhas de contexto ao redor de cada hit do grep (0–20, default 3)" },
        linhas: { type: "string", description: 'intervalo "N-M" (ex: "1-120")' },
      },
      required: ["doc"],
    },
  },
  {
    name: "vault_consultar",
    description:
      "Lê ou lista uma nota DERIVADA do vault Obsidian sob memoria/obsidian/ (estado, timeline, " +
      "moc-memoria, moc-regras, moc-projeto, moc-controles, entradas/, regras/, controles/, projeto/). " +
      "É o índice de consulta pontual: entrada antiga fora da janela, backlinks de uma regra, o que faz um script. " +
      "Passe caminho vazio p/ listar a raiz; um .md p/ ler.",
    inputSchema: {
      type: "object",
      properties: {
        caminho: { type: "string", description: 'relativo a memoria/obsidian/ (ex: "INICIO.md", "entradas/", "moc-regras.md"); vazio = listar a raiz' },
      },
    },
  },
];

async function callTool(name, args) {
  let text;
  if (name === "query_canon") text = await queryCanon(args);
  else if (name === "vault_consultar") text = await vaultConsultar(args);
  else throw new Error(`tool desconhecida: ${name}`);
  return { content: [{ type: "text", text }] };
}

// ---- loop JSON-RPC stdio --------------------------------------------------
function send(o) { process.stdout.write(JSON.stringify(o) + "\n"); }

async function handle(line) {
  let msg;
  try { msg = JSON.parse(line); } catch { return; }
  const { id, method, params } = msg;
  const notif = id === undefined || id === null;
  try {
    let result;
    if (method === "initialize") {
      result = {
        protocolVersion: (params && params.protocolVersion) || "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: "canon", version: "1.0.0" },
      };
    } else if (method === "tools/list") {
      result = { tools: TOOLS };
    } else if (method === "tools/call") {
      result = await callTool(params && params.name, (params && params.arguments) || {});
    } else if (method === "ping") {
      result = {};
    } else if (method && method.startsWith("notifications/")) {
      return; // notificação, sem resposta
    } else {
      if (!notif) send({ jsonrpc: "2.0", id, error: { code: -32601, message: `método não suportado: ${method}` } });
      return;
    }
    if (!notif) send({ jsonrpc: "2.0", id, result });
  } catch (e) {
    const message = (e && e.message) ? e.message : String(e);
    if (!notif) send({ jsonrpc: "2.0", id, error: { code: -32603, message } });
  }
}

let buf = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (d) => {
  buf += d;
  let i;
  while ((i = buf.indexOf("\n")) >= 0) {
    const line = buf.slice(0, i).trim();
    buf = buf.slice(i + 1);
    if (line) handle(line);
  }
});
// stdin fechou: NÃO force exit — deixa o event loop drenar (fetch em voo termina,
// aí o processo sai sozinho). Force-exit aqui truncaria uma tool/call em andamento.
process.stdin.on("end", () => {});
process.stderr.write("canon-mcp: pronto (proxy " + PROXY + ")\n");
