Du arbetar i motpart/runda-4/6-lokalitet/ (cwd). Svara på svenska.

Uppgift: förbättra väljaren rumshjarna/valjare.py (läs docstringen). Gemini har granskat den mot originalrutorna i rumshjarna/VALJARE_RAPPORT.md och ut/agy/rumshjarna/valjare_granskning.json (per tagning: mening, viktigast, ratt, saknas, brus). Minsta mängden täckte scenens kärnmening i 18 av 38 tagningar.

Gör de allmänna förbättringar rapporten föreslår (felmönster 1–6, förslag 1–5) som går att göra med signaler som redan finns, utan nytt GPU-anrop och utan klippkonstanter:
- handkopplingen begränsas till huvudpersonen
- föremål som verkligen hålls får vara stora (närbildskärl)
- storlekstaket och skärpan kalibreras mot små högkontrastobjekt
- minsta andel per roll
- dekor får inte ensam vara platsmarkör
- grafiköverlägg (sedlar, klistermärken) upptäcks och hålls utanför objekten, så långt det går

Rör bara rumshjarna/valjare.py. Kör den på alla fem klippen: .venv/Scripts/python.exe -I -X utf8 rumshjarna/valjare.py <klipp>, för duepiani, spanjorskan, 08burgerkebab, babasburgers och kennysgelato2.0.

Mät själv mot Geminis facit (valjare_granskning.json): andel tagningar där minsta mängden täcker allt i 'viktigast' som har en motsvarande OneFormer-instans, före och efter. Skriv ett litet mätskript rumshjarna/valjare_matt.py. Undvik överanpassning: ändra bara vikter och trösklar som har ett allmänt skäl, och skriv skälet i koden.

Slutmeddelande: före/efter-måttet per klipp, vad du ändrade och varför, och vad som återstår och inte går utan ny signal (t.ex. matnärbilder som OneFormer slår ihop). Sista raden: KLAR eller BLOCKERAD: <orsak>.
