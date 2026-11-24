---
id: 0036
status: klart (ändrat av 0038: punkt 3–5 strukna)
av: uppdragstagaren (Claude-appen, Opus 5.5)
datum: 2026-11-13
---

## Resultat
**1. Formatet** står i [BANK.md](../../forvarld/kropp/BANK.md).
- **Per post:** MHR-pose (global, efter roträttning där den finns), `cam_t`, `inom`, lodaxeln per ruta, vilopose, liggarens hela rollkarta (agent, mål, patient, kroppsdel, instrument), förlopp, sida och kvalitet.
- **Saknas i v0:** fotkontakter, handens föremål och kvalitet per ruta. Kedjan har dem men exporterar dem inte än (v1).

**2. Banken v0** ([bank/v0/](../../forvarld/kropp/bank/v0/), `bank_bygg.py` på 6 s): 23 poster och 32,0 s, utan speglingar.
| ram | poster | s | ram | poster | s |
|---|---|---|---|---|---|
| tala | 5 | 10,5 | ge | 1 | 1,0 |
| titta | 3 | 5,0 | luta_sig | 2 | 1,0 |
| gissa | 3 | 3,8 | lyfta | 1 | 0,9 |
| ata | 1 | 3,2 | rakna_fram | 1 | 0,9 |
| reagera | 1 | 1,6 | vaga | 1 | 0,7 |
| halla | 1 | 1,4 | rata_pa_sig | 1 | 0,6 |
| skopa | 1 | 1,3 | sta | 1 | 0,2 |

Källor: gelato (S1 Dreamina, roträttad; S2), b-tilltal och guacamole (ur originalet, ej roträttade).

**3–5. Strukna av 0038.** Helspegling plus matchning gjordes innan 0038 kom, och provet ligger märkt i [forskning/speglad_0036/](../../forvarld/kropp/forskning/speglad_0036/LAS-MIG.md). Två iakttagelser därifrån är värda att ta med till 0038:
- **IK:n blev naturlig när den bara tog de sista centimetrarna** (2,8° i armen) från en riktig rörelse. Det stöder en rörelsemodell med originalet som stil.
- **Banken saknar helt korsade armar** (b-tilltal m10): varje handled var minst 29 cm från motsatt armbåge. Blicken mot servitören (guacamole) är ett look-at-problem och inte ett bankproblem.

**6. Vägen till tusen** (i BANK.md):
- **Lokalt:** 210 analyser, 123 kontomappar och 152 mp4 under `data/` (troligen dubbletter), plus 8 i `scen/klipp`.
- **När kroppen syns:** cirka 0,5 USD och cirka 10 minuter per klipp genom kedjan (Modal-läsning 0,10–0,20, liggare 0,35, resten lokalt). Generativ 1:1 när kroppen är skymd kostar mer, i pengar och i ägarens tid.
- **Första omgången:** 50 klipp för cirka 25 USD och cirka 2 timmar med 10 containrar, vilket ger uppskattat 200–300 poster.
- **Tusen klipp:** cirka 500 USD.

## Bedömning
- **Banken håller som format och etikettkälla.** Den är för liten för att lära något: 32 s, och en post per ram för skopa och ge.
- **Dess roll efter 0038:** stil och finjusteringsdata för en rörelsemodell, inte matchningskälla.
- **Nästa steg:** v1-fälten och de 50 klippen, när rörelsemodellen och licensen är valda.

## Ändrade eller nya filer
- `forvarld/kropp/BANK.md`, `bank_bygg.py` (spegling bara med `--spegla`), `bank/v0/` (23 npz, `poster.jsonl`, `innehall.json`).
- `forvarld/kropp/forskning/speglad_0036/` (det strukna provet, märkt).
- `scen/3d/NASTA.md` och `PIPE.md`.

## Kontroll mot "Klart när" (efter 0038)
- [x] BANK.md med format, innehåll och vägen till tusen.
- [x] Banken v0 på disk, utan speglingar.
- [~] Punkt 3–5 strukna, med provet bevarat som forskning.

## Avvikelser
- Fotkontakter, föremål och kvalitet per ruta ingår inte i v0.
- Ingen Modal och ingen kostnad.
