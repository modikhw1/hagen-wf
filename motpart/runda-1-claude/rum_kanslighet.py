"""rum_kanslighet.py — sammanfattar känslighet (±30 %) och ablation per klipp mot varianten "bas".

    python rum_kanslighet.py [--md ut.md]

"Håller" = samma sluttro och samma bordsstruktur (mängden av tagningslistor per bord) som bas.
För notan räknas också s7-länken (A:s bord och burken sedda i s7). Avståndet A↔B redovisas som spann.
"""
from __future__ import annotations

import argparse
import json
import pathlib

HIT = pathlib.Path(__file__).resolve().parent


def struktur(m):
    return tuple(sorted(tuple(t) for t in m["bord"].values()))


def lank(m):
    a = next((t for t in m["bord"].values() if "s1" in t), [])
    return "s7" in a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=None)
    a = ap.parse_args()
    ut = []
    for klipp in ("notan", "guacamole", "gelato", "asketch"):
        d = HIT / "rum_ut" / "ablation" / klipp
        data = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted(d.glob("*.json"))}
        bas = data.get("bas")
        if not bas:
            continue
        s_var = {n: m for n, m in data.items() if n.startswith("S_")}
        brott = []
        avst = []
        for n, m in s_var.items():
            ok = m["tro"] == bas["tro"] and struktur(m) == struktur(bas)
            if klipp == "notan":
                ok = ok or (m["tro"] == bas["tro"] and lank(m))
            if not ok:
                brott.append(f"`{n}`: {m['tro']} | bord {'; '.join(','.join(t) for t in struktur(m))}")
            if "A-B" in m["avstand"]:
                avst.append((m["avstand"]["A-B"], n))
        rad = f"### {klipp}: {len(s_var) - len(brott)}/{len(s_var)} känslighetsvarianter håller"
        ut.append(rad)
        ut.append(f"bas: {bas['tro']} (P {bas['P']}) | bord {'; '.join(','.join(t) for t in struktur(bas))}"
                  + (f" | A↔B {bas['avstand'].get('A-B')}" if bas["avstand"].get("A-B") else ""))
        if avst:
            lo, hi = min(avst), max(avst)
            ut.append(f"A↔B över känslighetsvarianterna: {lo[0]} ({lo[1]}) – {hi[0]} ({hi[1]})")
        for b in brott:
            ut.append(f"- bryter: {b}")
        andra = [n for n in data if not n.startswith("S_") and n != "bas" and not n.startswith("bas")]
        abl_brott = [n for n in andra if not (data[n]["tro"] == bas["tro"] and struktur(data[n]) == struktur(bas))]
        ut.append(f"ablation/övrigt: {len(andra) - len(abl_brott)}/{len(andra)} samma som bas; avviker: "
                  + ", ".join(f"`{n}`" for n in abl_brott))
        ut.append("")
    txt = "\n".join(ut)
    if a.md:
        pathlib.Path(a.md).write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
