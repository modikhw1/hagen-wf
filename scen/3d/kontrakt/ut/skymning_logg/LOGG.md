# Skymning i 3D — arbetslogg 2026-11-12

- Lästa regler och baslinje: `CODEX-SKYMNING.md`, `CODEX-FOREMAL.md`, `PIPE.md` Öppet 6, `foremal_logg/LOGG.md`, `NASTA.md` och `fore_vaggar/omkord_ratt_skymning/`.
- Orsak funnen i `skymning.py`: maskprovet kastar en stråle genom provpixeln men stoppas vid endast närmaste MHR70-punkts Z-djup; punktens riktiga X/Y/Z används inte.
- S11 ut-ruta 439 (S11 lokal ruta 15), disk_C före möbellyftet: 5 480 maskprov; 85 gamla träffar på pixelrader 994–1022, varav 30 höft och 55 arm/hand.
- 30 höftprov får MHR70 10 (djup 1,1670 m, världshöjd 0,8154 m); 55 arm/handprov får MHR70 31/41/49/62 (djup 0,8796–0,9503 m, höjd 0,9382–1,0252 m); diskens topp är 0,9000 m.
- Gamla pixelstrålen träffar vid djup 0,8005–0,8368 m och räknar därför handen som skymd; riktiga 3D-segment missar alla 85 före lyftet. På bildbekräftad plats blir gamla 355 = 166 höft + 189 hand, nya behåller bara de 166 äkta höftträffarna.
- Ordningsfel funnet: `kvalitet.planbeslut` (möbelintervall + skymning) körs före `bildkamera`/`mobellyft`; en bildbekräftad disk kan därför strykas innan `kvalitet.mobel_lyft.status=flyttad` finns.
- `kontrakt/skymning.py` ändrad: `_rutdel` sparar vald MHR-punkts hela kamerarums-XYZ; `konflikt` transformerar punkten till världen och provar lådan mot segmentet kamera–punkt med oförändrad 5 cm-marginal.
- `kontrakt/kompilera.py` ändrad villkorligt: bara när en deklarerad möbel har `bild` körs `bildkamera`/`mobellyft` före `planbeslut`; övriga planer behåller den gamla anropsordningen.
- Bildbekräftad möbel (`mobel_lyft.status=flyttad`) prövas på sin flyttade plats av `mobelintervall`; kvarvarande konflikt bevarar möbeln och skrivs som `granskonflikt` i stället för att stryka den.
- Prov: hand över disk ej skymd, höft bakom disk skymd och bildbekräftad möbel bevarad; `test_snabb` 16, `test_deklaration` 7, `test_rum` 3, `test_scenbrief` 5 — alla OK.
- Orkestrator b: `python klipp_kor.py b-tilltal-ravara prepare --variant n06-skymning --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning2/deklaration_n06.json`; därefter samma kommando med `render`.
- Kontroll: `python kontrakt/kor_klipp.py notan_berattat ingest/ut/notan-tagningar ../klipp/d-dialog-notan.mp4 --kalla kalla_mobelintervall.json --undermapp skymning --hoppa-render`; motsvarande guacamole med `e-dialog-guacamole`, dess ingest/video och `--kalla kalla_vaggar.json`.
- Kvar: orkestratorn jämför notan/guacamoles nya `skymning.atgarder` mot rätt baslinjes 0/0 och kör n06; bar har inga möbelobjekt och behåller 0 åtgärder. Ingen full kompilering eller rendering kördes här.
