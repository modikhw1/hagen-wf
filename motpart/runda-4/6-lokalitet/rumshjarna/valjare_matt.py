"""CPU-mått mot Geminis fria text, med gemensam och granskningsbar instansnyckel.

Kör --spara fore före ändring/körning och sedan --jamfor fore efter körning.
Nyckeln följer ordningen i varje 'viktigast'. Mellanslag betyder OCH, | ELLER,
- saknad meningsfull instans. Sammanslagna kärl/table godtas när Gemini pekar
ut deras avgränsade motiv; mat uppslukad av wall/person får ingen egen träff.
Detta mäter urval av befintliga instanser, inte rätt etikett, handroll eller brus.
En tagning utan något mätbart krav särredovisas, aldrig som en tom fullträff.
Huvudmåttet behåller alla 38 tagningar i nämnaren (utan krav räknas som miss);
andelen bland enbart mätbara tagningar visas också.
Klippspecifika ID finns ENDAST här i facitnyckeln, aldrig i väljaren.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UT = ROOT / 'ut' / 'rumshjarna'
FACIT = ROOT / 'ut' / 'agy' / 'rumshjarna' / 'valjare_granskning.json'
# Manuellt operationaliserat från viktigast + ratt/saknas; samma krav i båda leden.
# Miljöpunkternas uttryckliga delmotiv (t.ex. vägg OCH lampa OCH golv) krävs alla
# när en identifierbar instans finns; vilken av flera likvärdiga lampor som väljs
# spelar ingen roll. Detta är en redovisad tolkning av fri text, inget nytt modellfacit.
# Delar utan egen instans inom en sammansatt punkt utvärderas inte.
NYCKEL = {
    'duepiani': [
        ['person#2', '-', 'wall#4', 'rug#1'],
        ['plate#1', 'person#2', 'table#3'],
        ['person#2', 'plate#4', 'wall#1', 'floor#3'],
        ['person#4', '-', 'stove#1', 'ceiling#6', 'wall#5'],
        ['person#2', '-', 'stove#4', 'ceiling#5', 'wall#1'],
        ['person#3', '-', 'stove#6', 'ceiling#8', 'wall#1'],
        ['person#3', '-', 'stove#5', 'ceiling#7', 'wall#1'],
        ['-', '-', '-', '-'],
        ['person#6', '-', 'stove#2', 'hood#4', 'wall#1'],
        ['plate#1', 'plate#1', 'table#3', 'table#3'],
        ['person#5', 'plate#14', 'person#5', 'stove#13', 'wall#1 ceiling#15'],
        ['person#2', 'tray#4', 'cabinet#6', 'stove#7', 'wall#1'],
    ],
    'spanjorskan': [
        ['person#16', 'food#7', 'table#30', 'plate#3 glass#26 bottle#37', 'wall#4'],
        ['food#2', 'tray#10', 'table#9', 'glass#1 plate#4'],
        ['person#14', 'food#41 food#33', 'table#31', 'glass#23', 'wall#2'],
    ],
    '08burgerkebab': [
        ['person#9', 'tray#4', '-', 'shelf#8 ceiling#12', 'wall#11 bottle#1|bottle#3|bottle#6|bottle#7'],
        ['person#3', 'cabinet#5', 'tray#8', '-', 'wall#1 window#2'],
        ['person#4', 'tray#7', 'bottle#8', 'stove#9 ceiling#10', 'wall#1'],
        ['person#5', 'tray#21 tray#20 tray#2', '-', 'tray#8', 'wall#1|wall#23'],
        ['person#3', 'tray#18 food#11', '-', '-', 'box#10'],
        ['person#4', 'tray#6 food#7', '-', 'counter#9', 'box#5 wall#1'],
        ['person#7', 'tray#27 food#26', '-', 'case#19', 'box#25 wall#24'],
        ['ceiling#5', 'light#1', 'person#3'],
        ['food#1', 'tray#2', 'table#3'],
        ['person#3', 'tray#5', 'stove#7', 'wall#1 floor#4'],
        ['person#4', 'tray#6', 'cabinet#8 hood#7', 'wall#1'],
    ],
    'babasburgers': [
        ['person#5', 'tray#18 tray#9 food#10', 'table#16', 'wall#2 stairway#8 lamp#19|lamp#3'],
        ['food#4 tray#7', 'bottle#2', 'table#8', 'person#3', 'bottle#2'],
        ['tray#3', 'tray#3', 'tray#2'],
        ['tray#2', 'bottle#4', 'tray#3'],
        ['person#4', 'tray#1', 'table#14', 'tray#11', 'wall#16 rail#3 lamp#12'],
        ['-', '-', '-', 'tray#1'],
        ['table#2', 'bottle#1', '-', 'tray#3'],
        ['person#8', 'tray#18', 'tray#2', 'table#24', 'floor#20 wall#1 lamp#4'],
        ['tray#5 tray#4', 'tray#5', '-', 'tray#4'],
        ['person#3', 'tray#10', 'food#2 tray#5', 'table#9', 'wall#11 floor#7 lamp#8|lamp#12'],
        ['person#4', 'tray#7', 'food#3', 'table#14', 'wall#15 lamp#2|lamp#12'],
    ],
    'kennysgelato2.0': [
        ['person#8', 'bed#9', 'floor#2', '-', 'wall#1 door#7'],
    ],
}


def las(root):
    return {k: json.loads((root / k / 'valjare.json').read_text(encoding='utf-8')) for k in NYCKEL}


def mat(data, facit):
    resultat = defaultdict(lambda: {'traff': 0, 'matbara': 0, 'utan_krav': [], 'tagningar': []})
    for r in facit:
        k, sid = r['klipp'], r['sid']
        krav = NYCKEL[k][int(sid[1:]) - 1]
        assert len(krav) == len(r['viktigast']), (k, sid, 'facit har ändrats')
        t = data[k]['tagningar'][sid]
        # Kontrollera även ej valda krav: ID/etikett måste finnas i originalets instanslista.
        alla = {f"{p['etikett']}#{p['instans']}" for key in ('rangordning', 'rum_klass', 'overlagg') for p in t[key]}
        valda = {f"{p['etikett']}#{p['instans']}" for p in t['minsta_mangd']}
        saknas = []
        for text, uttryck in zip(r['viktigast'], krav):
            if uttryck == '-':
                continue
            for term in uttryck.split():
                alt = set(term.split('|'))
                assert alt <= alla, (k, sid, 'ogiltig facitnyckel', alt - alla)
                if not alt & valda:
                    saknas.append({'viktigast': text, 'instanser': term})
        har_krav = any(x != '-' for x in krav)
        resultat[k]['matbara'] += har_krav
        resultat[k]['traff'] += har_krav and not saknas
        if not har_krav:
            resultat[k]['utan_krav'].append(sid)
        resultat[k]['tagningar'].append({'sid': sid, 'tacker': har_krav and not saknas, 'saknas': saknas,
                                        'antal_valda': len(valda),
                                        'utan_instans': [v for v, x in zip(r['viktigast'], krav) if x == '-']})
    return dict(resultat)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--spara', metavar='NAMN', help='spara oförändrade valjare.json som före-underlag')
    ap.add_argument('--jamfor', metavar='NAMN', help='jämför mot sparat underlag')
    args = ap.parse_args()
    for namn in (args.spara, args.jamfor):
        if namn and (Path(namn).name != namn or namn in ('.', '..')):
            ap.error('NAMN måste vara ett enkelt katalognamn')
    facit = json.loads(FACIT.read_text(encoding='utf-8'))
    nu = las(UT)
    assert len({(r['klipp'], r['sid']) for r in facit}) == sum(map(len, NYCKEL.values())), 'ofullständigt eller dubbelt facit'
    if args.spara:
        dst = UT / 'matt' / args.spara
        if dst.exists():
            ap.error(f'{dst} finns redan; skriv inte över före-underlaget')
        for k in NYCKEL:
            (dst / k).mkdir(parents=True)
            shutil.copyfile(UT / k / 'valjare.json', dst / k / 'valjare.json')
    resultat = {'facit_sha256': hashlib.sha256(FACIT.read_bytes()).hexdigest(),
                'nyckel': NYCKEL, 'efter': mat(nu, facit),
                'sha_efter': {k: d['kod_sha256'] for k, d in nu.items()}}
    if args.jamfor:
        fore = las(UT / 'matt' / args.jamfor)
        resultat.update(fore=mat(fore, facit), sha_fore={k: d['kod_sha256'] for k, d in fore.items()})
        # Blandade gamla körningar syns uttryckligen; efter måste komma från en enda kodversion.
        sha = hashlib.sha256((ROOT / 'rumshjarna' / 'valjare.py').read_bytes()).hexdigest()[:16]
        assert set(resultat['sha_efter'].values()) == {sha}, 'kör om alla klipp med nuvarande väljare'
        for k in NYCKEL:
            assert fore[k]['kallor'] == nu[k]['kallor'], (k, 'indata har ändrats sedan före-körningen')
    for k, r in resultat['efter'].items():
        prefix = ''
        n = len(r['tagningar'])
        if 'fore' in resultat:
            f = resultat['fore'][k]; prefix = f"{f['traff']}/{n} ({100*f['traff']/n:.1f} %) -> "
        print(f"{k}: {prefix}{r['traff']}/{n} ({100*r['traff']/n:.1f} %); mätbara {r['matbara']}; utan krav: {r['utan_krav']}")
    for fas in ('fore', 'efter'):
        if fas in resultat:
            antal = sum(r['traff'] for r in resultat[fas].values())
            n = sum(r['matbara'] for r in resultat[fas].values())
            val = [t['antal_valda'] for r in resultat[fas].values() for t in r['tagningar']]
            print(f"{fas} totalt: {antal}/{len(val)} ({100*antal/len(val):.1f} %); enbart mätbara {antal}/{n} ({100*antal/n:.1f} %); medel antal valda {sum(val)/len(val):.2f}")
    (UT / 'matt').mkdir(exist_ok=True)
    (UT / 'matt' / 'resultat.json').write_text(json.dumps(resultat, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
