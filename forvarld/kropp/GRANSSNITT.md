# Gränssnittet: från frihetsgrad i liggaren till mål för kroppskontrollern (0034)

Jev väljer en frihetsgrad (`fg_hand=vanster`). Liggaren gör valet till **mål**. Kontrollern gör målen till rörelse i hela kroppen. Det är samma form oavsett om kontrollern är en optimering (provet i 0034), motion matching eller en fysikbaserad kontroller.

## Indata till kontrollern (JSON, `kropp/mal.json`)
```json
{
 "person": "A",
 "kalla_rorelse": "<sekvens_1.npz>",
 "rutor": [0, 156],
 "aktiva_kroppsdelar": ["l_hand", "bal"],
 "passiva_kroppsdelar": ["r_hand"],
 "mal": [
  {"namn": "skopa", "kroppsdel": "l_hand", "rutor": [28, 66], "typ": "position", "kalla": "entitet trag (liggaren)", "varden": "originalets högerhandsbana i rutorna, dvs. där tråget nåddes"},
  {"namn": "ge", "kroppsdel": "l_hand", "rutor": [90, 146], "typ": "position", "kalla": "entitet kund_hand (liggaren e6.mottagare)", "varden": "originalets högerhandsbana, dvs. där kundens hand tog skeden"}
 ],
 "kontakter": [
  {"kroppsdel": "fotter", "typ": "still", "rutor": [0, 156], "kalla": "roträttningen (0027)"},
  {"kroppsdel": "l_hand", "foremal": "sked", "typ": "fast", "rutor": [0, 156], "kalla": "liggaren: i_hand(A_hand_v, sked) efter spridningen"}
 ],
 "stil": {"referens": "originalets rörelse", "vikt_pose": 1.0, "vikt_jamnhet": 1.0, "led_granser": "MHR"},
 "passiv": {"r_hand": "originalets vänstra arm, speglad (vila)"}
}
```

## För "andra handen"
- **Kroppsdelar:** vänster arm aktiv; höger arm passiv (gör det vänster gjorde: vilar, eller stöder mot disken); bålen fri att vrida sig, med en kostnad för avvikelsen från originalet.
- **Mål per tid:**
  - **skopa (h3, rutor 28–66):** vänster hand i tråget, där höger hand var.
  - **räcka fram och ge (h6–h8, rutor 90–146):** vänster hand vid kundens hand. Punkten är densamma eftersom kunden inte flyttar sig.
- **Kontakter:** fötterna står still (ankaret ur 0027); skeden sitter i vänster hand hela förloppet.
- **Stil:** originalets rörelse är priorn. Det ska vara samma tempo, samma lutning och samma bålrörelse, så nära som målen tillåter.
- **Tillbaka** ger kontrollern:
  - en ny sekvens (pose per ruta, MHR)
  - måtten: hur nära målen, hur långt från originalet, ledvinklar inom gränser, kontakter hållna
  - vilka rutor som är ändrade: `utford_niva_1`, märkt med kontrollerns namn

Liggarens spridning säger vad som följer med, och kontrollern säger hur. Jev rör ingenting av det.
