# byggsten

Fristående byggstenar. Sedan 14 nov 2026.

Här prövas delar som kan höra till förvärlden och slingan (källa → Jev → regi → bild), men som byggs var för sig. En byggsten kan kopplas in i den nuvarande kedjan (`scen/3d/`, `forvarld/`) eller ändra riktningen. Ingenting här är en del av kedjan förrän ägaren har bestämt det.

## Regler
- En sak per byggsten, i en egen mapp med en egen README: vad som går in, vad som kommer ut, i vilket format, och vad som är prövat.
- Byggstenarna importerar inte varandras kod. De talar via filer.
- En adapter som läser kedjans utdata får importera kedjans kod för att läsa (till exempel `jutsu/notan_export.py`, som använder `kontrakt/trohet.py`), men skriver bara under `byggsten/`.
- Varje byggsten har ett eget prov eller en logg som visar vad den klarar och var den tar stopp.
- Rör inte `app/`, `video/`, `scen/` eller `forvarld/` härifrån.
- Kostnader (credits, Modal) loggas per prov.

## Byggstenar
| mapp | vad | läge |
|---|---|---|
| [jutsu/](jutsu/) | Higgsfield 3D Jutsu: en hostad Blender med versionerade scener, styrd via MCP. Vad den klarar och var gränserna går. | experiment |
| [brygga/](brygga/) | Sammanställning från kedjans läsning till scenpaket/1, med grindar (G1–G7) och ett bpy-skript som körs både i lokal Blender och i Jutsu. Mandat från ägaren 14 nov: ok att ändra hur data sammanställs. | fungerar på notan |
| [hand/](hand/) | Ur bankens metadata: ryggraden (typ, takter, fingrar med räckvidd), anpassning mot en kunds linje, ställen per takt, rutter mellan två klipp, Jev-yta med låsta prov, blockout. | v0, obedömt |
| [hjarna/](hjarna/) | Problembild: vilken motor förstår vad en semantisk ändring gör med det som gör klippet bra, och varför. Binder scenlagret (liggare, Jev, förvärld) till innehållsanalysen (formatkort, bank, serie). Ingen lösning. | problembild |
| [rumshypotes/](rumshypotes/) | Rumshjärna: läser klipp för klipp, håller hypoteser om rummet i 2D med sannolikhet, omprövar dem och ger ett recept som Jutsu bygger på sekunder. Uppdraget i `UPPDRAG.md`. | experiment att ärva, se `EXPERIMENT.md` |
