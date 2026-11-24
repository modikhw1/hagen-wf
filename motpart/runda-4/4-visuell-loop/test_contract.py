"""Preservation and real HTTP persistence checks; test feedback never enters owner data."""
import copy, importlib.util, json, tempfile, threading, unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

spec=importlib.util.spec_from_file_location('visual_loop',Path(__file__).with_name('server.py'))
loop=importlib.util.module_from_spec(spec);spec.loader.exec_module(loop)

class Contract(unittest.TestCase):
    def test_only_lens_changes_and_identity_is_exact(self):
        for key in loop.SPECS:
            original=loop.load_clip(key)['package']; pristine=copy.deepcopy(original)
            for factor in (.8,1,1.2):
                altered=loop.lens_variant(original,factor)
                self.assertEqual(altered['rorelse'],original['rorelse'])
                self.assertEqual(altered['objekt'],original['objekt'])
                for a,b in zip(original['tagningar'],altered['tagningar']):
                    for x,y in zip(a['kamera']['nycklar'],b['kamera']['nycklar']):
                        self.assertEqual(x[:8],y[:8]);self.assertEqual(y[8],x[8]*factor)
                        y[8]=x[8]
                self.assertEqual(altered,original)
            self.assertEqual(original,pristine)
            for bad in (True,False,float('nan'),float('inf'),0,2,'1'):
                with self.assertRaises(ValueError):loop.lens_variant(original,bad)

    def test_append_only_verbatim_feedback_and_range(self):
        with tempfile.TemporaryDirectory(dir=loop.HERE/'ut',prefix='contract-') as tmp:
            previous=loop.OUT;loop.OUT=Path(tmp)
            server=loop.ThreadingHTTPServer(('127.0.0.1',0),loop.Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base='http://127.0.0.1:'+str(server.server_port)
            try:
                comment='TEST — inte ägarens dom.\nÅ, ä, ö; exakt text.'
                payload={'clip':'duepiani','factor':1.15,'time':.7,'verdict':'osaker','comment':comment}
                ids=[]
                for _ in range(2):
                    req=Request(base+'/api/feedback',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
                    with urlopen(req,timeout=5) as response:ids.append(json.load(response)['id'])
                self.assertNotEqual(*ids)
                rows=[json.loads(s) for s in (loop.OUT/'svar.jsonl').read_text(encoding='utf-8').splitlines()]
                self.assertEqual(len(rows),2);self.assertTrue(all(r['comment']==comment for r in rows))
                self.assertTrue(all(r['provenance']['source_sha256'] for r in rows))
                with urlopen(Request(base+'/media/duepiani',headers={'Range':'bytes=0-31'}),timeout=5) as response:
                    self.assertEqual(response.status,206);self.assertEqual(len(response.read()),32)
                for uri in ('/../blender_token.txt','/media/unknown','/api/clip/unknown'):
                    with self.assertRaises(HTTPError) as ctx:urlopen(base+uri,timeout=5)
                    self.assertEqual(ctx.exception.code,404)
            finally:
                server.shutdown();server.server_close();thread.join();loop.OUT=previous

if __name__=='__main__':unittest.main()
