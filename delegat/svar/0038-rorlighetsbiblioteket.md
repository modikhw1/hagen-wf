---
id: 0038
status: klart (punkt 4, provet, ersatt av 0039 enligt orkestratorn)
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
**Ändringen av 0036** är införd:
- Helspeglingen är struken. Provet ligger märkt i `forvarld/kropp/forskning/speglad_0036/`.
- Banken v0 är ombyggd utan speglingar (23 poster, 32 s).
- Svar 0036 pekar hit.

**1. Kartan** ([RORELSEMODELLER.md](../../forvarld/kropp/RORELSEMODELLER.md)) täcker:
- Kimodo
- MaskedMimic/ProtoMotions, PHC
- OmniControl, CondMDI, MotionFix/GMD
- ProtoRes
- Cascadeur, Uthana, DeepMotion, Move AI, Kinetix

Per modell: villkor, kropp, fart, och tre licenser (kod, vikter, träningsdata), märkta bekräftat eller antaget.

**Huvudfyndet:** **NVIDIA Kimodo-SOMA-RP** (mars 2026).
- **Villkor:** händer och fötter per ruta (position och rotation), helkroppsnyckelbilder, rotens bana och text, i upp till 10 s.
- **Vikter:** NVIDIA Open Model License, "ready for commercial use" enligt modellkortet.
- **Träningsdata:** 700 h studiomocap (Bones Rigplay), cirka 17 gånger AMASS.

Det är den enda modellen som både tar våra villkor och får användas kommersiellt i dag. Fysikdelen finns som SOMA-spåraren i ProtoMotions v3.3 (också OML).

**2. Data och licens** (samma fil):
- **AMASS:** förbjuder träning för kommersiellt bruk (bekräftat). Kommersiell licens förhandlas med Max Planck, inte Meshcapade.
- **SMPL:** Meshcapade säljer licensen, cirka 2 000–10 000 EUR/år för små företag enligt andrahandskällor.
- **CMU:** troligen fritt med erkännande, men obekräftat; sidan gick inte att läsa.
- **BONES-SEED:** gated, och licensen är oläst.
- **LAFAN1:** NC-ND.

**3. Beslutsunderlaget** ([BESLUT-LICENS.md](../../forvarld/kropp/BESLUT-LICENS.md)):
- **A:** köp SMPL och AMASS (två förhandlingar, veckor, AMASS kan bli ett nej).
- **B:** Kimodo-SOMA-RP med SOMA-spåraren (fritt, kommersiellt, tar våra villkor).
- **C:** tjänst via API (tar inte mål per tid).
- **Rekommendation: B.** A hålls öppet som jämförelse, eftersom MaskedMimic SMPL körs som forskning i 0039.
- **Blockeras utan beslut:** Jevs kroppsändringar till kund.

**4. Provet:** ersatt av 0039 (MaskedMimic). Se svar 0039.

**5. Jev och liggaren:**
- **Arbetsfördelning:**
  - Liggarens frihetsgrad (`fg_hand = vanster`) ger målen genom spridningen: vilka händelser, vilken kroppsdel, mål per tid ur entiteterna (tråget, kundens hand), och kontakter (fötterna, skeden i handen).
  - Det blir en `mal.json` i GRANSSNITT-form, som modellen gör till rörelse.
  - Jev väljer bara frihetsgrad och värde. Han rör aldrig rörelsen.
- **Fart:**
  - **I dag:** sekunder (en Modal-container per ändring; se tiderna i 0039).
  - **Under en sekund:** en varm container eller lokal GPU, modellen i minnet, och korta fönster (bara de ändrade rutorna med en toning).
  - **Kimodo:** ger 10 s rörelse i ett diffusionsförlopp på en GPU, och spåraren kör i realtid. Med en varm L4 är under en sekund för ett fönster på 2–3 s rimligt, men inte mätt.
- **Hur de tusen klippen förbättrar modellen:**
  1. **Finjustering i domänen:** servera, gestikulera, sitta, mobil.
  2. **Stil per person:** originalets rörelse som stilvillkor, och på sikt en kod per person.
  3. **Liggarens etiketter som text:** "ger smakprovet över disken med vänster hand" blir träningspar för textvillkoret.
  4. **Kvalitet per ruta** (BANK.md v1) håller dåliga läsningar utanför.

## Bedömning
- **Licensfrågan har ett svar som inte kräver köp:** Kimodo-SOMA-RP och SOMA-spåraren. Det bör prövas på "andra handen" direkt efter 0039, med samma mal.json.
- **MaskedMimic SMPL (0039) är den bästa jämförelsen,** men den kan aldrig bli standardväg utan AMASS-licens.
- **Nästa:** Kimodo på Modal, och MHR till SOMA (samma form som `mhr_smpl.py`).

## Ändrade eller nya filer
- `forvarld/kropp/RORELSEMODELLER.md` och `BESLUT-LICENS.md`.
- 0036-ändringen: `forvarld/kropp/bank_bygg.py`, `bank/v0/`, `BANK.md` och `forskning/speglad_0036/`.
- `scen/3d/NASTA.md` och `PIPE.md`.

## Kontroll mot "Klart när"
- [x] `RORELSEMODELLER.md` med licenser.
- [x] `BESLUT-LICENS.md` med tre alternativ och rekommendation.
- [~] Provet: gjort i 0039 (ersätter punkt 4).
- [x] Halva sidan om Jev och liggaren.

## Avvikelser
- Meshcapades prissida nekade åtkomst (403), och CMU:s sida hade certifikatfel. De priser och villkor som står som antagna kommer från andrahandskällor.
- Inga köp och inga konton.
