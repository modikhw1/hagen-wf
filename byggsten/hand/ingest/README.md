# ingest: Geminis läsning, byggd ur distinktioner

Sedan 14 nov 2026. Ligger under `byggsten/hand/`. **Inget anrop är gjort.** Prompten är bara torrkörd.

Ägarens besked 14 nov: Gemini är arbetshypotesen för bästa tolkning av indata, och prompten ska itereras mot återkoppling tills distinktionerna träffar. Den kan bli en serie bredvid dagens ingest eller bakas in i den.

## Vad som finns
| fil | vad |
|---|---|
| `distinktioner.json` | Liggaren. 14 distinktioner, var och en med regel (engelska, går in i prompten), fälten den styr, och skälet ur en mätning i `hand/`. Alla har status `obeprovad`. |
| `schema.mjs` | `scenlasning/0` i två pass: protokoll (det som syns och hörs, tidskodat) och tolkning (takter med ställe och uppställning, var poängen bor, kontrast, relation, grepp, källmärkning). |
| `kor.mjs` | Bygger prompterna ur liggaren. Utan `--kor` visar den bara prompterna. Med `--kor` gör den två anrop genom kedjans hjälpare `video/typer/lovable.mjs` och skriver under `ingest/ut/<id>/`. |

Torrkörning: `node kor.mjs <id> <video.mp4>`

## Tanken
Prompten ändras bara genom liggaren. En återkoppling från ägaren blir en ny eller ändrad distinktion med skälet citerat, och då går varje formulering att spåra. Det följer E1 i innehållsanalysen: distinktionerna avgör, inte ordvalet.

## Inte gjort
- Ingen körning mot video. Kostnaden är en uppskattning (2–4 öre per klipp på Flash, två anrop), inte mätt.
- Ingen mätare. Den ska jämföra två läsningar av samma klipp fält för fält, läsningen mot ffmpegs klippbyten och transkript, och mot tvillingparen och de 528 hårda motexemplen i `hand/ut/prov.json`.
- Ingen omvandling från `scenlasning/0` till regibordets tillstånd. Det är den som gör att bättre läsning syns i bilden.
- Ingen insamling av återkoppling i regibordet (ett fält per steg som sparas till en fil).
- Schemat är inte prövat mot hjälparens strikta läge.
- hagen-ui:s egen Gemini-analys är inte läst. Var den här läsningen ska sitta i förhållande till den är ägarens beslut.

## Om 3D som följer med
Också ägarens besked 14 nov, och inte påbörjat. Regibordet ritar dockor på schablonplatser. Två vägar: spela upp takterna som en animatik i bordet (går för alla klipp), eller rita den verkliga scenen ur `byggsten/brygga` för de klipp som har 3D (i dag notan). Fälten för uppställning i schemat (D05–D07) är det som skulle ersätta schablonerna.
