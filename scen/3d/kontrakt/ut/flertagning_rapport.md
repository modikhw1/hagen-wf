Klart: flerbildspassning är implementerad med bibehållen enbildsväg.

- `bilder` förs genom deklarationskedjan: [deklaration_till_hand.py](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/ingest/deklaration_till_hand.py:154).
- Robust soft-L1-passning och kantprojektion: [boxpassning.py](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/boxpassning.py:73).
- Möbelpassning, flerkameraklämning och residualrapport: [mobellyft.py](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/mobellyft.py:114).
- Föremålspassning och stödklämning: [foremallyft.py](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/foremallyft.py:79).
- Tester: 19 kontraktstester + 15 ingesttester OK; ingen full kompilering/rendering kördes.
- Indikativ disk_C RMS px: S11 1083→548; S6 929→1011; S7 15→4; S8 1354→862; S9 119→73.
- Indikativ våg RMS px: S10 45→40; S11 415→289; S8 113→151; S9 347→428.
- Rapport: [LOGG.md](C:/Users/praiseworthy/Desktop/hagen-wf/scen/3d/kontrakt/ut/foremal_logg/LOGG.md:37).
- Verifiera: `klipp_kor.py b-tilltal-ravara prepare --variant n06-fler --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning3/deklaration_n06_detekterad.json`
- Rendera: `klipp_kor.py b-tilltal-ravara render --variant n06-fler --deklaration ingest/ut/b-tilltal-ravara-tagningar/brief/uppsattning3/deklaration_n06_detekterad.json`