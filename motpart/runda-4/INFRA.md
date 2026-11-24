# INFRA v2: pröva hela Förvärlden i en kort experimentcykel

Reviderad 21 november 2026 efter ägarens förtydligande i denna konversation. Ursprunglig specifikation: [INFRA_2026-11-20.md](INFRA_2026-11-20.md). Bakgrund: [DIAGNOS_VANTETID.md](DIAGNOS_VANTETID.md). Revisionen beskriver vägval och acceptansprov; den betyder inte att infrastrukturen är byggd eller att grundhypotesen håller.

## 1. Uppdrag och mandat

**Ägarens riktning, sammanfattad:** läsa många verkliga klipp, bygga en användbar redigerbar 3D-förvärld och modulera scener utifrån relationer mellan klippen. CM bedömer genom en 9:16-kamera och påverkar scenen; scenens möjligheter och begränsningar ger i sin tur CM nya kreativa val. Textsvar och mått räcker inte. Ett fungerande visuellt experiment ska göra det möjligt att bedöma eller förkasta en idé utan lång, oklar väntan.

- Ägaren medger extern kapacitet inom **0–100 USD** för meningsfulla framsteg. USD är tolkningen av ”0-100d” i samtalet. Behandla 100 USD som totalt tak för denna provomgång, inte per jobb eller månad. Tidigare kontoförbrukning är okänd.
- Ägarens riktmärke är **cirka 15 minuter till ett bedömbart experimentutfall**. Det är inte ett löfte att ett nytt system kan implementeras eller tusen fullständiga 3D-rekonstruktioner slutföras på 15 minuter.
- Budgetfördelning, urvalsstorlekar, pilotoperatorer och övriga tekniska tidsmål nedan är **agentens arbetsbeslut**, inte nya ägarkrav.
- Bevara grundidén: video → observationer → redigerbar scen och tidslinje → styrd förändring → visuell återkoppling. Implementationerna bakom stegen ska kunna bytas och jämföras.
- Detta återupptar inte stoppade kinematiska attitydreglage i arbetsbord/STOPP_V2.md. Befintlig ingest får undersökas som felbehäftad baslinje. Inga generativa bild-/video-/röständringar införs genom denna specifikation; tidigare K7 gäller.

**Kunskapsgräns:** videon är observerat underlag. Rekonstruerad 3D är en hypotes förenlig med delar av underlaget, inte uppmätt ground truth för dolda ytor eller verkligt djup. Märk observerat, skattat, antaget och manuellt korrigerat separat. Lågt projektionsfel bevisar inte att scenen tål nya vyer eller ändrad interaktion.

## 2. Vad som är belagt

| Underlag | Observation | Konsekvens |
|---|---|---|
| 2-invarians/ref_kor.logg.txt | 21 batcher: E28 20,25 min, E30 2,85 min, E37 8,83 min. Summa 31,93 min i extraktoranrop, inte hela jobbets väggtid. | Seriell körning/processstarter är konkreta flaskhalsar. Hela väntan är inte en uppmätt Modal-kallstart. |
| mat_adapter.py, bilaga.py, test_kor.py i 2-invarians/ | Nya extraktorprocesser per batch, E28 med --par 1; testet kör E28 och VAD igen för bilagor. | Håll modeller laddade och få rålogg/sammanfattning från samma extraktion. Validera likvärdighet innan ersättning. |
| 2-invarians/ref_mat.jsonl | Kontrollerat 21 nov: 144 unika referens-id:n med E28/E30/E37 och lyckad C-byggkod. | Återanvänd med verifierad proveniens. Kompletta fält är inte visuell kvalitetsverifiering. |
| arbetsbord/data/ingest_v2/ingest_v2_benchmark.json | Två tidigare GPU-körningar: 79,12 s respektive 67,34 s väggtid inklusive överföring; intern ingest 30,28 respektive 62,94 s. | Ett externt exekveringsspår finns i historiken. Två olika klipp ger inget kontrollerat kall-/varmtest eller generell genomströmningsgaranti. |
| arbetsbord/ingest_v2/SKALNING_RAPPORT.md | SAM3D-ledet tar cirka 77 % av intern tid. Personförväxling, djupsprång och felaktiga bordshöjder identifieras. | Fler GPU:er gör inte scenerna riktiga. Mät kvalitet och tid tillsammans; dölj inte fel med höjdklämmor. |
| motpart/PROTOKOLL.md | Tidigare geometrigrindar och trohetsanspråk har underkänts genom motprov. | Gamla godkänd-etiketter i LAGE/arkitekturdokument är inte acceptansbevis. |

Ingen ny extern GPU-körning har gjorts vid revisionen. En read-only-kontroll med modal app list --json gav inget svar och avbröts; aktuell kontoåtkomst, kvot och tillgänglig kapacitet är **ej verifierade**. Inga resurser har hyrts genom revisionen.

## 3. Första försöket: två förmågor i samma visuella loop

Att först bygga hela bibliotekets 3D och därefter testa modulering riskerar att låsa fel representation. Börja med ett litet genomgående prov av båda leden och skala sedan. Tempo/invarians förblir delprov, inte ersättning för huvudprovet.

### A. Kan representationen bära originalet och en faktisk ändring?

Första omfattning: **12 utvecklingsklipp i 6 käll-/referenspar**. Ta tillåtna utvecklingskonton; använd inte T4:s låsta testgrupper som utvecklingsmaterial. Skriv urvalsregel och bortfallsregler före körning. Täck ensam person, två personer/ocklusion, händer mot bord/produkt, kamerarörelse, montage och premissbärande text/ljud. Redovisa luckor.

För varje källklipp:
1. Original med ljud.
2. Oförändrad rekonstruktion med originalets tagningar, kamera, rörelse och synlighet.
3. En avgränsad förändring mot referensen i flera styrkor.
4. Resultat efter ångring, för kontroll av återställning.

Första rumsliga kandidatoperator: **ändra kompositionen kring samma bord-/produktinteraktion mot referensens utsnitt och relativa placering**, med ärvd kroppsrörelse, kontakt, identitet, tagningsordning och ljud. Detta är ett arbetsval att pröva, inte en fungerande operator som redan finns. Antagen ny geometri får inte döljas. Saknas stöd ska försöket visa var det bryter samman eller ge nej. Avståenden räknas i täckningen, inte som lyckade ändringar.

Visa synkroniserad rörelse genom 9:16-kameran, inklusive övergångar och kontaktögonblick. Stillbilder kompletterar men ersätter inte animation. Förenklade material/ytdetaljer är tillåtna; statiska dockor, egen översiktskamera och tappade tagningar är inte en förenklad leverans av samma klipp.

### B. Ger biblioteket bättre val än en enkel regel?

Jämför samma käll-/referenspar och samma operatorutrymme/renderare:
- enkel explicit regel;
- metod som använder liknande klipps visuella/tidsmässiga relationer;
- vid behov strukturerad modelläsning som föreslår recept inom samma gränser.

Använd oförändrat klipp och lika stora ändringar med irrelevant referens som kontroller där de är meningsfulla. Bedömaren ser avsedd referens men inte metodnamnet. Pröva båda riktningarna när det går. Oförändrad kontroll kan belägga bevarande men räknas inte som träffad förändring.

Efter utvecklingsprovet låses en separat utvärderingsmängd och metoderna. Befintliga 200 original kan ge bredare täckning. De 2 707 lågupplösta kopiorna kan användas för sökning men är inte källor till fullständig rörelse-/3D-verifiering. Redovisa tillgängliga original och kontouppdelning innan ”1 000 klipp” utlovas.

Bedöm avsedd riktning, bevarat innehåll/särprägel, visuell användbarhet, kontakt/timing och om något bryter ryggraden. Spara ägarkommentarer ordagrant, godkännanden, ångringar och rättelser. Modellförklaringar/bankavstånd är diagnos. Metoden får inte bedömas enbart med måttet den optimerar.

**Stoppbeslut:** oläsbar originalrekonstruktion stoppar slutsatser om modulering för den enheten. Om biblioteksstyrning inte förbättrar bedömningen mot enkel regel finns ännu inget belägg för dess mervärde. En misslyckad stack fäller inte alla realiseringar av grundidén. Redovisa täckning, väntetid, kostnad och kvalitet tillsammans så att svåra fall inte göms.

## 4. Gemensamma data, utbytbara implementationer

Varje jobb har klipp-id, originalets SHA256, tidsbas/PTS, källa, konto/urvalsgrupp, versionsmanifest och variantrecept. Lagernyckel: källhash + föregående lagers hash + extraktorkod + modellvikter + parametrar + relevant runtimeversion. Invalidera bara beroende lager. Spara flera namngivna stackresultat utan att skriva över historiken.

| Lager | Innehåll och användning |
|---|---|
| Original/proveniens | Oförändrad video/ljud, ffprobe, hash och tidsbas. Beständig lagring nära beräkningen. |
| Lätta observationer | Tagningar, tidsserier, OCR/talintervall, detektioner och små tabeller. Biblioteksjämförelser utan ny videokörning. |
| Visning | Komprimerad 9:16-proxy och nyckelrutor. Upplösning/fps märks; visningsmaterial är inte automatiskt mätunderlag. |
| Rum/kropp | Kameror, identiteter/spår, djup/ytor, rörelser, kontakt och osäkerhet per tagning. Fördjupa där experimentet kräver det; redovisa alla begärda/skippade/felande fall. |
| Förändring | Recept, avsedda/tillåtna följdändringar, hårda bevarandekrav, avståenden och återställning. |
| Bedömning | Reproducerbar preview, metodblind nyckel, ägaromdöme och faktiska tid-/kostnadsloggar. |

Återanvänd scenpaket/2 och medielager/1 genom adaptrar där de räcker; lägg proveniens/osäkerhet i tydliga sidofiler vid behov. Ett byte av tracker, kropp-/geometrimodell eller semantisk läsare ska inte kräva nytt regibord eller bedömningsformat.

**Invariansprovet:** E28 använder förändring mellan bilder; T4 prövar bland annat kompression och 30→15 fps. Ett 540p/10fps-lager kan inte återskapa detta. Cachelagra exakt uppmätta resultat per faktisk variant/version. Testade codec-/signaländringar måste utföras och mätas, inte ersättas med algebra på originalvärden. Ändrade definitioner/förbehandling får ny metod-/protokollversion. Determinismprov måste kunna kringgå cachen.

**Minne:** små tabeller och aktiva arbetsmängder i RAM; komprimerade original/proxyer och större arrays på beständig disk. 30 s RGB i 540×960 vid 10 fps är 466,56 MB avkodat; tusen sådana klipp är 466,56 GB. ”64 GB för hela O-lagret” är inget generellt dimensioneringsunderlag.

## 5. Maskinval och budget

**Första val: Modal för ett begränsat jämförelseprov.** Befintlig integration och historiskt använda viktvolymer motiverar valet; det bevisar inte bäst pris eller kvalitet. Kontrollera åtkomst, volymer, image-cache och kvot. Adaptra gamla ingesten i separat försök/utdata; starta inte dess hårdkodade tvåklippsjobb eller stoppade UI-/attitydsteg av misstag.

Håll en worker varm under ett avgränsat pass och använd en liten begränsad pool för batchprovet. Separera billiga CPU-jobb från GPU-jobb och håll data servernära. Jämför fler workers/GPU-byte på samma klipp. Kärnantal och 500 GB disk är inte hårda förhandskrav.

**Reserv: RunPod-pod under arbetspasset**, om mätningen visar att Modal-start, överföring, utvecklingscykel eller kvot hindrar försöket. Bygg inte två produktionsplattformar först. Lägre timpris ensamt motiverar inte migrering.

Listpriser kontrollerade 21 nov 2026:
- [Modal](https://modal.com/pricing): L4 0,000222 USD/s = 0,7992 USD/h. CPU 0,0000131 USD/kärna/s och RAM 0,00000222 USD/GiB/s tillkommer. Exempel med 4 fysiska kärnor och 16 GiB: cirka **1,116 USD/h** vid dessa resursnivåer. Prisaritmetik, inte uppmätt jobbkostnad. Högre användning, lagring, trafik, API-anrop och skatt kan tillkomma.
- [RunPod](https://www.runpod.io/pricing): sidan visar L4 0,69 USD/h och RTX 4090 0,89 USD/h. Verifiera valt erbjudande, kapacitet och lagring före hyra. [Pod-prissättning](https://docs.runpod.io/pods/pricing).
- [Modal skalning](https://modal.com/docs/guide/scale): min_containers, max_containers, buffer_containers och scaledown_window styr beredskap/skala. Warmhållning kostar och avslutas efter passet.

Agentens fördelning inom totalt 100 USD:
| Del | Tak | Beslutsunderlag |
|---|---:|---|
| Åtkomst, baslinje och resursprov | 5 USD | Kan samma material köras, levereras och mätas? |
| Två implementationer och första visuella loop | 15 USD | Bär representationen en riktig ändring; vad lönar sig att rätta? |
| Bredare fryst prov/batch | 50 USD | Håller utfallet över fler klipp och under parallell last? Används efter bedömbart litet försök. |
| Reserv för specificerade omprov/andra läsare | 30 USD | Ingen automatisk förbrukning. |

Skilj faktisk fakturering från beräknad/reserverad kostnad. Reservera start, parallella jobb, retries och avslutningsmarginal före dispatch. Okänd faktura/andra kontojobb får inte räknas som noll. Begränsa workers och serverns timeout: att döda den lokala väntande processen räcker inte. Verifiera avslutade fjärrjobb och nollställd warmhållning efter avbrott. Sätt leverantörens budgetspärr där den finns. Lokal kostnadsberäkning ensam är ingen hård fakturaspärr.

## 6. Körkontrakt: väntan måste ge ett beslut

Klockan startar när ett definierat experiment skickas: kö, uppvärmning, uppladdning, beräkning, export och publicering ingår. Första installation/imagebygge är separat uppdrag med egen ETA/budget; det får inte gömmas i ”snart klart”. Följande ska mätas, inte beskrivas som uppnått:

| Mål | Vad som räknas |
|---|---|
| **Bedömbart första utfall inom 15 min** | Förutbestämd liten grupp med original, rekonstruktion, ändring och kontroller går att spela/bedöma. Siffror/laddningsindikator räcker inte. Fel/nej och bortfall redovisas. |
| Fullt batchutfall | Egen ETA/fullständighetsräknare. Första delmängden får aldrig utges för hela masstestet. |
| Upprepad ändring | End-to-end-latens på redan ingestat material inklusive visning; arbetsmål första användbara preview under 30 s. Ny analys/rendering kan behöva eget jobb. |
| Omanalys | Mät kall/varm läsning av små observationer separat från hel video. Ursprungliga M1 under 50 ms kan avse metadata/mättabell, inte all videodata. |
| Synlig väntan | Provlopp före större batch, ETA-intervall och progress var 15:e sekund. Agenten ger lägesbesked minst varje minut under aktivt arbete. |
| Återstart | Återanvänd färdiga verifierade enheter; markera halvskrivna resultat och publicera atomiskt. |

FRAMSTEG.json: experiment-id, hypotes, stackversion, fas, skickade/aktiva/färdiga/felande/avstådda enheter, cacheträffar, tid sedan beställning, ETA-intervall, kostnad (estimat/faktisk/reserverad), resurstak, senaste fel, länk/sökväg till bedömningsmaterial.

1–2 klipp räcker för startkontroll, inte säker ETA för en varierande bank. Använd historik och ett litet urval av kort/långt, få/många tagningar och en/flera personer. Redovisa p50/p95 när stickprovet räcker, annars osäkert intervall. Sätt parallellitet efter RAM/VRAM/CPU och kvot. Stoppa nya jobb vid budgettak eller tidsgräns. Vid 1,5 × ETA stoppas nya enheter och aktiva jobb avslutas/avbryts inom hårda taket. Rapportera vad som går att bedöma och vad som hindrar nästa steg.

## 7. Säkerhet och återanvändning

- Synka en explicit lista över kod/data. Rotens blender_token.txt, fal_ai.txt och andra lokala nyckelfiler får inte följa med.
- Använd hemlighetshantering för tokens och autentisering för fjärrpanel. Kunduppgifter skickas inte i detta prov. Modelläsning av offentliga klipp är separat versionerad diagnos och ingår i budgeten.
- Återanvänd original i ~/Downloads/letrend-r4/, manifest i 1-datagrund/, extraktorer/adaptrar i 2-invarians/ och panelens blindning/svarshistorik i A-domare/panel/ där de passar. Svar skrivs aldrig över.
- Följ AGENTS.md och byggsten/jutsu/README.md vid scenbygge; kamera, identitet, rörelse och synlighet följer med i samma koordinatram.
- Granska representativa rutor från varje tagning, övergångar och levererad animation mot original. Kan bilden inte granskas återstår visuell verifiering.

## 8. Leveransordning och aktuellt läge

1. Verifiera åtkomst och få en liten kostnadstakad körning med tidsuppdelning, sparade utdata och säkert avslut. Förbered samtidigt visning av original/baslinje/ändring.
2. Slut visuella loopen på utvecklingsurvalet med en faktisk rumslig operator. Granska rekonstruktion och ändring; ärv inte gamla godkänd-etiketter.
3. Byt en implementation i taget bakom samma kontrakt och jämför tid, kostnad, täckning och ägarbedömning.
4. Skala till 200 och sedan 1 000+ där data/resultat motiverar det. Indexering och fullständig 3D-ingest är olika jobb. Tusen jämförbara mått innebär inte tusen användbara redigerbara scener.
5. Pröva bättre policy, retrieval/rangordning och senare eventuell träning med verkliga val/rättelser. En stark modells förståelse av vaga instruktioner kan föreslå kandidater; visuell effekt måste ändå prövas.

**Status, uppdaterad efter första genomförandet:** [4-visuell-loop/RAPPORT.md](4-visuell-loop/RAPPORT.md) redovisar ett körbart lokalt granskningsbord med två befintliga utvecklingsklipp, synkroniserat original/3D, reversibel linsändring, ångring och sparade ägarkommentarer. Alla 15 tagningar har representativa granskningsbilder. Baslinjen visar väsentliga rekonstruktionsfel och ska inte massköras som godkänd 3D. Detta är en mindre startkontroll, inte det planerade 12-klippsprovet eller referensstyrd modulering. Ny workerpool, budgetvakt, gemensam cache och masstest återstår. Modal-åtkomst gav timeout efter 20 s; ingen extern beräkning startades. Första nya ägardom återstår. Prestanda för lokal linsändring får inte utges för ingestprestanda.
