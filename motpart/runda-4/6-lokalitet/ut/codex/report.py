"""Rebuild report tables from measured evidence; never changes source/results outside codex."""
from pathlib import Path
import csv, json
import numpy as np
from scipy.stats import spearmanr

OUT=Path(__file__).resolve().parent
KEYS=['duepiani','spanjorskan','08burgerkebab','babasburgers','kennysgelato2.0']
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
def save(name,text): (OUT/name).write_text(text,encoding='utf-8')
def num(v,n=1): return '—' if v is None else f'{v:.{n}f}'

rows=sum([read('vp-'+k+'.json') for k in KEYS],[])
good=[r for r in rows if r['pitch'] is not None]
errors=[r['delta'] for r in good]
cmed=spearmanr([np.median(r['spread']) for r in good],errors)
cmax=spearmanr([max(r['spread']) for r in good],errors)
bad=[r for r in good if r['delta']>10]
assert len(rows)==38 and len(good)==24 and not bad
stats={'shots':len(rows),'estimated':len(good),'missing':len(rows)-len(good),'median_error':float(np.median(errors)),
       'max_error':max(errors),'over_10_degrees':bad,
       'spearman_median':{'rho':float(cmed.statistic),'p':float(cmed.pvalue)},
       'spearman_max':{'rho':float(cmax.statistic),'p':float(cmax.pvalue)}}
save('statistics.json',json.dumps(stats,ensure_ascii=False,indent=2))

intro='''# Motprov 3–4: oberoende bildlinjer och spridningsdiagnos

Kör från `6-lokalitet/`, ett kommando åt gången:

```powershell
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py frames
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py duepiani
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py spanjorskan
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py 08burgerkebab
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py babasburgers
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py kennysgelato2.0
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/vp.py --selftest
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/diagnosis_injection.py
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/report.py
```

Alla 114 nyckelrutor hämtades ur originalvideorna i `data/format/kontroll/klipp/` enligt `obs_gpu.json`. Videornas SHA256 kontrollerades mot metadata. Originalbilderna ligger i `frames/`; linjer och accepterade inliers visas i `vp-images/` och kontaktkartorna nedan. Samtliga kontaktkartor granskades visuellt.

OpenCV LSD hittar raka segment. Manuellt valda bildregioner begränsar urvalet till synliga vertikaler, framför allt väggar, fönster, dörrar, skåp och upprätta föremål. Regionen och varje segments pixelkoordinater sparas i `vp-<klipp>.json` och i skriptet. Detta är ett manuellt granskat motprov, inte ett nytt autonomt ingestlöfte. Varken `lutning_grader`, MoGe-normaler, GeoCalib-gravitation, kroppsbål eller rapportens ”cirka −25°” används i anpassningen. Målutdata läses separat för jämförelsen.

Geometrin: segmentets mittpunkt `(x,y)` normaliseras med kamerans fokal; dess bildlutning `a=dx/dy` ger ekvationen `u_x + (a*y-x)*u_z = -a` med `u_y=-1`. Robust linjekonsensus följs av vinkelanpassning; `pitch=asin(u_z/||u||)`, negativt nedåt. Flyktpunkter i oändligheten kan representeras. Fokalen tas ur `lins_mm.anvand`, med samma virtuella 36 mm-sensor som systemet; vittnet är därför oberoende av gravitationsskattningen men **villkorat på dess intrinsik**, inte en oberoende objektivkalibrering. Huvudpunkt i bildcentrum, kvadratiska pixlar och försumbar linsdistorsion antas. Fokalen varieras även ±20 % i råresultaten och tabellen.

Grindar: längd minst 40 px (25 px för korta kakelfogar i Due Piani S9/S11/S12), riktning inom 35° från bildvertikalen, dublettkanter inom 6 px/0,5° samlas, inlierfel <0,8°, minst fem inlierlinjer över minst 25 % av bildbredden. Bootstrap med 150 återdragningar får ha högst 10° brett 95 %-intervall. Frön är fasta (829 och 54). Tagningens siffra är medianen av minst två godkända rutor; en enda ruta räcker inte. Bootstrap gäller slumpvariation hos linjerna och täcker inte systematiskt fel eller felmärkt linjefamilj.

Visuell prövning underkände babasburgers S10:s numeriskt starka positiva VP: inliers satt på lutande stolsben, kläder och skärmar. S11 saknar också tillräckliga säkra vertikaler. Råhypoteserna finns kvar men räknas inte som kamerafel. Matnärbildernas bordskanter, avsmalnande kärl och enstaka burkar får inte ersätta ett saknat vertikalvittne. Due Piani S9 är tvetydig: 25/40 px linjelängd ger −13,3/−4,5° i ruta 399 och −14,7/−6,7° i ruta 416. Endast ruta 433 återstår; inget tagningsvärde godtas. Ändringar efter bildgranskning gäller vittnets linjeurval, aldrig ingestens utdata.

Kameran rör sig dessutom i flera intervall som ingesten kallar statiska: tydlig taksvepning i 08burgerkebab S8 ruta 513, bordsvy i Spanjorskan S1 ruta 165 och kraftigt annan vy i kennysgelato S1 ruta 412. Dessa rutor saknar här godkänd VP; tagningarnas median är inte en verifiering av hela intervallet.

'''
intro+=f'Utfall: **{len(good)}/38 tagningar mätbara, 14 saknar tillräckligt vittne. Inga accepterade tagningsmedianer eller enskilda accepterade rutor avviker över 10°.** Median absolutavvikelse {num(np.median(errors))}°, största {num(max(errors))}° (Due Piani S7). De 14 luckorna är inte godkända vinklar.\n\n'
intro+='| Klipp/tagning | Rutor | Ingest ° | VP ° per godkänd ruta | VP-median ° | Absolut avvikelse ° | Median med fokal −20/+20 % | Saknat/anmärkning |\n|---|---|---:|---|---:|---:|---|---|\n'
frame_rows=[]
for r in rows:
    valid=[f for f in r['frames'] if f['valid']]
    vals=', '.join(str(f['frame'])+': '+num(f['pitch']) for f in valid) or 'saknas'
    sens='—' if r['pitch'] is None else '/'.join(num(float(np.median([f['focal_sensitivity'][i] for f in valid]))) for i in [0,1])
    reason=r['missing_reason'] or ('Endast en robust ruta; VP-kandidater parameterkänsliga.' if r['pitch'] is None else '')
    if r['clip']=='08burgerkebab' and r['shot']=='s8': reason='Ruta 513: taksvep, VP saknas.'
    if r['clip']=='spanjorskan' and r['shot']=='s1': reason='Ruta 165: bordsnärbild, VP saknas.'
    if r['clip']=='kennysgelato2.0': reason='Ruta 412: ändrad vy, VP saknas.'
    intro+=f'| {r["clip"]} {r["shot"].upper()} | '+', '.join(str(f['frame']) for f in r['frames'])+f' | {num(r["target_pitch"])} | {vals} | {num(r["pitch"])} | {num(r["delta"])} | {sens} | {reason} |\n'
    for f in r['frames']:
        frame_rows.append({'clip':r['clip'],'shot':r['shot'],'frame':f['frame'],'valid':f['valid'],
                           'pitch':f.get('pitch'),'target':r['target_pitch'],
                           'abs_difference':abs(f['pitch']-r['target_pitch']) if f['valid'] else None,
                           'reason':f['reason'],'ci95':f.get('ci95'),'vp_px':f.get('vp_px')})
with (OUT/'RUTOR.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=frame_rows[0].keys()); w.writeheader(); w.writerows(frame_rows)

intro+='\n**Diagnosen:** `lokalitet.py:721–726` mäter vinkeln mellan varje rutas MoGe-lod och den gemensamma MoGe-loden, före fusion. Listan är inte standardavvikelsen hos slutlig `lutning_grader`. Saknade per-rutelodlinjer utelämnas dessutom; listans index är därför inte alltid ett frame-id. `fusera_lodlinje`, rader 407–432, använder medianen, minst 3°, som MoGe-σ.\n\n'
intro+='| Verkligt exempel | spridning_per_ruta_grader | Median/max ° | Avvikelse mot VP ° | Vad exemplet visar |\n|---|---|---|---:|---|\n'
for key,sid,meaning in [('duepiani','s3','Båda små.'),('duepiani','s1','Maxspridning mycket stor, slutvinkelfelet litet.'),('spanjorskan','s1','Medianspridning stor, slutvinkelfelet under 10°.'),('08burgerkebab','s8','Stor maxspridning sammanfaller med verklig kamerarörelse; mittvittnet saknas.'),('duepiani','s7','Liten spridning trots störst uppmätt tagningsavvikelse.')]:
    r=next(r for r in rows if r['clip']==key and r['shot']==sid)
    intro+=f'| {key} {sid.upper()} | {r["spread"]} | {num(np.median(r["spread"]))}/{num(max(r["spread"]))} | {num(r["delta"])} | {meaning} |\n'
intro+=f'''\nNågot belagt exempel där både stor spridning och ett VP-fel >10° föreligger finns **inte** i denna ögonblicksbild. Babasburgers S6 har [68,5; 92,1; 0,1]° men saknar VP, så dess fel kan inte anges. Rapportens äldre babasburgers S1 med −46° och 32–34° spridning beskriver tidigare tagningsgränser; aktuella utdata är −13,3° och [0,8; 0,3; 0,7]°. Det gamla exemplet kan inte användas som aktuellt testresultat.

I de 24 mätbara tagningarna är Spearman ρ={num(cmed.statistic,3)} (p={num(cmed.pvalue,3)}) för medianspridning och ρ={num(cmax.statistic,3)} (p={num(cmax.pvalue,3)}) för maxspridning mot absolut slutvinkelfel. Inget tillförlitligt samband beläggs här; urvalet saknar de svåra närbilderna och är inte ett kalibreringsmaterial. En svag positiv korrelation ska inte beskrivas som bevis för att inget samband kan finnas.

**Körbar falsifiering:** `diagnosis_injection.py` exekverar de oförändrade funktionerna `dominant_axel` och `lodlinje` från AST:n och injicerar samma 30° normalbias i tre syntetiska rutor. Rätt lod har spridning [0;0;0]° och fel 0°; fel lod har också [0;0;0]° men fel 30°. Därmed faller spridning som ensam absolut tillförlitlighetsgaranti. Testet prövar MoGe-diagnosen; fusion med ett annat vittne kan fortfarande korrigera biasen. Se [diagnosis-injection.json](diagnosis-injection.json).

Vittnets egen geometrikontroll passerade för kända vinklar −50°, −15°, 0° och +15° (inklusive flyktpunkt i oändligheten). En injicerad avvikelse 15° utlöste jämförelsegrinden >10°: [vp-selftest.json](vp-selftest.json). Kontrollen kalibrerar inte verkliga kamerors fokal eller linsdistorsion.

Bildbevis, tre nyckelrutor per rad:

'''
for key in KEYS:
    sheets=sorted(OUT.glob(f'vp-{key}-[123].jpg'))
    intro+='- '+key+': '+', '.join(f'[{p.stem}]({p.name})' for p in sheets)+'\n'
intro+='\nAlla 114 rutor och avslagsorsaker: [RUTOR.csv](RUTOR.csv). Exakta pixelkoordinater, inliers, bootstrapintervall och fokalkänslighet: `vp-<klipp>.json`.\n'
save('LODLINJE.md',intro)

feet=read('feet.json')
ft='''# Motprov 5: fotkontakt i Due Piani

Kört från `6-lokalitet/`:

```powershell
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py basic
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/feet_injection.py
```

**Nio tagningar har exakt `kamerahojd.m == kamerahojd.fotter_m`, till lagrad millimeterprecision.** I samtliga är skalkällan `fotkontakt`. Det är en konstruktionsidentitet. Dessutom sätter S2 höjden direkt från fötterna utan något uppmätt golv. S8/S10 har varken fotmått eller golvhöjd och antar 1,40 m.

| Tagning | m | fotter_m | m − fotter_m | fot_over_golv_m per person | Skalkälla | Kontaktskala / personyteskala | Höjd med enbart personyteskala, cirka m |
|---|---:|---:|---:|---|---|---|---:|
'''
for r in feet:
    h=r['height']; sc=r['scale']; foot=', '.join(f'{p}: {v:.3f}' for p,v in r['feet'].items()) or 'saknas'
    ft+=f'| {r["shot"].upper()} | {h["m"]:.3f} | {num(h.get("fotter_m"),3)} | {num(r["height_minus_feet"],3)} | {foot} | {sc["kalla"]} | {sc["varde"]:.3f} / {num(sc.get("personyta_skulle_ge"),3)} | {num(r["height_with_surface_scale"],3)} |\n'
ft+='''
Källkedjan i `lokalitet.py`:

- Rader 735–741: medianavståndet `G` till det oskalade MoGe-golvet beräknas.
- Rader 742–745: `F = median(-min(J_left·u, J_right·u) + 0,08)` för stående, godkända kroppsspår. Fotledens antagna sulavstånd är 8 cm.
- Rader 746–749: personytans skala ersätts av `s = F/G`; den gamla skalan sparas endast i `personyta_skulle_ge`.
- Rader 751–762: samma golvpunkter ger `h = median(G_i*s) = F`. Därmed är källtexten `golv (MoGe)` ingen oberoende bekräftelse av kroppens fothöjd.
- Rader 756–776: `fotter_m` är åter samma fotberäkning; utan golv väljs `h=F` direkt (S2).
- Rader 777–815: kropparna roteras och flyttas med denna kamera. För ett ensamt stödbärande spår blir medianen av den lägre fotleden `h + median(min(J·u)) = 0,08 m` per konstruktion. Vid flera spår gäller tvånget deras poolade median, inte varje person eller varje ruta.

`fot_over_golv_m=0,080` mäter fotledens median, inte ett oberoende avstånd från skosulan till golvbilden. S1:s spår B ligger 0,284 m över golvet; det är uttryckligen uteslutet från höjd/skala med `spar_utan_2d_stod=[B]` och 409,4 px ursprungligt spårfel. S1 A är det spår som tvingas till 0,080 m. Måttet är inte heller en maxkontroll över hela animationen. `lokalitet.json` beräknas före L7:s gemensamma rumstransform (rader 848–871); tabellen gäller dessa lokala höjddiagnoser.

**Oberoende stöd:** inga uppmätta fysiska mått, synliga 2D-sulkontakter eller separata golvankare prövas av denna fotdiagnos. Personytans skala (rader 681–703) är en separat observation men delar kropp, kamera och MoGe; den är inte oberoende sanningsdata och används inte som godkännandegrind. Om dess sparade skala i stället används på samma golv fås i S5 cirka 1,951 m mot kontaktens 1,529 m: skillnad 0,422 m. Värdena är ungefärliga eftersom JSON-skalorna är avrundade. Flera andra tagningar skiljer 0,17–0,31 m. Det ger inget stöd för påståendet att den exakta fotkontakten har verifierats oberoende.

**Felinjektion i de faktiska källraderna 735–776:**

| Indata | Golvavstånd | Fotledsavstånd | Skala | Kamerahöjd | fot_over_golv |
|---|---:|---:|---:|---:|---:|
| Bas | 2,00 m | 1,40 m | 0,74 | 1,48 m | 0,08 m |
| Golvdjup dubblerat | 4,00 m | 1,40 m | 0,37 | 1,48 m | 0,08 m |
| Fötter flyttade en meter nedåt | 2,00 m | 2,40 m | 1,24 | 2,48 m | 0,08 m |

Testet läser och exekverar källblocket utan att ändra originalfilen. Grovt fel geometri lämnar kontaktmåttet perfekt. Slutsats: kontakt är en vald skala/origoförankring, och kan vara användbar som sådan, men är inte ett oberoende kvalitetsbevis. Råvärden: [feet.json](feet.json), [feet-injection.json](feet-injection.json).
'''
save('FOTKONTAKT.md',ft)

d1,d2=read('determinism-1.json'),read('determinism-2.json')
assert d1['sha256']==d2['sha256']==d2['original_restored_sha256']
det=f'''# Motprov 2: determinism

Oförändrad källkod och byteidentiska indata kördes två gånger med samma interpreter och argument:

```text
.venv/Scripts/python.exe -I -X utf8 -W ignore lokalitet.py babasburgers --obs gpu
```

För att samtidigt följa förbudet mot ändringar i andra `ut/`-filer kördes kommandot i en isolerad kataloghierarki under `ut/codex/isolated/motpart/runda-4/6-lokalitet/`. Interpretervägen är absolut till den befintliga `.venv`; `lokalitet.py`, `geom.py`, video, observationer, pose och valt ingest kopierades utan kodändringar. Detta är alltså en isolerad reproduktion, inte en körning som skriver över den levande ut-katalogen. Programmets vanliga relativa mål är även där `ut/babasburgers/paket_L.json`. Direkt körning på originalplatsen skulle också skriva `nat/*.bin`, `nat.json` och `lokalitet.json` (källrader 794–795, 883–890), vilket inte var tillåtet.

Originalet säkerhetskopierades före första körningen till `paket_L.original.json` och kopierades tillbaka efter respektive körning. Ingen originalobservation eller originaldiagnos ändrades. [baseline.json](baseline.json) och [integrity.json](integrity.json) kontrollerar de skyddade filerna.

| Fil | SHA256 | Tid/exit |
|---|---|---|
| Original, säkerhetskopia och återställt original | `{d2['original_restored_sha256']}` | — |
| Körning 1 | `{d1['sha256']}` | {d1['seconds']:.2f} s / {d1['exit']} |
| Körning 2 | `{d2['sha256']}` | {d2['seconds']:.2f} s / {d2['exit']} |

Källkodens SHA256: `{d1['source_sha256']}`. Originalet och de två körningarna är byteidentiska för det begärda paketet. Resultatet gäller denna maskin, dessa fasta observationer och dessa två separata processer. Det säger inget om determinism i nya GPU-observationer, andra OpenCV-versioner eller olika maskiner. Inga Modal-jobb startades.

Körbara omslag från `6-lokalitet/`:

```powershell
# Endast för en ny evidenskatalog: audit.py prepare. Befintlig baseline skrivs inte över.
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py det1
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py det2
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py integrity
```

Varje omslag har 155 s timeout för sin underprocess. Körloggar: [1](determinism-1.log), [2](determinism-2.log); maskinläsbara kommandon och hashvärden: [1](determinism-1.json), [2](determinism-2.json).
'''
save('DETERMINISM.md',det)

main=f'''Motprov av lokalitet/1, körd ögonblicksbild 2026-11-21. Kommandon nedan körs var för sig från `motpart/runda-4/6-lokalitet/`; `PY` betyder `.venv/Scripts/python.exe -I -X utf8 -W ignore`. Fem klipp, 38 tagningar, 114 originalrutor. Inga Modal-jobb.

| Påstående | Test (kommando) | Utfall | Status |
|---|---|---|---|
| 1. Ingen klippspecifik kod | `PY ut/codex/audit.py basic` + helkodsläsning av de tre filerna | Enda namnträffen är Due Piani i `modal_obs.py:3`, ett docstring-exempel. Ingen exekverbar klippgren eller tagningslista hittad. Gemensamma men delvis oredovisade priorer: bl.a. 0,90 m bänk, 0,08 m suloffset, 35° rullningskomponent, 1,38 m startkamera. 20° uppåt-prior och 1,40 m reservhöjd står i rapporten. Alla identifierade regler och 801 numeriska litteralförekomster redovisas i [KONSTANTER.md](KONSTANTER.md) / [råinventering](code-scan.json). | **står**, inom de tre filerna |
| 2. Determinism för babasburgers | `PY ut/codex/audit.py det1` och `PY ut/codex/audit.py det2`; omslagen kör `PY lokalitet.py babasburgers --obs gpu` i byteidentisk isolerad kopia | Två separata processer: {d1['seconds']:.2f}/{d2['seconds']:.2f} s, exit 0. SHA256 lika i båda och i originalet: `{d1['sha256']}`. Originalet kopierat undan och återställt. Isolering behövdes eftersom programmet även skriver andra förbjudna ut-filer. [Full körbeskrivning](DETERMINISM.md). | **står**, för paketet och dessa indata |
| 3. Lodlinje mot oberoende bildvittne | `PY ut/codex/audit.py frames`; `PY ut/codex/vp.py <nyckel>` för vart och ett av fem klipp; `PY ut/codex/vp.py --selftest` | LSD/flyktpunkt gav godtagbart vittne i **24/38** tagningar. **Ingen accepterad avvikelse >10°**; median {num(np.median(errors))}°, max {num(max(errors))}°. **14 saknar tillräckligt vittne** och lämnas utan gissning. Alla tagningar, rutor, luckor och bildbevis listas i [LODLINJE.md](LODLINJE.md). Vittnet är oberoende av gravitationsskattningarna men använder kamerans antagna fokal; ±20 % känslighet redovisas. | **delvis** |
| 4. Spridningen larmar tillförlitligt om vinkelfel | `PY ut/codex/diagnosis_injection.py`; `PY ut/codex/report.py` jämför VP med median/maxspridning | Gemensam injicerad bias 30° ger **[0;0;0]° spridning**. Verkligt små/små: Due Piani S3, median 0,4° och fel 0,1°. Stor/stor kunde inte beläggas. Due Piani S1 har max 89,4° men fel 0,9°; Spanjorskan S1 median 9,0° men fel 4,7°. Spearman ρ={num(cmed.statistic,2)}, p={num(cmed.pvalue,2)} (n=24); inget tillförlitligt samband visat. [Mätningar och avgränsning](LODLINJE.md). | **fallit** som ensamt absolut tillförlitlighetsmått |
| 5. Fotkontakt är oberoende stöd | `PY ut/codex/audit.py basic`; `PY ut/codex/feet_injection.py` | Due Piani: **9/9** kontaktskalade tagningar har exakt `m=fotter_m`; stödpersonens fotled ligger exakt 0,080 m över golvet. S2 väljer höjd direkt från fötterna; S8/S10 saknar fotvittne. Källrader 735–776 sätter skala=F/G och höjd=G×skala=F; 814–815 mäter följden. Dubbelt golvdjup eller +1 m fel fotdjup ger fortfarande perfekt 0,080 m kontakt. Alternativ personyteskala skiljer upp till 0,422 m i höjd. [Alla tal och källrader](FOTKONTAKT.md). | **fallit** som oberoende stöd |

Svagast är fotkontakten som bevis: den exakta överensstämmelsen byggs in i skala och kamerahöjd.  
Gör en VP-grind med sparade, granskade linjer, explicit ”vittne saknas” och en 15° felinjektion permanent; behåll också testet för gemensam 30° bias.  
De 14 VP-luckorna och verklig kamerarörelse hindrar ett godkännande av alla tagningar.  
Källfiler, observationer och originalpaket är hashkontrollerade oförändrade; endast den externa körarens löpande `ut/codex_kontroll.log` ändrades utanför `ut/codex/` ([kontroll](integrity.json)).
'''
save('MOTPROV.md',main)
print(json.dumps(stats,ensure_ascii=False))
print('Wrote MOTPROV.md, LODLINJE.md, FOTKONTAKT.md, DETERMINISM.md, RUTOR.csv')
