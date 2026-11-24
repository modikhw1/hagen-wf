# Motprov 5: fotkontakt i Due Piani

Kört från `6-lokalitet/`:

```powershell
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/audit.py basic
.venv/Scripts/python.exe -I -X utf8 -W ignore ut/codex/feet_injection.py
```

**Nio tagningar har exakt `kamerahojd.m == kamerahojd.fotter_m`, till lagrad millimeterprecision.** I samtliga är skalkällan `fotkontakt`. Det är en konstruktionsidentitet. Dessutom sätter S2 höjden direkt från fötterna utan något uppmätt golv. S8/S10 har varken fotmått eller golvhöjd och antar 1,40 m.

| Tagning | m | fotter_m | m − fotter_m | fot_over_golv_m per person | Skalkälla | Kontaktskala / personyteskala | Höjd med enbart personyteskala, cirka m |
|---|---:|---:|---:|---|---|---|---:|
| S1 | 1.467 | 1.467 | 0.000 | A: 0.080, B: 0.284 | fotkontakt (fötter på MoGe-golv) | 1.077 / 1.022 | 1.392 |
| S2 | 1.372 | — | — | A: 0.080 | kropp (SAM3D-djup mot MoGe-personyta) | 0.715 / — | — |
| S3 | 1.431 | 1.431 | 0.000 | A: 0.080 | fotkontakt (fötter på MoGe-golv) | 0.972 / 0.966 | 1.422 |
| S4 | 1.510 | 1.510 | 0.000 | D: 0.080 | fotkontakt (fötter på MoGe-golv) | 1.086 / 1.303 | 1.812 |
| S5 | 1.529 | 1.529 | 0.000 | D: 0.080 | fotkontakt (fötter på MoGe-golv) | 1.054 / 1.345 | 1.951 |
| S6 | 1.511 | 1.511 | 0.000 | D: 0.080 | fotkontakt (fötter på MoGe-golv) | 1.040 / 1.160 | 1.685 |
| S7 | 1.501 | 1.501 | 0.000 | D: 0.080 | fotkontakt (fötter på MoGe-golv) | 1.176 / 1.333 | 1.701 |
| S8 | 1.400 | — | — | saknas | MoGe-metrik, ej ankrad (antagen) | 1.000 / — | — |
| S9 | 1.556 | 1.556 | 0.000 | D: 0.080 | fotkontakt (fötter på MoGe-golv) | 1.154 / 1.386 | 1.869 |
| S10 | 1.400 | — | — | saknas | MoGe-metrik, ej ankrad (antagen) | 1.000 / — | — |
| S11 | 1.502 | 1.502 | 0.000 | C: 0.080 | fotkontakt (fötter på MoGe-golv) | 1.025 / 1.089 | 1.596 |
| S12 | 1.502 | 1.502 | 0.000 | D: 0.080 | fotkontakt (fötter på MoGe-golv) | 1.110 / 1.131 | 1.530 |

Källkedjan i `lokalitet.py`:

- Rader 735–741: medianavståndet `G` till det oskalade MoGe-golvet beräknas.
- Rader 742–745: `F = median(-min(J_left·u, J_right·u) + 0,08)` för stående, godkända kroppsspår. Fotledens antagna sulavstånd är 8 cm.
- Rader 746–749: personytans skala ersätts av `s = F/G`; den gamla skalan sparas endast i `personyta_skulle_ge`.
- Rader 751–762: samma golvpunkter ger `h = median(G_i*s) = F`. Därmed är källtexten `golv (MoGe)` ingen oberoende bekräftelse av kroppens fothöjd.
- Rader 756–776: `fotter_m` är åter samma fotberäkning; utan golv väljs `h=F` direkt (S2).
- Rader 777–815: kropparna roteras och flyttas med denna kamera. För ett ensamt stödbärande spår blir medianen av den lägre fotleden `h + median(min(J·u)) = 0,08 m` per konstruktion. Vid flera spår gäller tvånget deras poolade median, inte varje person eller varje ruta.

`fot_over_golv_m=0,080` mäter fotledens median, inte ett oberoende avstånd från skosulan till golvbilden. S1:s spår B ligger 0,284 m över golvet; det är uttryckligen uteslutet från höjd/skala med `spar_utan_2d_stod=[B]` och 409,4 px ursprungligt spårfel. S1 A är det spår som tvingas till 0,080 m. Måttet är inte heller en maxkontroll över hela animationen. `lokalitet.json` beräknas före L7:s gemensamma rumstransform (rader 848–871); tabellen gäller dessa lokala höjddiagnoser.

**Oberoende stöd:** inga uppmätta fysiska mått, synliga 2D-sulkontakter eller separata golvankare prövas av denna fotdiagnos. Personytans skala (rader 681–703) är en separat observation men delar kropp, kamera och MoGe; den är inte oberoende sanningsdata och används inte som godkännandegrind. Om dess sparade skala i stället används på samma golv fås i S5 cirka 1,951 m mot kontaktens 1,529 m: skillnad 0,422 m. Värdena är ungefärliga eftersom JSON-skalorna är avrundade. Flera andra tagningar skiljer 0,17–0,31 m. Det ger inget stöd för påståendet att den exakta fotkontakten har verifierats oberoende.

**Felinjektion i de faktiska källraderna 735–776:**

| Indata | Golvavstånd | Fotledsavstånd | Skala | Kamerahöjd | fot_over_golv |
|---|---:|---:|---:|---:|---:|
| Bas | 2,00 m | 1,40 m | 0,74 | 1,48 m | 0,08 m |
| Golvdjup dubblerat | 4,00 m | 1,40 m | 0,37 | 1,48 m | 0,08 m |
| Fötter flyttade en meter nedåt | 2,00 m | 2,40 m | 1,24 | 2,48 m | 0,08 m |

Testet läser och exekverar källblocket utan att ändra originalfilen. Grovt fel geometri lämnar kontaktmåttet perfekt. Slutsats: kontakt är en vald skala/origoförankring, och kan vara användbar som sådan, men är inte ett oberoende kvalitetsbevis. Råvärden: [feet.json](feet.json), [feet-injection.json](feet-injection.json).
