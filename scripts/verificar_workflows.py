#!/usr/bin/env python3
"""verificar_workflows.py [--raiz DIR | --diff ARQ.diff | --selftest]

Confere os workflows do GitHub (.github/workflows/*.yml e *.yaml) e falha no que o GitHub recusa:
  - YAML com erro de sintaxe, vazio, ou cuja raiz não é um mapeamento;
  - chave repetida em qualquer mapeamento, em qualquer nível. O PyYAML não reclama: a última vence
    em silêncio, e a primeira some.

Por que existe (12/11/2026): c4c71956 acrescentou um segundo `env:` no passo "Fiscalizar" de
fiscal-p8.yml. O GitHub recusou o arquivo inteiro ("workflow file issue"): o check obrigatório
fiscal-p8 deixou de rodar e todo PR ficou BLOCKED. Pelo PyYAML, o BASE_SHA e o HEAD_SHA do passo
também se perderiam (a última chave, GH_TOKEN, vence).

Modos:
  (sem argumento) ou --raiz DIR   confere DIR/.github/workflows (padrão: raiz do repositório).
  --diff ARQ.diff                 confere o que o .diff produz sobre HEAD, só nos caminhos
                                  .github/workflows/ que ele toca. Sem esses caminhos, passa sem ler
                                  o resto. Usado por p8_verificar.sh e aprovar.sh, antes de assinar.
  --selftest                      casos com o arquivo quebrado (positivo) e corrigido (negativo).
Exit 0 = ok; 1 = falha (diz onde); 2 = uso errado.
Dependência: PyYAML (já usado por scripts/testar_dados_externos.py). Sem PyYAML, falha fechada.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # sem leitor de YAML não há verificação: falha fechada, nunca passa calado
    yaml = None

RAIZ = Path(__file__).resolve().parents[1]
WF = ".github/workflows"
_CABECALHO_WF = re.compile(r"^(?:\+\+\+ b/|--- a/)\.github/workflows/", re.M)


def achados_yaml(texto, origem):
    """Falhas de um workflow em texto. Lista vazia = válido."""
    try:
        raiz = yaml.compose(texto, Loader=yaml.SafeLoader)
    except yaml.YAMLError as e:
        marca = getattr(e, "problem_mark", None)
        onde = f", linha {marca.line + 1}" if marca is not None else ""
        return [f"{origem}: YAML inválido{onde}: {getattr(e, 'problem', None) or e}"]
    if raiz is None:
        return [f"{origem}: arquivo vazio"]
    if not isinstance(raiz, yaml.MappingNode):
        return [f"{origem}: a raiz do YAML não é um mapeamento"]
    achados, vistos = [], set()
    pilha = [(raiz, "")]
    while pilha:
        no, caminho = pilha.pop()
        if id(no) in vistos:  # âncora/alias: o mesmo nó é conferido uma vez só
            continue
        vistos.add(id(no))
        if isinstance(no, yaml.MappingNode):
            linhas = {}
            for chave, valor in no.value:
                if isinstance(chave, yaml.ScalarNode):
                    nome, linha = chave.value, chave.start_mark.line + 1
                    if nome in linhas:
                        achados.append(
                            f"{origem}: chave '{nome}' repetida em '{caminho or 'raiz'}' "
                            f"(linhas {linhas[nome]} e {linha}); o GitHub recusa o arquivo inteiro")
                    else:
                        linhas[nome] = linha
                    pilha.append((valor, f"{caminho}.{nome}" if caminho else nome))
                else:
                    pilha.append((chave, caminho))
                    pilha.append((valor, caminho))
        elif isinstance(no, yaml.SequenceNode):
            pilha.extend((item, f"{caminho}[{i}]") for i, item in enumerate(no.value))
    return achados


def conferir_raiz(raiz):
    """(quantos arquivos, falhas) de DIR/.github/workflows."""
    pasta = Path(raiz) / WF
    arquivos = sorted([*pasta.glob("*.yml"), *pasta.glob("*.yaml")]) if pasta.is_dir() else []
    falhas = []
    for arq in arquivos:
        rel = f"{WF}/{arq.name}"
        try:
            texto = arq.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            falhas.append(f"{rel}: não lido ({e})")
            continue
        falhas.extend(achados_yaml(texto, rel))
    return len(arquivos), falhas


def diff_toca_workflows(texto):
    return bool(_CABECALHO_WF.search(texto))


def conferir_diff(diff_path):
    """Confere o que o .diff produz sobre HEAD, só nos workflows. Devolve (ok, mensagem)."""
    texto = Path(diff_path).read_text(encoding="utf-8")
    if not diff_toca_workflows(texto):
        return True, "o .diff não toca .github/workflows"
    absoluto = Path(diff_path).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        ls = subprocess.run(["git", "ls-tree", "-r", "-z", "--name-only", "HEAD", "--", WF],
                            cwd=RAIZ, capture_output=True)
        if ls.returncode != 0:
            return False, "git ls-tree HEAD falhou: " + ls.stderr.decode(errors="replace").strip()
        for caminho in filter(None, ls.stdout.decode().split("\0")):
            conteudo = subprocess.run(["git", "show", f"HEAD:{caminho}"], cwd=RAIZ,
                                      capture_output=True, check=True).stdout
            destino = Path(tmp) / caminho
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(conteudo)
        ap = subprocess.run(["git", "apply", f"--include={WF}/*", str(absoluto)],
                            cwd=tmp, capture_output=True, text=True)
        if ap.returncode != 0:
            return False, ("o .diff não aplica sobre HEAD nos workflows (cópia desatualizada?): "
                           + ap.stderr.strip()[:300])
        n, falhas = conferir_raiz(tmp)
    if falhas:
        return False, "; ".join(falhas)
    return True, f"workflows do resultado: {n} arquivo(s), YAML válido e sem chave repetida"


# --- selftest -------------------------------------------------------------------------------
# Trecho do fiscal-p8.yml como estava no main depois de c4c71956 (PR #982): dois `env:` no mesmo passo.
_ENV_ERRADO = """        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        env:
          GH_TOKEN: ${{ github.token }}
"""
_ENV_CERTO = """        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
          GH_TOKEN: ${{ github.token }}
"""
_FISCAL_QUEBRADO = """name: Fiscal P-8 (PR, raiz de confiança anterior)

on:
  pull_request_target:
    branches: [main]

permissions:
  contents: read
  pull-requests: read

jobs:
  fiscal-p8:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout da BASE (única fonte de código confiável)
        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
        with:
          ref: ${{ github.event.pull_request.base.sha }}
          fetch-depth: 0
          persist-credentials: false

      - name: Traz o head só como objetos do git (nunca checkout)
        env:
          PR: ${{ github.event.pull_request.number }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          git fetch --no-tags origin "+refs/pull/${PR}/head:refs/remotes/pr/head"

      - name: Fiscalizar (par assinado, consumo integral, raiz da base)
""" + _ENV_ERRADO + """        run: bash scripts/p8_verificar_pr.sh "$BASE_SHA" "$HEAD_SHA"
"""
assert _ENV_ERRADO in _FISCAL_QUEBRADO
_FISCAL_CORRIGIDO = _FISCAL_QUEBRADO.replace(_ENV_ERRADO, _ENV_CERTO)


def _selftest():
    casos = [
        # (nome, texto, deve_falhar, trecho esperado na falha)
        ("fiscal-p8 atual, com dois env no passo", _FISCAL_QUEBRADO, True, "'env'"),
        ("fiscal-p8 com um env só (correção)", _FISCAL_CORRIGIDO, False, ""),
        ("YAML com erro de sintaxe", "jobs:\n  a:\n   steps: [\n", True, "YAML inválido"),
        ("chave repetida na raiz", "on: push\non: pull_request\njobs: {}\n", True, "'on'"),
        ("chave repetida dentro de item de lista",
         "jobs:\n  a:\n    steps:\n      - name: x\n        run: y\n        run: z\n", True, "'run'"),
        ("mesma chave em dois mapeamentos (válido)",
         "jobs:\n  a:\n    env: {A: 1}\n  b:\n    env: {A: 2}\n", False, ""),
        ("arquivo vazio", "", True, "vazio"),
        ("raiz é lista", "- a\n- b\n", True, "não é um mapeamento"),
    ]
    falhas = []
    for nome, texto, deve_falhar, esperado in casos:
        achados = achados_yaml(texto, "caso.yml")
        if bool(achados) != deve_falhar:
            falhas.append(f"{nome}: esperado {'falha' if deve_falhar else 'ok'}, veio {achados or 'ok'}")
        elif esperado and not any(esperado in a for a in achados):
            falhas.append(f"{nome}: falha sem o trecho '{esperado}': {achados}")
    cabecalhos = [
        ("--- a/.github/workflows/x.yml\n+++ b/.github/workflows/x.yml\n", True),
        ("--- /dev/null\n+++ b/.github/workflows/novo.yml\n", True),
        ("--- a/scripts/x.py\n+++ b/scripts/x.py\n", False),
    ]
    for texto, esperado in cabecalhos:
        if diff_toca_workflows(texto) != esperado:
            falhas.append(f"cabeçalho {texto.splitlines()[0]!r}: esperado {esperado}")
    if falhas:
        print("SELFTEST FALHOU:\n  " + "\n  ".join(falhas))
        return 1
    print(f"SELFTEST OK -- {len(casos) + len(cabecalhos)} casos")
    return 0


# --- principal ------------------------------------------------------------------------------
def main(argv):
    if yaml is None:
        print("FALHA: PyYAML ausente -- sem leitor de YAML não há verificação dos workflows (pip install pyyaml)",
              file=sys.stderr)
        return 1
    if argv == ["--selftest"]:
        return _selftest()
    if len(argv) == 2 and argv[0] == "--diff":
        ok, msg = conferir_diff(argv[1])
        print(msg if ok else f"FALHA: {msg}")
        return 0 if ok else 1
    if not argv or (len(argv) == 2 and argv[0] == "--raiz"):
        raiz = argv[1] if argv else RAIZ
        n, falhas = conferir_raiz(raiz)
        if falhas:
            print("FALHA: workflow do GitHub inválido -- o GitHub recusa o arquivo inteiro:")
            for f in falhas:
                print(f"  {f}")
            return 1
        print(f"OK: {n} workflow(s) em {WF}, YAML válido e sem chave repetida")
        return 0
    print(__doc__.split("\n\n")[0], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
