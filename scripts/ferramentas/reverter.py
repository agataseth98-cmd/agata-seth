#!/usr/bin/env python3
"""Reverte uma execução do sync pelo registro (lote ferramentas-unificadas-26-11; A3, AC-09, AC-10).

Uso:
  reverter.py --listar                      lista as execuções com registro
  reverter.py <ts> --dry-run                mostra o que voltaria, sem mexer
  reverter.py <ts> [--com-overlay]          reverte; --com-overlay também move o overlay para ~/agata-arquivo/

Regra: se alguma entrada, ponteiro ou o opencode.jsonc mudou depois do sync, nada é revertido (código 3).
- Claude e Codex: remove a entrada, ou recoloca o valor anterior, pelo comando nativo. Ausente é registrado, sem falhar.
- OpenCode (sem remove, L6): volta o arquivo do backup só se o hash ainda é o que o sync deixou; senão, pede ao Humano.
- Ponteiros de skill: mv para ~/agata-arquivo/ferramentas-<ts>/ (nunca rm).
- Manifest: volta ao que havia antes de cada ação (campo manifesto_antes do registro).
Códigos: 0 ok; 2 execução inexistente, registro ou config ilegível, ou falha de comando; 3 recusa.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estado as E  # noqa: E402
import nativos as N  # noqa: E402
import schema as S  # noqa: E402
import sincronizar as SYNC  # noqa: E402

NATIVAS = ("adicionar", "substituir", "remover")


class ErroReversao(RuntimeError):
    """Execução inexistente, já revertida ou com registro que não serve para reverter."""


def listar(ctx: E.Contexto) -> list[dict]:
    raiz = ctx.base / "backup"
    if not raiz.is_dir():
        return []
    saida = []
    for d in sorted(raiz.iterdir()):
        reg = d / "sincronia.json"
        if not reg.is_file():
            continue
        try:
            r = json.loads(reg.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            saida.append({"ts": d.name, "erro": "registro ilegível"})
            continue
        saida.append({"ts": d.name, "mcp": len(r.get("mcp", [])), "ponteiros": len(r.get("ponteiros", [])),
                      "revertida_em": r.get("revertida_em")})
    return saida


def _carregar(ctx: E.Contexto, ts: str) -> dict:
    p = ctx.base / "backup" / ts / "sincronia.json"
    if not p.is_file():
        raise ErroReversao(f"execução {ts} não encontrada")
    try:
        reg = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ErroReversao(f"registro de {ts} ilegível") from None
    if reg.get("revertida_em"):
        raise ErroReversao(f"execução {ts} já foi revertida em {reg['revertida_em']}")
    return reg


def _divergencias(ctx: E.Contexto, reg: dict, nativos: dict) -> list[str]:
    out = []
    for a in reg.get("mcp", []):
        atual = nativos[a["cli"]].get(a["nome"])
        h_atual = N.hash_entrada(atual) if atual is not None else None
        if a["acao"] not in NATIVAS or h_atual == a.get("depois"):
            continue
        if a.get("estado") == "iniciado":
            # a chamada nativa não terminou: aceita ausente (falhou antes) ou o valor de antes (não chegou a mudar)
            if h_atual is None or (a.get("antes") is not None and h_atual == N.hash_entrada(a["antes"])):
                continue
        out.append(f"{a['cli']} {a['nome']}: mudou depois do sync")
    info = reg.get("arquivos", {}).get("opencode")
    if info and info.get("depois") is not None and E.hash_arquivo(ctx.opencode_jsonc) != info["depois"]:
        out.append("opencode.jsonc mudou depois do sync; volta só com ordem do Humano (A3)")
    for p in reg.get("ponteiros", []):
        if p["acao"] in ("registrar_sem_escrita", "limpar_manifest"):
            continue
        atual = SYNC.destino_ponteiro(Path(p["link"]))
        if p["acao"] == "ponteiro_remover":
            if atual is not None:
                out.append(f"skill {p['nome']} ({p['cli']}): ponteiro reapareceu depois do sync")
        elif atual is None or str(atual) != p.get("depois"):
            out.append(f"skill {p['nome']} ({p['cli']}): ponteiro mudou depois do sync")
    return out


def _restaurar(secao: dict, chave: str, antes) -> None:
    if antes is None:
        secao.pop(chave, None)
    else:
        secao[chave] = antes


def _reverter_mcp(ctx: E.Contexto, reg: dict, nativos: dict, manifesto: dict, imprimir) -> None:
    for a in reversed(reg.get("mcp", [])):
        cli, nome = a["cli"], a["nome"]
        if cli != "opencode" and a["acao"] in NATIVAS:
            atual = nativos[cli].get(nome)
            antes = a.get("antes")
            if antes is None:
                if atual is not None:
                    SYNC.rodar_nativo(ctx, N.argv_remover(cli, nome), f"{cli} remover {nome}")
                    imprimir(f"removida: {cli} {nome}")
                else:
                    imprimir(f"ausente: {cli} {nome} (registrada, sem falhar)")
            elif atual is None or N.hash_entrada(atual) != N.hash_entrada(antes):
                if antes.get("transporte") not in ("stdio", "http"):
                    raise ErroReversao(f"{cli} {nome}: transporte anterior não restaurável pelo comando nativo")
                if atual is not None:
                    SYNC.rodar_nativo(ctx, N.argv_remover(cli, nome), f"{cli} remover {nome}")
                antes_resolvido = {k: antes.get(k) for k in ("transporte", "comando", "args", "url", "env")}
                SYNC.rodar_nativo(ctx, N.argv_adicionar(cli, nome, antes_resolvido), f"{cli} restaurar {nome}")
                imprimir(f"restaurada: {cli} {nome}")
        _restaurar(manifesto["entradas"], f"{cli}|mcp|{nome}", a.get("manifesto_antes"))


def _reverter_opencode(ctx: E.Contexto, reg: dict, manifesto: dict, ts: str, imprimir) -> None:
    info = reg.get("arquivos", {}).get("opencode")
    if not info:
        return
    if info.get("depois") is not None:
        pasta = ctx.base / "backup" / ts
        if ctx.opencode_jsonc.exists():
            E.gravar_bytes(pasta / "opencode-antes-de-reverter.jsonc", ctx.opencode_jsonc.read_bytes())
        if info.get("backup"):
            E.gravar_bytes(ctx.opencode_jsonc, (pasta / info["backup"]).read_bytes())
            imprimir("restaurado: opencode.jsonc do backup (hash conferido antes)")
        elif ctx.opencode_jsonc.exists():
            os.rename(ctx.opencode_jsonc, E.area_arquivo(ctx, ts) / "opencode.jsonc")
            imprimir("opencode.jsonc movido para ~/agata-arquivo (não existia antes do sync)")
    _restaurar(manifesto["arquivos"], "opencode", info.get("manifesto_antes"))


def _reverter_ponteiros(ctx: E.Contexto, reg: dict, manifesto: dict, ts: str, imprimir) -> None:
    for p in reversed(reg.get("ponteiros", [])):
        cli, nome, acao = p["cli"], p["nome"], p["acao"]
        link = Path(p["link"])
        if acao == "ponteiro_criar" and link.is_symlink():
            os.rename(link, E.area_arquivo(ctx, ts) / f"{cli}-{nome}")
            imprimir(f"ponteiro movido para o arquivo: {cli} {nome}")
        elif acao == "ponteiro_atualizar":
            if p.get("antes"):
                tmp = link.with_name(f".{link.name}.{ts}.rev")
                os.symlink(p["antes"], tmp)
                os.replace(tmp, link)
                imprimir(f"ponteiro voltou ao alvo anterior: {cli} {nome}")
            elif link.is_symlink():
                os.rename(link, E.area_arquivo(ctx, ts) / f"{cli}-{nome}")
        elif acao == "ponteiro_remover" and p.get("arquivo") and os.path.lexists(p["arquivo"]):
            os.rename(p["arquivo"], link)
            imprimir(f"ponteiro restaurado: {cli} {nome}")
        _restaurar(manifesto["ponteiros"], f"{cli}|skill|{nome}", p.get("manifesto_antes"))


def reverter(ctx: E.Contexto, ts: str, dry_run: bool = False, com_overlay: bool = False, imprimir=print) -> int:
    try:
        reg = _carregar(ctx, ts)
        manifesto = E.ler_manifest(ctx)
        nativos = {cli: N.ler_mcp(cli, ctx) for cli in S.CLIS}
    except (ErroReversao, E.ErroEstado, N.ErroConfig) as e:
        imprimir(f"ERRO: {e}")
        return 2
    recusas = _divergencias(ctx, reg, nativos)
    if recusas:
        for r in recusas:
            imprimir(f"RECUSA: {r}")
        imprimir("nada revertido: volte só com o estado que o sync deixou")
        return 3
    prefixo = "(simulação, nada revertido) " if dry_run else ""
    for a in reversed(reg.get("mcp", [])):
        if a["acao"] in NATIVAS and a["cli"] != "opencode":
            imprimir(f"{prefixo}{a['cli']} {a['nome']}: {'remover' if a.get('antes') is None else 'recolocar valor anterior'}")
    if reg.get("arquivos", {}).get("opencode", {}).get("depois") is not None:
        imprimir(f"{prefixo}opencode.jsonc: voltar ao backup (A3)")
    for p in reversed(reg.get("ponteiros", [])):
        if p["acao"] in ("ponteiro_criar", "ponteiro_atualizar", "ponteiro_remover"):
            imprimir(f"{prefixo}skill {p['nome']} ({p['cli']}): {p['acao']} desfeito")
    if dry_run:
        return 0
    try:
        _reverter_mcp(ctx, reg, nativos, manifesto, imprimir)
        _reverter_opencode(ctx, reg, manifesto, ts, imprimir)
        _reverter_ponteiros(ctx, reg, manifesto, ts, imprimir)
        if com_overlay and ctx.overlay.exists():
            os.rename(ctx.overlay, E.area_arquivo(ctx, ts) / "ferramentas.yml")
            imprimir("overlay movido para ~/agata-arquivo")
    except (SYNC.ErroCli, ErroReversao, OSError) as e:
        imprimir(f"ERRO: {e}")
        imprimir("reversão parcial; rode de novo com o mesmo ts depois de olhar o erro")
        return 2
    finally:
        E.gravar_json(ctx.base / "gerenciado.json", manifesto)
    reg["revertida_em"] = datetime.now().isoformat(timespec="seconds")
    E.gravar_json(ctx.base / "backup" / ts / "sincronia.json", reg)
    E.registrar(ctx, {"ts": ts, "acao": "reverter", "cli": "-", "tipo": "-", "nome": "-"})
    imprimir(f"execução {ts} revertida")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Reverte uma execução do sync de ferramentas.")
    p.add_argument("ts", nargs="?", help="nome da pasta em <base>/backup/")
    p.add_argument("--listar", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--com-overlay", action="store_true")
    a = p.parse_args(argv)
    ctx = E.contexto_padrao()
    if a.listar:
        execucoes = listar(ctx)
        for e in execucoes:
            if "erro" in e:
                print(f"{e['ts']}  {e['erro']}")
            else:
                estado = f"revertida em {e['revertida_em']}" if e["revertida_em"] else "pode reverter"
                print(f"{e['ts']}  mcp={e['mcp']}  ponteiros={e['ponteiros']}  {estado}")
        if not execucoes:
            print("nenhuma execução registrada")
        return 0
    if not a.ts:
        p.error("informe a execução (ts) ou use --listar")
    return reverter(ctx, a.ts, a.dry_run, a.com_overlay)


if __name__ == "__main__":
    sys.exit(main())
