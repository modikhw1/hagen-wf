# Kimodo: hur villkoren verkar, och ett recept för b-tilltal s3

Läst 17 nov 2026: källkoden (`kimodo_src`, inklusive MotionCorrection) och den tekniska rapporten (kimodo_tech_report.pdf). Radnummer avser filerna i klonen. "Ej i koden" betyder att det inte går att utläsa.

## 1. Hur villkoren verkar
- **Bara imputering (överskrivning) med mask som extra indata, ingen gradientguidning.** I varje steg skrivs den brusiga rörelsen över med målvärdena där masken är 1, och masken läggs till som extra kanaler: `x = x*(1-mask) + observed*mask; cat([x, mask])` (`model/twostage_denoiser.py:102-103`). Det sker vid alla 100 DDIM-steg (`kimodo_model.py:617-633`). Modellens *utdata* skrivs aldrig över. Villkoren blir därför mjuka: modellen har lärt sig att följa dem (rapporten §4.3, fas 2), men inget tvingar fram dem. Rapporten säger uttryckligen att gradientguidning prövades och valdes bort (§4.4). `guide_masks` skickas med men används aldrig (`kimodo_model.py:87`).
- **Leder utan villkor** skapas fritt av modellen, betingade av texten, villkoren och resten av sekvensen genom attention. Ingen interpolering sker.
- **Helkroppsnyckelbild** (`FullBodyConstraintSet`) låser *positionerna* för alla leder, smooth_root_2d, rotens höjd och global riktning på de rutorna. Rotationerna går inte till modellen (`constraints.py:233-259`, kommentar "global rotations are not used here"). Rapportens medelfel är 3,2 cm.
- **Ändeffektorer** (`EndEffectorConstraintSet`) låser position och rotation för handled/hand respektive häl/tå. De låser också smooth_root_2d, **rotens höjd och global riktning** på samma rutor (`constraints.py:387-428`). Ett handvillkor låser alltså även höften i höjdled. Medelfelet är 3,6 cm och 6,9°.
- **root2d** låser bara smooth_root_2d (x,z), och riktningen bara om den skickas in (`constraints.py:112-121`). Höjd och kropp lämnas fria. Smooth root är en utjämnad bäckenbana (rapporten fig. 8), inte själva bäckenet, som får gunga runt den.
- **Träningsfördelningen** omfattar glesa nyckelbilder med högst 20 per typ. Täta villkor har bara tränats för root2d-banor (`docs/.../limitations.md`, rapporten §4.3). Fotkontakt finns i modellen men inte i API:t (`docs/.../key_concepts/constraints.md`).

## 2. cfg_type 'separated'
- Formeln är `ut = uncond + w_text*(text - uncond) + w_villkor*(villkor - uncond)` (`model/cfg.py:126-129`). Text-grenen ser **inga** villkor (masken nollas, `cfg.py:97-99`) och villkors-grenen ser **ingen** text. Standard är [2.0, 2.0] (`kimodo_model.py:387`, rapporten §4.4, `generate.py:229-233`).
- **Konkret:** en högre textvikt förstärker det som skiljer "uttråkad och sänker köttet" från ett ovillkorat medelvärde. Eftersom text-grenen ignorerar villkoren drar en hög textvikt också bort från nyckelbilderna. Det märks främst kring de låsta rutorna, och efterbehandlingen (punkt 5) tar igen det.
- **Intervall:** koden och rapporten anger inget intervall. Min bedömning, som måste provas: text 2,5–3,5 och villkor 2,0–2,5. Över cirka 4 brukar CFG-modeller börja överdriva och skaka, men det är inte verifierat för Kimodo.

## 3. Flera prompter och num_transition_frames
- **Uppdelning:** CLI:t delar prompten vid **varje punkt** (`scripts/generate.py:133`). Skriv därför prompten utan punkt mitt i, annars blir den flera segment.
- **Mekanik** (`kimodo_model.py:163-355`): segmenten genereras ett i taget. Segment 2 får de sista 5 rutorna (standard) från segment 1 som helkropps- och ändeffektorvillkor på händer och fötter (rad 206-225). Därefter blandas de linjärt (rad 324-327), eller så efterbehandlas hela segmentet (rad 290-318). Övergången äter alltså början av segment 2 (`limitations.md`). Varje prompt måste kunna stå för sig själv.
- **Kontextprompt plus stilprompt:** det går, men det ger en *genererad* kontext. För oss är originalets egna första rutor bättre kontext, och samma mekanism kan återanvändas direkt: 5 rutor helkropp plus händer och fötter från originalet (se 6).

## 4. Korta klipp (42 rutor ≈ 1,4 s)
- Koden har ingen hård minimigräns. Demon har dock `MIN_DURATION = 2.0` s (`demo/config.py:35`, `demo/app.py:214`), och rapporten utvärderar 3–9 s med max 10 s i träningen. Hur korta klipp som finns i träningsdatat framgår inte. 42 rutor ligger utanför det som är prövat.
- **Rekommendation:** generera 75–90 rutor och klipp ut rutorna 0–41. Starten behålls med villkor på rutorna 0–4. Rutorna efter 41 ger rörelsen utrymme att fortsätta i stället för att pressas ihop. Ska slutet också passa nästa klipp, lägg en helkroppsnyckelbild på ruta 41 i det längre klippet. Det gör den nya känslan svårare att se i slutet, så det är en avvägning. Kör båda varianterna och jämför.

## 5. Efterbehandling (`post_processing=True`)
- Kedjan går `kimodo_model.py:541-551` → `postprocess.py:186-351` → C++ `MotionCorrection/.../Utility.cpp`. Den låser fötter med IK där modellens kontaktklassning säger att foten står, men inte på villkorade rutor (`Utility.cpp:821`). Den spikar helkroppsrutorna exakt, med marginal 0, och sprider korrektionen till grannrutorna genom en optimering av hastighet och acceleration (`Utility.cpp:461-485`). Händer och fötter med villkor får 2-bens-IK som sedan jämnas ut (`Utility.cpp:497-600`). Roten rättas bara om den avviker mer än `root_margin` = 0,04 m.
- **Villkorade leder** dras alltså exakt till målet, och här används även rotationerna från villkoret, som modellen själv inte såg. **Fria leder och rutor** ändras också, men mjukt kring korrektionerna och i benen vid fotlåsning. Ha den påslagen.

## 6. Recept för b-tilltal s3
Koordinater: canonical. Rotens smooth-xz ska vara (0,0) på ruta 0 och `first_heading_angle` ska vara originalets riktning på ruta 0 (`docs/.../user_guide/constraints.md`). Beräkna smooth root med `motion_rep/smooth_root.py`, inte med rå bäckenposition.
1. **Längd:** N = 75 rutor (2,5 s). Använd rutorna 0–41.
2. **Helkropp ruta 0–4** från originalet. Det är samma recept som koden använder för sömlösa övergångar (`kimodo_model.py:208-214`). Det ärver hållningen, köttgreppet och platsen.
3. **Händer och fötter ruta 0–4** (`EndEffectorConstraintSet`, joint_names = LeftHand, RightHand, LeftFoot, RightFoot) ger greppets rotation (`kimodo_model.py:216-223`).
4. **root2d alla N rutor, utan riktning.** Använd originalets smooth root för rutorna 0–41 och håll sista värdet därefter. Det håller honom bakom disken, och täta root2d-banor ingår i träningen. Riktningen lämnas fri så att överkroppen kan vända sig bort.
5. **Inga täta fotvillkor.** De ligger utanför fördelningen (fler än 20 rutor), och de låser rotens höjd och riktning på varje ruta (`constraints.py:422-428`). Då kan han inte sjunka ihop. Fotlåsningen i efterbehandlingen sköter glidningen.
6. **Inga handvillkor efter ruta 4.** Att han sänker köttet och tittar bort ska komma ur texten. Vill man styra höjden på köttet är det bättre med *ett* glest handvillkor (t.ex. ruta 35, händerna cirka 20 cm lägre, samma inbördes avstånd) än flera leder flyttade för hand. Det glesa villkoret ingår i träningen, och modellen fyller i resten av kroppen. Något villkor för avståndet mellan händerna finns inte, så att han fortsätter hålla köttet med båda händerna måste texten säga.
7. **Text** (engelska, börja med "A person", en till två handlingar, ingen punkt mitt i, medelhög detaljnivå enligt `limitations.md`): `A bored butcher standing behind a counter slowly lets the piece of meat he holds with both hands sink to waist height, his shoulders slump and his head turns away to the side`.
8. **Vikter och steg:** `cfg_type="separated"`, `cfg_weight=[3.0, 2.0]`, `num_denoising_steps=100`, `post_processing=True`.
9. **Prov:** `num_samples=8–16` i en batch, med olika seeds. Välj sedan med domaren. Sveper man textvikten (2,5 / 3,0 / 3,5) blir det 24–48 prov.

## 7. Originalet som utgångspunkt (SDEdit)
- **Finns inte i koden.** `_generate` startar alltid från rent brus, `cur_mot = torch.randn(shape)` (`kimodo_model.py:610`), och loopar över alla steg (rad 608).
- **Byggstenarna finns:** `Diffusion.q_sample(x_start, t)` (`model/diffusion.py:96-111`) används inte vid inferens. Originalet kodas till modellens representation med `self.motion_rep(local_rot_mats, root_positions, to_normalize=True, lengths=...)` (samma anrop som `kimodo_model.py:313-318`).
- **Så här gör man:** skriv en egen variant av `_generate` som tar `x0` (originalet, normaliserat, canonical). Anropa `space_timesteps` och `calc_diffusion_vars` som i rad 615-616, välj startindex `k = round(s*(steps-1))` med styrka s ≈ 0,4–0,7, och sätt `cur_mot = q_sample(x0, t=k)`. Loopa sedan `i = k, k-1, …, 0` med oförändrat `denoising_step`. Det går eftersom q_sample och DDIM använder samma delsamplade schema efter `calc_diffusion_vars`. Villkor och text fungerar som vanligt. Låg s ger nära originalet, hög s mer av texten.
- **Förbehåll:** detta är min konstruktion, inte prövad av NVIDIA. Rapporten nämner inte SDEdit eller redigering av befintlig rörelse. Originalet måste ligga i SOMA30-skelettet och vara rimligt rent. En brusig läsning från video följer med in i grovformen.
