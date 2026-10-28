#!/usr/bin/env python3
"""vigia_par.py <eu> [canal.md] -- olha o canal da Equipe e diz, em uma linha, se alguém está esperando alguém demais.
Vale para qualquer membro do Conselho. Silêncio = nada a alertar. A linha NÃO traz contador de minutos (para o vigia.sh
deduplicar: uma emissão por pendência). Saídas:
  DEVO RESPOSTA: depois do meu último bloco, outro membro pôs 'Próximo responsável' = eu, parado há >= 8 min;
  SEM RESPOSTA: meu pedido a um membro (próximo = ele) segue sem bloco dele depois, parado há >= 15 min (silêncio não prova ausência).
Só leitura. Hora do bloco = linha '- Hora:' (relógio da Máquina). 'humano' não é membro: pedido ao Humano não alerta."""
import datetime, os, re, sys
eu = sys.argv[1]
canal = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/.cache/agata/sincronia/conversa.md")
def parse(b):
    cab = b.split("\n", 1)[0][3:].strip()
    m = re.search(r"^- Hora: (\S+)", b, re.M)
    prox = re.search(r"Próximo responsável:\s*([\w-]+)", b)
    try:
        t = datetime.datetime.fromisoformat(m.group(1)) if m else None
    except ValueError:
        t = None
    autor = re.match(r"^([a-z][a-z0-9-]*?)-\d{4}-\d{2}-\d{2}-", cab)  # id = <membro>-<data>-<hash>; membro pode ter hífen
    return (autor.group(1) if autor else cab.split("-", 1)[0]), cab, t, (prox.group(1) if prox else None)


try:
    blocos = [parse(b) for b in re.split(r"(?m)^(?=## )", open(canal, encoding="utf-8").read()) if b.startswith("## ")]
except OSError:
    sys.exit(0)
agora = lambda t: datetime.datetime.now(t.tzinfo)
ultimo = lambda quem: max([k for k, x in enumerate(blocos) if x[0] == quem], default=-1)
# Pendência de OUTROS comigo: o pedido MAIS ANTIGO a mim depois do meu último bloco.
ped = [x for x in blocos[ultimo(eu) + 1:] if x[0] != eu and x[3] == eu and x[2]]
if ped and (agora(ped[0][2]) - ped[0][2]).total_seconds() >= 480:
    print(f"DEVO RESPOSTA a {ped[0][0]} (>= 8 min sem eu responder; primeiro pedido em {ped[0][1]})")
# Pendência MINHA com cada membro: meu pedido mais antigo a ele depois do último bloco dele.
for alvo in sorted({x[3] for x in blocos if x[0] == eu and x[3] and x[3] not in (eu, "humano")}):
    ped = [x for x in blocos[ultimo(alvo) + 1:] if x[0] == eu and x[3] == alvo and x[2]]
    if ped and (agora(ped[0][2]) - ped[0][2]).total_seconds() >= 900:
        print(f"SEM RESPOSTA: {alvo} não responde (>= 15 min; primeiro pedido em {ped[0][1]}). Silêncio NÃO prova cota esgotada: "
              f"confirme com o Humano ou com {alvo} antes de usar `equipe.py ausente`")
