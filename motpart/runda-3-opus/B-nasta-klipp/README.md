# B-nasta-klipp: allmän kedja från ingest till scenpaket/2 (spår B, runda 3)

Läs `RAPPORT.md` för resultat och svagheter. Den här filen beskriver hur man kör kedjan och vad som skiljer
paketen från `forvarld_karna/ut/<klipp>/paket.json`. Spår C kan läsa paketen direkt.

**20 nov:** koden är fryst sedan 10:41 (`FRYST.md`), och ändringarna står i `KORLOGG.md`. Paketformatet är oförändrat. Gällande
utvecklingsresultat ligger i `ut/regr5/<klipp>/`. Deras `paket.json` har samma innehåll som `ut/<klipp>/paket.json` (logg4),
utom `proveniens.skapad`. Två saker skiljer sig utanför paketet: `paket_grindar.json`/`GRINDAR.md` räknar nu G6- och G3-fel i
`sammanfattning` (logg4-filerna i `ut/<klipp>/` underräknar G6), och `tider.json` har fått nyckeln `kontrollrutor_saknas`.
Hold-out finns i `holdout/`.

## Köra

```powershell
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONHASHSEED="0"
scen\.venv\Scripts\python.exe motpart\runda-3-opus\B-nasta-klipp\karna\kor.py --ingest scen\3d\ingest\ut\<ingestmapp>
```

Utdata hamnar i `B-nasta-klipp/ut/<ingestmapp>/`: `obs.json`, `matning.json` (alla mätningar och antaganden i Lager 1),
`recept.json`, `paket.json`, `paket_grindar.json`, `GRINDAR.md`, `lokal_bygg.py` (Blender 5.2), `lokal/kontroll_*.png`
(tre rutor per tagning) och `kontaktkarta*.png` (original bredvid rendering). `cache/` håller försvinningspunkter,
SIFT-grupper och kamerabanor så att en omkörning av Lager 3 går fort.

Kedjan läser bara ingestens egna filer för klippet: `S*/meta.json`, `S*/rum/depth/*.npz` (MoGe), `S*/sekvens_*.npz`
(SAM 3D Body), `S*/personer.json` och `S*/masker.npy` (YOLO), `S*/rum.json` (väggplan) och `klipp/S*.mp4`. Den läser
inte `plats/deklaration.json`, `brief/`, `semantik/`, `semantik_beslut.json`, någon VLM-mapp eller någon tabell per klipp.

## Filer i `karna/`

| fil | ursprung | vad |
|---|---|---|
| `kor.py` | ny | ett kommando för hela kedjan |
| `fokal.py` | ny (VP-koden kopierad ur `scen/3d/ingest/fokal_klipp.py`) | fokal ur försvinningspunkter + telefonprior; lodlinje utan klämma |
| `identitet.py` | ny | person-re-ID över tagningar (utseende + proportioner + SIFT-bakgrund), hållning ur lårvinkeln |
| `obs_motor.py` | omskriven kopia | Lager 1 utan deklaration, VLM och namnuppslag; kamerahöjd ur fysiska ledtrådar |
| `rums_pussel.py` | kopia + 2 patchar | Lager 2 oförändrad i logik; bär skivhöjd (`topp_m`) och detektionskällor (`kallor`) till receptet |
| `schema.py`, `regler.py` | kopia + patch | nya valfria fält; `"bonaqua"` borttagen |
| `kamera_bana.py` | ny (efter runda 1:s R25c) | kamerans 6-DOF-bana ur bakgrunden (ersätter R25) |
| `scen_brygga.py` | omskriven | Lager 3: full kamerarotation, ingen höjdklämma, synlighet per led, epistemik |
| `grindar.py` | omskriven | en rad per (tagning, person), G7 mot oberoende 2D, nya G8/G9 |
| `mutation.py` | ny | felinjektion per grind |
| `emit_bpy.py`, `rotation.py` | kopia + patch | tre kontrollrutor per tagning; antagna kroppsdelar grå |
| `kontaktkarta.py` | ny | original bredvid rendering, tre rutor per tagning |

## Formatändringar i `paket.json` (fortfarande `schema: "scenpaket/2"`)

Alla tillägg är nya nycklar. Befintliga nycklar har samma betydelse, så en läsare av Argons paket fungerar.

| nyckel | innehåll |
|---|---|
| `tagningar[].kamera.nycklar` | som förut `[ruta, x, y, z, qw, qx, qy, qz, lins_mm]`, men kvaternionen bär nu pitch och roll, och en rörlig kamera har nycklar varannan ruta ur bakgrunden (inte ur kroppens drift) |
| `tagningar[].kamera.hojd` | `{v, s, status, matt_andel}`: kamerahöjd, sigma, `matt`/`antagen`, andel av vikten från mätningar |
| `tagningar[].kamera.lodlinje` | pitch, roll, sigma, källa (`vertikal försvinningspunkt`, `MoGe-normalernas läge`, prior), flaggor |
| `tagningar[].kamera.fokal_px`, `fokal_status` | fokal i bildens pixlar och om den är mätt eller antagen |
| `tagningar[].personer[]` | `spar` (personspåret i ingesten) och `tillstand` (`HEL`, `DEL`, `EXTREMITET`, `UTANFOR`) |
| `rorelse[pid][].spar` | personspårets id |
| `rorelse[pid][].synlig_bitmask_rle` | `[[ruta, bitmask], …]`, bara rutor där masken ändras; bit *i* = led *i* i `leder` har bildstöd (i bild, i personens YOLO-ruta, i masken, detekterad, och för benleder `ben_synliga`) |
| `rorelse[pid][].tillstand`, `skala_s`, `skala_kalla` | huvudtillstånd i tagningen; personlig strålskala (bildläget bevaras) och varför |
| `synlighet["<tagning>:<pid>"]` | `tillstand`, `tillstand_andel`, `led_andel_sedd`, `led_status` (`sedd`/`antagen`/`utanfor_bild`) |
| `objekt[].epistemik` | `Z1_sedd`, `Z2_harledd` (ritas) eller, i `antaganden`, `Z3_okand` (ritas inte) |
| `objekt[].status` | för bord: hur läge och höjd kom till (MoGe-skiva, handleder eller prior) |
| `objekt[].evidence_shots` | tagningar där rumshjärnan såg objektet |
| `skala` | `fokal` (värde, sigma, status, källa, kandidater) och kamerahöjd per tagning |
| `antaganden` | allt som är antaget: väggar ingen såg, stolar, fokal/lodlinje/kamerahöjd när de vilar på prior, osäkra identiteter |
| `trohet` | G7 mätt mot oberoende 2D på slutpaketet (inte paketets egen projektion) |

Borttaget jämfört med Argons paket: beslut `R25_separera_kamerarorelse`, `R1_kollisionsskydd`/`R1_skymningsskydd` (möbler
döljs inte längre för att grindarna ska bli gröna) och kroppsflyttar bakom diskar. Personid är `A`, `B`, … i
ordning efter första framträdande; de bygger på `identitet.py` och kan skilja sig från Argons namn.
