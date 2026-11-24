"""Passar in kroppsläsningar mot en rumsdeklaration (plats/deklaration.json): golvet är givet, läsningen redovisas som fel mot det.
  python passa_deklaration.py   -> ut/notan-tagningar/plats/inpassning.json
Per person och ruta: lodriktning ur kroppen (stående: vrister->nacke; sittande: höfter->nacke), höjder längs lodet relativt kameran.
Stående: golv = lägsta fotpunkt minus sula. Sittande: golv = höft minus (sitthöjd + höftled över sits). Allt i meter, median över rutor.
Kroppsläsningarna är SAM 3D Body med rätt brännvidd för respektive bild (1024 px för originalen, 768 px för Lumas breddade S4)."""
import json, glob
from pathlib import Path
import numpy as np

HIT = Path(__file__).resolve().parent; NOTAN = HIT / 'ut' / 'notan-tagningar'
LUMA = HIT.parent / 'lasformat' / 'luma-paket' / 'mat_video' / 'V1_S4' / 'kropp' / 'p'
D = json.loads((NOTAN / 'plats' / 'deklaration.json').read_text(encoding='utf-8')); P = D['berattat_rum']['platser']
SITS, BORD = P['stol_A']['sitthojd_m'], P['bord_1']['storlek_m']['hojd']
HOFT_OVER_SITS = 0.085      # golvmätningens prior "backen_over_sits_m" 0,02–0,15, mitten
SULA = 0.025                # golvmätningens "sula_prior_m"
OGON, AXEL, ARMB, HOFT, KNA, VRIST, FOT, NACKE = [1, 2], [5, 6], [7, 8], [9, 10], [11, 12], [13, 14], [15, 16, 17, 18, 19, 20], 69

def las(mapp):
    R = []
    for f in sorted(glob.glob(str(mapp / '*.npz'))):
        d = np.load(f); R.append(d['pred_keypoints_3d'] + d['pred_cam_t'])    # kamerarum: x höger, y ned, z framåt
    return np.array(R)

def lod(K, staende):
    a = K[:, VRIST].mean(1) if staende else K[:, HOFT].mean(1); u = K[:, NACKE] - a
    u = np.median(u, axis=0); return u / np.linalg.norm(u)                      # en lodriktning per tagning (kameran antas stilla nog)

def hojd(K, u): return K @ u                                                    # höjd över kameran längs lodet (negativ = under)

def plan(K, u):                                                                 # vågrätt avstånd från kameran
    v = K - np.outer(K @ u, u); return np.linalg.norm(v, axis=-1)

def med(x): return round(float(np.median(x)), 3)
def spr(x): return round(float(np.percentile(x, 90) - np.percentile(x, 10)), 3)

res = {}
def person(namn, mapp, staende, kalla):
    K = las(mapp); u = lod(K, staende); h = hojd(K, u)                          # h: rutor x leder
    r = dict(kalla=kalla, rutor=len(K), lage='står' if staende else 'sitter', kameralutning_grader=round(float(np.degrees(np.arccos(-u[1]))), 1))
    if staende:
        v, hö = h[:, [13, 15, 16, 17]].min(1), h[:, [14, 18, 19, 20]].min(1)
        golv = np.minimum(v, hö) - SULA
        r['golv_ur'] = 'synliga fötter'; r['fot_vanster_mot_hoger_cm'] = round(float(np.median(v - hö)) * 100, 1)
        r['langd_hjassa_till_sula_m'] = None
    else:
        golv = h[:, HOFT].mean(1) - (SITS + HOFT_OVER_SITS)
        r['golv_ur'] = f'deklarerad sits {SITS} m + höftled {HOFT_OVER_SITS} m över sits'
        r['lasta_vrister_over_golv_m'] = med(h[:, VRIST].mean(1) - golv)       # fötterna syns inte: detta är modellens gissning mot deklarationen
        r['lagsta_armbage_over_golv_m'] = med(np.percentile(h[:, ARMB].min(1) - golv, 10)); r['bord_deklarerat_m'] = BORD
    r['kamerahojd_over_golv_m'] = med(-golv); r['kamerahojd_spridning_p10_p90_m'] = spr(-golv)
    r['ogonhojd_over_golv_m'] = med(h[:, OGON].mean(1) - golv); r['hofthojd_over_golv_m'] = med(h[:, HOFT].mean(1) - golv)
    r['axelhojd_over_golv_m'] = med(h[:, AXEL].mean(1) - golv)
    r['vagratt_avstand_kamera_till_hoft_m'] = med(plan(K[:, HOFT].mean(1), u)); r['vagratt_avstand_kamera_till_ogon_m'] = med(plan(K[:, OGON].mean(1), u))
    res[namn] = r; return r

def sittande(namn, tagning, kalla):
    """Sittande med deklarerad kamerahöjd: lodet löses ur höjden i stället för ur bålen. Rollning 0, bara lutningen är fri."""
    K = las(NOTAN / tagning / 'kropp' / '1'); H = D['kameror'][tagning]['hojd_m']; hoft = np.median(K[:, HOFT].mean(1), axis=0)
    mal = -(H - SITS - HOFT_OVER_SITS)                                          # höftens höjd relativt kameran
    ps = np.radians(np.linspace(-60, 60, 24001)); us = np.c_[np.zeros_like(ps), -np.cos(ps), -np.sin(ps)]   # p > 0: kameran tittar nedåt
    p = ps[np.argmin(np.abs(us @ hoft - mal))]; u = np.array([0, -np.cos(p), -np.sin(p)]); h = hojd(K, u); golv = -H
    bal = np.median(K[:, NACKE] - K[:, HOFT].mean(1), axis=0); bal /= np.linalg.norm(bal)
    fram = np.array([0, 0, -1.0]) - u * (np.array([0, 0, -1.0]) @ u); fram /= np.linalg.norm(fram)          # vågrätt mot kameran
    r = dict(kalla=kalla, rutor=len(K), lage='sitter', golv_ur=f'deklarerad kamerahöjd {H} m', kameralutning_grader=round(float(np.degrees(p)), 1),
             ballutning_mot_kameran_grader=round(float(np.degrees(np.arctan2(bal @ fram, bal @ u))), 1),
             ogonhojd_over_golv_m=med(h[:, OGON].mean(1) - golv), axelhojd_over_golv_m=med(h[:, AXEL].mean(1) - golv),
             lagsta_armbage_over_golv_m=med(np.percentile(h[:, ARMB].min(1) - golv, 10)), bord_deklarerat_m=BORD,
             lagsta_handled_over_golv_m=med(np.percentile(h[:, [41, 62]].min(1) - golv, 10)),
             lasta_vrister_over_golv_m=med(h[:, VRIST].mean(1) - golv),
             vagratt_avstand_kamera_till_hoft_m=med(plan(K[:, HOFT].mean(1), u)), vagratt_avstand_kamera_till_ogon_m=med(plan(K[:, OGON].mean(1), u)))
    res[namn] = r; return r

for nm, tg in (('A_S1', 'S1'), ('A_S3', 'S3'), ('A_S6', 'S6'), ('B_S2', 'S2'), ('B_S5', 'S5')):
    sittande(nm + '_deklarerad_kamera', tg, f'original {tg}, fokal 1024')

A = person('A_S1', NOTAN / 'S1' / 'kropp' / '1', False, 'original S1, fokal 1024')
B = person('B_S2', NOTAN / 'S2' / 'kropp' / '1', False, 'original S2, fokal 1024')
C = person('C_S4_luma', LUMA, True, 'Luma V1 breddat S4, fokal 768')
# Originalets S4 har inga fötter i bild: golvet sätts med C:s höfthöjd ur den breddade läsningen.
K = las(NOTAN / 'S4' / 'kropp' / '1'); u = lod(K, True); h = hojd(K, u)
golv = h[:, HOFT].mean(1) - C['hofthojd_over_golv_m']
res['C_S4_original'] = dict(kalla='original S4, fokal 1024; golv ur höfthöjden i Lumas läsning', rutor=len(K), kamerahojd_over_golv_m=med(-golv),
                            modellens_dolda_fotter_over_golv_cm=round(float(np.median(h[:, [13, 14, 15, 16, 17, 18, 19, 20]].min(1) - SULA - golv)) * 100, 1),
                            vagratt_avstand_kamera_till_hoft_m=med(plan(K[:, HOFT].mean(1), u)), ogonhojd_over_golv_m=med(h[:, OGON].mean(1) - golv))

a, b, c = np.array(P['stol_A']['pos_m']), np.array(P['stol_B']['pos_m']), np.array(P['staplats_C']['pos_m'])
kors = {
    'S1_kamera_vid_B_huvud': dict(regel='motbildskameran står vid motpartens huvud', kamerahojd_m=A['kamerahojd_over_golv_m'], B_ogonhojd_m=B['ogonhojd_over_golv_m'],
                                  skillnad_cm=round((A['kamerahojd_over_golv_m'] - B['ogonhojd_over_golv_m']) * 100, 1)),
    'S2_kamera_vid_A_huvud': dict(regel='motbildskameran står vid motpartens huvud', kamerahojd_m=B['kamerahojd_over_golv_m'], A_ogonhojd_m=A['ogonhojd_over_golv_m'],
                                  skillnad_cm=round((B['kamerahojd_over_golv_m'] - A['ogonhojd_over_golv_m']) * 100, 1)),
    'stolsavstand': dict(deklarerat_m=float(np.linalg.norm(b - a)), last_S1_kamera_till_A_hoft_m=A['vagratt_avstand_kamera_till_hoft_m'], last_S2_kamera_till_B_hoft_m=B['vagratt_avstand_kamera_till_hoft_m']),
    'S4_kamera': dict(kamerahojd_luma_m=C['kamerahojd_over_golv_m'], kamerahojd_original_m=res['C_S4_original']['kamerahojd_over_golv_m'],
                      sittande_ogonhojd_A_B_m=[A['ogonhojd_over_golv_m'], B['ogonhojd_over_golv_m']],
                      last_avstand_kamera_till_C_m=C['vagratt_avstand_kamera_till_hoft_m'], last_avstand_original_m=res['C_S4_original']['vagratt_avstand_kamera_till_hoft_m'],
                      deklarerat_fran_A_stol_m=round(float(np.linalg.norm(c - a)), 2), deklarerat_fran_B_stol_m=round(float(np.linalg.norm(c - b)), 2),
                      deklarerat_fran_bordets_mitt_m=round(float(np.linalg.norm(c - np.array(P['bord_1']['mitt_m']))), 2)),
}
ut = dict(deklaration='plats/deklaration.json', antaganden=dict(sitthojd_m=SITS, hoftled_over_sits_m=HOFT_OVER_SITS, sula_m=SULA, lod='ur kroppen, en riktning per tagning'), personer=res, korskontroller=kors)
(NOTAN / 'plats' / 'inpassning.json').write_text(json.dumps(ut, indent=1, ensure_ascii=False), encoding='utf-8')
for k, v in res.items():
    print(k)
    for x, y in v.items(): print('   ', x, y)
for k, v in kors.items(): print(k, v)
