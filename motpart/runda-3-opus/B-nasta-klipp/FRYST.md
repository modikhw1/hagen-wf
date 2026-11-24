# Fryst kod, spår B (runda 3)

**Frusen 2026-11-20 10:41:27 (+01:00).** Efter den här tidpunkten ändras ingenting i `karna/`. Ett fel som upptäcks på hold-out redovisas i `RAPPORT.md` och rättas inte här. En rättning efteråt görs som en ny version i en separat mapp och redovisas för sig.

Ingen hold-out-video, ingen hold-out-ingest och inget hold-out-resultat hade öppnats när hashen togs. Före frysningen hade jag läst `HOLDOUT.md` (klipp-id och sökvägar), `A-domare/holdout_facit/README.md` (facitintervallen för kamerahöjd) och mätavsnitten i `A-domare/RAPPORT.md`, eftersom uppdraget säger att de ska läsas först. Inget i `karna/` ändrades efter den läsningen, utom de tre rättningarna nedan. De gäller tyst fel i rendering och grindar, och ingen av dem berör kamerahöjd eller skala.

## sha256 per fil i `karna/`

`__pycache__/` ingår inte.

| fil | sha256 |
|---|---|
| `emit_bpy.py` | `940c79dccdfbb235bc70c8fd2bf8e1e374d8c28b80165b73c6319ad1cafe9983` |
| `fokal.py` | `17ea506fe0320157d2f219d3dab45a3db3a1563b8555eb68376e4a0682778553` |
| `grindar.py` | `00752069d90a487725516b2acb6398590412aa3362b7b90f7942ae484b7bd7af` |
| `identitet.py` | `c7f9cd2ae56eda7b63032edc41996c41d2a68caf1c17c102e1439565900c0d50` |
| `kamera_bana.py` | `369f4716aca693678ab3155c03180b9586c93787acec21535f522aaf14db59a2` |
| `kontaktkarta.py` | `e6011ea363606fc6e150e873f0fa3540859037e61cf43b13aa649d7fc078b695` |
| `kor.py` | `603487d61d36ee754136898a561f45b9f54ea064ec1228a9646bf5b4bb13d458` |
| `mutation.py` | `766994c56a07b0cf167d20f961681717e2a130e3e21875e1053e62b68eca3550` |
| `obs_motor.py` | `7f0122d52209ca294763755dfef6fa982f218bc441e1861a667b4cb36365438e` |
| `regler.py` | `4166af27e1a00734a27dc3fb135cada4538c37448e6e75490c114c1a618f75cc` |
| `rotation.py` | `6b0db05fee056d26e0380d6d7fb74f4fdb87a71eeb7e6009e3c3b0150010447a` |
| `rums_pussel.py` | `56a9773950eb67bf555cfd58ed7fdaa6233f157562b7d4fb3fad5c43d6c5d06b` |
| `scen_brygga.py` | `6a5a620f906810c776d7bf44b4876cf68467a9d868e10b4197ba98e698092e87` |
| `schema.py` | `5c959a77e87557f1bed53f4494ed137a45e9ea081f28352f8875eab6fcebe5a3` |

Sammanslagen hash, `cat karna/*.py | sha256sum` (filerna i namnordning): **`7d79302318ec35c10d9d3f644f028746962b667da121a59d8a911d11675fe6c0`**

Kontroll: `sha256sum -c` mot tabellen ovan, eller samma `cat`-kommando i Git Bash från `B-nasta-klipp/`.

## Miljö

Python 3.12.13 (`scen/.venv`), Blender 5.2.3 LTS (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`), `PYTHONHASHSEED=0`, `PYTHONIOENCODING=utf-8`.

## Ändrat i `karna/` den 20 nov före frysningen

Varje ändring och dess skäl finns också i `KORLOGG.md`.

1. `kor.py`: utmappen görs absolut (`.resolve()`). Med en relativ `--ut` skrev Blender inga kontrollrutor, eftersom `render.filepath` var relativ, och avslutade ändå med 0. Kontaktkartan fick då svarta celler. Dessutom räknas nu saknade kontrollrutor (`tider.json: kontrollrutor_saknas`) och en varning skrivs ut.
2. `grindar.py`: G6 (`vst <= 0,30`) och G3 (intervalljämförelse) gav `np.bool_`. `sammanfatta` räknade bara `ok is False`, så G6-larm stod som **FEL** i `GRINDAR.md` men som 0 i sammanfattningen (notan 1, guacamole 2, a-sketch 2). Nu används `bool(...)`, och `sammanfatta` räknar varje falskt värde som inte är `None`.
3. `mutation.py`: grindvärdena normaliseras till `bool` innan kandidater väljs (`is True`) och larm räknas (`is False`). Före rättningen kunde G6 aldrig provas, och originalets grindar hade kunnat se ut att aldrig larma bara på grund av numpy-typen.

Lager 1–3 gav byte-identiska `obs.json`, `matning.json` och `recept.json` och, utom tidsstämpeln `proveniens.skapad`, identiska `paket.json` före och efter ändringarna (`ut/regr5/` mot logg4 i `ut/<klipp>/`).
