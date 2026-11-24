# Källa: kan MaskedMimic bära intentioner?

14 nov 2026, orkestratorn (Opus 5.5). Bara en anteckning för nästa agent. Inget är byggt och inget uppdrag är ändrat.

**Svar:** nej. MaskedMimic har handtag men inga rörelser med intention. Systemet som ger handtagen mening måste byggas. Masken passar avsiktsriggen (S2 i [UTMANING.md](UTMANING.md)) bättre än text.

## Vad källorna visar

**ProtoMotions v3.0** (lokal klon i `forvarld/kropp/forskning/ProtoMotions`, commit 56e49e7)
- Inget textspår. Sökningen efter text, xclip och embedding gav noll träffar.
- Priorn ser maskade framtida målposer (5 steg), masker per kroppsdel och 15 steg historik. Se `examples/experiments/masked_mimic/transformer.py` och `protomotions/agents/masked_mimic/model.py`.
- Latenten har 64 dimensioner och inga etiketter. Utvärderingen i artikeln använder priorns medelvärde.

**ProtoMotions v2.3** (GitHub-taggen v2.3, `data/pretrained_models/masked_mimic/smpl/config.yaml`)
- Den förtränade SMPL-vikten har `motion_text_embeddings: true`, 512 dimensioner och `motion_text_embeddings_visible_prob: 0.5`, plus terräng.
- `scenes: null` betyder att den inte ser några föremål.
- Konfigurationen finns i `protomotions/config/agent/masked_mimic/models/text_conditioning.yaml`. Det finns även en variant utan text.
- Licens: vikten bygger på AMASS och HumanML3D och får bara användas i forskning.

**Texten är HumanML3D** (`data/yaml_files/amass_hml3d_train.yaml` i v2.3). Alla 30 591 etiketter är räknade med regex, så andelarna är grova:

| Kategori | Andel | Kommentar |
|---|---|---|
| Känsla (angrily, nervous, excitedly …) | 0,8 % | |
| Avsikt eller mentalt (tries, pretends, carefully, as if …) | 4,5 % | Mest pantomim, som "as if shaking a salt shaker" |
| Tempo eller stil (slowly, like a chicken …) | 9,7 % | |
| Föremål (picks up, cup, sits on …) | 14 % | Modellen ser inte föremålen |
| Resten | | Kroppsbeskrivning, som "a person jumps sideways to the left" |

Annotatörerna är ibland oense om riktningen i samma klipp.

Räkneskriptet ligger bara i scratchpad och skrivs om vid behov. Kör det med `scen/.venv` och `-I`.

**Artikeln** (arXiv 2409.14393)
- Text via XCLIP och atomiska kommandon. Föremål via 8 hörn av en bounding box plus typindex (SAMP).
- Uppgifterna är handskrivna FSM:er för målplaneringen.
- Begränsningar: långsiktig planering saknas, och målplanering styrd av en språkmodell nämns som framtida arbete.

**Kimodo-SOMA-RP** (`forvarld/kropp/kimodo/modellkort-SOMA-RP-v1.1.md`)
- Tar text, längd och villkor, högst 10 s.
- Kinematisk och ser inga föremål.
- Texten följs inte alltid. Modellkortet rekommenderar neutrala fysiska prompter.

**SEED-annoteringarna** (nvidia/SEED-Timeline-Annotations)
- Består av en översikt plus tidsatta händelser.
- Människor märkte en delmängd, och etiketterna spreds sedan med DTW till andra utföranden av samma handlingstyp.
- Slutsats, inte verifierad: spridningen suddar ut skillnaden mellan två utföranden av samma handling, och det är där intentionen sitter. BONES-SEED kräver att man godkänner villkor, och metadatan på 51 kolumner är oläst.

## Vad det betyder

1. Intention finns som mest som ett adverb på ett verb, och den är sällsynt och brusig. Det motsvarar "gå stressat"-etiketten, som UTMANING förkastar som gränssnitt.
2. Latenten bär variation men ingen mening. Riktningar för till exempel "osäker" kräver data som vi märker själva.
3. Masken är redan ett språk för prioriteringar:
   - en låst led betyder "måste"
   - en släppt led betyder "spelar ingen roll"
   - ett tidsfönster anger "när"
   - ett fritt huvud ger vidgad uppmärksamhet
   - en hand som låses först när roten har stannat ger mindre överlapp
4. Det som saknas är lexikonet från skäl via prioriteringar till villkor, och en domare som läser av tillståndet. Ingen modell levererar det.

**Kedjan som bild:**
1. Skäl, ur liggaren och formatkortet.
2. Prioriteringar.
3. Villkor: leder, fönster, hårdhet och vad som är fritt.
4. Originalet som referens, eller Kimodo med verb plus villkor.
5. MaskedMimic eller ProtoMotions som fysisk följare.
6. En domare.

## Föreslaget, inte beslutat

- **En fjärde arm i [0044](../../delegat/uppdrag/0044-prioriteringar-som-villkor.md):** samma ändring en gång som text i v2.3-vikten ("walks nervously") och en gång som mask. Ger masken ett igenkännbart tillstånd men inte texten, så står S2 kvar. Ägaren har inte sagt ja.

## Länkar

- https://github.com/NVlabs/ProtoMotions (taggarna v2.3 och v3.0)
- https://huggingface.co/datasets/nvidia/SEED-Timeline-Annotations
- https://huggingface.co/datasets/nvidia/Kimodo-Motion-Gen-Benchmark
- https://huggingface.co/datasets/bones-studio/seed
