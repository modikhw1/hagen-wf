# -*- coding: utf-8 -*-
"""Ändringsoperationer per medielager. Varje operation tar en tidslinje (medielager/1), ger en ny tidslinje
och en förhandsvisning (mp4) eller ett ärligt nej / en motfråga. Ingen generativ bild, video eller ljud (K7):
bara ffmpeg (trim, concat, overlay, drawbox, boxblur, amix, afade), Pillow för att rita text, och kundens
eget material.

Signaturer (alla returnerar Resultat, se _resultat):
    lagg_till_text(tl, text, fran=0.0, till=None, position="mitt")
    byt_text(tl, ny_text, mal=None)            mal: objekt-id ("x3"), del av den gamla texten, eller None
    ta_bort_text(tl, mal=None)
    ta_bort_musik(tl)
    byt_musik(tl, kalla)                       kalla: ljudfil som CM har bifogat, eller kundens eget klipp (mp4)
    byt_matbild(tl, mot=None, kundmaterial=None)  mot: maträtt i fri text ("pizzan"), eller None = annan egen matbild
    korta_montage(tl, andel=0.3, mal_s=None)

Resultat (dict):
    utfall        "utford" | "nej" | "motfraga"
    skal          varför (alltid ifyllt)
    lager         "skarmtext" | "ljud" | "mat" | "montage"
    tidslinje     ny tidslinje (dict) med nyckeln "andring", eller None
    forhandsvisning  sökväg (relativ repo-roten) till mp4, eller None
    andrat        det ändrade området: {"tid": [[a, b], ...], "box": [x0, y0, x1, y1] normerat eller None,
                  "ljud": bool, "video": bool, "tidsavbildning": [[ny_a, ny_b, orig_a, orig_b], ...] eller None}
    metoder       lista över verktyg som användes (för K7-loggen)
    alternativ    vid motfråga
"""
import copy
import json
import re
import tempfile
import textwrap
from pathlib import Path

import numpy as np

from .gemensamt import FORHANDS, ROT, abs_, ff, las, probe, rel, skriv

FONT = "C:/Windows/Fonts/arialbd.ttf"
X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p"]
K7_METODER = {"ffmpeg", "pillow", "kundens eget material", "demucs-stam (separation av originalets ljud)"}


def _resultat(utfall, skal, lager, tl=None, fil=None, andrat=None, metoder=(), alternativ=None):
    return dict(utfall=utfall, skal=skal, lager=lager, tidslinje=tl,
                forhandsvisning=rel(fil) if fil else None, andrat=andrat, metoder=list(metoder),
                generativt=False, alternativ=alternativ)


def _ut(tl, namn):
    p = FORHANDS / tl["klipp"] / f"{namn}.mp4"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _ny_tl(tl, op, param, lager):
    n = copy.deepcopy(tl)
    n["andring"] = dict(op=op, parametrar=param, lager=lager, fran_tidslinje=tl.get("andring", {}).get("op", "original"),
                        generativt=False)
    return n


def _hex(h, standard=(255, 255, 255)):
    if not h or not isinstance(h, str) or not re.match(r"^#[0-9a-fA-F]{6}$", h):
        return standard
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


# ---------------------------------------------------------------- text som bild
def _text_png(W, H, text, box_n, stil, ut_png):
    """Rita text i den lästa stilen på en genomskinlig bild i ramens storlek. Returnerar ritad låda (px)."""
    from PIL import Image, ImageDraw, ImageFont
    stil = stil or {}
    radh = max(0.018, float(stil.get("radhojd_rel") or 0.03))
    storlek = max(14, int(round(radh * H * 0.9)))
    f = ImageFont.truetype(FONT, storlek)
    x0, y0, x1, y1 = box_n
    cx = (x0 + x1) / 2 * W
    cy = (y0 + y1) / 2 * H
    maxb = 0.86 * W
    tecken_b = max(1.0, f.getlength("abcdefghij") / 10)
    rader = []
    for stycke in text.split("\n"):
        rader += textwrap.wrap(stycke, width=max(4, int(maxb / tecken_b))) or [""]
    glyf = _hex(stil.get("glyffarg"), (255, 255, 255))
    kontur = stil.get("kontur")
    platta = bool(stil.get("platta"))
    bak = _hex(stil.get("bakgrund"), (255, 255, 255))
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rad_px = int(storlek * 1.22)
    tot_h = rad_px * len(rader)
    bredder = [d.textlength(r, font=f) for r in rader]
    top = cy - tot_h / 2
    pad = int(storlek * 0.35)
    if platta:
        bx0 = cx - max(bredder) / 2 - pad
        d.rounded_rectangle([bx0, top - pad, cx + max(bredder) / 2 + pad, top + tot_h + pad], radius=pad,
                            fill=bak + (255,))
    stroke = 0 if platta else max(2, storlek // 12)
    sfarg = _hex(kontur, (0, 0, 0)) if kontur else ((0, 0, 0) if sum(glyf) > 380 else (255, 255, 255))
    for i, (r, b) in enumerate(zip(rader, bredder)):
        d.text((cx - b / 2, top + i * rad_px), r, font=f, fill=glyf + (255,), stroke_width=stroke,
               stroke_fill=sfarg + (255,))
    im.save(ut_png)
    return [int(cx - max(bredder) / 2 - pad), int(top - pad), int(cx + max(bredder) / 2 + pad), int(top + tot_h + pad)]


def _box_px(box_n, W, H, pad_rel=0.25):
    x0, y0, x1, y1 = box_n
    h = (y1 - y0) * H
    p = pad_rel * h
    return [max(0, int(x0 * W - p)), max(0, int(y0 * H - p)), min(W, int(x1 * W + p)), min(H, int(y1 * H + p))]


def _filter_tack_och_text(W, H, tack, bilder, start="[0:v]"):
    """Bygg filterkedja: täck lådor (platta eller oskärpa) och lägg på PNG-bilder (ingång 1..n)."""
    kedja, cur, n = [], start, 0
    for t in tack:
        x0, y0, x1, y1 = t["px"]
        w, h = (x1 - x0) // 2 * 2, (y1 - y0) // 2 * 2
        en = f"between(t,{t['fran']:.3f},{t['till']:.3f})"
        if t["metod"] == "platta":
            r, g, b = _hex(t.get("farg"), (255, 255, 255))
            kedja.append(f"{cur}drawbox=x={x0}:y={y0}:w={w}:h={h}:color=0x{r:02x}{g:02x}{b:02x}@1:t=fill:enable='{en}'[v{n}]")
        else:
            rad = max(2, min(h // 2 - 1, w // 2 - 1, 24))
            kedja.append(f"{cur}split[s{n}a][s{n}b];[s{n}b]crop={w}:{h}:{x0}:{y0},boxblur={rad}:4[s{n}c];"
                         f"[s{n}a][s{n}c]overlay={x0}:{y0}:enable='{en}'[v{n}]")
        cur = f"[v{n}]"
        n += 1
    for i, b in enumerate(bilder, 1):
        en = f"between(t,{b['fran']:.3f},{b['till']:.3f})"
        kedja.append(f"{cur}[{i}:v]overlay=0:0:enable='{en}'[v{n}]")
        cur = f"[v{n}]"
        n += 1
    return ";".join(kedja), cur


def _rendera_text(tl, tack, nya, namn):
    video = abs_(tl["kalla"]["video"])
    W, H = tl["kalla"]["bredd"], tl["kalla"]["hojd"]
    ut = _ut(tl, namn)
    with tempfile.TemporaryDirectory() as td:
        bilder = []
        for i, n in enumerate(nya):
            png = Path(td) / f"t{i}.png"
            n["ritad_px"] = _text_png(W, H, n["text"], n["box"], n.get("stil"), png)
            bilder.append(dict(png=png, fran=n["fran"], till=n["till"]))
        graf, slut = _filter_tack_och_text(W, H, tack, bilder)
        args = ["-i", video]
        for b in bilder:
            args += ["-loop", "1", "-i", b["png"]]
        if not graf:
            graf, slut = "[0:v]null[v0]", "[v0]"
        ff(*args, "-filter_complex", graf, "-map", slut, "-map", "0:a?", *X264, "-c:a", "copy",
           "-t", f"{tl['kalla']['langd']:.3f}", ut)
    return ut


def _overlag(tl):
    return [x for x in tl.get("skarmtext", []) if x.get("typ") == "overlag"]


def _valj_text(tl, mal):
    ov = _overlag(tl)
    if not ov:
        return None, "nej"
    if mal:
        for x in ov:
            if x["id"] == mal:
                return [x], "ok"
        kand = [x for x in ov if mal.lower() in x["text"].lower()]
        if kand:
            return kand[:1], "ok"
        return None, "motfraga"
    fria = [x for x in ov if not x.get("remsa")]
    if fria:
        return [max(fria, key=lambda x: (x["till"] - x["fran"]) * (x["box"][2] - x["box"][0]))], "ok"
    return None, "motfraga"


def _tack_for(x, W, H):
    st = x.get("stil") or {}
    return dict(px=_box_px(x["box"], W, H), fran=x["fran"], till=x["till"],
                metod="platta" if st.get("platta") else "oskarpa", farg=st.get("bakgrund"))


def byt_text(tl, ny_text, mal=None):
    W, H = tl["kalla"]["bredd"], tl["kalla"]["hojd"]
    val, s = _valj_text(tl, mal)
    if s == "nej":
        return _resultat("nej", "Klippet har ingen pålagd skärmtext. Text i själva bilden (skylt, meny) hör till scenen "
                                "och byts inte här. Vill du lägga till en ny text?", "skarmtext")
    if s == "motfraga":
        alt = [dict(id=x["id"], text=x["text"], fran=x["fran"], till=x["till"]) for x in _overlag(tl)][:12]
        return _resultat("motfraga", "Vilken text menar du? Klippet har flera textrader (eller bara löpande textning).",
                         "skarmtext", alternativ=alt)
    tack = [_tack_for(x, W, H) for x in val]
    nya = [dict(text=ny_text, box=x["box"], stil=x.get("stil"), fran=x["fran"], till=x["till"]) for x in val]
    fil = _rendera_text(tl, tack, nya, "byt_text")
    n = _ny_tl(tl, "byt_text", dict(ny_text=ny_text, mal=[x["id"] for x in val]), "skarmtext")
    for x in n["skarmtext"]:
        if x["id"] in [v["id"] for v in val]:
            x.update(text_original=x["text"], text=ny_text, andrad=True)
    return _resultat("utford", f"Bytte '{val[0]['text'][:60]}' ({val[0]['fran']}–{val[0]['till']} s) mot ny text. "
                               f"Originalet täcks med {tack[0]['metod']}.", "skarmtext", n, fil,
                     dict(tid=[[x["fran"], x["till"]] for x in val], box=[x["box"] for x in val],
                          ritad_px=[v["ritad_px"] for v in nya], ljud=False, video=True, tidsavbildning=None),
                     ["ffmpeg drawbox/boxblur/overlay", "pillow text"])


def ta_bort_text(tl, mal=None):
    W, H = tl["kalla"]["bredd"], tl["kalla"]["hojd"]
    val, s = _valj_text(tl, mal)
    if s == "nej":
        return _resultat("nej", "Klippet har ingen pålagd skärmtext att ta bort.", "skarmtext")
    if s == "motfraga":
        alt = [dict(id=x["id"], text=x["text"]) for x in _overlag(tl)][:12]
        return _resultat("motfraga", "Vilken text ska bort?", "skarmtext", alternativ=alt)
    tack = [_tack_for(x, W, H) for x in val]
    fil = _rendera_text(tl, tack, [], "ta_bort_text")
    n = _ny_tl(tl, "ta_bort_text", dict(mal=[x["id"] for x in val]), "skarmtext")
    n["skarmtext"] = [x for x in n["skarmtext"] if x["id"] not in [v["id"] for v in val]]
    return _resultat("utford", f"Tog bort '{val[0]['text'][:60]}' genom att täcka den ({tack[0]['metod']}). "
                               "Pixlarna under texten finns inte; täckningen syns.", "skarmtext", n, fil,
                     dict(tid=[[x["fran"], x["till"]] for x in val], box=[x["box"] for x in val], ljud=False,
                          video=True, tidsavbildning=None), ["ffmpeg drawbox/boxblur"])


def lagg_till_text(tl, text, fran=0.0, till=None, position="mitt"):
    till = min(tl["kalla"]["langd"], till if till is not None else fran + 3.0)
    y = {"ovre": 0.18, "mitt": 0.5, "nedre": 0.78}.get(position, 0.5)
    stil = dict(radhojd_rel=0.035, glyffarg="#ffffff", kontur="#000000", platta=False)
    ov = _overlag(tl)
    if ov:  # ärv klippets egen textstil
        stil = dict(ov[0].get("stil") or stil)
    box = [0.1, y - 0.02, 0.9, y + 0.02]
    fil = _rendera_text(tl, [], [dict(text=text, box=box, stil=stil, fran=fran, till=till)], "lagg_till_text")
    n = _ny_tl(tl, "lagg_till_text", dict(text=text, fran=fran, till=till, position=position), "skarmtext")
    n["skarmtext"].append(dict(id=f"x{len(tl.get('skarmtext', [])) + 1}", text=text, fran=fran, till=till, box=box,
                               typ="overlag", stil=stil, ny=True))
    return _resultat("utford", f"Lade till texten {fran}–{till} s ({position}).", "skarmtext", n, fil,
                     dict(tid=[[fran, till]], box=[box], ljud=False, video=True, tidsavbildning=None),
                     ["ffmpeg overlay", "pillow text"])


# ---------------------------------------------------------------- ljud
def ta_bort_musik(tl):
    mu = tl.get("musik") or {}
    if not tl["kalla"].get("ljud"):
        return _resultat("nej", "Klippet har inget ljudspår.", "ljud")
    if not mu.get("finns"):
        return _resultat("nej", f"Ingen musik hittad (andel musikfönster {mu.get('andel_fonster')}; {mu.get('regel', '')}).",
                         "ljud")
    st = mu.get("stammar") or {}
    tal = abs_(st["tal"]) if st.get("tal") else None
    if not tal or not tal.exists():
        return _resultat("nej", "Musik finns men separationen saknas; kan inte skilja tal från musik.", "ljud")
    ut = _ut(tl, "ta_bort_musik")
    video = abs_(tl["kalla"]["video"])
    ff("-i", video, "-i", tal, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
       "-t", f"{tl['kalla']['langd']:.3f}", ut)
    n = _ny_tl(tl, "ta_bort_musik", {}, "ljud")
    n["musik"] = dict(finns=False, borttagen=True, tidigare=mu)
    varning = ""
    if (mu.get("sang_risk") or 0) > 0.3:
        varning = f" Varning: sångrisk {mu['sang_risk']}: sång i musiken kan ligga kvar i talstammen."
    if tl["tal"].get("sekunder", 0) < 0.5:
        varning += " Klippet har inget tal; kvar blir tystnad och omgivningsljud som hamnat i röststammen."
    return _resultat("utford", "Musiken (trummor, bas, övrigt) är borttagen; röststammen ur originalet är kvar. Bilden "
                               "är orörd (strömkopia)." + varning, "ljud", n, ut,
                     dict(tid=[[0, tl["kalla"]["langd"]]], box=None, ljud=True, video=False, tidsavbildning=None),
                     ["demucs-stam (separation av originalets ljud)", "ffmpeg strömkopia av bild"])


def byt_musik(tl, kalla):
    """Byt musikbädden mot en ljudfil CM bifogar eller kundens eget klipp. Talstammen behålls."""
    mu = tl.get("musik") or {}
    if not kalla:
        return _resultat("motfraga", "Vilken musik? Bifoga en ljudfil eller peka på ett av kundens egna klipp. "
                                     "Ny musik genereras inte.", "ljud", alternativ=["bifoga fil", "kundens klipp"])
    kalla = abs_(kalla)
    if not kalla.exists():
        return _resultat("nej", f"Hittar inte {kalla}.", "ljud")
    st = mu.get("stammar") or {}
    tal = abs_(st["tal"]) if st.get("tal") else None
    video = abs_(tl["kalla"]["video"])
    L = tl["kalla"]["langd"]
    ut = _ut(tl, "byt_musik")
    if tal and tal.exists():
        graf = f"[2:a]atrim=0:{L:.3f},afade=t=out:st={max(0, L - 1):.3f}:d=1,volume=0.6[m];[1:a][m]amix=inputs=2:normalize=0[a]"
        ff("-i", video, "-i", tal, "-stream_loop", "-1", "-i", kalla, "-filter_complex", graf, "-map", "0:v",
           "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-t", f"{L:.3f}", ut)
        skal = "Röststammen behölls och den nya musiken lades under."
    else:
        graf = f"[1:a]atrim=0:{L:.3f},afade=t=out:st={max(0, L - 1):.3f}:d=1[a]"
        ff("-i", video, "-stream_loop", "-1", "-i", kalla, "-filter_complex", graf, "-map", "0:v", "-map", "[a]",
           "-c:v", "copy", "-c:a", "aac", "-t", f"{L:.3f}", ut)
        skal = "Klippet saknar separerat tal; hela ljudet byttes mot den nya musiken."
    n = _ny_tl(tl, "byt_musik", dict(kalla=rel(kalla)), "ljud")
    n["musik"] = dict(finns=True, kalla=rel(kalla), tidigare=mu)
    return _resultat("utford", skal, "ljud", n, ut,
                     dict(tid=[[0, L]], box=None, ljud=True, video=False, tidsavbildning=None),
                     ["ffmpeg amix/atrim/afade", "kundens eget material eller CM:s fil"])


# ---------------------------------------------------------------- mat / B-roll
def kundmaterial(tl, pool_mapp=None):
    """Kundens andra egna klipp i den lokala banken (samma konto). Tagningar och CLIP-vektorer räknas och cachas.

    Körs i scen/.venv. Returnerar lista med dict(video, klipp, tagning, fran, till, klass, p, vektor).
    """
    from .gemensamt import CACHE
    from . import steg_bild, steg_tagningar
    konto = tl["klipp"].rsplit("-", 1)[0]
    pool = Path(pool_mapp) if pool_mapp else ROT / "data/format/kontroll/klipp"
    ut = []
    for v in sorted(pool.glob(f"{konto}-*.mp4")):
        if v.stem == tl["klipp"] or v.stem in UNDANTAG:
            continue
        cfil = CACHE / "kundmaterial" / f"{v.stem}.json"
        if cfil.exists():
            tg = las(cfil)
        else:
            with tempfile.TemporaryDirectory() as td:
                tg, _ = steg_tagningar.tagningar(v, td)
            steg_bild.klassa_tagningar(v, tg)
            for t in tg:
                t.pop("nyckelruta", None)
            skriv(cfil, tg)
        ut += [dict(video=rel(v), klipp=v.stem, tagning=t["id"], fran=t["fran"], till=t["till"], klass=t.get("klass"),
                    p=t.get("p"), vektor=t.get("vektor")) for t in tg]
    return ut


UNDANTAG = set()   # klipp som inte får användas som material (t.ex. hold-out före utvärdering); sätts av anroparen


def byt_matbild(tl, mot=None, kundmaterial_lista=None):
    from . import steg_bild
    tg = tl["tagningar"]
    mat = [t for t in tg if t.get("klass") == "mat"]
    pmm = [t for t in tg if t.get("klass") == "person_med_mat"]
    if not mat:
        if pmm:
            return _resultat("nej", f"Maten syns bara i tagningar där en person håller eller äter den "
                                    f"({', '.join(t['id'] for t in pmm)}). Att byta den i bild kräver nyinspelning; "
                                    "det står i manuset i stället.", "mat")
        return _resultat("nej", "Klippet har ingen matbild (ingen tagning klassad som mat).", "mat")
    mal = mat[0]
    kand = []
    for t in tg:  # andra mattagningar i samma klipp
        if t is mal or t.get("klass") != "mat" or not t.get("vektor"):
            continue
        kand.append(dict(video=tl["kalla"]["video"], klipp=tl["klipp"], tagning=t["id"], fran=t["fran"], till=t["till"],
                         klass="mat", p=t.get("p"), vektor=t["vektor"]))
    kand += [k for k in (kundmaterial_lista or []) if k.get("klass") == "mat" and k.get("vektor")]
    mv = np.array(mal["vektor"], np.float32)
    kand = [k for k in kand if float(np.dot(np.array(k["vektor"], np.float32), mv)) < 0.92]  # inte samma bild
    if not kand:
        return _resultat("nej", "Kunden har ingen annan egen matbild i materialet som finns (samma klipp och kundens "
                                "andra klipp i banken). Ny bild genereras inte.", "mat")
    if mot:
        x_en, p = steg_bild.matcha_mat(mot, [k["vektor"] for k in kand])
        bast = int(np.argmax(p))
        if p[bast] < 0.5:
            return _resultat("nej", f"Hittar ingen egen bild av '{mot}' ({x_en}) hos kunden (bästa p={p[bast]:.2f}). "
                                    "Ny bild genereras inte.", "mat",
                             alternativ=[dict(klipp=k["klipp"], tagning=k["tagning"]) for k in kand[:5]])
        kalla = kand[bast]
        kalla["p_mot"] = round(p[bast], 3)
    else:
        kalla = max(kand, key=lambda k: (k.get("p") or {}).get("mat", 0))
    video = abs_(tl["kalla"]["video"])
    src = abs_(kalla["video"])
    W, H, fps = tl["kalla"]["bredd"], tl["kalla"]["hojd"], tl["kalla"]["fps"] or 30
    a, b = mal["fran"], mal["till"]
    L = b - a
    Ls = kalla["till"] - kalla["fran"]
    s0 = kalla["fran"] + max(0.0, (Ls - L) / 2)
    tpad = max(0.0, L - Ls)
    ut = _ut(tl, "byt_matbild")
    # Text som låg ovanpå den gamla bilden ritas om på den nya (samma text, läst stil och plats).
    ovan = [x for x in _overlag(tl) if min(b, x["till"]) - max(a, x["fran"]) > 0.1]
    with tempfile.TemporaryDirectory() as td:
        bilder = []
        for i, x in enumerate(ovan):
            png = Path(td) / f"o{i}.png"
            _text_png(W, H, x["text"], x["box"], x.get("stil"), png)
            bilder.append(dict(png=png, fran=max(a, x["fran"]), till=min(b, x["till"])))
        delar = [f"[0:v]trim=0:{a:.3f},setpts=PTS-STARTPTS[p0]",
                 f"[1:v]trim={s0:.3f}:{s0 + min(L, Ls):.3f},setpts=PTS-STARTPTS,fps={fps},"
                 f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
                 + (f",tpad=stop_mode=clone:stop_duration={tpad:.3f}" if tpad > 0 else "") + "[p1]",
                 f"[0:v]trim={b:.3f},setpts=PTS-STARTPTS[p2]",
                 "[p0][p1][p2]concat=n=3:v=1:a=0[c]"]
        graf = ";".join(delar)
        cur = "[c]"
        for i, bl in enumerate(bilder, 2):
            graf += f";{cur}[{i}:v]overlay=0:0:enable='between(t,{bl['fran']:.3f},{bl['till']:.3f})'[o{i}]"
            cur = f"[o{i}]"
        args = ["-i", video, "-i", src]
        for bl in bilder:
            args += ["-loop", "1", "-i", bl["png"]]
        ff(*args, "-filter_complex", graf, "-map", cur, "-map", "0:a?", *X264, "-c:a", "copy",
           "-t", f"{tl['kalla']['langd']:.3f}", ut)
    n = _ny_tl(tl, "byt_matbild", dict(mot=mot, mal=mal["id"], kalla=dict(klipp=kalla["klipp"], tagning=kalla["tagning"],
                                                                         fran=round(s0, 3))), "mat")
    for t in n["tagningar"]:
        if t["id"] == mal["id"]:
            t.update(utbytt=dict(klipp=kalla["klipp"], tagning=kalla["tagning"], fran=round(s0, 3)))
    eget = "samma klipp" if kalla["klipp"] == tl["klipp"] else "kundens klipp " + kalla["klipp"]
    return _resultat("utford", f"Tagning {mal['id']} ({a:.2f}–{b:.2f} s) bytt mot {eget}, tagning {kalla['tagning']}."
                               + (f" Källan är {tpad:.2f} s för kort; sista rutan står still." if tpad > 0 else "")
                               + (f" {len(bilder)} textrad(er) ovanpå ritades om." if bilder else ""), "mat", n, ut,
                     dict(tid=[[a, b]], box=None, ljud=False, video=True, tidsavbildning=None,
                          kalla=dict(video=kalla["video"], fran=round(s0, 3), till=round(s0 + min(L, Ls), 3))),
                     ["ffmpeg trim/concat/scale/overlay", "kundens eget material"]
                     + (["pillow text"] if bilder else []))


# ---------------------------------------------------------------- montage
def korta_montage(tl, andel=0.3, mal_s=None):
    tg = tl["tagningar"]
    L = tl["kalla"]["langd"]
    if len(tg) < 3:
        return _resultat("nej", f"Klippet har {len(tg)} tagning(ar); det finns inget montage att korta. Kortare "
                                "tagningar inom en tagning är en ryggradsändring (spår C).", "montage")
    mal = mal_s if mal_s else L * (1 - andel)
    if mal >= L - 0.5:
        return _resultat("nej", "Målet är inte kortare än klippet.", "montage")
    tal = tl["tal"]["segment"]
    skydd = {tg[0]["id"], tg[-1]["id"]}           # krok och avslut
    for t in tg:
        if t.get("tal"):
            skydd.add(t["id"])                    # tal klipps inte mitt i
    beh = {t["id"]: [t["fran"], t["till"]] for t in tg}
    kvar = L
    # 1) Stryk hela B-rolltagningar utan tal, från mitten och utåt, kortaste först.
    stryk = sorted([t for t in tg if t["id"] not in skydd and t.get("klass") in ("mat", "miljo", "text")],
                   key=lambda t: t["langd"])
    strukna = []
    for t in stryk:
        if kvar - t["langd"] < mal - 0.3:
            continue
        if kvar <= mal:
            break
        strukna.append(t["id"])
        kvar -= t["langd"]
        beh.pop(t["id"])
    # 2) Korta återstående tagningar utan tal till minst 1,0 s, kring mitten, längsta först.
    if kvar > mal:
        for t in sorted([t for t in tg if t["id"] in beh and not t.get("tal")], key=lambda t: -t["langd"]):
            if kvar <= mal:
                break
            a, b = beh[t["id"]]
            kan = (b - a) - 1.0
            if kan <= 0.1:
                continue
            ta = min(kan, kvar - mal)
            m = (a + b) / 2
            ny = (b - a) - ta
            beh[t["id"]] = [m - ny / 2, m + ny / 2]
            kvar -= ta
    if L - kvar < 0.5:
        return _resultat("nej", "Alla tagningar som går att korta bär tal, krok eller avslut; montaget kortas inte "
                                "utan att tal klipps. Säg vilken tagning som får gå.", "montage",
                         alternativ=[t["id"] for t in tg])
    seg = [(tid, *beh[tid]) for tid in [t["id"] for t in tg] if tid in beh]
    avb, t0 = [], 0.0
    for tid, a, b in seg:
        avb.append([round(t0, 3), round(t0 + b - a, 3), round(a, 3), round(b, 3)])
        t0 += b - a
    video = abs_(tl["kalla"]["video"])
    ut = _ut(tl, "korta_montage")
    st = (tl.get("musik") or {}).get("stammar") or {}
    harmusik = bool((tl.get("musik") or {}).get("finns")) and st.get("tal") and abs_(st["tal"]).exists()
    vdel = [f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}]" for i, (_, a, b) in enumerate(seg)]
    graf = ";".join(vdel) + ";" + "".join(f"[v{i}]" for i in range(len(seg))) + f"concat=n={len(seg)}:v=1:a=0[v]"
    args = ["-i", video]
    if not tl["kalla"].get("ljud"):
        amap = []
    elif harmusik:
        # Tal följer sina tagningar; musikbädden löper obruten från start och tonas ut i slutet.
        args += ["-i", abs_(st["tal"]), "-i", abs_(st["musik"])]
        adel = [f"[1:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={max(0, b - a - 0.02):.3f}:d=0.02[a{i}]"
                for i, (_, a, b) in enumerate(seg)]
        graf += ";" + ";".join(adel) + ";" + "".join(f"[a{i}]" for i in range(len(seg))) + \
            f"concat=n={len(seg)}:v=0:a=1[tal];[2:a]atrim=0:{t0:.3f},afade=t=out:st={max(0, t0 - 1):.3f}:d=1[mus];" \
            "[tal][mus]amix=inputs=2:normalize=0[a]"
        amap = ["-map", "[a]"]
    else:
        adel = [f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={max(0, b - a - 0.02):.3f}:d=0.02[a{i}]"
                for i, (_, a, b) in enumerate(seg)]
        graf += ";" + ";".join(adel) + ";" + "".join(f"[a{i}]" for i in range(len(seg))) + \
            f"concat=n={len(seg)}:v=0:a=1[a]"
        amap = ["-map", "[a]"]
    ff(*args, "-filter_complex", graf, "-map", "[v]", *amap, *X264, "-c:a", "aac", "-b:a", "160k", ut)
    n = _ny_tl(tl, "korta_montage", dict(andel=andel, mal_s=round(mal, 2)), "montage")
    nya = []
    for (tid, a, b), (na, nb, _, _) in zip(seg, avb):
        t = copy.deepcopy(next(x for x in tg if x["id"] == tid))
        t.update(fran=na, till=nb, langd=round(nb - na, 3), fran_original=[round(a, 3), round(b, 3)])
        nya.append(t)
    n["tagningar"] = nya
    n["kalla"] = dict(n["kalla"], langd=round(t0, 3))
    return _resultat("utford", f"{L:.1f} s blev {t0:.1f} s. Strukna tagningar: {', '.join(strukna) or 'inga'}; "
                               f"tal, krok (första) och avslut (sista) rördes inte."
                               + (" Musiken löper obruten under." if harmusik else ""), "montage", n, ut,
                     dict(tid=[[0, L]], box=None, ljud=True, video=True, tidsavbildning=avb, strukna=strukna),
                     ["ffmpeg trim/concat/atrim/amix/afade"] + (["demucs-stam (separation av originalets ljud)"] if harmusik else []))
