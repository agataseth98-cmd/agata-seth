"""Objetos sintéticos; não executa serviço ou escreve canon real."""
import importlib.util, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
with patch.dict(os.environ,{'SETH_REPO':str(ROOT)}):
 spec=importlib.util.spec_from_file_location('escriba',ROOT/'redesign/router/seth_escriba.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Locks(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
  self.p=Path(self.t.name)/'alvo.md';self.p.write_text('antes')
 def test_inode_stays_after_target_replaced(self):
  with m._travar_arquivo(self.p):
   lock=self.p.with_name('alvo.md.lock');ino=lock.stat().st_ino
   m._escreve_atomico(self.p,'depois')
  with m._travar_arquivo(self.p):self.assertEqual(lock.stat().st_ino,ino)
 def test_lock_symlink_rejected(self):
  other=Path(self.t.name)/'segredo';other.write_text('intacto')
  self.p.with_name('alvo.md.lock').symlink_to(other)
  with self.assertRaises(OSError):
   with m._travar_arquivo(self.p):self.fail('aceitou symlink')
  self.assertEqual(other.read_text(),'intacto')
 def test_lock_fifo_rejected(self):
  os.mkfifo(self.p.with_name('alvo.md.lock'))
  with self.assertRaises(RuntimeError):
   with m._travar_arquivo(self.p):self.fail('aceitou FIFO')
 def test_target_symlink_rejected_at_open(self):
  self.p.unlink();other=Path(self.t.name)/'segredo';other.write_text('intacto');self.p.symlink_to(other)
  with self.assertRaises(OSError):
   with m._travar_arquivo(self.p):self.fail('aceitou symlink')
  self.assertEqual(other.read_text(),'intacto')
 def test_diary_bootstrap_and_append(self):
  diario=Path(self.t.name)/'DIARIO.md'
  with patch.object(m,'DIARIO',diario):m._anota_diario('primeira');m._anota_diario('segunda')
  s=diario.read_text();self.assertIn('primeira',s);self.assertIn('segunda',s)
  self.assertLess(s.index('segunda'),s.index('primeira'))
if __name__=='__main__':unittest.main(verbosity=2)
