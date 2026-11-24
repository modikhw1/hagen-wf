# -*- coding: utf-8 -*-
"""Bygger ägarpanelen (K2) av material som redan finns. Inga generativa eller betalda anrop.

Kör:  .\\scen\\.venv\\Scripts\\python.exe motpart\\runda-4\\A-domare\\panel\\bygg_panel.py
Skriver bara under motpart/runda-4/A-domare/panel/:
  media/      blinda mediefiler (m_<hex>.mp4|png), metadata strippad
  par.json    det sidan läser (inga system-, klipp- eller filnamn)
  nyckel.json det sidan INTE läser: system, källa, kontrolltyp, egna mått
  urval_logg.json  urvalsregel, pooler, dragning, frö
"""
from __future__ import annotations

import json
import random
import secrets
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

FRO = 20261120
ROT = Path(__file__).resolve().parents[4]
PANEL = Path(__file__).resolve().parent
MEDIA = PANEL / "media"
R3 = ROT / "motpart" / "runda-3-opus"
C_UT = R3 / "C-cm-mening" / "ut"
D = R3 / "D-medielager"
B_UT = R3 / "B-nasta-klipp" / "ut"
KARNA = ROT / "forvarld_karna" / "ut"
AB = ROT / "arbetsbord"
KLIPP_BANK = ROT / "data" / "format" / "kontroll" / "klipp"
SCEN_KLIPP = ROT / "scen" / "klipp"

W, H = 540, 960  # gemensamt 9:16-format för allt som visas

rng = random.Random(FRO)
nyckel_par: list[dict] = []
publika_par: list[dict] = []


# ---------------------------------------------------------------- hjälp
def nytt_namn(ext: str) -> str:
    return f"m_{secrets.token_hex(8)}.{ext}"


def ffmpeg(args: list[str]) -> None:
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)


def video(kalla: Path, vf: str = "", mask_topp: int = 0, crop: str = "") -> str:
    """Kodar om till 540x960 H.264/AAC utan metadata. crop/mask före skalning."""
    namn = nytt_namn("mp4")
    filt = []
    if crop:
        filt.append(f"crop={crop}")
    if mask_topp:
        filt.append(f"drawbox=x=0:y=0:w=iw:h={mask_topp}:color=black:t=fill")
    filt.append(f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2")
    if vf:
        filt.append(vf)
    filt.append("format=yuv420p")
    ffmpeg(["-i", str(kalla), "-map_metadata", "-1", "-map_chapters", "-1", "-vf", ",".join(filt),
            "-c:v", "libx264", "-crf", "23", "-preset", "veryfast", "-c:a", "aac", "-b:a", "128k",
            "-ac", "2", "-movflags", "+faststart", "-fflags", "+bitexact", str(MEDIA / namn)])
    return namn


def bild(im: Image.Image, remsa: bool = False) -> str:
    namn = nytt_namn("png")
    im = im.convert("RGB")
    if not remsa:
        im = ImageOps.pad(im, (W, H), color=(0, 0, 0)) if im.size != (W, H) else im
    im.save(MEDIA / namn, format="PNG")  # Pillow skriver ingen textmetadata utan pnginfo
    return namn


def ruta_ur_video(kalla: Path, n: int) -> Image.Image:
    tmp = MEDIA / f"_tmp_{secrets.token_hex(4)}.png"
    ffmpeg(["-i", str(kalla), "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", str(tmp)])
    im = Image.open(tmp).convert("RGB")
    im.load()
    tmp.unlink()
    return im


def sudda_etikett(im: Image.Image, box=(0, 0, 110, 30)) -> Image.Image:
    im = im.copy()
    reg = im.crop(box).filter(ImageFilter.GaussianBlur(10))
    im.paste(reg, box[:2])
    return im


def band(im: Image.Image) -> list[tuple[int, int]]:
    """Hittar innehållsband (rader som inte är vit bakgrund) i en C-kompositbild."""
    g = im.convert("L")
    w, h = g.size
    px = g.load()
    rader = []
    for y in range(h):
        vals = [px[x, y] for x in range(0, w, 3)]
        m = sum(vals) / len(vals)
        rader.append(m < 238 or (max(vals) - min(vals)) > 60 and m < 246)
    ut, start = [], None
    for y, v in enumerate(rader + [False]):
        if v and start is None:
            start = y
        elif not v and start is not None:
            if y - start >= 150:
                ut.append((start, y))
            start = None
    return ut


def c_kolumner(png: Path) -> dict[str, Image.Image]:
    """3-kolumnsformat: Original | A | B. Returnerar ruta per kolumn, etiketter suddade."""
    im = Image.open(png).convert("RGB")
    (y0, y1), = [b for b in band(im) if b[1] - b[0] > 400][:1]
    cols = {}
    for i, k in enumerate(["original", "A", "B"]):
        cols[k] = sudda_etikett(im.crop((i * 270, y0, i * 270 + 270, y0 + 480)).resize((W, H), Image.LANCZOS),
                                box=(0, 0, 220, 60))
    return cols


def c_remsor(png: Path) -> dict[str, Image.Image]:
    """Remsformat: tre rader (original, A, B) med 6 rutor vardera."""
    im = Image.open(png).convert("RGB")
    bb = [b for b in band(im) if 200 <= b[1] - b[0] <= 260]
    assert len(bb) == 3, (png, band(im))
    return {k: im.crop((0, y0, 810, y0 + 240)) for k, (y0, _) in zip(["original", "A", "B"], bb)}


def m(namn: str, typ: str) -> dict:
    return {"url": f"/media/{namn}", "typ": typ}


def lagg_till(sektion, mening, media, nyckel, synk=True, ljud=False):
    pid = f"p_{secrets.token_hex(5)}"
    publika_par.append({"id": pid, "sektion": sektion, "mening": mening, "media": media,
                        "synk": synk, "ljud": ljud})
    nyckel["id"] = pid
    nyckel["sektion"] = sektion
    nyckel["mening"] = mening
    nyckel["media"] = {k: v["url"] for k, v in media.items()}
    nyckel_par.append(nyckel)
    print("  +", pid, nyckel.get("system"), nyckel.get("andringstyp"), nyckel.get("kontroll") or "", "|", mening[:60])


# ---------------------------------------------------------------- urval
def main() -> None:
    if MEDIA.exists():
        shutil.rmtree(MEDIA)
    MEDIA.mkdir(parents=True)
    logg: dict = {"fro": FRO, "skapad": datetime.now().isoformat(timespec="seconds"), "pooler": {}, "dragning": {}}

    # ---- C (runda 3, mening -> scenpaket, lådrendering). Bara still-synliga ändringar.
    cnyckel = {p["id"]: p for p in json.loads((C_UT / "blind_nyckel" / "nyckel.json").read_text(encoding="utf-8"))["par"]}
    c_mening = {}
    for r in json.loads((C_UT / "resultat.json").read_text(encoding="utf-8"))["resultat"]:
        c_mening[r.get("id")] = r.get("text")
    c_pooler = {
        "plats": ["n_t5", "n_t5@B", "n_t16", "n_t16@B", "B1", "B1@B"],
        "foremal": ["B2", "B2@B", "B3", "B6", "B6@B", "g4", "g4@B", "g5", "n_t6"],
        "kamera": ["B4", "B4@B", "B8", "B8@B", "n_t2", "n_t2@B"],
        "handling": ["g3", "g3@B"],
        "kropp": ["l1"],
    }
    c_antal = {"plats": 1, "foremal": 2, "kamera": 1, "handling": 1, "kropp": 1}
    logg["pooler"]["C"] = c_pooler
    logg["regel_C"] = ("Pooler = C:s utförda meningar vars ändring syns i en stillbild (tidsändringar som "
                       "'långsammare', 'stabilisera', 'korta ner', 'ta bort scen' utesluts eftersom C bara har "
                       "stillbilder). Dragning per pool med random.Random(FRO); högst en variant per grund-id "
                       "(X och X@B räknas som samma mening). Egna mått används inte i urvalet.")
    anvanda_bas = set()
    c_valda = {}
    for typ, pool in c_pooler.items():
        p = sorted(pool)
        rng.shuffle(p)
        val = []
        for cid in p:
            bas = cid.split("@")[0]
            if bas in anvanda_bas:
                continue
            val.append(cid)
            anvanda_bas.add(bas)
            if len(val) == c_antal[typ]:
                break
        c_valda[typ] = val
    logg["dragning"]["C"] = c_valda

    def c_text(cid: str) -> str:
        t = c_mening.get(cid)
        if not t:
            raise KeyError(cid)
        return t

    def c_par(cid: str, typ: str, kontroll: str | None = None):
        k = cnyckel[cid]
        png = C_UT / "blind" / k["bild"]
        fore_k = "A" if k["efter"] == "B" else "B"
        paket = "B:s paket" if "@B" in cid else "kärnans paket"
        if typ == "handling":
            r = c_remsor(png)
            media = {"original": m(bild(r["original"], remsa=True), "remsa"),
                     "fore": m(bild(r[fore_k], remsa=True), "remsa"),
                     "efter": m(bild(r[k["efter"]], remsa=True), "remsa")}
        else:
            r = c_kolumner(png)
            efter = r[k["efter"]]
            if kontroll == "saknas":
                efter = r[fore_k]
            elif kontroll == "annat":
                efter = ImageOps.mirror(efter)
            media = {"original": m(bild(r["original"]), "bild"), "fore": m(bild(r[fore_k]), "bild"),
                     "efter": m(bild(efter), "bild")}
        lagg_till("andring", c_text(cid), media, {
            "system": "runda3-C (mening -> scenpaket, lådrendering)", "paket": paket, "klipp": k["klipp"],
            "kalla_id": cid, "andringstyp": "kropp" if typ == "kropp" else ("rum/miljö" if typ == "plats" else
                                                                          f"scen:{typ}"),
            "kalla": str(png.relative_to(ROT)), "kontroll": kontroll,
            "forvantat": {"saknas": "a=nej", "annat": "b=nej/delvis"}.get(kontroll),
            "injektion": {"saknas": "efter = före-renderingen (ingen ändring)",
                          "annat": "efter speglad vänster-höger (rum och personer byter sida)"}.get(kontroll),
        })

    for typ, val in c_valda.items():
        for cid in val:
            c_par(cid, typ)

    # ---- forvarld_karna (mening_motor, Blender-lokalrendering)
    for klipp, manip, ruta, kalla_vid, n, mening in [
        ("guacamole", "manip_ga_med_attityd", "kontroll_s1_044.png", SCEN_KLIPP / "e-dialog-guacamole.mp4", 44,
         "låt kunden gå genom lokalen fram till bardisken med samma slappa attityd i stället för att sitta"),
        ("gelato", "manip_byt_hand", "kontroll_s1_078.png",
         SCEN_KLIPP / "kand-kennysgelato2.0-7596403003901381910.mp4", 78,
         "låt henne skopa och räcka fram med andra handen"),
    ]:
        orig = ruta_ur_video(kalla_vid, n)
        fore = Image.open(KARNA / klipp / "lokal" / ruta)
        efter = Image.open(KARNA / klipp / manip / "lokal" / ruta)
        lagg_till("andring", mening, {"original": m(bild(orig.resize((W, H), Image.LANCZOS)), "bild"),
                                      "fore": m(bild(fore.resize((W, H), Image.LANCZOS)), "bild"),
                                      "efter": m(bild(efter.resize((W, H), Image.LANCZOS)), "bild")}, {
            "system": "forvarld_karna (mening_motor + lokal Blender)", "klipp": klipp, "kalla_id": manip,
            "andringstyp": "kropp", "kontroll": None,
            "kalla": [str((KARNA / klipp / "lokal" / ruta).relative_to(ROT)),
                      str((KARNA / klipp / manip / "lokal" / ruta).relative_to(ROT)), f"{kalla_vid.name} ruta {n}"]})

    # ---- arbetsbord (regi -> Three.js), miljöbyte, video
    so = AB / "ut"
    lagg_till("andring", "det ska utspela sig i ett restaurangkök, med ett stekbord och en bänk med burgare och tillbehör",
              {"original": m(video(SCEN_KLIPP / "e-dialog-guacamole.mp4"), "video"),
               "fore": m(video(so / "soundoverlay_guacamole_orig.mp4", crop="576:1024:576:0", mask_topp=60), "video"),
               "efter": m(video(so / "soundoverlay_guacamole_kok.mp4", crop="576:1024:576:0", mask_topp=60), "video")},
              {"system": "arbetsbord v1 (regi -> Three.js)", "klipp": "guacamole", "andringstyp": "rum/miljö",
               "kontroll": None, "kalla": ["arbetsbord/ut/soundoverlay_guacamole_kok.mp4 (höger halva)",
                                           "arbetsbord/ut/soundoverlay_guacamole_orig.mp4 (höger halva)",
                                           "scen/klipp/e-dialog-guacamole.mp4"],
               "ops": "byt_miljo kok + spis 'Stekbord' + bank 'Burgare & tillbehor' (prov/rendera_soundoverlay.mjs)"},
              ljud=True)

    # ---- Kimodo-kontrasten (generativ rörelsemodell, dömd KILL på egna mått), video
    kk = AB / "kimodo_kontrast" / "ut"
    for fil, mening, typ in [
        ("fall2_ny_prop_hand_soundoverlay.mp4",
         "låt henne lyfta upp en liten tallrik på en hylla med vänster hand och hålla högerhanden nere", "kropp"),
        ("fall3_kansla_sdedit_soundoverlay.mp4",
         "låt bartendern se uttråkad och trött ut, hopsjunken bakom disken", "kropp (känsla)"),
    ]:
        lagg_till("andring", mening,
                  {"original": m(video(kk / fil, crop="576:1024:0:0", mask_topp=70), "video"),
                   "efter": m(video(kk / fil, crop="576:1024:576:0", mask_topp=70), "video")},
                  {"system": "Kimodo-SOMA-RP (generativ rörelse, arbetsbord/kimodo_kontrast)", "klipp": fil,
                   "andringstyp": typ, "kontroll": None, "kalla": str((kk / fil).relative_to(ROT)),
                   "not": "Generativ rörelsemodell: utanför K7 i CM:s ändringsled. Med för att domen 17-20 nov fälldes på egna mått."},
                  ljud=True)

    # ---- D medielager (ffmpeg/Demucs/Pillow), video
    poster = []
    for f in ["resultat.jsonl", "resultat_holdout.jsonl"]:
        for line in (D / "k8" / f).read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            fh = r.get("forhandsvisning")
            if r.get("utfall") == "utford" and fh and (ROT / fh).exists() and (ROT / fh).stat().st_size > 0 \
                    and (KLIPP_BANK / f"{r['klipp']}.mp4").exists():
                poster.append(r)
    d_pooler: dict[str, list[dict]] = {}
    for r in poster:
        d_pooler.setdefault(r["lager"], []).append(r)
    for v in d_pooler.values():
        v.sort(key=lambda r: r["klipp"])
    logg["pooler"]["D"] = {k: [r["klipp"] for r in v] for k, v in d_pooler.items()}
    logg["regel_D"] = ("Pooler = D:s utförda operationer med förhandsvisning (urval + hold-out), en pool per lager. "
                       "En dragning per lager med random.Random(FRO), oavsett D:s egna syns/kvar. Kontrollparen "
                       "dras sedan bland återstående poster där D:s egna mått sa syns=True och kvar=True.")
    d_text = {"skarmtext": "byt den pålagda texten till 'Testa vår nya meny i helgen'",
              "ljud": "ta bort musiken, behåll rösterna",
              "broll": "byt matbilden mot en annan av våra rätter",
              "montage": "korta montaget med 30 %"}
    d_valda = {}
    for lager in sorted(d_pooler):
        r = rng.choice(d_pooler[lager])
        d_valda[lager] = r
    logg["dragning"]["D"] = {k: r["klipp"] for k, r in d_valda.items()}

    def d_par(r, kontroll=None):
        orig = KLIPP_BANK / f"{r['klipp']}.mp4"
        if kontroll == "saknas":
            efter = video(orig)
        elif kontroll == "annat":
            efter = video(ROT / r["forhandsvisning"], vf="hue=h=110:s=1.4")
        else:
            efter = video(ROT / r["forhandsvisning"])
        lagg_till("andring", d_text[r["lager"]],
                  {"original": m(video(orig), "video"), "efter": m(efter, "video")},
                  {"system": "runda3-D (medielager, ffmpeg/Demucs/Pillow)", "klipp": r["klipp"],
                   "holdout": r.get("holdout"), "andringstyp": f"medielager:{r['lager']}", "kontroll": kontroll,
                   "forvantat": {"saknas": "a=nej", "annat": "b=nej/delvis"}.get(kontroll),
                   "injektion": {"saknas": "efter = originalet omkodat (ingen ändring)",
                                 "annat": "D:s riktiga förhandsvisning + kraftig färgtonsförskjutning (hue 110°)"}.get(kontroll),
                   "egna_matt_D": {"syns": r.get("syns"), "kvar": r.get("kvar")},
                   "kalla": r["forhandsvisning"]},
                  synk=r["lager"] not in ("montage",), ljud=True)

    for lager, r in d_valda.items():
        d_par(r)

    # ---- Kontrollpar (felinjektion), dragna bland material som inte redan är med
    def ren(r):
        return r.get("syns") is True and r.get("kvar") is True and r is not d_valda.get(r["lager"])
    ka_pool = [r for r in d_pooler["skarmtext"] if ren(r) and r["klipp"] not in {x["klipp"] for x in d_valda.values()}]
    kb_pool = [r for r in d_pooler["ljud"] if ren(r) and r["klipp"] not in {x["klipp"] for x in d_valda.values()}]
    ka = rng.choice(ka_pool)
    kb = rng.choice([r for r in kb_pool if r["klipp"] != ka["klipp"]])
    d_par(ka, "saknas")
    d_par(kb, "annat")
    rest_foremal = [c for c in sorted(c_pooler["foremal"]) if c.split("@")[0] not in anvanda_bas]
    rest_plats = [c for c in sorted(c_pooler["plats"]) if c.split("@")[0] not in anvanda_bas]
    kc = rng.choice(rest_foremal)
    anvanda_bas.add(kc.split("@")[0])
    kd = rng.choice(rest_plats)
    c_par(kc, "foremal", "saknas")
    c_par(kd, "plats", "annat")
    logg["dragning"]["kontroll"] = {"D_saknas": ka["klipp"], "D_annat": kb["klipp"], "C_saknas": kc, "C_annat": kd}

    # ---- 1:1-sektion: är detta samma scen?
    ett = [
        ("B (runda 3, fryst kedja), hold-out", KLIPP_BANK / "sabai.soong-7474616203366108439.mp4", 37,
         B_UT / "sabai.soong-7474616203366108439-tagningar" / "lokal" / "kontroll_s1_0037.png"),
        ("B (runda 3, fryst kedja), hold-out", KLIPP_BANK / "faros_shipandterrace-7540756212032326934.mp4", 110,
         B_UT / "faros_shipandterrace-7540756212032326934-tagningar" / "lokal" / "kontroll_s2_0110.png"),
        ("B (runda 3, fryst kedja), hold-out", KLIPP_BANK / "thepitaspot-7680489103195917590.mp4", 271,
         B_UT / "thepitaspot-7680489103195917590-tagningar" / "lokal" / "kontroll_s1_0271.png"),
        ("B (runda 3, fryst kedja), utvecklingsklipp", SCEN_KLIPP / "a-sketch-servering.mp4", 399,
         B_UT / "a-sketch-servering-tagningar" / "lokal" / "kontroll_s4_0399.png"),
    ]
    for sys_, vid, n, rend in ett:
        lagg_till("ett_till_ett", "", {"original": m(bild(ruta_ur_video(vid, n).resize((W, H), Image.LANCZOS)), "bild"),
                                       "efter": m(bild(Image.open(rend).resize((W, H), Image.LANCZOS)), "bild")},
                  {"system": sys_, "klipp": vid.stem, "ruta": n, "kalla": str(rend.relative_to(ROT)),
                   "andringstyp": "1:1-trohet", "kontroll": None})
    for namn, kalla in [("notan", "d-dialog-notan.mp4"), ("guacamole_orig", "e-dialog-guacamole.mp4")]:
        lagg_till("ett_till_ett", "", {"original": m(video(SCEN_KLIPP / kalla), "video"),
                                       "efter": m(video(so / f"soundoverlay_{namn}.mp4", crop="576:1024:576:0",
                                                        mask_topp=60), "video")},
                  {"system": "arbetsbord v1 (Three.js, utan ändring)", "klipp": kalla,
                   "kalla": f"arbetsbord/ut/soundoverlay_{namn}.mp4 (höger halva)",
                   "andringstyp": "1:1-trohet", "kontroll": None}, ljud=True)
    # 1:1-kontroll: original ur ett klipp, rendering ur ett annat
    lagg_till("ett_till_ett", "", {
        "original": m(bild(ruta_ur_video(KLIPP_BANK / "sabai.soong-7474616203366108439.mp4", 163).resize((W, H), Image.LANCZOS)), "bild"),
        "efter": m(bild(Image.open(B_UT / "thepitaspot-7680489103195917590-tagningar" / "lokal" / "kontroll_s2_0644.png").resize((W, H), Image.LANCZOS)), "bild")},
        {"system": "kontroll", "klipp": "sabai (original) / thepitaspot (rendering)", "andringstyp": "1:1-trohet",
         "kontroll": "fel_scen", "forvantat": "nej",
         "injektion": "originalruta ur sabai r163, rendering ur thepitaspot s2 r644"})

    # ---- ordning: ändringssektionen först, sedan 1:1, var för sig slumpade med FRO
    andr = [p for p in publika_par if p["sektion"] == "andring"]
    ett_ = [p for p in publika_par if p["sektion"] == "ett_till_ett"]
    ordn = random.Random(FRO + 1)
    ordn.shuffle(andr)
    ordn.shuffle(ett_)
    ordning = andr + ett_
    for i, p in enumerate(ordning, 1):
        p["nr"] = i
    (PANEL / "par.json").write_text(json.dumps({"par": ordning}, ensure_ascii=False, indent=1), encoding="utf-8")
    nyck = {"fro": FRO, "ordningsfro": FRO + 1, "skapad": logg["skapad"],
            "ordning": [p["id"] for p in ordning], "par": sorted(nyckel_par, key=lambda x: [p["id"] for p in ordning].index(x["id"]))}
    (PANEL / "nyckel.json").write_text(json.dumps(nyck, ensure_ascii=False, indent=1), encoding="utf-8")
    (PANEL / "urval_logg.json").write_text(json.dumps(logg, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"klart: {len(andr)} ändringspar, {len(ett_)} 1:1-par, frö {FRO}")


if __name__ == "__main__":
    sys.exit(main())
