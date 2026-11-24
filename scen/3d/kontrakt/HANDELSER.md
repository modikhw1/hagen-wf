# Händelser och tidsankare

`kalla_handelser.py` läser befintliga spår, råa handledspunkter, propregioner,
repliktider och den redan sparade semantiken. Det kör ingen ingest, kropp,
modelltjänst eller rendering. Utfilen måste vara ny och ligga bredvid källan.

```
scen/.venv/Scripts/python.exe scen/3d/kontrakt/kalla_handelser.py scen/3d/kontrakt/ut/b/kalla_prop.json scen/3d/kontrakt/semantik/ut/b/semantik.json scen/3d/kontrakt/ut/b/kalla_handelser.json
```

För notan används `ut/notan/kalla_prop_golv.json`: den källkopian innehåller
den avbrutna körningens rättning av det tidigare golvbeslutet. De nya
källfilerna är redan skapade; välj ett nytt namn vid en ny körning.

`semantik.handelser` är valfritt. Varje post har `id`, `typ`, `vad`, `vem`,
`till_vem`, `prop`, `scen`, `start_s`, `slut_s` och `ursprung` med typ, metod,
modell och konfidens. Person/mottagare/prop kan vara null. Tiderna är på
hela klippets källklocka. En tidpunkt har lika start och slut; övriga poster
är spann. Provbilder och filbelägg ligger i `matning.handelsebevis`, knutna
med händelse-id. Underlagen är hashlåsta i `matning.handelsekallor`.

## Vad detektorn faktiskt säger

| Typ | Underlag | Vad som är osäkert |
|---|---|---|
| `person_synlig`, `person_forsvinner` | Första respektive gränsen efter sista detektion i `personer_matning.json`, annars äldre `personer.json`. | Spårstart vid klippgräns är ingen entré. Skymning och spårfel kan ge samma gräns. Luckor inuti spåret blir inte nya entréer. |
| `handmote` | Två olika personers råa handledspunkter inom 3 % av bildhöjden, minst två intilliggande rutor. | Diagnostiska val. Närhet i 2D bevisar varken kontakt eller överlämning i 3D. Punkter utanför bilden används inte. |
| `replik_start` | Sparad starttid i kalla. | Whisper märks uppmätt automatisk tidsuppskattning; modellbedömda repliker behåller modellursprunget. En repliks scen väljs efter den faktiska starttiden. |
| `prop_synlig` | Första manuellt avlästa propregionen i en scen. | Produkten är synlig senast här, men kan ha synts tidigare. Det är ingen kontinuerlig detektion av första synliga bildrutan. |
| `hallarbyte_kandidat` | Samma semantiska prop har olika föreslagna hållare i två handscener. | Antaget kandidatspann i den nya scenen. Klipp, fel hållare eller olika exemplar kan förklara skillnaden. Ingen säker mottagning. |
| `scen_handling` | `data.tagningar[].vad` i den sparade semantiken. | Modellbedömd handling över hela scenen. Ingen exakt handlingstid mäts. |

De aktuella klippen ger ingen säker fysisk överräckning och inget godkänt
handmöte mellan två uppmätta personer. Det går därför inte att sanningsenligt
tolka ”efter att hon har fått maten” som en exakt uppmätt tid här. CM kan
ankra till en avläst förekomst eller välja kanten på ett tydligt märkt
kandidatspann. Ursprung och osäkerhet följer med till planen.

## Regi och plan

`tid` stöds för `trimma_scen`, `skarmtext`, `byt_prop`, `lagg_till_prop`,
`flytta_prop` och `ta_bort_prop`. Exempel:

```json
{
  "id": "produktbyte_fiktivt",
  "op": "byt_prop",
  "ursprung": {"typ": "cm"},
  "prop": "prop_o1",
  "ny_typ": "fiktiv_molnfrukt",
  "tid": {
    "fran": {"handelse": "s6_prop_o1_synlig"},
    "till": {"handelse": "s8_semantisk_handling", "kant": "start"}
  },
  "kommentar": "PÅHITTAD produkt. Från första avlästa förekomsten, inte säker mottagning."
}
```

`kant` är `start` eller `slut`. Den måste anges för ett spann; en tidpunkt
behöver ingen kant. `offset_s` kan vara positiv eller negativ. En utelämnad
gräns använder den aktuella scenens början/slut. Numeriska start-/sluttider
och ankare får inte ange samma gräns. Okänt id, tomt/omvänt spann och tider
utanför klippet avvisas före bygget.

Planens `handelser[].forekomster` anger alla utdatascener och rutor där en
källhändelse finns efter trimning, omordning och duplicering. Bortklippta
händelser har en tom lista. `tillampat[].andring.tid` sparar begärda ankare,
upplösta källsekunder och utdatarutor. Tidsatta propändringar delar
propinstansernas `synlig_ut`; kroppar, kameror och filmens tidskarta påverkas
inte. Ändringarna tillämpas i ordning och varje edit är atomisk.

## Om ingest räknas om

Ingest varnar direkt när en omräknad mätfil gör ett känt manifest inaktuellt.
`kontrollera.py` och `kompilera.py` stoppar dessutom med exakt uppdateringskommando.
`kalla_omhasha.py <kalla.json> --uppdatera` är en uttrycklig manifestuppdatering:
originalet kopieras till `ut/fore_prop/omhashning_<tid>/` och ändrade pekare
loggas bredvid källfilen. Semantikens revision behålls eftersom bara
mätmanifestet ändras. Ändrad semantik/tidsbas kräver ett nytt källbygge.

Om ett händelseunderlag ändrats avvisas omhashning: skapa i stället en aktuell
propkälla och kör `kalla_handelser.py` igen med en ny utfil. Anpassa regins
revision till den nya källkopian. Äldre renderplaner och filmer ändras aldrig.

Prov: `python -m unittest test_handelser test_props` med kontraktsmappen i
`PYTHONPATH`, från projektroten. Slutrapport, riktiga planer och tidsmätningar
finns i `ut/aterupptagning/`.
