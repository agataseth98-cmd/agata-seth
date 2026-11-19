#!/usr/bin/env python3
"""Verificação de locutor (canal de voz). Interface; na fase 1 não verifica ninguém.

`verificar(pcm)` devolve um de: "verificado", "rejeitado", "nao_verificado". Na fase 1 devolve sempre
"nao_verificado": o canal opera só em modo conversa e nada com efeito é aceito por voz. A fase 2 (ECAPA-TDNN,
speechbrain no venv igpu, perfil em ~/.local/share/agata/humanos/<marca>/voz/) troca o corpo desta função sem
mudar quem chama. Mesmo "verificado" nunca autoriza ação com efeito (decisão D5a do Humano, 18/11/2026).
"""
from __future__ import annotations

VERIFICADO = "verificado"
REJEITADO = "rejeitado"
NAO_VERIFICADO = "nao_verificado"


def verificar(pcm: bytes) -> str:  # noqa: ARG001 — fase 1: sem modelo
    return NAO_VERIFICADO
