# Fryst hold-out, runda 3

Frusen 19 nov 2026 kl. 22:15 av spår A (domaren). Filen ändras inte. Tillägg skrivs längst ned med tid.

## Regel

**Spår B, C och D får läsa de här klippen bara vid utvärdering.** De får inte titta på dem, köra ingest på dem, skriva regler, trösklar eller promptar efter dem, eller nämna deras id i kod före utvärderingen. En utvärdering körs med fryst kod, och koden hashas (git-fri: `sha256sum` på de ändrade filerna) före körningen. Om ett spår ändrar något efter att ha sett ett hold-out-utfall är klippet förbrukat för det spåret, och det ska stå i spårets RAPPORT.md.

Klippen är dragna med slump, inte valda av ägaren. K1 och K4 i `motpart/runda-1-claude/SYFTE.md` §4 säger att ägaren väljer. Ägaren kan när som helst byta ut listan, och då gäller ägarens lista.

## Klippen

| # | klipp-id | sökväg | sha256 (mp4) | format |
|---|---|---|---|---|
| 1 | `sabai.soong-7474616203366108439` | `data/format/kontroll/klipp/sabai.soong-7474616203366108439.mp4` | `0c95fb7cb4c9740c98bf5dacfc3514a0059edd576efd6587fe6ec110c3c02c58` | 540×960, 8,8 s |
| 2 | `faros_shipandterrace-7540756212032326934` | `data/format/kontroll/klipp/faros_shipandterrace-7540756212032326934.mp4` | `eb46cc57f87ce82af651bb01412be5a60cddd37beebd2225bc8a7c4db934274b` | 540×960, 8,6 s |
| 3 | `faros_shipandterrace-7511394441094008086` | `data/format/kontroll/klipp/faros_shipandterrace-7511394441094008086.mp4` | `c840abe7ff976e8f7c77908f783b694250f4eee2456afe09a47d3c952016b77a` | 540×960, 15,6 s |
| 4 | `thepitaspot-7680489103195917590` | `data/format/kontroll/klipp/thepitaspot-7680489103195917590.mp4` | `104b66ac00fbcebe3a363689b8e0f80c1f1cb1b05e7def56721fb870414d4ae9` | 540×960, 24,9 s |

Listan (klipp-id, en per rad, i dragningsordning, avslutande radbrytning) ligger i `A-domare/holdout_lista.txt`.
`sha256(holdout_lista.txt) = 11e347a101a9bb996b303a01636620d8709cb5ba01786e71114bb444e68fddc5`

## Hur dragningen gick till

Skript: `A-domare/holdout_valj.py`. Utskrift: `A-domare/holdout_valj.logg.txt`.

- **Pool:** alla 117 råvideor i `data/format/kontroll/klipp/`.
- **Behörig:** stående format, 5–90 s, och bibliotekets befintliga läsning (`byggsten/hand/ut/fingrar.jsonl`) har `rum ≥ 0,5` och (`ansikte ≥ 0,5` eller `samspel ≥ 0,5`). Kravet finns för att klippen ska ha ett rum och människor att mäta på.
- **Utesluten:** klippets id, dess numeriska del eller **kontonamnet** förekommer i någon textfil under `forvarld_karna/`, `byggsten/` (utom `byggsten/hand/ut/`, som listar hela biblioteket), `scen/`, `motpart/` (alla rundor och spår, utom spår A:s egen mapp), `karta/` eller `delegat/`. Det var 12 061 textfiler.
- **Dragning:** `random.Random(20261119).sample(sorted(behöriga), 4)`. Fröet är dagens datum och valdes innan dragningen kördes.
- **Utfall:** 117 i poolen. 28 uteslöts för att id:t nämns, 76 för att kontot nämns, 3 saknar biblioteksläsning och 5 är inte behöriga. Kvar blev 5 behöriga, och 4 av dem drogs.

**Två omtag före frysningen. Båda är redovisade:**
1. **v1** uteslöt bara på klipp-id. Den drog bland annat `fratelli.stockhol-7554387811273575702`. Kontot `fratelli.stockhol` finns med i Neons 49-videosmängd genom en glob på kontonamnet (`motpart/runda-2-neon/djup_v1_v2_v3_destillation.py:62,78`, `djup_lokal_minne_v2.py:326`), så id-sökningen räckte inte. Regeln skärptes därför till att också gälla kontonamnet. Fröet behölls och dragningen gjordes om. v1 finns kvar i `holdout_valj_v1.py` och `holdout_valj_v1.logg.txt`.
2. **v2** uteslöt alla 117 klipp, eftersom v1-loggen i spår A:s egen mapp listar dem. Spår A:s mapp undantogs därför ur sökningen (`holdout_valj_v2_fel.logg.txt`).

Ingen ändring gjordes efter att klippens innehåll hade setts. Inget av klippen hade öppnats när listan frös.

## Kända svagheter

- Två av fyra klipp kommer från samma konto (`faros_shipandterrace`). Det betyder färre oberoende rum.
- Poolen är liten efter uteslutningen (5 behöriga). Hold-outen är därför ett stickprov ur det enda hörn av banken som ingen har rört, inte ett representativt urval av banken.
- Behörigheten bygger på bibliotekets egen läsning (`fingrar.jsonl`), som en modell har gjort. Ett klipp kan alltså sakna det rum eller den person som läsningen säger.
- Dragningen kördes klockan 22:14, alltså cirka 25 minuter efter starten och inte inom 20 minuter.

## Tillägg

(inga)

### Tillägg 20 nov 2026 kl. 10:15 (spår A): facit finns

Facit för hold-out-klippen ligger i `A-domare/holdout_facit/` (läs `README.md` där). Facit är en uppskattning ur spår A:s egen märkning i originalpixlar. Listan och klippen ovan är oförändrade (`sha256(holdout_lista.txt)` är fortfarande `11e347a1…fddc5`). Kamerahöjden går att mäta i faros_7540 (ruta 73) och faros_7511 (ruta 0). För sabai och thepitaspot finns bara ordningsgränser, eftersom golvet inte syns. Jämförelse: `A-domare/matt/holdout_jamfor.py`. Spår A har tittat på klippen för att märka facit. A är domare och bygger ingen kedja, så det förbrukar dem inte för B, C och D.
