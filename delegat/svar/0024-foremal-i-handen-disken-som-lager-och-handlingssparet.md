---
id: 0024
status: blockerat
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
Punkterna 3, 4 och 5 är klara. Punkterna 1 och 2 är förberedda men inte körda, av två skäl:
- **fal-saldot är slut** (403 "Exhausted balance", se svar 0023).
- **Gatewayen är på gratisnivå** och nekar Gemini 2.5 Pro. Flash fungerar.

**1. Skeden i handen.** Prompten i 0023 är bytt till `P_FOREMAL` (`scen/3d/gennedbrytning/d2_video.py`). "Tomma händer" är struket, och skeden beskrivs i ordning: håller, för ned, skopar, lyfter, räcker fram. Kundens hand och disken ska fortfarande bort. Försöken heter `k2s` och `k2sn`. Startbild och nyckelbilder med skeden vid ruta 0 och 55 behöver ägarens GPT: indata och prompter ligger i `luma-agaren/gpt/NASTA-BILDER.md` och `0024/`. `e3_sked.py` lägger GPT-bilderna i den kamerafria ramen. Mätningen av om skeden stör handens läsning görs när k2s finns (k2 mot k2s, samma källa, bara prompten skiljer).

**2. Disken som lager.** *Tillägg: gjort i 0025 del B som V3 genom Codex, se `fargkod/blad_disk_och_rum_000.jpg`. "Bara disken" ligger kvar på plats och är kompletterad; i "rummet utan disk" syns golvet och bakre bänken, och det rutiga golvet är antaget.* Ursprungligen: fal är tomt, så indata ligger färdiga åt ägarens GPT i samma `NASTA-BILDER.md`: "bara disken" och "rummet utan disk", negativt formulerade och med en ny konversation per bild. `k_disk.py` mäter diskens kanter mot originalet (promille) och märker det tillagda som `antagen`, så fort bilderna finns.

**3. Samspelet** (`j_samspel_blender.py` läser ur den byggda scenen; `j_samspel.py` räknar i diskens ram). Fötterna är låsta på golvet, vilket är antagandet "står still":

| Mått ur kroppen | Dagens plan | Dagens kropp | k2-kroppen | Vad stämmer, vad kroppen rättar |
|---|---|---|---|---|
| Hur nära disken: höften bakom bakkanten (median) | staplatsen 0,84 m bakom | 0,82 m | 0,72 m (0,26 m när hon räcker fram) | disken står för långt bort |
| Tråget: ovankanten minus handens lägsta punkt | höjd 0,90 m, tråg saknas | 0,32 m i rutorna 59–61 | når aldrig under ovankanten: lägst 0,92 m, 0,14 m bakom bakkanten | i originalet skopar hon i tråget, så disken bör stå cirka 0,15–0,4 m närmare |
| Diskens djup: hur långt handen når förbi bakkanten | 0,70 m | 0,47 m | 0,75 m | djupet stämmer med k2 |

Utan låsta fötter lyfts höften cirka 0,5 m när hon böjer sig, i båda läsningarna. Rotens plats i världen är det svaga ledet, inte kroppens form. Datan ligger i `samspel/*_samspel*.json`.

**4. Handlingsspåret:** [handling/S1/handling.json](../../scen/3d/gennedbrytning/handling/S1/handling.json), med remsan i [remsa.mp4](../../scen/3d/gennedbrytning/handling/S1/remsa.mp4) och `remsa.jpg`.
- **Indelningen:** nio segment utan luckor (h1 0–7, h2 8–20, h3 21–58, h4 59–76, h5 77–82, h6 83–94, h7 95–108, h8 109–138, h9 139–147, i klipprutor; planens ruta = klippets + 7).
- **Ur mätning (`matt`):** gränserna, hållningen (ur bålens lutning), handens läge mot disken och rörelse, kundens hand i bild (ur ingestens kantmasker), och kameran (zoomar in och tippar ned i 8–58, tippar upp i 59–94, står still från 95).
- **Ur planen:** föremålet `A:hand:provsked`.
- **Ur Gemini 2.5 Flash (`last`):** verb ur ett litet ordförråd (sta, ga, luta_sig, rata_pa_sig, vanda_sig, titta, peka, ta, halla, lyfta, sanka, racka), kroppsdel, mål, kontakt och beskrivning. Två anrop kostade 0,017 USD.
- **Utfall:** när modellen fick handläget som fakta upprepade den mätfelet ("handen står stilla bakom disken" i h3), se `handling_med_handlage.json`. Utan handläget blev h3 `ta` (skopar), h8 `racka` med kontakten `kund:hand>A:hand:provsked`, och h6 och h7 riktades mot kunden.
- **Kvarstående fel:** h9 påstår att skeden är släppt, medan planen säger att den syns till ruta 156. Det står i `modellen_sager`.

**5. Fem CM-meningar mot spåret:**

| Mening | Pekar på | Vad som saknas |
|---|---|---|
| "Låt henne räcka fram två smakprov" | h3–h8 (`ta` … `racka`) som en följd | begreppet följd eller upprepning ("servera ett smakprov" = h2–h8), och smakprovet som eget föremål skilt från skeden |
| "Hoppa över när hon skopar" | h3, `handling=ta` | övergången: h4 börjar böjd. Hållningen före och efter ett borttaget segment behöver gå att knyta ihop, och kamerans zoom i h3 följer med |
| "Låt kunden ta emot med andra handen" | h8, `kontakt=kund:hand>…` | kunden som person med sida och hand. Planen har ingen kund, bara en hand i kantmasken |
| "Gör skopandet långsammare" | h3, `rutor` 21–58 | tempo som fält, och rörelserna inne i h3 (ned, ösa, upp) som delsegment. h3 är 38 rutor som bara heter "böjd" |
| "Byt glassen mot en kaka" | h3 `kontakt`, h8 `foremal` | innehållet (glassen i tråget, smakprovet på skeden) som id. Kaka betyder att greppet ändras (hand i stället för sked), och det sprider sig till `ta`, `halla` och `racka` |

## Ändrade eller nya filer
Under `scen/3d/gennedbrytning/`:
- **Nya skript:** `j_samspel_blender.py`, `j_samspel.py`, `l_handling.py`, `e3_sked.py`, `k_disk.py`.
- **Nya mappar:** `samspel/`, `handling/S1/` och `luma-agaren/gpt/0024/`.
- **Ny fil:** `luma-agaren/gpt/NASTA-BILDER.md`.
- **Ändrade:**
  - `d2_video.py`: `P_FOREMAL`, `k2s` och `k2sn`. `k2n` är borttagen, och jag tog också bort den tomma mappen `d_video/k2n` som jag själv skapat.
  - `STRATEGI.md`: lagren 2–4, samspelet, handlingsspåret och tre rader i "Prövat".
- **Utanför `gennedbrytning/`:** `delegat/svar/0023-…md` har nästa steg uppdaterat till `k2s` och `k2sn`.

## Kontroll mot "Klart när"
- [ ] En generering med skeden i handen, mätt: förberedd (`k2s`), stoppad av fal-saldot.
- [x] "Bara disken" och "rummet utan disk": indata åt ägaren färdiga, mätningen skriven.
- [x] Tabell för samspelet: tre mått mot dagens plan.
- [x] `handling.json` och remsan.
- [x] Fem meningar mot spåret.
- [x] `STRATEGI.md`.
- [x] Bedömning:
  - **Utan modell:** segmentgränser, hållning, kamerarörelse, kundens hand i bild, och handens läge mot möbeln, men bara när kroppen står rätt i rummet.
  - **Med en modell som ser klippet:** verbet, målet (kunden eller kameran), kontakten (skopar i tråget, kunden tar emot) och föremålets tillstånd (laddad sked, lämnad).
  - **Gränser före namn håller.** Modellen ska få gränserna och hållningen, inte osäkra mätningar.
  - **Nästa tagning:** prova formen på b-tilltal (tal, inget föremål) och guacamole S1 (två händer, föremål), och lägg till tempo och delsegment.

## Frågor
- **fal behöver fyllas på** (gäller också 0023). Cirka 0,50 USD räcker till `k2s` och `k2sn`.
- **Fyra bilder åt ägarens GPT,** enligt `scen/3d/gennedbrytning/luma-agaren/gpt/NASTA-BILDER.md`. Mätskripten kör sedan utan fler beslut.
- **Gateway-krediten verkar slut** (gratisnivå; Pro nekas). Flash räckte här.

## Avvikelser
- **Samspelet mäts med fötterna låsta**, alltså antagandet "står still" (märkt antagen), eftersom roten annars lyfts 0,5 m. Kroppens form ändras inte, och inga läsningar blandas.
- **Kundens hand som signal** är tillagd utöver uppdragets lista. Den gav gränsen för mottagandet (h8).
- **Gemini Flash i stället för Pro,** eftersom Pro nekas på gratisnivån.
