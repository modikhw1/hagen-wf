"""Återanvänd identiska diagnostikresultat inom samma process, högst 32 poster."""
from prop_filer import andra

wrapper='''

# Källfiler, geometri, tidsurval och mätkamera ingår i nyckeln. Färg och props
# påverkar inte kroppsmåttet. Bara små sammanfattningar cachas, aldrig hudnät.
_MATT_CACHE = {}

def _matt_nyckel(plan, stod):
    import hashlib
    import json
    scener = plan.get('scener') or plan.get('matkamera', {}).get('scener') or []
    sources = set(); geometry = []
    for sc in scener:
        ds = {k: sc[k] for k in ('id','ut','lokal_start','till_plats','varld') if k in sc}
        ds['personer'] = []
        sources.add(str(sc['varld']))
        for pm in sc['personer']:
            ds['personer'].append({k: pm[k] for k in ('id','ingest_id','rorelse','stod','benlangder_m','skyddade_knan','till_plats') if k in pm})
            file = Path(pm['rorelse']); folder = file.parent; pid = str(pm.get('ingest_id') or file.stem[8:])
            sources.add(str(file))
            sources.update(str(folder / n) for n in ('masker.npy','personer.json',f'palitlig_{pid}.json',f'bildskydd_{pid}.json'))
            sources.update(str(p) for p in (folder/'kropp'/pid).glob('*.npz'))
        geometry.append(ds)
    stamps=[]
    for name in sorted(sources):
        p=Path(name)
        stat=p.stat() if p.exists() else None
        stamps.append((name, stat.st_mtime_ns if stat else None, stat.st_size if stat else None))
    key=dict(scener=geometry, filer=stamps, stod=stod, flerklipp=bool(plan.get('scener')),
             kallrutor=plan['kallrutor'], kamera=plan.get('matkamera',plan.get('renderkamera')),
             bredd=plan['kallbild_bredd'], hojd=plan.get('kallbild_hojd'), utdata=plan['utdata'])
    return hashlib.sha256(json.dumps(key,sort_keys=True,allow_nan=False).encode('utf-8')).digest()

def matt_plan(plan, stod=True):
    """Samma fulla mått som utan cache. Ändrad kamera/geometri/filstämpel ger ommätning."""
    import copy
    key=_matt_nyckel(plan,stod)
    if key not in _MATT_CACHE:
        result=_matt_plan_utan_cache(plan,stod)
        if len(_MATT_CACHE)>=32: _MATT_CACHE.pop(next(iter(_MATT_CACHE)))
        _MATT_CACHE[key]=copy.deepcopy(result)
    return copy.deepcopy(_MATT_CACHE[key])
'''
andra('scen/3d/kontrakt/kroppmatt.py',lambda s:s.replace('def matt_plan(plan, stod=True):','def _matt_plan_utan_cache(plan, stod=True):',1)+wrapper)
andra('scen/3d/kontrakt/engang/prop_verifiera.py',lambda s:s.replace("log=out/'prov.log';result=out/'prov.json'", "tag=sys.argv[1] if len(sys.argv)>1 else 'prov'\nlog=out/(tag+'.log');result=out/(tag+'.json')"))
andra('scen/3d/kontrakt/test_kroppmatt.py',lambda s:s.replace("if __name__ == '__main__':",'''class Matcache(unittest.TestCase):
    def test_cache_ogiltig_vid_fil_kamera_och_stod(self):
        import copy
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='matcache_',dir=HIT/'ut') as td:
            folder=Path(td);file=folder/'sekvens_1.npz';file.write_bytes(b'initial')
            sc=dict(id='s1',ut=[0,1],lokal_start=0,varld=str(folder/'varld.npz'),personer=[dict(id='A',ingest_id='1',rorelse=str(file))])
            p=dict(scener=[sc],kallrutor=[0],kallbild_bredd=576,utdata=dict(bredd=576,hojd=1024),matkamera=dict(nycklar=[dict(lins_mm=36,matris=np.eye(4).tolist())]))
            K._MATT_CACHE.clear()
            with patch.object(K,'_matt_plan_utan_cache',return_value=[dict(matt=1)]) as measure:
                first=K.matt_plan(p);first[0]['matt']=999
                self.assertEqual(K.matt_plan(p),[dict(matt=1)]);self.assertEqual(measure.call_count,1)
                file.write_bytes(b'changed file size');K.matt_plan(p);self.assertEqual(measure.call_count,2)
                p['matkamera']['nycklar'][0]['lins_mm']=40;K.matt_plan(p);self.assertEqual(measure.call_count,3)
                p['scener'][0]['personer'][0]['stod']=dict(hojd_m=.75);K.matt_plan(p);self.assertEqual(measure.call_count,4)
                K.matt_plan(p,False);self.assertEqual(measure.call_count,5)
            K._MATT_CACHE.clear()


if __name__ == '__main__':'''))
