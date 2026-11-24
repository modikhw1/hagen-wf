"""Uppdrag 0017: tunn klient mot fal.ai (REST, kö), utan fal_client.

Nyckeln: första raden i fal_ai.txt i repots rot. Den skrivs aldrig ut, loggas inte och kopieras inte; fel rensas från den innan de visas.
Varje anrop sparas i <ut>/anrop.json (modell, indata utan bilddata, svar, tid) och kostnaden läggs i ../kostnad.json.
"""
import base64
import json
import mimetypes
import time
from pathlib import Path

import requests

HIT = Path(__file__).resolve().parent
ROT = HIT.parents[3]
KOSTNAD = HIT.parent / 'kostnad.json'


def _nyckel():
    return (ROT / 'fal_ai.txt').read_text(encoding='utf-8').splitlines()[0].strip()


def _h():
    return {'Authorization': 'Key ' + _nyckel()}


def _rensa(t):
    t = str(t); k = _nyckel()
    return t.replace(k, '<nyckel>').replace(k.split(':')[0], '<nyckel-id>')


def get(url, **kw):
    try:
        r = requests.get(url, headers=_h(), timeout=60, **kw)
    except Exception as e:
        raise RuntimeError(_rensa(e)) from None
    return r


def data_uri(p):
    p = Path(p); mt = mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
    return f'data:{mt};base64,' + base64.b64encode(p.read_bytes()).decode()


def ladda_upp(p):
    """Laddar upp en fil till fal:s lagring och ger en URL (för video, som är för stor som data-URI)."""
    p = Path(p); mt = mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
    try:
        r = requests.post('https://rest.alpha.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3', headers=_h(),
                          json=dict(content_type=mt, file_name=p.name), timeout=60)
        r.raise_for_status(); d = r.json()
        u = requests.put(d['upload_url'], data=p.read_bytes(), headers={'Content-Type': mt}, timeout=300); u.raise_for_status()
    except Exception as e:
        raise RuntimeError(_rensa(e)) from None
    return d['file_url']


def logga_kostnad(steg, modell, usd, grund):
    k = json.loads(KOSTNAD.read_text(encoding='utf-8')) if KOSTNAD.exists() else dict(tak_usd=6.0, tak_fal_usd=4.0, poster=[])
    k['poster'].append(dict(tid=time.strftime('%Y-%m-%dT%H:%M:%S'), steg=steg, modell=modell, usd=round(usd, 4), grund=grund))
    k['summa_usd'] = round(sum(x['usd'] for x in k['poster']), 4)
    k['summa_fal_usd'] = round(sum(x['usd'] for x in k['poster'] if not x['modell'].startswith('modal:')), 4)
    KOSTNAD.write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding='utf-8')
    return k


def summa():
    return json.loads(KOSTNAD.read_text(encoding='utf-8')) if KOSTNAD.exists() else dict(summa_usd=0, summa_fal_usd=0)


def kor(modell, indata, ut, steg, usd_uppskattat, grund, max_fal=1.85, vanta_s=1800):
    """Kör en modell via kön. Stoppar före anropet om fal-summan skulle passera max_fal (saldot på kontot)."""
    ut = Path(ut); ut.mkdir(parents=True, exist_ok=True)
    s = summa()
    if s.get('summa_fal_usd', 0) + usd_uppskattat > max_fal:
        raise RuntimeError(f'Kostnadsspärr: {s.get("summa_fal_usd", 0)} + {usd_uppskattat} > {max_fal} USD på fal')
    if (ut / 'anrop.json').exists(): raise FileExistsError(f'{ut}/anrop.json finns: kör aldrig om en generering oförändrad')
    bort = lambda v: (v[:40] + f'…({len(v)} tecken)') if isinstance(v, str) and v.startswith('data:') else v
    post = dict(modell=modell, indata={k: ([bort(x) for x in v] if isinstance(v, list) else bort(v)) for k, v in indata.items()},
                start=time.strftime('%Y-%m-%dT%H:%M:%S'))
    t = time.perf_counter()
    try:
        r = requests.post(f'https://queue.fal.run/{modell}', headers=_h(), json=indata, timeout=300)
        if r.status_code >= 300: raise RuntimeError(f'HTTP {r.status_code}: {r.text[:800]}')
        q = r.json(); post['request_id'] = q.get('request_id')
        status_url, svar_url = q['status_url'], q['response_url']
        while True:
            st = requests.get(status_url, headers=_h(), timeout=60).json()
            if st.get('status') == 'COMPLETED': break
            if time.perf_counter() - t > vanta_s: raise RuntimeError('Tidsgräns i kön')
            time.sleep(4)
        svar = requests.get(svar_url, headers=_h(), timeout=120)
        if svar.status_code >= 300: raise RuntimeError(f'HTTP {svar.status_code}: {svar.text[:1500]}')
        svar = svar.json()
    except Exception as e:
        post.update(fel=_rensa(e), sekunder=round(time.perf_counter() - t, 1))
        (ut / 'anrop.json').write_text(json.dumps(post, ensure_ascii=False, indent=1), encoding='utf-8')
        raise RuntimeError(_rensa(e)) from None
    post.update(svar=svar, sekunder=round(time.perf_counter() - t, 1))
    (ut / 'anrop.json').write_text(json.dumps(post, ensure_ascii=False, indent=1), encoding='utf-8')
    logga_kostnad(steg, modell, usd_uppskattat, grund)
    return svar


def hamta(url, mal):
    mal = Path(mal); mal.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=600); r.raise_for_status(); mal.write_bytes(r.content); return mal
