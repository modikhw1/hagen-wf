# Rekvisita: första lokala versionen

Källan får ett eget, fryst `kalla_prop.json`. `kalla_prop.py` läser sparad semantik,
källvideo och befintliga handledspunkter. Ingen modelltjänst eller kroppskörning
används. `prop_referenser.json` innehåller manuellt avlästa regioner från två
källrutor per scen. Regionerna är ungefärliga omslutningar, inte segmentering.
Bildbevis från granskningen finns i `ut/prop_granskning/regioner_v2_*.jpg`.

Kör från projektroten, med `PYTHONIOENCODING=utf-8`:

```
scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_prop.py scen/3d/kontrakt/ut/b/kalla_jamn.json scen/3d/kontrakt/semantik/ut/b/semantik.json b scen/3d/kontrakt/ut/b/kalla_prop.json
scen/.venv/Scripts/python.exe scen/3d/kontrakt/kompilera.py scen/3d/kontrakt/ut/b/kalla_prop.json scen/3d/kontrakt/ut/b/regi_prop_tom.json scen/3d/kontrakt/ut/b/ny_data_plan.json
```

Källbyggaren kräver en ny utfil. Välj alltid en ny planplats manuellt: kompilatorn kan skriva över sin utfil. Ett tungt steg i taget. Den nya avgränsningen gäller data och plan, utan nya renderingar. Befintlig Blenderkod behålls bakom sitt gränssnitt och utvidgas inte.

## Vad värdena betyder

`semantik.props[].rekonstruktion` har typens ursprung och bankform samt en post
per scen. Scenposten anger hållare, hand och led, mallens yta eller kamerahand,
de två källregionerna med rutnummer och median RGB. Ursprung, metod och
konfidens finns separat för hållare, placering, bildregion, färg och mått.
De gamla fälten finns kvar för källor med uppmätta rumsobjekt.

Typ, användning och föreslagen hållare är `modellbedomd`, med den sparade
modellens namn. Motsägelser rättas bara med ett märkt antagande: b:s P3 anges
också där P1/P2 syns; a:s server anges där kunden bär tallriken. Notans gula
burk finns i bilden men saknas i semantiken. Den kompletteras från lokal
bildgranskning och märks `antagen` typ, med uppmätt region.

Region och RGB är `uppmatt`, med låg konfidens. RGB är medianen av mättade
pixlar inom regionen; även bakgrund och text kan ingå. Det är ingen uppmätt
materialfärg. Bankens färger används i denna version. Metrisk bredd härleds
ur regionens pixelbredd och antaget/estimerat djup. Höjd, djup, grepp och dolda
sidor följer bankens proportioner och är `antagen` eller `mall`.

## Placering och rörelse

`propplan.py` räknar ut samma matriser som Blender använder. Ett handfäste följer
handledens position och relativa rotation, efter samma kroppsstöd som filmen.
Första mätregionen bestämmer ett fast greppoffset vid handledens djup. Rörelsen
mellan rutorna kommer därefter från handen, inte från interpolering mellan
de två produktregionerna. En handöverräckning inom en scen modelleras ännu
inte automatiskt: samma hand behåller föremålet hela scenen. Det kan ge bildfel och lagras
som osäkerhet, inte som uppmätt greppkontakt.

Ett ytstöd är en faktisk skiva i den upplösta rumsmallen, synlig i scenen.
Regionens siktlinje skär skivans höjd. Om träffen ligger utanför skivan flyttas
den till dess kant, med avstånd och antagande i rapporten. Det är ett synligt
mått på dålig mallpassning, inte en dold korrigering. Köttet i b s8–s10 stöds
av vågens parametriska bricka. I s9 är köttet utanför bildens mätbara region;
det utelämnas när position saknas. Produkter utan mätbar position eller
explicit giltigt CM-fäste får ingen påhittad geometri.

B s5 använder förgrundsspår 2 från `personer_matning.json`: handens bildläge
följer boxens övre del och underarmen pekar mot bildens underkant. Djupet
0,65 m och anatomiska mått är antagna. Handen är kamerafäst i den redan införda Blenderbyggaren som två
primitiver; ingen ny propfilm har verifierat den. Det är inte en ny kroppsskattning. Kenny s2:s separata arm är ännu
inte rekonstruerad; där saknas därför delar av handlingen trots ett propfäste.

## Bank, regi och kvalitet

`propbank.py` har papper med kött, våg, glassked, glasspatel, tallrik, burk,
matlåda, kortterminal, mynt, kebabskärare, liten portion på tallrik och burgare.
Formerna använder låda, cylinder och ellipsoid. Varje form har greppunkt,
mallursprung och `modell_ref: null` för en framtida riktig tillgång. Den lila
`fiktiv_molnfrukt` är uttryckligen påhittad och används i produktbytesprovet.

`byt_prop` ändrar bankform och behåller fäste/mätregion. `lagg_till_prop`
accepterar banktyp med handfäste eller explicit ytplacering. `flytta_prop`
byter till explicit placering. `ta_bort_prop` tar bort geometri och kvalitetspost.
Okänd banktyp vid byte av en rekonstruerad produkt ger `ej_tillampat` med skäl.
Äldre uppmätta rumslådor behåller sitt tidigare beteende.

Kvalitetssidan har en rad per produkt och scen, byggstatus, fäste/yta, centrumfel
och breddkvot på provrutorna samt antaganden. Omslutningen är bankgeometrins
projektion, inte en segmentering av den synliga renderingen. Möbel- och
kroppsskymning kan alltså fortfarande dölja föremålet. Öppna alltid bladen.
Att passa första regionen och sedan mäta mot den är inte oberoende validering.

Test: `python -m unittest test_props` i kontraktsmappen. De vanliga kropp-,
text-, mall- och semantikproven ska också köras efter ändringar.

Händelser och edits från/till en händelse beskrivs i `HANDELSER.md`. Kvalitetsraderna kräver ingen rendering. `byggd` är det äldre fältnamnet för att geometri/matriser är upplösta i planen, inte att Blender har körts. Den aktuella omfattningen och verifieringen står i `ut/aterupptagning/rapport.md`.
