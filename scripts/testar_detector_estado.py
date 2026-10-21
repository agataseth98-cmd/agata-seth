"""Casos fixos do detector (M4): derivados da conversa auditada de 20/10/2026."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "redesign" / "router"))
from detector_estado_sem_prova import achados  # noqa: E402

CASOS = [
    ("endereçado sem PR deve ser achado", "O risco CAP-02 está endereçado.", True),
    ("endereçado com PR deve passar", "O risco CAP-02 está endereçado no PR #406.", False),
    ("confiança 99% deve ser achada", "Confiança: 99% no diagnóstico.", True),
    ("Hermes ativo deve ser achado", "O Hermes está ativo no sistema.", True),
    ("Hermes com marcação de remoção passa", "O Hermes foi removido (312).", False),
    ("texto neutro passa", "Não medido nesta rodada.", False),
]

falhas = 0
for nome, texto, deve_achar in CASOS:
    tem = bool(achados(texto))
    ok = tem == deve_achar
    falhas += 0 if ok else 1
    print(("PASSOU" if ok else "FALHOU"), "-", nome)
print("SUITE OK" if falhas == 0 else f"SUITE FALHOU ({falhas})")
sys.exit(1 if falhas else 0)
