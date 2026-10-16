#!/usr/bin/env python3
"""inventario_componentes.py -- inventário de componentes EXTERNOS com versão e digest (Fase I, I1/I3). CANDIDATO.

O que existe espalhado e este script junta, sem criar um segundo manifesto de modelos:
  * `models/manifest.json` (9 modelos Ollama, de 02/09) segue como está: é a régua do P-12 (backup) e só a
    chave `modelos` é lida por ele. Este script acrescenta a chave NOVA `componentes_externos`; nunca toca `modelos`.
  * imagens Docker (digest ou só tag?), modelos do Ollama (digest da API), arquivos listados em
    `config/componentes-externos.txt` (sha256), Obsidian (Flatpak).

Só LEITURA do sistema: `docker inspect`, API local do Ollama, `sha256sum`, `flatpak info`. Não baixa nada, não
atualiza nada, não chama rede externa. Atualizar componente é decisão do Humano (PROJETO, "Decisor local").

Uso:
  scripts/inventario_componentes.py --gerar [--manifesto models/manifest.json] [--saida ARQ|-]   escreve a chave nova
  scripts/inventario_componentes.py --verificar [--profundo] [--estrito]                        compara disco x manifesto
  scripts/inventario_componentes.py --selftest
Saída de `--verificar`: linhas AVISO/OK. Exit 0 sempre, salvo `--estrito` (exit 1 se houver deriva).
Honestidade de método: tag de imagem NÃO é imutável (`pinada_por: tag`); só `@sha256:` é (`pinada_por: digest`).
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zoneinfo

TZ = zoneinfo.ZoneInfo("America/Sao_Paulo")
OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")


def _cmd(*a, timeout=30):
    try:
        p = subprocess.run(a, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def sha256_arquivo(caminho, bloco=1 << 20):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while True:
            b = f.read(bloco)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def imagens_docker():
    if not shutil.which("docker"):
        return None
    nomes = _cmd("docker", "ps", "-a", "--format", "{{.Names}}")
    if nomes is None:
        return None
    out = []
    for nome in sorted(nomes.splitlines()):
        j = _cmd("docker", "inspect", nome, "--format", "{{.Config.Image}}|{{.Image}}")
        if not j or "|" not in j:
            continue
        ref, imagem_id = j.split("|", 1)
        digs = _cmd("docker", "image", "inspect", imagem_id, "--format", "{{json .RepoDigests}}")
        try:
            repo_digests = json.loads(digs) if digs else []
        except ValueError:
            repo_digests = []
        out.append({"contêiner": nome, "imagem": ref, "id": imagem_id.removeprefix("sha256:")[:12],
                    "pinada_por": "digest" if "@sha256:" in ref else "tag",
                    "repo_digests": sorted(repo_digests)})
    return out


def modelos_ollama():
    try:
        with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=5) as r:
            dados = json.loads(r.read())
    except (OSError, ValueError):
        return None
    return sorted(({"nome": m["name"], "digest": m.get("digest", ""), "bytes": m.get("size")} for m in dados.get("models", [])),
                  key=lambda x: x["nome"])


def arquivos_listados(lista):
    """Globs (com ~) de config/componentes-externos.txt -> [{caminho, bytes, sha256?}]. Sem o arquivo: []."""
    if not os.path.exists(lista):
        return []
    out = []
    with open(lista, encoding="utf-8") as f:
        padroes = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    for pad in padroes:
        for c in sorted(glob.glob(os.path.expanduser(pad))):
            if os.path.isfile(c):
                out.append({"caminho": c.replace(os.path.expanduser("~"), "~", 1), "bytes": os.path.getsize(c)})
    return out


def flatpak_obsidian():
    j = _cmd("flatpak", "info", "md.obsidian.Obsidian") if shutil.which("flatpak") else None
    if not j:
        return None
    dados = {}
    for linha in j.splitlines():
        if ":" in linha:
            k, v = linha.split(":", 1)
            dados[k.strip()] = v.strip()
    return {"versão": dados.get("Version"), "commit": (dados.get("Commit") or "")[:12], "origem": dados.get("Origin")}


def gerar(lista_arquivos, com_hash=True):
    arqs = arquivos_listados(lista_arquivos)
    if com_hash:
        for a in arqs:
            a["sha256"] = sha256_arquivo(os.path.expanduser(a["caminho"]))
    return {
        "gerado_em": datetime.datetime.now(TZ).isoformat(timespec="seconds"),
        "gerador": "scripts/inventario_componentes.py (candidato 16/10/2026)",
        "regra": "atualizar componente externo é decisão do Humano; nada `latest`; tag de imagem não é imutável",
        "imagens_docker": imagens_docker(), "modelos_ollama": modelos_ollama(),
        "arquivos": arqs, "obsidian_flatpak": flatpak_obsidian(),
    }


def comparar(manifesto, atual, profundo=False):
    """Lista de avisos: deriva entre o que o manifesto registra e o que o disco mostra agora."""
    av = []
    reg = manifesto.get("componentes_externos")
    if not reg:
        return ["AVISO: models/manifest.json ainda não tem `componentes_externos` (rode --gerar)"]
    for secao, chave in (("imagens_docker", "contêiner"), ("modelos_ollama", "nome")):
        antes = {x[chave]: x for x in (reg.get(secao) or [])}
        agora = {x[chave]: x for x in (atual.get(secao) or [])}
        if atual.get(secao) is None:
            av.append(f"AVISO: {secao} não pôde ser lido agora (serviço fora do ar?); sem comparação")
            continue
        for k in sorted(set(antes) | set(agora)):
            if k not in agora:
                av.append(f"AVISO: {secao}: `{k}` está no manifesto e sumiu do disco")
            elif k not in antes:
                av.append(f"AVISO: {secao}: `{k}` existe no disco e não está no manifesto")
            else:
                campo = "id" if secao == "imagens_docker" else "digest"
                if antes[k].get(campo) != agora[k].get(campo):
                    av.append(f"AVISO: {secao}: `{k}` mudou ({campo} {str(antes[k].get(campo))[:12]} -> {str(agora[k].get(campo))[:12]})")
        if secao == "imagens_docker":
            for k, x in sorted(agora.items()):
                if x["pinada_por"] == "tag":
                    av.append(f"AVISO: imagens_docker: `{k}` usa só tag (`{x['imagem']}`): mutável; fixe por digest quando decidir atualizar")
    antes = {x["caminho"]: x for x in reg.get("arquivos") or []}
    agora = {x["caminho"]: x for x in atual.get("arquivos") or []}
    for k in sorted(set(antes) | set(agora)):
        if k not in agora:
            av.append(f"AVISO: arquivo `{k}` está no manifesto e sumiu do disco")
        elif k not in antes:
            av.append(f"AVISO: arquivo `{k}` existe e não está no manifesto")
        elif antes[k]["bytes"] != agora[k]["bytes"]:
            av.append(f"AVISO: arquivo `{k}` mudou de tamanho ({antes[k]['bytes']} -> {agora[k]['bytes']})")
        elif profundo and antes[k].get("sha256") and agora[k].get("sha256") != antes[k]["sha256"]:
            av.append(f"AVISO: arquivo `{k}` mudou de conteúdo (sha256 divergente)")
    return av


def _selftest():
    import tempfile
    global imagens_docker, modelos_ollama, flatpak_obsidian
    res = {}
    salvo = (imagens_docker, modelos_ollama, flatpak_obsidian)
    imagens_docker = lambda: [{"contêiner": "a", "imagem": "x@sha256:" + "0" * 64, "id": "aaa", "pinada_por": "digest", "repo_digests": []},
                              {"contêiner": "b", "imagem": "y:1.2", "id": "bbb", "pinada_por": "tag", "repo_digests": []}]
    modelos_ollama = lambda: [{"nome": "m1", "digest": "d1", "bytes": 1}]
    flatpak_obsidian = lambda: None
    try:
        with tempfile.TemporaryDirectory() as td:
            f1 = os.path.join(td, "v.onnx")
            open(f1, "wb").write(b"modelo\n")
            lista = os.path.join(td, "lista.txt")
            open(lista, "w").write(f"# comentário\n{td}/*.onnx\n")
            m = {"modelos": [{"name": "legado"}], "gerado_por": "P3-02"}
            m["componentes_externos"] = gerar(lista)
            res["1 gera as seções e preserva o que já existia no manifesto (`modelos`, `gerado_por`)"] = \
                m["modelos"] == [{"name": "legado"}] and m["gerado_por"] == "P3-02" and len(m["componentes_externos"]["arquivos"]) == 1
            res["2 arquivo listado leva sha256 correto"] = m["componentes_externos"]["arquivos"][0]["sha256"] == hashlib.sha256(b"modelo\n").hexdigest()
            res["3 sem deriva: só o aviso fixo de imagem por tag"] = \
                [x for x in comparar(m, gerar(lista)) if "usa só tag" not in x] == []
            open(f1, "wb").write(b"modelx\n")   # mesmo tamanho, outro conteúdo
            res["4 mudou o conteúdo com o mesmo tamanho: só o modo --profundo acusa"] = \
                not any("conteúdo" in x for x in comparar(m, gerar(lista, com_hash=False))) and \
                any("conteúdo" in x for x in comparar(m, gerar(lista), profundo=True))
            modelos_ollama = lambda: [{"nome": "m1", "digest": "d2", "bytes": 1}, {"nome": "m2", "digest": "x", "bytes": 2}]
            av = comparar(m, gerar(lista, com_hash=False))
            res["5 digest do Ollama mudou e modelo novo: acusa os dois"] = any("`m1` mudou" in x for x in av) and any("`m2` existe no disco" in x for x in av)
            imagens_docker = lambda: None
            res["6 docker fora do ar: avisa e não inventa deriva"] = any("não pôde ser lido" in x for x in comparar(m, gerar(lista, com_hash=False)))
            res["7 manifesto sem a chave nova: pede --gerar"] = "--gerar" in comparar({"modelos": []}, gerar(lista))[0]
    finally:
        imagens_docker, modelos_ollama, flatpak_obsidian = salvo
    for k, v in res.items():
        print(("OK    " if v else "FALHOU"), k)
    ruins = [k for k, v in res.items() if not v]
    print(f"inventario_componentes selftest: {len(res) - len(ruins)}/{len(res)} verificações OK")
    return 1 if ruins else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gerar", action="store_true")
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--profundo", action="store_true")
    ap.add_argument("--estrito", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--manifesto", default="models/manifest.json")
    ap.add_argument("--lista", default="config/componentes-externos.txt")
    ap.add_argument("--saida", default="-")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if a.gerar:
        try:
            with open(a.manifesto, encoding="utf-8") as f:
                m = json.load(f)
        except (OSError, ValueError):
            m = {}
        m["componentes_externos"] = gerar(a.lista)
        txt = json.dumps(m, ensure_ascii=False, indent=1) + "\n"
        if a.saida == "-":
            sys.stdout.write(txt)
        else:
            with open(a.saida, "w", encoding="utf-8") as f:
                f.write(txt)
        return 0
    if a.verificar:
        try:
            with open(a.manifesto, encoding="utf-8") as f:
                m = json.load(f)
        except (OSError, ValueError) as e:
            print(f"AVISO: manifesto ilegível ({e})")
            return 1 if a.estrito else 0
        av = comparar(m, gerar(a.lista, com_hash=a.profundo), profundo=a.profundo)
        print("\n".join(av) if av else "OK: componentes externos conferem com o manifesto")
        return 1 if (av and a.estrito) else 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
