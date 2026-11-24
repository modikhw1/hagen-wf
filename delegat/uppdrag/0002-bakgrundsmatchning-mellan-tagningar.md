---
id: 0002
titel: Mät överlapp mellan tagningar ur bakgrunden (personer maskade)
status: redo
från: orkestratorn (Fable, ägarens session 12 nov kväll)
datum: 2026-11-12
följer:
tillåten_skrivning: [scen/3d/ingest/bakgrund_prov/]
---

## Mål
Det ska vara känt om bakgrunden i ett klipp räcker för att mäta hur kamerauppställningarna förhåller sig till varandra, så att rummets topologi och avstånd inte behöver gissas av en språkmodell. Provet görs på `b-tilltal-ravara` och ett klipp till.

## Bakgrund
Läs `scen/3d/PIPE.md`: Grundregeln och Öppet punkt 6. Spår (b) där är detta uppdrag och har aldrig provats. Spår (a), Gemini som skriver deklarationen, ger rätt personer och ungefär rätt topologi men lämnar två gissningar: om två tagningar delar kameraplats, och avståndet mellan rummets hörn (2,3 m i en omgång, 4,1 m i en annan). Ingenting i kedjan mäter det i dag.

Uppdrag 0001 undersöker samma brist från andra hållet (de lösta kamerorna). Uppdragen är oberoende, och 0001 behöver inte vara klart.

## Underlag
- Tagningsgränser och nyckelbilder: `scen/3d/ingest/ut/b-tilltal-ravara-tagningar/` (se även `scen/3d/ingest/rum_detektera.py` för hur nyckelbilder väljs)
- Personmasker eller personrutor finns i ingestens utdata för klippet. Leta där innan något eget byggs.
- Ägarens läsning som facit för topologin: `scen/3d/ingest/ut/b-tilltal-ravara-tagningar/plats/deklaration.json` (v0.3): samma lokal, de två männen på ungefär samma ställe, Lærke i en vinkel som öppnar mot vågen.
- Andra klippet: `e-dialog-guacamole` (facit finns) eller `kand-kennysgelato` (rörlig kamera). Välj det som har mest synlig bakgrund.
- Python: venv i `scen/.venv`. Använd det som redan är installerat (OpenCV med SIFT eller ORB räcker för ett första svar).

## Gränser
- Bara nya filer i `tillåten_skrivning`. Inga ändringar i befintlig kod.
- Installera ingenting. Om LoFTR, COLMAP eller liknande skulle behövas: gör provet med det som finns och skriv i svaret vad det andra väntas tillföra. Det blir då ett eget beslut för ägaren.
- Inga nätverksanrop, ingen Modal, ingen Gemini.
- Egna trösklar (antal matchningar, inlier-andel) är diagnos och inte krav. Redovisa talen och döm inte godkänt eller underkänt efter dem.

## Klart när
- En matris över tagningspar för varje klipp: antal matchningar utanför personmasken, inlier-andel, och vilken modell som förklarar dem bäst (homografi = samma kameraplats med ren rotation eller zoom, essentiell matris = förflyttad kamera, ingen = inget mätbart överlapp).
- För par med överlapp: relativ rotation i grader och, där det går, förflyttningens riktning. Skalan är okänd i monokulär matchning; säg det uttryckligen och ange vad i bilden som kunde ge skala (kakelstorlek, diskens höjd, personens längd).
- Jämförelse mot facit: vilka av ägarens påståenden om b-tilltal som mätningen bekräftar, motsäger eller inte säger något om.
- En bedömning i högst fem rader av om spåret är värt att bygga in i kedjan före deklarationen, och i så fall vilken utdata lösaren skulle få (till exempel "S1, S3, S4 delar kameraplats, mätt").
- Två eller tre bilder med ritade matchningar för de tydligaste paren, så att ägaren kan se det med egna ögon.

## Leveransform
`delegat/svar/0002-bakgrundsmatchning-mellan-tagningar.md` enligt mallen, högst cirka 80 rader. Skript, matriser (JSON) och bilder i `scen/3d/ingest/bakgrund_prov/`.
