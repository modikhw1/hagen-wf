import sys
from pathlib import Path
sys.path.insert(0,str(Path('scen/3d/ingest').resolve()))
from sakra_filer import sakerhetskopiera
def edit(path,old,new):
 p=Path(path);s=p.read_text(encoding='utf-8')
 if old not in s:raise ValueError(f'{p}: {old[:100]}')
 sakerhetskopiera(p);p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
R='scen/3d/ingest/rum.py'
edit(R,"focal=float(np.load(next(ut.glob('sekvens_*.npz')))['fokal'])", "seqfile=next(ut.glob('sekvens_*.npz'), None)\n    focal=float(np.load(seqfile)['fokal']) if seqfile else max(M['bredd'], M['hojd'])")
edit(R,"        for name in ['depth','gemini','detections_gemini.json','detections.json']:", "        old = json.loads(manifest.read_text())\n        source_changed = any(old.get(k) != raw_signature.get(k) for k in ('source', 'source_bytes', 'source_mtime'))\n        for name in (['depth','gemini','detections_gemini.json','detections.json'] if source_changed else ['depth']):")
edit(R,"            if p.is_dir():shutil.rmtree(p)\n            else:p.unlink(missing_ok=True)", "            from sakra_filer import arkivera\n            arkivera(p)")
edit(R,"    det=detect(clip,ut)", "    # Geometriförändring kräver nytt djup men inte nya bilddetektioner.\n    # Nätanrop för Gemini är uttryckligt avstängbara, även inne i rumsteget.\n    if os.environ.get('HAGEN_NO_GEMINI') == '1' and not (ut / 'rum/detections_gemini.json').exists():\n        det=[]\n    elif os.environ.get('HAGEN_NO_GEMINI') == '1':\n        det=json.loads((ut / 'rum/detections_gemini.json').read_text())\n    else: det=detect(clip,ut)")
edit(R,"np.concatenate(roots))", "np.concatenate(roots) if roots else None)")
edit(R,"    overlay(clip,ut,M,V,focal,objects)", "    room['kunskap'] = dict(status='modellbedomd' if walls or objects else 'saknas', orsak='Ytor ur modelldjup och befintliga detektioner.' if walls or objects else 'Inga stödda ytor. Tom utdata betyder okänt rum, inte tom lokal.')\n    overlay(clip,ut,M,V,focal,objects)")

# Återanvända sekvenser får också utsnittsdiagnos, utan ny kroppskostnad.
F='scen/3d/ingest/flera/ingest_flera.py'
edit(F,"om = 'kropp' if invalid else ('varld' if x.regler else None)", "om = 'kropp' if invalid else ('sekvens' if x.regler and fp else 'varld' if x.regler else None)")
# Semantik-klippregistret kan ligga i ingestmappen för ett nytt mp4.
edit(F,"        sf = hitta(ut, x.semantik)", "        sf = hitta(ut, x.semantik)\n        if sf is None and (ut / 'semantik/semantik.json').exists(): sf = ut / 'semantik/semantik.json'")
