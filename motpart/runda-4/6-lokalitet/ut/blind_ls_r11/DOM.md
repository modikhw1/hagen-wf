# Blind parvis bedömning av 3D-rekonstruktioner (X vs Y)

Omfattning: 54 tagningar ur `lista.json` (X och Y slumpade per tagning).

## Antal X / Y / lika per kategori

| Kategori | X | Y | lika | Totalt |
|---|---:|---:|---:|---:|
| Från originalkameran (`original`) | 18 | 13 | 23 | 54 |
| Rummet vid vridning (`rum`) | 26 | 24 | 4 | 54 |
| Föremålen vid vridning (`foremal`) | 14 | 24 | 16 | 54 |
| Helhet för att regissera om (`helhet`) | 25 | 25 | 4 | 54 |

## God nog för att regissera om

| Rekonstruktion | ja | delvis | nej | Totalt |
|---|---:|---:|---:|---:|
| X (`god_nog_X`) | 0 | 21 | 33 | 54 |
| Y (`god_nog_Y`) | 0 | 12 | 42 | 54 |

Sammanlagt når vinnaren i paret `delvis` i 33/54 tagningar (förloraren är alltid `nej`) och båda får `nej` i 21/54 tagningar. Ingen rekonstruktion når `ja` utan efterstädning.

## Vanligaste fel i vardera

Eftersom X och Y är slumpade per tagning uppträder båda metodernas felmönster i såväl X som Y, men med skild tyngdpunkt i detta stickprov:

- **Vanligaste fel i X:** Saknat golv eller bordsskiva så dockor och mat svävar över rutnätet; stora ljusgrå ocklusionsskärvor/spökskuggor bakom personer och över mat; kvarlämnade spökpersoner, kläder och text i 0-vyn; svarta hål och söndertrasade 2.5D-skärvor i bänkar, väggar och föremål; i vissa vinnande/gränsfall även grålila/bruna blockytor som slukar pannor eller bänkföremål (t.ex. `duepiani/s4–s6`, `08burgerkebab/s7`).
- **Vanligaste fel i Y:** Samma rums- och djupskollaps i förlorande fall (totalt 42 `nej`): avsaknad av golv/bord, papperstunna 2.5D-flisor i 50h, stora grå ocklusionsflisor, personspöken och cyan/svarta pixelfel i 0-vyn (t.ex. `spanjorskan/s1,s3`, `babasburgers/s1,s10`); där Y lägger stödytor syns också enfärgade plattor/grå skivor som äter upp bord, kylar, tallrikar eller hela 50h-vyn (t.ex. `spanjorskan/s2`, `kennysgelato2.0/s1`, `08burgerkebab/s4–s5`).

## Vad den bättre fortfarande gör fel

- **Föremål blir klossiga eller uppätna:** Mat, glas, flaskor, strutar och lådor får klumpiga enfärgade sidoväggar/extrusioner eller hackiga 2.5D-kanter; enfärgade bänk- och spisytor skär in i stekpannor, tallrikar och skålar.
- **Kvarstående hål och stora skärvor i 50°:** Även med helt golv och bord förekommer mörka luckor i bänkar, bord och mat samt stora utdragna tak-, lamp-, fläkt- eller dörrkarmskärvor som skymmer scenen vid 50° vridning.
- **Överlägg och inpainting-rester:** 2D-text och sedlar blir svävande 3D-skärvor; mindre kläd-/hårrester, suddiga retuschfläckar, grå vägglappar och svarta kantpixlar på lådor och fläktar dröjer kvar.
- **Mörka och oskarpa klipp kollapsar:** I mörka eller rörelseoskarpa scener (`blackstone/s1–s6`, `08burgerkebab/s8`) räcker inte heller den bättre till en användbar 3D-nollpunkt.
