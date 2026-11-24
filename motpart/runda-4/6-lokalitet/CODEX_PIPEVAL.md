Du arbetar i motpart/runda-4/6-lokalitet/ (cwd). Svara på svenska. Använd webbsökning. Ändra inga filer utom den du levererar.

Fråga: har vi valt fel avläsningspipe för att få en "god nog" 3D-nollpunkt (0.0) ur korta vertikala restaurangvideor (TikTok, 9:16, 10–60 s, 3–12 tagningar, oftast en person som pratar eller visar mat, kameran statisk eller handhållen)?

Läs först:
- ut/agy/facit00/FACIT.md, ett oberoende visuellt facit över 38 tagningar. Bara 16 % av tagningarna är god nog. Objekt och rum brister i nästan varje tagning, eftersom 2,5D-skärvor faller sönder när kameran vrids. Skala och sittande kroppar kommer därefter. Kameran är starkast.
- README.md och docstringen överst i lokalitet.py, om pipen idag: MoGe-2 ViT-L för djup och normaler per ruta, OneFormer ADE20K för panoptisk segmentering, GeoCalib, SAM 3D Body för kroppar, yolo11n-pose, nät per pixel med klippning vid djupsprång, regler L1–L9.

Uppgift:
1. Kartlägg vad som finns nu (2025–2026) och som angriper just våra brister. Ta med representativa metoder, modeller och verktyg med öppen kod eller öppna vikter, samt licens:
   - rum som strukturerade primitiver (plan, lådor, layout) i stället för pixelskärvor (layoutskattning, plananpassning, SpatialLM/SceneScript-liknande)
   - flervyrekonstruktion inom en tagning (handhållen kamera ger parallax: VGGT, MASt3R, π3 och liknande)
   - objekt som hela 3D-föremål (bild till 3D per objekt, amodal komplettering) och placering på stödytor
   - bättre segmentering än OneFormer ADE20K för mat, kärl och handhållna föremål (öppen vokabulär, SAM-familjen)
   - sittande människor och samspel mellan människa och möbel (stol, bord, kontakt)
2. För varje område: välj det mest lovande för oss, med kostnad (GPU-sekunder per tagning), mognad, licens och hur det kopplas in i vår kedja (vad det ersätter). Var konkret med repo, vikter och indata/utdata.
3. Ge en rekommenderad pipe i nivåer: "god nog för 200–500 klipp nu" (få byten med stor effekt) och "på sikt". Peka ut det byte som sannolikt lyfter flest tagningar från "nej" till "delvis/ja" enligt facit.

Var ärlig om osäkerhet. Skilj på det du verifierat i källor och det du tror. Ange källhänvisningar (URL) för varje metod.

Leverans: skriv ut/codex/pipeval/PIPEVAL.md (max 120 rader) och sammanfatta den i ditt slutmeddelande. Sista raden: KLAR eller BLOCKERAD: <orsak>.
