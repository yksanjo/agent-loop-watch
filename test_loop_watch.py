import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from loop_watch import inspect, load, MAX_BYTES

A = {'tool': 'fixture_read', 'arguments': {'id': 1}, 'result': {'status': 'waiting'}}
B = {'tool': 'fixture_check', 'arguments': {}, 'result': None}

class Tests(unittest.TestCase):
    def test_empty(self): self.assertFalse(inspect([])['review_required'])
    def test_short(self): self.assertFalse(inspect([A,A])['review_required'])
    def test_single(self): self.assertEqual(inspect([A]*3)['period'],1)
    def test_alternating(self): self.assertEqual(inspect([A,B]*3)['period'],2)
    def test_longer(self): self.assertEqual(inspect([A,B]*5)['repetitions'],5)
    def test_prefix(self): self.assertEqual(inspect([B]+[A]*4)['start_index'],1)
    def test_not_suffix(self): self.assertFalse(inspect([A]*3+[B])['review_required'])
    def test_changed_result(self):
        changed=copy.deepcopy(A);changed['result']={'status':'done'}
        self.assertFalse(inspect([A,A,changed])['review_required'])
    def test_changed_args(self):
        changed=copy.deepcopy(A);changed['arguments']['id']=2
        self.assertFalse(inspect([A,A,changed])['review_required'])
    def test_key_order(self):
        changed=dict(reversed(list(A.items())))
        self.assertTrue(inspect([A,changed,A])['review_required'])
    def test_period_cap(self):self.assertFalse(inspect([A,B]*3,max_period=1)['review_required'])
    def test_threshold(self):self.assertFalse(inspect([A]*3,repeats=4)['review_required'])
    def test_invalid(self):
        for value in [None,{},[{}],[dict(A,extra=1)],[A]*1001]:
            with self.assertRaises(ValueError):inspect(value)
    def test_settings(self):
        for kw in [{'repeats':1},{'repeats':True},{'max_period':33}]:
            with self.assertRaises(ValueError):inspect([],**kw)
    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'trace.json'
            for data,code in [(json.dumps([A]*3).encode(),1),(b'[]',0),
                              (b'[{"tool":"a","tool":"b"}]',2),
                              (b'['*2000+b'0'+b']'*2000,2),
                              (b'\xff',2),(b' '*(MAX_BYTES+1),2)]:
                p.write_bytes(data)
                r=subprocess.run([sys.executable,str(Path(__file__).with_name('loop_watch.py')),str(p)],capture_output=True,text=True,timeout=5)
                self.assertEqual(r.returncode,code,r.stderr)
                self.assertEqual(r.stderr,'')
                json.loads(r.stdout)

if __name__=='__main__':unittest.main()
