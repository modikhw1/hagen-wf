# Relevanslistan (0025 del A, 13 nov)

Steget ligger i `relevans_steg.py`.
- **Modell:** Gemini 2.5 Flash genom gatewayen. Det är den enda modellen gratisnivån släpper fram.
- **Indata:** tagningarnas kontaktblad (`brief/kontakt_S*.jpg`), och underlaget nedan som givna fakta.
- **Ut:** `<klipp>/relevans.json` (körning 1), `korning_1..3.json`, `prompt_<n>.txt` och `underlag.json`.
- **Kostnad:** 0,010–0,020 USD per körning, 0,090 USD för alla sex.

## 1. Underlaget

| Källa | Fält om syfte och relevans | Gelato | Guacamole |
|---|---|---|---|
| `data/analys/<id>.json` | per scen: kamerans ord (tilt, in, följer), händernas andel, saker (YOLO), utsnitt | finns (`kennysgelato2.0-7596403003901381910`) | **saknas** |
| `data/bank/sallning/<id>.json` | `innehall`, `typ` (t.ex. relaterbar_sketch), `personer_max`, `skal` | finns | **saknas** |
| `data/e5/pro-b/<id>.json` (innehållsbedömningen) | `helhet`, `handling`, `karna`, `mall`, `platser`, `beats` (funktion: krok, vändning) | finns, och är rikast | **saknas** |
| deklarationen | `berattat_rum`, `roller`, `relevans` (bar_scenen, satter_rummet, stryks) | finns, men `relevans` och `berattat_rum` är **tomma** (n06-hand) | finns, med `relevans` ifylld (menyn i A:s hand, bardisken …) |
| `semantik/semantik.json` | sammanfattning, kärna, props, repliker, skärmtext | **saknas** | finns |
| planen | id för objekt, personer, handföremål och skärmtext | finns | finns (`e-dialog-guacamole_grupp`) |

**Det som saknas i alla källor:** kundens hand som egen post, vad personen bär, och blickriktning. Ingen källa säger "tittar på mobilen".

## 2–4. Utfallet mot ägarens läsning (`delegat/bilagor/0025/agarens-lasning.md`, öppnad efter att listorna sparats)

**Gelato.** Meningen är rätt och stabil i alla tre körningarna: kontrasten mellan det lilla smakprovet till kunden och den stora skopan till personalen.

| Ägaren | Körning 1 | 2 | 3 |
|---|---|---|---|
| hennes hand | egen post, `bar` | ingår i "hand med sked" | ingen egen post |
| vad hon bär | — | — | — |
| disken | `ramar`, eget lager | `ramar`, eget lager | `ramar`, förenklad form |
| enklare vägg eller bakgrund | `ramar`, förenklad form | samma | samma |
| kundens hand som når ut | **saknas** | **saknas** | **saknas** |
| hon bakom disken | bara som `samspel` (A–glassdisk) | samma | samma |
| skeden i handen | `bar`, bakas in i personen | samma | samma |

**Kom med i onödan, eller utanför tagningen:**
- tre skärmtexter som `bar` och eget lager
- kameran (`ramar`, en gång utelämnad och två gånger eget lager)
- den stora skopan ur S2. Den hör till klippet, men inte till S1.

**Guacamole.** Meningen är rätt och stabil: missförståndet om guacamolen "av sig själv".

| Ägaren | Körning 1 | 2 | 3 |
|---|---|---|---|
| baren mellan de två | `bar`, eget lager | `ramar`, förenklad form | `bar`, eget lager |
| han håller mobilen och tittar på den | **saknas** | "meny i A:s hand", `bar`, bakas in | "meny", `ramar`, bakas in |

**Kom med i onödan:**
- 7–8 textrader (undertexter) som `bar`
- väggar och golv som egna poster
- kassaterminalen, korrekt som `brus`

**Varför "meny":** deklarationens relevansfält säger "menyn i A:s hand". Modellen följer det givna i stället för bilden. Samma sak hände i 0024, där Gemini upprepade mätfelet när handläget gavs som fakta.

**Stabilitet mellan körningar:**
- **Stabilt:** meningen, personerna, möblerna och deras roll (disken alltid `ramar`, baren `bar` två av tre gånger).
- **Ostabilt:**
  - id-namnen (`A`, `person_A`)
  - om hand och föremål blir en eller två poster
  - kamerans roll och behandling
  - om det hållna föremålet kommer med alls (guacamole: en av tre gånger saknas det)
- **Slutsats:** listan behöver en ordning mellan körningarna (konsensus över tre, som deklarationen redan gör med k1–k5) och fasta id ur planen.

## 5. Var i kedjan
1. **Efter tagningsindelningen och semantiken, före deklarationen.** Deklarationens `relevans` ska läsas ur listan, inte tvärtom. Annars ärver listan deklarationens fel ("meny").
2. **Indata:**
   - kontaktbladen
   - innehållsbedömningen (e5: kärna, beats), när klippet finns i `data/analys`
   - sållningens typ
   - planens id
   - **inte** deklarationens relevansfält
3. **Kör tre gånger och slå ihop.** En post som finns i två av tre körningar behålls. Rollen tas efter majoritet.
4. **Lägg till posttyperna `relation` och `blick`:** "hon bakom disken" och "han tittar på mobilen". Ägaren nämner båda, och dagens form kan inte bära dem.
5. **Skärmtext och undertexter är egna:** de är inte föremål i rummet och ska inte färgas eller bli lager.
6. **Nedbrytningen läser `behandling`:** `eget_lager` ger en egen isolering eller färgkodning, `bakas_in_i_personen` ger lager 2 med föremålet (0024), `forenklad_form` ger en låda eller platt vägg, och `utelamnas` ger ingenting.
7. **Handlingsspåret (0024) läser listans id för `foremal`, `mal` och `kontakt`,** så att samma namn används i spåret och i lagren.
8. **Kundens hand som når ut ska kunna bli `bar`,** fast den saknar en egen person i planen. Listan måste kunna namnge en kroppsdel som tillhör någon utanför bild.
