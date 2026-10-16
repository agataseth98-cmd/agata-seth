#!/usr/bin/env python3
"""vigia_par.py <eu> [canal.md] -- olha o ÚLTIMO bloco do canal e diz, em uma linha, se alguém está esperando alguém demais.
Silêncio = nada a alertar. A linha NÃO traz contador de minutos (para o vigia.sh deduplicar: uma emissão por pendência). Saídas:
  DEVO RESPOSTA: o último bloco é do outro, 'Próximo responsável' = eu, parado há >= 8 min;
  PAR SEM RESPOSTA: o último bloco é meu, 'Próximo responsável' = o outro, parado há >= 15 min (silêncio não prova ausência).
Só leitura. Hora do bloco = linha '- Hora:' (relógio da Máquina)."""
import datetime, os, re, sys
eu = sys.argv[1]
canal = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/.cache/agata/sincronia/conversa.md")
outro = "codex" if eu == "claude" else "claude"
def parse(b):
    cab = b.split("\n", 1)[0][3:].strip()
    m = re.search(r"^- Hora: (\S+)", b, re.M)
    prox = re.search(r"Próximo responsável:\s*(\w+)", b)
    try:
        t = datetime.datetime.fromisoformat(m.group(1)) if m else None
    except ValueError:
        t = None
    return cab.split("-", 1)[0], cab, t, (prox.group(1) if prox else None)


try:
    blocos = [parse(b) for b in re.split(r"(?m)^(?=## )", open(canal, encoding="utf-8").read()) if b.startswith("## ")]
except OSError:
    sys.exit(0)
agora = lambda t: datetime.datetime.now(t.tzinfo)
# Pendência do OUTRO comigo: medida a partir do pedido MAIS ANTIGO dele (com próximo = eu) depois do meu último bloco.
ult_meu = max([k for k, x in enumerate(blocos) if x[0] == eu], default=-1)
ped = [x for x in blocos[ult_meu + 1:] if x[0] == outro and x[3] == eu and x[2]]
if ped and (agora(ped[0][2]) - ped[0][2]).total_seconds() >= 480:
    print(f"DEVO RESPOSTA a {outro} (>= 8 min sem eu responder; primeiro pedido em {ped[0][1]})")
# Pendência MINHA com o outro: meu pedido mais antigo (próximo = outro) depois do último bloco dele.
ult_dele = max([k for k, x in enumerate(blocos) if x[0] == outro], default=-1)
ped = [x for x in blocos[ult_dele + 1:] if x[0] == eu and x[3] == outro and x[2]]
if ped and (agora(ped[0][2]) - ped[0][2]).total_seconds() >= 900:
    print(f"PAR SEM RESPOSTA: {outro} não responde (>= 15 min; primeiro pedido em {ped[0][1]}). Silêncio NÃO prova cota esgotada: confirme com o Humano ou com o outro antes de usar `dupla.py ausente`")
