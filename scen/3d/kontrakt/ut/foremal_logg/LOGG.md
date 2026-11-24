# Föremål mot löst kamera — slutrapport 2026-11-12
- Del A: `kontrakt/mobelintervall.py:156` flyttar varje `:pa:`-föremål med möbelns valda XY-mitt och topphöjd utan att ändra dess storlek.
- `kontrakt/mobelintervall.py:207` gör samma följförflyttning i planens rumsmallskopia.
- Prov: `kontrakt/test_snabb.py:27` täcker höjd, yaw-roterad mitt och bevarade mått utan kompilering.
- Del B dataväg: `hand.json.deklarerat.foremal` → `plats.json.deklarerat.foremal` → `plan.plats[].deklarerat.foremal` (`ingest/deklaration_till_hand.py:157`).
- Den vägen valdes för att rumsmallens strikta schema ska förbli orört; planer utan `foremal` får ingen ny metadata eller åtgärd.
- `kontrakt/foremallyft.py:20` använder mittrutan i tagningens `ut`, slutkameran och strålen genom `box_2d`-bottenmitt.
- `kontrakt/foremallyft.py:47` klämmer föremålets roterade fotavtryck till stödytan; `:73` loggar före/efter/metod eller orsak i `kvalitet.foremal_lyft`.
- `kontrakt/kompilera.py:654` kör lyftet efter `bildkamera`, möbelintervall och väggar.
- Prov: `kontrakt/test_snabb.py:48` täcker syntetisk slutkamera, planträff och klämning.
- Del C: `ingest/deklaration_till_hand.py:232` bygger stöd-kedjor rekursivt, t.ex. `disk_C:pa:vag:pa:kottbit`.
- Prov: `ingest/test_deklaration.py:103` täcker metadatavägen och stöd-kedjans höjder; verklig n06-mall gav 0 schemafel.
- Tester: `test_deklaration.py` 7 OK; `test_rum.py` 3 OK; `test_scenbrief.py` 5 OK; `test_snabb.py` 10 OK.
- Verifiera: `klipp_kor.py b-tilltal-ravara prepare --variant n06-foremal --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning2/deklaration_n06.json`
- Rendera: `klipp_kor.py b-tilltal-ravara render --variant n06-foremal --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning2/deklaration_n06.json`
- Kvar: `halls_av` kräver vald handled/handmatris per ruta i planen och ett tidsvarierande fäste i `ingest/mhr_rig.py`.

## Möbellyft mot löst kamera — 2026-11-12
- Del 1 klar: `bild` för deklarerade `bord` följer `hand.json.deklarerat.mobler` → `plats.json.deklarerat.mobler` → `plan.plats[].deklarerat.mobler`; rumsmallens schema är orört.
- Snabbprov: `test_deklaration.Deklaration.test_bord_som_intervall_ger_mobler_och_mallens_mitt` OK.
- Del 2 klar: `kontrakt/mobellyft.py` använder slutkamerans mittruta; synlig bottenkant träffar golvet och beskuren botten använder toppens bakkant mot vald möbelhöjd.
- Möbeln behåller Z, mått och yaw; byggdelar och `:pa:`-barn flyttas med samma XY-delta innan `foremallyft.los` körs.
- `kvalitet.mobel_lyft` redovisar före/efter, använd ruta, kantval och orsak eller varför möbeln bevarades.
- Snabbprov: bottenkant, beskuren toppkant, följande barn samt befintligt föremålslyft — 4 OK.
- Slutprov: `ingest/test_deklaration.py` 7 OK; `test_rum.py` 3 OK; `test_scenbrief.py` 5 OK; `kontrakt/test_snabb.py` 13 OK.
- Verifiera: `klipp_kor.py b-tilltal-ravara prepare --variant n06-mobel --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning2/deklaration_n06.json`
- Rendera: `klipp_kor.py b-tilltal-ravara render --variant n06-mobel --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning2/deklaration_n06.json`

## Möbellyftets djupordning — uppföljning 2026-11-12
- `framfor` följer nu endast bilddeklarerade möbler genom `deklarerat.mobler`; planer utan möbelbild får ingen ny metadata.
- Möbelns kameradjup kläms till framkant minst 0,30 m efter kameran och bakkant minst 0,10 m före personplatsen; boxens sidoläge bevaras.
- Rapporten anger `klamd`, använd gräns, ankarkälla, djup före/efter och uppnådda marginaler i `kvalitet.mobel_lyft`.
- Om båda marginalerna inte ryms prioriteras ordningen mot personen och `granskonflikt: true` redovisar avvikelsen; detta gäller n06/S9 (0,77 m till person mot 0,90 m som krävs).
- Snabbprov: `test_deklaration.py` 7 OK; `test_rum.py` 3 OK; `test_scenbrief.py` 5 OK; `test_snabb.py` 14 OK. In-memory n06-kontroll: båda diskar klämdes mot personplatsgränsen.
- Verifiera/rendera med samma `n06-mobel`-kommandon ovan; ingen kompilering, rendering, modellkörning eller Blender kördes här.

## Flerbildspassning – 2026-11-12
- `ingest/deklaration_till_hand.py:154,172` för `bilder` genom `deklarerat` för både möbler och föremål; tom lista bevaras som uttryckligt ”inga boxar”.
- `kontrakt/boxpassning.py:73,97` projicerar lådans synliga kanter per tagnings slutkamera och passar gemensamt XY med soft-L1; toppkanten tas från toppplanet.
- `kontrakt/mobellyft.py:114,157` passar alla möbelboxar, klämmer kamera–möbel–person mot varje kamera och loggar kanter, före/efter-residualer samt slutposition.
- `kontrakt/foremallyft.py:79` gör samma flerbildspassning för föremål och klämmer det färdiga läget till stödets ovansida; 0/1 box ger orsak respektive gamla enbildsvägen.
- Snabbprov: `kontrakt/test_snabb.py` 19 OK; `ingest/test_deklaration.py test_rum.py test_scenbrief.py` 15 OK; berörda filer klarar `py_compile`.
- Utan omkompilering, på gamla `n06-skymning`-planen, disk_C RMS px: S11 1083,3→547,9; S6 928,9→1010,9; S7 15,4→3,8; S8 1354,0→861,8; S9 119,4→72,7.
- Samma indikativa kontroll för vågen: S10 44,5→40,2; S11 414,8→288,6; S8 112,9→150,9; S9 346,8→428,3; full körning krävs för slutvärden.
- Verifiera: `klipp_kor.py b-tilltal-ravara prepare --variant n06-fler --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning3/deklaration_n06_detekterad.json`
- Rendera: `klipp_kor.py b-tilltal-ravara render --variant n06-fler --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning3/deklaration_n06_detekterad.json`
- Ingen full kompilering, rendering, modellkörning eller Blender kördes.

## Avbruten följdrättelse (orkestratorn, 12 nov ~18:10)
Följduppdraget i CODEX-FLERTAGNING.md (hoppa över tagningar där lådan ligger bakom kameran, ersättningsstöd för saknat `pa`) stoppades på ägarens begäran mitt i körningen. `kontrakt/boxpassning.py` och `kontrakt/mobellyft.py` hann ändras. Båda importeras, och snabbtesterna är gröna (test_snabb 19/19, ingest 14/14), men ändringen är ofullständig och inte provad i kedjan. Granska dessa två filer innan nästa körning.

## Passningens robusthet — uppdrag 0005/0007, 2026-11-12 (uppdragstagaren)
- `kontrakt/boxpassning.py:93` `klassa_bilder`: en helt beskuren eller trasig box hoppas över med orsak (`hoppad_orsak`, `anvand: false`) i stället för att `ValueError` avbryter hela passningen. Gäller `passa`, `framfor_alla_kameror` och `tillforlitligast`.
- `boxpassning.py:123` `startlage`: startläget är medianen av enbildslägena. Boxar över 0,75 m från medianen (minst tre lyft) pekas ut och utesluts ur anpassningen; `kontrakt/mobellyft.py:224` och `foremallyft.py` använder den i stället för "tillförlitligaste" boxen.
- `boxpassning.py:201` `passa`: sökområde ±4 m (var ±20 m), `villkor` som halvplan straffas i själva anpassningen och projiceras efteråt, så `lyckad` gäller det använda läget (`lyckad_slutlage` visar om efterbehandlingen flyttade det). Andra varvet utesluter boxen som passar sämst (över 50 px och över 2,5 × medianen, en i taget, minst två kvar). Riktningar i XY som kanterna knappt känner av (under 100 px/m, `las_svaga`) låses vid startläget, så en underbestämd riktning inte driver bort.
- `mobellyft.py:118–178`: kamera–möbel–person-ordningen är villkor med nivåer (0,30/0,10 m, 0,30/0 m, 0,05/0 m, 0/0 m). Kamerans gräns lättas aldrig under 0 m. Ryms ingen nivå behålls möbelns tidigare läge med `granskonflikt: true`, `ordningsniva: null` och orsak. Dubbletten av `_projektera_halvplan` är borta; den skyddade versionen i `boxpassning.py:150` importeras. Enbildsvägen (`_klam_djup`) är oförändrad.
- `foremallyft.py:79` `_ersattningsstod`: när stödet inte byggs används närmast byggda stöd (kedjan i objekt-id, förälderns stöd, ankare) och bytet loggas i `stod_ersatt`.
- Prov: `kontrakt/test_snabb.py:223–330`: hoppad box, start och avvikande, villkor i passningen, nivåtrappan, dubbletten och ersättningsstöd. Nya totalsiffror: `test_snabb` 25 OK (var 19); `ingest/test_deklaration.py test_rum.py test_scenbrief.py` 15 OK. Körda med tom bytekodscache (`-X pycache_prefix`), ingen fil utbytt under körning.
- Minneskopia av `b-tilltal-ravara_n06-fler/narvaro/plan.json`: `disk_C` `[2,170; 1,006]` (före `[1,871; 0,906]`), 0,04 m från medianen utan S6 (före 0,33 m). S6 pekas ut (1,96 m), S8 och S11 utesluts i andra varvet. Lägsta kameramarginal +0,06 m (S9, före −0,04 m); ordningsnivå 2, `granskonflikt: true`. Se `kontrakt/ut/fore_passning_0005/kontroll.py`.
- Notan (4 planer) och guacamole (4 planer): `mobellyft.los` och `foremallyft.los` ger `None` och planen är oförändrad med både baslinjen (`ut/fore_passning_0005/kod/`) och den nya koden, byteidentiskt (`identitet_fore.txt`, `identitet_efter.txt`). `prepare` kördes inte (`klipp_kor.py` hittar inte notan under namnet d-dialog-notan).
- Kvar: `kottbit` byggs fortfarande inte (stödkedjan bryts uppströms i `ingest/deklaration_till_hand.py`, utanför uppdragets filer). Planen n06-fler har också två objekt med id `disk_A`.

## Sidled och placering per kameragrupp — uppdrag 0012, 2026-11-12 (uppdragstagaren)
- Baslinje: `kontrakt/ut/fore_sidled_0012/kod/`. Svar: `delegat/svar/0012-sidled-och-placering-per-kameragrupp.md`.
- `boxpassning.py` `kantvillkor`/`olikhetsrest`: beskuren kant = olikhet (straffas bara när den projiceras innanför bilden). `projicerade_kanter` mäter topp/botten på den del av lådan som ligger inom bildens bredd.
- `boxpassning.py` `passa_grupp`: likheter + olikheter + svagt förval (20 px/m). Koordinat med färre än två likhetskanter (> 100 px/m) hålls vid förvalet och märks `antagen`.
- `mobellyft.py` `los_grupper` (körs när bilderna bär `grupp`): ett läge per mätt grupp, tagning utan grupp passas för sig. Förval = framför `framfor`-platsen mot gruppens kameror, bakkant 0,15 m före platsen, centrerad. Väggar (0,10 m marginal), deklarerat intervall och ordningen är villkor. Kopia av möbeln och dess `:pa:`-barn per synlighetsintervall.
- `foremallyft.py` `los_kopior`: föremål på möbel ur maskens tyngdpunkt mot planet på halva föremålshöjden över stödets ovansida; bredd ur masken (bara rutor obeskurna i sidled), inom deklarerat intervall.
- `ingest/modal_segmentera.py`: separat Grounding DINO-pass per prompt, L4, deterministisk torch; masken ger tyngdpunkt, bredd, höjd. `rum_rutor.py` väljer på exakt prompt, skriver `spridning_2d`, `tyngdpunkt_2d`, `bredd_2d`, `grupp`. Två körningar på b-tilltal gav byteidentiska fynd.
- Prov: `test_snabb` 33 OK (+6, `Sidled0012`), ingest 21 OK (+1). Tom bytekodscache.
- b-tilltal `n06-grupp`: `disk_C` x 2,26–2,28 i alla grupper (var 3,09), x `antagen` utom S11. Notan och guacamole: 66 planer byteidentiska mot baslinjen (`fore_sidled_0012/oforandrad_*.json`).
- Varianter: `kontrakt/ut/b-tilltal-ravara_n06-grupp/`, `e-dialog-guacamole_grupp/`.
