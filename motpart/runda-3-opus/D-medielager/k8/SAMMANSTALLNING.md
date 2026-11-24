# K8, sammanställning

Genererad av `sammanstall.py` ur `k8/resultat*.jsonl`. Måtten är mina (diagnos). "Finns" är min egen
bildgranskning av nyckelrutorna och, för musik, bankens E4-läsning (Gemini); jag kan inte lyssna.

## Urvalet (20 klipp)

| lager | ok | syns ej | rest ändrad | nej | motfråga | fel | rätt hanterat* |
|---|---|---|---|---|---|---|---|
| skärmtext: byt texten | 8 | 2 | 1 | 2 | 2 | 5 | 0/0 |
| ljud: ta bort musiken | 7 | 8 | 2 | 3 | 0 | 0 | 0/0 |
| mat: byt matbilden | 0 | 0 | 1 | 19 | 0 | 0 | 0/0 |
| montage: korta 30 % | 1 | 3 | 4 | 12 | 0 | 0 | 0/0 |

\* rätt hanterat = lagret finns (min granskning) och ok, eller lagret saknas och nej. Klipp där jag inte kan avgöra om lagret finns räknas inte.

| stratum | klipp | ok per lager (text/ljud/mat/montage) | klipp med >= 3 lager rätt hanterade |
|---|---|---|---|
| montage | 5 | 0/2/0/0 | 0/5 |
| sketch | 5 | 2/2/0/1 | 0/5 |
| tilltal | 5 | 4/0/0/0 | 0/5 |
| visning | 5 | 2/3/0/0 | 0/5 |

Klipp med minst 3 av 4 lager rätt hanterade: **0/20**. Klipp där minst 3 av 4 lager faktiskt ändrades (ok): **1/20**.

### Per klipp

| klipp | stratum | text | ljud | mat | montage | finns (text/musik/mat/montage) |
|---|---|---|---|---|---|---|
| `08burgerkebab-7677567629392874774` | tilltal | motfraga | syns_ej | nej | nej | ?/?/?/? |
| `anettesrestaurang-7639497346149027094` | montage | rest_andr | ok | nej | rest_andr | ?/?/?/? |
| `blackstonesteakhouse-7439658286305037601` | visning | fel | ok | nej | syns_ej | ?/?/?/? |
| `blackstonesteakhouse-7565053584014888214` | sketch | ok | ok | nej | ok | ?/?/?/? |
| `blubnan.liljeholm-7479372817633479959` | tilltal | ok | syns_ej | nej | nej | ?/?/?/? |
| `blubnan.liljeholm-7633500587832741143` | montage | fel | syns_ej | rest_andr | rest_andr | ?/?/?/? |
| `chickenstreet.canada-7696579583734320392` | sketch | syns_ej | nej | nej | nej | ?/?/?/? |
| `duepiani-7650849186912406806` | montage | fel | syns_ej | nej | syns_ej | ?/?/?/? |
| `epicburgers.se-7392215506121444641` | visning | ok | ok | nej | rest_andr | ?/?/?/? |
| `fratelli.stockhol-7539549931233807618` | visning | fel | nej | nej | rest_andr | ?/?/?/? |
| `fratelli.stockhol-7646804960532892950` | sketch | fel | syns_ej | nej | nej | ?/?/?/? |
| `inspektorcevap-7631295246483180832` | tilltal | ok | nej | nej | nej | ?/?/?/? |
| `lux_cafe_-7628557472768265494` | sketch | nej | ok | nej | nej | ?/?/?/? |
| `mcdnyborg-7592218213610540310` | sketch | ok | syns_ej | nej | nej | ?/?/?/? |
| `slagter.lund-7582605104348466454` | tilltal | ok | rest_andr | nej | nej | ?/?/?/? |
| `spanjorskansthlm-7474263274415082774` | visning | ok | syns_ej | nej | syns_ej | ?/?/?/? |
| `steamhotel-7450055215866416386` | montage | syns_ej | ok | nej | nej | ?/?/?/? |
| `viasalessverige-7513977626315230486` | montage | motfraga | syns_ej | nej | nej | ?/?/?/? |
| `wooristockholm-7629710951587073302` | visning | nej | ok | nej | nej | ?/?/?/? |
| `zezuliverpool-7573043978854075670` | tilltal | ok | rest_andr | nej | nej | ?/?/?/? |

## Hold-out (spår A, fryst kod)

| lager | ok | syns ej | rest ändrad | nej | motfråga | fel | rätt hanterat* |
|---|---|---|---|---|---|---|---|
| skärmtext: byt texten | 1 | 0 | 0 | 1 | 2 | 0 | 0/0 |
| ljud: ta bort musiken | 1 | 2 | 0 | 1 | 0 | 0 | 0/0 |
| mat: byt matbilden | 0 | 0 | 0 | 4 | 0 | 0 | 0/0 |
| montage: korta 30 % | 1 | 0 | 1 | 2 | 0 | 0 | 0/0 |

\* rätt hanterat = lagret finns (min granskning) och ok, eller lagret saknas och nej. Klipp där jag inte kan avgöra om lagret finns räknas inte.

| stratum | klipp | ok per lager (text/ljud/mat/montage) | klipp med >= 3 lager rätt hanterade |
|---|---|---|---|
| montage | 1 | 0/1/0/0 | 0/1 |
| sketch | 3 | 1/0/0/1 | 0/3 |

Klipp med minst 3 av 4 lager rätt hanterade: **0/4**. Klipp där minst 3 av 4 lager faktiskt ändrades (ok): **0/4**.

### Per klipp

| klipp | stratum | text | ljud | mat | montage | finns (text/musik/mat/montage) |
|---|---|---|---|---|---|---|
| `faros_shipandterrace-7511394441094008086` | montage | motfraga | ok | nej | rest_andr | ?/?/?/? |
| `faros_shipandterrace-7540756212032326934` | sketch | ok | syns_ej | nej | ok | ?/?/?/? |
| `sabai.soong-7474616203366108439` | sketch | nej | nej | nej | nej | ?/?/?/? |
| `thepitaspot-7680489103195917590` | sketch | motfraga | syns_ej | nej | nej | ?/?/?/? |

## Felinjektion: kan måtten larma?

Variant a = ingen ändring alls (ska fällas på *syns*). Variant b = ändringen plus en ändring utanför lagret (ska fällas på *kvar*).

| klipp | lager | variant | larmade |
|---|---|---|---|
| `lux_cafe_-7628557472768265494` | ljud | a_ingen_andring | True |
| `lux_cafe_-7628557472768265494` | ljud | b_andring_utanfor | True |
| `chickenstreet.canada-7696579583734320392` | skarmtext | a_ingen_andring | True |
| `chickenstreet.canada-7696579583734320392` | skarmtext | b_andring_utanfor | True |
| `blackstonesteakhouse-7565053584014888214` | skarmtext | a_ingen_andring | True |
| `blackstonesteakhouse-7565053584014888214` | skarmtext | b_andring_utanfor | True |
| `blackstonesteakhouse-7565053584014888214` | ljud | a_ingen_andring | True |
| `blackstonesteakhouse-7565053584014888214` | ljud | b_andring_utanfor | True |
| `blackstonesteakhouse-7565053584014888214` | montage | a_ingen_andring | True |
| `blackstonesteakhouse-7565053584014888214` | montage | b_andring_utanfor | True |
| `mcdnyborg-7592218213610540310` | skarmtext | a_ingen_andring | True |
| `mcdnyborg-7592218213610540310` | skarmtext | b_andring_utanfor | True |
| `mcdnyborg-7592218213610540310` | ljud | a_ingen_andring | True |
| `mcdnyborg-7592218213610540310` | ljud | b_andring_utanfor | True |
| `spanjorskansthlm-7474263274415082774` | montage | a_ingen_andring | True |
| `spanjorskansthlm-7474263274415082774` | montage | b_andring_utanfor | True |
| `blackstonesteakhouse-7439658286305037601` | montage | a_ingen_andring | True |
| `blackstonesteakhouse-7439658286305037601` | montage | b_andring_utanfor | True |
| `blubnan.liljeholm-7633500587832741143` | broll | a_ingen_andring | True |
| `blubnan.liljeholm-7633500587832741143` | broll | b_andring_utanfor | True |
| `faros_shipandterrace-7540756212032326934` | skarmtext | a_ingen_andring | True |
| `faros_shipandterrace-7540756212032326934` | skarmtext | b_andring_utanfor | True |
| `faros_shipandterrace-7540756212032326934` | ljud | a_ingen_andring | True |
| `faros_shipandterrace-7540756212032326934` | ljud | b_andring_utanfor | True |
| `faros_shipandterrace-7540756212032326934` | montage | a_ingen_andring | True |
| `faros_shipandterrace-7540756212032326934` | montage | b_andring_utanfor | True |
| `faros_shipandterrace-7511394441094008086` | ljud | a_ingen_andring | True |
| `faros_shipandterrace-7511394441094008086` | ljud | b_andring_utanfor | True |
| `faros_shipandterrace-7511394441094008086` | montage | a_ingen_andring | True |
| `faros_shipandterrace-7511394441094008086` | montage | b_andring_utanfor | True |
| `thepitaspot-7680489103195917590` | ljud | a_ingen_andring | True |
| `thepitaspot-7680489103195917590` | ljud | b_andring_utanfor | True |

Larmade i 32 av 32 injektioner.

## K7: metoder i ändringsledet

| metod | antal |
|---|---|
| demucs-stam (separation av originalets ljud) | 29 |
| ffmpeg strömkopia av bild | 20 |
| pillow text | 13 |
| ffmpeg drawbox/boxblur/overlay | 12 |
| ffmpeg trim/concat/atrim/amix/afade | 10 |
| ffmpeg trim/concat/scale/overlay | 1 |
| kundens eget material | 1 |

Generativa anrop: 0.

## Tider

Operation till färdig förhandsvisning (utförda): median 2.5 s, max 18.5 s.
Ingesten kördes i delsteg med cache (forbered.py); tiden per klipp står i `lager/<klipp>/tidslinje.json` (`tider_s`).

