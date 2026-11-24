"""Tester som inte anropar Gemini. MOCK-svaren här är påhittade och används bara för att pröva kod (validering, avvisning, ordtidsmatchning,
omvandling). De skrivs till en temporär mapp och är aldrig utvärderingsdata.

    scen/.venv/Scripts/python.exe -B scen/3d/kontrakt/semantik/test_semantik.py
"""
import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import semantik_ingest as si  # noqa: E402
import ordtider_klipp as ok_  # noqa: E402
from sem_gemensamt import validera, ladda, HIT  # noqa: E402

K = 'hog'
MOCK = dict(
    klipp=dict(sprak='sv', tal_finns=True, sammanfattning='MOCK', karna='MOCK', konfidens=K),
    personer=[dict(id='P1', beskrivning='MOCK', roll='woman', spar=[dict(tagning='S1', spar_id='1', konfidens=K), dict(tagning='S4', spar_id='4', konfidens=K)], konfidens=K),
              dict(id='P2', beskrivning='MOCK', roll='man', spar=[dict(tagning='S2', spar_id='1', konfidens=K)], konfidens=K)],
    ej_personer=[dict(tagning='S4', spar_id='1', typ='bakgrundsperson', skal='MOCK', konfidens=K)],
    kamerauppstallningar=[dict(id='K1', tagningar=['S1', 'S3'], beskrivning='MOCK', konfidens=K)],
    par=[dict(a='P1', b='P2', vander_mot_varandra='ja', over='separata_bord', tagningar=['S1'], kommentar='MOCK', konfidens=K)],
    plats=dict(typ='restaurang_matsal', beskrivning='MOCK', rumsmall_forslag='notan_tva_bord', motivering='MOCK', konfidens=K),
    placeringar=[dict(person='P1', hallning='sitter', ankartyp='sate', vid_del='bord', beskrivning='MOCK', tagningar=['S1'], konfidens=K)],
    repliker=[dict(id='r1', talare='P1', tagning='S1', text='Men vadå, menar du att du inte ska betala notan?', sprak='sv', start_s=0.0, slut_s=2.2, talare_i_bild='ja', konfidens=K)],
    skarmtext=[], props=[],
    tagningar=[dict(tagning='S1', funktion='krok', vad='MOCK', konfidens=K)],
)


def svar(d):
    return dict(candidates=[dict(content=dict(parts=[dict(text=json.dumps(d))]), finishReason='STOP')])


def main():
    schema = ladda(HIT / 'semantik.schema.json')
    assert validera(MOCK, schema) == [], validera(MOCK, schema)
    # 1. schemafel avvisas
    d = copy.deepcopy(MOCK); d['klipp']['konfidens'] = 'kanske'; del d['plats']
    f = validera(d, schema); assert any('kanske' in x for x in f) and any('saknar plats' in x for x in f), f
    # 2. mot mätningen: ett spår som inte finns, ett spår som används två gånger, en okänd talare
    v, data = si.skottar('notan')
    d = copy.deepcopy(MOCK); d['personer'][0]['spar'].append(dict(tagning='S1', spar_id='9', konfidens=K)); d['repliker'][0]['talare'] = 'P7'
    fel, var = si.kontrollera_mot_matning(d, data)
    assert any('S1:9' in x for x in fel) and any('P7' in x for x in fel), fel
    d = copy.deepcopy(MOCK); d['ej_personer'].append(dict(tagning='S1', spar_id='1', typ='annat', skal='MOCK', konfidens=K))
    fel, _ = si.kontrollera_mot_matning(d, data); assert any('två gånger' in x for x in fel), fel
    # 3. ett komplett men ofullständigt svar godkänns med varningar om saknade spår/tagningar
    fel, var = si.kontrollera_mot_matning(MOCK, data); assert not fel, fel
    assert any('S3:1' in x for x in var) and any('S7 saknar' in x for x in var), var
    # 4. behandla_svar skriver semantik.json för giltigt och avvisat.json för ogiltigt, och ändrar inget i mätdata
    with tempfile.TemporaryDirectory() as t:
        ok, p = si.behandla_svar(svar(MOCK), 'notan', data, {}, None, 'MOCK-modell', t, ursprung_typ='mock_test')
        assert ok and p.name == 'semantik.json' and json.loads(p.read_text(encoding='utf-8'))['ursprung']['typ'] == 'mock_test'
    with tempfile.TemporaryDirectory() as t:
        bad = copy.deepcopy(MOCK); bad['tagningar'][0]['funktion'] = 'mittpunkt'
        ok, p = si.behandla_svar(svar(bad), 'notan', data, {}, None, 'MOCK-modell', t, ursprung_typ='mock_test')
        assert not ok and p.name == 'avvisat.json' and 'mittpunkt' in p.read_text(encoding='utf-8')
        ok, p = si.behandla_svar('{ inte json', 'notan', data, {}, None, 'MOCK-modell', t, ursprung_typ='mock_test'); assert not ok
        trunk = svar(MOCK); trunk['candidates'][0]['finishReason'] = 'MAX_TOKENS'
        ok, p = si.behandla_svar(trunk, 'notan', data, {}, None, 'MOCK-modell', t, ursprung_typ='mock_test'); assert not ok
    # 5. ordmatchning: rätt rad stöds, påhittad rad flaggas, ordning bevaras
    ord_ = [dict(w=w, start=i * .3, end=i * .3 + .25, p=.9) for i, w in enumerate('men vad å menar du att du inte ska betala notan'.split())]
    rader = [dict(id='r1', text='Men vadå, menar du att du inte ska betala notan?'), dict(id='r2', text='Det här har ingenting med ljudet att göra alls')]
    res, ofork = ok_.justera(rader, ord_)
    assert res[0]['stodd'] and res[0]['start_s'] == 0.0 and res[0]['tackning'] > .8, res[0]
    assert not res[1]['stodd'] and res[1]['start_s'] is None, res[1]
    print('alla tester ok')


if __name__ == '__main__':
    main()
