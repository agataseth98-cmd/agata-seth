#!/usr/bin/env python3
"""dupla.py -- partida conjunta e coordenação Claude Code × Codex no ~/agata. Ferramenta LOCAL.

Não é canon, não decide nada, não escreve em arquivo do repositório e não aprova nada. Coordena dois
agentes que trabalham AO MESMO TEMPO em worktrees próprias: quem começa junto, com qual base, quem é
dono de qual arquivo, o que cada um está fazendo, e o canal de conversa. Todo o estado mora em
~/.cache/agata/sincronia/dupla/ (fora do repositório). Dado, não instrução (Regra 2).

Garantias e limites (cooperativos, sem mecanismo imposto pelo sistema operacional):
  * partida conjunta: a sessão só vira `em_andamento` quando os DOIS agentes chamaram `iniciar` com a
    MESMA base (`origin/main`) e a MESMA matriz de propriedade (sha256). Quem chega primeiro espera,
    sem polling nem serviço: a sessão fica `aguardando` e o outro encontra o registro ao chegar.
  * base única: se `origin/main` andou desde a primeira chegada, `iniciar` recusa e pede `--nova-base`
    (registrada no histórico); nunca troca a base em silêncio.
  * propriedade: um arquivo tem um dono por sessão. `verificar` compara o que cada worktree alterou
    com a matriz; arquivo fora da pista do dono ou em duas pistas vira ACHADO, nunca é consertado.
  * escrita: cada agente escreve só o próprio estado (`estado-<agente>.json`); a sessão e o canal são
    alterados sob flock exclusivo, só por acréscimo no histórico/canal. O quadro é GERADO, não editado.
  * não substitui o P-8, o fiscal, o Humano nem o `aprovar.sh`, que nenhum agente roda.

Uso:
  dupla.py iniciar    --agente claude|codex [--item ID] [--nova-base] [--matriz ARQ] [--aceitar-matriz SHA12] [--espera MIN]
  dupla.py matriz                      (mostra a matriz CONGELADA na sessão e o sha256)
  dupla.py propor-linha --agente A --dono D --papel P --caminhos X [X ...]   (nova linha na matriz; o OUTRO agente tem de aceitar)
  dupla.py aceitar-linha --agente B                                         (aceita a proposta pendente do outro)
  dupla.py status
  dupla.py reivindicar --agente A --item ID --caminhos P [P ...]
  dupla.py estado     --agente A --item ID --estado em_andamento|em_revisao|bloqueado|pronto [--bloqueio T]
  dupla.py verificar  [--repo DIR]
  dupla.py quadro
  dupla.py dizer      --agente A --assunto T --texto T [--resposta-a ID] [--estado T] [--proximo A]
  dupla.py ler        --agente A
  dupla.py encerrar   --agente A
  dupla.py --selftest
"""
import argparse
import datetime
import fcntl
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zoneinfo

TZ = zoneinfo.ZoneInfo("America/Sao_Paulo")
AGENTES = ("claude", "codex")
RAIZ_SINC = os.environ.get("DUPLA_DIR", os.path.expanduser("~/.cache/agata/sincronia"))
D = os.path.join(RAIZ_SINC, "dupla")
CANAL = os.path.join(RAIZ_SINC, "conversa.md")
REPO = os.environ.get("DUPLA_REPO", os.path.expanduser("~/agata"))

# Matriz de propriedade PROPOSTA (parecer do Claude sobre o v4, anexo A). Só vale quando os dois a aceitam
# (mesmo sha256 em `iniciar`). Padrão com `/` no fim = prefixo de diretório; senão, glob de fnmatch.
MATRIZ_PADRAO = [
    {"dono": "claude", "papel": "integração e registro",
     "caminhos": ["MEMÓRIAS.md", "ONDE_ESTAMOS.md", "PROJETO.md", "REGRAS.md", "PROTOCOLOS.md", "FALHAS.md",
                  "CLAUDE.md", "PROMPT_CARREGAMENTO.md", "propostas/"]},
    {"dono": "claude", "papel": "fiscal",
     "caminhos": [".github/workflows/perimetro.yml", ".github/workflows/fiscal-p8.yml", "scripts/p8_*",
                  "scripts/testar_perimetro.sh", "scripts/testar_p8_*", "scripts/perimetro.sh",
                  "scripts/perimetro/p08_quarentena.sh"]},
    {"dono": "claude", "papel": "hooks e derivados",
     "caminhos": [".githooks/", "scripts/gerar_obsidian.py", "scripts/gerar_indice_derivado.py",
                  "scripts/perimetro/p10_vault_derivado.sh", "scripts/perimetro/p17_skip_cronico.sh",
                  "scripts/testar_post_commit.py"]},
    {"dono": "codex", "papel": "escriba", "caminhos": ["redesign/router/seth_escriba.py"]},
    {"dono": "claude", "papel": "defesa local", "caminhos": ["redesign/systemd/", "config/portas-agata.txt"]},
    {"dono": "codex", "papel": "evidência, estilo e doutrina",
     "caminhos": ["AGENTS.md", "redesign/router/auditoria_turno.py", "redesign/router/afirmacoes_desmentidas.json",
                  "redesign/router/seth_gateway.py"]},
    {"dono": "codex", "papel": "memória e missões",
     "caminhos": ["scripts/busca_semantica.py", "scripts/busca_texto.py", "redesign/mcp/",
                  "scripts/avaliar_decisor.py", "redesign/grafo/evals/", "config/temas.tsv"]},
    {"dono": "claude", "papel": "atualização",
     "caminhos": ["models/manifest.json", "scripts/atualizar.sh", ".github/dependabot.yml"]},
    {"dono": "claude", "papel": "voz", "caminhos": ["redesign/router/tts_piper.py", "redesign/router/tts-piper/"]},
    {"dono": "claude", "papel": "github", "caminhos": ["SECURITY.md", ".github/CODEOWNERS", "README.md"]},
    {"dono": "claude", "papel": "conselho", "caminhos": ["scripts/conselho_remoto.py"]},
]


def agora():
    return datetime.datetime.now(TZ).isoformat(timespec="seconds")


def _p(nome):
    return os.path.join(D, nome)


def _git(repo, *a):
    p = subprocess.run(["git", "-C", repo, *a], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                       env={k: v for k, v in os.environ.items() if not k.startswith("GIT_") or k == "GIT_CONFIG_GLOBAL"})
    return p.returncode, p.stdout.strip(), p.stderr.strip()


class Trava:
    """flock exclusivo no arquivo de trava da sessão. Cooperativo."""
    def __enter__(self):
        os.makedirs(D, exist_ok=True)
        self.f = open(_p("sessao.lock"), "a")
        fcntl.flock(self.f, fcntl.LOCK_EX)
        return self

    def __exit__(self, *e):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


def _ler_json(nome, padrao):
    try:
        with open(_p(nome), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _gravar_json(nome, obj):
    tmp = _p(nome + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, _p(nome))   # só nos arquivos de estado da dupla; o canal NUNCA é substituído


def _historico(evento, **kw):
    """Acrescenta ao histórico (JSON por linha), sob a trava do chamador."""
    with open(_p("historico.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"quando": agora(), "evento": evento, **kw}, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def sha_matriz(matriz):
    return hashlib.sha256(json.dumps(matriz, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def dono_de(caminho, matriz):
    """Lista de (dono, papel) cujas pistas cobrem o caminho. Esperado: exatamente um."""
    achados = []
    for linha in matriz:
        for pad in linha["caminhos"]:
            if (pad.endswith("/") and caminho.startswith(pad)) or fnmatch.fnmatchcase(caminho, pad) or caminho == pad:
                achados.append((linha["dono"], linha["papel"]))
                break
    return achados


def disjunta(matriz):
    """Pistas sem sobreposição entre papéis diferentes: devolve os conflitos entre padrões literais."""
    conflitos = []
    for i, a in enumerate(matriz):
        for b in matriz[i + 1:]:
            for pa in a["caminhos"]:
                for pb in b["caminhos"]:
                    exemplos = [pa.rstrip("*"), pb.rstrip("*")]
                    for ex in exemplos:
                        if ex and dono_de(ex, [a]) and dono_de(ex, [b]):
                            conflitos.append((a["papel"], b["papel"], ex))
    return sorted(set(conflitos))


# ---------------------------------------------------------------------------------------------
def cmd_iniciar(a):
    repo = a.repo or REPO
    matriz = MATRIZ_PADRAO
    if a.matriz:
        with open(a.matriz, encoding="utf-8") as f:
            matriz = json.load(f)
    hm = sha_matriz(matriz)
    rc, base, err = _git(repo, "rev-parse", "origin/main")
    if rc:
        print(f"ERRO: não consegui ler origin/main em {repo}: {err}", file=sys.stderr)
        return 2
    _git(repo, "fetch", "-q", "origin")
    rc, base, _ = _git(repo, "rev-parse", "origin/main")
    c = disjunta(matriz)
    if c:
        print("ERRO: a matriz de propriedade tem pistas sobrepostas:", *[f"  {x}" for x in c], sep="\n", file=sys.stderr)
        return 2
    with Trava():
        s = _ler_json("sessao.json", None)
        if s is None or s.get("estado") == "encerrada":
            s = {"estado": "aguardando", "base": base, "matriz_sha256": hm, "matriz": matriz, "criada_em": agora(),
                 "presentes": {}, "versao": 2}
            _historico("sessao_criada", agente=a.agente, base=base, matriz=hm[:12])
        if s["base"] != base and not a.nova_base:
            print(f"RECUSADO: origin/main andou desde a primeira chegada (sessão {s['base'][:7]}, agora {base[:7]}). "
                  "Se ambos concordam, rode de novo com --nova-base (fica no histórico).", file=sys.stderr)
            return 1
        if a.nova_base and s["base"] != base:
            _historico("nova_base", agente=a.agente, de=s["base"], para=base)
            s["base"] = base
            s["presentes"] = {}
            s["estado"] = "aguardando"
        if s["matriz_sha256"] != hm and a.aceitar_matriz and s.get("matriz") \
                and s["matriz_sha256"].startswith(a.aceitar_matriz):
            # Adoção explícita da matriz CONGELADA na sessão, depois de o agente tê-la lido (`matriz`).
            _historico("matriz_aceita", agente=a.agente, matriz=s["matriz_sha256"][:12])
            hm, matriz = s["matriz_sha256"], s["matriz"]
            if s["estado"] == "divergente":
                s["estado"] = "aguardando"
                s.pop("divergencia", None)
        if s["matriz_sha256"] != hm:
            s["estado"] = "divergente"
            s["divergencia"] = {"agente": a.agente, "matriz_sessao": s["matriz_sha256"][:12], "matriz_agente": hm[:12]}
            _historico("matriz_divergente", agente=a.agente, matriz=hm[:12])
            _gravar_json("sessao.json", s)
            linhas = lambda m: {f"{l['dono']} | {l['papel']} | {c}" for l in m for c in l["caminhos"]}
            so_sessao = sorted(linhas(s.get("matriz") or MATRIZ_PADRAO) - linhas(matriz))
            so_agente = sorted(linhas(matriz) - linhas(s.get("matriz") or MATRIZ_PADRAO))
            print(f"DIVERGENTE: matriz da sessão {s['matriz_sha256'][:12]} x matriz de {a.agente} {hm[:12]}. Nada começou.", file=sys.stderr)
            if so_sessao:
                print("  só na sessão:", *so_sessao, sep="\n    ", file=sys.stderr)
            if so_agente:
                print(f"  só em {a.agente}:", *so_agente, sep="\n    ", file=sys.stderr)
            print(f"  Para adotar a matriz da sessão, leia `dupla.py matriz` e rode `iniciar ... --aceitar-matriz {s['matriz_sha256'][:12]}`. "
                  "Para mudar a matriz da sessão, é decisão do Humano.", file=sys.stderr)
            return 1
        s["presentes"][a.agente] = {"chegou_em": agora(), "item": a.item, "base": base}
        _historico("chegada", agente=a.agente, item=a.item)
        faltam = [x for x in AGENTES if x not in s["presentes"]]
        if not faltam and s["estado"] in ("aguardando", "solo"):
            s["estado"] = "em_andamento"
            s["iniciada_em"] = agora()
            _historico("partida_conjunta", base=base, matriz=hm[:12])
        _gravar_json("sessao.json", s)
        _gravar_json(f"estado-{a.agente}.json", _ler_json(f"estado-{a.agente}.json", {"agente": a.agente, "itens": {}}))
    if s["estado"] == "em_andamento":
        print(f"PARTIDA CONJUNTA: base {base[:7]}, matriz {hm[:12]}, ambos presentes. Podem trabalhar em paralelo.")
        return 0
    print(f"AGUARDANDO {', '.join(faltam)}: base {base[:7]} registrada, matriz {hm[:12]}. "
          f"Quem chegar depois encontra este registro; nada fica em segundo plano. "
          f"(Se o outro não vier em {a.espera} min, rode `status` e decida com o Humano; não há relógio automático.)")
    return 0


def cmd_status(_a):
    s = _ler_json("sessao.json", None)
    if not s:
        print("sem sessão. Rode `iniciar`.")
        return 0
    rc, base, _ = _git(REPO, "rev-parse", "origin/main")
    print(f"estado: {s['estado']} | base da sessão: {s['base'][:7]} | origin/main agora: {base[:7] if not rc else '?'}"
          + ("  <-- DERIVA" if not rc and base != s["base"] else ""))
    for ag in AGENTES:
        pr = s["presentes"].get(ag)
        print(f"  {ag}: {'presente desde ' + pr['chegou_em'] if pr else 'ausente'}")
    for ag, info in _ausentes().items():
        outro = [x for x in AGENTES if x != ag][0]
        print(f"  AUSENTE: {ag} desde {info['desde']}" + (f" até {info['ate']}" if info.get('ate') else "")
              + (f" ({info['motivo']})" if info.get('motivo') else "") + f" -> {outro} cobre a pista dele (fallback mútuo)")
    if s.get("divergencia"):
        print("  divergência:", s["divergencia"])
    return 0


def _ausentes():
    """{agente: {desde, motivo, ate}} dos agentes declarados ausentes (cota esgotada, sessão fechada, etc.)."""
    return {ag: _ler_json(f"ausencia-{ag}.json", None) for ag in AGENTES if _ler_json(f"ausencia-{ag}.json", None)}


def cmd_ausente(a):
    """FALLBACK MÚTUO: declara que `agente` não está disponível. A pista dele pode ser assumida pelo outro SEM alerta de
    FORA DA PISTA; o trabalho feito assim fica listado como ASSUMIDA e vale revisão do titular ao voltar (autor != revisor)."""
    _gravar_json(f"ausencia-{a.agente}.json", {"desde": agora(), "motivo": a.motivo or "", "ate": a.ate or ""})
    _historico("ausente", agente=a.agente, motivo=a.motivo or "", ate=a.ate or "")
    outro = [x for x in AGENTES if x != a.agente][0]
    print(f"OK: {a.agente} ausente" + (f" até {a.ate}" if a.ate else "") + f". {outro} pode assumir a pista de {a.agente}; "
          f"volte com `presente --agente {a.agente}`.")
    return 0


def cmd_presente(a):
    p = _p(f"ausencia-{a.agente}.json")
    if os.path.exists(p):
        os.unlink(p)
    _historico("presente", agente=a.agente)
    outro = [x for x in AGENTES if x != a.agente][0]
    print(f"OK: {a.agente} presente de novo. O que {outro} fez na pista dele (ASSUMIDA) espera a revisão de {a.agente}.")
    return 0


def cmd_matriz(_a):
    s = _ler_json("sessao.json", None)
    m = (s or {}).get("matriz") or MATRIZ_PADRAO
    print(f"matriz {sha_matriz(m)[:12]} ({'congelada na sessão' if s and s.get('matriz') else 'padrão da ferramenta; sessão antiga sem congelamento'})")
    for l in m:
        print(f"  {l['dono']:6s} {l['papel']}: {', '.join(l['caminhos'])}")
    return 0


def cmd_propor_linha(a):
    """Acrescenta UMA linha nova à matriz da sessão, por consentimento mútuo (o outro agente aceita). Nunca
    altera nem remove linha existente; a linha nova não pode sobrepor pista já existente."""
    with Trava():
        s = _ler_json("sessao.json", None)
        if not s or s["estado"] != "em_andamento":
            print("RECUSADO: sem partida conjunta em andamento.", file=sys.stderr)
            return 1
        pend = _ler_json("proposta-matriz.json", None)
        if pend:
            print(f"RECUSADO: já há proposta pendente de {pend['proposta_por']} ({pend['linha']['papel']}); aguarde o aceite "
                  "ou combine a retirada no canal. Nada é sobrescrito em silêncio.", file=sys.stderr)
            return 1
        linha = {"dono": a.dono, "papel": a.papel, "caminhos": sorted(a.caminhos)}
        nova = (s.get("matriz") or MATRIZ_PADRAO) + [linha]
        conflitos = disjunta(nova)
        if conflitos:
            print("RECUSADO: a linha sobrepõe pista existente:", *[f"  {c}" for c in conflitos], sep="\n", file=sys.stderr)
            return 1
        _gravar_json("proposta-matriz.json", {"proposta_por": a.agente, "linha": linha, "em": agora()})
        _historico("proposta_de_linha", agente=a.agente, linha=linha)
    print(f"OK: proposta registrada; {[x for x in AGENTES if x != a.agente][0]} precisa rodar `aceitar-linha`.")
    return 0


def cmd_aceitar_linha(a):
    with Trava():
        s = _ler_json("sessao.json", None)
        prop = _ler_json("proposta-matriz.json", None)
        if not s or not prop:
            print("RECUSADO: não há proposta pendente.", file=sys.stderr)
            return 1
        if prop["proposta_por"] == a.agente:
            print("RECUSADO: quem propõe não aceita a própria proposta (Regra 3).", file=sys.stderr)
            return 1
        nova = (s.get("matriz") or MATRIZ_PADRAO) + [prop["linha"]]
        if disjunta(nova):
            print("RECUSADO: a linha passou a sobrepor outra pista.", file=sys.stderr)
            return 1
        s["matriz"] = nova
        s["matriz_sha256"] = sha_matriz(nova)
        _gravar_json("sessao.json", s)
        os.replace(_p("proposta-matriz.json"), _p(f"proposta-matriz.aceita-{datetime.datetime.now(TZ):%H%M%S}.json"))
        _historico("linha_aceita", agente=a.agente, linha=prop["linha"], matriz=s["matriz_sha256"][:12])
    print(f"OK: matriz agora {s['matriz_sha256'][:12]} (linha de {prop['proposta_por']}, aceita por {a.agente}).")
    return 0


def cmd_reivindicar(a):
    with Trava():
        s = _ler_json("sessao.json", None)
        matriz = (s or {}).get("matriz") or MATRIZ_PADRAO
        if not s or s["estado"] != "em_andamento":
            print("RECUSADO: sem partida conjunta em andamento.", file=sys.stderr)
            return 1
        est = _ler_json(f"estado-{a.agente}.json", {"agente": a.agente, "itens": {}})
        outro = [x for x in AGENTES if x != a.agente][0]
        est_o = _ler_json(f"estado-{outro}.json", {"agente": outro, "itens": {}})
        usados = {c: (outro, i) for i, v in est_o["itens"].items() for c in v.get("caminhos", [])}
        ruins = []
        for c in a.caminhos:
            for (d, _papel) in dono_de(c, matriz) or [(None, None)]:
                if d != a.agente:
                    ruins.append(f"{c}: pista de {d or 'ninguém'}")
            if c in usados:
                ruins.append(f"{c}: já reivindicado por {usados[c][0]} ({usados[c][1]})")
        if ruins:
            print("RECUSADO:", *ruins, sep="\n  ", file=sys.stderr)
            return 1
        est["itens"].setdefault(a.item, {"estado": "em_andamento"})["caminhos"] = sorted(a.caminhos)
        est["itens"][a.item]["reivindicado_em"] = agora()
        _gravar_json(f"estado-{a.agente}.json", est)
        _historico("reivindicado", agente=a.agente, item=a.item, caminhos=sorted(a.caminhos))
    print(f"OK: {a.agente} reivindicou {a.item}: {', '.join(sorted(a.caminhos))}")
    return 0


def cmd_estado(a):
    with Trava():
        est = _ler_json(f"estado-{a.agente}.json", {"agente": a.agente, "itens": {}})
        it = est["itens"].setdefault(a.item, {})
        it.update(estado=a.estado, atualizado_em=agora())
        if a.bloqueio:
            it["bloqueio"] = a.bloqueio
        em_andamento = sum(1 for v in est["itens"].values() if v.get("estado") == "em_andamento")
        if em_andamento > 2:
            print(f"AVISO: {a.agente} tem {em_andamento} itens em andamento (limite combinado: 2).", file=sys.stderr)
        _gravar_json(f"estado-{a.agente}.json", est)
        _historico("estado", agente=a.agente, item=a.item, estado=a.estado)
    print(f"OK: {a.item} -> {a.estado}")
    return 0


_ANC = re.compile(rb"<!-- ANCORA-SHA:INICIO.*?<!-- ANCORA-SHA:FIM -->", re.DOTALL)
_ANCORADOS = ("REGRAS.md", "PROJETO.md", "MEMÓRIAS.md", "PROMPT_CARREGAMENTO.md")
# Gerados pelos hooks a cada commit (derivados do canon, SEM quarentena no P-8); e pastas que não são do repositório.
_IGNORAR = ("reports/", "research_notes/", ".hidrata.md", "INDICE_MEMORIAS.md", "INDICE_MEMORIAS_PALAVRAS-CHAVE.md")


def _so_ancora(wt, base_wt, caminho):
    """True se o arquivo (versão da worktree) só difere da base dentro do bloco ANCORA-SHA gerado pelo pre-commit."""
    rc, antigo, _ = subprocess.run(["git", "-C", wt, "show", f"{base_wt}:{caminho}"], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE).returncode, None, None
    a = subprocess.run(["git", "-C", wt, "show", f"{base_wt}:{caminho}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if a.returncode:
        return False
    try:
        with open(os.path.join(wt, caminho), "rb") as f:
            b = f.read()
    except OSError:
        return False
    return _ANC.sub(b"<ANCORA>", a.stdout, count=1) == _ANC.sub(b"<ANCORA>", b, count=1)


def cmd_verificar(a):
    """Compara o que cada worktree (ramos claude/* e codex/*) alterou frente ao ponto em que saiu da base da
    sessão com a matriz de propriedade. Só RELATA: nada é corrigido."""
    repo = a.repo or REPO
    s = _ler_json("sessao.json", None)
    if not s:
        print("sem sessão.")
        return 1
    rc, saida, _ = _git(repo, "worktree", "list", "--porcelain")
    pistas = []
    for bloco in saida.split("\n\n"):
        d = dict(l.split(" ", 1) for l in bloco.splitlines() if " " in l)
        if "worktree" in d and d.get("branch", "").startswith(("refs/heads/claude/", "refs/heads/codex/")):
            pistas.append((d["worktree"], d["branch"]))
    achados, vistos, assumidas = [], {}, []
    ausentes = set(_ausentes())
    for caminho, ramo in pistas:
        quem = "claude" if ramo.startswith("refs/heads/claude/") else "codex"
        rc, mb, _ = _git(caminho, "merge-base", "HEAD", s["base"])
        if rc:
            mb = s["base"]
        _, nomes, _ = _git(caminho, "diff", "--name-only", mb)
        _, novos, _ = _git(caminho, "ls-files", "--others", "--exclude-standard")
        for f in sorted(set((nomes + "\n" + novos).splitlines()) - {""}):
            if f.startswith(_IGNORAR) or f in _IGNORAR:
                continue
            if f in _ANCORADOS and _so_ancora(caminho, mb, f):
                continue
            donos = dono_de(f, s.get('matriz') or MATRIZ_PADRAO)
            if not donos:
                achados.append(f"SEM DONO: {f} (alterado por {quem}, {os.path.basename(caminho)})")
            elif quem not in {d for d, _ in donos}:
                if all(d in ausentes for d, _ in donos):
                    assumidas.append(f"ASSUMIDA: {f} por {quem} (pista de {donos[0][0]}, ausente; revisão do titular ao voltar)")
                else:
                    achados.append(f"FORA DA PISTA: {f} alterado por {quem} (pista de {donos[0][0]}, {donos[0][1]})")
            vistos.setdefault(f, set()).add(quem)
    for f, qs in vistos.items():
        if len(qs) > 1:
            achados.append(f"DUPLO: {f} alterado pelos dois ({', '.join(sorted(qs))})")
    print(f"worktrees examinadas: {len(pistas)} ({', '.join(os.path.basename(c) for c, _ in pistas) or 'nenhuma'})")
    if assumidas:
        print("FALLBACK (não é achado):", *sorted(assumidas), sep="\n  ")
    if achados:
        print("ACHADOS (nada foi corrigido):", *sorted(achados), sep="\n  ")
        return 1
    print("OK: nenhuma alteração fora da pista nem em duas pistas.")
    return 0


def cmd_quadro(_a):
    s = _ler_json("sessao.json", {})
    print(f"# Quadro (gerado em {agora()}; sessão {s.get('estado', '-')}, base {s.get('base', '-')[:7]})\n")
    print("| item | dono | estado | caminhos | bloqueio |\n|---|---|---|---|---|")
    for ag in AGENTES:
        for i, v in sorted(_ler_json(f"estado-{ag}.json", {"itens": {}})["itens"].items()):
            print(f"| {i} | {ag} | {v.get('estado', '-')} | {', '.join(v.get('caminhos', [])) or '-'} | {v.get('bloqueio', '')} |")
    return 0


def _acrescentar_canal(texto):
    os.makedirs(os.path.dirname(CANAL), exist_ok=True)
    with open(CANAL, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(texto)
        f.flush()
        os.fsync(f.fileno())
        fcntl.flock(f, fcntl.LOCK_UN)


def cmd_dizer(a):
    ident = f"{a.agente}-{datetime.datetime.now(TZ):%Y-%m-%d}-{hashlib.sha256((agora() + a.texto).encode()).hexdigest()[:8]}"
    nome = {"claude": "Claude Code", "codex": "Codex"}[a.agente]
    msg = (f"\n## {ident}\n- Autor: {nome} (modelo exato não medido por esta ferramenta).\n- Hora: {agora()} (relógio da Máquina).\n"
           + (f"- Resposta-a: {a.resposta_a}.\n" if a.resposta_a else "")
           + f"- Assunto: {a.assunto}.\n" + (f"- Estado: {a.estado}.\n" if a.estado else "")
           + f"\n{a.texto.strip()}\n" + (f"\nPróximo responsável: {a.proximo}.\n" if a.proximo else ""))
    _acrescentar_canal(msg)
    print("OK:", ident)
    return 0


def cmd_ler(a):
    marca = _ler_json(f"leitura-{a.agente}.json", {"offset": 0})
    try:
        with open(CANAL, encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            f.seek(marca["offset"])
            novo = f.read()
            fim = f.tell()
            fcntl.flock(f, fcntl.LOCK_UN)
    except OSError:
        print("canal ausente.")
        return 1
    print(novo if novo.strip() else "(nada novo no canal desde a última leitura)")
    with Trava():
        _gravar_json(f"leitura-{a.agente}.json", {"offset": fim, "lido_em": agora()})
    return 0


def cmd_encerrar(a):
    with Trava():
        s = _ler_json("sessao.json", None)
        if not s:
            return 0
        s["presentes"].pop(a.agente, None)
        if not s["presentes"]:
            s["estado"] = "encerrada"
        _historico("saida", agente=a.agente, sessao=s["estado"])
        _gravar_json("sessao.json", s)
    print("OK: saída registrada.")
    return 0


# ---------------------------------------------------------------------------------------------
def _selftest():
    import shutil
    import threading
    global D, CANAL, RAIZ_SINC
    res = {}
    tmp = tempfile.mkdtemp(prefix="dupla-t-")
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    for k in [k for k in env if k.startswith("GIT_") and k not in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM")]:
        del env[k]
    sh = lambda *c, cwd=repo: subprocess.run(c, cwd=cwd, env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sh("git", "init", "-q", "-b", "main")
    sh("git", "config", "user.email", "t@e.i"); sh("git", "config", "user.name", "t")
    open(os.path.join(repo, "a.txt"), "w").write("a\n")
    sh("git", "add", "-A"); sh("git", "commit", "-qm", "base")
    bare = os.path.join(tmp, "origin.git")
    sh("git", "clone", "-q", "--bare", repo, bare, cwd=tmp)
    sh("git", "remote", "add", "origin", bare); sh("git", "fetch", "-q", "origin")
    D = os.path.join(tmp, "sinc", "dupla"); RAIZ_SINC = os.path.join(tmp, "sinc"); CANAL = os.path.join(RAIZ_SINC, "conversa.md")
    ns = lambda **k: argparse.Namespace(**{"repo": repo, "matriz": None, "nova_base": False, "item": None, "espera": 20,
                                           "aceitar_matriz": None, **k})
    try:
        res["01 a matriz padrão é disjunta (um dono por arquivo)"] = disjunta(MATRIZ_PADRAO) == []
        res["02 cada arquivo tem 1 dono e nenhum fica sem dono nos casos conhecidos"] = all(
            len(dono_de(f, MATRIZ_PADRAO)) == 1 for f in (
                "MEMÓRIAS.md", "scripts/p8_integral.py", ".githooks/post-commit", "redesign/router/seth_escriba.py",
                "redesign/router/tts-piper/instalar-agata.sh", "scripts/busca_semantica.py", "AGENTS.md"))
        buf = []
        rc1 = cmd_iniciar(ns(agente="claude", item="A1"))
        s = _ler_json("sessao.json", {})
        res["03 o primeiro a chegar fica AGUARDANDO"] = rc1 == 0 and s["estado"] == "aguardando"
        rc2 = cmd_iniciar(ns(agente="codex", item="A2"))
        s = _ler_json("sessao.json", {})
        res["04 a chegada do segundo abre a PARTIDA CONJUNTA"] = rc2 == 0 and s["estado"] == "em_andamento" and "iniciada_em" in s
        # base que anda
        open(os.path.join(repo, "b.txt"), "w").write("b\n"); sh("git", "add", "-A"); sh("git", "commit", "-qm", "avanço"); sh("git", "push", "-q", "origin", "main")
        res["05 origin/main andou: iniciar recusa sem --nova-base"] = cmd_iniciar(ns(agente="claude", item="A1")) == 1
        res["06 --nova-base é aceita e entra no histórico"] = cmd_iniciar(ns(agente="claude", item="A1", nova_base=True)) == 0 \
            and "nova_base" in open(_p("historico.jsonl")).read()
        # reivindicação
        s = _ler_json("sessao.json", {})
        cmd_iniciar(ns(agente="codex", item="A2"))
        res["07 reivindicar arquivo da própria pista funciona"] = cmd_reivindicar(argparse.Namespace(
            agente="claude", item="A1", caminhos=["scripts/p8_integral.py"])) == 0
        res["08 reivindicar arquivo da pista do outro é recusado"] = cmd_reivindicar(argparse.Namespace(
            agente="claude", item="X", caminhos=["redesign/router/seth_escriba.py"])) == 1
        res["09 reivindicar o que o outro já reivindicou é recusado"] = (
            cmd_reivindicar(argparse.Namespace(agente="codex", item="A2", caminhos=["redesign/router/seth_escriba.py"])) == 0
            and cmd_reivindicar(argparse.Namespace(agente="claude", item="Y", caminhos=["redesign/router/seth_escriba.py"])) == 1)
        # matriz divergente
        alt = os.path.join(tmp, "alt.json")
        json.dump(MATRIZ_PADRAO[:-1], open(alt, "w"))
        res["10 matriz diferente da aceita pelo outro: DIVERGENTE e nada começa"] = cmd_iniciar(ns(agente="codex", item="A2", matriz=alt)) == 1 \
            and _ler_json("sessao.json", {}).get("estado") == "divergente"

        s10 = _ler_json("sessao.json", {})
        res["10b a sessão congela a matriz e mostra a diferença na divergência"] = bool(s10.get("matriz")) and s10["estado"] == "divergente"
        sess_pref = s10["matriz_sha256"][:12]
        res["10c adotar a matriz congelada (--aceitar-matriz) tira a divergência e abre a partida"] = \
            cmd_iniciar(ns(agente="codex", item="A2", matriz=alt, aceitar_matriz=sess_pref)) == 0 \
            and _ler_json("sessao.json", {})["estado"] == "em_andamento"

        # emenda da matriz por consentimento mútuo
        s_ant = _ler_json("sessao.json", {})
        prop = argparse.Namespace(agente="claude", dono="claude", papel="inventário", caminhos=["scripts/inventario_componentes.py"])
        res["10d propor linha nova: registrada, e quem propõe NÃO aceita a própria"] = cmd_propor_linha(prop) == 0 \
            and cmd_aceitar_linha(argparse.Namespace(agente="claude")) == 1
        res["10e o outro aceita: matriz muda (sha novo), linha existente intacta e a pista passa a ter dono"] = \
            cmd_aceitar_linha(argparse.Namespace(agente="codex")) == 0 \
            and _ler_json("sessao.json", {})["matriz_sha256"] != s_ant["matriz_sha256"] \
            and dono_de("scripts/inventario_componentes.py", _ler_json("sessao.json", {})["matriz"]) == [("claude", "inventário")]
        res["10g com a proposta anterior já aceita, nova proposta é possível; com uma pendente, a segunda é recusada"] = (
            cmd_propor_linha(argparse.Namespace(agente="codex", dono="codex", papel="outra", caminhos=["x/y.txt"])) == 0
            and cmd_propor_linha(argparse.Namespace(agente="claude", dono="claude", papel="terceira", caminhos=["z/w.txt"])) == 1)
        os.unlink(_p("proposta-matriz.json"))
        res["10f linha que sobrepõe pista existente é recusada"] = cmd_propor_linha(argparse.Namespace(
            agente="codex", dono="codex", papel="intruso", caminhos=["scripts/p8_integral.py"])) == 1
        # canal: dois escritores simultâneos, nada se perde
        for k in ("sessao.json", "historico.jsonl"):
            os.path.exists(_p(k)) and os.unlink(_p(k))
        ts = []
        for i in range(12):
            ag = AGENTES[i % 2]
            ts.append(threading.Thread(target=cmd_dizer, args=(argparse.Namespace(
                agente=ag, assunto=f"a{i}", texto=f"mensagem {i}", resposta_a=None, estado=None, proximo=None),)))
        [t.start() for t in ts]; [t.join() for t in ts]
        txt = open(CANAL).read()
        res["11 12 mensagens simultâneas: todas presentes e inteiras"] = all(f"mensagem {i}" in txt for i in range(12)) and txt.count("## ") == 12
        before = open(CANAL).read()
        cmd_dizer(argparse.Namespace(agente="claude", assunto="x", texto="y", resposta_a=None, estado=None, proximo=None))
        res["12 o canal só cresce (o texto anterior segue intacto)"] = open(CANAL).read().startswith(before)
        # chegada simultânea: abre uma única partida
        threads = [threading.Thread(target=cmd_iniciar, args=(ns(agente=ag, item="Z"),)) for ag in AGENTES]
        [t.start() for t in threads]; [t.join() for t in threads]
        hist = open(_p("historico.jsonl")).read()
        res["13 chegada simultânea: exatamente 1 partida conjunta"] = hist.count("partida_conjunta") == 1 \
            and _ler_json("sessao.json", {})["estado"] == "em_andamento"
        # leitura incremental
        cmd_ler(argparse.Namespace(agente="codex"))
        n1 = _ler_json("leitura-codex.json", {})["offset"]
        cmd_dizer(argparse.Namespace(agente="claude", assunto="novo", texto="oi", resposta_a=None, estado=None, proximo=None))
        cmd_ler(argparse.Namespace(agente="codex"))
        res["14 `ler` avança o marcador e só mostra o novo"] = _ler_json("leitura-codex.json", {})["offset"] > n1
        # verificar com worktrees reais
        sh("git", "branch", "claude/it"); sh("git", "branch", "codex/it")
        wc, wx = os.path.join(tmp, "wc"), os.path.join(tmp, "wx")
        sh("git", "worktree", "add", "-q", wc, "claude/it"); sh("git", "worktree", "add", "-q", wx, "codex/it")
        s0 = _ler_json("sessao.json", {})
        base_atual = subprocess.run(["git", "-C", repo, "rev-parse", "origin/main"], stdout=subprocess.PIPE, text=True).stdout.strip()
        with Trava():
            s0["base"] = base_atual
            _gravar_json("sessao.json", s0)
        def escreve(wt, rel, txt):
            os.makedirs(os.path.dirname(os.path.join(wt, rel)), exist_ok=True)
            open(os.path.join(wt, rel), "w").write(txt)
        escreve(wc, "scripts/p8_integral.py", "x\n"); escreve(wx, "redesign/router/seth_escriba.py", "y\n")
        o = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "verificar", "--repo", repo], capture_output=True, text=True,
                           env=dict(os.environ, DUPLA_DIR=RAIZ_SINC))
        res["15 cada um na própria pista: verificar OK"] = o.returncode == 0 and "OK:" in o.stdout
        escreve(wx, "scripts/p8_integral.py", "z\n")
        o = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "verificar", "--repo", repo], capture_output=True, text=True,
                           env=dict(os.environ, DUPLA_DIR=RAIZ_SINC))
        res["16 o Codex mexe na pista do Claude: FORA DA PISTA e DUPLO"] = o.returncode == 1 and "FORA DA PISTA: scripts/p8_integral.py" in o.stdout and "DUPLO" in o.stdout
        os.unlink(os.path.join(wx, "scripts/p8_integral.py"))
        bloco = "<!-- ANCORA-SHA:INICIO (x) -->\n  sha\n<!-- ANCORA-SHA:FIM -->\n"
        sh("git", "-C", wc, "checkout", "-q", "-B", "claude/it") if False else None
        escreve(repo, "REGRAS.md", bloco.replace("sha", "aaa") + "corpo\n"); sh("git", "add", "-A"); sh("git", "commit", "-qm", "regras"); sh("git", "push", "-q", "origin", "main")
        sh("git", "-C", wc, "merge", "-q", "--ff-only", "main") if False else None
        s0["base"] = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], stdout=subprocess.PIPE, text=True).stdout.strip()
        with Trava():
            _gravar_json("sessao.json", s0)
        for w in (wc, wx):
            subprocess.run(["git", "-C", w, "merge", "-q", "--ff-only", s0["base"]], check=True, capture_output=True)
        escreve(wc, "REGRAS.md", bloco.replace("sha", "bbb") + "corpo\n")
        o = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "verificar", "--repo", repo], capture_output=True, text=True,
                           env=dict(os.environ, DUPLA_DIR=RAIZ_SINC))
        res["17 só o bloco de âncora mudou em REGRAS.md: não é achado"] = "REGRAS.md" not in o.stdout
        escreve(wc, "REGRAS.md", bloco.replace("sha", "bbb") + "corpo ALTERADO\n")
        o = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "verificar", "--repo", repo], capture_output=True, text=True,
                           env=dict(os.environ, DUPLA_DIR=RAIZ_SINC))
        res["18a REGRAS.md mudou fora da âncora pelo integrador (Claude): sem achado"] = "FORA DA PISTA: REGRAS.md" not in o.stdout
        escreve(wx, "REGRAS.md", bloco.replace("sha", "ccc") + "corpo DO CODEX\n")
        o = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "verificar", "--repo", repo], capture_output=True, text=True,
                           env=dict(os.environ, DUPLA_DIR=RAIZ_SINC))
        res["18b o Codex muda REGRAS.md fora da âncora: FORA DA PISTA"] = "FORA DA PISTA: REGRAS.md alterado por codex" in o.stdout
        if not res["18b o Codex muda REGRAS.md fora da âncora: FORA DA PISTA"]:
            print("DEBUG 18b:", o.returncode, o.stdout, o.stderr[-300:])
        # 19-21: fallback mútuo. Claude é o dono de REGRAS.md; o Codex a alterou (18b). Se o CLAUDE for declarado ausente, vira ASSUMIDA.
        env19 = dict(os.environ, DUPLA_DIR=RAIZ_SINC)
        subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "ausente", "--agente", "claude", "--motivo", "teste"], capture_output=True, text=True, env=env19)
        o = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "verificar", "--repo", repo], capture_output=True, text=True, env=env19)
        res["19 titular ausente: o outro mexer na pista vira ASSUMIDA, não FORA DA PISTA"] = \
            "ASSUMIDA: REGRAS.md por codex" in o.stdout and "FORA DA PISTA: REGRAS.md alterado por codex" not in o.stdout
        st = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "status"], capture_output=True, text=True, env=env19)
        res["20 status mostra o ausente e quem cobre"] = "AUSENTE: claude" in st.stdout and "codex cobre a pista" in st.stdout
        subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "presente", "--agente", "claude"], capture_output=True, text=True, env=env19)
        o = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "verificar", "--repo", repo], capture_output=True, text=True, env=env19)
        res["21 titular de volta: volta o alerta FORA DA PISTA"] = "FORA DA PISTA: REGRAS.md alterado por codex" in o.stdout
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for k, v in res.items():
        print(("OK    " if v else "FALHOU"), k)
    ruins = [k for k, v in res.items() if not v]
    print(f"dupla selftest: {len(res) - len(ruins)}/{len(res)} verificações OK")
    return 1 if ruins else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    sp = ap.add_subparsers(dest="cmd")
    def com(nome, **args):
        p = sp.add_parser(nome)
        for k, v in args.items():
            p.add_argument(f"--{k.replace('_', '-')}", **v)
        return p
    ag = {"required": True, "choices": AGENTES}
    p = com("iniciar", agente=ag, item={}, nova_base={"action": "store_true"}, matriz={}, aceitar_matriz={},
            espera={"type": int, "default": 20}, repo={})
    sp.add_parser("matriz")
    p = com("propor-linha", agente=ag, dono={"required": True, "choices": AGENTES}, papel={"required": True}); p.add_argument("--caminhos", nargs="+", required=True)
    com("aceitar-linha", agente=ag)
    sp.add_parser("status")
    p = com("reivindicar", agente=ag, item={"required": True}); p.add_argument("--caminhos", nargs="+", required=True)
    com("estado", agente=ag, item={"required": True}, estado={"required": True, "choices": ["em_andamento", "em_revisao", "bloqueado", "pronto"]}, bloqueio={})
    com("verificar", repo={})
    sp.add_parser("quadro")
    com("dizer", agente=ag, assunto={"required": True}, texto={"required": True}, resposta_a={}, estado={}, proximo={})
    com("ler", agente=ag)
    com("ausente", agente=ag, motivo={}, ate={})
    com("presente", agente=ag)
    com("encerrar", agente=ag)
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    f = {"iniciar": cmd_iniciar, "status": cmd_status, "reivindicar": cmd_reivindicar, "estado": cmd_estado,
         "verificar": cmd_verificar, "quadro": cmd_quadro, "matriz": cmd_matriz, "propor-linha": cmd_propor_linha, "aceitar-linha": cmd_aceitar_linha, "dizer": cmd_dizer, "ler": cmd_ler, "ausente": cmd_ausente, "presente": cmd_presente, "encerrar": cmd_encerrar}.get(a.cmd)
    if not f:
        ap.print_help()
        return 2
    return f(a)


if __name__ == "__main__":
    sys.exit(main())
