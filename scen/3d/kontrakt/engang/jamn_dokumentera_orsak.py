"""Ersätt obekräftade orsaksanspråk med den nya stegvisa ablationen."""
from prop_filer import andra

cause='''**Verifierad orsak till avvikelsen, uppföljning 10 november.** Den tidigare ablationen använde samma felaktiga ledurval som metodtabellen. Den var därför inget tillräckligt stöd för påståendet att rad-Hampel och rotorienteringen ensamma förklarade felet. `kontrakt/engang/jamn_stegablation.py` isolerar nu stegen med filmens 44/48 ledpar. Underlag: `kontrakt/ut/prop_granskning/stegablation.json`.

| Tagning | Benhållning, rå cam_t p90 px | + rad-Hampel | + komponent-Hampel för handled/underarm | + fartgräns | + lågpass |
|---|---:|---:|---:|---:|---:|
| b S1 | < 0,001 | < 0,001 | 56,79 | 56,79 | 53,46 |
| a S1 | < 0,001 | < 0,001 | 32,20 | 30,18 | 64,47 |

Komponent-Hampel ersatte verkliga handleds-/underarmsvinklar med fönstermedianer. Det flyttade alla deras fingerleder och gav ett stort p90-fel trots nästan oförändrade axlar. Lågpassningen spred och ändrade avvikelsen. Kamerarumspositionens gamla filter bidrog också: med råa kroppsparametrar ger enbart gammal cam_t b S1 3,38/8,47 px och a S1 10,29/39,50 px. Det är alltså inte samma sak som kamerans världsbana eller golvsteget. Enbart återställd rå rot förbättrar inte helheten: b S1 median 12,51 → 15,02 px, a S1 11,99 → 17,12 px med gammal cam_t. Det tidigare säkra påståendet om roten var för starkt.

Råa formparametrar varierar (b S1 maxspann 1,335), men första form, medianform och per-ruta-form ger samma FK-resultat i den testade b S1-ablationen. Variationen förklarar därför inte dess px-glapp. Det glappet kom från att tabellen felaktigt uteslöt fingrar när benen var dolda.

'''
def readme(s):
    a=s.index('**Orsaken till att den stabiliserade posen drev**');b=s.index('**Oberoende kontroll',a)
    s=s[:a]+cause+s[b:]
    a=s.index('**Vad som byttes mot vad**');b=s.index('**Omkörning.**',a)
    s=s[:a]+'''**Vad som byttes mot vad, rättad tabell.** b S1 gammal: 12,51/53,80 px, darr 0,77; bildskydd: 2,77/6,02 px, darr 2,86; vald rör 4 Hz k2 + ny cam_t: 15,73/48,50 px, darr 0,97. b S5 p90 46,14 → 30,98 mot gammal metod, men darr 1,14 → 1,53. Kenny S1 p90 62,34 → 50,14, darr 1,28 → 3,77. Metoden är jämnare än bildskyddet, men löser inte både fingerpassning och darr i alla scener. Gränserna är oförändrade; Kenny S1 och a S1 är fortfarande problem, inte godkända resultat.

'''+s[b:]
    return s+'\nKroppsmåttets processlokala cache sparar högst 32 små sammanfattningar. Nyckeln omfattar kropp/stöd, kamera, tidsurval, bildmått samt storlek och ändringstid för alla lästa mätfiler. Ändrad mätning ger ommätning; inga maskrutor hoppas över. Test i `test_kroppmatt.Matcache`.\n'
andra('scen/3d/ingest/README.md',readme)
andra('scen/3d/ingest/sekvens_jamn.py',lambda s:s[:s.index('Ersätter Hampel')]+'''Ersätter Hampel-radbyte, komponent-Hampel för handled/underarm, lågpass och bildskyddets blandning. Stegvis ablation med samma
leder som filmen visar att komponent-Hampel flyttar fingerleder och att cam_t-filter och lågpass också bidrar. Roten ensam är
ingen fastställd huvudorsak. Siffror och kända rester står i ingest/README.md och kontrakt/ut/prop_granskning/stegablation.json.

'''+s[s.index('Metod ('):])
andra('scen/3d/ingest/sekvens_stabil.py',lambda s:s[:s.index('Ändrat 10 nov')]+'''Ändrat 10 nov (jämn-passet). Före: Hampel-radbyte, komponent-Hampel för handled/underarm, lågpass, cam_t-filter och bildskydd.
Stegvis ablation visar att komponent-Hampel, cam_t-filter och lågpass gav avvikelse. Roten ensam förklarar inte felet.
Nu: rör-utjämning (sekvens_jamn.py), utan komponent-Hampel och ruta-för-ruta-blandning. Metoden ger mindre darr än bildskyddet,
men fortfarande fingerfel och darr i vissa scener; se ingest/README.md. Identiteten är låst som förr.
'''+s[s.index(' 1. Identiteten'):])
andra('scen/3d/kontrakt/PROPS.md',lambda s:s.replace('regioner_*.jpg','regioner_v2_*.jpg'))
