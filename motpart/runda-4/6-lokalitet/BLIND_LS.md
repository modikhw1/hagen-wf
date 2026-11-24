# Uppdrag: blint parvis prov av två 3D-rekonstruktioner per tagning

Du arbetar i `motpart/runda-4/6-lokalitet/` (cwd). Svara på svenska. Ändra ingen kod.

## Varför

Vi bygger en 3D-nollpunkt (0.0) ur korta restaurangvideor. Den ska kunna regisseras om: kameran ska kunna flyttas och föremål bytas ut. Det finns två sätt att bygga rummet och föremålen, X och Y. Vilket som är vilket är slumpat per tagning och okänt för dig. Avgör vilket som är bäst för att regissera om scenen.

## Material

Katalog `ut/blind_ls/`, tagningarna står i `lista.json` (`<klipp>/<sid>`). Per tagning:

- `<klipp>_<sid>_orig.png`: originalbilden
- `<klipp>_<sid>_X_0.png` och `_Y_0.png`: sedd från originalkameran
- `_X_35.png` och `_Y_35.png`: kameran vriden 35°
- `_X_50h.png` och `_Y_50h.png`: hela rummet vridet 50°

Personerna är blå dockor och är likadana i X och Y, så döm inte dem. Mörka partier i vridna vyer är ytor originalkameran aldrig såg.

## Bedöm per tagning

1. **Från originalkameran:** vilken liknar originalet mest? (X / Y / lika)
2. **Rummet vid vridning:** golv, väggar och bänkar hela och rimliga, inga skärvor eller hål. (X / Y / lika)
3. **Föremålen vid vridning:** tallrikar, kärl och mat är hela och står på ytor. (X / Y / lika)
4. **Helhet för att regissera om:** (X / Y / lika)
5. **God nog** för vardera, som utgångspunkt för att regissera om: X ja/delvis/nej, Y ja/delvis/nej
6. Kort skäl, och vad som är fel i den sämre.

Titta på varje bild med ditt bildverktyg. Gissa inte utifrån filnamn.

## Leverans

- `ut/blind_ls/dom.json`: en post per tagning `{tagning, original, rum, foremal, helhet, god_nog_X, god_nog_Y, skal}`
- `ut/blind_ls/DOM.md`: sammanställning med antal X/Y/lika per kategori, god nog-fördelning för X och Y, vanligaste fel i vardera, och vad den bättre fortfarande gör fel. Max 50 rader.

Sista raden: `KLAR` eller `BLOCKERAD: <orsak>`.
