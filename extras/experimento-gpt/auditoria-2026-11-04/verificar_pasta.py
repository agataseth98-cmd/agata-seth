"""Verifica integridade e referências da revisão documental, sem avaliar semântica."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parent
REPO = Path('/home/orusoua/agata')

def main():
    snapshot = json.loads((AUDIT / 'evidencias-iniciais.json').read_text())
    checks = []
    def check(name, ok, detail=None):
        checks.append({'item':name,'ok':bool(ok),'detalhe':detail})
    with tarfile.open(AUDIT / 'originais.tar.gz','r:gz') as tar:
        for name, info in snapshot['arquivos_antes'].items():
            stream = tar.extractfile(name)
            original = stream.read() if stream else b''
            check('copia:'+name,hashlib.sha256(original).hexdigest()==info['sha256'])
            if name == 'conclusoes.md':
                atual = (ROOT/name).read_bytes()
                check('historico_preservado',atual.startswith(original))
            if name == 'transcricao-etapa-1.txt':
                check('transcricao_preservada',(ROOT/name).read_bytes()==original)
    docs = sorted(ROOT.rglob('*.md'))
    for p in docs:
        text = p.read_text(encoding='utf-8')
        if p.name != 'conclusoes.md':
            nums = [int(n) for n in re.findall(r'^## (\d+)\.\s',text,re.M)]
            check('numeracao:'+str(p.relative_to(ROOT)),not nums or nums==list(range(1,len(nums)+1)))
        # Links controlados destes documentos: destino com ou sem <...>; ignora URLs externas.
        for match in re.finditer(r'\]\((<[^>]+>|[^)\n]+)\)',text):
            target = match.group(1).strip('<>')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):
                continue
            target = unquote(target.split('#',1)[0])
            resolved = (p.parent/target).resolve()
            check('link:'+str(p.relative_to(ROOT))+':'+target,resolved.exists())
    entradas = re.findall(r'^### (\d+) — ',(ROOT/'conclusoes.md').read_text(),re.M)
    check('ids_memoria_unicos',len(entradas)==len(set(entradas)))
    for p in AUDIT.glob('*.json'):
        try:
            json.loads(p.read_text())
            check('json:'+p.name,True)
        except (ValueError,OSError) as e:
            check('json:'+p.name,False,type(e).__name__)
    hashes = snapshot['canon_hashes']['stdout'].splitlines()
    for line in hashes:
        digest, name = line.split(maxsplit=1)
        check('canon_sem_alteracao:'+name,hashlib.sha256((REPO/name).read_bytes()).hexdigest()==digest)
    status = subprocess.run(['git','status','--short'],cwd=REPO,capture_output=True,text=True,check=True).stdout
    check('status_git_preservado',status==snapshot['status_git']['stdout'])
    head = subprocess.run(['git','rev-parse','HEAD'],cwd=REPO,capture_output=True,text=True,check=True).stdout
    check('head_preservado',head==snapshot['head']['stdout'])
    arquivo_hashes = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(ROOT.rglob('*')) if p.is_file() and p != AUDIT/'verificacao.json'}
    result = {'quando':datetime.now().astimezone().isoformat(),'escopo':'integridade e estrutura; sem garantia semântica',
              'arquivos_revisados_sha256':arquivo_hashes,
              'aprovados':sum(c['ok'] for c in checks),'total':len(checks),'checks':checks}
    (AUDIT/'verificacao.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))
    for c in checks:
        if not c['ok']:
            print('FALHA: '+c['item'])
    return 0 if all(c['ok'] for c in checks) else 1

if __name__=='__main__':
    raise SystemExit(main())
