#!/usr/bin/env python3
"""Horário de Brasília para modelos em nuvem, sem depender de `date` local.

Fonte única hoje: timeapi.io, com cache-busting (parâmetro `cachebust` na
URL força nova requisição, contorna cache de ferramentas tipo
web_extractor -- achado real em MEMÓRIAS (264)/(272)/(273)). Sem
fallback automático de segunda API: worldtimeapi.org (cotado
originalmente) foi descontinuado pelo mantenedor ("WorldTimeAPI has been
sunset") e, além disso, devolvia o timestamp na chave `unixtime`, não
`unix_timestamp` -- o fallback nunca teria funcionado mesmo com o
serviço no ar. Corrigido em MEMÓRIAS (275): sem um segundo provedor
testado e vivo pra por no lugar, o fallback real é o que REGRAS.md já
documenta (Regra 1.1, "Fallback universal"): horário informado pelo
Humano, selo `(não verificada)` -- não finge redundância que não existe.

Uso: python3 scripts/consultar_horario.py
Saída: uma linha, "AAAA-MM-DD HH:MM:SS -03 (timeapi.io)". Exit 1 e
mensagem em stderr se a API falhar -- quem chama decide o fallback.
"""
import sys
import time
import urllib.request
import json
from datetime import datetime, timezone, timedelta

URL = "https://timeapi.io/api/v1/time/current/unix"
BRASILIA = timezone(timedelta(hours=-3))


def consultar() -> str:
    cachebust = int(time.time())
    resposta = urllib.request.urlopen(f"{URL}?cachebust={cachebust}", timeout=5)
    dados = json.loads(resposta.read())
    ts = dados["unix_timestamp"]
    dt_brasilia = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(BRASILIA)
    return dt_brasilia.strftime("%Y-%m-%d %H:%M:%S") + " -03 (timeapi.io)"


if __name__ == "__main__":
    try:
        print(consultar())
    except Exception as e:
        print(f"FALHA consultando timeapi.io: {e}", file=sys.stderr)
        sys.exit(1)
