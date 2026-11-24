---
id: 0032
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
**1. Liggarna.** Båda är skrivna med 0031:s prompt, utan ändring:
- [b-tilltal](../../scen/3d/kontrakt/ut/b-tilltal-ravara_n06-hand/liggare_0032.json): 14 entiteter, 11 händelser (tala, lyfta, gissa ×3, hålla, scenbyte, väga, titta, reagera) och 4 förlopp (en gissning per person, plus avgörandet).
- [guacamole](../../scen/3d/kontrakt/ut/e-dialog-guacamole_grupp/liggare_0032.json): 12 entiteter, 7 händelser och 2 förlopp (missförstånd, upplösning).
- Båda går in i källan som `kalla_0032.json`.

**Blind?** Flash-körningarna är blinda. Mina egna är det inte: jag såg ägarens läsning i 0030. Det redovisas i liggarens `skriven_av`.

| | Ägaren | Stark (jag) | Flash, blint |
|---|---|---|---|
| guacamole: mobilen och blicken | viktigt | bär: `tittar_pa(A,mobil)` när han frågar; `fg_blick_fraga` | mobilen och `tittar_pa` finns, men **bär inte** (meningen = repliker och gester) |
| guacamole: baren mellan dem | viktig | bär: `star_mellan(bardisk,A,B)` | ramar |
| b-tilltal: gissningarna och vågen | (ingen läsning) | gissa ×3 och väga, som avgör; bär | gissningar med värden och väga; bär |

**2. Kontrollen:**
- **Mina:** 0 luckor och 0 faktafel. För guacamole först efter att kontrollen godtog konstanten `kamera` som roll; det var en allmän rättelse i kontrollen.
- **Flash:** b-tilltal 2 luckor, 11 faktafel och 10 täckningsfel; guacamole 1 lucka och 20 faktafel. Dessutom fältnamnet `lagg_add` i stället för `lagg_till`, och regi som inte följer mallen.
- Flash förstår alltså mening och händelser, men inte liggarens form.

**Det som behövdes för att schemat skulle bära:**
- `reagera` och `vaga` som ramar (fältet är redan fri text)
- platshållaren `{citat}` i regi-mallen, för text ur meningen (b-tilltal m3)
- konstanter (`kamera`) som roller i kontrollen

Inga fält ändrades. Prompten är oförändrad.

**3. Kedjan:** steget `liggare` ligger efter `mening` och före `kalla` ([kedja.py](../../scen/3d/gennedbrytning/kedja.py)). Leverantören (`stark` eller `flash`) är en parameter.
- **Gelato S1 genom hela kedjan:** liggaren är klar ur cachen; kontrollen och källan körs.
- **Provkonfig utan liggare:** `liggare VÄNTAR` med paket (`prompt_med_underlag.md`, `LAS-MIG.md`).
- **Brist:** en ändrad konfig ogiltigförklarar alla stegs cache, så hela kedjan kördes om (cirka 20 min). Nyckeln bör bara omfatta stegets egna fält.

**4. b-tilltal, tio meningar × fem** (`forvarld/btilltal/ut_0032/`):

| # | Mening | 0016 | 0030 | 0032, liggaren (5/5 alla) | Når |
|---|---|---|---|---|---|
| 1 | Ta bort scen 5 | bild | samma | `fg_scen=s5` | plan ✔ |
| 2 | Morten före Mads | bild | **föll** (grupp efter sig själv) | `fg_ordning_AB=fore_A` | plan ✔ |
| 3 | Byt "Vægt:" | bild | samma | `fg_text` (citat) | plan ✔ |
| 4 | Närmare Lærke i s6 | tillämpad | samma | `fg_kamera_nara` | plan ✔ |
| 5 | Ta bort vågen | bild | samma | `fg_vag=nej` | plan ✔ |
| 6 | Köttbit → ost | bild | typ tappad | `fg_kottbit_sak=ost` | plan ✔ (varning: bär) |
| 7 | Fjärde person | avvisad | avvisad | `fg_fjarde=4`, ingen regi | långsam väg: nej, 3,3 s |
| 8 | Glassbar | avvisad | avvisad | `fg_plats`, ingen regi | långsam väg: nej, 2,5 s (Flash missar att `byt_miljo` finns) |
| 9 | En sekund längre | bild | samma | `fg_langd_slut=1` | plan ✔ |
| 10 | Armarna i kors | avvisad | avvisad | `fg_hallning`, ingen regi | långsam väg: nej, 5,2 s |

**5. Jevs variation.** Regeln står i `PIPE.md`:
- Ett anrop. Valet gäller om dess sannolikhet är minst 0,5.
- Under 0,5: majoritet av tre parallella anrop. Utan majoritet: den långsamma vägen.
- Modellen ska låsas.
- **Underlag:** 125 val i 0031–0032 var stabila 5 av 5 (lägsta sannolikhet 0,52). Sannolikheten varierar dock upp till 0,17 mellan identiska anrop, så API:t samplar.
- **Tid och kostnad:** median 170–180 ms och cirka 1 700 tokens per anrop; ett extra anrop kostar cirka 0,00007 USD.
- Att bara visa det som är lagligt per scen behövdes inte.

**6. Guacamole, tre meningar** (skrivna före körningen, [meningar.json](../../forvarld/guacamole/ut_0032/meningar.json)), 5 av 5 var:
- **"Lägg ifrån sig mobilen när servitören svarar":** `fg_mobil_lagga`, utan regi. Spridningen: g3 och g4, `i_hand(A_hander,mobil)` upphör i s2, och mobilen flyttas.
- **"Titta på servitören hela tiden":** `fg_blick_fraga=B` (redigering, bär meningen). Spridningen: g1, g2 och g6, och `tittar_pa(A,mobil)` byts mot `tittar_pa(A,B)`.
- **"Servitören svarar långsammare":** `fg_tempo_svar=2`. Spridningen: g3, regi `tempo_handling s2h3`.

**Bakåtkompatibelt och tester:** 0032 ändrade ingen kompilatorkod, bara `liggare_kontroll.py` (fakta, inte planen). Källorna `kalla_0032.json` är nya filer. Testsviten körs med 0033.

## Bedömning
- **Schemat är allmänt:** tre klipp med helt olika mening (portionskontrast, gissningslek och missförstånd) fick plats utan nya fält, bara med nya ramar.
- **Det som behövdes:** `{citat}` i regi-mallen, ramarna `vaga` och `reagera`, och att kontrollen godtar konstanter som roller.
- **Slingan för tre klipp:** Jev väljer rätt för 24 av 24 meningar mot liggarna. 16 tillämpas i planen, och 8 går med skäl till den långsamma vägen (det som saknas är mimik, rörelse, nya personer och miljöer).
- **Svagaste ledet:** liggaren skrivs bäst av en stark modell. Flash ger luckor och fel form, så kedjans steg behöver en stark modell via API, eller paketet.
- **Enligt ägarens besked (vagen.md)** blir allt med nivån `generering` i liggarna ett nej, eller en uppgift för kroppskontrollern (0034).

## Ändrade eller nya filer
- **Kontrakt:**
  - nya: `ut/b-tilltal-ravara_n06-hand/{liggare_0032*,kalla_0032}.json` och `ut/e-dialog-guacamole_grupp/{liggare_0032*,kalla_0032}.json`
  - ändrad: `liggare_kontroll.py` (konstanter som roller)
- **Gennedbrytning:** `kedja.py` (steget `liggare`; före-kopia i `kontrakt/ut/fore_0032/gennedbrytning/`) och konfigarna `S1.json` och `S1_liggarprov.json`.
- **Förvärld:** `forvarld/liggare/prov_yta.mjs` (allmänt Jev-prov), `forvarld/btilltal/ut_0032/` och `forvarld/guacamole/ut_0032/`.
- `PIPE.md` och `NASTA.md`.

## Kontroll mot "Klart när"
- [x] Liggare för båda klippen, jämförelsen med ägarens läsning och kontrollens utfall (blindheten redovisad).
- [x] Steget `liggare` i kedjan.
- [x] b-tilltal 10 × 5, jämfört med 0016 och 0030.
- [x] Regeln för variation, med tid och kostnad.
- [x] Guacamoles tre meningar, med val och spridning.
- [x] Bedömning.

## Avvikelser
- Mina liggare är inte blinda (se ovan).
- Kedjans cache kördes om helt på grund av den ändrade konfigen (cirka 20 min).
- **Kostnad:**
  - Flash: 0,13 för liggarna och cirka 0,005 för den långsamma vägen
  - Jev: cirka 0,005 USD
  - Modal och Codex användes inte
- **Ägarens besked kom under arbetet** (vagen.md, 0034). Inget i 0032 gick genom generativ video.
