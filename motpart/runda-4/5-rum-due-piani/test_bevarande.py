"""Kontrakt för variant B: A orörd, kroppsrörelse bevarad, inga påhittade bord, antaganden märkta."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from geom import q2R, f_px, project, led_rutor
from bygg_b import sha, A_FIL

A = json.loads(A_FIL.read_text(encoding='utf-8'))
B = json.loads((HERE / 'ut/paket_B.json').read_text(encoding='utf-8'))
rec = json.loads((HERE / 'ut/recept_B.json').read_text(encoding='utf-8'))
W, H = A['bild']['bredd'], A['bild']['hojd']; ok = []

assert sha(A_FIL) == rec['a_paket_sha256'], 'A har ändrats'; ok.append('A-paketets hash oförändrad')
assert sha(HERE / 'ut/paket_B.json') == rec['b_paket_sha256']; ok.append('B matchar receptets hash')
assert not [o for o in B['objekt'] if o['typ'] == 'bord'], 'bord kvar'; ok.append('inga bord i B')
for o in B['objekt']:
    if o['id'] != 'golv' and o.get('tilltro') == 'observerad':
        raise AssertionError(f"{o['id']} påstås observerad")
ok.append('inget objekt utom golv märkt observerad')
assert all(t['kamera']['statisk'] and len(t['kamera']['nycklar']) == 1 for t in B['tagningar']); ok.append('alla B-kameror statiska')
assert [t['ut'] for t in A['tagningar']] == [t['ut'] for t in B['tagningar']]; ok.append('samma tagningsgränser')

rot = {s for s, i in rec['tagningar'].items() if 'B3' in i['regler']}
for t in B['tagningar']:
    sid = t['id']
    for p in t['personer']:
        fa, XA = led_rutor(A, p['id'], sid); fb, XB = led_rutor(B, p['id'], sid)
        assert list(fa) == list(fb)
        if sid not in rot:
            assert np.array_equal(XA, XB), (sid, p['id'])
        else:
            # Kroppens form/rörelse relativt sig själv bevarad (stel transform per tagning)
            dA = np.linalg.norm(XA - XA[:, :1], axis=2); dB = np.linalg.norm(XB - XB[:, :1], axis=2)
            assert np.abs(dA - dB).max() < 0.003, (sid, p['id'], np.abs(dA - dB).max())
ok.append('kroppsspår identiska utanför B3-tagningar; stel transform inom dem (<3 mm)')

# S10: kroppens bild genom B-kameran = genom A:s kamera vid kartläggningen (B3 utan 2D-registrering)
t = next(x for x in B['tagningar'] if x['id'] == 's10'); kA = next(x for x in A['tagningar'] if x['id'] == 's10')['kamera']['nycklar'][0]
kb = t['kamera']['nycklar'][0]
for p in t['personer']:
    _, XA = led_rutor(A, p['id'], 's10'); _, XB = led_rutor(B, p['id'], 's10')
    uA, _ = project(XA, np.array([0, 0, 1.38]), q2R(kA[4:8]), f_px(kA[8], W), W, H)
    uB, _ = project(XB, np.array(kb[1:4]), q2R(kb[4:8]), f_px(kb[8], W), W, H)
    assert np.abs(uA - uB).max() < 1.0, np.abs(uA - uB).max()
ok.append('S10: kroppens projektion oförändrad (<1 px) trots ny lodlinje')
dub = {s: i['dubbletter_bort'] for s, i in rec['tagningar'].items() if i.get('dubbletter_bort')}
print(json.dumps({'ok': ok, 'dubbletter_bort': dub, 'manuella_inslag': rec['manuella_inslag']}, ensure_ascii=False, indent=1))
