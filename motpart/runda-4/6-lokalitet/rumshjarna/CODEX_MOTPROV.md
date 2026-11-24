Du granskar kod i motpart/runda-4/6-lokalitet/ (cwd). Svara på svenska. Ändra inga filer. Skriv ditt svar som slutmeddelande.

Bakgrund: rumshjärna/1 (läs rumshjarna/RUMSHJARNA.md). En bildmodell genererar rummet utan personer (V2), en bild per tagning. Den används som hypotes i hål bakom personen i 0.0, men bara efter en grind.

Granska följande med fokus på korrekthetsfel (fel index, fel skala mellan rutnät, maskförväxling, cirkularitet, cache som ger fel resultat, tyst felhantering) och på om reglerna är allmänna (inga klippkonstanter):

1. lokalitet.py, bygg_nat(): parametern genfyll. Det gäller blocket med kantpixlar (flyg, ring), vakten "bakom &= ..." för observerad fyllnad ur andra rutor, blocket "(1b) rumshjärnan" (okg med person0, strålarna och djupet Zg) och bildtäckningen (obs_celler utan -3/-4).
2. lokalitet.py, main: blocket där genfyll laddas (gfil, synl, kz, dfel, trohet, grind 1b med förskjutning och skala, LOKALITET_UTAN_GENFYLL).
3. rumshjarna/hjarna.py: plan (ankare per L7-grupp, fas1/fas2, båda kandidaterna), codex_bild (parallellsäkerhet via session-id), registrera (ECC, WARP_INVERSE_MAP), valet mellan kandidaterna och fyllnad.json.
4. rumshjarna/rest.py: DIS-flödet som mått på lokal förskjutning (maskskalning, gradienturval).
5. rumshjarna/likhet.py: betingat(), att utseende aldrig länkar.

Kontrollera också att halvupplöst npz (obs_gpu), originalbild (540x960) och rutnätet F=3 linjeras rätt på alla ställen där genfyll används.

Leverans: en lista med fynd. Varje fynd ska ha fil:rad, allvar (fel / risk / stil), vad som händer i ett konkret fall och en föreslagen ändring. Avsluta med en rad "SAMMANFATTNING: n fel, m risker".
