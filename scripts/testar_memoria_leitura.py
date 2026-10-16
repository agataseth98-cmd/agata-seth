"""Provas offline do candidato; nenhuma rede, canon real ou cache real."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import struct
from types import SimpleNamespace
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
SOURCE = ROOT / 'scripts/busca_semantica.py'
spec = importlib.util.spec_from_file_location('candidate', SOURCE)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class _Vector:
 """Stub só para contrato de consulta; não testa precisão ou API NumPy."""
 def __init__(self, values): self.values=list(values)
 def tobytes(self): return struct.pack('<'+'f'*len(self.values),*self.values)
 def __matmul__(self, other): return sum(a*b for a,b in zip(self.values,other.values))

class ReadContract(unittest.TestCase):
 def setUp(self):
  # Só os vetores sintéticos importam aqui; CI não instala dependência numérica.
  numpy_stub=SimpleNamespace(asarray=lambda values,dtype=None:_Vector(values),frombuffer=lambda raw,dtype=None:_Vector(struct.unpack('<'+'f'*(len(raw)//4),raw)))
  p=patch.dict(sys.modules,{'numpy':numpy_stub});p.start();self.addCleanup(p.stop)
  self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
  self.cache=Path(self.tmp.name)/'cache';self.cache.mkdir()
  self.index=self.cache/'indice-v2.json'
  self.e={'num':1,'titulo':'Retenção','data':'16/10/2026','linhas':['Preservar todas as fontes.']}
  self.vector=m._b64([1.,0.])
  self.vectors={m._h(m.texto_entrada(self.e)):self.vector}
  self.index.write_text(json.dumps({'versao':2,'modelo':m.MODELO,'vetores':self.vectors}))
  for key,value in [('CACHE_DIR',str(self.cache)),('INDICE_V2',str(self.index))]:
   p=patch.object(m,key,value);p.start();self.addCleanup(p.stop)
  p=patch.object(m,'_todas_entradas_todas_camadas',return_value=([self.e],[]));p.start();self.addCleanup(p.stop)
  p=patch.object(m,'docs_extras',return_value=[]);p.start();self.addCleanup(p.stop)
  self.update_original=m.atualizar
  p=patch.object(m,'atualizar',side_effect=AssertionError('consulta tentou manter índice'));self.maintenance=p.start();self.addCleanup(p.stop)
  def embed(texts,prefix):
   self.assertEqual((texts,prefix),(['pergunta'],'query'))
   return [[1.,0.]]
  p=patch.object(m,'_embed',side_effect=embed);self.embed=p.start();self.addCleanup(p.stop)
 def run_query(self):
  err=io.StringIO()
  with contextlib.redirect_stderr(err): result=m.buscar_dados('pergunta',blocos=False)
  return result,err.getvalue()
 def test_no_maintenance_or_index_write(self):
  before=self.index.read_bytes();rs,w=self.run_query()
  self.assertEqual(before,self.index.read_bytes());self.maintenance.assert_not_called()
  self.assertEqual(rs[0]['num'],1);self.assertEqual(w,'')
 def test_missing_cache_not_created(self):
  self.index.unlink();self.cache.rmdir();rs,w=self.run_query()
  self.assertEqual(rs,[]);self.assertIn('AVISO',w);self.assertFalse(self.cache.exists());self.embed.assert_not_called()
 def test_empty_index_warns(self):
  self.index.write_text('{"versao":2,"vetores":{}}');rs,w=self.run_query()
  self.assertEqual(rs,[]);self.assertIn('AVISO',w)
 def test_corrupt_json_preserved(self):
  self.index.write_bytes(b'{broken');rs,w=self.run_query()
  self.assertEqual(rs,[]);self.assertIn('AVISO',w);self.assertEqual(self.index.read_bytes(),b'{broken')
 def test_partial_index_returns_existing(self):
  other=dict(self.e,num=2,titulo='Novo texto')
  with patch.object(m,'_todas_entradas_todas_camadas',return_value=([self.e,other],[])):
   rs,w=self.run_query()
  self.assertEqual([r['num'] for r in rs],[1]);self.assertIn('índice parcial',w)
 def test_unindexed_sources_not_reported_absent(self):
  self.index.write_text(json.dumps({'versao':2,'vetores':{'unrelated':self.vector}}))
  rs,w=self.run_query();self.assertEqual(rs,[]);self.assertIn('incompletos',w)
 def test_json_stdout_stays_list(self):
  out=io.StringIO()
  with contextlib.redirect_stdout(out):m.buscar('pergunta',10,como_json=True)
  result=json.loads(out.getvalue());self.assertIsInstance(result,list)
  self.assertEqual(set(result[0]),{'tipo','num','bloco','score','titulo','data','trecho'})
 def test_json_missing_index_stdout_and_stderr(self):
  self.index.unlink();out=io.StringIO();err=io.StringIO()
  with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):m.buscar('pergunta',10,como_json=True)
  self.assertEqual(json.loads(out.getvalue()),[]);self.assertIn('AVISO',err.getvalue())
 def test_json_partial_stdout_and_stderr(self):
  other=dict(self.e,num=2,titulo='Texto recém-escrito sem vetor')
  out=io.StringIO();err=io.StringIO()
  with patch.object(m,'_todas_entradas_todas_camadas',return_value=([self.e,other],[])),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):m.buscar('pergunta',10,como_json=True)
  self.assertEqual([x['num'] for x in json.loads(out.getvalue())],[1]);self.assertIn('índice parcial',err.getvalue())
 def test_explicit_update_still_writes(self):
  self.index.unlink()
  with patch.object(m,'_itens',return_value=[('fixture','texto')]),patch.object(m,'_embed_seguro',return_value=[[1.,0.]]):
   self.assertEqual(self.update_original(silencioso=True),(1,1,True))
  self.assertTrue(self.index.exists())

if __name__=='__main__':unittest.main(verbosity=2)
