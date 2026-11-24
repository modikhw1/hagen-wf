# Rapport, domaren runda 4: ägarpanelen (K2)

20 nov 2026, kväll. Panelen är byggd helt av material som redan fanns. Inga betalda, generativa eller nätverksanrop har gjorts. Allt är skrivet under `motpart/runda-4/A-domare/`. Ingen ägardom finns ännu, och den här rapporten innehåller inga utfall.

## Starta panelen (ägaren)

Kör från repo-roten `C:\Users\praiseworthy\Desktop\hagen-wf` i PowerShell:

```
.\scen\.venv\Scripts\python.exe motpart\runda-4\A-domare\panel\server.py
```

Öppna sedan **http://127.0.0.1:5190/** i Chrome. Det tar ungefär 10 minuter. Avsluta servern med Ctrl+C när du är klar.

Efteråt kör domaren eller orkestratorn:

```
.\scen\.venv\Scripts\python.exe motpart\runda-4\A-domare\panel\sammanstall.py
```

**Kör inte `bygg_panel.py` igen efter att ägaren har börjat.** Mediernas och parens id slumpas om vid varje bygge, och då passar nyckeln inte längre till svaren.

## Filer (`panel/`)

| fil | innehåll |
|---|---|
| `bygg_panel.py` | urval, kontrollpar, omkodning till blinda filer |
| `server.py` | stdlib-server på port 5190: sida, `/api/par`, `/media/m_<hex>.(mp4\|png)` med Range-stöd och `POST /api/svar` |
| `index.html` | sidan, utan externa resurser |
| `par.json` | det enda sidan läser: slumpade id, meningen, medie-URL:er, `synk`/`ljud` |
| `nyckel.json` | system, klipp, källfil, ändringstyp, kontrolltyp och D:s egna mått per par. Servern serverar den aldrig, och anrop till den ger 404 |
| `urval_logg.json` | pooler, frö och dragning |
| `svar.json` | ägarens svar. Skapas vid första svaret, varje svar läggs till listan (skrivs atomärt och skrivs aldrig över) och speglas i `svar.logg.jsonl` (ren append). Varje svar har tidsstämpel, session, sekunder per par och om ljud slogs på |
| `sammanstall.py` | läser svar och nyckel. Ger giltighet, kontrollparen, utfall per system och ändringstyp, 1:1 per system och K2-diagnosen. Skriver `<svarsfil>_sammanstallning.json` |
| `svar_test.json` (+ `.logg.jsonl`, `_sammanstallning.json`) | mina fyra testsvar från verifieringen. De ligger avskilt från `svar.json`, som inte finns ännu |

## Vad panelen innehåller: 26 par

Frö `20261120` för urvalet och `20261121` för ordningen. Del 1 och del 2 är slumpade var för sig, och del 1 kommer först.

**Del 1, ändring (19 par = 15 riktiga + 4 kontroller).** Varje par visar meningen, originalet och förhandsvisningen. Där systemet har en rendering utan ändring visas den i mitten som jämförelse. Ägaren svarar på (a) "Syns det som meningen bad om?" och (b) "Är det fortfarande samma klipp där meningen inte ändrade något?", ja/delvis/nej, och kan lämna en kommentar.

| system (bara i nyckeln) | par | typ | medium |
|---|---|---|---|
| runda 3 C (mening → scenpaket, lådrendering) | 6 | rum/miljö "samma sak men i en bar"; föremål "byt burken mot en kaffekopp", "Ta bort disken."; kamera "kom närmare honom…" (B:s paket); handling "Låt henne räcka fram två smakprov." (B:s paket, filmremsa); kropp "låt kunden gå genom lokalen…" | stillbild |
| forvarld_karna (mening_motor + lokal Blender) | 2 | kropp: gå med attityd (guacamole s1 r44), byt hand (gelato s1 r78) | stillbild |
| arbetsbord v1 (regi → Three.js) | 1 | rum/miljö: restaurangkök med stekbord och bänk (guacamole) | video med ljud |
| Kimodo-SOMA-RP (generativ, dömd KILL på egna mått) | 2 | kropp: vänster hand upp till hylla (gelato); känsla "uttråkad och trött" (guacamole s4) | video med ljud |
| runda 3 D (medielager, ffmpeg/Demucs/Pillow) | 4 | skärmtext (zezuliverpool), ljud "ta bort musiken" (anettesrestaurang), montage −30 % (blackstone-743965, osynkat), b-roll (blubnan-763350) | video med ljud |

**Del 2, 1:1-trohet (7 par = 6 riktiga + 1 kontroll).** Frågan är "Är detta samma scen (rum, personer, kamera)?" (ja/delvis/nej) med kommentar. Paren:
- B:s frysta kedja på hold-out: sabai r37, faros_7540 r110, thepitaspot r271 (stillbilder)
- B på utvecklingsklippet a-sketch r399
- arbetsbordets Three.js utan ändring, på notan och guacamole (video)

Kimodo finns med trots att den bryter mot K7 i CM:s ändringsled. UPPDRAG.md säger att den domen fälldes på egna mått och inte på om känslan syns. Paren mäter bara det ägaren ser och är inget förslag om att väcka Kimodo igen.

## Urvalsregel

Regeln skrevs i `bygg_panel.py` före dragningen. Egna mått styr inte vilka riktiga par som kommer med.

- **C:** Poolerna består av C:s utförda meningar vars ändring går att se i en stillbild, för C har bara stillbilder. Pool och antal: plats 1, föremål 2, kamera 1, handling 1, kropp 1. Högst en variant per mening, där X och X@B räknas som samma. Dragningen görs med `random.Random(FRO)`.
- **D:** Poolerna består av alla utförda operationer med förhandsvisning, både urval och hold-out, en pool per lager. Ett par dras per lager oavsett D:s `syns`/`kvar`. Två av de dragna har D:s egna mått emot sig (montage `syns=False`, b-roll `kvar=False`).
- **forvarld_karna, arbetsbordets miljöbyte och 1:1:** Allt som fanns togs med. Det är 2, 1 och 2 par, plus B:s tre hold-out-klipp och ett utvecklingsklipp, en ruta per klipp.

**Bortvalt, med skäl:**
- C:s tidsändringar (g2 och q3 "långsammare", g6/a2/n_u1 "stabilisera", g7 "en sekund längre", n_t7 "korta ner", n_t11 "börja med punchlinen", B7 "ta bort scen 6"). Bara stillbilder finns, så ändringen går inte att se. De kräver video från C.
- C:s egna kontrollbilder (par_031, par_033). Jag gör egna kontroller.
- Kimodo fall 1 (runda hörn): det är samma klipp och tagning som fall 3, och tiden räcker inte.
- Arbetsbordets UI-skärmbilder (`ut/ui_check/regi_*.png`). De är gränssnittsbilder med etiketter och inga rena par.
- Kontaktkartor (`kontakt_*.png`, B:s `kontaktkarta*.png`). Samma material som paren men med etiketter.
- faros_7511 i 1:1. B:s kedja blev inte klar på det klippet.

## Kontrollpar (felinjektion), dragna bland material som inte redan var med

| nr i panelen | typ | gjort så | fälls om |
|---|---|---|---|
| 3 | ändringen saknas (video) | D-mening "byt den pålagda texten…" på mcdnyborg. Förhandsvisningen är originalet omkodat | a = nej |
| 12 | ändringen saknas (stillbild) | C "Byt glassen mot en kaka." (gelato, B:s paket). Efter-bilden är före-renderingen | a = nej |
| 8 | något annat ändrat (stillbild) | C "det ska vara på en uteservering" (notan, B:s paket). Den riktiga efter-bilden är spegelvänd | b = nej/delvis |
| 19 | något annat ändrat (video) | D "ta bort musiken" på steamhotel. D:s riktiga förhandsvisning har fått kraftig färgtonsförskjutning (hue 110°) | b = nej/delvis |
| 22 | fel scen (1:1) | originalruta ur sabai r163 mot rendering ur thepitaspot s2 r644 | samma scen = nej |

`sammanstall.py` skriver **OGILTIG** om något kontrollpar inte fälls, och då räknas K2-andelen inte. Det skriver "ofullständig" om något kontrollpar saknar svar. Logiken är prövad med syntetiska svar: när alla kontroller fälls blir det "giltig", och när kontroll 8 missas blir det "OGILTIG".

## Verifiering (gjord, server stängd efteråt)

- `GET /` 200, `/favicon.ico` 204. `/nyckel.json` och `/media/../nyckel.json` ger 404.
- Alla 63 medie-URL:er svarar 200/206 med Range.
- Headless Chrome via `arbetsbord/prov/node_modules/playwright-core` (channel chrome):
  - videorna når `readyState 4`, spelar och ligger i takt (2,03 mot 2,06 s)
  - bilderna laddar
  - 0 konsolfel och 0 sidfel
  - testsvaren sparades och listan växte från 3 till 4 utan att något skrevs över
- Skärmbilderna av intro, video-, tre-kolumns- och remspar har jag tittat på.
- Läckagesökning i HTML och `par.json` efter system-, modell-, klipp- och kontonamn (forvarld, karna, kimodo, arbetsbord, runda, opus, gemini, claude, codex, medielager, blender, notan, guacamole, gelato, sabai, faros, kontonamn…): 0 träffar.
- I mediefilerna är metadatan strippad (`-map_metadata -1`, `bitexact`), och Pillow skriver ingen PNG-text. Bannertexterna i soundoverlay-renderingarna ("Förvärld 3D – s3", "Fall 3 SDEdit…", "1:1 – 45.9mm") är svärtade, de översta 60–70 px av 1024. C:s kolumnetiketter (Original/A/B) är suddade.

## Kända svagheter

1. **Blindheten läcker via stilen.** Varje system har sin egen bildvärld:
   - C: grova lådor och streckgubbar, uppskalade från 270×480, med en gul suddfläck där etiketten låg.
   - forvarld_karna: Blender-kroppar.
   - arbetsbordet och Kimodo: Three.js-dockor, med en svart rand upptill där bannern låg.
   - D: riktig video.

   Ägaren ser alltså vilket "slags" system det är, men inte namnet. Jämförelser mellan system blandar ihop system och medium.
2. **C har bara stillbilder,** så kropps- och handlingsändringar döms på en ruta eller en remsa. forvarld_karna döms på en enda ruta (s1), och "gå genom lokalen" är en rörelse.
3. **Referensen "utan ändring" visas för C, forvarld_karna och arbetsbordet men inte för D och Kimodo.** Det gör det lättare att se en ändring där referensen finns, och det är också en stilsignal.
4. **Kontrollerna är få och tydliga,** två per typ. Att de fälls visar att ägaren tittar. Det visar inte att subtila sidoändringar skulle upptäckas. Spegling och färgton är grova fel.
5. **Montageparet spelas osynkat,** eftersom längderna skiljer sig. Ljudparen kräver att ägaren slår på ljudet själv. Det loggas i `ljud_hort`, så ett "nej" på ljudparet utan att ljudet varit på kan sorteras bort.
6. **Kimodo-orignalet är vänster halva av soundoverlay.** Dess topp är svärtad, så originalet ser något annorlunda ut än i andra par.
7. **Meningarna är systemens egna eller mina omformuleringar** av operationer (D, Kimodo, arbetsbordet). De är inte K1:s frysta CM-meningar, och några finns i två system (l1).
8. **Urvalet är litet:** 15 riktiga ändringspar, 1–6 per system. Utfallet per system är diagnos, inte statistik.
9. **En bedömare och en session.** Det slumpade id:t har inget med ägaren att göra, och den som vill backa och ändra får det senaste svaret räknat.

## Inte gjort

Ingen ägardom finns. Ingen K-status har flyttats.
