"""GOLV2: jämför ut/golv2/<fore>/matning.json med <efter>/matning.json.

    scen/.venv/Scripts/python.exe scen/3d/kontrakt/engang/golv2_jamfor.py mat_fore mat_efter
Skriver ut/golv2/jamforelse.md och listar varje försämring (rot/bildfel upp, IoU ner).
"""
import sys, json
from pathlib import Path
UT = Path(__file__).resolve().parents[1] / 'ut/golv2'
fore, efter = (json.loads((UT/a/'matning.json').read_text(encoding='utf-8')) for a in sys.argv[1:3])
f2 = lambda v, d=3: '–' if v is None else f'{v:.{d}f}'
rows = ['# GOLV2 före → efter', '', f'Före: `{sys.argv[1]}` (backupträdets kod). Efter: `{sys.argv[2]}`. Samma rutor, masker, rigg och estimatorpunkter.', '',
        '**Läs så här.** Oförändrat rot-/bildfel och IoU är till stor del en matematisk följd av att kroppens gamla cam_t-skala och kamerans kompensation försvinner tillsammans. Det visar att projektionen i originalkameran är hel, inte att golvet är rätt. Det som prövar golvet är sulornas höjd över golvet per person (tabellen nedan) och personernas inbördes placering från flyttad kamera (bilderna).', '',
        '## Lägsta sula över golvet (riggens fothud, median över rutor), m', '',
        '| Klipp | Scen/person | i plan | Modellpose före → efter | Byggd pose (efter stöd) före → efter | Synliga fotrutor |', '|---|---|---|---|---|---|',
        *[f"| {k} | {r['scen']}/{r['ingest_id']} ({r['person'] or 'utelämnad'}) | {'ja' if r['i_plan'] else 'nej'} | {f2(next((o.get('sula_modell_m') for o in fore[k]['personer'] if (o['scen'],o['ingest_id'])==(r['scen'],r['ingest_id'])),None))} → {f2(r.get('sula_modell_m'))} | {f2(next((o.get('sula_byggd_m') for o in fore[k]['personer'] if (o['scen'],o['ingest_id'])==(r['scen'],r['ingest_id'])),None))} → {f2(r.get('sula_byggd_m'))} | {r['synliga_fotrutor']} |" for k in efter for r in efter[k]['personer']],
        '', '## Alla mått', '',
        '| Klipp | Scen/person | i plan | Rot px | Median px | p90 px | IoU | Kamera→rumskamera m | Kamerahöjd m | Modellfotrest m | Synlig fotrest m (rutor) | Byggd fotrest m | Höft m | Huvud m |',
        '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
samre = []
for klipp in efter:
    fo = {(r['scen'], r['ingest_id']): r for r in fore[klipp]['personer']}
    for r in efter[klipp]['personer']:
        o = fo.get((r['scen'], r['ingest_id']), {})
        def p(k, d=3): return f"{f2(o.get(k), d)} → {f2(r.get(k), d)}"
        rows.append(f"| {klipp} | {r['scen']}/{r['ingest_id']} ({r['person'] or 'utelämnad'}) | {'ja' if r['i_plan'] else 'nej'} | {p('rot_px',1)} | {p('median_px',2)} | {p('p90_px',2)} | {p('iou')} | {p('kamera_rum_avstand_m')} | {p('kamerahojd_m',2)} | {p('modellfotrest_m')} | {p('synlig_fotrest_m')} ({r['synliga_fotrutor']}) | {p('fotrest_byggd_m')} | {p('hoft_over_golv_m',2)} | {p('huvud_over_golv_m',2)} |")
        for k, sign, tol in (('rot_px', 1, .5), ('median_px', 1, .5), ('p90_px', 1, .5), ('iou', -1, .005)):
            a, b = o.get(k), r.get(k)
            if a is not None and b is not None and sign * (b - a) > tol:
                samre.append(f"- {klipp} {r['scen']}/{r['ingest_id']}: {k} {a:.3f} → {b:.3f}")
rows += ['', '## Försämringar (rot/bild > 0,5 px, IoU > 0,005)', ''] + (samre or ['Inga.'])
rows += ['', '## Förklaringar (mätta 10 nov kväll)', '',
  '- **b s3/B, IoU 0,795 → 0,773.** Samma plan mätt utan stöd (kroppmatt stod=False) ger 0,795 efter GOLV2. Fallet kommer alltså från det längdbevarande stödet för dolda ben: golvet i b S3 väljs nu av antagen kamerahöjd (förr −1,568 m ur den gamla medianen över cue-familjer, där kroppsräckvidd fick rösta), 5 cm högre relativt kroppen, och stödet böjer de dolda benen mer för att nå golvet. Silhuettkostnad för dold benpose redovisas separat enligt GOLV2.md.',
  '- **notan S4/C svävar (lägsta sula 0,112 m byggd, 0,118 m modell).** C:s fötter är utanför bilden: 0 fotpunkter i egen ruta, 0 användbara rutor. Golvet i S4 väljs av den utelämnade person 4:s synliga fötter (55 rutor, modellbedömd kontakt). Resten är en konflikt mellan två personers skattade djup, inte en uppmätt kontakt för C. Förr skalade golvsteget C:s cam_t tills foten nådde golvet och kompilatorn flyttade kameran 0,23 m för att dölja det. GOLV2 flyttar inte kroppen; stödet når inte golvet med bevarad benlängd.',
  '- **Sittande A/B i notan.** Modellens sulor ligger 0,20–0,32 m under golvet (dolda ben); efter stöd 0,000 m både före och efter. Golvet väljs av sits mot identifierad stol (antagen prior) i alla tagningar utom S4.',
  '- **b S5/C 0,514 m över golvet** både före och efter: golvet väljs av djupgolvet (MoGe, modellbedömt) och C:s ben är dolda. Oförändrat av GOLV2, men en kvarstående brist.']
for klipp in efter:
    rows += ['', f'## Objekt {klipp}', '', '| Objekt | Topp m före → efter | XY före → efter |', '|---|---|---|']
    fo = {o['id']: o for o in fore[klipp].get('objekt', [])}
    for o in efter[klipp].get('objekt', []):
        a = fo.get(o['id'], {})
        rows.append(f"| {o['id']} | {f2(a.get('topp_m'),2)} → {o['topp_m']:.2f} | {[round(x,2) for x in a.get('xy',[])]} → {[round(x,2) for x in o['xy']]} |")
(UT/'jamforelse.md').write_text('\n'.join(rows) + '\n', encoding='utf-8')
print('\n'.join(rows))
