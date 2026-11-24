# -*- coding: utf-8 -*-
"""Sammanställ K8 ur k8/resultat*.jsonl och min egen bildgranskning (k8/facit_mitt.json) till k8/SAMMANSTALLNING.md.

Kategorier per klipp och lager:
  ok        utförd, syns (mitt mått) och resten kvar (mitt mått)
  syns_ej   utförd men mitt mått ser ingen ändring
  rest_andr utförd, syns, men något utanför lagret ändrades enligt mitt mått
  nej       ärligt nej;  motfraga;  fel (krasch)
Rätt hanterat (mot min granskning, inte ägarens): lagret finns och ok, eller lagret saknas och nej.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

D = Path(__file__).resolve().parent
LAGER = ["skarmtext", "ljud", "broll", "montage"]
LNAMN = {"skarmtext": "skärmtext: byt texten", "ljud": "ljud: ta bort musiken", "broll": "mat: byt matbilden",
         "montage": "montage: korta 30 %"}
FACITNYCKEL = {"skarmtext": "skarmtext", "ljud": "musik", "broll": "mat_broll", "montage": "montage"}


def kat(r):
    u = r.get("utfall")
    if u == "utford":
        if not r.get("syns"):
            return "syns_ej"
        return "ok" if r.get("kvar") else "rest_andr"
    return u or "fel"


def main():
    rader = []
    for f in ("resultat.jsonl", "resultat_holdout.jsonl"):
        p = D / "k8" / f
        if p.exists():
            rader += [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    facit = json.loads((D / "k8" / "facit_mitt.json").read_text(encoding="utf-8")) if (D / "k8" / "facit_mitt.json").exists() else {}
    L = ["# K8, sammanställning", "",
         "Genererad av `sammanstall.py` ur `k8/resultat*.jsonl`. Måtten är mina (diagnos). \"Finns\" är min egen",
         "bildgranskning av nyckelrutorna och, för musik, bankens E4-läsning (Gemini); jag kan inte lyssna.", ""]
    for grupp, filt in (("Urvalet (20 klipp)", lambda r: not r.get("holdout")), ("Hold-out (spår A, fryst kod)", lambda r: r.get("holdout"))):
        R = [r for r in rader if filt(r) and r.get("lager") in LAGER]
        if not R:
            continue
        klipp = sorted({r["klipp"] for r in R})
        L += [f"## {grupp}", "", "| lager | ok | syns ej | rest ändrad | nej | motfråga | fel | rätt hanterat* |",
              "|---|---|---|---|---|---|---|---|"]
        for lg in LAGER:
            c = Counter(kat(r) for r in R if r["lager"] == lg)
            rh = [_ratt(r, facit) for r in R if r["lager"] == lg]
            rh_n = sum(1 for x in rh if x is True)
            rh_k = sum(1 for x in rh if x is not None)
            L.append(f"| {LNAMN[lg]} | {c['ok']} | {c['syns_ej']} | {c['rest_andr']} | {c['nej']} | {c['motfraga']} | "
                     f"{c['fel']} | {rh_n}/{rh_k} |")
        L += ["", "\\* rätt hanterat = lagret finns (min granskning) och ok, eller lagret saknas och nej. "
                  "Klipp där jag inte kan avgöra om lagret finns räknas inte.", ""]
        # per stratum
        L += ["| stratum | klipp | ok per lager (text/ljud/mat/montage) | klipp med >= 3 lager rätt hanterade |", "|---|---|---|---|"]
        per = defaultdict(list)
        for r in R:
            per[r["stratum"]].append(r)
        for s, rs in sorted(per.items()):
            ks = sorted({r["klipp"] for r in rs})
            okl = "/".join(str(sum(1 for r in rs if r["lager"] == lg and kat(r) == "ok")) for lg in LAGER)
            tre = sum(1 for k in ks if sum(1 for r in rs if r["klipp"] == k and _ratt(r, facit) is True) >= 3)
            L.append(f"| {s} | {len(ks)} | {okl} | {tre}/{len(ks)} |")
        tre_alla = sum(1 for k in klipp if sum(1 for r in R if r["klipp"] == k and _ratt(r, facit) is True) >= 3)
        tre_ok = sum(1 for k in klipp if sum(1 for r in R if r["klipp"] == k and kat(r) == "ok") >= 3)
        L += ["", f"Klipp med minst 3 av 4 lager rätt hanterade: **{tre_alla}/{len(klipp)}**. "
                  f"Klipp där minst 3 av 4 lager faktiskt ändrades (ok): **{tre_ok}/{len(klipp)}**.", ""]
        L += ["### Per klipp", "", "| klipp | stratum | text | ljud | mat | montage | finns (text/musik/mat/montage) |", "|---|---|---|---|---|---|---|"]
        for k in klipp:
            rs = {r["lager"]: r for r in R if r["klipp"] == k}
            f = facit.get(k, {})
            fin = "/".join({True: "ja", False: "nej", None: "?"}[f.get(FACITNYCKEL[lg])] for lg in LAGER)
            L.append(f"| `{k}` | {rs[LAGER[0]]['stratum'] if LAGER[0] in rs else '?'} | " +
                     " | ".join(kat(rs[lg]) if lg in rs else "–" for lg in LAGER) + f" | {fin} |")
        L.append("")
    # felinjektion
    fi = [(r, x) for r in rader for x in (r.get("felinjektion") or [])]
    if fi:
        L += ["## Felinjektion: kan måtten larma?", "",
              "Variant a = ingen ändring alls (ska fällas på *syns*). Variant b = ändringen plus en ändring utanför lagret "
              "(ska fällas på *kvar*).", "", "| klipp | lager | variant | larmade |", "|---|---|---|---|"]
        for r, x in fi:
            L.append(f"| `{r['klipp']}` | {r['lager']} | {x['variant']} | {x.get('larmade', 'fel: ' + str(x.get('fel'))[:60])} |")
        n = sum(1 for _, x in fi if x.get("larmade"))
        L += ["", f"Larmade i {n} av {len(fi)} injektioner.", ""]
    # K7
    met = Counter(m for r in rader for m in (r.get("metoder") or []))
    gen = sum(1 for r in rader if r.get("generativt"))
    L += ["## K7: metoder i ändringsledet", "", "| metod | antal |", "|---|---|"] + \
         [f"| {m} | {n} |" for m, n in met.most_common()] + ["", f"Generativa anrop: {gen}.", ""]
    # tider
    ing = [r["ingest_s"] for r in rader if r.get("ingest_s") and r["lager"] == "skarmtext"]
    ops = [r.get("op_s") for r in rader if r.get("op_s") is not None and r.get("utfall") == "utford"]
    if ops:
        import statistics as st
        L += ["## Tider", "", f"Operation till färdig förhandsvisning (utförda): median {st.median(ops):.1f} s, max {max(ops):.1f} s.",
              "Ingesten kördes i delsteg med cache (forbered.py); tiden per klipp står i `lager/<klipp>/tidslinje.json` (`tider_s`).", ""]
    (D / "k8" / "SAMMANSTALLNING.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def _ratt(r, facit):
    f = facit.get(r["klipp"], {}).get(FACITNYCKEL[r["lager"]])
    if f is None:
        return None
    k = kat(r)
    return (f and k == "ok") or ((not f) and k == "nej")


if __name__ == "__main__":
    main()
