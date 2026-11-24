# Frön till 1.5: nästa scen, lika bra och utan handpåläggning

> **Utkast.** Ägaren bad om ~90 % nöjdhet med MVP:n innan fröna läggs fast. MVP:n väntar på ägarens bedömning (`verifiering/fas4/mvp-xbot.mp4`, live på `localhost:8000`).

Frågan för 1.5 är hur nästa klipp ska gå från mp4 till en redigerbar 3D-scen med samma förväntningar som det här: rätt kameror, rätt kroppar, repliker som aldrig klipps, neutrala dockor, designade röster och semantiska ändringar under 15 ms. Det ska gå snabbt och utan att någon för hand bygger rummet.

## Var tiden och handarbetet ligger i dag (det här klippet, 12,8 s, CPU)

| Steg | Verktyg | Tid | Automatiskt? |
|---|---|---|---|
| Tagningar, pose, händer, ansikte 30 fps | PySceneDetect, MediaPipe Tasks | ~2–4 min | Ja |
| Kamera per tagning | PnP på kroppen, 68° förkunskap | sekunder | Ja |
| Rörelse inom tagningen | LK-flöde på bakgrunden (`kamerarorelse.py`) | ~10 s | Ja |
| **Rummet** (bord, väggar, fönster, lampor) | Codex fas 1b/2 + mätning av bordskanter i S7 | timmar | **Nej, det är flaskhalsen** |
| Rekvisita | Gemini Flash-Lite-rutor (gratis) + minsta kvadrat | ~2 s + ~7 anrop | Nästan; typerna valdes för hand |
| Stabilisering av armar | `stabilisera.py` | ~10 s | Ja |
| Ordtider | KBLab Whisper medium (`ordtider.py`) | 133 s (small ≈ 4× snabbare) | Ja |
| Designade röster och munnar | Piper (`roster.py`, varm `rostserver.py`) | 14 s kallt; en ändrad replik 0,4–0,6 s | Ja (casting per roll) |
| Kamera-ingest och klipp mot tal | `kamera_ingest.py` | < 1 s | Ja |
| Verifiering | `verifiera_fas4.py` | ~3 min | Ja |

Allt utom rummet går redan att köra som en kedja.

## Fröna

1. **Ett kommando per klipp.** `ingest.py <klipp>` kör kedjan ovan med cache per klipp och skriver `kalla.json`. Samma steg finns redan; de behöver bara kopplas ihop och ges en klippmapp.
2. **Dela upp källan och regin.** `scen3d.json` blandar i dag frysta mätningar med redigering. Dela den i `kalla.json` (mätt, frusen) och `regi.json` (operationerna i ordning, som de redan loggas i `editLog`). Väljarna är semantiska (`A:huvud`, `S1:burger`, roller), så samma regi kan spelas upp mot en annan källa. **Det är anpassningen**: harnessens scenplan översätts till en regi, och regin spelas mot kundens version.
3. **Rumslåda i stället för handbyggt rum.** Några parametriska rum (cafébord, disk, bås, kök, gata) väljs ur ingesten: sittande eller stående, bordskanter, väggens färg. Måtten anpassas mot kropparna, som redan bär skalan. Kundens lokalbild (lokalbanken) ger färger, material och möbelval. Det är `byt_lokal`.
4. **Ordtider ur rösten.** `replik` och `casting` finns, men en ny repliks ordtider delas i dag efter ordlängd. Piper kan ge fonemjustering (`PiperVoice.load(..., include_alignments=True)`, kräver paketet `onnx`), och det ger exakta ordtider för teleprompter och munnar.
5. **Rörelsebank över klipp.** En tillagd aktör loopar i dag sin egen tagning. Uppmätta rörelser bör sparas som motiv (lyssna, reagera, gestikulera, gå) och väljas efter beat, så att servitören i S6 kan reagera i stället för att upprepa S4. Rörelsebiblioteket från `scen/` iteration 1 (32 motiv) är en start.
6. **Kvalitetsgränser som test.** Följande ska köras automatiskt på varje nytt klipp, så att "samma förväntningar" går att mäta:
   - ledfel ≤ 0,04 H;
   - silhuett-IoU ≥ 0,5, med hår och kläder som känd avvikelse;
   - noll sidfel över tidslinjen;
   - inga klippta ord;
   - J-klippens förskjutning bevarad inom ±0,05 s.
7. **Bättre röster när det är värt det.** Piper räcker som platshållare (ordfel 7–9 % vid rundtur). Kopplingen för ElevenLabs röstdesign finns, men den kostar krediter och används bara efter ägarens ja. Gemini TTS på gratisnivån är ett tredje alternativ. Bytet görs i casting-steget, inte i scenen.
8. **Snabbare ingest.** MediaPipe och Whisper på GPU, eller Whisper small, ger runt en minut per klipp. De 210 bankklippen i `data/ra` har landmärken i 10 fps; det räcker för kamera och placering men inte för munnar och händer.

## Öppna frågor till ägaren

- Ska dockorna ha neutralt hår per roll (vald i casting, inte kopierad)? Silhuetten saknar i dag håret, och S1 hamnar på IoU 0,46.
- Ska 1.5 börja med rumslådan (`byt_lokal`) eller med regi mot ny källa (frö 2)?
