"""Record the image review already performed with view_image, with output hashes."""
import json,hashlib,datetime
from pathlib import Path
B=Path(__file__).resolve().parent
previous=json.loads((B/'overlay_review.json').read_text(encoding='utf-8')) if (B/'overlay_review.json').exists() else {}
approved={(x['path'],x['sha256']) for x in previous.get('files',[]) if x.get('reviewed')}
notes={
 'notan_S1':'Bordets och väggens utvalda ytfläckar ligger visuellt stilla genom gestiken. Golvet syns inte tillräckligt: ingen golvverifiering. En stabil originalvy bekräftar inte djup eller möbelmått.',
 'notan_S4':'Golvgrid och väggfläck går att följa över de åtta rutorna. De tre nya metoderna är visuellt lugna här. Gridlinjer över benen kommer av att diagnosen saknar skymning; detta bedöms inte som ett separat geometrifel.',
 'b_S5':'Kameran flyttas lite och mycket av förgrunden är kött, händer och text. Vägglådan glider betydligt, särskilt med ViPE. Personmasken omfattar inte allt rörligt rekvisitainnehåll. Inget golv synligt. Återprojektion och den extrema ViPE-fokalen stödjer avvisning; orsaken har inte isolerats med maskablation.',
 'b_closeup':'Närbild S9: den lilla väggytan ligger förhållandevis stilla, medan ansikte, händer och våg dominerar. Inget golv. Visuell stabilitet skiljer inte de kraftigt olika djupskalorna åt.',
 'pool':'Svart första och sista provruta är märkta ogiltiga. MapAnything ändrar gridens perspektiv starkt; ViPE följer bakgrunden bäst och DA3 är lugnare än Map. Alla har avvikande skattade golvplan. Bordsrutorna är små observerade ytfläckar, inte hela bordets 2,4 × 1,3 m.',
 'kenny_S2':'Lådan följer en liten disk-/trågfläck under första delen och går ur bild när kameran vänds mot ansiktet. Då finns få gemensamma bakgrundsankare till diskvyn. Inget golv kan kontrolleras. En rimlig låda i de första rutorna godkänner inte den sena kameran.',
 'notan_uncut':'Alla tre ger utdata över klippen. Grid från S4 projiceras även in i andra kameravyer, ibland högt i bilden. Utan gemensamma synliga ankare och djupordning går ett gemensamt rum inte att bekräfta. Klippförflyttningar är inte fysisk kamerahastighet.',
 'notan_joint_S1_S4':'Båda strips, totalt 16 rutor, öppnade. En gemensam koordinatram ges men S1-bordets och väggytans relation till S4 är inte mätverifierad. Lådor som överlappar personen är inte ensamma bevis för fel, eftersom överlägget saknar skymning. Jämför dessutom bordshöjd och fokal mellan körningarna.',
 'notan_fullrate':'383/383 rutor körda; åtta jämnt fördelade överlägg öppnade. Ursprungsvyer återkommer men ett enda samstämmigt rum är fortfarande inte styrkt. DA3:s stora korsvysfel och de olika stationernas skalor kräver egna spärrar. En låda/ett grid kan projiceras också i en felaktigt sammankopplad vy.',
 'pool_fullrate':'369/369 rutor körda. Fullrutekontrollen gör inte MapAnything stabilt med svart/fade-intro. DA3 och framför allt ViPE ger lugnare kamera. Bordets fixerade ytfläck och golvets djup är fortfarande inte ett metrisk verifierat rum. Svarta rutor förblir ogiltiga i måtten.',
 'pool_visible':'Svarta rutor borttagna men mycket mörka fades återstår i första/sista rutan. Map-grid och låda lämnar större delen av de ljusa mellanbilderna; detta är ett misslyckat fall. Det utesluter inte fade-exponeringen som orsak.',
 'pool_core':'311 rutor, source 40–350: även fades borttagna. Tydligt bättre överlägg och lugnare Map-kamera. Den tunna bordsfläcken förblir delvis på den gröna ytan. Det är inte en komplett bordslåda. Brännvidd och kroppsdjup är fortfarande motstridiga; förbättrad originalvy räcker inte för meterskalan.'
}
files=[]
for candidate in ['baseline','mapanything','da3','vipe']:
    for shot in (B/'ut'/candidate).iterdir():
        if not shot.is_dir():continue
        for p in sorted(shot.glob('overlay*.jpg')):
            path=str(p.relative_to(B));sha=hashlib.sha256(p.read_bytes()).hexdigest();checked=(path,sha) in approved
            files.append(dict(path=path,sha256=sha,reviewed=checked,observation=notes.get(shot.name) if checked else 'Kräver ny visuell granskning; tidigare anteckningar godkänner inte en ändrad bild.',method_note='ViPE dense files are raw MoGe2 at its K, not the NC-blocked adaptive dense pipeline.' if candidate=='vipe' else None))
result=dict(reviewed_utc=previous.get('reviewed_utc'),audit_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),method='Only reviewed=true entries were actually opened with view_image and visually inspected by the assistant. This script preserves an existing hash-bound attestation; it never approves a new or changed image.',warning='Diagnostic grid and thin surface boxes lack depth occlusion and are not automatic complete furniture reconstructions. Source ROI choices were made before looking at model overlays.',files=files)
(B/'overlay_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('unchanged visually reviewed strips:',sum(x['reviewed'] for x in files),'need new review:',sum(not x['reviewed'] for x in files))
