# Rörelsemodeller och licenser (0038)

Ägarens fråga: om X rör sig så här med höger arm i den här scenen, hur hade X rört sig med vänster arm? Hur hade X förflyttat sig, bytt riktning och hållit resten av kroppen?

Svaret kräver en modell som:
- tar villkor: hand, mål per tid, kontakter, scen, och originalet som stil
- ger en ny, naturlig helkroppsrörelse

**Tre licenser per modell: kod, vikter, träningsdata.**
- **Bekräftat** betyder att det står på projektets egen sida eller i modellkortet (läst 13 nov 2026).
- **Antaget** betyder att det kommer från en andrahandskälla eller inte är läst.

## Modeller
| Modell | Villkor den tar | Kropp | Fart, hårdvara | Kod | Vikter | Träningsdata | Kommersiellt |
|---|---|---|---|---|---|---|---|
| **NVIDIA Kimodo** (mars 2026; [repo](https://github.com/nv-tlabs/kimodo), [kort](https://huggingface.co/nvidia/Kimodo-SOMA-RP-v1.1)) | text på tidslinje, helkroppsnyckelbilder, händer och fötter (position och rotation) per ruta, rotens bana i 2D; högst 10 s | SOMA (30 eller 77 leder), G1; SMPL-X-variant | sekunder per klipp; 17 GB VRAM, eller under 3 GB med textkodaren på CPU (bekräftat) | Apache-2.0 (bekräftat) | **SOMA-RP: NVIDIA Open Model License, "ready for commercial use"** (bekräftat); SMPLX-RP: bara forskning | Bones Rigplay, 700 h studiomocap, proprietärt men licensierat för NVIDIA (bekräftat). SEED-varianterna: BONES-SEED, 288 h | **Ja, SOMA-RP.** Kinematisk: fotglidning förekommer, och modellen känner inte till föremål (modellkortet) |
| **MaskedMimic** i ProtoMotions ([repo](https://github.com/NVlabs/ProtoMotions)) | ofullständiga mål: valfria kroppar (bäcken, fötter, händer, huvud), position och/eller rotation, på framtida tider; referensrörelse; text i forskningsversionen | SMPL (v3.0); SOMA och G1 (v3.3) | realtid per steg, kräver Nvidia-GPU och simulator (IsaacGym, IsaacLab, Newton) | Apache-2.0 (bekräftat) | v3.0 SMPL-kontrollpunkt: tränad på AMASS, alltså **bara forskning**. v3.3: SOMA-spårare och GPC-prior under NVIDIA Open Model License (bekräftat i dokumentationen) | AMASS för SMPL (icke-kommersiellt); BONES-SEED för SOMA (gated licens, oläst) | **SMPL-versionen nej.** SOMA-spåraren troligen ja (vikter OML; BONES-SEED-villkoren olästa). Fysiskt rimlig: inga glidande fötter. Prövas i 0039 |
| **PHC / PHC+** (Luo m.fl.) | följer en referensrörelse fysiskt | SMPL | realtid, GPU | antaget BSD/forskning (oläst) | AMASS-tränade | AMASS | nej utan egen träning |
| **OmniControl** ([repo](https://github.com/neu-vi/OmniControl)) | valfri led på valfri tid, plus text | SMPL (HumanML3D) | sekunder, GPU | MIT (bekräftat) | HumanML3D, som bygger på AMASS | AMASS | nej utan egen träning |
| **CondMDI** (flexibel in-betweening) | nyckelbilder och leder per tid | SMPL (HumanML3D) | sekunder, GPU | MIT (bekräftat) | HumanML3D/AMASS | AMASS | nej utan egen träning |
| **MotionFix, GMD och liknande** (text- eller målstyrd redigering) | redigera en given rörelse med text eller mål | SMPL | sekunder, GPU | forskningslicenser (antaget, oläst) | AMASS-baserade | AMASS | nej |
| **ProtoRes** (Unity Labs) | glesa mål per ruta, ger pose (ej tid) | eget skelett | millisekunder | publik, licens oklar | egen mocap | — | oklart |
| **Cascadeur** (AutoPosing, AutoPhysics) | nyckelposer med få kontrollpunkter; fysik som rättar banor; Python-API i skrivbordsprogrammet | eget rigg, FBX | interaktivt, CPU/GPU | stängd | — | — | kommersiella planer (Indie cirka 19 USD/mån enligt tredje part; Pro/Studio över 100 000 USD i intäkt); **inget moln-API**, alltså svårt att automatisera i kedjan |
| **Uthana** ([API](https://uthana.com/docs/api/pricing)) | text till rörelse, video till rörelse, lopa/sy ihop, retargeting; **inga ledmål per tid** enligt dokumentationen | egna riggar, export | sekunder, moln | stängd | — | — | ja, betalt per sekund genererad rörelse |
| **DeepMotion, Move AI, Kinetix** | huvudsakligen video till rörelse (mocap ur video) och text till rörelse | FBX/BVH | moln | stängda | — | — | ja mot betalning; tar inte våra villkor (mål per tid) |

## Data och licens
- **AMASS:** bara för icke-kommersiell forskning. Licensen förbjuder uttryckligen att träna nät för kommersiellt bruk (bekräftat i [licensen](https://amass.is.tue.mpg.de/license.html)). En kommersiell licens förhandlas med Max Planck (ps-license@tue.mpg.de), inte med Meshcapade.
- **SMPL (kroppsmodellen):**
  - Kommersiell licens via Meshcapade, som har exklusiv rätt att licensiera ut den (bekräftat på [meshcapade.com/smpl](https://meshcapade.com/smpl)). Prissidan nekade åtkomst för oss.
  - **Priser** (andrahandskällor, antaget): kommersiell nivå cirka 2 000 EUR/år för mikroföretag och 10 000 EUR/år för små och medelstora; enterprise på förfrågan.
  - **Träning av nät:** att SMPL-licensen också förbjuder träning av nät för kommersiellt bruk utan särskild licens står i en andrahandskälla (antaget).
  - **Uppgift om att Epic Games köpt Meshcapade** (februari 2026) finns i en källa, men är obekräftad.
- **CMU mocap:** fritt också kommersiellt med erkännande enligt flera andrahandskällor; CMU:s egen sida gick inte att läsa (certifikatfel). CMU i AMASS-form faller under AMASS-villkoren. **Antaget.**
- **BONES-SEED** (Bones Studio, 142 220 animationer, 288 h): gated på Hugging Face under en egen BONES-SEED-licens, oläst. Licensfrågor går till licensing@bones.studio. Modeller som NVIDIA tränat på den (Kimodo-SEED, ProtoMotions SOMA) är OML och "ready for commercial use".
- **Bones Rigplay** (700 h): proprietär. Den släpps inte, men Kimodo-SOMA-RP som är tränad på den är fri för kommersiellt bruk.
- **LAFAN1** (Ubisoft): CC BY-NC-ND, alltså inte kommersiellt (andrahandskälla).
- **100STYLE:** licensen gick inte att bekräfta.
- **Säljare av mocap för träning:** Bones Studio (Rigplay på förfrågan), Meshcapade (SMPL och modeller), Rokoko/Mixamo-liknande bibliotek (licens för animation, inte uttryckligen för träning; oläst).

## Slutsats för valet
Den enda modell som både tar våra villkor (hand och fötter per tid, rotens bana) och har vikter som får användas kommersiellt i dag är **Kimodo-SOMA-RP**. Fysikdelen finns som NVIDIA:s SOMA-spårare i ProtoMotions v3.3 (OML). Tillsammans är det samma kedja som NVIDIA beskriver (`kimodo_preparation` i ProtoMotions-dokumentationen):
1. Kimodo ger rörelsen ur villkoren.
2. Spåraren gör den fysisk, utan glidande fötter.

MaskedMimic på SMPL (0039) är forskningsreferensen, eftersom den bara är tränad på AMASS.
