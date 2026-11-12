"""Armazém local do painel: itens do vault (só leitura, lista fechada) e conversas salvas.

Saiu de server.py em 03/11/2026 sem mudar comportamento; o servidor importa estes nomes.
Lote 3 (09/11/2026): organização das conversas (fixar, arquivar, marcadores, pastas) em `organizacao.json`
dentro de CONVERSAS_DIR, busca por texto, exportação JSON/Markdown e importação de JSON exportado.
Tudo local, em ~/.cache/agata/painel-conversas. Conversa antiga (sem organização) abre com os valores padrão.
Proteção (09/11/2026, chat-protege-conversas-09-11): apagar move a conversa para `.lixeira/` (com a organização dela);
purga só por pedido manual; cada escrita ganha uma linha em `.registro.jsonl` (sem conteúdo); salvar uma conversa
importada mantém a origem dela.
Lote 4 (09/11/2026): árvore de ramos (`arvore`, com `mensagens` do caminho ativo), feedback e resposta interrompida
nas respostas, cortes de continuação e origem da ramificação (`ramificada_de`). Conversa sem ramo segue em `mensagens`.
"""
from __future__ import annotations

import json
import os
import re
import threading
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from chat_stream import MODELO_PADRAO, modelo_permitido, modelo_real_valido
from relogio import _reading_window

ROOT = Path(__file__).resolve().parents[2]


VAULT_ITENS = {"inicio": "INICIO.md", "timeline": "timeline.md", "estado": "estado.md",
               "mapa": "mapa-do-sistema.canvas", "memorias": "memorias.base", "moc-projeto": "moc-projeto.md",
               "moc-memoria": "moc-memoria.md", "moc-documentos": "moc-documentos.md", "moc-scripts": "moc-scripts.md"}
VAULT_LIMITE = 65536


def _vault_item(item_id: str) -> dict:
    """Um item do vault, só leitura, de uma lista fechada. Texto cru; canvas também vira lista de nós."""
    observed_at, fresh_until = _reading_window()
    nome = VAULT_ITENS[item_id]
    arq = ROOT / "memoria/obsidian" / nome
    base = {"schema_version": 1, "id": item_id, "fonte": "memoria/obsidian/" + nome,
            "observed_at": observed_at, "fresh_until": fresh_until}
    if not arq.is_file():
        return {**base, "state": "unknown", "titulo": nome, "motivo": "arquivo ausente no vault"}
    st = arq.stat()
    with arq.open("rb") as f:
        bruto = f.read(VAULT_LIMITE)
    texto = bruto.decode("utf-8", errors="replace")
    titulo = next((l[2:].strip() for l in texto.splitlines() if l.startswith("# ")), nome)
    out = {**base, "state": "ok", "titulo": titulo, "texto": texto, "tamanho": st.st_size,
           "truncado": st.st_size > VAULT_LIMITE,
           "modificado": datetime.fromtimestamp(st.st_mtime, ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds")}
    if nome.endswith(".canvas") and not out["truncado"]:
        try:
            dados = json.loads(texto)
            out["canvas"] = {"nos": [{"tipo": n.get("type", ""), "texto": str(n.get("text") or n.get("file") or "")[:200]}
                                     for n in dados.get("nodes", [])[:200]],
                             "arestas": len(dados.get("edges", []))}
        except ValueError:
            out["canvas"] = None
    return out


def _vault_caminho(caminho: str) -> dict | None:
    """Nota .md do vault pelo caminho relativo, só leitura. Recusa tudo que sair de memoria/obsidian."""
    if not re.fullmatch(r"[^\x00-\x1f\\]{1,200}\.md", caminho) or caminho.startswith("/") or ".." in caminho.split("/"):
        return None
    raiz = (ROOT / "memoria/obsidian").resolve()
    arq = (raiz / caminho).resolve()
    if raiz not in arq.parents or not arq.is_file():
        return None
    observed_at, fresh_until = _reading_window()
    st = arq.stat()
    with arq.open("rb") as f:
        texto = f.read(VAULT_LIMITE).decode("utf-8", errors="replace")
    titulo = next((l[2:].strip() for l in texto.splitlines() if l.startswith("# ")), arq.stem)
    return {"schema_version": 1, "id": caminho, "fonte": "memoria/obsidian/" + caminho, "state": "ok",
            "titulo": titulo, "texto": texto, "tamanho": st.st_size, "truncado": st.st_size > VAULT_LIMITE,
            "modificado": datetime.fromtimestamp(st.st_mtime, ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds"),
            "observed_at": observed_at, "fresh_until": fresh_until}


CONVERSAS_DIR = Path.home() / ".cache/agata/painel-conversas"
CONVERSA_ID = re.compile(r"[0-9a-f]{12}")
CONVERSA_LIMITE_BYTES = 262144
CONVERSA_MENSAGEM_LIMITE = 65536
# Lote 3 (09/11/2026). O nome do arquivo de organização não casa com CONVERSA_ID: a lista de conversas o ignora.
ORGANIZACAO_ARQUIVO = "organizacao.json"
IMPORTACAO_LIMITE_BYTES = CONVERSA_LIMITE_BYTES + 1024  # conversa de até 262144 bytes mais o cabeçalho do arquivo exportado
CONVERSAS_LISTA_LIMITE = 200
PASTAS_LIMITE = 50
PASTA_NOME_LIMITE = 60
MARCADORES_LIMITE = 10
MARCADOR_LIMITE = 24
BUSCA_TERMO_LIMITE = 120
BUSCA_RESULTADOS_LIMITE = 50
BUSCA_CONTEXTO = 60
FORMATOS_EXPORTACAO = ("json", "md")
FORMATO_EXPORTACAO = "agata-conversa"
VERSAO_EXPORTACAO = 1
CAMPOS_ORGANIZAR = ("fixada", "arquivada", "marcadores", "pasta")
_ORGANIZACAO_TRAVA = threading.Lock()
# Proteção (09/11/2026). A lixeira é uma pasta dentro de CONVERSAS_DIR; o nome de cada item é <id>-<AAAAMMDD-HHMMSS>.
LIXEIRA_PASTA = ".lixeira"
LIXEIRA_NOME = re.compile(r"[0-9a-f]{12}-[0-9]{8}-[0-9]{6}")
LIXEIRA_LISTA_LIMITE = 200
REGISTRO_ARQUIVO = ".registro.jsonl"
_REGISTRO_TRAVA = threading.Lock()
# Campos de origem de uma conversa importada (migrar.py, LibreChat). O salvar do painel não os reescreve.
ORIGEM_CAMPOS = ("origem", "origem_id", "titulo_original", "data_original", "importado_em")
# Lote 4 (09/11/2026): ramos (edição, regeneração e ramificação), feedback, resposta interrompida e continuação.
# Sem ramo, a conversa segue no formato de sempre (`mensagens`). Com ramo, grava `arvore` (nós com `id` e `pai`),
# sem repetir o caminho. Pai sempre vem antes do filho no arquivo: a leitura não entra em laço.
CONVERSA_NOS_LIMITE = 400
CONVERSA_CAMINHO_LIMITE = 200
NO_ID = re.compile(r"[A-Za-z0-9]{1,16}")
FEEDBACK_NOTAS = ("bom", "ruim")
FEEDBACK_MOTIVO_LIMITE = 200
CONTINUACOES_LIMITE = 20


class ErroConversa(Exception):
    """Recusa de uma operação de conversa: status HTTP e motivo curto em português, sem o conteúdo da conversa."""

    def __init__(self, status: int, motivo: str):
        super().__init__(motivo)
        self.status = status
        self.motivo = motivo


def _conversa_caminho(conversa_id: str) -> Path | None:
    if not isinstance(conversa_id, str) or not CONVERSA_ID.fullmatch(conversa_id):
        return None
    return CONVERSAS_DIR / (conversa_id + ".json")


def _conversa_arquivos() -> list[Path]:
    """Arquivos de conversa válidos (nome de 12 hex). Organização, temporários e lixo ficam de fora."""
    if not CONVERSAS_DIR.is_dir():
        return []
    return [a for a in CONVERSAS_DIR.glob("*.json") if CONVERSA_ID.fullmatch(a.stem) and a.is_file()]


def _conversa_ids() -> set[str]:
    return {a.stem for a in _conversa_arquivos()}


def _atualizada(arq: Path) -> str:
    return datetime.fromtimestamp(arq.stat().st_mtime, ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds")


def _entrada_padrao() -> dict:
    return {"fixada": False, "arquivada": False, "marcadores": [], "pasta": None, "origem_id": None}


# Organização: pastas e uma entrada por conversa, em organizacao.json (escrito inteiro, por troca atômica).

def _organizacao_caminho() -> Path:
    return CONVERSAS_DIR / ORGANIZACAO_ARQUIVO


def _marcador_ok(marcador: str) -> bool:
    return 0 < len(marcador) <= MARCADOR_LIMITE and all(c.isalnum() or c in " -" for c in marcador)


def _entrada_lida(e: dict) -> dict:
    """Entrada de organização com valores seguros. A pasta não é conferida aqui: quem usa a entrada confere."""
    bruto = e.get("marcadores") if isinstance(e.get("marcadores"), list) else []
    marcadores = []
    for m in bruto:
        if isinstance(m, str) and _marcador_ok(m) and m not in marcadores:
            marcadores.append(m)
    pasta = e.get("pasta")
    origem = e.get("origem_id")
    return {
        "fixada": e.get("fixada") is True,
        "arquivada": e.get("arquivada") is True,
        "marcadores": marcadores[:MARCADORES_LIMITE],
        "pasta": pasta if isinstance(pasta, str) else None,
        "origem_id": origem if isinstance(origem, str) and CONVERSA_ID.fullmatch(origem) else None,
    }


def _organizacao_ler() -> tuple[dict, bool]:
    """(organização, legível). Arquivo ausente vale vazio. Arquivo ilegível devolve legível=False: quem escreve
    recusa, para não sobrescrever o que não se conseguiu ler. Entradas malformadas são ignoradas.
    `lixeira` guarda a entrada de cada conversa apagada (chave: nome do item na lixeira)."""
    vazia = {"pastas": [], "conversas": {}, "lixeira": {}}
    arq = _organizacao_caminho()
    if not arq.is_file():
        return vazia, True
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return vazia, False
    if not isinstance(dados, dict):
        return vazia, False
    pastas = []
    for p in dados["pastas"] if isinstance(dados.get("pastas"), list) else []:
        if not isinstance(p, dict) or not isinstance(p.get("id"), str) or not CONVERSA_ID.fullmatch(p["id"]):
            continue
        nome = " ".join(p["nome"].split()) if isinstance(p.get("nome"), str) else ""
        if 0 < len(nome) <= PASTA_NOME_LIMITE and p["id"] not in {x["id"] for x in pastas}:
            pastas.append({"id": p["id"], "nome": nome})
    ids_pastas = {p["id"] for p in pastas}
    conversas = {}
    entradas = dados["conversas"] if isinstance(dados.get("conversas"), dict) else {}
    for cid, e in entradas.items():
        if not CONVERSA_ID.fullmatch(cid) or not isinstance(e, dict):
            continue
        entrada = _entrada_lida(e)
        if entrada["pasta"] not in ids_pastas:
            entrada["pasta"] = None
        conversas[cid] = entrada
    lixeira = {}
    apagadas = dados["lixeira"] if isinstance(dados.get("lixeira"), dict) else {}
    for nome, e in apagadas.items():
        if LIXEIRA_NOME.fullmatch(nome) and isinstance(e, dict):
            lixeira[nome] = _entrada_lida(e)
    return {"pastas": pastas, "conversas": conversas, "lixeira": lixeira}, True


def _organizacao_gravar(org: dict) -> None:
    CONVERSAS_DIR.mkdir(parents=True, exist_ok=True)
    arq = _organizacao_caminho()
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps({"schema_version": 1, **org}, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, arq)


def _organizacao_mudar(alterar):
    """Lê, altera e grava a organização sob trava. `alterar(org)` muda o dicionário e devolve o resultado.
    Se `alterar` recusar (ErroConversa), nada é gravado. Arquivo ilegível recusa com 409."""
    with _ORGANIZACAO_TRAVA:
        org, legivel = _organizacao_ler()
        if not legivel:
            raise ErroConversa(409, "organização das conversas ilegível; nada foi alterado")
        resultado = alterar(org)
        _organizacao_gravar(org)
        return resultado


def _marcadores_novos(valor) -> list[str]:
    """Marcadores pedidos pelo painel: texto curto, sem repetir, até MARCADORES_LIMITE. Recusa o resto com motivo."""
    if not isinstance(valor, list):
        raise ErroConversa(400, "marcadores precisa ser uma lista")
    saida = []
    for item in valor:
        if not isinstance(item, str):
            raise ErroConversa(400, "cada marcador precisa ser texto")
        marcador = " ".join(item.split()).lower()
        if not marcador:
            raise ErroConversa(400, "marcador vazio")
        if len(marcador) > MARCADOR_LIMITE:
            raise ErroConversa(400, f"marcador passa de {MARCADOR_LIMITE} caracteres")
        if not _marcador_ok(marcador):
            raise ErroConversa(400, "marcador só pode ter letras, números, espaço e hífen")
        if marcador not in saida:
            saida.append(marcador)
    if len(saida) > MARCADORES_LIMITE:
        raise ErroConversa(400, f"a conversa aceita até {MARCADORES_LIMITE} marcadores")
    return saida


def _conversa_organizar(conversa_id, campos) -> dict:
    """Fixar, arquivar, marcadores e pasta de uma conversa salva. Não mexe no conteúdo nem na data da conversa."""
    arq = _conversa_caminho(conversa_id)
    if arq is None or not arq.is_file():
        raise ErroConversa(404, "conversa não encontrada")
    if not isinstance(campos, dict) or not campos:
        raise ErroConversa(400, "nada para mudar")
    for nome in campos:
        if nome not in CAMPOS_ORGANIZAR:
            raise ErroConversa(400, f"campo desconhecido: {nome}")
    for nome in ("fixada", "arquivada"):
        if nome in campos and not isinstance(campos[nome], bool):
            raise ErroConversa(400, f"{nome} precisa ser sim ou não")
    if "pasta" in campos and campos["pasta"] is not None and not isinstance(campos["pasta"], str):
        raise ErroConversa(400, "pasta precisa ser um identificador ou vazio")
    marcadores = _marcadores_novos(campos["marcadores"]) if "marcadores" in campos else None

    def alterar(org):
        if campos.get("pasta") is not None and campos.get("pasta") not in {p["id"] for p in org["pastas"]}:
            raise ErroConversa(400, "a pasta não existe")
        atual = {**_entrada_padrao(), **org["conversas"].get(conversa_id, {})}
        for nome in ("fixada", "arquivada", "pasta"):
            if nome in campos:
                atual[nome] = campos[nome]
        if marcadores is not None:
            atual["marcadores"] = marcadores
        if atual == _entrada_padrao():
            org["conversas"].pop(conversa_id, None)
        else:
            org["conversas"][conversa_id] = atual
        return {"id": conversa_id, "fixada": atual["fixada"], "arquivada": atual["arquivada"],
                "marcadores": list(atual["marcadores"]), "pasta": atual["pasta"]}
    return _organizacao_mudar(alterar)


def _nome_pasta_pedido(nome) -> str:
    if not isinstance(nome, str):
        raise ErroConversa(400, "nome da pasta precisa ser texto")
    limpo = " ".join(nome.split())
    if not limpo:
        raise ErroConversa(400, "nome da pasta vazio")
    if len(limpo) > PASTA_NOME_LIMITE:
        raise ErroConversa(400, f"nome da pasta passa de {PASTA_NOME_LIMITE} caracteres")
    return limpo


def _pasta_mudar(acao, pasta_id=None, nome=None) -> dict:
    """Pastas (projetos): criar, renomear e apagar. Apagar pasta não apaga conversa: as conversas dela ficam sem pasta."""
    if acao not in ("criar", "renomear", "apagar"):
        raise ErroConversa(400, "ação de pasta desconhecida")
    if acao != "criar" and (not isinstance(pasta_id, str) or not CONVERSA_ID.fullmatch(pasta_id)):
        raise ErroConversa(400, "pasta inválida")
    nome_limpo = _nome_pasta_pedido(nome) if acao in ("criar", "renomear") else None

    def repetido(pastas, ignorar):
        return any(p["nome"].casefold() == nome_limpo.casefold() and p["id"] != ignorar for p in pastas)

    def alterar(org):
        pastas = org["pastas"]
        if acao == "criar":
            if len(pastas) >= PASTAS_LIMITE:
                raise ErroConversa(400, f"limite de {PASTAS_LIMITE} pastas; apague alguma antes")
            if repetido(pastas, None):
                raise ErroConversa(400, "já existe pasta com esse nome")
            ids = {p["id"] for p in pastas}
            novo = os.urandom(6).hex()
            while novo in ids:
                novo = os.urandom(6).hex()
            pastas.append({"id": novo, "nome": nome_limpo})
            return {"id": novo, "nome": nome_limpo}
        alvo = next((p for p in pastas if p["id"] == pasta_id), None)
        if alvo is None:
            raise ErroConversa(404, "pasta não encontrada")
        if acao == "renomear":
            if repetido(pastas, pasta_id):
                raise ErroConversa(400, "já existe pasta com esse nome")
            alvo["nome"] = nome_limpo
            return {"id": pasta_id, "nome": nome_limpo}
        org["pastas"] = [p for p in pastas if p["id"] != pasta_id]
        soltas = 0
        for entrada in org["conversas"].values():
            if entrada.get("pasta") == pasta_id:
                entrada["pasta"] = None
                soltas += 1
        return {"apagada": True, "conversas_soltas": soltas}
    return _organizacao_mudar(alterar)


def _conversas_listar() -> dict:
    """Conversas salvas. `total` conta as legíveis; `ilegiveis` conta os arquivos que não puderam ser lidos.
    Arquivo ilegível não aparece na lista e não é apagado nem mexido: só entra na contagem."""
    org, legivel = _organizacao_ler()
    arquivos = _conversa_arquivos()
    lidas = []
    for arq in arquivos:
        dados = _conversa_lida(arq)
        if dados is not None:
            lidas.append((arq, dados))
    lidas.sort(key=lambda par: par[0].stat().st_mtime, reverse=True)
    itens = []
    for arq, dados in lidas[:CONVERSAS_LISTA_LIMITE]:
        meta = {**_entrada_padrao(), **org["conversas"].get(arq.stem, {})}
        caminho = _mensagens_brutas(dados)
        itens.append({"id": arq.stem, "titulo": dados.get("titulo") or "Sem título", "atualizada": _atualizada(arq),
                      "mensagens": len(caminho),
                      "fixada": meta["fixada"], "arquivada": meta["arquivada"],
                      "marcadores": list(meta["marcadores"]), "pasta": meta["pasta"]})
    itens.sort(key=lambda c: not c["fixada"])  # estável: dentro de cada grupo, a mais recente primeiro
    pastas = [{"id": p["id"], "nome": p["nome"], "conversas": sum(1 for c in itens if c["pasta"] == p["id"])}
              for p in org["pastas"]]
    marcadores = sorted({m for c in itens for m in c["marcadores"]})
    return {"schema_version": 1, "state": "ok", "items": itens, "total": len(lidas),
            "ilegiveis": len(arquivos) - len(lidas), "pastas": pastas,
            "marcadores": marcadores, "organizacao": "ok" if legivel else "ilegivel"}


def motivo_conversa_recusada(dados) -> str:
    """Motivo, em português simples, de a conversa não ser gravada. Diz só a regra e a contagem, nunca o texto."""
    if not isinstance(dados, dict):
        return "formato da conversa inválido"
    arvore = dados.get("arvore")
    nos = arvore.get("nos") if isinstance(arvore, dict) and isinstance(arvore.get("nos"), list) else None
    if nos is not None and len(nos) > CONVERSA_NOS_LIMITE:
        return f"mais de {CONVERSA_NOS_LIMITE} mensagens contando as versões"
    caminho = _mensagens_brutas(dados)
    if len(caminho) > CONVERSA_CAMINHO_LIMITE:
        return "mais de 200 mensagens"
    todas = nos if nos is not None else caminho
    if any(isinstance(m, dict) and isinstance(m.get("content"), str) and len(m["content"]) > CONVERSA_MENSAGEM_LIMITE
           for m in todas):
        return f"uma mensagem passa de {CONVERSA_MENSAGEM_LIMITE} caracteres"
    modelo = dados.get("modelo")
    if (modelo is not None and not modelo_permitido(modelo)) or any(
            isinstance(m, dict) and m.get("role") == "assistant" and m.get("modelo") is not None
            and not modelo_permitido(m.get("modelo")) for m in todas):
        return "modelo fora da lista"
    if dados.get("id") and _conversa_caminho(dados.get("id")) is None:
        return "identificador da conversa inválido"
    return "formato da conversa inválido"


def _feedback_limpo(valor):
    """Feedback de uma resposta: nota `bom` ou `ruim`, motivo opcional. Fora do formato, sai sem recusar a conversa."""
    if not isinstance(valor, dict) or valor.get("nota") not in FEEDBACK_NOTAS:
        return None
    limpo = {"nota": valor["nota"]}
    motivo = " ".join(valor["motivo"].split()) if isinstance(valor.get("motivo"), str) else ""
    if motivo:
        limpo["motivo"] = motivo[:FEEDBACK_MOTIVO_LIMITE]
    return limpo


def _cortes_limpos(valor, tamanho):
    """Posições, no texto da resposta, onde começa uma continuação: inteiros sem repetir, dentro do texto."""
    if not isinstance(valor, list) or not valor or len(valor) > CONTINUACOES_LIMITE:
        return None
    if not all(type(c) is int and 0 <= c <= tamanho for c in valor):
        return None
    return sorted(set(valor))


def _ramo_limpo(valor):
    """Origem de uma conversa ramificada: id da conversa de onde saiu e posição da mensagem no caminho (0 = primeira)."""
    if not isinstance(valor, dict) or not isinstance(valor.get("id"), str) or not CONVERSA_ID.fullmatch(valor["id"]):
        return None
    posicao = valor.get("mensagem")
    if type(posicao) is not int or not 0 <= posicao < CONVERSA_CAMINHO_LIMITE:
        return None
    return {"id": valor["id"], "mensagem": posicao}


def _mensagem_limpa(m, leve: bool = False) -> dict | None:
    """Mensagem (ou nó da árvore) no formato salvo. None se inválida. `leve`: modelo fora da lista some em vez de recusar."""
    if not isinstance(m, dict) or m.get("role") not in ("user", "assistant") or not isinstance(m.get("content"), str):
        return None
    if len(m["content"]) > CONVERSA_MENSAGEM_LIMITE:
        return None
    item = {"role": m["role"], "content": m["content"]}
    if m["role"] == "assistant":
        if m.get("modelo") is not None:
            if modelo_permitido(m["modelo"]):
                item["modelo"] = m["modelo"]
            elif not leve:
                return None
        if modelo_real_valido(m.get("modelo_real")):
            item["modelo_real"] = m["modelo_real"]
        if m.get("interrompida") is True:
            item["interrompida"] = True
        feedback = _feedback_limpo(m.get("feedback"))
        if feedback is not None:
            item["feedback"] = feedback
        cortes = _cortes_limpos(m.get("cortes"), len(m["content"]))
        if cortes is not None:
            item["cortes"] = cortes
    return item


def _caminho_de(nos: dict, folha) -> list | None:
    """Nós da raiz até a folha, em ordem. `nos` é {id: nó}. Folha desconhecida ou laço: None."""
    if not isinstance(folha, str):
        return None
    caminho, atual, visto = [], folha, set()
    while atual is not None:
        if not isinstance(atual, str) or atual in visto or atual not in nos:
            return None
        visto.add(atual)
        caminho.append(nos[atual])
        atual = nos[atual].get("pai")
    return list(reversed(caminho))


def _arvore_limpa(bruto, leve: bool = False):
    """Árvore de uma conversa com ramos: (árvore limpa, caminho ativo em formato de mensagem) ou None."""
    if not isinstance(bruto, dict) or not isinstance(bruto.get("nos"), list) or not 0 < len(bruto["nos"]) <= CONVERSA_NOS_LIMITE:
        return None
    nos, ids = [], {}
    for bruto_no in bruto["nos"]:
        if not isinstance(bruto_no, dict) or not isinstance(bruto_no.get("id"), str) \
                or not NO_ID.fullmatch(bruto_no["id"]) or bruto_no["id"] in ids:
            return None
        pai = bruto_no.get("pai")
        if pai is not None and (not isinstance(pai, str) or pai not in ids):
            return None
        item = _mensagem_limpa(bruto_no, leve)
        if item is None:
            return None
        no = {"id": bruto_no["id"], "pai": pai, **item}
        nos.append(no)
        ids[no["id"]] = no
    folha = bruto.get("folha")
    caminho = _caminho_de(ids, folha)
    if caminho is None or len(caminho) > CONVERSA_CAMINHO_LIMITE:
        return None
    return {"nos": nos, "folha": folha}, [{k: v for k, v in no.items() if k not in ("id", "pai")} for no in caminho]


def _mensagens_brutas(dados: dict) -> list:
    """Caminho ativo de uma conversa lida do arquivo, sem validar o texto (listas e busca). Com árvore: o caminho da folha."""
    if isinstance(dados.get("mensagens"), list):
        return dados["mensagens"]
    arvore = dados.get("arvore")
    if isinstance(arvore, dict) and isinstance(arvore.get("nos"), list):
        nos = {n["id"]: n for n in arvore["nos"] if isinstance(n, dict) and isinstance(n.get("id"), str)}
        return _caminho_de(nos, arvore.get("folha")) or []
    return []


def _formato_gravar(limpo: dict) -> dict:
    """O que vai ao arquivo. Sem ramo: `mensagens`, como sempre. Com ramo: `arvore` e também `mensagens` (o caminho
    ativo), para que uma versão anterior, que não lê árvore, abra a conversa pelo caminho. Quem lê árvore usa só ela."""
    saida = {"titulo": limpo["titulo"], "modelo": limpo["modelo"], "mensagens": limpo["mensagens"]}
    if "arvore" in limpo:
        saida["arvore"] = limpo["arvore"]
    if "ramificada_de" in limpo:
        saida["ramificada_de"] = limpo["ramificada_de"]
    # Proteção: arquivo com origem (importado) guarda o próprio id e os campos de origem; o salvar não os perde.
    for chave in ("id", *ORIGEM_CAMPOS):
        if chave in limpo:
            saida[chave] = limpo[chave]
    return saida


def _conversa_validar(dados: dict, leve: bool = False) -> dict | None:
    """Conversa no formato do painel, com o modelo escolhido (`modelo`, e `modelo` em cada resposta da Seth).

    Modelo ausente vale MODELO_PADRAO (conversa antiga, sem o campo). Modelo fora da lista recusa a
    gravação (None). `leve` é para leitura de arquivo já salvo: modelo fora da lista vira o padrão, e a
    conversa abre mesmo assim; árvore ilegível cai no caminho `mensagens`, se houver. `modelo_real` (nome que
    respondeu, cabeçalho do gateway) é só guardado quando tem formato de nome; se não tem, sai da conversa sem
    recusar a gravação.

    Lote 4: com `arvore` (ramos), o caminho vem da folha e `mensagens` é ignorado. Sem ramo (todo nó no
    caminho), a árvore é descartada e a conversa segue como lista. `ramificada_de` inválido sai sem recusar.
    """
    if not isinstance(dados, dict):
        return None
    titulo = str(dados.get("titulo") or "").strip()[:80] or "Sem título"
    modelo = dados.get("modelo")
    if modelo is None:
        modelo = MODELO_PADRAO
    elif not modelo_permitido(modelo):
        if not leve:
            return None
        modelo = MODELO_PADRAO
    arvore, limpas = None, None
    if dados.get("arvore") is not None:
        feita = _arvore_limpa(dados["arvore"], leve)
        if feita is None and not leve:
            return None
        if feita is not None:
            arvore, limpas = feita
    if limpas is None:
        mensagens = dados.get("mensagens")
        if not isinstance(mensagens, list) or len(mensagens) > CONVERSA_CAMINHO_LIMITE:
            return None
        limpas = []
        for m in mensagens:
            item = _mensagem_limpa(m, leve)
            if item is None:
                return None
            limpas.append(item)
    limpo = {"titulo": titulo, "modelo": modelo, "mensagens": limpas}
    if arvore is not None and len(arvore["nos"]) > len(limpas):
        limpo["arvore"] = arvore
    ramo = _ramo_limpo(dados.get("ramificada_de"))
    if ramo is not None:
        limpo["ramificada_de"] = ramo
    return limpo


# Origem de conversa importada (09/11/2026, origem-preservada-07-11): o salvar do painel não a perde nem a duplica.

def _origem_valida(dados: dict) -> dict:
    """Campos de origem (importação do LibreChat) que o salvar aceita de quem envia. O que não couber fica de fora."""
    origem, origem_id = dados.get("origem"), dados.get("origem_id")
    if not (isinstance(origem, str) and 0 < len(origem) <= 40 and isinstance(origem_id, str) and 0 < len(origem_id) <= 200):
        return {}
    out = {"origem": origem, "origem_id": origem_id}
    titulo_original = dados.get("titulo_original")
    if isinstance(titulo_original, str) and len(titulo_original) <= 500:
        out["titulo_original"] = titulo_original
    importado_em = dados.get("importado_em")
    if isinstance(importado_em, str) and len(importado_em) <= 40:
        out["importado_em"] = importado_em
    data = dados.get("data_original")
    if isinstance(data, dict) and all(v is None or (isinstance(v, str) and len(v) <= 40) for v in data.values()):
        out["data_original"] = {k: data.get(k) for k in ("criada", "atualizada")}
    return out


def _conversa_lida(arq: Path) -> dict | None:
    """Conteúdo do arquivo como objeto, ou None se não der para ler (sem validar o formato da conversa)."""
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dados if isinstance(dados, dict) else None


def _conversa_com_origem(origem: str, origem_id: str) -> str | None:
    """Id do arquivo que já guarda esta origem. Assim, salvar uma conversa importada não cria segundo arquivo."""
    if not CONVERSAS_DIR.is_dir():
        return None
    for arq in CONVERSAS_DIR.glob("*.json"):
        if not CONVERSA_ID.fullmatch(arq.stem):
            continue
        dados = _conversa_lida(arq)
        if dados and dados.get("origem") == origem and dados.get("origem_id") == origem_id:
            return arq.stem
    return None


def _origem_do_arquivo(anterior: dict | None) -> dict:
    """Origem já gravada no arquivo. O salvar nunca a reescreve: vale a que o arquivo já tem."""
    if not anterior or not isinstance(anterior.get("origem"), str) or not isinstance(anterior.get("origem_id"), str):
        return {}
    return {k: anterior[k] for k in ORIGEM_CAMPOS if k in anterior}


def _mensagens_com_origem(novas: list, anteriores: list) -> list:
    """Mantém 'criada' e 'origem_id' de cada mensagem que continua no mesmo lugar, com o mesmo papel e texto."""
    saida = []
    for i, m in enumerate(novas):
        velha = anteriores[i] if i < len(anteriores) and isinstance(anteriores[i], dict) else {}
        extra = {k: velha[k] for k in ("criada", "origem_id") if isinstance(velha.get(k), str)}
        if extra and velha.get("role") == m["role"] and velha.get("content") == m["content"]:
            m = {**m, **extra}
        saida.append(m)
    return saida


def _conversa_gravar(dados: dict) -> dict | None:
    limpo = _conversa_validar(dados)
    if limpo is None:
        return None
    origem = _origem_valida(dados)
    conversa_id = None
    if origem:
        conversa_id = _conversa_com_origem(origem["origem"], origem["origem_id"])
    conversa_id = conversa_id or dados.get("id") or os.urandom(6).hex()
    arq = _conversa_caminho(conversa_id)
    if arq is None:
        return None
    anterior = _conversa_lida(arq) if arq.is_file() else None
    origem_gravada = _origem_do_arquivo(anterior)
    if origem_gravada:
        origem = origem_gravada  # a origem já gravada não é reescrita
        anteriores = anterior.get("mensagens")
        limpo["mensagens"] = _mensagens_com_origem(limpo["mensagens"], anteriores if isinstance(anteriores, list) else [])
    if origem:
        limpo.update(origem)
        limpo["id"] = conversa_id  # arquivo com origem guarda o próprio id, como o importador grava
    CONVERSAS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps(_formato_gravar(limpo), ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, arq)
    return {"id": conversa_id, **limpo}


def _conversa_ler(conversa_id: str) -> dict | None:
    """Lê e valida uma conversa no contrato que o cliente exige: versão, id e conteúdo.
    Com ramos, devolve também `arvore` (nós e folha); `mensagens` é sempre o caminho ativo."""
    arq = _conversa_caminho(conversa_id)
    if arq is None or not arq.is_file():
        return None
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    limpo = _conversa_validar(dados, leve=True)
    if limpo is None:
        return None
    return {"schema_version": 1, "id": conversa_id, **limpo}


# Lixeira (09/11/2026). Apagar não apaga: move o arquivo (bytes iguais) e a entrada de organização vai junto.
# Só a purga, pedida à mão e confirmada na tela, apaga de vez. Nada apaga sozinho.

def _lixeira_caminho(nome) -> Path | None:
    if not isinstance(nome, str) or not LIXEIRA_NOME.fullmatch(nome):
        return None
    return CONVERSAS_DIR / LIXEIRA_PASTA / (nome + ".json")


def _lixeira_nome_livre(conversa_id: str) -> str:
    """<id>-<AAAAMMDD-HHMMSS>, sem repetir item da lixeira: se a mesma conversa foi apagada no mesmo segundo, sobe um segundo."""
    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
    for passo in range(3600):
        marca = (agora + timedelta(seconds=passo)).strftime("%Y%m%d-%H%M%S")
        nome = f"{conversa_id}-{marca}"
        if not _lixeira_caminho(nome).exists():
            return nome
    raise ErroConversa(500, "não foi possível guardar a conversa na lixeira; nada foi apagado")


def _quando_apagada(nome: str) -> str:
    try:
        return datetime.strptime(nome[13:], "%Y%m%d-%H%M%S").strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return "data desconhecida"


def _conversa_apagar(conversa_id: str) -> str | None:
    """Move a conversa para a lixeira, com a entrada de organização. Devolve o nome do item, ou None se não existe."""
    arq = _conversa_caminho(conversa_id)
    if arq is None or not arq.is_file():
        return None
    with _ORGANIZACAO_TRAVA:
        org, legivel = _organizacao_ler()
        if not legivel:
            raise ErroConversa(409, "organização das conversas ilegível; nada foi apagado")
        nome = _lixeira_nome_livre(conversa_id)
        try:
            _lixeira_caminho(nome).parent.mkdir(parents=True, exist_ok=True)
            os.replace(arq, _lixeira_caminho(nome))
        except OSError as erro:
            raise ErroConversa(500, "não foi possível mover a conversa para a lixeira; nada foi apagado") from erro
        entrada = org["conversas"].pop(conversa_id, None)
        if entrada is not None:
            org["lixeira"][nome] = entrada
            _organizacao_gravar(org)
    return nome


def _lixeira_nomes() -> list[str]:
    """Nomes dos itens da lixeira, pelo que está na pasta (não pela organização)."""
    pasta = CONVERSAS_DIR / LIXEIRA_PASTA
    if not pasta.is_dir():
        return []
    return [a.stem for a in pasta.glob("*.json") if LIXEIRA_NOME.fullmatch(a.stem) and a.is_file()]


def _lixeira_listar() -> dict:
    """Conversas na lixeira, mais recentes primeiro. Sem conteúdo além do título e da contagem de mensagens."""
    pasta = CONVERSAS_DIR / LIXEIRA_PASTA
    nomes = _lixeira_nomes()
    lidas = []
    for nome in nomes:
        dados = _conversa_lida(pasta / (nome + ".json"))
        if dados is not None:
            lidas.append((nome, dados))
    lidas.sort(key=lambda par: par[0][13:], reverse=True)  # AAAAMMDD-HHMMSS ordena como texto
    itens = []
    for nome, dados in lidas[:LIXEIRA_LISTA_LIMITE]:
        # Lote 4: a conta é do caminho ativo; uma conversa com ramos (arvore) apagada conta igual à de antes.
        itens.append({"nome": nome, "id": nome[:12], "titulo": str(dados.get("titulo") or "Sem título"),
                      "apagada_em": _quando_apagada(nome), "mensagens": len(_mensagens_brutas(dados))})
    return {"schema_version": 1, "state": "ok", "items": itens, "total": len(lidas), "ilegiveis": len(nomes) - len(lidas)}


def _lixeira_restaurar(nome) -> dict:
    """Devolve a conversa ao lugar dela, com a organização. Recusa se já existe conversa com o mesmo id."""
    origem = _lixeira_caminho(nome)
    if origem is None:
        raise ErroConversa(400, "item da lixeira inválido")
    conversa_id = nome[:12]
    with _ORGANIZACAO_TRAVA:
        if not origem.is_file():
            raise ErroConversa(404, "conversa não está na lixeira")
        org, legivel = _organizacao_ler()
        if not legivel:
            raise ErroConversa(409, "organização das conversas ilegível; nada foi restaurado")
        destino = _conversa_caminho(conversa_id)
        if destino.exists():
            raise ErroConversa(409, "já existe conversa com este identificador; nada foi restaurado")
        try:
            os.replace(origem, destino)
        except OSError as erro:
            raise ErroConversa(500, "não foi possível restaurar a conversa; nada foi alterado") from erro
        entrada = org["lixeira"].pop(nome, None)
        if entrada is not None:
            if entrada["pasta"] not in {p["id"] for p in org["pastas"]}:
                entrada["pasta"] = None  # a pasta pode ter sido apagada enquanto a conversa estava na lixeira
            if entrada != _entrada_padrao():
                org["conversas"][conversa_id] = entrada
        _organizacao_gravar(org)
    dados = _conversa_lida(destino) or {}
    return {"id": conversa_id, "titulo": str(dados.get("titulo") or "Sem título"), "restaurada": True}


def _lixeira_purgar(nome) -> dict:
    """Apaga de vez um item da lixeira. Só é chamada por pedido manual, depois de confirmação na tela."""
    arq = _lixeira_caminho(nome)
    if arq is None:
        raise ErroConversa(400, "item da lixeira inválido")
    with _ORGANIZACAO_TRAVA:
        if not arq.is_file():
            raise ErroConversa(404, "conversa não está na lixeira")
        org, legivel = _organizacao_ler()
        if not legivel:
            raise ErroConversa(409, "organização das conversas ilegível; nada foi apagado")
        try:
            arq.unlink()
        except OSError as erro:
            raise ErroConversa(500, "não foi possível apagar a conversa; ela continua na lixeira") from erro
        if org["lixeira"].pop(nome, None) is not None:
            _organizacao_gravar(org)
    return {"purgada": True}


# Registro de escritas (09/11/2026): uma linha por pedido de escrita, só de acréscimo. Hora, rota, id e status.
# Nunca título, texto da mensagem, marcador ou nome de pasta.

def _registro_escrever(rota: str, conversa_id, status: int) -> None:
    """Acrescenta uma linha em .registro.jsonl. Se o arquivo não puder ser escrito, a ação segue (sem linha)."""
    identificador = conversa_id if isinstance(conversa_id, str) and (
        CONVERSA_ID.fullmatch(conversa_id) or LIXEIRA_NOME.fullmatch(conversa_id)) else None
    linha = {"hora": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(timespec="seconds"),
             "rota": rota, "id": identificador, "status": status}
    try:
        CONVERSAS_DIR.mkdir(parents=True, exist_ok=True)
        with _REGISTRO_TRAVA, (CONVERSAS_DIR / REGISTRO_ARQUIVO).open("a", encoding="utf-8") as arq:
            arq.write(json.dumps(linha, ensure_ascii=False) + "\n")
    except OSError:
        pass


# Busca: texto em títulos e mensagens das conversas salvas. Ignora caixa e acento; posição preservada.

def _dobrar(texto: str) -> str:
    """Minúsculas e sem acento, letra a letra: cada caractere vira exatamente um, então a posição no texto original vale."""
    saida = []
    for c in texto:
        base = "".join(d for d in unicodedata.normalize("NFD", c) if not unicodedata.combining(d)) or c
        minusc = base.lower()
        if len(minusc) != 1:
            minusc = c.lower() if len(c.lower()) == 1 else c
        saida.append(minusc)
    return "".join(saida)


def _posicoes(texto: str, alvo: str) -> list[int]:
    saida, i = [], texto.find(alvo)
    while i >= 0:
        saida.append(i)
        i = texto.find(alvo, i + len(alvo))
    return saida


def _trecho(texto: str, inicio: int, tamanho: int) -> str:
    a = max(0, inicio - BUSCA_CONTEXTO)
    b = min(len(texto), inicio + tamanho + BUSCA_CONTEXTO)
    corte = " ".join(texto[a:b].split())
    return ("…" if a > 0 else "") + corte + ("…" if b < len(texto) else "")


def _conversas_buscar(termo) -> dict:
    limpo = " ".join(termo.split()) if isinstance(termo, str) else ""
    if not limpo:
        raise ErroConversa(400, "digite o que procurar")
    if len(limpo) > BUSCA_TERMO_LIMITE:
        raise ErroConversa(400, f"a busca aceita até {BUSCA_TERMO_LIMITE} caracteres")
    alvo = _dobrar(limpo)
    org, _ = _organizacao_ler()
    achados = []
    for arq in sorted(_conversa_arquivos(), key=lambda a: a.stat().st_mtime, reverse=True):
        try:
            dados = json.loads(arq.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(dados, dict):
            continue
        titulo = str(dados.get("titulo") or "Sem título")
        mensagens = _mensagens_brutas(dados)  # busca no caminho ativo (as versões de outros ramos não entram)
        pos_titulo = _posicoes(_dobrar(titulo), alvo)
        ocorrencias = len(pos_titulo)
        primeira = None  # (índice da mensagem, texto, posição)
        for i, m in enumerate(mensagens):
            if not isinstance(m, dict) or not isinstance(m.get("content"), str):
                continue
            pos = _posicoes(_dobrar(m["content"]), alvo)
            ocorrencias += len(pos)
            if pos and primeira is None:
                primeira = (i, m["content"], pos[0])
        if primeira is not None:
            indice, texto, posicao = primeira
            campo, mensagem, trecho = "mensagem", indice, _trecho(texto, posicao, len(alvo))
        elif pos_titulo:
            campo, mensagem, trecho = "titulo", None, _trecho(titulo, pos_titulo[0], len(alvo))
        else:
            continue
        achados.append({"id": arq.stem, "titulo": titulo, "atualizada": _atualizada(arq),
                        "arquivada": (org["conversas"].get(arq.stem) or {}).get("arquivada") is True,
                        "ocorrencias": ocorrencias, "campo": campo, "mensagem": mensagem, "trecho": trecho})
    return {"schema_version": 1, "state": "ok", "termo": limpo, "total": len(achados),
            "resultados": achados[:BUSCA_RESULTADOS_LIMITE]}


# Exportação (download pelo navegador) e importação de JSON exportado.

def _markdown(dados: dict, agora: datetime) -> str:
    titulo = " ".join(dados["titulo"].split()) or "Sem título"
    linhas = [f"# {titulo}", "", f"Modelo escolhido: {dados['modelo']}. Exportada em {agora.strftime('%d/%m/%Y %H:%M')}.", ""]
    if "arvore" in dados:
        linhas += ["Este arquivo traz só o caminho escolhido. As outras versões (ramos) estão no JSON.", ""]
    for m in dados["mensagens"]:
        if m["role"] == "user":
            cabeca = "## Você"
        else:
            if m.get("modelo_real"):
                detalhe = "modelo: " + m["modelo_real"]
            elif m.get("modelo"):
                detalhe = "modelo escolhido: " + m["modelo"]
            else:
                detalhe = "modelo não registrado"
            cabeca = f"## Seth ({detalhe})"
        linhas += [cabeca, "", m["content"], ""]
    return "\n".join(linhas)


def _conversa_exportar(conversa_id, formato) -> tuple[bytes, str, str]:
    """(corpo, nome do arquivo, tipo). O nome usa só o id (12 hex): nenhum texto do usuário vai ao cabeçalho."""
    if formato not in FORMATOS_EXPORTACAO:
        raise ErroConversa(400, "formato de exportação desconhecido (use json ou md)")
    dados = _conversa_ler(conversa_id)
    if dados is None:
        raise ErroConversa(404, "conversa não encontrada")
    org, _ = _organizacao_ler()
    origem = (org["conversas"].get(conversa_id) or {}).get("origem_id") or conversa_id
    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
    if formato == "md":
        return _markdown(dados, agora).encode("utf-8"), f"agata-conversa-{conversa_id}.md", "text/markdown; charset=utf-8"
    payload = {"formato": FORMATO_EXPORTACAO, "versao": VERSAO_EXPORTACAO, "id": conversa_id, "origem_id": origem,
               "titulo": dados["titulo"], "modelo": dados["modelo"], "mensagens": dados["mensagens"]}
    for chave in ("arvore", "ramificada_de"):  # lote 4: as versões de outros ramos e a origem da ramificação também vão no JSON
        if chave in dados:
            payload[chave] = dados[chave]
    payload["exportada_em"] = agora.isoformat(timespec="seconds")
    corpo = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return corpo, f"agata-conversa-{conversa_id}.json", "application/json; charset=utf-8"


def _id_livre() -> str:
    novo = os.urandom(6).hex()
    while (CONVERSAS_DIR / (novo + ".json")).exists():
        novo = os.urandom(6).hex()
    return novo


def _conversa_importar(dados) -> dict:
    """Importa um JSON exportado pelo painel. Reconhece a conversa pelo `id` e pelo `origem_id` do arquivo: se já
    existe aqui (como id ou como origem de outra conversa), não grava nada e devolve `ja_existe`."""
    if not isinstance(dados, dict) or dados.get("formato") != FORMATO_EXPORTACAO \
            or type(dados.get("versao")) is not int or dados.get("versao") != VERSAO_EXPORTACAO:
        raise ErroConversa(400, "o arquivo não é uma conversa exportada pelo painel (formato ou versão)")
    ids = []
    for campo in ("id", "origem_id"):
        if campo in dados:
            if not isinstance(dados[campo], str) or not CONVERSA_ID.fullmatch(dados[campo]):
                raise ErroConversa(400, "identificador da conversa inválido")
            ids.append(dados[campo])
    if not ids:
        raise ErroConversa(400, "arquivo sem identificador da conversa")
    limpo = _conversa_validar(dados)
    if limpo is None:
        raise ErroConversa(400, motivo_conversa_recusada(dados))
    origem = dados["origem_id"] if "origem_id" in dados else dados["id"]

    def alterar(org):
        locais = _conversa_ids()
        origens = {e["origem_id"]: cid for cid, e in org["conversas"].items() if e.get("origem_id")}
        # Na lixeira também conta: a conversa existe e pode ser restaurada. Importar de novo não duplica.
        # A lixeira vale o que está na pasta; a origem guardada na organização só conta para item que ainda está lá.
        presentes = set(_lixeira_nomes())
        na_lixeira = {nome[:12]: nome[:12] for nome in presentes}
        origens_lixeira = {e["origem_id"]: nome[:12] for nome, e in org["lixeira"].items()
                           if e.get("origem_id") and nome in presentes}
        for chave in ids:
            if chave in locais:
                return {"estado": "ja_existe", "id": chave, "titulo": limpo["titulo"]}
            if chave in origens:
                return {"estado": "ja_existe", "id": origens[chave], "titulo": limpo["titulo"]}
            if chave in na_lixeira:
                return {"estado": "ja_existe", "id": chave, "titulo": limpo["titulo"], "lixeira": True}
            if chave in origens_lixeira:
                return {"estado": "ja_existe", "id": origens_lixeira[chave], "titulo": limpo["titulo"], "lixeira": True}
        novo = _id_livre()
        CONVERSAS_DIR.mkdir(parents=True, exist_ok=True)
        arq = CONVERSAS_DIR / (novo + ".json")
        tmp = arq.with_suffix(".tmp")
        tmp.write_text(json.dumps(_formato_gravar(limpo), ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, arq)
        org["conversas"][novo] = {**_entrada_padrao(), "origem_id": origem}
        return {"estado": "importada", "id": novo, "titulo": limpo["titulo"]}
    return _organizacao_mudar(alterar)
