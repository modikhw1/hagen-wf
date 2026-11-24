# C: tre personer ? Jutsu

## Levererad animatik v1 — 2026-11-14
Jutsu revision **6** (sceneSequence 2) är byggd och granskad. 300 objekt inklusive befintligt dolt Web_sun, tre roller i full/beat-samlingar, källkamera, 0–818 vid 30 fps, rum, bricka/mat, telefon och terminal. Projekt: https://higgsfield.ai/3d-jutsu/6e364261-709e-4ab8-a030-fc9cd2d85627

Filer:
- `jamforelse.mp4`: original | animatik med originalljud, 576×512, 819 rutor, 27,3 s, H.264/AAC.
- `animatik.mp4`: animatik med originalljud, 288×512, samma längd och antal rutor.
- `preview/scene.blend`: lokal redigerbar motsvarighet, ljussatt med kamera och animation. Filmen använder Workbench för snabb formgranskning.
- `jamforelse_kontakt.jpg`: sex prov ur den faktiskt muxade jämförelsefilmen.
- `delivery_validation.json`, `visual_audit.json`: teknisk verifiering.

Rättningar i denna fortsättning:
1. Jutsu-adaptern använder knäpunkterna 11–12, egen personruta och mask. Den äldre funktionen tittade på vristerna 13–14. Kundens alla 259 kroppsprov har knästöd. Benavvikelse median föll från 40,17 % till 0,14 % av personrutans höjd.
2. Källgranskning visar att servitören står kvar vid 411/414/417, men rådjupet hoppar från cirka 2,2 m till 4,2–4,4 m. Dessa tre prov får vikt noll; grannrutor interpolerar rörelsen. Max rothastighet föll från 22,31 till 1,85 m/s.
3. Korta spårluckor upp till sex rutor interpoleras, kanter hålls högst fem rutor. Sista rutan innehåller kund och matbärare. Sex regressionstester passerar.
4. Separat, källstyrd skymningsanimation: servitören 451–549 (sista pose, utgång åt bildhöger); matbäraren 413–479 (interpolation mellan samma identitets ändposer). Dessa är INTE nya uppmätta kroppsrutor. Dolda ben vid matbärarens sittande 780–818 får uttryckligt antaget sittstöd. Ingestens rådata ändras inte.
5. Rekvisita följer händer/bord med granskad timing. Brickan har kontinuerlig rotation, max cirka 4 grader per ruta i upptaget; kontakt med huvudbordet verifierad till numerisk avrundning. Rumsmått, möbler, bakvägg och tak är förenklade antaganden.
6. Muxning paddar det kortare ljudet i stället för att kapa sista videorutan.

Granskning: lokala kamera-/sidobilder, sex prov från slutfilmen, Jutsus ljussatta f200 och slutrevisionens f000/f600/f818 visuellt kontrollerade. Strukturell kontroll: CAM_main, 30 fps, 0–818, rätt roller i slutbilden. Molnbilder hämtades genom Higgsfields sandbox, eftersom webbverktyget och IAB inte kunde visa bildlänken.

Återbyggnad utan nya GPU-jobb:
`c_ingest.py --rebuild-sequences` vid behov → `c_ops.py` → Blender med `c_preview.py` → öppna sparad blend i bakgrund och kör `c_render.py` → `c_mux.py`.

Avgränsning: leveransen är en förenklad animatik, inte fotorealism eller metrisk verifiering av restaurangen. Fingrar, ansikten och exakt stol-/fotkontakt är inte återskapade. Rum och skymningsrörelse kan fortsatt förfinas mot originalet. Ingen ny Modal-kroppsanalys eller betald AI-bild/video-generation gjordes.

All text nedan är tidigare arbetslägen.

## Aktuellt läge efter lyckad Modal-körning och lokal rättning
Äldre blockeringsnoteringar nedan är historik. Användaren körde Modal i vanlig PowerShell: 612 jobb, 82,3 s för kroppsteget, 0,509 s median per jobb. Alla 612 kroppsfiler finns: kund 259, servitör 127, matbärare 226. Kostnad i pengar är inte avläst.

Sekvenssteget kraschade därefter: brus_sigma i den gemensamma utjämnaren söker fyra intilliggande giltiga rutor. Med --steg 3 saknas sådana grupper, sigma faller till 0,0001 och avvikarfiltret kan avvisa alla rutor. Jutsu-adaptern c_sekvens.py skattar i stället bruset från grupper vid observerad samplingskadens, utan att använda interpolerade luckor som mätningar. c_ingest.py återanvänder samma ingest med denna adapter endast för sekvenssteget. Inget i scen/ ändrat.

Verifierat: tre regressionstester (tät paritet, gles brusskattning, NaN i luckor), tre ändliga sekvenser om 819 rutor, kamera/värld och golv klara. Sekvens 145,1 s; värld 13,3 s; golv 2,9 s. Kropp/personer/kamera återanvändes; ingen ytterligare GPU-körning. Återstart: `scen/.venv/Scripts/python.exe byggsten/jutsu/c_ingest.py`.

c_ops.py körd och lokal Blender-förhandsvisning byggd med c_preview.py. Redigerbar lokal scen: preview/scene.blend. Stillbilder: preview/kropp_f000.png, f090, f450, f600, f818. f090, f600 och f818 visuellt granskade. Detta är en underkänd arbetsversion, inte slutleverans.

Återstår innan publicering till Jutsu:
- Sittande kundens ben saknar tillräckligt bildstöd. Vakt: benavvikelse median 40,17 procent av personrutans höjd; överkropp median 0,12 procent. Lös stöd/antagen sittpose explicit, inte genom att beskriva benen som uppmätta.
- Servitörens rot hoppar vid 408–421 (max 22,31 m/s); granska källrutor och råresultat innan korrigering.
- Sista bilden 818 saknar kroppar eftersom sekvensstödet slutar 816. Hantera de sista två rutorna som explicit hållen/extrapolerad pose där personspåren stöder synlighet.
- Rumspassning, bricka, terminal, kontakt och full animationsgranskning återstår.
- Jutsu kontrollerat igen: revision 1, sequence 1, endast Web_sun; inga scenmutationer gjorda i denna fortsättning. Lokal förhandsvisning har inte överförts till Jutsu.

Diagnostik: ingest/vakt_sparse.json och .png. Överkropparnas medianavvikelse från råanalysen: kund 0,12 %, servitör 0,09 %, matbärare 0,27 %. Detta bevisar närhet till estimatet, inte korrekt 3D-djup eller slutlig visuell kvalitet.

## Återupptaget 2026-11-14 i nytt konto
- Modal-felsökning: klient 1.6.3 finns; lokal .modal.toml finns med en profil och båda tokenfälten (värden ej utskrivna, giltighet ej verifierad). DNS för api.modal.com fungerar. Direkt TCP till api.modal.com:443 stoppas med PermissionError / WinError 10013 före TLS och autentisering. Sessionen har begränsat nätverk och tillåter inte behörighetseskalering. Nästa körning behöver en miljö med tillåten nätverksåtkomst; det finns inget belägg för att nya inloggningsuppgifter behövs. Inga nya GPU-jobb startades under felsökningen.
- Jutsu kontrollerat via get_project: revision 0, sceneSequence 0, ingen aktiv operation eller artefakt.
- Återstartskommandot nedan kördes. Personer och kamera återanvändes från cache. Modal misslyckades åter med `Could not connect to the Modal server` innan några kroppsfiler skapades. Logg: `ingest/modal.log`. Ingen ny GPU-kostnad har kunnat bekräftas.
- Referensbilden `tracks.jpg` granskad. Fortsatt samma process och samma tre roller.
- Exportfel rättat i `c_ops.py`: sekvenssteget fyller `inom` mellan första och sista kroppsprovet och kan därför överbrygga undantagna identitetsluckor. Exporten skär nu detta intervall med den granskade synligheten i `personer.json`; luckor blir dolda. Kontroll med syntetisk lucka 451–479 och sekvensgräns godkänd.
- Exporten stoppar nu tydligt om varld.npz eller någon av de tre sekvenserna saknas. Detta stopp verifierat på nuvarande underlag. Rörelsens uppskattning/interpolation beskrivs i exportens proveniens.
- Ingen scen eller rendering skapad. Nästa beroende är fortfarande fungerande Modal-anslutning; därefter samma återstartskommando och visuell validering. Ändringar endast under byggsten/.

K?lla: scen/klipp/c-sketch-tre.mp4, 819 rutor, 30 fps.
Projekt: https://higgsfield.ai/3d-jutsu/6e364261-709e-4ab8-a030-fc9cd2d85627

## Scenpass
Leverans: redigerbar 3D-animatik och j?mf?relse med originalet, 288 ? 512.
Huvudroller: kunden p? b?nken, servit?ren, mannen som tar maten.
Rum: restaurang, b?nk l?ngs v?nster v?gg, rad med bord och stolar, g?ng till h?ger.
M?tning: befintlig ingest, nya personsp?r, kamera och kropp; inget fotorealistiskt genereringssteg.
Antagna m?tt/dold geometri ska m?rkas i rumunderlaget.
Granskning: roller best?ende, gester och intr?den f?ljer k?llan, matbrickans ?verl?mning synlig, fem tidsprov och slutruta.

## Hittills
- Tre sp?r extraherade, 274 s.
- Identitetsbyte granskat visuellt. Originalsp?r sparade i ingest/personer_matning.json.
- Roll 1 kund; roll 2 servit?r (ursprungligt sp?r 3 t.o.m. ruta 450); roll 3 matb?rare (ursprungligt sp?r 2 plus sp?r 3 fr?n ruta 480).
- Blandade rutor 451?479 undantagna fr?n kroppsavl?sning; luckan f?r inte beskrivas som uppm?tt.
- 612 personrutor vid 10 fps, reserverade i befintlig budget; total 3502 av 5000.
- Kameraanalys p?g?r.
- c_ops.py ?teranv?nder Notans operationstexter; ?terst?r att k?ra och validera med f?rdiga indata.

## Senaste resultat
Kamera klar: 273/273 registrerade bilder, 0,541 px ?terprojektionsfel, fokal 948,54 px. Alla kamerakrav godk?nda.
Kroppssteget misslyckades f?re resultat: "Could not connect to the Modal server". Inga kroppsfiler skapade. Inga fj?rrjobb bekr?ftade.
Jutsu-projektet ?r fortfarande tomt, revision 0. Inga renderade resultat finns.
c_ops.py ?r syntaxkontrollerad men inte k?rd mot 3D-data; rumspassning och visuell kvalitet ?terst?r att verifiera.

?terstart fr?n projektroten (kr?ver fungerande anslutning till Modal):
```
scen/.venv/Scripts/python.exe scen/3d/ingest/ingest_klipp.py scen/klipp/c-sketch-tre.mp4 byggsten/jutsu/ut/c-sketch-tre/ingest --personer 3 --steg 3 --till golv
```
Personer och kamera ?teranv?nds. K?r inte --om personer: det skulle kasta den granskade rollmappningen.
Efter?t: k?r c_ops.py, kontrollera rum.json mot k?llan, k?r op1/op2 med f?rska Jutsu-revisionsvakter, granska stillbilder, komplettera brickans och terminalens animation, rendera delarna och muxa originalets ljud i j?mf?relsen. Detta ?r ?terst?ende arbete, inte genomf?rda steg.
