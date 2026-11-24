# Rättning 0039 – MaskedMimic följer inte referensen

Status: kodfelet är rättat, men eftermått saknas eftersom verifieringsjobbet överskred 15 minuter före containerstart.

## Orsak och belägg
- `kor_mm.py` använde `env.reset(None)`. ProtoMotions `MotionManager.sample_time()` väljer då en slumpmässig fas i klippet.
- Loopen antog ändå ruta 0 och körde hela klipplängden. När den slumpmässiga starten låg nära slutet föll kroppen efter klippets slut.
- `raw_orig_full2`: rothöjden föll 0,893→0,126 m. Efter konstant miljöförskjutning drogs bort var medelfelet 111,5 cm/led; bäckenfelet var 103,7 cm i medel och 137,3 cm i sista rutan.
- Även bäckenrelativt var posefelet 57,9 cm/led. Första simrutan låg däremot 3,1 cm från närmaste referenspose: indata laddades, sedan tappades följningen.
- XY-miljöursprunget var 201,3/156,3 m i denna råfil. `efter_mm.py` drar redan bort denna konstanta offset; den är inte den kvarvarande driften.
- `dt=1/30 s` mot 29,97 fps ger bara 0,1 % skillnad. Råkvaternionerna är xyzw; wxyz gav större rotationsfel. Ingen reset mitt i filen syntes.

## Rättning
- `kor_mm.py`: sätt motion-id 0 och motionstid 0,0; återställ med `sample_flat=True` och `disable_motion_resample=True`, samma väg som `MimicEvaluator`.
- Utdata sparar nu `starttid` och `spawn`, så startfas och terrängoffset kan verifieras direkt.
- Ändrade filer: `mm/kor_mm.py` och denna rapport.
- Baslinje: `forskning/kontrakt/ut/fore_rattning_0039/` (åtta py/json-filer).
- Lokal syntaxkontroll: godkänd.

## Mått före och efter
- `orig_full` före: 111,5 cm/led efter fast världsoffset; bäcken 103,7 cm medelfel, 137,3 cm slutfel.
- `orig_full` efter: saknas; Modal hann inte starta en task inom 15 minuter och skapade ingen NPZ.
- Andra handen före: hand skopa/ge 52,3/126,5 cm; bål 64,3/56,6°; ryck VH/HH/bål 615,4/557,1/235,1 m/s³; fotglid V/H 0,43/1,01 cm/ruta; rot 155,4 cm.
- Andra handen efter: inte körd, eftersom den första verifieringen måste avbrytas enligt 15-minutersgränsen.

## Modal och kvarstående
- Modal: 1 verifieringsförsök, avbrutet efter 15 min; appen visar `tasks: 0`, stoppades uttryckligen. GPU-körningar: 0. Uppskattad kostnad: 0,00 USD.
- Kvar: kör `orig_full` när Modal kan starta inom gränsen; om ≤10 cm/led, kör därefter `villkor_a` och generera slutmåtten.

Sammanfattning: slumpmässig startfas var felet och är rättad med deterministisk reset; verifiering och andra handen saknar eftermått eftersom Modal inte startade någon task inom 15 minuter (0 GPU-körningar, cirka 0,00 USD).
