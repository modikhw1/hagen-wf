# Spår A (domaren): hur man kör måtten

Alla kommandon körs från repots rot med `$env:PYTHONIOENCODING="utf-8"` och `scen\.venv\Scripts\python.exe` (nedan `py`). Varje mått har ett självtest med felinjektion. Kör det först: ett mått som inte kan larma räknas inte. Gränserna är spår A:s diagnos och inte ägarens krav.

| mått | kommando | självtest (senast 20 nov) |
|---|---|---|
| (a) rumsskala | `py motpart\runda-3-opus\A-domare\matt\rumsskala.py --ankare ankare.json --pastaende sys.json` | `--sjalvtest`: 40 syntetiska scener, täckning 0,90–0,975, larm 40/40 på injektion (disk −20 cm, kamera −25 cm), 8/40 falsklarm på sanna värden |
| (a') hold-out-facit | `py ...\matt\holdout_jamfor.py --pastaende pas.json` (format och facit: `holdout_facit/README.md`) | `--sjalvtest`: 6/6 |
| (b) 2D-trohet | `py ...\matt\trohet2d.py --pastaende sys2d.json` · adapter för scenpaket/2: `--adapter-paket paket.json --video klipp.mp4 --ut sys2d.json` | `--kalibrera <videor>` (5 klipp som inte är hold-out): rent 0/7 personer och 0/5 videor; injektion sidled 7/7, vänster/höger 7/7, skala 0,85 5/5 videor, hopsjunkna ben 1/1 (det enda med ben i bild) |
| (c) bevarande | `py ...\matt\bevarande.py --fore a.json --efter b.json --rackvidd "mönster"` (även `.npz` och bild med mask) | `--sjalvtest`: 12/12 |
| (d) K7-vakt | `py ...\matt\k7_vakt.py --logg ut.json -- andringsled.py [args]` (statisk sökning: `--statisk mapp`) | `--sjalvtest`: 9/9 |

Kända gränser per mått står i skriptens docstring och i `RAPPORT.md` (de egna svagaste punkterna). K7-vakten känner bara igen spegling och liknande på namnet, och den ser inte en lokal generativ modell som laddas utan de listade modulerna.

Andra filer: `holdout_lista.txt` och `../HOLDOUT.md` (fryst hold-out), `holdout_facit/` (facit), `prov_runda2.md` och `prov/` (prövningen av runda 2), `RAPPORT.md`.
