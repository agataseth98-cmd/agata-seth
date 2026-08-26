#!/usr/bin/env python3
from datetime import datetime, timezone, timedelta
import json
import sys

def unix_to_brasilia(unix_timestamp):
    dt_utc = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    brasilia_tz = timezone(timedelta(hours=-3))
    dt_brasilia = dt_utc.astimezone(brasilia_tz)
    return dt_brasilia.strftime('%Y-%m-%d %H:%M:%S -03')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        unix_ts = int(sys.argv[1])
        print(unix_to_brasilia(unix_ts))
    else:
        data = json.load(sys.stdin)
        unix_ts = data.get('unix_timestamp')
        if unix_ts is not None:
            print(unix_to_brasilia(unix_ts))
