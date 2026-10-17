#!/usr/bin/env python3
"""Contratos de recuperação da janela; tarefas e diretórios sintéticos, sem serviço/modelo."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
S = importlib.util.spec_from_file_location('janela', Path(__file__).with_name('janela_manutencao.py'))
j = importlib.util.module_from_spec(S); S.loader.exec_module(j)
NOW = dt.datetime(2026, 10, 17, 12, 20, tzinfo=j.TZ)
TASK = {'id':'a','cadence':'daily','budget_seconds':1,'env':{},'precond':[],'cmd':['true']}

def main():
    checks = {}
    def test(name, body):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td); calls = []
            def runner(t,p): calls.append(t['id']); return 'success',False
            def cycle(**kwargs):return j.ciclo(d,[TASK],kwargs.pop('runner',runner),lambda: NOW,**kwargs)
            checks[name] = bool(body(d,calls,cycle))
    def corrupt(d,calls,cycle):
        cycle(); (d/'state.json').write_text('{broken'); cycle()
        return calls==['a'] and list(d.glob('state.json.corrompido-*'))
    test('sucesso reconstruído após corrupção, sem repetir',corrupt)
    def missing(d,calls,cycle):
        cycle(); (d/'state.json').unlink(); cycle();return calls==['a']
    test('estado perdido reconstruído por recibos',missing)
    def after_effect(d,calls,cycle):
        with patch.object(j,'estado_atomico',side_effect=OSError('disk')):
            try:cycle()
            except OSError:pass
        r=cycle()
        rows=[json.loads(x) for x in (d/'receipts.jsonl').read_text().splitlines()]
        return r=='complete' and calls==['a','a'] and any(x.get('reconciled_interrupted') for x in rows)
    test('queda no meio da tarefa: conta tentativa e a janela segue',after_effect)
    def queda_dois_dias_seguidos(d,calls,cycle):
        for _ in range(2):
            with patch.object(j,'estado_atomico',side_effect=OSError('disk')):
                try:cycle()
                except OSError:pass
        r=cycle()
        return r=='complete' and calls==['a','a']
    test('limite de 2 tentativas vale também para execuções interrompidas',queda_dois_dias_seguidos)
    def final_failed(d,calls,cycle):
        def receipt(p,r):
            if r['phase']=='finished':raise OSError('disk')
            j.recibo_duravel(p,r)
        cycle(recibo=receipt);cycle()
        rows=[json.loads(x) for x in (d/'receipts.jsonl').read_text().splitlines()]
        return calls==['a'] and sum(x['phase']=='finished' for x in rows)==1
    test('estado conclusivo recupera recibo final perdido',final_failed)
    def final_and_state_lost(d,calls,cycle):
        def receipt(p,r):
            if r['phase']=='finished':raise OSError('disk')
            j.recibo_duravel(p,r)
        cycle(recibo=receipt);(d/'state.json').write_text('{bad')
        r=cycle()
        rows=[json.loads(x) for x in (d/'receipts.jsonl').read_text().splitlines()]
        return r=='complete' and calls==['a','a'] and any(x.get('reconciled_interrupted') for x in rows)
    test('sem estado nem término: tratada como interrompida, 1 tentativa contada (não inventa sucesso)',final_and_state_lost)
    def broken_journal(d,calls,cycle):
        cycle();(d/'receipts.jsonl').open('a').write('{partial')
        return cycle()=='blocked' and calls==['a']
    test('recibo truncado bloqueia',broken_journal)
    def failed_rebuild(d,calls,cycle):
        def bad(t,p):calls.append(t['id']);return 'failed',False
        cycle(runner=bad);cycle(runner=bad);(d/'state.json').unlink();cycle(runner=bad)
        return calls==['a','a']
    test('limite de tentativas sobrevive à perda do estado',failed_rebuild)
    def skip_rebuild(d,calls,cycle):
        def skip(t,p):calls.append(t['id']);return 'skipped',False
        cycle(runner=skip);(d/'state.json').unlink();cycle(runner=skip)
        return calls==['a']
    test('skipped esgota dia mesmo sem estado',skip_rebuild)
    def unsupported(d,calls,cycle):
        (d/'state.json').write_text('{bad');return cycle()=='blocked' and calls==[]
    test('corrupção sem prova não libera tarefas',unsupported)
    def invalid_shape(d,calls,cycle):
        cycle();(d/'state.json').write_text('{"a":[]}');cycle();return calls==['a']
    test('estado com estrutura inválida recupera recibos',invalid_shape)
    def contradiction(d,calls,cycle):
        cycle();rs=[json.loads(x) for x in (d/'receipts.jsonl').read_text().splitlines()];r=next(x for x in rs if x['phase']=='finished');r['result']='failed';j.recibo_duravel(d/'receipts.jsonl',r)
        return cycle()=='blocked' and calls==['a']
    test('recibos contraditórios não permitem execução',contradiction)
    got=j.executar(dict(TASK,cmd=[sys.executable,'-c','print("linha 1");print("2026-10-17 12:17: 15 exemplo(s) real(is) novo(s) (mínimo 20) -- sem treino esta semana")'],budget_seconds=5),5)
    checks['saída final do comando vai ao resultado (motivo do pulo visível)']=got[0]=='success' and got[2]=='2026-10-17 12:17: 15 exemplo(s) real(is) novo(s) (mínimo 20) -- sem treino esta semana'
    got=j.executar(dict(TASK,cmd=[sys.executable,'-c','print("token "+"A"*40+" fim")'],budget_seconds=5),5)
    checks['sequência longa (token) é redigida na saída final']=got[2]=='token [redigido] fim'
    got=j.executar(dict(TASK,cmd=[sys.executable,'-c','print("x"*500)'],budget_seconds=5),5)
    checks['saída final é cortada em 200 caracteres']=len(got[2] or '')<=200
    got=j.executar(dict(TASK,cmd=[sys.executable,'-c','import sys;print("falhou assim");sys.exit(3)'],budget_seconds=5),5)
    checks['comando que falha: resultado failed e a última linha guardada']=got[0]=='failed' and got[2]=='falhou assim'
    def com_saida(d,calls,cycle):
        cycle(runner=lambda t,p:('success',False,'motivo X'))
        rows=[json.loads(x) for x in (d/'receipts.jsonl').read_text().splitlines()]
        return any(x.get('saida_final')=='motivo X' for x in rows if x.get('phase')=='finished')
    test('recibo final traz saida_final quando o executor a devolve',com_saida)
    t0=time.monotonic()
    got=j.executar(dict(TASK,precond=[sys.executable,'-c','import time;time.sleep(.3)'],cmd=[sys.executable,'-c','import time;time.sleep(.3)']),.4)
    checks['prazo único cobre precondição e comando']=got[:2]==('failed',True) and time.monotonic()-t0<1.3
    got=j.executar(dict(TASK,precond=[sys.executable,'-c','import time;time.sleep(5)']),.1)
    checks['precondição em timeout é skipped (não gasta tentativa de falha)']=got==('skipped',False)
    # Falha transitória de leitura não autoriza remover a evidência antiga.
    for name,ok in checks.items():print(('PASS  ' if ok else 'FALHA ')+name)
    print(f'janela recuperação: {sum(checks.values())}/{len(checks)}')
    return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())
