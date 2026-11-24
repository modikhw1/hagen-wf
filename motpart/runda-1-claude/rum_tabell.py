"""rum_tabell.py — sammanställer rum_ut/ablation/<klipp>/*.json till en markdowntabell.

    python rum_tabell.py notan [--prefix L2_] [--md ut.md]

Kolumner: variant, sluttro, P, bord (tagningar), A↔B, antal bord, tid.
För notan: "s7-länk" = A:s bord (det som innehåller s1) och burken (bonaqua) är sedda i s7.
"""
from __future__ import annotations

import argparse
import json
import pathlib

HIT = pathlib.Path(__file__).resolve().parent


def las(klipp: str):
    d = HIT / "rum_ut" / "ablation" / klipp
    return {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted(d.glob("*.json"))}


def s7_lank(m):
    a_bord = next((t for t in m["bord"].values() if "s1" in t), [])
    burk = [t for k, t in m["foremal"].items() if "s1" in t and "s3" in t and "s6" in t]
    return ("s7" in a_bord), any("s7" in t for t in burk)


def rad(namn, m, klipp):
    bord = "; ".join(",".join(t) for t in sorted(m["bord"].values(), key=lambda t: t[0]))
    av = m["avstand"].get("A-B", "–")
    extra = ""
    if klipp == "notan":
        b, f = s7_lank(m)
        extra = f" | {'ja' if b else 'NEJ'}/{'ja' if f else 'NEJ'}"
    return f"| {namn} | {m['tro']} | {m['P']:.3f} | {bord} | {av} | {m['n_bord']}{extra} | {m['sek']} |"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("klipp")
    ap.add_argument("--prefix", default="")
    ap.add_argument("--md", default=None)
    a = ap.parse_args()
    data = las(a.klipp)
    huvud = "| variant | sluttro | P | bord (tagningar) | A↔B m | n bord" + (" | s7: bord/burk" if a.klipp == "notan" else "") + " | s |"
    streck = "|" + "---|" * (huvud.count("|") - 1)
    ut = [huvud, streck]
    for n, m in data.items():
        if n.startswith(a.prefix) or n == "bas":
            ut.append(rad(n, m, a.klipp))
    txt = "\n".join(ut)
    if a.md:
        pathlib.Path(a.md).write_text(txt + "\n", encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
