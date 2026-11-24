Genomfört enligt `CODEX-MOBELLYFT.md`.

- Möbelns `bild` förs genom deklarerat-vägen i [deklaration_till_hand.py](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/deklaration_till_hand.py:153).
- [mobellyft.py](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/mobellyft.py:49) placerar möbler från botten- eller toppkant, behåller Z/mått/yaw och flyttar `:pa:`-barn.
- [kompilera.py](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/kompilera.py:652) kör möbellyftet före vägg- och föremålslyft.
- Resultatet loggas i `kvalitet.mobel_lyft`; planer utan möbelbild förblir oförändrade.
- Tre syntetiska fall finns i [test_snabb.py](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/test_snabb.py:82).
- Tester: `test_deklaration` 7 OK, `test_rum` 3 OK, `test_scenbrief` 5 OK, `test_snabb` 13 OK.
- Rapporten är uppdaterad i [LOGG.md](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/foremal_logg/LOGG.md).
- Verifiera: `klipp_kor.py b-tilltal-ravara prepare --variant n06-mobel --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning2/deklaration_n06.json`
- Rendera: `klipp_kor.py b-tilltal-ravara render --variant n06-mobel --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning2/deklaration_n06.json`