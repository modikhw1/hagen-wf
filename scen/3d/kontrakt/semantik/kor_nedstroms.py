"""kor_nedstroms.py: kör de befintliga verktygen på de genererade underlagen, bara läsande mot allt utanför semantik/ut/<klipp>/.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/semantik/kor_nedstroms.py <klipp> [--plats-skript <fil>]

1. plats.py  --scen3d underlag/scen3d_roller.json --hand underlag/hand.json --ut ut/<klipp>/plats    (vid fel och om --plats-skript anges: den patchade kopian)
2. kalla_bygg.py <ingest> ut/<klipp>/kalla/kalla.json --video --scen3d --ordtider --plats
3. bro/kort_till_kalla.tillampa_patch + till_kalla_underlag.tillampa_tillagg på en kopia av kalla, kontroll mot kalla.schema.json och kontrollera.py:s id-kontroller
Rapport: ut/<klipp>/nedstroms.json. Inga verktyg ändras; ett fel i ett verktyg rapporteras ordagrant och steget hoppas över.
"""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sem_gemensamt import HIT, ROT, SCEN, ladda, skriv, klipp_vagar  # noqa: E402
from till_kalla_underlag import tillampa_tillagg  # noqa: E402

PY = str(SCEN / '.venv/Scripts/python.exe')
KONTRAKT = HIT.parent


def kor(args, cwd=ROT):
    r = subprocess.run([PY, '-B', *map(str, args)], capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd, env={**__import__('os').environ, 'PYTHONIOENCODING': 'utf-8'})
    return dict(returkod=r.returncode, stdout=r.stdout[-1500:], stderr=r.stderr[-2500:])


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('klipp'); a.add_argument('--plats-skript'); x = a.parse_args()
    v = klipp_vagar(x.klipp); ut = v['ut']; u = ut / 'underlag'; rap = dict(klipp=x.klipp)
    plats_dir = ut / 'plats'; kalla_fil = ut / 'kalla/kalla.json'
    skript = SCEN / '3d/ingest/plats.py'
    cmd = [skript, v['ingest'], '--ut', plats_dir, '--scen3d', u / 'scen3d_roller.json', '--hand', u / 'hand.json']
    if (plats_dir / 'plats.json').exists(): rap['plats'] = dict(anm='plats.json fanns redan i utmappen; körs inte om (radera mappen för att köra om)', fil=str(plats_dir / 'plats.json'))
    else:
        r = kor(cmd); rap['plats'] = dict(skript=str(skript.relative_to(ROT)), **r)
        if r['returkod'] and x.plats_skript:
            r2 = kor([x.plats_skript, *cmd[1:]]); rap['plats_forsok_2'] = dict(skript=x.plats_skript, **r2)
    pf = plats_dir / 'plats.json'
    if not kalla_fil.exists():
        kc = [KONTRAKT / 'kalla_bygg.py', v['ingest'], kalla_fil, '--video', v['video'], '--scen3d', u / 'scen3d_roller.json']
        if (u / 'ordtider_underlag.json').exists(): kc += ['--ordtider', u / 'ordtider_underlag.json']
        else: rap['ordtider'] = 'ordtider_underlag.json saknas: kalla_bygg faller tillbaka på notans data/ordtider.json om inget anges, så steget hoppas över'
        if pf.exists(): kc += ['--plats', pf]
        if 'ordtider' in rap: rap['kalla'] = dict(hoppad=True)
        else: rap['kalla'] = kor(kc)
    else: rap['kalla'] = dict(anm='kalla.json fanns redan; körs inte om')
    if kalla_fil.exists():
        kalla = ladda(kalla_fil); patch = ladda(u / 'patch.json')
        spec = importlib.util.spec_from_file_location('kort_till_kalla', KONTRAKT / 'bro/kort_till_kalla.py'); bro = importlib.util.module_from_spec(spec); spec.loader.exec_module(bro)
        k2 = bro.tillampa_patch(kalla, patch); k3, gjort = tillampa_tillagg(k2, patch, semantik_fil=(ut / 'semantik.json').relative_to(ROT).as_posix())
        k3['revision'] = kalla['revision'] + 1
        skriv(ut / 'kalla/kalla_med_patch.json', k3)
        sys.path.insert(0, str(KONTRAKT)); from gemensamt import kontrollmodul  # noqa: E402
        mod = kontrollmodul(); schema = ladda(KONTRAKT / 'kalla.schema.json')
        fel = mod.validera(k3, schema, 'kalla', schema)
        andrade = [(s['id'], s['funktion']) for s in k3['semantik']['scener']]
        rap['patch'] = dict(schemafel=fel, scener_efter=andrade, tillagg_gjort=gjort, intention=k3['semantik']['intention'],
                            personer=[(p['id'], p['roll'], p['roll_kalla']) for p in k3['semantik']['personer']],
                            repliker_kalla_falt=sorted({r['kalla'] for r in k3['semantik']['repliker']}), roll_kalla_efter_bygg=sorted({str(p['roll_kalla']) for p in kalla['semantik']['personer']}))
    skriv(ut / 'nedstroms.json', rap)
    for k, vv in rap.items():
        if isinstance(vv, dict) and 'returkod' in vv: print(k, 'returkod', vv['returkod'], vv['stderr'][-400:] if vv['returkod'] else vv['stdout'][-160:])
    if 'patch' in rap: print('patch: schemafel', rap['patch']['schemafel'][:3], 'tillagg', len(rap['patch']['tillagg_gjort']), rap['patch']['scener_efter'])


if __name__ == '__main__':
    main()
