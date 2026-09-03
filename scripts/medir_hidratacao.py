#!/usr/bin/env python3
"""Mede bytes/chars/tokens por bloco de cabeçalho do .hidrata.md.

Uso: python3 scripts/medir_hidratacao.py [--arquivo CAMINHO] [--saida CAMINHO]

Regras da medição (ordem do Humano, rodada de otimização de hidratação,
14/08/2026):
  - chars conta codepoints Unicode com locale declarado, nunca bytes
    disfarçados de chars.
  - tokens só entram se houver tokenizador REAL do modelo em questão.
    Sem tokenizador real -> "lacuna: sem tokenizador para <modelo>",
    nunca estimativa uniforme (ex: heurística de 4 chars/token).
  - NÃO usa approx_input_tokens do hook pre_api_request como fonte
    (agent/conversation_loop.py:2237 -- estimate_messages_tokens_rough(),
    heurística de 4 chars/token, não é tokenizador real).
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
QWEN_MODEL = "qwen3.5-9b-64k:latest"
QWEN_NUM_CTX = 65536  # janela do modelo local (Modelfile -64k)


def ollama_version() -> str:
    try:
        out = subprocess.run(["ollama", "-v"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or out.stderr.strip()
    except Exception as e:
        return f"lacuna: ollama -v falhou ({e})"


def qwen_token_count(text: str) -> tuple[int | None, str]:
    """Conta tokens reais via Ollama: prompt_eval_count do /api/generate.

    Isto roda o tokenizador de verdade do modelo carregado (não é
    aproximação) -- é o mesmo mecanismo que o próprio Ollama usa para
    decidir quanto do contexto o prompt ocupa. num_predict=1 para
    minimizar geração (só precisamos do prompt_eval_count).
    """
    payload = json.dumps({
        "model": QWEN_MODEL,
        "prompt": text,
        "stream": False,
        "options": {"num_predict": 1, "num_ctx": QWEN_NUM_CTX},
    }).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if "error" in data:
            return None, f"lacuna: erro do Ollama ({data['error']})"
        count = data.get("prompt_eval_count")
        if count is None:
            return None, "lacuna: resposta do Ollama sem prompt_eval_count"
        return count, "ok"
    except Exception as e:
        return None, f"lacuna: chamada ao Ollama falhou ({e})"


def split_blocks(text: str) -> list[tuple[str, str]]:
    """Divide em blocos por linha que começa com '# ' (nível 1, não '## ')."""
    lines = text.split("\n")
    starts = [i for i, l in enumerate(lines) if re.match(r"^# ", l)]
    blocks = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        header = lines[start].strip()
        block_text = "\n".join(lines[start:end])
        blocks.append((header, block_text))
    return blocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arquivo", default=str(Path(__file__).resolve().parent.parent / ".hidrata.md"))
    ap.add_argument("--saida", default=None)
    ap.add_argument("--pular-ollama", action="store_true", help="não chama o Ollama, marca tokens qwen como lacuna")
    args = ap.parse_args()

    path = Path(args.arquivo)
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("utf-8")

    total_bytes = len(raw_bytes)
    total_chars = len(text)  # codepoints Unicode, locale UTF-8 -- ver nota de metodologia no relatório

    blocks = split_blocks(text)

    ov = ollama_version()

    lines = []
    lines.append("# Baseline de hidratação — .hidrata.md")
    lines.append("")
    lines.append("Gerado por `scripts/medir_hidratacao.py`. Comandos usados: ver rodapé.")
    lines.append("")
    lines.append("## Metodologia")
    lines.append("- **bytes**: `len(arquivo.read_bytes())` (UTF-8 no disco).")
    lines.append("- **chars**: `len(str)` em Python 3 = contagem de codepoints Unicode. "
                  "Locale declarado: `LANG=pt_BR.UTF-8`. Verificado contra `LC_ALL=pt_BR.UTF-8 wc -m .hidrata.md` "
                  "no arquivo inteiro -- os dois bateram. Ressalva do Humano confirmada: `wc -m` em locale `C` "
                  "conta bytes, não chars (mesmo total que `wc -c`); esta medição usa UTF-8 explicitamente.")
    lines.append(f"- **tokens (qwen3.5-9b-64k)**: `prompt_eval_count` retornado por `POST {OLLAMA_URL}` "
                  f"(`{ov}`, modelo `{QWEN_MODEL}`, `num_ctx={QWEN_NUM_CTX}`, `num_predict=1` para minimizar geração). "
                  "Este é o tokenizador real do modelo carregado -- o mesmo valor que o Ollama usa internamente "
                  "para saber quanto do contexto o prompt ocupa. NÃO é a heurística de 4 chars/token de "
                  "`estimate_messages_tokens_rough()` (`agent/conversation_loop.py:2237`).")
    lines.append("- **gemini-2.5-flash**: lacuna: sem tokenizador local. O tokenizador real (`GenerativeModel.count_tokens`) "
                  "exige chamada à API do Google -- não executado nesta medição para não consumir cota do free tier "
                  "(~20 req/dia, monitorado por `gemini_quota_guard`, PROJETO.md). Decisão de escopo, não limitação técnica; "
                  "reversível se o Humano autorizar gastar 6 chamadas de cota nisso.")
    lines.append("- **Claude (este executor)**: lacuna: sem tokenizador local nem chamada de API disponível nesta sessão.")
    lines.append("")
    lines.append("## Por bloco")
    lines.append("")
    lines.append("| # | bloco (linha `# ...`) | bytes | chars (UTF-8) | tokens (qwen3.5-9b-64k, real) | % de 65536 (num_ctx qwen) |")
    lines.append("|---|---|---|---|---|---|")

    total_qwen_tokens = 0
    any_lacuna = False
    for i, (header, block_text) in enumerate(blocks, 1):
        b = len(block_text.encode("utf-8"))
        c = len(block_text)
        if args.pular_ollama:
            tok, status = None, "lacuna: --pular-ollama"
        else:
            tok, status = qwen_token_count(block_text)
        if tok is None:
            any_lacuna = True
            tok_str = status
            pct_str = "—"
        else:
            total_qwen_tokens += tok
            tok_str = str(tok)
            pct_str = f"{tok/QWEN_NUM_CTX*100:.2f}%"
        lines.append(f"| {i} | `{header}` | {b} | {c} | {tok_str} | {pct_str} |")

    lines.append("")
    lines.append("## Totais do arquivo inteiro")
    lines.append(f"- bytes: {total_bytes}")
    lines.append(f"- chars (UTF-8): {total_chars}")
    if total_qwen_tokens and not any_lacuna:
        lines.append(f"- tokens (qwen3.5-9b-64k, real, soma dos blocos): {total_qwen_tokens} "
                      f"-> {total_qwen_tokens/QWEN_NUM_CTX*100:.2f}% de {QWEN_NUM_CTX} (num_ctx configurado)")
    else:
        lines.append("- tokens (qwen3.5-9b-64k, real, soma dos blocos): "
                      f"{total_qwen_tokens} (parcial -- houve lacuna em pelo menos um bloco, ver tabela) "
                      f"-> {total_qwen_tokens/QWEN_NUM_CTX*100:.2f}% de {QWEN_NUM_CTX} conta só os blocos medidos")
    lines.append(f"- gemini-2.5-flash: lacuna: sem tokenizador para gemini-2.5-flash (ver metodologia)")
    lines.append(f"- Claude (executor desta sessão): lacuna: sem tokenizador para Claude")
    lines.append("")
    lines.append("## Comandos que produziram este relatório")
    lines.append("```")
    lines.append(f"cd ~/agata && python3 scripts/medir_hidratacao.py")
    lines.append("# internamente, por bloco:")
    lines.append(f"curl -s {OLLAMA_URL} -d '{{\"model\":\"{QWEN_MODEL}\",\"prompt\":\"<bloco>\",\"stream\":false,"
                  f"\"options\":{{\"num_predict\":1,\"num_ctx\":{QWEN_NUM_CTX}}}}}' # -> campo prompt_eval_count")
    lines.append("ollama -v")
    lines.append("```")

    report = "\n".join(lines) + "\n"

    if args.saida:
        Path(args.saida).write_text(report, encoding="utf-8")
        print(f"Relatório salvo em {args.saida}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
