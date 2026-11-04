import tempfile,unittest
from pathlib import Path
from compresso.memoryd import load_config,validate,MemoryErrorSafe
class Tests(unittest.TestCase):
 def test_defaults(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(load_config(Path(d)/"none")["PROFILE"],"zram-fast")
 def test_unknown(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"c";p.write_text("NOPE=1")
   with self.assertRaises(MemoryErrorSafe):load_config(p)
 def test_duplicate(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"c";p.write_text("PROFILE=zram-fast\nPROFILE=hybrid-exp")
   with self.assertRaises(MemoryErrorSafe):load_config(p)
 def test_bad_percent(self):
  c={"PROFILE":"zram-fast","DISKSIZE_PERCENT":"101","MEM_LIMIT_PERCENT":"20","ZSWAP_PERCENT":"5","SWAP_PRIORITY":"100","DEVICE":"/dev/zram0","ALLOW_EXISTING_SWAP":"false","ALGORITHM":"lz4","BACKING_SWAP":""}
  with self.assertRaises(MemoryErrorSafe):validate(c)
 def test_zswap_requires_backend(self):
  c={"PROFILE":"zswap-first","DISKSIZE_PERCENT":"50","MEM_LIMIT_PERCENT":"20","ZSWAP_PERCENT":"5","SWAP_PRIORITY":"100","DEVICE":"/dev/zram0","ALLOW_EXISTING_SWAP":"false","ALGORITHM":"lz4","BACKING_SWAP":""}
  with self.assertRaises(MemoryErrorSafe):validate(c)
if __name__=="__main__":unittest.main()