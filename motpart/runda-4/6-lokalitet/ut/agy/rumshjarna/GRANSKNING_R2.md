# Visuell granskning omgång 2 av V2-rum (14 tagningar)

## Korstabell: grindens dom mot visuell bedömning (R2)

| Grindens dom | `ja` | `delvis` | `nej` | Totalt |
|---|---:|---:|---:|---:|
| Släppt (`tillit: hög`) | 7 | 4 | 0 | **11** |
| Avvisad (`tillit: låg`) | 2 | 1 | 0 | **3** |
| **Totalt** | **9** | **5** | **0** | **14** |

- **Falskt släppta:** 4 av 11 (36 %), samtliga `delvis` och samtliga i `08burgerkebab` (`s1, s5, s6, s7`) — **0 `nej`**.
- **Falskt avvisade:** 2 av 3 (`duepiani s3` på `förskjutning` 3,73 px; `duepiani s10` på `skala` `kz=0,364`, bildmässigt `ja` men skyddande i 3D tills hållen bunke maskas).

## Jämförelse med omgång 1 (samma 14 tagningar)

| Mått (samma 14 tagningar) | Omgång 1 | Omgång 2 | Förändring |
|---|---:|---:|---|
| Bildkvalitet (`ja` / `delvis` / `nej`) | 5 / 7 / 2 | 9 / 5 / 0 | +4 `ja`, båda `nej` helt borta |
| Falskt släppta (av släppta) | 8 / 12 (2 `nej`, 6 `delvis`) | 4 / 11 (0 `nej`, 4 `delvis`) | Halverade; inga grova `nej` kvar |
| Falskt avvisade (av avvisade) | 1 / 2 (`babasburgers s1`) | 2 / 3 (`duepiani s3, s10`) | `babasburgers s1` räddad; 2 nya gränsfall |

- **Stora vinster (7):** Oberoende kandidat löste båda R1:s värsta `nej` (`duepiani s6, s12`) och tre `delvis` (`duepiani s7, s9`, `babasburgers s5`) till knivskarpa `ja` (`0,58–1,25 px`, noll ankardrift); `duepiani s5` stärktes till `0,75 px`; `duepiani s1` fångades av `förskjutning` (`4,35 px`); `babasburgers s1` släpptes korrekt.
- **Kvarvarande ankarfel (2):** `08burgerkebab s1, s5` behöll ankarbetingad kandidat (`0,95`/`0,60 px`) och har kvar trasig 3D-topologi direkt bakom personen (separat stekbord/korvrullgrill i `s1`; avklippt kylbänk/klinker i `s5`).
- **Ny avvägningsbrist i `08burgerkebab s6, s7` (2):** Byte till oberoende sänkte DIS (`1,28`/`0,90 px`) men utan ankare hittades grova vitvaror på bakom personen — **regression** i `s6` (`ja → delvis`: induktionshäll över salladskantiner, ugnbox bakom ansiktet, raka skåp, klinker) och stor vit mikrovågsugn bakom huvudet i `s7` (nu släppt).
- **Nya avvisningar (`duepiani s3, s10`):** `s3` har ~1–4 px kantlinjering men mörkt glas (svag ECC `0,268`) och borttagen logga/glasreflektion i `synl` drev DIS över 3 px; `s10` stoppas av `kz=0,364` p.g.a. omaskad handhållen bunke.

## Kvarvarande allmänna förslag

1. **Prioritera ankare inom DIS-marginalen (≤ 2 px) när personen täcker mycket:** Byt inte bort en ankarbetingad kandidat bara för ~0,5 px lägre DIS (`08burgerkebab s6/s7`); ankaret hindrar påhittade vitvaror bakom stora silhuetter.
2. **Kontrollera ytan *bakom* personen mot rumsgruppens ankare:** DIS-flöde ser bara synlig yta och missar påhittad 3D-geometri bakom personen (`08burgerkebab s1/s5/s6/s7`). Jämför semantik/djup inom personmasken mot ankaret, och skärp övre `kz`-gräns (t.ex. `≤ 1,35` fångar `08burgerkebab s6` på `1,467`).
3. **Lås synliga pixlar (maskad inpainting/komposit):** Förhindrar att synliga föremål vid silhuettkanten skrivs över (`08burgerkebab s1` stekbord, `s7` dispenserlåda).
4. **Maska loggor, text, glasreflektioner och handhållna föremål före DIS/`kz`:** Exkludera överlagrad grafik och objekt i handkontakt ur `synl` — räddar `duepiani s10` och minskar falskt DIS-flöde i `duepiani s3`.
5. **Texturviktat DIS och feature-registrering vid svag ECC:** Mät DIS bara på skarpa kanter och fall tillbaka på SIFT/LoFTR när ECC < 0,3 (`duepiani s1, s3`), så mörkt glas inte ger falskt flöde eller kvarstående ~5–10 px skift.
