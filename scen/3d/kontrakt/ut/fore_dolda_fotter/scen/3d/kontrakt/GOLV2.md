# GOLV2: kroppens meter, platsens golv

Beslut före kodändring, 10 november 2026.

Kroppen behåller MHR-identitet, benlängder och den utjämnade skattningens
kameratranslation. Världspunkten är X = R · (F · pose/100 + cam_t) + C.
Ingen golvregel får multiplicera bara cam_t. Ingen kamera får flyttas för att
dölja en persons golvfel. Kontakt mäts; automatisk rotförflyttning stängs av.
Äldre sekvenser läses med cam_t_fore_golv, annars cam_t_fore_kontakt,
annars cam_t. Kontaktens tidigare poseändring återställs där förfält finns.
Originalfilerna behöver inte skrivas om eller ingest köras igen.

## Tillit och beslut

1. Synlig fot i personens egen bildruta och mask, tillförlitlig skattning,
   med låg vertikal rörelse: kontaktkandidat. Kontakt är modellbedömd,
   inte en fysisk inmätning. Median per person, sedan median mellan personer;
   många bilder av en person ger inte fler röster. Sulans offset är en prior.
2. Sittande höft mot en identifierad sitstyp ger ett svagare, antaget intervall.
   Sittande måste ha stöd i semantiken eller synlig hållning. En låg dold
   höft bevisar inte en stol. Sitsen anpassas till bäckenet, aldrig benlängden.
3. Flera personer jämförs i samma tagning. Den starkaste tillgängliga
   cue-familjen väljer golvet; svagare familjer får inte rösta bort synlig
   kontakt. Alla avstånd till det valda golvet sparas, även konflikter.
4. Flera tagningar av samma plats delar ett golv. Endast accepterad
   bildregistrering får överföra uppmätt relativ höjd mellan kamerastationer.
   Utan sådan koppling är överföringen antagen, med lokal evidens och
   registreringsosäkerhet redovisade. Ett gemensamt plan verifierar inte
   kamerornas relativa höjd. Dolda fötter används aldrig som golvlandmärken.
5. COLMAP:s accepterade relativa kamera och dess meterskala behålls. En
   korrigering av bakgrundens skala måste skala kameratranslation och
   bakgrundspunkter tillsammans kring samma origo; kroppens meter ändras inte.
   Ingen ny skala väljs ur enbart önskad möbelhöjd. Oidentifierbar skala är okänd.
6. MoGe-golv är modellbedömt och underordnat synlig kroppskontakt och
   identifierad sits. MoGe/COLMAP-konflikt sparas; ingen dold medelvärdesskala.
   Kroppslängdsprior och möbelpriorer är kontroller, inte oberoende mätningar.
   Antagen kamerahöjd 1,45 m används sist och märks antagen.

## Dolda ben och bildkostnad

En person vars ben aldrig syns placeras med sin skattade kameraposition.
Fotkontakt är okänd. Modellens fothöjd rapporteras som modellrest, inte som
uppmätt golv. Ingen vertikal eller strålriktningskorrektion av kroppen görs:
en sådan skulle flytta bildpunkter eller ändra skenbar storlek. Dold benpose
kan fortfarande få kontraktets längdbevarande stöd; dess antaganden och
eventuell silhuettkostnad redovisas separat. Bäcken och överkropp flyttas inte.

## Rapport och verifiering

Per plats och tagning: vald cue, status (uppmätt, modellbedömd, antagen),
spridning, avvisade cues med orsak, konflikt och om golvkontakt faktiskt syns.
Per person: kamerahöjd, fotrest med synlighet, bäcken/sits och handled/bord.
Kamerans avstånd till rummets kamera ska vara noll utan regiändring.
Ingen synlig golvkontakt innebär texten: ”Tagningen kan inte placeras
tillförlitligt i höjd: inget i bilden mäter golvkontakt.” Sits och djup kan
ge ett arbetsantagande men tar inte bort denna begränsning.

Före/efter mäts med samma rutor, masker, rigg och estimatorpunkter. Rotfel,
bildfel median/p90 och silhuett-IoU sparas, liksom alla försämringar och deras
orsaker. Flyttad kamera (+0,5 m sidled, +0,3 m upp, samma mål) granskas visuellt.
Snabb projektion är tillåten; den är inte ett verifierat Blenderresultat.
Diagnostiska toleranser ändras inte för att få proven att passera.
