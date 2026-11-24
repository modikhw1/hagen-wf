Genomfört enligt alla fyra delar. Slutresultatet är bättre som rumsblockning, men ännu inte bildtroget nog för godkännande.

### Var inramningen tappades

Den tappas inte i kamerakedjan: [plats.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/plats.py:457), [kompilera.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/kompilera.py:183) och [mhr_rig.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/mhr_rig.py:232) överför kamera och kroppar konsekvent. Blender-, plan- och originalleder stämmer inom några pixlar. Den synliga skillnaden uppstår främst i standardkroppens volym/avsaknad av kläder ([mhr_rig.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/mhr_rig.py:41)) och den tidigare tunna möbeln ([rumsmall.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/rumsmall.py:140)).

### Ändrade filer

- [bildkamera.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/bildkamera.py) — generell slutkameralösare.
- [trohet.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/trohet.py) — nya slutbildsmått; äldre väg bevarad.
- [kompilera.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/kompilera.py) — kopplar in lösaren.
- [kvalitet.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/kvalitet.py) — rapportering för båda vägarna.
- [test_kroppmatt.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/test_kroppmatt.py) — mät- och lösarprov.
- [deklaration_till_hand.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/deklaration_till_hand.py) — kamera-xy och `massiv`.
- [rumsmall.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/rumsmall.py) — massiv låda till golvet.
- [test_deklaration.py](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/test_deklaration.py) — deklarations-/geometriprov.
- [rumsmall.schema.json](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/rumsmall/rumsmall.schema.json) — `massiv`.
- [deklaration.json](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/ut/e-dialog-guacamole-tagningar/plats/deklaration.json) — guacamole 0.8; 0.7 arkiverad.
- [PIPE.md](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/PIPE.md), [GUACAMOLE-LOGG.md](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/GUACAMOLE-LOGG.md) och [BILDTRO-LOGG.md](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/BILDTRO-LOGG.md) — dokumentation och full arbetslogg.

### Guacamole före/efter

| scen/roll | före: px / % / skala / IoU | efter |
|---|---|---|
| s1/A | 2,56 / 0,25 / 1,002 / 0,974 | oförändrat |
| s2/B | 3,98 / 0,39 / 0,999 / 0,984 | oförändrat |
| s3/A | 4,84 / 0,47 / 0,998 / 0,939 | oförändrat |
| s4/B | 3,52 / 0,34 / 1,000 / 0,965 | oförändrat |
| s4/A | 0,92 / 0,09 / 0,999 / 0,980 | oförändrat |

Notan: endast nya diagnostikposter samt borttagen gammal s6-varning; utan dessa är planen identisk. Gamla vägen är byte-identisk, 0 skillnader, samma SHA-256. Alla 171 tillåtna tester är gröna; `test_flode.Plats` kördes inte enligt instruktionen.

### Slutartefakter och visuell dom

- [Ren film utan text](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/bildtro_massiv_narvaro/film_utan_text.mp4)
- [Jämförelsefilm](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/bildtro_massiv_narvaro/jamforelse.mp4)
- [f0030](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/bildtro_massiv_narvaro/stillbilder/jamforelse_f0030.png) — bättre diskfront; lådan är för grov och mörk.
- [f0100](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/bildtro_massiv_narvaro/stillbilder/jamforelse_f0100.png) — B:s högerbeskärning kvarstår.
- [f0120](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/bildtro_massiv_narvaro/stillbilder/jamforelse_f0120.png) — samma beskärning; förenklad miljö.
- [f0230](/C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/e-dialog-guacamole/bildtro_massiv_narvaro/stillbilder/jamforelse_f0230.png) — klart bättre ocklusion, men B är för voluminös/nära, A läser lågt/litet och U-returen saknas.

Olöst: kroppens ytform/kläder, s4/A:s svaga källsilhuett, diskens U-form och textlagret. Kameran kan inte rätta detta utan att försämra den redan matchande ledprojektionen.