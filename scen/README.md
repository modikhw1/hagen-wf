# scen/: scenmotorn (experiment, 7 nov 2026)

Separat från `video/` (ingest och harness) och från `app/` (CM:s visuella flöde). Den här mappen prövar en enda fråga:

> Kan ett exempelklipp översättas till en redigerbar ryggrad (scener, personer, rörelser, föremål, bakgrund) i JSON, så att CM med semantisk input kan ändra det på under en sekund, och så att ändringen kan bedömas som rimlig mot inlärd data?

Fotorealism är inte målet. Uppspelningen visar former i ett rum.

## Innehåll

| Sökväg | Vad |
|---|---|
| `klipp/` | De tre lekplatsklippen (kopior ur `Downloads/letrend-bank`) |
| `ark/` | Kontaktark, en bild per sekund |
| `py/` | Utvinning med paketerade beroenden (Python 3.12-venv i `.venv/`) |
| `data/` | Utvunnen data per klipp, rörelsebiblioteket och scen-JSON |
| `spela/` | Uppspelning och ändring i webbläsaren |
| `RESULTAT.md` | Vad varje metod gav, kostnad och flexibilitet |

## De tre klippen

| Fall | Klipp | Typ | Varför |
|---|---|---|---|
| A | uncles_aarhus_ 7458981220274228502 (22,7 s) | sketch, en person, servering | Många klipp (~10 scener), närbilder, mat (kebabspett, pizza) |
| B | slagter.lund 7660216458277915926 (15,7 s) | tilltal, tre personer i tur | Handhållen kamera, ett föremål (köttbit) går mellan personer, våg |
| C | b.b.kebab 7620427663328480545 (27,3 s) | sketch, tre personer | En enda statisk vidbild, personer går in och ut, tallrik flyttas |

## Metoderna (en per fall, alla körs på alla tre)

1. **2D-spår** (fall A): PySceneDetect delar in i scener, Ultralytics YOLO11 ger poser, föremål och spårning. Scenen blir platta spår per scen.
2. **Rum i 2,5D/3D** (fall C): Depth Anything V2 skattar bakgrundens djup (golv, vägg, ankare), och MediaPipe Pose ger 3D-pose. Personerna placeras på golvplanet.
3. **Semantisk graf** (fall B): händelser, avsikt och kamera skrivs som en graf (för hand eller av en LLM ur kontaktarket). Graferna pekar på motiv i rörelsebiblioteket i stället för att bära rådata.

## Formatet `scen-json` v0

```
{
  klipp: {id, langd_s, w, h, fps},
  bakgrund: {rum:[{id, typ, ankare:[{namn, x, y, z}]}], golv, djup_bild},
  aktorer: [{id, roll}],
  foremal: [{id, klass}],
  scener: [{
    i, start, slut, rum, avsikt,           // krok | uppbyggnad | vändning | payoff
    kamera: {utsnitt, rorelse},             // närbild|halvbild|total|detalj ; statisk|handhållen|panorering
    handelser: [{t, aktor, verb, objekt, mal}],
    rorelser: [{aktor, motiv, start, slut, bana}]   // motiv = id i biblioteket
  }]
}
```

## Rimlighet

`data/bibliotek/` innehåller rörelsemotiv som utvunnits ur bankklipp (andra än de tre). En ändrad rörelse får ett närhetsvärde mellan 0 och 100 mot biblioteket. 80 betyder lika nära som 90 % av verkliga, osedda rörelser. Varje ändring rapporterar också sin hastighet, det vill säga hur långt den ligger från originalet.
