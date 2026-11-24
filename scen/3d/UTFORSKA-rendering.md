# Att utforska: renderingshalvan (ägarens not, 8 nov 2026)

Ägarens bedömning av MVP:n (`verifiering/fas4/mvp-xbot.mp4`):
- Vissa delar har onödigt mycket detaljer, och andra ser lite konstiga ut. Dockorna i animationerna är lite konstiga.
- Analysen av originalet är halva jobbet. Den andra halvan är att rendera modellerna.

Riktning att pröva (inte påbörjad):
- **Blender med MCP** (eller liknande verktyg) som skapar olika meshes som kopplas in. Alternativt **typfall** som abstraheras ner till mycket enkla versioner av slutmålet.
- **Snabb redigerbarhet, helst JSON-baserad.** Ägaren ser själv att det kan krocka med komplexiteten. Med Blender kan utseendet standardiseras, med givna standardmodeller för kropp och annat.
- **Återanvänd det som fungerar**, till exempel kameraanvändningen, om det inte redan finns standardiserade och snabba sätt att föra scener vidare.
- **Ägarens fråga:** hur avancerat är det att få till en PS2-stil, ungefär som GTA Vice City?

Beslut i samma svar:
- Silhuettkravet (IoU ≥ 0,5) var mitt eget påhitt och ska inte behandlas som krav. Det får finnas kvar som diagnosmått.
- 1.5 väntar (`FRON-1.5.md` är fortfarande utkast).

Att veta innan något byggs:
- **C: var full den 8 nov** (476 MB ledigt av 237 GB). Blender (cirka 1 GB uppackat) får inte plats. Ägaren avbröt mätningen av cacheminnena, så inget har rensats.
- Kandidater att undersöka:
  - lågpolygonala riggade CC0-baser: Quaternius, Kenney;
  - `blender-mcp` (ahujasid) eller Blender i bakgrundsläge via bpy-skript med export till GLB;
  - PS2-utseende i three.js: låg upplösning uppskalad med nearest, vertexljus eller Lambert, målade texturer med låg upplösning, dimma, vantar i stället för fingrar.

## Svar 8 nov: är Blender rätt verktyg?

Ja, men som **kitfabrik på serversidan**, inte som det som visar scenen. Blender har ingen lätt visare för webben. Visningen förblir three.js (under 1 MB) med GLB-filer.

- **Blender på servern:** körs i bakgrundsläge med Python-skript, JSON in och GLB ut. Antingen `blender -b --python bygg.py -- order.json`, eller `bpy` från pip i en process som hålls varm. Ett pass tar sekunder till minuter, så det körs **inte** vid varje ändring.
- **Kitet:** en enhetlig stil. Ett par lågpolygonala kroppar med standardskelett och riktiga munformer, rekvisita och rumsmoduler med namngivna delar och färgfält.
- **JSON-scenen** pekar på kit-id plus parametrar (färg, mått, munform, placering). Ändringar sker i webbläsaren på millisekunder, som `op.py` i dag.
- **Server-pass bara för nya tillgångar,** till exempel ett nytt föremål eller ett rum ur kundens lokalbild. Asynkront och cachat.
- **Där Blender ger mest:** enhetlig stil (mycket av det som ser "konstigt" ut i dag), bakat ljus som gör visningen billig och ger PS2-looken, riktig rigg och riktiga ansiktsformer, samt varianter i mängd.
- **`blender-mcp`** passar för att ta fram kitet interaktivt, inte för produktion. Produktion bör vara deterministiska skript.
- **PS2 eller Vice City är rimligt:**
  - 500–3000 trianglar per figur;
  - texturer på 128–256 px;
  - vantar och målade ansikten;
  - bakat ljus, dimma och låg upplösning som skalas upp.

  Det svåra är att göra figurerna, inte att visa dem.
- **Godot** kan exporteras till webben och har textbaserade scener, men är tyngre (tiotals MB). Det lönar sig bara om en hel spelmotor behövs.
- **Första test:** en PS2-figur och ett rum, inkopplade i nuvarande spelare.

## Diskplats för Blender (Windows, 4.x)

| Del | Ungefär |
|---|---|
| Nedladdning (zip eller installerare) | 350–400 MB |
| Uppackad installation | 1–1,3 GB |
| `bpy` från pip (Blender som Python-modul) | cirka 1 GB installerad |
| Kit, cache och tillfälliga filer | 0,5–1 GB |
| **Att frigöra innan start** | **minst 2–3 GB, gärna 5 GB** |

C: hade 476 MB ledigt den 8 nov.
