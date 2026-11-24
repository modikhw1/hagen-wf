"""Steg 1: samla kedjans utdata till ett scenpaket (scenpaket/1).

Läser deklaration, plan och källa och skriver ett självständigt paket. Här ändras
sammanställningen jämfört med kedjan: rummen per tagning tillämpas (berättat mot
avslöjat), personers platser följer tagningen, och varje beslut redovisas med orsak.

Kör från projektroten:
  scen/.venv/Scripts/python.exe byggsten/brygga/samla.py --klipp notan \
     --plan scen/3d/kontrakt/ut/notan_berattat/skymning/plan.json \
     --kalla scen/3d/kontrakt/ut/notan_berattat/kalla_mobelintervall.json \
     --deklaration scen/3d/ingest/ut/notan-tagningar/plats/deklaration.json
Flaggor: --steg N (rutsteg för kroppen, 1 = varje ruta), --leder docka|bal|alla, --utan-regler
"""
import argparse, collections, datetime, hashlib, json, sys
from pathlib import Path
import numpy as np

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "scen/3d/kontrakt"))
import trohet  # noqa: E402  (adapter: läser kedjans kroppar exakt som kedjans Blender)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rotation import mat_till_quat, quat_xyzw  # noqa: E402

LEDSET = {
    "docka": ["c_spine0", "c_spine2", "c_neck", "c_head", "l_uparm", "l_lowarm", "l_wrist", "r_uparm", "r_lowarm",
              "r_wrist", "l_upleg", "l_lowleg", "l_foot", "r_upleg", "r_lowleg", "r_foot", "l_ball", "r_ball"],
}
LEDSET["bal"] = LEDSET["docka"] + ["c_spine1", "c_spine3", "l_clavicle", "r_clavicle", "c_jaw", "l_eye", "r_eye"]
LEDSET["alla"] = [n for n in trohet.NAMN if not n.startswith(("c_tongue", "c_teeth", "__"))]
# T1: armaturens leder. Härledda punkter räknas som medelvärde av källorna.
LEDSET["t1"] = ["c_spine0", "c_spine1", "c_spine2", "c_spine3", "c_neck", "c_head", "huvud_upp", "nasa_mal",
                "l_clavicle", "l_uparm", "l_lowarm", "l_wrist", "l_hand_mitt", "l_index1",
                "r_clavicle", "r_uparm", "r_lowarm", "r_wrist", "r_hand_mitt", "r_index1",
                "l_upleg", "l_lowleg", "l_foot", "l_ball", "r_upleg", "r_lowleg", "r_foot", "r_ball"]
HARLEDD = {"ogon_mitt": ("l_eye", "r_eye"),  # huvud_upp och nasa_mal räknas ur huvudets MHR-rotation
            "l_hand_mitt": ("l_index1", "l_pinky1"), "r_hand_mitt": ("r_index1", "r_pinky1")}
FOTLED_OVER_GOLV, TA_OVER_GOLV = 0.065, 0.02


def fotkontakt(X, leder, golv):
    """R3: fot under golvet lyfts till golvet, knät räknas om (två led, fasta längder, böj mot det lästa knät).
    X: (rutor, leder, 3) i meter. Returnerar antal ändrade rutor per sida."""
    ix = {n: i for i, n in enumerate(leder)}; andrade = {}
    for s in ("l", "r"):
        if not all(f"{s}_{n}" in ix for n in ("upleg", "lowleg", "foot")): continue
        h, k, f = ix[f"{s}_upleg"], ix[f"{s}_lowleg"], ix[f"{s}_foot"]; b = ix.get(f"{s}_ball")
        L1 = np.median(np.linalg.norm(X[:, k] - X[:, h], axis=1)); L2 = np.median(np.linalg.norm(X[:, f] - X[:, k], axis=1))
        n = 0
        for t in range(len(X)):
            mal = golv + FOTLED_OVER_GOLV
            if X[t, f, 2] >= mal - 0.01: continue
            H, K, F = X[t, h].copy(), X[t, k].copy(), X[t, f].copy()
            F2 = F.copy(); F2[2] = mal
            d = min(np.linalg.norm(F2 - H), L1 + L2 - 1e-4); u = (F2 - H) / max(np.linalg.norm(F2 - H), 1e-6)
            a = (L1 ** 2 - L2 ** 2 + d ** 2) / (2 * d); hh = np.sqrt(max(L1 ** 2 - a ** 2, 0.0))
            bv = (K - H) - np.dot(K - H, u) * u
            bv = bv / np.linalg.norm(bv) if np.linalg.norm(bv) > 1e-6 else np.array([0, -1.0, 0])
            X[t, k] = H + u * a + bv * hh; X[t, f] = H + u * d
            if b is not None:
                X[t, b] = X[t, b] + (X[t, f] - F); X[t, b, 2] = max(X[t, b, 2], golv + TA_OVER_GOLV)
            n += 1
        if n: andrade[s] = n
    return andrade


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p):
    try: return str(Path(p).resolve().relative_to(ROT)).replace("\\", "/")
    except ValueError: return str(p)


def r(x, n=4): return [round(float(v), n) for v in x]


def tid(s): return s.upper()  # plan 's1' <-> deklaration 'S1'


def intervall_minus(iv, bort):
    """[a,b) minus en lista [c,d), som lista av intervall."""
    ut = [list(iv)]
    for c, d in bort:
        ny = []
        for a, b in ut:
            if d <= a or c >= b: ny.append([a, b]); continue
            if a < c: ny.append([a, c])
            if d < b: ny.append([d, b])
        ut = ny
    return [x for x in ut if x[1] > x[0]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--klipp", required=True); ap.add_argument("--plan", required=True)
    ap.add_argument("--kalla", required=True); ap.add_argument("--deklaration", required=True)
    ap.add_argument("--steg", type=int, default=1); ap.add_argument("--leder", default="docka")
    ap.add_argument("--utan-regler", action="store_true", help="sammanställ som kedjan gör i dag (för jämförelse)")
    ap.add_argument("--ut")
    a = ap.parse_args()
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    kalla = json.loads(Path(a.kalla).read_text(encoding="utf-8"))
    dekl = json.loads(Path(a.deklaration).read_text(encoding="utf-8"))
    sem = kalla.get("semantik", {})
    N = len(plan["kallrutor"]); fps = plan["utdata"]["fps_taljare"] / plan["utdata"]["fps_namnare"]
    beslut = []

    # --- tagningar ---
    tagningar = []
    for sc in plan["scener"]:
        a0, b0 = sc["ut"]
        tagningar.append(dict(id=sc["id"], ut=[a0, b0], personer=[dict(id=p["id"], ankare=p.get("ankare")) for p in sc["personer"]]))
    T = {t["id"]: t for t in tagningar}

    # --- rum ur deklarationen (alla nycklar med galler_tagningar) ---
    rum = []
    for k, v in dekl.items():
        if isinstance(v, dict) and v.get("galler_tagningar"):
            tg = [t["id"] for t in tagningar if tid(t["id"]) in {tid(x) for x in v["galler_tagningar"]}]
            rum.append(dict(id=k, tagningar=tg, ut=[T[t]["ut"] for t in tg], platser=list(v.get("platser", [])),
                            status=v.get("status"), beskrivning=v.get("beskrivning"), regel=v.get("regel")))
    tackning = {k: sum(b - a for a, b in x["ut"]) for x in rum for k in [x["id"]]}
    huvudrum = max(tackning, key=tackning.get) if tackning else None
    plats_rum = {p: x["id"] for x in rum for p in x["platser"]}

    # personers platser per tagning: planens ankare, annars deklarationens person_plats
    kam_dekl = dekl.get("kameror", {})
    hem = {}
    for t in tagningar:
        pp = (kam_dekl.get(tid(t["id"])) or {}).get("person_plats")
        for p in t["personer"]:
            if not p["ankare"] and pp:
                p["ankare"] = pp
                beslut.append(dict(regel="plats_ur_deklaration", tagning=t["id"], person=p["id"], plats=pp,
                                   orsak="Planen saknar ankare; deklarationens kameror.%s.person_plats anger platsen." % tid(t["id"])))
            if p["ankare"]: hem.setdefault(p["id"], collections.Counter())[p["ankare"]] += 1
    hem = {k: v.most_common(1)[0][0] for k, v in hem.items()}

    # --- objekt: slå ihop kopior per tagning, tillämpa reglerna ---
    rad = []
    for o in plan["objekt"]:
        bas = o["id"].split(":")[0]
        s = o.get("synlig_ut") or [0, N]
        prev = next((x for x in rad if x["id"] == o["id"] and x["_slut"] == s[0]
                     and max(abs(p - q) for p, q in zip(x["pos"], o["pos_m"])) <= 0.003), None)
        if prev: prev["_slut"] = s[1]; prev["synlig_ut"][-1][1] = s[1]; continue
        rad.append(dict(id=o["id"], bas=bas, typ=o.get("deltyp") or o.get("typ"), pos=r(o["pos_m"]), rot=r(o["rotation_rad"]),
                        matt=r(o["matt_m"]), farg=o.get("farg", "#888888"), status=o.get("status"),
                        rum=plats_rum.get(bas, "gemensamt"), synlig_ut=[list(s)], _slut=s[1]))
    for x in rad: x.pop("_slut")

    if not a.utan_regler:
        for x in rad:
            # R1: ett rums objekt syns bara i rummets tagningar (huvudrummets objekt står kvar i övriga tagningar)
            if x["rum"] not in ("gemensamt", huvudrum):
                R = next(q for q in rum if q["id"] == x["rum"])
                bort = [T[t["id"]]["ut"] for t in tagningar if t["id"] not in R["tagningar"]]
                fore = x["synlig_ut"]; x["synlig_ut"] = [iv for s in fore for iv in intervall_minus(s, bort)]
                if x["synlig_ut"] != fore:
                    beslut.append(dict(regel="R1_rum_per_tagning", objekt=x["id"], rum=x["rum"], synlig_ut=x["synlig_ut"],
                                       orsak=f"{x['rum']} gäller bara {R['tagningar']} (deklarationens galler_tagningar)."))
            # R2: en persons hemplats syns inte i tagningar där personen sitter på en annan plats
            for pid, h in hem.items():
                if x["bas"] != h: continue
                bort = [t["ut"] for t in tagningar for p in t["personer"]
                        if p["id"] == pid and p["ankare"] and p["ankare"] != h]
                if bort:
                    fore = x["synlig_ut"]; x["synlig_ut"] = [iv for s in fore for iv in intervall_minus(s, bort)]
                    if x["synlig_ut"] != fore:
                        beslut.append(dict(regel="R2_hemplats_ledig", objekt=x["id"], person=pid, synlig_ut=x["synlig_ut"],
                                           orsak=f"{pid} sitter på en annan plats i {bort}; hemplatsen {h} hör till berättelsen."))
        rad = [x for x in rad if x["synlig_ut"]]

    # --- kameror per tagning ---
    nyck = plan["renderkamera"]["nycklar"]
    for t in tagningar:
        a0, b0 = t["ut"]; ks = []
        for u in range(a0, b0):
            m = np.array(nyck[u]["matris"]); k = [u] + r(m[:3, 3]) + r(mat_till_quat(m[:3, :3]), 5) + [round(nyck[u]["lins_mm"], 2)]
            if ks and ks[-1][1:] == k[1:] and u != b0 - 1: continue
            ks.append(k)
        statisk = all(k[1:] == ks[0][1:] for k in ks)
        t["kamera"] = dict(statisk=statisk, nycklar=ks[:1] if statisk else ks)

    # --- rörelse ---
    leder = LEDSET[a.leder]
    kallor = [HARLEDD.get(n, (n,)) if n not in ("huvud_upp", "nasa_mal") else ("c_head",) for n in leder]; golv_z = float(next((p.get("golv_hojd_m", 0.0) for p in plan.get("plats", [])), 0.0))
    rorelse = {}
    for sc in plan["scener"]:
        for pm in sc["personer"]:
            s = trohet.las_sekvens(pm["rorelse"]); v = dict(np.load(sc["varld"]))
            U, XS = [], []
            for u in range(*sc["ut"]):
                if (u - sc["ut"][0]) % a.steg and u != sc["ut"][1] - 1: continue
                f = sc["lokal_start"] + u - sc["ut"][0]
                pose, qm, tv = trohet.ruta_pose(sc, pm, f, True, (s, v)); alla = pose[:, :3] / 100 @ qm.T + tv
                hi = trohet.IX["c_head"]; Mh = qm @ quat_xyzw(pose[hi, 3:7]) @ quat_xyzw(s["rest"][hi, 3:7]).T
                harl = {"huvud_upp": alla[hi] + Mh @ np.array([0, 0.10, 0]), "nasa_mal": alla[hi] + Mh @ np.array([0, 0.03, 0.12])}
                XS.append(np.array([harl[n] if n in harl else alla[[trohet.IX[q] for q in k]].mean(axis=0) for n, k in zip(leder, kallor)])); U.append(u)
            X = np.array(XS)
            if not a.utan_regler:
                andr = fotkontakt(X, leder, golv_z)
                if andr:
                    beslut.append(dict(regel="R3_fotkontakt", person=pm["id"], tagning=sc["id"], rutor=andr,
                                       orsak="Foten var läst under golvet; den lyfts till fotledshöjd och knät räknas om med fasta benlängder. Bäckenet flyttas inte."))
            rutor = [[u] + [int(round(c * 1000)) for c in x.reshape(-1)] for u, x in zip(U, X)]
            rorelse.setdefault(pm["id"], []).append(dict(tagning=sc["id"], ut=sc["ut"], rutor=rutor,
                                                           kalla=dict(sekvens=rel(pm["rorelse"]), varld=rel(sc["varld"]))))

    mening = dict(
        repliker=[dict(id=x["id"], talare=x.get("talare"), text=x.get("text"), tagning=x.get("scen"),
                       a=int(round(x["start_s"] * fps)), b=int(round(x["slut_s"] * fps))) for x in sem.get("repliker", [])],
        skarmtext=[dict(id=x["id"], text=x["text"], a=int(round(x["start_s"] * fps)), b=int(round(x["slut_s"] * fps)))
                   for x in plan.get("skarmtext", [])],
        roller=dekl.get("roller"), relevans=dekl.get("relevans") or sem.get("relevans"),
        handling=sem.get("handling"), liggare=sem.get("liggare"),
        rum_relationer={x["id"]: dekl.get(x["id"], {}).get("relationer") for x in rum})

    # kedjans egen bildtrohet (kroppen genom renderkameran mot originalets 2D-leder), om den finns bredvid planen
    trohet_fil = Path(a.plan).with_name("plan_trohet.json"); tro = {}
    if trohet_fil.exists():
        for x in json.loads(trohet_fil.read_text(encoding="utf-8")).get("personer", []):
            tro[f"{x['scen']}:{x['person']}"] = dict(offset_bildhojd=round(x.get("medel_offset_bildhojdandel") or 0, 4),
                                                     skala=round(x.get("skalfaktor") or 0, 3), iou=round(x.get("bbox_iou") or 0, 3),
                                                     flaggad=bool(x.get("flaggad")), rutor=x.get("matta_rutor"))
    paket = dict(trohet=tro,
        schema="scenpaket/1", klipp=dict(id=a.klipp, video=plan.get("kallvideo")),
        tidsbas=dict(fps=fps, antal_rutor=N, regel="Rutor är sanning; sekunder = ruta / fps. Intervall [a, b)."),
        bild=dict(bredd=plan["utdata"]["bredd"], hojd=plan["utdata"]["hojd"], sensor_mm=plan["renderkamera"]["sensor_bredd_mm"]),
        koordinater="Blender: Z upp, meter; kvaternion (w,x,y,z); kroppens leder i heltal mm.",
        golv_z=float(next((p.get("golv_hojd_m", 0.0) for p in plan.get("plats", [])), 0.0)),
        rum=rum, huvudrum=huvudrum, objekt=rad, tagningar=tagningar,
        personer={p["id"]: dict(roll=p.get("roll"), farg=p.get("farg"), hemplats=hem.get(p["id"])) for p in plan["personer"]},
        leder=leder, rorelse_steg=a.steg, rorelse=rorelse, mening=mening, beslut=beslut,
        regler="av" if a.utan_regler else "R1_rum_per_tagning, R2_hemplats_ledig, R3_fotkontakt",
        proveniens=dict(skapad=datetime.datetime.now().isoformat(timespec="seconds"), av="byggsten/brygga/samla.py",
                        filer={k: dict(sokvag=rel(p), sha256=sha(p)) for k, p in
                               (("plan", a.plan), ("kalla", a.kalla), ("deklaration", a.deklaration))}))
    ut = Path(a.ut or (Path(__file__).resolve().parent / "ut" / a.klipp / ("paket_ra.json" if a.utan_regler else "paket.json")))
    ut.parent.mkdir(parents=True, exist_ok=True)
    ut.write_text(json.dumps(paket, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{rel(ut)}  {ut.stat().st_size // 1024} KB  objekt {len(rad)}  tagningar {len(tagningar)}  "
          f"kroppsrutor {sum(len(x['rutor']) for v in rorelse.values() for x in v)}  beslut {len(beslut)}")
    for b in beslut: print("  -", b["regel"], b.get("objekt") or b.get("person"), b.get("synlig_ut") or b.get("plats"))


if __name__ == "__main__":
    main()
