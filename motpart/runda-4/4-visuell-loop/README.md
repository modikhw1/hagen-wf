# Första visuella loopen

Öppna http://127.0.0.1:5204 när servern kör. Ett isolerat utvecklingsprov: original, befintlig ingest_v2-rekonstruktion och reversibel linsändring. Återanvänder arbetsbordets Three.js-renderare utan att aktivera stoppade attitydreglage. Ingen extern tjänst anropas.

Starta från repots rot:

    .\scen\.venv\Scripts\python.exe -I -X utf8 motpart\runda-4\4-visuell-loop\server.py --port 5204

1. Välj klipp och spela. Originalets ljud används, 3D följer videons tidsbas.
2. Hoppa mellan tagningar. Bedöm först oförändrad rekonstruktion.
3. Pröva vidare/snävare utsnitt och ångra. Endast linsvärdet i varje kameranyckel ändras. Kroppsspår, objekt och kamerans position/rotation bevaras exakt.
4. Spara bedömning/kommentar vid vald tid. Svar läggs till i ut/svar.jsonl med käll-/paket-/kodhash, recept och tidpunkt. Inga ägarsvar har skapats av agenten.

Detta är inte en blind jämförelse, ny ingest, inlärd stilöverföring eller godkänd rekonstruktion. Cyan är den gamla ingestens egna markeringar och kan själv vara felaktig/ofullständig. Originalkameran är ingestens skattning, inte oberoende kalibrerad kamera. Provet visar nu dessa begränsningar direkt.

Verifiering:

    .\scen\.venv\Scripts\python.exe -I -X utf8 motpart\runda-4\4-visuell-loop\test_contract.py
    node motpart/runda-4/4-visuell-loop/verify.cjs

Webbtestet använder befintlig Chrome och playwright-core i arbetsbord/prov. Servern måste vara igång. Testet skriver bilder och teknisk rapport i ut/qa, aldrig ägarsvar. Testet ändrar inga ingångsfiler. HTTP-testet sparar syntetiska svar endast i en separat temporär testmapp.

Se RAPPORT.md för observerade fel och nästa beslut. Att visningen fungerar innebär inte att rekonstruktionen fungerar.
