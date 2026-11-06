"""Fotografia de auditoria: GETs locais e comandos de leitura; não gera inferência."""
from __future__ import annotations
import hashlib
import json
import subprocess
import tarfile
import urllib.request
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent
EXPERIMENTO = PASTA.parent
REPO = Path('/home/orusoua/agata')

def comando(*args):
    try:
        p = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=20)
        return {'argv': list(args), 'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {'argv': list(args), 'erro': type(e).__name__}

def get(url, selecionar):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return {'url': url, 'status': r.status, 'dados': selecionar(json.load(r))}
    except Exception as e:
        return {'url': url, 'erro': type(e).__name__, 'status': getattr(e, 'code', None)}

def main():
    alvo = PASTA / 'evidencias-iniciais.json'
    if alvo.exists():
        raise SystemExit('Snapshot existente: não sobrescrito.')
    arquivos = sorted(p for p in EXPERIMENTO.rglob('*') if p.is_file() and PASTA not in p.parents)
    hashes = {str(p.relative_to(EXPERIMENTO)): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
              'bytes': p.stat().st_size} for p in arquivos}
    with tarfile.open(PASTA / 'originais.tar.gz', 'x:gz') as tar:
        for p in arquivos:
            tar.add(p, arcname=str(p.relative_to(EXPERIMENTO)), recursive=False)
    dados = {
        'quando': datetime.now().astimezone().isoformat(),
        'escopo': 'metadados de leitura; sem chaves, sem POST, sem teste de geração',
        'arquivos_antes': hashes,
        'head': comando('git','rev-parse','HEAD'),
        'status_git': comando('git','status','--short'),
        'canon_hashes': comando('sha256sum','REGRAS.md','PROTOCOLOS.md','FALHAS.md','PROJETO.md','MEMÓRIAS.md','AGENTS.md'),
        'portas': comando('ss','-ltn'),
        'servicos': comando('systemctl','--user','show','omniroute.service','omniroute-sanitizer.service',
             'seth-gateway.service','seth-escriba.service','seth-verificador.service','openvino-embeddings.service',
             'laya-roteador.service','painel-operacional.service','-p','Id','-p','ActiveState','-p','SubState'),
        'ollama': get('http://127.0.0.1:11434/api/tags',lambda d: [
            {k:m.get(k) for k in ('name','digest','size','details')} for m in d.get('models',[])]),
        'catalogo_remoto': get('http://127.0.0.1:20128/api/models',lambda d: [
            {k:m.get(k) for k in ('fullModel','provider','available','supportsVision')} for m in d.get('models',[])]),
        'rotas_expostas': get('http://127.0.0.1:20128/v1/models',lambda d: [
            {k:m.get(k) for k in ('id','owned_by')} for m in d.get('data',[])]),
        'combos': get('http://127.0.0.1:20128/api/combos',lambda d: [
            {'name': c.get('name'), 'strategy':c.get('strategy'),
             'models':[m.get('model') for m in c.get('models',[]) if isinstance(m,dict)]}
             for c in d.get('combos',[])]),
    }
    alvo.write_text(json.dumps(dados,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'quando':dados['quando'],'arquivos_preservados':len(arquivos),
        'ollama':len(dados['ollama'].get('dados',[])),
        'catalogo_remoto':len(dados['catalogo_remoto'].get('dados',[])),
        'rotas_expostas':len(dados['rotas_expostas'].get('dados',[])),
        'combos_seth':[c for c in dados['combos'].get('dados',[]) if c['name'].startswith('seth')]
        },ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
