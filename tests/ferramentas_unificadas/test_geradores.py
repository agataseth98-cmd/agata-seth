"""Testes extra (fora dos AC-01 a AC-15): gerador de hook que edita o home do Humano, sempre com home temporária.

O gerador só grava com --aplicar. Copia o original para backup 600 antes de gravar e não duplica.
(O gerador da denylist saiu deste lote, Alto 2 da revisão: fica para o lote 2 junto com R4 final.)
"""
from __future__ import annotations

import json
import stat

import instalar_hook_arranque as IH


def _settings(home):
    return home / ".claude" / "settings.json"


def test_hook_arranque_idempotente_e_preserva(tmp_path):
    home = tmp_path / "h"
    _settings(home).parent.mkdir(parents=True)
    original = {"model": "x", "hooks": {"SessionStart": [{"matcher": "startup", "hooks": [
        {"type": "command", "command": "bash outro.sh", "timeout": 5}]}]}}
    _settings(home).write_text(json.dumps(original), encoding="utf-8")
    saida: list[str] = []
    assert IH.executar(home, aplicar=False, imprimir=saida.append) == 0
    assert json.loads(_settings(home).read_text()) == original, "sem --aplicar não pode gravar"

    assert IH.executar(home, aplicar=True, imprimir=saida.append) == 0
    novo = json.loads(_settings(home).read_text())
    assert novo["model"] == "x"
    grupos = novo["hooks"]["SessionStart"]
    assert len(grupos) == 2 and grupos[0] == original["hooks"]["SessionStart"][0]
    assert "agata-arranque/SKILL.md" in grupos[1]["hooks"][0]["command"]
    codex = home / ".codex" / "hooks.json"
    assert codex.exists() and "agata-arranque/SKILL.md" in codex.read_text()
    backups = list((home / ".local" / "share" / "agata" / "ferramentas" / "backup").iterdir())
    assert backups, "sem cópia do original"
    copia = next(p for p in backups[0].iterdir() if p.name == "claude.json")
    assert stat.S_IMODE(copia.stat().st_mode) == 0o600

    # segunda rodada: nada a fazer, nada duplicado
    assert IH.executar(home, aplicar=True, imprimir=saida.append) == 0
    assert len(json.loads(_settings(home).read_text())["hooks"]["SessionStart"]) == 2


