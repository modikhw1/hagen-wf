# Dreamina-paket för 0023 (k2s och k2sn), 13 nov

Ersätter Ray 3.2 på fal medan fal-saldot är slut. Ägaren kör i Dreaminas webbapp (Seedance 2.5 Flash eller annan videomodell som tar nyckelbilder). Svaren läggs i `svar/` med de namn som står nedan. Sedan kör uppdragstagaren läsningen och kontrollen (`f_las.py`, `h_kontroll.py`) som vanligt.

## Indata
- `1_kalla_k2_kamerafri.mp4`: källan, 148 rutor i 29,97 fps (4,94 s). Den är kamerafri med originalets pixlar kvar och kundens hand grå. Rörelsen ska följa den.
- `nyckel_ruta000.png`, `055`, `094`, `136`: hon isolerad i samma ram som källan, vid källrutorna 0, 55, 94 och 136, alltså 0,00, 1,84, 3,14 och 4,54 s. Ruta 0 och 55 saknar skeden än (väntar på ägarens GPT-bilder, se `luma-agaren/gpt/NASTA-BILDER.md`).
- `prompt.txt`: prompten (engelska). Den gäller båda körningarna.

## Körningar
1. **k2s** → `svar/k2s.mp4`.
   - **Startbild:** `nyckel_ruta000.png`.
   - **Video som rörelsereferens:** `1_kalla_k2_kamerafri.mp4`, om modellen tar emot en sådan.
   - **Prompt:** `prompt.txt`.
   - **Inställningar:** 9:16 och 5 s.
2. **k2sn** → `svar/k2sn.mp4`.
   - Som k2s, men med alla fyra nyckelbilderna på sina tider (0,00, 1,84, 3,14 och 4,54 s) i stället för bara startbilden.

## Vad som avgör om Dreamina duger här
- **Rörelsereferensen avgör mest.** Ray 3.2 fick källvideon som styrning. Tar Seedance bara bilder och text, följer rörelsen bara prompten och nyckelbilderna. Då blir nyckelbilderna det enda som binder överkroppen, och lutningen i rutorna 40–70 riskerar att försvinna som i variant k.
- **Notera vilken modell och vilka inställningar som användes,** i `svar/installningar.txt`. Notera också om videon blev 148 rutor eller något annat.
