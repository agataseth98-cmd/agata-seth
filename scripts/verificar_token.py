#!/usr/bin/env python3
"""Verificação empírica do token: refresh -> criar arquivo de teste no Drive
(escopo drive.file) -> apagar. Não imprime segredo. Sai 0 se o ciclo completa.
Uso: python3 verificar_token.py
"""
import json, os, sys, urllib.parse, urllib.request

BASE = os.path.expanduser("~/.config/agata/google-project")
with open(os.path.join(BASE, "token.json")) as f:
    t = json.load(f)

# 1. refresh -> access token
data = urllib.parse.urlencode({
    "client_id": t["client_id"], "client_secret": t["client_secret"],
    "refresh_token": t["refresh_token"], "grant_type": "refresh_token",
}).encode()
req = urllib.request.Request(t["token_uri"], data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
try:
    r = json.load(urllib.request.urlopen(req, timeout=30))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print("REFRESH FALHOU:", e.code)
    if "invalid_grant" in body:
        print(">>> invalid_grant: app ficou em Testing, refresh token expira em 7 dias. "
              "Publicar o app de verdade e refazer o consentimento.")
    else:
        print(body[:300])
    sys.exit(1)
access = r["access_token"]
H = {"Authorization": f"Bearer {access}"}

# 2. criar arquivo de teste (multipart simples: metadata só, conteúdo vazio)
meta = json.dumps({"name": "agata-sistema-verificacao.txt"}).encode()
req = urllib.request.Request(
    "https://www.googleapis.com/drive/v3/files?fields=id,name",
    data=meta, headers={**H, "Content-Type": "application/json"}, method="POST")
try:
    f = json.load(urllib.request.urlopen(req, timeout=30))
except urllib.error.HTTPError as e:
    print("CRIAR FALHOU:", e.code, e.read().decode()[:300]); sys.exit(1)
fid = f["id"]
print("criar arquivo de teste: OK  (id existe:", bool(fid), ")")

# 3. apagar
req = urllib.request.Request(f"https://www.googleapis.com/drive/v3/files/{fid}",
                             headers=H, method="DELETE")
try:
    urllib.request.urlopen(req, timeout=30)
    print("apagar arquivo de teste: OK")
except urllib.error.HTTPError as e:
    print("APAGAR FALHOU (arquivo pode ter ficado):", e.code, fid); sys.exit(1)

print("\nCICLO COMPLETO: refresh -> criar -> apagar, tudo 200. Credencial funcional.")
print("consentimento em:", t.get("obtained"))
