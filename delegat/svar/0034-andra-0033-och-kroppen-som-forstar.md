---
id: 0034
status: klart
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
**Ändringen av 0033 är gjord:**
- punkterna 1, 3 och 4 utförda (svar 0033)
- punkterna 2 och 5 strukna
- `vanster_hand/LAS-MIG.md` är märkt "Återkallad 13 nov" överst

**1. Kartan:** [KARTA.md](../../forvarld/kropp/KARTA.md) går igenom fem vägar: motion matching (UE5 Pose Search), inlärd IK (ProtoRes), kontroller för samspel med föremål (NSM och AI4Animation), fysikbaserad kontroller (MaskedMimic i ProtoMotions) och optimering över sekvensen. För varje väg anges indata, fart, licens, kropp och vad våra data ger. Det viktigaste:
- **ProtoMotions:** Apache-2.0 och SMPL, men de förtränade modellerna bygger på AMASS, som bara får användas icke-kommersiellt och uttryckligen förbjuder att träna nät för kommersiellt bruk.
- **AI4Animation:** bara forskning, med data under CC BY-NC.
- **CMU mocap** sägs vara fritt, men det är obekräftat.
- **Kroppen:** behåll MHR i kedjan; läsaren ger den, och den har 127 leder mot SMPL:s 24. Konvertera till SMPL bara mot en förtränad kontroller; MHR-repot har ett konverteringsverktyg.
- **De tusen klippen** är den enda kommersiellt fria rörelsebanken inom vår domän.

**2. Gränssnittet:** [GRANSSNITT.md](../../forvarld/kropp/GRANSSNITT.md) skriver ut målen för "andra handen":
- **Mål:** vänster hand till tråget i h3 (28–66) och till kundens hand i h6–h8 (90–146).
- **Kontakter:** fötterna stilla och skeden i vänster hand.
- **Stil:** originalet som prior.
- **Tillbaka:** ny sekvens, mått och märkta rutor.
- Jev väljer bara frihetsgraden.

**3. Provet** ([prov_optimering.py](../../forvarld/kropp/prov_optimering.py)): ingen förtränad kontroller gick att köra inom uppdraget. ProtoMotions kräver Nvidia-GPU och Isaac, och modellerna är tränade på AMASS. Därför gjordes en optimering över hela sekvensen, med samma form som en kontroller.
- **Fria parametrar:** bålens vridning och lutning, och vänster och höger överarm och underarm.
- **Kostnader:** att nå målen, att ligga nära originalet och att armbågen inte översträcks. Därtill utjämning över tiden.
- **Inte med:** en inlärd prior och fysik.

| Mått (median i fönstren) | skopa (h3) | ge (h6–h8) |
|---|---|---|
| vänster handled till målet | 1,0 cm | 1,8 cm |
| höger handled till vila | 0,7 cm | 0,9 cm |
| bålens vridning | 25° | 34° |
| vänster armbåge | 161° | 163° |

- **Tid:** 165 s för 156 rutor, på CPU och under last. Optimeringen per ruta kan göras om på GPU eller som batch.
- **Film:** [andra_handen_kropp.mp4](../../forvarld/kropp/ut/andra_handen_kropp.mp4) med original, före, efter och remsan.

**Vad en betraktare ser** (rakt):
- **h3:** Bålen vrids så att vänster hand når tråget, och hon skopar böjd med vänster arm. Det läses som skopande, men bålen ser vriden och stel ut.
- **h6:** Vänster arm går tvärs över bröstet för att nå den punkt där höger hand var. Det är ingen ny räckning, utan en korsning, och skeden hamnar framför bröstet.
- **h8:** Vänster hand når kundens hand (1,8 cm), men bålen är vriden 34°, huvudet deformeras och höger arm pekar bakåt. Det ser fel ut.

Provet visar alltså ägarens poäng i siffror. Kroppen når målen, men utan en prior för hur människor rör sig blir det en vridning, inte en ny naturlig rörelse. Målet själv är också för snävt: "samma punkt med andra handen" borde vara "kundens hand, med en naturlig vänsterräckning". Det kräver en kontroller som vet hur en vänsterhänt räckning ser ut.

## Rekommendation
- **Bygg: en egen motion matching-bank plus inlärd IK,** tränad på våra egna klipp.
  - **Steg 1 (dagar):** gör kedjans utdata till en bank. Det är 3D-rörelse per klipp i MHR, med liggarens händelser som etiketter (ram, roll, mål, kroppsdel).
  - **Steg 2 (cirka en vecka):** motion matching mot banken, med liggarens mål som frågan och en kort IK för att landa handen. Det går på CPU och kommer ur ägarens data.
- **Sedan:** en fysikbaserad kontroller av typen MaskedMimic, tränad om på CMU och våra klipp i stället för AMASS. Det är veckor och moln-GPU, men ger "kroppen som förstår" fullt ut.
- **Så att de tusen klippen blir träningsdata:**
  - roträttning och kontakter i kedjan för alla klipp (finns för gelato)
  - liggaren per klipp, som ger etiketterna
  - en kvalitetsflagga per segment
  - ett fast skelett (MHR)
  - samma världsram
- **Optimeringen** behålls som sista steg efter matchningen, för att landa på exakt mål. Den ensam räcker inte.

## Ändrade eller nya filer
- `forvarld/kropp/`: `KARTA.md`, `GRANSSNITT.md`, `prov_optimering.py`, `film.py` och `ut/` (sekvens, mått, planer, film).
- `scen/3d/NASTA.md`.
- `scen/3d/gennedbrytning/d_video/dreamina-paket/vanster_hand/LAS-MIG.md` (återkallad).

## Kontroll mot "Klart när"
- [x] KARTA.md och GRANSSNITT.md.
- [x] Provet med tid, film och raderna per segment.
- [x] Rekommendationen.
- [x] Tillägg i NASTA.

## Avvikelser
- **Ingen förtränad kontroller kördes,** av skälen ovan: licens, hårdvara och tid. Inga paket installerades. Modal användes inte (0 USD).
- **Provets tid mättes under last** (Blender och tester parallellt).
