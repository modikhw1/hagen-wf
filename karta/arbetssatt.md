# Arbetssätt

- **En del i taget.** Föreslå nästa steg på några rader och vänta på ja. Bygg inte helheter i ett svep.
- **Korta svar.** Det som ska läsas syns i appen, inte i texten.
- **Visa, gömd inte bakom etiketter.** Hellre form, färg och rörelse än förklarande text i gränssnittet.
- **Reglerna formar ytorna.** Wikin i `hagen-ui/wiki` är källa, men reglerna vägs om. Några få bär flödet, resten räknas fram eller väntar. Ny regel = forma om helheten, inte lägga till en panel.
- **Kreativitet först.** CM styr och AI:n föreslår. Inget glitter: modernt och levande, som Lovable och Recraft.
- **Wireframe före kod i hagen-ui.** `app/` är platshållare. Inga riktiga videor och ingen backend.

## Köra wireframen

```
cd app
npm install
npm run dev        # http://localhost:5180/#1 … #6
```

## Uppdatera kartan

När något bestäms: lägg till en rad i [beslut.md](beslut.md), uppdatera vyn eller objektet det gäller och flytta frågan ur [pins.md](pins.md). En ny vy får en egen fil i `vyer/` och en rad i [README.md](README.md).
