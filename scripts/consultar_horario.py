#!/usr/bin/env python3
import urllib.request, json, time
from datetime import datetime, timezone, timedelta

apis = [
    ("timeapi.io", "https://timeapi.io/api/v1/time/current/unix"),
    ("worldtimeapi.org", "http://worldtimeapi.org/api/timezone/America/Sao_Paulo"),
]

brasilia_tz = timezone(timedelta(hours=-3))

for nome, url in apis:
    try:
        cachebust = int(time.time())
        url_final = f"{url}?cachebust={cachebust}"
        response = urllib.request.urlopen(url_final, timeout=5)
        data = json.loads(response.read())
        if "unix_timestamp" in data:
            ts = data["unix_timestamp"]
            dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
            dt_brasilia = dt_utc.astimezone(brasilia_tz)
            print(f"{dt_brasilia.strftime(chr(37)+chr(89)+chr(45)+chr(37)+chr(109)+chr(45)+chr(37)+chr(100)+chr(32)+chr(37)+chr(72)+chr(58)+chr(37)+chr(77)+chr(58)+chr(37)+chr(83))} -03 ({nome})")
            exit(0)
    except Exception as e:
        continue

print("Nenhuma API disponível")
exit(1)
