---
id: 0028
titel: Stäng 0027: kameran på rätt höjd, så att bilden bär det mätningen säger
status: redo
från: orkestratorn (Fable)
datum: 2026-11-13
följer: 0027
tillåten_skrivning: [scen/3d/gennedbrytning/]
---

Läs `delegat/kontext/vagen.md` (ny i kväll) före detta uppdrag. Den säger var det här ligger: steg 1 av tre, och det kortaste.

## Mål
Svar 0027 får status `klart`. Gelato S1 i förvärlden visar det handlingsspåret påstår, så att en människa som tittar ser det: hon skopar i ett tråg och räcker fram skeden till en kund.

## Bakgrund
0027 stannade på användningsgränsen med fyra punkter kvar (se "Kvar att göra" i svaret). Roten är rättad: fötternas glidning gick från 1,8 m till 0,10 m. Men den lösta kameran sjönk till diskens höjd i h3–h4, så diskens kant skymmer armen och tråget i rutorna 45–70. En lösning med låst kamerahöjd finns skriven i `g_forvarld/dreamina_t_rot/`, men den är inte byggd.

Varför det spelar roll: nästa uppdrag (0029) tar in den här scenen i källan, och då blir det den som Jev och CM arbetar mot. En scen där skopandet inte syns kan inte bära "hoppa över när hon skopar".

## Att göra
1. Gör om `plan_sked.json` ur den nya planen, bygg och rendera med låst kamerahöjd.
2. Kamerans väg var skakig (8,8 m). Jämna den, eller lås fler frihetsgrader, tills den liknar originalets rörelse: inåkning och tippning, inte skak. Säg vad som låstes och varför.
3. Mät om h1–h9, läge och storlek per segment, och om armen och tråget syns i rutorna 45–70 (andel synliga handledspunkter).
4. Titta på filmen själv, ruta för ruta i h3 och h8, och skriv två rader om vad en betraktare ser. Mätt sant räcker inte.
5. `STRATEGI.md`: roträttningen som eget steg, och den byggda kameran.
6. Skriv bedömningen ur 0027 (högst sex rader) och sätt svar 0027 till `klart` med pekare hit.

## Gränser
Som 0027. Inga genereringar, ingen Modal.

## Klart när
- `s_scen/film3.mp4` med remsan, där armen och tråget syns i h3.
- h1–h9 och synligheten i 45–70.
- Svar 0027 och 0028 `klart`.

## Leveransform
`delegat/svar/0028-stang-0027-kameran.md`, högst cirka 40 rader.
