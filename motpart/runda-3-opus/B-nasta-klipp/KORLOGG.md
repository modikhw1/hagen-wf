# Körlogg, spår B, 20 nov 2026 (övertagande efter kvotstoppet 19 nov 22:53)

Alla kommandon kördes från repots rot `C:\Users\praiseworthy\Desktop\hagen-wf` i Git Bash med `PYTHONIOENCODING=utf-8 PYTHONHASHSEED=0` och `PY=scen/.venv/Scripts/python.exe`.

## 1. Kontroll av det som stod kvar (cirka 10:25)

- `py_compile` på alla `karna/*.py` och `prov/*.py`: inga fel. `json.load` på alla `ut/*/*.json` och `prov/*.json`: inga fel.
- Logg4 (19 nov 22:44–22:51) kördes efter den sista ändringen av `obs_motor.py` (22:43). Den speglar alltså koden som stod på disk.
- `prov/motprov.json` fanns inte. Motproven för C1, C2, A2, A3 och C3 hade aldrig körts klart. De kördes i steg 4 nedan.
- Ingesten finns inte för något hold-out-klipp under `scen/3d/ingest/ut/`.

## 2. Regression med tom cache (10:29–10:34)

```
for k in notan-tagningar e-dialog-guacamole-tagningar kand-kennysgelato-tagningar a-sketch-servering-tagningar; do
  $PY motpart/runda-3-opus/B-nasta-klipp/karna/kor.py --ingest scen/3d/ingest/ut/$k --ut motpart/runda-3-opus/B-nasta-klipp/ut/regr5/$k &
done
```
Utfall: exit 0 på alla fyra (`ut/regr5/logg_*.txt`). `obs.json`, `matning.json`, `recept.json` och `paket_grindar.json` var byte-identiska med logg4, och `paket.json` skilde sig bara i `proveniens.skapad`. **Fel:** `lokal/` innehöll bara `scen.blend` och inga kontrollrutor, så kontaktkartorna fick svarta celler, men exit var ändå 0.

## 3. Rättningar (före frysningen)

| tid | fil | ändring | skäl / bevis |
|---|---|---|---|
| 10:35 | `karna/kor.py` | `ut = (...).resolve()`. Efter Blender räknas förväntade kontrollrutor, och saknade skrivs i `tider.json: kontrollrutor_saknas` med en varning | Med relativ `--ut` skrev Blender ingen bild, och felet var tyst (steg 2). Efter rättningen: 21/12/6/21 kontrollrutor och `kontrollrutor_saknas: []` (`ut/regr5/logg_brygga_*.txt`) |
| 10:37 | `karna/grindar.py` | G6 och G3: `ok=bool(...)`. `sammanfatta` räknar `v is not None and not bool(v)` | G6 gav `np.bool_`, och `sammanfatta` räknade `is False`. Logg4:s `GRINDAR.md` visar **FEL** i G6-kolumnen (notan s4 D, guacamole s1/s3 A, a-sketch s1/s7 A) men `G6_skymning: 0` i sammanfattningen. Efter rättningen är summan 1/2/0/2 (`ut/regr5/*/paket_grindar.json`) |
| 10:37 | `karna/mutation.py` | `_normalisera`: `np.bool_` → `bool` innan `is True`/`is False` | Samma typfel gjorde att G6 aldrig valdes som kandidat i felinjektionen. Efter rättningen larmar G6 3/3 på notan (`prov/motprov.json`) |

Omkörning efter varje rättning: `kor.py --ingest <abs> --ut <abs>/ut/regr5/$k --bara-brygga` (Lager 3 och Blender). `paket.json` var fortfarande identiskt med logg4 utom tidsstämpeln.

Logg4-mapparna `ut/<klipp>/` är orörda. Deras `paket.json` har samma innehåll som `ut/regr5/<klipp>/paket.json`, men deras `paket_grindar.json`/`GRINDAR.md` har den gamla G6-summan. Gällande utvecklingsresultat ligger i `ut/regr5/`.

## 4. Motprov och felinjektion (10:39–10:41, före frysningen)

```
$PY motpart/runda-3-opus/B-nasta-klipp/prov/motprov.py notan=scen/3d/ingest/ut/notan-tagningar guacamole=scen/3d/ingest/ut/e-dialog-guacamole-tagningar gelato=scen/3d/ingest/ut/kand-kennysgelato-tagningar asketch=scen/3d/ingest/ut/a-sketch-servering-tagningar
```
Resultat i `prov/motprov.json`, utskrift i `prov/motprov_logg.txt`. "Före" är `forvarld_karna/ut/<namn>/paket.json` och "efter" är `ut/<klipp>/paket.json`, vars innehåll är detsamma som i regr5. Grindarna räknas om med aktuell kod.

## 5. Frysning 10:41:27

Se `FRYST.md`. Sammanslagen hash `7d79302318ec35c10d9d3f644f028746962b667da121a59d8a911d11675fe6c0`.

## 6. Hold-out efter frysningen (10:41 →)

Ingen ändring i `karna/` efter frysningen (`cat karna/*.py | sha256sum` gav samma hash 10:51). Den frysta kedjan har **inte** startats på något hold-out-klipp.

```
# kontroll
sha256sum motpart/runda-3-opus/A-domare/holdout_lista.txt        # 11e347a1…fddc5
sha256sum data/format/kontroll/klipp/<id>.mp4                    # alla fyra = HOLDOUT.md

# 10:42–10:43: delning i tagningar (lokalt, ingestens klippgrans.py + ffmpeg)
$PY scen/3d/ingest/flera/ingest_flera.py data/format/kontroll/klipp/<id>.mp4 scen/3d/ingest/ut/<id>-tagningar --endast-dela

# 10:43 →: YOLO-personer + COLMAP per tagning (lokalt), utskrift i holdout/logg/lokal_ingest_<id>.txt
$PY motpart/runda-3-opus/B-nasta-klipp/holdout/lokal_ingest.py scen/3d/ingest/ut/<id>-tagningar
```
- Första försöket på faros_7511 och pitaspot (10:43) föll på `UnicodeDecodeError`, eftersom `ingest_flera.py` skriver `tagningar.json` i cp1252. Jag rättade läsningen i `holdout/lokal_ingest.py` (inte fryst kod) och körde om. Den gamla loggen heter `*_forsok1_kodningsfel.txt`.
- `ingest_flera.py` varnade för faros_7511: S14 fick 24 rutor (väntade 12) och S15 25 (väntade 13).
- Kropp (SAM 3D Body) och rum (MoGe-2) är **inte** körda. De kräver Modal-GPU och är betalda.

```
# 10:45: jämförelse mot A:s facit (holdout_jamfor.py oförändrat)
$PY motpart/runda-3-opus/A-domare/matt/holdout_jamfor.py --pastaende motpart/runda-3-opus/B-nasta-klipp/holdout/pastaende_B.json --logg motpart/runda-3-opus/B-nasta-klipp/holdout/jamforelse_B.json
$PY motpart/runda-3-opus/A-domare/matt/holdout_jamfor.py --pastaende motpart/runda-3-opus/B-nasta-klipp/holdout/pastaende_baslinje_telefonprior.json --logg motpart/runda-3-opus/B-nasta-klipp/holdout/jamforelse_baslinje_telefonprior.json
```

## 7. Kontroller efter frysningen (utveckling, ingen kod ändrad)

- A6 med den frysta koden: Lager 1 på `prov/namnprov/zz-omdopt-utan-ledtradar` (kopia av gelatos ingest) med tom cache, jämfört med `ut/regr5/kand-kennysgelato-tagningar/obs.json`. Bara `klipp_id` skiljer (`prov/namnprov_fryst/logg.txt`).
- `prov/andel_antagen.py` → `prov/andel_antagen_regr5.json`; `prov/huvud_mot_box.py` → `prov/huvud_mot_box_regr5.txt`.
- Upptäckt efter frysningen, inte rättat: `scen_brygga.py:372` märker skivhöjden "(matt)" fast kamerahöjden är `antagen` (`RAPPORT.md` §5).

## 8. Hold-out-ingestens utfall (10:46–10:55)

- Klart: sabai 10:46:52 (302 kroppsjobb), faros_7540 10:46:14 (445), pitaspot 10:52:51 (1 271), faros_7511 10:54:53 (1 396). Exit 0 på alla fyra.
- `ffprobe -show_entries stream=r_frame_rate,avg_frame_rate,nb_frames` på källorna: faros_7511 har `60/1`, `5604/187`, 467. De andra tre har 30/1 och 30/1. `ingest_flera.fps_rat` läser `r_frame_rate`, så alla 15 tagningar i faros_7511 delades till 60 fps med dubblerade rutor (937 i stället för 467). Inte rättat, eftersom det ligger i `scen/`.
- Kostnadsunderlaget (kroppsjobb, satser om 40, djuprutor var 6:e) räknades ur `lokal_ingest.json` och 30 tidigare `tider.json`. Se `RAPPORT.md` §3.3.
- `cat karna/*.py | sha256sum` efter allt detta: `7d79302318ec35c10d9d3f644f028746962b667da121a59d8a911d11675fe6c0` (oförändrad).

## 9. Efter ägarens godkännande via koordinatorn (20 nov, cirka 11:00): fps-rättning i ingesten och Modal

Koordinatorn meddelade att ägaren godkänt två saker: att rätta fps-felet i `scen/3d/ingest/` och att köra kropp och djup på Modal för hold-out med ett hårt tak på 15 USD. Jag har inte sett godkännandet direkt från ägaren. Det kom i koordinatorns meddelande. **`karna/` är orörd** (frysningshashen gäller). Rättningen ligger i ingesten, efter frysningen.

### 9.1 fps-rättning, `scen/3d/ingest/flera/ingest_flera.py`

Säkerhetskopia före ändringen: `scen/3d/ingest/flera/ingest_flera.py.fore_fps.bak` (sha256 `0140809d…686b`, samma som originalet). Efter: sha256 `f5c0d29dd292141fec9147e78ef4dfc114863d1b3cbbd0cab53b6a33368f6cae`. Ingen annan fil i `scen/3d/ingest/` läser `r_frame_rate` (grep).

```diff
--- ingest_flera.py.fore_fps.bak	2026-11-10 07:08:58.256682000 +0100
+++ ingest_flera.py	2026-11-20 11:03:21.128956700 +0100
@@ -28,8 +28,18 @@
 
 
 def fps_rat(klipp):
-    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0', str(klipp)], capture_output=True, text=True).stdout.strip()
-    a, b = r.split('/'); return int(a), int(b)
+    """Verklig bildfrekvens (n, d). Den angivna r_frame_rate gäller när den stämmer med medelfrekvensen (avg_frame_rate,
+    rutor/längd) inom 1 %; annars gäller avg_frame_rate. Rättat 20 nov 2026: en källa med r_frame_rate 60/1 men 467 rutor
+    på 15,6 s (avg 5604/187) delades till 60 fps, och varje ruta dubblerades. Före-version: ingest_flera.py.fore_fps.bak."""
+    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate,avg_frame_rate', '-of', 'json', str(klipp)], capture_output=True, text=True).stdout
+    s = json.loads(r)['streams'][0]
+    def rat(t):
+        a, b = (t or '0/0').split('/'); return int(a), int(b)
+    rn, rd = rat(s.get('r_frame_rate')); an, ad = rat(s.get('avg_frame_rate'))
+    if rd and an and ad and abs(rn / rd - an / ad) > 0.01 * (an / ad):
+        print(f"fps: angiven {rn}/{rd} skiljer från verklig medelfrekvens {an}/{ad}; använder {an}/{ad}", flush=True)
+        return an, ad
+    return rn, rd
 
 
 def planera(klipp):
```

Kontroll (`holdout/fps_kontroll.py` → `holdout/fps_kontroll.json`): gamla och nya `fps_rat` på källvideon för alla 9 ingestmappar med `tagningar.json`. Lika för a-sketch (30/1), b-tilltal, c-sketch, guacamole (30/1), gelato (2997/100), sabai, faros_7540 och pitaspot. ffmpeg-anropet i `dela` beror bara på fps, så deras delning blir identisk, och deras befintliga tagningsfiler har lika många rutor som planen (680, 470, 819, 299, 252, 261, 259, 745). Notan har ingen `tagningar.json` (den delades inte med `ingest_flera.py`) och påverkas inte. Bara faros_7511 skiljer: 60/1 → 5604/187.

Omdelning av faros_7511:
```
mv scen/3d/ingest/ut/faros_shipandterrace-7511394441094008086-tagningar scen/3d/ingest/ut/faros_shipandterrace-7511394441094008086-tagningar.fel_60fps
$PY scen/3d/ingest/flera/ingest_flera.py data/format/kontroll/klipp/faros_shipandterrace-7511394441094008086.mp4 scen/3d/ingest/ut/faros_shipandterrace-7511394441094008086-tagningar --endast-dela
$PY motpart/runda-3-opus/B-nasta-klipp/holdout/lokal_ingest.py scen/3d/ingest/ut/faros_shipandterrace-7511394441094008086-tagningar
```
Utfall: 15 tagningar i 29,968 fps med 469 rutor mot källans 467. S1 fick 88 rutor i stället för 86, eftersom ffmpeg dubblerar två rutor där källans tidsstämplar är oregelbundna (delningen varnar själv). Övriga 14 tagningar stämmer exakt. Följden är att tagningarna efter S1 ligger 2 rutor senare i paketets tidsbas än i originalet. Facitrutan för faros_7511 (ruta 0) påverkas inte.
