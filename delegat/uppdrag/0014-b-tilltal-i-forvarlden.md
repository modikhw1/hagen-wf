---
id: 0014
titel: Första semantiska ändringarna på ett klipp som kedjan byggt själv: b-tilltal i förvärlden
status: redo
från: orkestratorn (Fable)
datum: 2026-11-12
följer: 0012
tillåten_skrivning: [forvarld/btilltal/]
---

## Mål
Det ska vara känt vad som håller och vad som brister när en CM ändrar ett klipp semantiskt i förvärlden, på ett klipp som kedjan har byggt utan ägarens input. Hittills är förvärlden och Jev bara provade på Notan, som är handbyggd.

## Bakgrund
Syftet med hela scenkedjan är lättviktiga scener som en CM kan ändra med ord. Kvällens arbete har gällt geometrin. Det här uppdraget vänder tillbaka till syftet och frågar var ändringar faktiskt brister, så att nästa geometriarbete väljs efter det och inte efter precision för sin egen skull.

Läs: `forvarld/varld/README.md` (särskilt "Snabbvägen: ändring, visning, kompilerad plan" längst ned) och `SNABB-LOGG.md`, `forvarld/jevprov/README.md`, `scen/3d/SYFTE.md`, och kontraktet källa/regi under `scen/3d/kontrakt/`. Jev (TypeSafe System One) väljer bland färdiga alternativ; det hittar inte på.

Utgå från den senaste planen för `b-tilltal-ravara`: `n06-grupp` om 0012 är klart, annars `n06-matt`. Är 0013 klart, ta `n06-hand`.

## Att göra
1. **Tio meningar som en CM kunde skriva om just det här klippet**, på svenska, spridda över det förvärlden säger sig kunna och det den troligen inte kan. Minst: ta bort en tagning, byt ordning på två gissningar, byt en skärmtext, flytta kameran närmare i en tagning, ta bort vågen, byt köttbiten mot något annat, låt en fjärde person gissa, flytta scenen till en annan miljö, gör slutet längre, ändra en persons hållning. Skriv dem innan något körs, och ändra dem inte efteråt.
2. **Kör dem genom befintlig väg** så långt den går för ett klipp som inte är Notan: tillståndet som Jev ser, routningen (familj och delar), den ändrade regin, och kompilering genom snabbvägen. Allt nytt (tillstånd, regi, utdata) läggs i `forvarld/btilltal/`. Kopiera det som behövs dit i stället för att ändra i `forvarld/varld/` eller `forvarld/jevprov/`.
3. **Per mening:** var den stannade (tillstånd saknar begreppet, Jev valde fel, regin kan inte uttrycka det, kompilatorn föll, resultatet blev fel i bild), och vad i scenens data som saknades för att den skulle gå.
4. **Vad Notan-vägen antar som inte gäller här:** en person per tagning, montage utan dialogaxel, föremål på möbler och i händer, kameragrupper, lägen per grupp.

## Gränser
- Bara nya filer under `forvarld/btilltal/`. Inget ändras i `scen/`, `forvarld/varld/` eller `forvarld/jevprov/`.
- Jev-anrop mot TypeSafe är förhandsgodkända som modellanrop enligt `REGLER.md`, tak 0,30 dollar. Nyckeln läses på samma sätt som i `forvarld/jevprov/prov.mjs` och skrivs aldrig ut.
- Starta ingen tjänst på 5180, 5181 eller 5190. Webbvärlden på 5195 behöver inte startas; kompilering och en stillbild per ändring räcker.
- Bygg inga nya förmågor. Uppdraget är en mätning av läget. Går en mening inte, är det ett resultat.

## Klart när
- De tio meningarna finns i en fil med tidsstämpel före första körningen.
- En tabell: mening, Jevs val, väntat val, hur långt den kom, vad som saknades.
- För de meningar som gick hela vägen: en bild före och efter, och en rad om bilden visar det meningen bad om.
- En lista, högst åtta rader, över vad scenformatet behöver bära för att de övriga ska gå, ordnad efter hur många meningar varje sak låser upp.
- Tre rader: vilket geometriarbete från kvällen spelade roll för ändringarna, och vilket gjorde det inte.

## Leveransform
`delegat/svar/0014-b-tilltal-i-forvarlden.md` enligt mallen, högst cirka 70 rader.
