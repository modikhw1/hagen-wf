"""Skriv spårbar slutrapport av sparade mått och manuell bladgranskning."""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from textarbete import spara,jsonfil,UT

HIT=Path(__file__).resolve().parent
ROT=HIT.parents[2]
NOTES={
 'b':[
  'A är rätt rollspår; storlek och läge nära källan. Kamera på personalsidan. Första texten rättad till en rad. Vänster hand har tydliga hudspikar; kött, papper och förgrundshand saknas.',
  'A rätt spår och sida; armgest och storlek rimliga. Mads visas före vikten som i bladets källrutor. Kött och papper saknas; disken är för gles.',
  'B rätt spår på personalsidan. Huvud och händer nära källutsnittet, generisk kropp och ansikte. Namn/vikt finns. Kött och papper saknas.',
  'B rätt spår och sida. Kroppens bildläge förbättrat; rumsdjup är en mall. Text på rätt band. Kött saknas. I redigerad2 är kameran avsiktligt stativbunden.',
  'C rätt spår bakom disk, kamera från kundsidan. Utsnittet följer källan bättre; identitet och förkläde saknas. Vikter på rätt band, men kött, papper och kundens hand saknas. Öppen monter blir mest räcken.',
  'C rätt sida och liknande huvudläge. Lærkes värde kommer senare än etiketten i båda bilderna. Källans ljusa diskyta saknas i förgrunden; kvarvarande räcken är för svaga.',
  'C rätt sida och ungefärlig storlek; liten huvud-/handavvikelse finns. Tre viktrader syns. Kött och papper saknas; disken läses dåligt.',
  'C rätt spår, nära huvudutsnitt men kroppen är för generisk. Vikter syns. Vågen, köttet och dess kontakt med disken saknas; räcken ersätter inte vågbordet.',
  'C rätt spår, ansiktet stort som i källans närbild, händer ungefär rätt. Text finns. Våg och ansiktsuttryck saknas; inga igenkännbara råvaror.',
  'C rätt spår, huvud-/armvändning går att följa. Svart Vægt-rad finns tillsammans med vikterna. Vågen, cirkelmarkeringen och köttet saknas.',
  'C rätt spår, huvud-/torsoläge förbättrat. Vikter och Vægt-rad syns. Vågen, kött och papper saknas; diskkantens passning har kvar rest.'
 ],
 'kenny':[
  'A rätt spår bakom disk, kamera kundsida. Framåtlutning och pekgest går att följa. Rubrik och Vs finns. Glass, sked, tråg och glas saknas; en öppen ram återger inte glassdisken.',
  'Första provrutan är tom för kropp: bara hand/arm finns i källan och spåret börjar först lokalruta 60. Senare huvud nära källans läge men utan sked/glass. Text och emoji finns. Kamerans orimliga metriska translation är avvisad.'
 ],
 'a':[
  'A är kundspåret; kundsida och kamera personalsida. Huvud/torso läge förbättrat, handgest rimlig. Röd text på rätt band. Mynt, kläder, identitet och den blanka disken saknas.',
  'B personalspår, kamera kundsida. Hand vid hakan går att läsa; huvud ligger nära källan. Röd text kommer senare som i källan. Rummet lutar mer än källan och disken är för gles.',
  'Mat-/handnärbild: renderingen visar främst rum/räcken, trots enstaka sparade kroppsrutor utanför utsnittet. Röd text finns. Kebab, kniv och synliga händer saknas. Berättelsen går förlorad.',
  'B rätt spår på arbetssidan; kameran också på arbetssidan enligt källavläsningen. Huvud/axlar följer källan ungefär. De korta röda texterna visas, men beredning och råvaror saknas.',
  'B rätt sida och gest, första huvudstorleken rimlig men den andra bilden saknar hela matmotivet i förgrunden. Röd text finns och följer de två avlästa textbanden. Papper/mat saknas; rumsriktning osäker.',
  'Scen utan person är korrekt som spårbeslut. Källan är en närbild på mat, renderingen bara en tom mall. Ingen text i dessa provrutor. Helt oanvändbar som matbild.',
  'A kundspår, rätt sida och vändning. Händer ungefär rätt men bär tom luft. Inga texter i provrutorna, som i källan. Mat/papper och miljöidentitet saknas.'
 ]}


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def quality(p):
    out={}
    for line in Path(p).read_text(encoding='utf-8').splitlines():
        cells=[x.strip() for x in line.split('|')[1:-1]]
        if cells and re.fullmatch(r's\d+',cells[0]):out[cells[0]]=dict(bildfel=cells[1],omdome=cells[-1].split(':')[0])
    return out


def main():
    diag=read(UT/'diagnos_fore.json');rows=[]
    for clip in ['b','kenny','a']:
        before=quality(HIT/f'ut/{clip}/tom/kvalitet.md');after=quality(HIT/f'ut/{clip}/tom2/kvalitet.md')
        for i,note in enumerate(NOTES[clip],1):
            sid=f's{i}'
            rows.append(dict(klipp=clip,scen=sid,fore=before[sid],efter=after[sid],visuellt='inte leveransklar',visa_agaren='endast uttryckligt tekniskt prov',iakttagelse=note))
    jsonfil(UT/'scenbedomning.json',rows)
    out=['# Slutrapport: bildutsnitt, skärmtext och diskplatser',
         '',
         'Fem nya filmer har byggts lokalt och seriellt. Ingen nätanslutning, modellservice, betald kroppskörning eller paketinstallation har använts. Den öppna Blender-GUI:n lämnades orörd. Blender hittades via `ingest_klipp.py` och kördes med `-b --factory-startup` i egna processer.',
         '',
         'Resultatet är ett bättre tekniskt underlag, inte färdiga kundfilmer. Jag skulle visa b s5 som en förklarad text-/miljöbytesdemo och notan s7 som en replik-/undertextdemo. Jag skulle inte visa någon hel film från b, kenny eller a som färdig leverans: motivets råvaror saknas och kropparnas identitet återges inte. Alla 37 slutblad har öppnats: 11 + 2 + 7 + 11 + 6. Notans s3 tas avsiktligt bort av befintlig regi.',
         '', '## Framing: mätning före ingrepp', '',
         'Måttet är egenprojektion mot estimatorns sparade 2D-ledpunkter, inte en oberoende annotering av källbilden eller hudens kontur. Råpose + råtranslation projicerar tillbaka på samma punkter med ungefär 0,00005 px p90; det är en konsistenskontroll. Gränserna 20/40 px, 4/8 % av personhöjd och IoU 0,65 är oförändrade. Även skymningsgränsen 2 % och djupmarginalen 5 cm är oförändrade.',
         '', '| Scen | Före median/p90 px | Dominerande orsak | Kontrollerat belägg |', '|---|---|---|---|']
    for d in diag:
        v=d['varianter'];p=v['plan']
        if not p['flaggad']:continue
        reason='Stabilisering av pose/form'
        evidence=f"Rå cam_t ensam ger p90 {v['raw_t']['p90_px']:.2f} px; råpose + rå cam_t ≈ 0 px."
        if (d['klipp'],d['scen'])==('b','s5'):
            reason='Djuptranslationens utjämning passerar gränsen, ovanpå posens rest'
            evidence=f"Stabil pose + rå cam_t {v['raw_t']['p90_px']:.2f}; utjämnad {p['p90_px']:.2f}. Accepterad COLMAP/raw focal 2334,69 px; längsta sida ger {v['fallback']['p90_px']:.2f} px."
        if (d['klipp'],d['scen'])==('kenny','s2'):
            evidence+=' Bara 36/96 rutor har råkropp och 12 är tillförlitliga. Skala 785 och 11,7 km bana gör dessutom platsen orimlig.'
        out.append(f"| {d['klipp']} {d['scen']} | {p['median_px']:.2f}/{p['p90_px']:.2f} | {reason} | {evidence} |")
    out += ['',
      'Alla 19 personscener undersöktes; fulla varianter finns i `diagnos_fore.json`. Bildens längsta sida är redan identisk med kroppens focal i alla fallback-scener. De två accepterade COLMAP-värdena, b s5 (2334,69 px) och kenny s2 (1505,54 px), är också kroppens egna konstanta focal. Att byta bara kamerans focal till andra COLMAP-värden ökar felet kraftigt och blandar två olika kameramodeller.',
      '',
      'En gemensam rigid kamera-/persontransform och platsregistrering lämnar projektionen oförändrad; det bekräftas av seq-/planjämförelsen. Golvkompensationen fanns redan. Kort-bana-regeln var däremot fel för rum: den slängde rotation vid ren kameravridning. Den nollar nu bara translation och skala. Kenny s2:s orimliga translation avvisas med rapporterad hastighet, rotation behålls. Uppmätta bakgrundsvertikaler med konsensus per kamerauppställning ger bättre rumsriktning, men flera riktningar är ärvda/antagna och a:s rum lutar fortfarande för mycket visuellt.',
      '',
      'Lokalt bildskydd på de 19 befintliga sekvenserna begränsar stabiliseringens p90-förskjutning mot pålitliga råpunkter till min(6 px, 1,5 % personhöjd). Dolda ben behåller stabil geometri relativt höften. Det är en signalvakt före kvalitetskontrollen, inte en lättad godkännandegräns. Överkroppsspår binds till disksidan utan att hitta på fotkontakt. Dubbletter var redan sammanförda/filtrerade; inget nytt identitetsbyte förklarade de sju flaggorna.',
      '',
      'Lokalt omgjort: 19 seq-cachefiler med redan sparade råposer, kamerariktning för 19 tagningar från källbilder, kenny S2:s varld-steg en gång och platssteg för tre klipp. Ingen ny kroppsprediktion. Råkroppscachen innehåller 1183 NPZ-personrutor (b 461, kenny 190, a 532); vissa seq-rutor är interpolerade.',
      '',
      'Betald etapp behövs inte för de genomförda rättningarna. Om själva råkroppen ska omestimeras i de sju ursprungligen flaggade tagningarna är det b S1/A 50, S5/C 46, S11/C 43; kenny S1/A 156 spårrutor (154 NPZ), S2/A 36; a S1/A 60 (59 NPZ), S4/B 216: totalt 607 spårrutor, 604 befintliga NPZ. Det garanterar inte bättre händer. Kenny S2 lokalruta 0–59 och a S3:s handnärbilder kräver först hand-/armspårning; ett fullkroppsjobb är inte belagt som rätt lösning. Inget av detta har körts.',
      '', '## Text: källa, kontrakt och noggrannhet', '',
      'Inventeringen i `verktyg.json` hittade OpenCV 5 med textmodul och ffmpeg 8.1, men ingen Tesseract-binär och inga installerade OCR-paket eller OCR-vikter. Därför användes kända strängar från den sparade semantiken, teckenmallar i färg-/kontrastmasker och synlighet ruta för ruta. Inga tjänster anropades. Svår font/bakgrund kompletterades med avlästa pixelboxar och radbrytningar i `textreferenser/`; detta är dokumenterad mänsklig avläsning, inte ny modellbedömning.',
      '',
      'Kalla: id, scen, text, start_s/slut_s (halvöppet källintervall), typ overlay/undertext, replik-id, box X/Y/bredd/höjd i källpixlar, stil med font/storlek/justering/färg/kontur, ursprung och konfidens. Befintlig regi-op `skarmtext` används för byt/ta_bort/lagg_till och kan ändra box/stil. Planen löser textens ut-rutor genom tidskartan. En tillämpad replikändring ersätter kopplad undertext; en nekad ändring gör det inte.',
      '',
      'Konfidens är matchningsstyrka, inte en kalibrerad sannolikhet för korrekt text. Närmaste installerade font är antagen; färg, textband och kontur är avlästa. Tal och kg på samma rad får gemensam synlighet, märkt antagen association. B:s första fontträff bröt felaktigt på två rader och rättades mot ruta 16; synlighet 3–38 är avläst mot rutorna före/efter. Textens tillväxt i ruta 3–7 är ännu bara en fast storlek.',
      '',
      'Pillow skapar transparenta PNG-lager. ffmpeg kompositerar dem som sista 2D-steg över render/ och skriver både film.mp4 och komposit/-rutorna till jämförelsebladen. Det är enklare än Blender-kompositorn eftersom bildsekvens och tidskarta redan finns och texten slipper möbelocklusion. B s1 rättades utan ny Blender-körning.',
      '', '| Klipp | Lager i kalla | Antagna standardboxar | Lokal matchningsrest median X/Y; p90 X/Y px | Matchningspoäng median |', '|---|---|---|---|---|']
    audits={x['klipp']:x for x in read(UT/'textgranskning.json')}
    for clip in ['b','kenny','a','notan']:
        k=read(HIT/f'ut/{clip}/kalla.json');ts=k['semantik']['skarmtext'];a=audits[clip]
        assumed=[f"{t['scen']}/{t['id']}" for t in ts if t['ursprung'].get('typ')=='antagen']
        out.append(f"| {clip} | {len(ts)} | {', '.join(assumed) or 'inga'} | {a['median_abs_forskjutning_px']}; {a['p90_abs_forskjutning_px']} | {a['median_matchning']:.3f} |")
    out += ['',
      'Resten ovan är en lokal sökning ±12 px av den ritade teckenfärgen i källbilden vid textens mittruta. Den mäter font-/lägesöverensstämmelse, inte oberoende korrekthet; ändrade repliker jämförs med originaltexten. Bakgrund och outline stör särskilt kenny. Ingen fullständig tidsannotering finns, så generell timingprecision i procent kan inte ärligt anges. Detektorn fyller högst tre rutors kontrastbortfall (cirka 0,1 s); avlästa gränser och missad storleksanimation redovisas i referenserna. B s1:s manuellt kontrollerade gränser är exakta till en ruta. Bladen kontrollerar två tidpunkter per scen och bevisar inte alla mellanrutor.',
      '',
      'Demonstrationer: b s5 i redigerad2 ändrar 2,400 till 2,500, resten ligger kvar. Notan s7 visar ”Men jag känner dig ju inte?” och s4 visar den lyckade nya repliken; s1 behåller originalet eftersom det längre talbytet nekades. Borttagningen av notan s3 flyttar senare texter 57 rutor tidigare. Det finns sex blad i den redigerade notanfilmen.',
      '', '## Diskrum och lokalkoder', '',
      'De nio kundlinjefilerna innehåller exakt disk_kassa, kok, matsal, entre, bar och uteservering. `rumsmall/lokalkoder.json` märker kopplingen uttryckligen som vår egen antagna mapping. Sex lokal_*-mallar och specialiseringarna chark_disk, glass_disk, servering_disk och fiktiv_mandisk använder befintliga deltyper. Motstående sta_bakom/kundsida vetter mot varandra; kameror har egna kund-/personalankare och höjdprior 1,45 m.',
      '',
      'Semantikens ”bakom disk” bestämmer inte ensam kamerans sida. Avlästa källbilder visar b s1–s4 och a s3–s4 från arbetssidan; dessa korrigeringar finns i `textreferenser/disksidor.json`. Övriga kund-POV-upplägg har kameran på motsatta sidan. Samma plats och ankare återanvänds mellan kamerauppställningens tagningar, men den visuella diskpassningen är fortfarande för svag för att kallas konsekvent korrekt.',
      '', '| Klipp | Höjd/status | Rest mot handled | Rest mot avläst bildkant |', '|---|---|---|---|']
    for clip in ['b','kenny','a']:
        m=read(HIT/f'ut/{clip}/plats_text2/plats.json')['mallbeslut']['hojdpassning']
        pixels=', '.join(f"{x['tagning']} {x['rms_px']:.2f} px RMS" for x in m.get('pixelpassning',[])) or 'ingen oberoende kantpassning'
        out.append(f"| {clip} | {m['hojd_m']:.3f} m / {m['status']} | {m.get('evidens_rest_m')} m | {pixels} |")
    out += ['',
      'B:s stilla händer håller kött och är inte verifierad diskontakt; därför används ärligt en mallhöjd 1 m. Efter kantpassningen ligger handlederna cirka 16,7 cm över den. Kenny använder en stilla handled som osäker kontaktcue. A:s råcue 75,7 cm klipps av den antagna priorn till 85 cm och ger 9,3 cm rest. Ankarnas konstruktions-RMS är nära noll eftersom de konstrueras tillsammans; det är inget bildmätningsbevis.',
      '',
      'Öppna monterramar används eftersom en ogenomskinlig hylla skymde källans synliga händer. Enstaka motstridiga räcken utelämnas per scen under oförändrad 2 %-gräns. Det bevarar fler delar än den gamla lösningen som tog bort hela disken, men lämnar ibland en visuellt alltför gles disk. Inget glas, ingen trogen kyldisk eller belagd kontaktgeometri har skapats.',
      '',
      'Kalla.scen.kamera_bindning anger ankare, status och metod. Planen sparar kamerans lokala rörelse relativt det ankaret. Vid byt_miljo mappas kamera och person var för sig; K-specifika kameraankare kan falla tillbaka till kamera_kund/kamera_personal i målmall. Ett särskilt test använder ett kameraankare som skiljer sig från personens och jämför den exakta matrisen.',
      '',
      'B redigerad2 byter endast s5 till fiktiv_mandisk: en uttryckligen påhittad lila Måndisk på planeten Ärtan, med samma ankarslag. Edits e1–e5 tillämpas. Lila hyllor/ramar och golv syns. Målmallens större ankaravstånd gör personen mindre och längre åt höger; det är en konsekvens av den oberoende kamerabindningen och en kvarvarande svaghet i demonstrationsutsnittet.',
      '', '## Före/efter och egen visuell bedömning', '',
      'Bra/granska/dålig i kvalitet.md är den automatiska diagnosen. Den manuella bedömningen nedan är strängare. Alla rätt person-noteringar avser rollspåret, inte igenkännbart ansikte, kläder eller könsuttryck. Ingen av de 20 scenerna är leveransklar. Jag kan visa b s2–s7 som märkta tekniska skisser; b s5:s textdemo är tydligast. Jag skulle inte visa b s1 med handspikarna eller mat-/handnärbilderna kenny s2, a s3 och a s6 annat än som fellista.',
      '', '| Klipp/scen | Före median/p90 px | Efter median/p90 px | Automatisk före → efter | Manuell iakttagelse |', '|---|---|---|---|---|']
    for r in rows:out.append(f"| {r['klipp']}/{r['scen']} | {r['fore']['bildfel']} | {r['efter']['bildfel']} | {r['fore']['omdome']} → {r['efter']['omdome']} | {r['iakttagelse']} |")
    out += ['',
      'Alla elva redigerade b-blad öppnades också: s1–s3/s6–s11 har samma synliga brister som tom2, C är avsiktligt röd; s4:s stativ ändrar utsnittet; s5 visar lila målrum och 2,500. Notans sex blad öppnades: s1/s2/s5/s6 har rätt text i provrutorna men saknar måltidsrekvisita och identitet; s4:s nya text syns över servitören; s7:s nya text syns i båda provrutorna. Texten är en tydlig förbättring men gör inte råvarunärbilderna användbara.',
      '', '## Regressioner och kontroller', '']
    for r in read(UT/'regression.json'):
        out.append(f"- {r['klipp']}: {r['sekunder']} s. Skillnader i skyddade delar: {r['skyddade']}. Alla ändrade toppnycklar: {r['alla_andrade_sokvagar']}.")
    out += ['',
      'Notan jämförs med ut/notan/golv_tom/plan.json från en färsk tom kompilering. Bar jämförs med exakt ut/bar/plan_efter_baromkorning.json med bar-exemplets befintliga defaultregi. Bar hade inte matkamera i den gamla planen: den nya valfria mätkameran tillkommer, inte en ändrad renderkamera. Exempel/bar, råkroppar och de förbjudna ingestmapparna skrevs aldrig. Bro-koden är oförändrad.', '']
    for r in read(UT/'kontroller.json'):
        out.append(f"- exit {r['exit']}, {r['sekunder']} s, cwd {r['cwd']}: `{' '.join(r['kommando'])}`.")
    log=(UT/'kontroll_unittest.log').read_text(encoding='utf-8')
    out += ['', 'Unittest-slut: '+ '\n'.join(log.splitlines()[-5:]), '',
      'Nya testfall täcker textbyte, tillägg/borttagning, replikbunden undertext, tid efter borttagen scen, fullständig lokalkodsmapping, ankarnas motriktning, kameraankare, oberoende ankare vid miljöbyte, överkropp utan påhittad fotkontakt, bibehållen rotation vid kort translation och minimal utelämning av monterramdel. Befintliga bro-testfall ändrades inte.',
      '', '## Leveranser och tider', '',
      'Python kördes från arbetsroten med scen/.venv/Scripts/python.exe och PYTHONIOENCODING=utf-8; unittest-kommandot kördes i kontrakt som beställt. Tiderna är väggtid per subprocess, inte en uppskattning av aktiv arbetstid. Inga tunga jobb överlappade.', '', '| Film | Renderkedja sekunder | Delsteg |', '|---|---|---|']
    for r in read(UT/'renderingar.json'):
        d=HIT/f"ut/{r['klipp']}/{r['mapp']}";tm=read(d/'tider.json')
        out.append(f"| ut/{r['klipp']}/{r['mapp']}/film.mp4 | {r['sekunder']}"+(f" (första färgprovet {r['forsta_render_sekunder']} s)" if 'forsta_render_sekunder' in r else '')+f" | {tm} |")
    out += ['',
      'Varje mapp ovan innehåller plan.json, kvalitet.md, blad/s*.png, film.mp4, render/ utan text, textlager/ med alpha och komposit/ med slutbilder. De gamla tom-, golv_tom- och bar-mapparna har bevarats. Bakgrunds-.blend finns i resultatmapparna; den öppna GUI-sessionens filer användes inte.',
      '',
      'Alla tidigare befintliga ändrade filer kopierades till ut/fore_text/ med samma relativa sökväg från arbetsroten före första ändringen. Egna senare provversioner finns också där. `andrade_filer.json` listar gamla filer med före-/efterhash och radslut; `skapade_filer.json` listar tillkomna källfiler och slutresultatens ingångar. Ingen radering utanför egna testtempmappar har utförts.',
      '', '## Kvar, mest värde först', '',
      '1. Rekvisita: kött, papper, våg, glass/sked och mat. Nästa bästa insats är enkla märkta objekt med hand-/diskkontakt i b s5 och a s6, före mer persondetalj.',
      '2. Händer och huddeformation: b s1:s spikar måste lösas i rigg/rotationsinterpolation med redan sparade data; bättre pixelmått räcker inte.',
      '3. Diskgeometri och gemensam kamerakalibrering: passa verkliga kanter över flera källrutor per uppställning. Nu är öppna räcken en grov mall, b har upp till 16 px rest och a saknar oberoende kantpassning.',
      '4. Hand-/armnärbilder: kenny s2 tidiga 60 rutor och a s3 kräver synliga handspår. Utred lokal spårning innan någon betald fullkroppsetapp beställs.',
      '5. Identitet, kläder och uttryck saknas i alla generiska figurer; materialfärg skiljer bara rollspår.',
      '6. Text: exakt font, b s1:s storleksanimation, bättre outline/emoji och oberoende annotering av samtliga tidsgränser. Nu finns bara lokal matchningsrest och dokumenterade stickprov.',
      '7. Miljöbytet behöver kompositionskontroll av kameraankare så att ändrade ankaravstånd inte gör personen för liten eller för långt åt sidan.']
    spara(UT/'rapport.md','\n'.join(out)+'\n')


if __name__=='__main__':main()
