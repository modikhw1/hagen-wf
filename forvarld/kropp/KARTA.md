# Kroppen som förstår: karta över vägarna (0034)

Frågan: hur blir "ge glassen med andra handen" en naturlig helkroppsrörelse, på sekunder, utan generativ video? Alla vägar nedan är kroppsbundna kontroller eller sökningar i rörelsedata.

| Väg | Vad den gör | Indata | Fart och hårdvara | Kod och licens | Kropp | Våra data |
|---|---|---|---|---|---|---|
| **Motion matching** ([UE5 Pose Search](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-matching-in-unreal-engine)) | Väljer ruta för ruta den bit i en rörelsedatabas som bäst passar målet (bana, pose), och blandar. | Önskad bana och pose (kanaler), en databas med animationer | Realtid, CPU | Ingår i UE5 (Epics EULA). Algoritmen är enkel att skriva själv. | Vilket skelett som helst | **De tusen klippen är databasen.** Kräver 3D-rörelse per klipp och många exempel per handling (räcka fram med vänster hand finns bara om någon gjort det). |
| **Inlärd IK med prior** (ProtoRes, Unity Labs, ICLR 2022, [arXiv](https://arxiv.org/abs/2106.01981), kod `boreshkinai/protores`) | Ger en naturlig helkroppspose ur ett fåtal mål (positioner, riktningar). | Glesa mål per ruta | Millisekunder per pose, GPU eller CPU | Kod publik, licensen framgår inte. Tränad på mocap med egen licens. | Eget skelett, kräver omriktning | Kan tränas om på klippbanken. Ger pose per ruta; tidskoherens kommer separat. |
| **Kontroller för samspel med föremål** (Neural State Machine, Starke 2019, [pdf](https://www.ipab.inf.ed.ac.uk/cgvu/nsm.pdf); DeepPhase; AI4Animation) | Kroppen anpassar sig till ett föremåls läge: sitta, bära, ta. | Mål, föremålets geometri | Realtid, GPU | AI4Animation: forskning och utbildning, inte kommersiellt; mocap-data CC BY-NC 4.0 | Eget skelett | Rätt form för "ge", men kräver träning på handlingar med föremål. |
| **Fysikbaserad kontroller** (DeepMimic, AMP, PHC; NVIDIA MaskedMimic i [ProtoMotions](https://github.com/NVlabs/ProtoMotions)) | En simulerad kropp fyller i hela rörelsen ur ofullständiga mål ("vänster hand här vid 3,5 s, behåll stilen"), fysiskt rimligt. | Glesa mål per led och tid, text, eller referensrörelse (maskerad) | Realtid per steg i Isaac eller Genesis; kräver Nvidia-GPU | ProtoMotions **Apache-2.0**. SMPL-kroppen har egen licens. Förtränade modeller tränas på AMASS (**bara icke-kommersiellt**). | SMPL och SMPL-X | Den mest kompletta formen av "kroppen som förstår". Kommersiellt kräver träning på egna data (CMU eller våra klipp). Ingen lokal Nvidia-GPU här (kvot 0); Modal går. |
| **Optimering över sekvensen** (det vi kan göra nu) | Vanlig minimering: kroppen når målen, håller kontakter, ligger nära originalet och en rimlig pose (gränser, jämnhet). | Mål, kontakter och originalets rörelse som stil | Sekunder per sekvens, CPU | Egen kod | MHR, direkt | Ingen träning. Ger "kroppen anpassar sig" men utan lärd naturlighet. Priorn är originalet självt. |

## Data och licens
- **AMASS** (den största mocap-samlingen i SMPL-form): bara för icke-kommersiell forskning. Det förbjuder uttryckligen träning av nät för kommersiellt bruk ([licens](https://amass.is.tue.mpg.de/license.html)).
- **CMU mocap** sägs vara fritt också kommersiellt, men det står bara i sekundära källor. Det måste bekräftas på mocap.cs.cmu.edu, och CMU i AMASS-form faller ändå under AMASS-villkoren.
- **De tusen klippen** är ägarens egna data. När kedjan ger 3D-rörelse per klipp är det den enda kommersiellt fria och domänrätta rörelsebanken vi har: servera, gestikulera, sitta vid bar, titta i mobil.

## Kroppen: MHR eller SMPL?
- **MHR** (Meta, [repo](https://github.com/facebookresearch/MHR)) har 127 leder och 18 400 hörn. SMPL har 24 och 6 890. Licensen beskrivs som "industry-friendly", men måste läsas i repots LICENSE.
- **Konvertering:** MHR-repot har ett konverteringsverktyg mellan SMPL eller SMPL-X och MHR. SMPL-filerna har egen licens.
- **Bedömning:** behåll MHR i kedjan; läsaren SAM 3D Body ger MHR. Konvertera till SMPL bara där en förtränad kontroller kräver det (ProtoMotions, MotionFix), och konvertera tillbaka för renderingen. Rotationerna kan föras över; fingrar och ansikte går förlorade i SMPL.

## Vad som måste in i kedjan för att klippen ska bli träningsdata
- 3D-rörelse per klipp i ett fast skelett, världsfixerad, med kontakter, alltså fötterna och händerna mot föremål (finns delvis: sekvens, samspel, roträttning).
- Liggarens händelser som etiketter på rörelsen: ram, roller, mål, rutor. Det är precis den etikett en kontroller tränas på ("ge med höger hand mot mål X").
- Kvalitetsflagga per segment ur kontrollen, så att dåliga läsningar inte blir träningsdata.
