# Scen3D: syfte, regler och var den passar in

## Varför den finns

Harnessen (4–6 nov) väljer ett biblioteksklipp åt en kund. Den gör också en **scenplan** (`video/format/h-scener.mjs`), som per beat säger om scenen ska behållas, vara fri, få kundens produkt, göras i kundens lokal, få en frontfigur, få eget tal eller förenklas. I scenplanen står:

> "harnessen ska veta när och varför en scen behöver göras om (för omrendering med enkla platshållare)"

Scen3D är den omrenderingen. Den gör om ett källklipp till ett rum med neutrala dockor, kameror, rekvisita och repliker med ordtider. Där kan varje beat med `omrendera: true` visas som det skulle se ut hos kunden, innan någon filmar. Ägarens formregel ur pass 8 är att varje scen behöver känsla, struktur och vad den kräver, helst visuellt (3D).

## Regler ur hagen-ui-wikin som styr bygget

| Regel | Så följs den |
|---|---|
| Ingen syntetisk likhet med källans skapare | Neutrala dockor (Mixamo X Bot) utan hår, i rollfärg (tröja), mörka byxor och en och samma neutrala hudton. Ingen rösttyp kopieras. |
| Designade röster, inte läppsynk | Piper (lokalt och gratis), med rösten vald per roll. Munnen följer den designade rösten och inte källpersonens mun. MediaPipes mun används bara i läget "Originalljud". |
| Inga fotorealistiska genererade scener; spela live, rendera inte | Uppspelaren bygger scenen i webbläsaren ur `scen3d.json`. Filmen `mvp-*.mp4` är bara en förhandsvisning för granskning. |
| Räls: ordning, rytm, krok, ljud, mekanik och syfte är låsta tills de öppnas medvetet | `langd` klipper aldrig ord. Tagningen kortas genom att pauserna krymper och talet går upp till ×1,15. Om målet ändå inte nås stannar den och förklarar varför (`--lage trim` öppnar spärren). En kopierad tagning upprepar inte repliken. |
| Teleprompter följer ordtider | Replikerna har ordtider ur källjudet (KBLab Whisper). Textningen framhäver ord för ord. |
| Casting märker repliker ("A → Ägaren") | `casting A --roll Ägaren [--rost] [--farg]`. Rollnamnet står före repliken i textningen, även när talaren är utanför bild. |

## Scenplanens verb och Scen3D:s operationer

| Scenplanens åtgärd | Operation i `op.py` | Läge |
|---|---|---|
| behåll | Ingen. Rälsen skyddar repliker och klipp. | Finns: `langd` är replik-säker och kopior är tysta |
| byt_produkt | `byt A:burger --typ pizza_slice` | Finns, med cirka tio föremålstyper |
| byt_lokal | Rummets mått, färger och möbler ur kundens lokalbank | **Saknas** (frö för 1.5) |
| frontfigur | `casting A --roll Ägaren --rost alma --farg #a05a3c` | Finns |
| eget_tal | `replik 3 --text "..."`: designad röst i samma lucka, ordtider, teleprompter. Rälsen varnar om texten kräver mer än 15 % högre fart än originalet. | Finns: 0,4–0,6 s med `rostserver.py`, ~6 s utan |
| forenkla | `ta-bort`, statisk kamera, inga effekter | Finns |
| (fart, stress, betoning, blick) | `intensitet`, `humor`, `langd`, `dolly`, `orbit`, `vand`, `titta` (bara huvudet, högst 80°) | Finns |

## Vad källklippet lär oss (ingest, `shots[].ingest`)

- **Kamera.** Varje tagning står still. Rörelsen i bild är under 1° (högst 10 px), alltså stativ. Utsnitten är MCU och CU på 0,8–1,1 m, med ett MS på 2,5 m som avslut. Kameran sitter 6–14 cm över hennes ögon och ser ner 11–17°, och 4–10 cm under hans ögon med 4–7° lutning. Brännvidden motsvarar 26,7 mm.
- **Klipp mot tal.** Bilden byter till talaren 0,05–0,07 s efter att hen börjat prata (J-klipp). Undantaget är insticket med servitören, där båda hörs utanför bild och B börjar 0,71 s före klippet. Detta är rytmen som rälsen skyddar.
- **Tal.** Talet fyller 70–98 % av varje tagning. Pauserna inne i tagningarna är 0–0,3 s.
