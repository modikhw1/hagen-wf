# Beslut: rörelsemodell och licens (0038)

**Frågan:** vilken rörelsemodell ska ge kroppen i Jevs ändringar ("andra handen", "byt riktning"), och vad måste köpas för att den får användas kommersiellt? Underlaget finns i `RORELSEMODELLER.md`. Ägaren fattar beslutet.

## A. Köp licens för SMPL och AMASS (MaskedMimic, PHC, OmniControl …)
- **Vem:** SMPL via Meshcapade. AMASS via Max Planck Innovation (ps-license@tue.mpg.de), som en separat förhandling.
- **Pris:** SMPL cirka 2 000–10 000 EUR/år för små företag enligt andrahandskällor (antaget). AMASS-licensens pris är okänt och kan vara ett nej, eftersom AMASS är en samling av andras dataset. Det tar troligen veckor.
- **Låser upp:** alla förtränade SMPL-modeller ur forskningen, alltså MaskedMimic (prövas i 0039), PHC, OmniControl och CondMDI, och träning på AMASS.
- **Risk:** två licenser i stället för en. Ägarskapet hos Meshcapade kan ha ändrats (uppgiften om Epic är obekräftad). Även med SMPL-licens kräver en AMASS-tränad vikt AMASS-villkor.

## B. Bara fria vikter och egna data: Kimodo-SOMA-RP + SOMA-spåraren (NVIDIA)
- **Vad:** Kimodo ger rörelsen ur villkoren (händer och fötter per ruta, rotens bana, text som "hands the sample over the counter with her left hand"). Spåraren i ProtoMotions v3.3 gör den fysisk.
- **Licens:** båda vikterna under NVIDIA Open Model License, "ready for commercial use". Koden är Apache-2.0. Inget köp.
- **Kvalitet jämfört med A:** Kimodo är tränad på 700 h studiomocap, vilket är mer data än AMASS (cirka 40 h). Den bör vara minst lika bra på vardagsrörelse.
  - Svagheter: den är kinematisk (fotglidning, ingen kunskap om föremål), och det rättar spåraren.
  - Den är inte prövad på vårt material än.
- **Kroppen:** SOMA i stället för SMPL. Retargetingen MHR till SOMA skrivs som MHR till SMPL i 0039 (ledkarta plus vilokalibrering). Repot har redan SOMA-X-tillgångar från GEM-X.
- **Egna klipp:** behövs inte för att börja. De tusen klippen blir finjustering och stil per person (BANK.md: cirka 0,5 USD per klipp).
- **Kvar att läsa:** BONES-SEED-licensen (gated) gäller bara om vi vill träna om på den. För att använda vikterna räcker OML.

## C. Kommersiell tjänst via API
- **Vem:** Uthana (betalar per sekund genererad rörelse, API), DeepMotion, Move AI, Kinetix. Cascadeur har AutoPosing och AutoPhysics men inget moln-API.
- **Tar de våra villkor?** Nej. De gör text eller video till rörelse, inte "vänster hand här vid 3,5 s, fötterna kvar, resten som originalet". Cascadeur kan det manuellt men inte i kedjan.
- **Pris:** låga per klipp, men de svarar inte på ägarens fråga.

## Rekommendation: **B**
B är den enda väg som tar våra villkor, får användas kommersiellt i dag och inte kostar något. A är värt att hålla öppet som jämförelse, eftersom MaskedMimic SMPL redan körs i 0039 som forskning. Köp A bara om B inte duger på "andra handen".

**Nästa steg om B väljs:**
- Kimodo-SOMA-RP på Modal (en L4 räcker med textkodaren på CPU).
- MHR till SOMA.
- "Andra handen" med samma villkor som 0039.
- Spåraren i v3.3.

**Blockeras om inget väljs:** allt i kedjan förblir forskning (flaggan `licens: forskning`). Jevs kroppsändringar kan inte levereras till kund. Banken (0036) kan byggas, men ingen modell tränas på den.
