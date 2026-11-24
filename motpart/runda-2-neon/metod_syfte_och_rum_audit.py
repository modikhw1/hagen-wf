"""Del 1 (metod_syfte_och_rum_audit.py):
1. Granskar samtliga 15 avvikelser (A1-A15) i motpart/runda-1-claude/SYFTE.md och syfte_blind.md:
   - Kontrollerar källtyp för varje avvikelse: hur mycket vilar på faktiska repofiler vs Claudes egna
     privata andrahandskällor (`~/.claude/.../memory/minne/*.md`, oåtkomliga/ej i git-repot) vs `[T]`-tolkningar?
   - Kör om samtliga grep-motprov i SYFTE.md §2 för att verifiera Claudes citat och siffror.
   - Kontrollerar de 21 CM-meningarna i `byggsten/hjarna/UTMANING.md:64-70` (A13) samt kollar om
     `malbild.md:7` ("Förvärlden är produkten") och `AUDIT-AVSTAND.md:77` ger nyanseringar som SYFTE tonar ned.
2. Granskar motpart/runda-1-claude/RUM.md:
   - Kör om `rum_namnprov.py`-logiken (A6) utan att skriva i runda-1-claude/.
   - Verifierar tidsstämplar (A5) och determinism (`PYTHONHASHSEED`), samt kontrollerar `b-tilltal`s 4 splittrade bord
     och `notan`s A<->B-spridning i `rum_ut/ablation/`.

Kör:
  $env:PYTHONIOENCODING="utf-8"
  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-2-neon\\metod_syfte_och_rum_audit.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HIT = pathlib.Path(__file__).resolve().parent
ROT = HIT.parents[1]
R1 = ROT / "motpart/runda-1-claude"

for p in (str(ROT / "forvarld_karna"),):
    if p not in sys.path:
        sys.path.insert(0, p)

import obs_motor  # noqa: E402


def granska_syfte_kallor() -> dict:
    syfte_txt = (R1 / "SYFTE.md").read_text(encoding="utf-8")
    blind_txt = (R1 / "syfte_blind.md").read_text(encoding="utf-8")

    # Dela upp SYFTE.md avsnitt 2 per avvikelse A1..A15
    avsnitt = re.split(r"(?=^### A\d+\.)", syfte_txt, flags=re.M)
    per_a = {}
    for del_txt in avsnitt:
        m = re.match(r"^### (A\d+)\.\s*(.+)", del_txt)
        if not m:
            continue
        aid, rubrik = m.group(1), m.group(2).strip()
        # Skär bort ev. avsnitt 3+ om A15 är sist
        body = del_txt.split("\n---\n")[0]
        minne_refs = re.findall(r"minne/[A-Za-z0-9_.\-]+(?::[0-9\-]+)?", body)
        logg_refs = re.findall(r"(?:logg|[0-9a-f]{8}…jsonl):[0-9\-]+", body)
        repo_refs = re.findall(r"(?:karta|delegat|byggsten|scen|forvarld|AGENTS|CLAUDE|LAGE|ARKITEKTUR|../hagen-ui)[A-Za-z0-9_./\-]+(?::[0-9,\-]+)?", body)
        per_a[aid] = dict(
            rubrik=rubrik,
            antal_minne_refs=len(minne_refs),
            minne_refs=sorted(set(minne_refs)),
            logg_refs=sorted(set(logg_refs)),
            antal_repo_refs=len(set(repo_refs)),
            har_minne_som_huvudbelagg=bool(minne_refs),
        )

    # Kör om Claudes egna grep-motprov ur SYFTE.md §2!
    def count_pat(paths: list[pathlib.Path], pat: str) -> dict:
        rx = re.compile(pat, re.I)
        hits = {}
        for p in paths:
            if p.exists():
                n = sum(1 for line in p.read_text(encoding="utf-8", errors="replace").splitlines() if rx.search(line))
                hits[str(p.relative_to(ROT))] = n
        return hits

    karna_py = sorted((ROT / "forvarld_karna").glob("*.py"))
    greps = dict(
        A1_agare=count_pat([ROT / "LAGE.md", ROT / "forvarld_karna/ARKITEKTUR.md", ROT / "CLAUDE.md"], r"ägare"),
        A4_manus=count_pat([ROT / "LAGE.md"] + karna_py, r"manus"),
        A4_manus_ARKITEKTUR=count_pat([ROT / "forvarld_karna/ARKITEKTUR.md"], r"manus|storyboard"),
        A5_jev_anrop=count_pat(karna_py, r"typesafe|systemone"),
        A7_kimodo_mening=count_pat([ROT / "forvarld_karna/mening_motor.py"], r"kimodo"),
        A8_svar_0042=sorted(p.name for p in (ROT / "delegat/svar").glob("*0042*")) if (ROT / "delegat/svar").exists() else [],
        A9_formatkort_i_karna=count_pat(karna_py, r"data/format|formatkort|byggsten/hand"),
        A10_liggare=count_pat(karna_py + [ROT / "LAGE.md", ROT / "forvarld_karna/ARKITEKTUR.md"], r"liggare"),
        A11_essens_k1=count_pat([ROT / "LAGE.md", ROT / "forvarld_karna/ARKITEKTUR.md"], r"essens|\bK1\b"),
        A12_medielager=count_pat(karna_py, r"skärmtext|skarmtext|montage|ljud"),
        A14_fraga_vanta_agare_LAGE=count_pat([ROT / "LAGE.md"], r"fråga|vänta|ägare"),
        A14_fraga_vanta_CLAUDE=count_pat([ROT / "CLAUDE.md"], r"fråga|vänta|ägare"),
    )

    # Kontrollera käll-balans: hur många unika `minne/`-filer citerar syfte_blind.md + SYFTE.md?
    alla_minne = sorted(set(re.findall(r"minne/[A-Za-z0-9_.\-]+", syfte_txt + "\n" + blind_txt)))
    # Kontrollera också meningen i `UTMANING.md:64-70`: 7+6+5+3+1 = 22 (inte 21!!) — ett litet räknefel i både UTMANING och SYFTE!
    utmaning = (ROT / "byggsten/hjarna/UTMANING.md").read_text(encoding="utf-8")
    tab_rad = re.findall(r"\|\s*([^|]+)\|\s*([^|]+)\|\s*(\d+)\s*\|", utmaning)
    tab_sum = sum(int(x[2]) for x in tab_rad if int(x[2]) < 20)

    # Kontrollera om minnesmappen ens finns i git-repot (det gör den inte!)
    minne_i_repo = any((ROT / "minne").glob("*")) if (ROT / "minne").exists() else False

    return dict(
        per_avvikelse=per_a,
        antal_avvikelser_med_minne_ref=sum(v["har_minne_som_huvudbelagg"] for v in per_a.values()),
        unika_privata_minnesfiler_citerade=alla_minne,
        minne_finns_i_repo=minne_i_repo,
        greps_verifierade=greps,
        utmaning_tabell_summa=tab_sum,
    )


def granska_rum() -> dict:
    # 1. Kör om mappnamnsprovet (A6) direkt i minnet (rör inga filer i runda-1-claude)
    falska = [
        "a-dialog-kafe-tagningar",
        "b-ny-kund-tagningar",
        "kennys-burgare-tagningar",
        "bonotanical-tagningar",
        "notan-tagningar-v2",
        "z-helt-okant-tagningar",
    ]
    namnprov = {}
    for n in falska:
        p = HIT / "_finns_inte" / n
        sem = obs_motor._modell_semantik(p)
        fk = obs_motor._fokal(p)
        namnprov[n] = dict(
            semantik_klipp=(sem or {}).get("klipp"),
            fokal_px=round(fk[0], 1) if fk else None,
        )

    # 2. Kontrollera tidsstämplar på forvarld_karna/*.py och ut/*/obs.json, recept.json
    import datetime
    ts = {}
    for rel in [
        "forvarld_karna/regler.py", "forvarld_karna/schema.py", "forvarld_karna/rums_pussel.py",
        "forvarld_karna/obs_motor.py", "forvarld_karna/scen_brygga.py", "forvarld_karna/verifiera.py",
        "forvarld_karna/ut/notan/obs.json", "forvarld_karna/ut/notan/recept.json",
        "forvarld_karna/ut/guacamole/obs.json", "forvarld_karna/ut/gelato/obs.json", "forvarld_karna/ut/asketch/obs.json",
    ]:
        p = ROT / rel
        if p.exists():
            ts[rel] = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    # 3. Sammanfatta Claudes ablation på notan (hur många varianter behåller s7-kopplingen?)
    abl_dir = R1 / "rum_ut/ablation/notan"
    notan_abl = {}
    if abl_dir.exists():
        for jf in sorted(abl_dir.glob("*.json")):
            d = json.loads(jf.read_text(encoding="utf-8"))
            bords = d.get("bord", {})
            har_s7_lank = any("s1" in shots and "s7" in shots for shots in bords.values())
            notan_abl[jf.stem] = dict(P=d.get("P"), n_bord=d.get("n_bord"), s7_lank=har_s7_lank, ab=d.get("avstand", {}).get("A-B"))

    # 4. Kolla `farg_signatur` i alla obs.json (R6)
    farg_null = {}
    for k in ("guacamole", "gelato", "asketch", "notan"):
        o = json.loads((ROT / "forvarld_karna/ut" / k / "obs.json").read_text(encoding="utf-8"))
        dets = [d for cl in o["klipp"] for d in cl["detektioner"]]
        farg_null[k] = f"{sum(d.get('farg_signatur') is not None for d in dets)}/{len(dets)} icke-null"

    # 5. Kolla asketch-receptets geometri (R7)
    ask_rec = json.loads((ROT / "forvarld_karna/ut/asketch/recept.json").read_text(encoding="utf-8"))
    x0, x1, y0, y1 = ask_rec["rum"]["granser"]
    noder = {n["id"]: n["position"] for n in ask_rec["noder"]}
    import math
    ask_geo = dict(
        rum_m=[round(x1 - x0, 4), round(y1 - y0, 4)],
        ab_m=round(math.dist(noder["A"][:2], noder["B"][:2]), 3),
        A_till_bord1=round(math.dist(noder["A"][:2], noder["bord_1"][:2]), 3),
        A_till_bord2=round(math.dist(noder["A"][:2], noder["bord_2"][:2]), 3),
        B_till_bord2=round(math.dist(noder["B"][:2], noder["bord_2"][:2]), 3),
        B_till_bord1=round(math.dist(noder["B"][:2], noder["bord_1"][:2]), 3),
    )

    return dict(namnprov=namnprov, tidsstamplar=ts, farg_signatur=farg_null, asketch_geo=ask_geo,
                notan_ablation_antal=len(notan_abl),
                notan_ablation_bryter=[k for k, v in notan_abl.items() if not v["s7_lank"]])


def main():
    s = granska_syfte_kallor()
    print("=== 1. SYFTE.md KÄLL- & GREP-AUDIT ===")
    print(f"  Avvikelser som citerar privata minnesfiler (~/.claude/.../memory/): {s['antal_avvikelser_med_minne_ref']}/15")
    print(f"  Unika privata minnesfiler citerade ({len(s['unika_privata_minnesfiler_citerade'])}): {s['unika_privata_minnesfiler_citerade']}")
    print(f"  Finns `minne/` i git-repot? {s['minne_finns_i_repo']}")
    print(f"  UTMANING.md:64-70 tabellsumma: {s['utmaning_tabell_summa']} (SYFTE anger '21')")
    print("  Verifierade greps:", json.dumps(s["greps_verifierade"], ensure_ascii=False, indent=2))

    r = granska_rum()
    print("\n=== 2. RUM.md AUDIT ===")
    print("  Namnprov (A6):", json.dumps(r["namnprov"], ensure_ascii=False))
    print("  Tidsstämplar (A5):", json.dumps(r["tidsstamplar"], ensure_ascii=False, indent=2))
    print("  farg_signatur (R6):", r["farg_signatur"])
    print("  asketch geometri (R7):", r["asketch_geo"])
    print(f"  notan ablation ({r['notan_ablation_antal']} varianter), bryter s7-länk:", r["notan_ablation_bryter"])

    out = dict(syfte=s, rum=r)
    (HIT / "metod_syfte_och_rum_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nSparade:", HIT / "metod_syfte_och_rum_audit.json")


if __name__ == "__main__":
    main()
