# Rörelsebanken

Uppdrag 0036 (ändrat av 0038). Bygg: `scen/.venv/Scripts/python.exe forvarld/kropp/bank_bygg.py`. Banken är träningsdata och stil för rörelsemodellen (0038), inte en lösning i sig.

## Format (v0)
En post per händelse i liggaren och agent (scenbyten och händelser utan kropp hoppas över). Inga speglingar (0038).

`bank/v0/<id>.npz`:
| fält | innehåll |
|---|---|
| `pose` | MHR, rutor × 127 leder × 8 (global i modellrummet: tx, ty, tz cm, kvaternion, x), ur kedjans sekvens efter roträttning där sådan finns |
| `cam_t`, `inom` | rotens kameraform och synlighet per ruta (ur sekvensen) |
| `upp` | lodaxeln i modellrummet per ruta (ur tagningens `varld.npz`), för att vrida kring rätt axel |
| `rest` | viloposen (behövs för spegling och IK) |

`bank/v0/poster.jsonl` per post: `id, klipp, scen, handelse, ram, roller` (hela liggarens rollkarta: agent, mål, patient, kroppsdel, instrument), `forlopp`, `person`, `kroppsdel_sida` (hoger, vanster, bada, okand), `rutor_kalla, rutor, sekunder, speglad, kvalitet, fil`.

**Spegling** finns kvar bakom `--spegla` för forskning men är struken som lösning (0038): den byter sida på allt, också på scenen. Det strukna provet ligger i `forskning/speglad_0036/`.

**Saknas i v0** (står i uppdraget, kommer i v1):
- **fotkontakter:** kedjan har dem i `t_tid`/`h_kontroll` men exporterar dem inte per ruta
- **handens föremål:** finns i `m_handling.py` (`i_handen`), inte i posten
- **kvalitetsflagga per segment:** idag en text per scen, inte kontrollens ja/nej per ruta

## Innehåll v0 (23 poster, 32,0 s)
| ram | poster | s | | ram | poster | s |
|---|---|---|---|---|---|---|
| tala | 5 | 10,5 | | ge | 1 | 1,0 |
| titta | 3 | 5,0 | | luta_sig | 2 | 1,0 |
| gissa | 3 | 3,8 | | lyfta | 1 | 0,9 |
| ata | 1 | 3,2 | | rakna_fram | 1 | 0,9 |
| reagera | 1 | 1,6 | | vaga | 1 | 0,7 |
| halla | 1 | 1,4 | | rata_pa_sig | 1 | 0,6 |
| skopa | 1 | 1,3 | | sta | 1 | 0,2 |

Källor: gelato (S1 Dreamina, roträttad; S2 ur originalet), b-tilltal och guacamole (ur originalet, ej roträttade). `innehall.json` har samma tabell.

## Vägen till tusen klipp
**Lokalt finns:**
- `data/analys`: 210 analyser, med text och scener men utan 3D
- `data/bank`: 123 kontomappar
- 152 mp4-filer under `data/`, varav 76 i `format/sekvens/vid` och 60 i `format/perc`; troligen dubbletter mellan dem, inte räknat
- 8 videor i `scen/klipp`

Det betyder att tusen klipp kräver nedladdning, och bara metadata ligger redo.

**Kostnad per klipp genom kedjan** (uppskattat ur tidigare uppdrag; fakturor är inte lästa):
| steg | kostnad | tid |
|---|---|---|
| läsning direkt ur originalet (SAM 3D Body + MHR på Modal, cirka 200 rutor) | 0,10–0,20 USD | 2–4 min väggtid, parallellt per container |
| liggare och mening (flash) | cirka 0,35 USD | 1–2 min |
| scenen, kamera, roträttning, kontroll (lokalt) | 0 | 3–6 min CPU |
| **summa när kroppen syns** | **cirka 0,5 USD** | **cirka 10 min, varav det mesta kan köras parallellt** |
| generativ återskapning 1:1 när kroppen är skymd (Dreamina via ägaren, eller fal/Ray) | +0,15 USD (fal) eller ägarens krediter, + en läsning till | + ägarens tid, 5–15 min per tagning |

**Vad som duger utan generering:** de segment där `h_kontroll` säger ja direkt på läsningen ur originalet, det vill säga hela kroppen i bild, ingen disk framför höften och ingen kant som skär huvudet. I våra tre klipp gäller det b-tilltal (alla scener), guacamole (överkroppen; borden skymmer benen) och gelato S2. Gelato S1 (bakom disken) krävde generering. Grov gissning: hälften av segmenten i ett vanligt restaurangklipp duger direkt, och resten ger överkropp men osäkra ben. **Banken kan ta överkroppsposter med en kvalitetsflagga** i stället för att vänta på generering.

**Förslag, första omgången:** 50 klipp ur `data/analys` som har mest tal, gester och servering (ramarna `ge`, `skopa`, `peka`, `armar_i_kors` saknas eller är tunna i v0).
- **Kostnad:** cirka 25 USD (50 × 0,5) utan generering.
- **Tid:** cirka 2 timmar väggtid med 10 Modal-containrar parallellt, plus ägarens nedladdning.
- **Ger:** uppskattat 200–300 poster och 10–20 minuter rörelse.
- **Tusen klipp:** cirka 500 USD och ett par dygn väggtid.

Flaskhalsen är inte pengar utan att liggaren och kontrollen ska hålla utan ägarens öga. Den ska därför mätas på de 50 först.
