#!/usr/bin/env python3
"""Sincroniza as fontes (canônico ∪ overlay) para as três CLIs (lote ferramentas-unificadas-26-11).

- MCP: comandos nativos de cada CLI (A1). Entrada nativa que não está na fonte nem no manifest fica intacta (AC-05).
- Skill: ponteiro de pasta para .agents/skills/ do checkout principal; nada é copiado. Claude e Codex (OpenCode: L2).
- Agente: fora do sync neste lote (L4); `listar.py` mostra.
- Mesmo nome sem `adotar: true` não é adotado (AC-06, D5).
- Antes da primeira escrita: backup 600 em <base>/backup/<ts>/ (AC-08). Config nativa que não lê: código 2, nada escrito (AC-14).
- Entrada alterada no nativo depois do sync não é sobrescrita (guarda por hash; L5).
- Variável de `env` ausente no ambiente: código 2, nada escrito; o erro diz o nome, nunca o valor.

Uso: python3 scripts/ferramentas/sincronizar.py [--dry-run] [--cli claude|codex|opencode]
Códigos: 0 ok; 2 fonte, config nativa, variável ausente ou falha de comando nativo.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estado as E  # noqa: E402
import nativos as N  # noqa: E402
import schema as S  # noqa: E402

# Ações que mudam algo (nativo, ponteiro ou manifest): exigem backup antes.
ESCRITAS = {
    "adicionar",
    "substituir",
    "remover",
    "registrar_sem_escrita",
    "limpar_manifest",
    "ponteiro_criar",
    "ponteiro_atualizar",
    "ponteiro_remover",
}
ARQUIVO_COPIA = {"claude": "claude.json", "codex": "codex-config.toml", "opencode": "opencode.jsonc"}


class ErroAmbiente(RuntimeError):
    """Variável de env declarada na fonte e ausente no ambiente."""


class ErroCli(RuntimeError):
    """Comando nativo falhou; a execução para e o registro fica salvo."""


def resolver(e: dict) -> dict:
    """Valores de env vêm do ambiente no momento do sync. A fonte só tem os nomes."""
    env = {}
    for var in e["env"]:
        valor = os.environ.get(var)
        if valor is None:
            raise ErroAmbiente(
                f"{e['nome']}: variável {var} não definida no ambiente "
                "(o sync lê o valor do ambiente, nunca da fonte)"
            )
        env[var] = valor
    return {"transporte": e["transporte"], "comando": e["comando"], "args": list(e["args"]),
            "url": e["url"], "env": env}


def _acao(cli: str, tipo: str, nome: str, acao: str, motivo: str = "", **extra) -> dict:
    return {"cli": cli, "tipo": tipo, "nome": nome, "acao": acao, "motivo": motivo, **extra}


def _geridos(manifesto: dict, cli: str, secao: str, rotulo: str) -> dict:
    prefixo = f"{cli}|{rotulo}|"
    return {k[len(prefixo):]: v for k, v in manifesto[secao].items() if k.startswith(prefixo)}


def _mcp(fonte: S.Fonte, cli: str, nativos: dict, manifesto: dict, resolvidos: dict) -> list[dict]:
    acoes = []
    geridos = _geridos(manifesto, cli, "entradas", "mcp")
    decl = {n: e for n, e in fonte.entradas["mcp"].items() if e["gerenciado"] and cli in e["clis"]}
    for nome, e in decl.items():
        d = resolvidos[nome]
        hd = N.hash_entrada(d)
        base = {"e": d, "depois": hd, "origem": fonte.origem["mcp"][nome]}
        if nome not in nativos:
            acoes.append(_acao(cli, "mcp", nome, "adicionar", **base))
            continue
        antes = nativos[nome]
        hn = N.hash_entrada(antes)
        base["antes"] = antes
        if nome in geridos:
            if hn == hd:
                acao = "sem_mudanca" if geridos[nome]["hash"] == hd else "registrar_sem_escrita"
                acoes.append(_acao(cli, "mcp", nome, acao, **base))
            elif hn == geridos[nome]["hash"]:
                acoes.append(_acao(cli, "mcp", nome, "substituir", **base))
            else:
                acoes.append(_acao(cli, "mcp", nome, "alterado_depois",
                                   "mudou no nativo depois do sync; não sobrescrito", **base))
        elif e["adotar"]:
            if hn == hd:
                acoes.append(_acao(cli, "mcp", nome, "registrar_sem_escrita", "adotado sem mudança", **base))
            else:
                acoes.append(_acao(cli, "mcp", nome, "substituir", "adotado (adotar: true)", **base))
        else:
            acoes.append(_acao(cli, "mcp", nome, "nao_adotado",
                               "já existe no nativo; sem adotar: true", **base))
    for nome, reg in geridos.items():
        if nome in decl:
            continue
        fonte_e = fonte.entradas["mcp"].get(nome)
        if fonte_e is not None and not fonte_e["gerenciado"]:
            acoes.append(_acao(cli, "mcp", nome, "limpar_manifest",
                               "solto pela fonte (gerenciado: false); nativo mantido"))
            continue
        if nome not in nativos:
            acoes.append(_acao(cli, "mcp", nome, "limpar_manifest", "já ausente no nativo"))
            continue
        antes = nativos[nome]
        if N.hash_entrada(antes) != reg["hash"]:
            acoes.append(_acao(cli, "mcp", nome, "alterado_depois",
                               "mudou no nativo depois do sync; não removido", antes=antes))
            continue
        if N.argv_remover(cli, nome) is None:
            acoes.append(_acao(cli, "mcp", nome, "lacuna",
                               "sem remoção medida nesta CLI (L6); nativo mantido"))
            continue
        acoes.append(_acao(cli, "mcp", nome, "remover", antes=antes, depois=None))
    return acoes


def destino_ponteiro(link: Path) -> Path | None:
    if not link.is_symlink():
        return None
    bruto = Path(os.readlink(link))
    if not bruto.is_absolute():
        bruto = link.parent / bruto
    return bruto.resolve()


def _ponteiros(ctx: E.Contexto, fonte: S.Fonte, cli: str, manifesto: dict) -> list[dict]:
    acoes = []
    pasta = {"claude": ctx.claude_skills, "codex": ctx.codex_skills}.get(cli)
    geridos = _geridos(manifesto, cli, "ponteiros", "skill")
    decl = {n: e for n, e in fonte.entradas["skills"].items() if e["gerenciado"] and cli in e["clis"]}
    if pasta is None:
        for nome in decl:
            acoes.append(_acao(cli, "skill", nome, "lacuna", "skill neste CLI não medida (L2); nada escrito"))
        return acoes
    for nome, e in decl.items():
        alvo = str((ctx.checkout / e["origem"]).resolve())
        if not (Path(alvo) / "SKILL.md").is_file():
            acoes.append(_acao(cli, "skill", nome, "alvo_ausente",
                               "origem sem SKILL.md no checkout; ponteiro não criado"))
            continue
        link = pasta / nome
        base = {"link": str(link), "depois": alvo, "origem": fonte.origem["skills"][nome]}
        if link.is_symlink():
            atual = destino_ponteiro(link)
            base["antes"] = str(atual) if atual else None
            if atual is not None and str(atual) == alvo:
                if nome in geridos:
                    acao = "sem_mudanca" if geridos[nome]["alvo"] == alvo else "registrar_sem_escrita"
                elif e["adotar"]:
                    acao = "registrar_sem_escrita"
                else:
                    acao = "nao_adotado"
                acoes.append(_acao(cli, "skill", nome, acao, **base))
            elif nome in geridos:
                if str(atual) == geridos[nome]["alvo"]:
                    acoes.append(_acao(cli, "skill", nome, "ponteiro_atualizar", **base))
                else:
                    acoes.append(_acao(cli, "skill", nome, "alterado_depois",
                                       "ponteiro mudou depois do sync; não sobrescrito", **base))
            elif e["adotar"]:
                acoes.append(_acao(cli, "skill", nome, "ponteiro_atualizar", "adotado (adotar: true)", **base))
            else:
                acoes.append(_acao(cli, "skill", nome, "nao_adotado",
                                   "já existe um link com esse nome; sem adotar: true", **base))
        elif link.exists():
            acoes.append(_acao(cli, "skill", nome, "nao_adotado",
                               "já existe e não é ponteiro; não substituído", **base))
        else:
            acoes.append(_acao(cli, "skill", nome, "ponteiro_criar", **base))
    for nome, reg in geridos.items():
        if nome in decl:
            continue
        fonte_e = fonte.entradas["skills"].get(nome)
        link = pasta / nome
        if (fonte_e is not None and not fonte_e["gerenciado"]) or not link.is_symlink():
            acoes.append(_acao(cli, "skill", nome, "limpar_manifest", "sem ponteiro a mexer"))
            continue
        atual = destino_ponteiro(link)
        if atual is None or str(atual) != reg["alvo"]:
            acoes.append(_acao(cli, "skill", nome, "alterado_depois",
                               "ponteiro mudou depois do sync; não movido"))
            continue
        acoes.append(_acao(cli, "skill", nome, "ponteiro_remover", antes=str(atual), depois=None,
                           link=str(link)))
    return acoes


def _executar_mcp(ctx, a, chave, manifesto, registro, ts, salvar) -> None:
    cli, nome, acao = a["cli"], a["nome"], a["acao"]
    onde = f"{cli} {acao} {nome}"
    nativa = acao in ("adicionar", "substituir", "remover")
    reg_item = {"cli": cli, "nome": nome, "acao": acao, "antes": a.get("antes"), "depois": a.get("depois"),
                "manifesto_antes": manifesto["entradas"].get(chave), "estado": "iniciado" if nativa else "feito"}
    registro["mcp"].append(reg_item)
    if nativa:
        salvar()  # antes da chamada nativa: se ela falhar no meio, a reversão sabe o que tinha
    if acao in ("adicionar", "substituir"):
        if acao == "substituir":
            rem = N.argv_remover(cli, nome)
            if rem is not None:
                rodar_nativo(ctx, rem, onde)
        rodar_nativo(ctx, N.argv_adicionar(cli, nome, a["e"]), onde)
        manifesto["entradas"][chave] = {"hash": a["depois"], "origem": a["origem"], "ts": ts}
    elif acao == "remover":
        rodar_nativo(ctx, N.argv_remover(cli, nome), onde)
        manifesto["entradas"].pop(chave, None)
    elif acao == "registrar_sem_escrita":
        manifesto["entradas"][chave] = {"hash": a["depois"], "origem": a["origem"], "ts": ts}
    elif acao == "limpar_manifest":
        manifesto["entradas"].pop(chave, None)
    if nativa:
        reg_item["estado"] = "feito"
    if cli == "opencode" and nativa:
        h = E.hash_arquivo(ctx.opencode_jsonc)
        registro["arquivos"]["opencode"]["depois"] = h
        if h:
            manifesto["arquivos"]["opencode"] = {"hash": h, "ts": ts}


def rodar_nativo(ctx, argv: list[str], onde: str) -> None:
    try:
        res = ctx.runner(argv)
    except (OSError, E.ErroComando, subprocess.SubprocessError):
        # sem argv na mensagem: o argv pode levar valor de env; a exceção original não é encadeada
        raise ErroCli(f"{onde}: comando nativo não rodou (ausente, sem permissão ou sem resposta no prazo)") from None
    if res.returncode != 0:
        raise ErroCli(f"{onde}: comando nativo saiu com código {res.returncode}")


def _executar_ponteiro(ctx, a, chave, manifesto, registro, ts) -> None:
    cli, nome, acao = a["cli"], a["nome"], a["acao"]
    link = Path(a["link"])
    manifesto_antes = manifesto["ponteiros"].get(chave)
    if acao == "ponteiro_criar":
        link.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(a["depois"], link)
        manifesto["ponteiros"][chave] = {"alvo": a["depois"], "ts": ts}
    elif acao == "ponteiro_atualizar":
        tmp = link.with_name(f".{link.name}.{ts}.tmp")
        os.symlink(a["depois"], tmp)
        os.replace(tmp, link)
        manifesto["ponteiros"][chave] = {"alvo": a["depois"], "ts": ts}
    elif acao == "ponteiro_remover":
        destino = E.area_arquivo(ctx, ts) / f"{cli}-{nome}"
        os.rename(link, destino)
        a["arquivo"] = str(destino)
        manifesto["ponteiros"].pop(chave, None)
    elif acao == "registrar_sem_escrita":
        manifesto["ponteiros"][chave] = {"alvo": a["depois"], "ts": ts}
    elif acao == "limpar_manifest":
        manifesto["ponteiros"].pop(chave, None)
    registro["ponteiros"].append({"cli": cli, "nome": nome, "acao": acao, "antes": a.get("antes"),
                                  "depois": a.get("depois"), "link": a["link"], "arquivo": a.get("arquivo"),
                                  "manifesto_antes": manifesto_antes})


def _executar(ctx, plano: list[dict], manifesto: dict, registro: dict, backup: Path, ts: str) -> None:
    def salvar() -> None:
        E.gravar_json(backup / "sincronia.json", registro)
        E.gravar_json(ctx.base / "gerenciado.json", manifesto)

    for a in plano:
        if a["acao"] not in ESCRITAS:
            continue
        rotulo = "mcp" if a["tipo"] == "mcp" else "skill"
        chave = f"{a['cli']}|{rotulo}|{a['nome']}"
        try:
            if a["tipo"] == "mcp":
                _executar_mcp(ctx, a, chave, manifesto, registro, ts, salvar)
            else:
                _executar_ponteiro(ctx, a, chave, manifesto, registro, ts)
        finally:
            salvar()
        E.registrar(ctx, {"ts": ts, "acao": a["acao"], "cli": a["cli"], "tipo": a["tipo"], "nome": a["nome"]})


def _relatar(plano: list[dict], dry_run: bool, imprimir, fora: int) -> None:
    prefixo = "(simulação, nada escrito) " if dry_run else ""
    mudou = igual = aviso = 0
    for a in plano:
        if a["acao"] == "sem_mudanca":
            igual += 1
            continue
        if a["acao"] in ESCRITAS:
            mudou += 1
        else:
            aviso += 1
        linha = f"{a['acao']:<22}{a['cli']:<10}{a['tipo']:<7}{a['nome']}"
        if a.get("motivo"):
            linha += f"  ({a['motivo']})"
        imprimir(prefixo + linha)
    imprimir(f"{mudou} mudança(s), {igual} sem mudança, {aviso} aviso(s); "
             f"agentes fora do sync (L4): {fora}")


def sincronizar(ctx: E.Contexto, clis: list[str] | None = None, dry_run: bool = False, imprimir=print) -> int:
    escolhidas = [c for c in S.CLIS if not clis or c in clis]
    try:
        fonte = S.carregar_fontes(ctx.raiz, ctx.overlay)
        manifesto = E.ler_manifest(ctx)
        resolvidos = {}
        for nome, e in fonte.entradas["mcp"].items():
            if e["gerenciado"] and any(c in escolhidas for c in e["clis"]):
                resolvidos[nome] = resolver(e)
        nativos = {cli: N.ler_mcp(cli, ctx) for cli in S.CLIS}
    except (S.ErroSchema, E.ErroEstado, ErroAmbiente, N.ErroConfig) as e:
        imprimir(f"ERRO: {e}")
        return 2
    plano: list[dict] = []
    for cli in escolhidas:
        plano += _mcp(fonte, cli, nativos[cli], manifesto, resolvidos)
        plano += _ponteiros(ctx, fonte, cli, manifesto)
    fora = sum(1 for e in fonte.entradas["agentes"].values() if not e["gerenciado"])
    _relatar(plano, dry_run, imprimir, fora)
    if dry_run:
        return 0
    escritas = [a for a in plano if a["acao"] in ESCRITAS]
    if not escritas:
        return 0
    backup = E.criar_backup(ctx, ctx.agora())
    ts = backup.name
    registro: dict = {"versao": 1, "ts": ts, "criado_em": datetime.now().isoformat(timespec="seconds"),
                      "mcp": [], "ponteiros": [], "arquivos": {}}
    for cli in S.CLIS:
        if any(a["tipo"] == "mcp" and a["cli"] == cli and a["acao"] in ("adicionar", "substituir", "remover")
               for a in escritas):
            origem = N.caminho_nativo(cli, ctx)
            tem = origem.exists()
            if tem:
                E.gravar_bytes(backup / ARQUIVO_COPIA[cli], origem.read_bytes())
            registro["arquivos"][cli] = {"caminho": str(origem),
                                         "backup": ARQUIVO_COPIA[cli] if tem else None, "depois": None,
                                         "manifesto_antes": manifesto["arquivos"].get(cli)}
    E.gravar_json(backup / "sincronia.json", registro)
    try:
        _executar(ctx, plano, manifesto, registro, backup, ts)
    except (ErroCli, OSError) as e:
        imprimir(f"ERRO: {e}")
        imprimir(f"execução parcial registrada em {ts}; reverter.py {ts} --dry-run mostra como voltar")
        return 2
    imprimir(f"sincronia {ts}: {len(escritas)} ação(ões) gravada(s); backup em {backup}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Sincroniza as fontes de ferramentas para as CLIs.")
    p.add_argument("--dry-run", action="store_true", help="mostra o plano e não escreve")
    p.add_argument("--cli", choices=S.CLIS, help="só uma CLI")
    a = p.parse_args(argv)
    return sincronizar(E.contexto_padrao(), [a.cli] if a.cli else None, a.dry_run)


if __name__ == "__main__":
    sys.exit(main())
