# Utanför bild och redigering: bokföring (0025 del C, 13 nov)

Här byggs inget. Underlaget ligger i `utanfor.json` (`utanfor.py`, ur ingestens personmasker per tagning) och i `data/analys`.

## När lämnar en bärande post bilden?
Personerna är alltid `bar`. Med "delvis" menas att masken når bildkanten. Botten är vanligt i halvbild; toppen betyder att huvudet är ute.

| Klipp, tagning | Helt borta | Delvis ute | Vad kedjan gör i dag |
|---|---|---|---|
| gelato S1 | ruta 52 | huvudet ute 38–91 (kameran zoomar in och tippar ned), botten 116–149 | Kroppen läses ändå. Saknade rutor (45–46) interpoleras i sekvensen, så hon **fryser eller glider** genom luckan. Kameran i förvärlden följer originalet, så hon **lämnar** renderingens bild där originalet gör det. Hon finns kvar i 3D, men utanför den renderade rutan. |
| gelato S2 | 48, 54–59 | topp 4–11 och 64–67 | samma |
| gelato S1, kundens hand (`bar` enligt ägaren) | utanför utom cirka 109–132 | kommer in från kanten | **Försvinner.** Den finns inte som person i planen, bara som maskdel som 0021 och 0023 tog bort. |
| guacamole S1, S3, S4 | — | — | i bild hela tiden |
| guacamole S2 | — | botten 25–50 | kundens förgrundsarm (semantik: `forgrund_arm_hand`) **utelämnas** |
| b-tilltal S1–S5, S8–S11 | S2:51, S4:70–71, S10:13, 26, 33, S11:43–45 | 82–100 % av rutorna, topp och/eller botten | Kroppen läses delvis. Det som är utanför **antas** av läsaren (ben, huvud), och korta luckor **interpoleras**. |

**Ägarens antagande, att personen finns kvar i 3D när kameran fladdrar bort, gäller redan för personer med ett spår.** Hon renderas inte, men finns. Det gäller inte för en kroppsdel utan egen person, som kundens hand. Den försvinner helt.

## Redigeringshändelser som kan misstas för rörelse
`data/analys` (210 klipp) har följande händelsetyper:
- `scen`: hårt klipp, 387 st.
- `hopp`: klipp inom samma scen, alltså jump cut, 201 st.
- `inskott`: kort inklippt bild, 60 st.
- `zoomryck`: plötslig zoom, 46 st.
- `overgang`: 47 st.
- `montage`: 10 scener.

Dessutom finns 15 scener kortare än 0,6 s. Någon egen typ för blixt eller för svep som byter vinkel finns inte. De hamnar som `scen`, `hopp` eller `zoomryck`.

**I våra fyra klipp:**
- **Gelato:** finns i `data/analys`, med ett enda klipp vid 5,2 s, alltså S1 till S2. Den snabba zoomen in och tippningen ned i S1 (rutorna 16–60, zoom 2,88 enligt analysen) är kamerarörelse, ingen redigering. Ingesten har redan förkastat 21 klippkandidater i det intervallet (`tagningar.json`, `forkastade_kandidater`), och det är rätt.
- **Guacamole och b-tilltal:** finns inte i `data/analys`. b-tilltal har elva tagningar på 0,67–2,4 s. S8 (0,67 s) och S7 (0,87 s) ligger nära gränsen för "kort klipp i samma scen". Om de är samma vinkel är inte prövat.
- **Notan:** saknar `tagningar.json` i `notan-tagningar/`. Inte kontrollerad.

**Provkroppar för senare:**
- `kennysgelato2.0-7541714460306672918`: scen på 0,5 s vid 9,97 s, samma konto som gelato.
- `blackstonesteakhouse-1778687639716`: `zoomryck` vid 11,2 och 17,7 s.
- `b.b.kebab-7695742605895765280`: `inskott` vid 12,7 s.
- `beirutfoodbynatt-7524670191163231510`: tre `hopp`, och montage i samma konto.

## Var i kedjan
1. **Vid tagningsindelningen.** `hopp`, `inskott` och `zoomryck` ur analysen (eller samma detektor körd vid ingest) skrivs in som händelser i `tagningar.json` bredvid de förkastade kandidaterna, så att sekvensen inte tolkar dem som rörelse.
2. **I handlingsspåret.** Ett segment får `kamera: klipp` eller `kamera: ryck` som mätt fält, och rutorna intill exkluderas från rörelseläsningen.
3. **Personer som lämnar bilden.** Spåret ska ha tillståndet `utanfor_bild` per ruta, i stället för tyst interpolering. En bärande kroppsdel utan egen person (kundens hand) behöver en ägare i planen.
