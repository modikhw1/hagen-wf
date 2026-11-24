"""Kontroll av vad ingreppen faktiskt gjorde (läser bygg_logg.jsonl): determinism, A/V-sluttider mot avsedd tidsavbildning, uppmätt gain, bildtakt, upplösning.
  python bygg_kontroll.py --lage test|dry
Skriver bygg_kontroll.json och bygg_kontroll.md (dry_ vid dry). Allt är diagnos; inga nya grindar.
"""
import argparse, json
from pathlib import Path
from collections import defaultdict

HER = Path(__file__).parent
ap = argparse.ArgumentParser()
ap.add_argument("--lage", required=True)
a = ap.parse_args()
pre = "" if a.lage == "test" else "dry_"
rader = [json.loads(l) for l in (HER / f"{pre}bygg_logg.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
D = defaultdict(dict)
fel = []
for r in rader:
    if "sha256" in r:
        D[r["id"]][r["variant"]] = r
    else:
        fel.append(r)
TOL = 1 / 30
SR = 44100
ut = {"bygg_fel": [{k: v for k, v in f.items() if k != "argv"} for f in fel], "klipp": {}}
md = ["| klipp | variant | upplösning | bildtakt | bildpaket | slut v (s) | slut a (s) | avsedd v/a (s) | avvikelse v/a (s) | inom 1 ruta+1 sample | gain (dB, medel) | gain (dB, max) |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for i, V in D.items():
    k = {"determinism": {}, "per_variant": {}}
    C = V.get("C")
    if not C:
        ut["klipp"][i] = {"fel": "ingen C"}
        continue
    for a_, b_ in [("Cr", "C"), ("N0", "C"), ("N0r", "N0"), ("C2", "C")]:
        if a_ in V and b_ in V:
            k["determinism"][f"{a_} mot {b_}"] = {"sha256_lika": V[a_]["sha256"] == V[b_]["sha256"], "bildhash_lika": V[a_]["innehall"]["bild"] == V[b_]["innehall"]["bild"], "ljudhash_lika": V[a_]["innehall"]["ljud"] == V[b_]["innehall"]["ljud"]}
    cv, ca = C["slutider"]["v"]["slut"], C["slutider"]["a"]["slut"]
    cm, cx = C["volym"]["mean"], C["volym"]["max"]
    for n in ["O", "C", "N0", "N1", "N2", "N3", "N4", "N5", "N6", "P"]:
        if n not in V:
            continue
        v = V[n]
        f = 1.25 if n == "P" else 1.0
        av, aa = cv / f, ca / f
        dv, da = v["slutider"]["v"]["slut"] - av, v["slutider"]["a"]["slut"] - aa
        ok = abs(dv) <= TOL + 1 / SR and abs(da) <= TOL + 1 / SR
        gm = None if (v["volym"]["mean"] is None or cm is None) else round(v["volym"]["mean"] - cm, 2)
        gx = None if (v["volym"]["max"] is None or cx is None) else round(v["volym"]["max"] - cx, 2)
        fv = v["ffprobe"]["video"]
        k["per_variant"][n] = {"upplosning": f"{fv['width']}x{fv['height']}", "bildtakt": fv["avg_frame_rate"], "paket_v": v["slutider"]["v"]["paket"], "slut_v": v["slutider"]["v"]["slut"], "slut_a": v["slutider"]["a"]["slut"],
                                "avsedd_v": av, "avsedd_a": aa, "avvikelse_v": dv, "avvikelse_a": da, "inom_tolerans": ok, "gain_medel_db": gm, "gain_max_db": gx, "codec": fv["codec_name"], "storlek": v["storlek"]}
        md.append(f"| {i.split('-')[0]} | {n} | {fv['width']}x{fv['height']} {fv['codec_name']} | {fv['avg_frame_rate']} | {v['slutider']['v']['paket']} | {v['slutider']['v']['slut']:.3f} | {v['slutider']['a']['slut']:.3f} | {av:.3f}/{aa:.3f} | {dv:+.3f}/{da:+.3f} | {'ja' if ok else '**nej**'} | {gm} | {gx} |")
    ut["klipp"][i] = k
(HER / f"{pre}bygg_kontroll.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1), encoding="utf-8")
det = [(i, kk, vv) for i, k in ut["klipp"].items() for kk, vv in k.get("determinism", {}).items()]
md.append("")
md.append("Determinism (sha256 av container / hash av avkodad bild / hash av avkodat ljud):")
md.append("")
for i, kk, vv in det:
    md.append(f"- {i.split('-')[0]} {kk}: container {vv['sha256_lika']}, bild {vv['bildhash_lika']}, ljud {vv['ljudhash_lika']}")
(HER / f"{pre}bygg_kontroll.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("bygg_fel:", len(fel))
print("\n".join(md))
