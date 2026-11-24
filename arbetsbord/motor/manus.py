"""Live K6-inspelningsmanus ur aktuellt arbetsbordstillstånd (`huvud`, `scener`, `md`)."""
from __future__ import annotations

from typing import Any

_POS_TEXT = {"ovre": "överst", "mitt": "i mitten", "nedre": "nederst"}


def _stil_sammanfattning(stil: dict[str, Any] | None) -> str:
    st = stil or {}
    delar = []
    if st.get("glyffarg"):
        delar.append(f"färg {st['glyffarg']}")
    if st.get("platta"):
        delar.append(f"platta {st.get('bakgrund') or ''}".strip())
    elif st.get("kontur"):
        delar.append("kontur")
    if st.get("position"):
        delar.append(_POS_TEXT.get(st["position"], st["position"]))
    return ", ".join(delar) or "standardstil"


def bygg_manus(tillstand: dict[str, Any]) -> dict[str, Any]:
    """Genererar live K6-inspelningsmanus ur tillståndet i NY tidslinje."""
    klipp = tillstand["klipp"]
    media = tillstand["media"]
    tagningar = tillstand["tagningar"]
    andringar = tillstand.get("andringar") or []
    tidal_waves = tillstand.get("tidal_waves") or []
    miljo = tillstand.get("miljo_tema") or {}
    kund = tillstand.get("kund")
    fk = tillstand.get("formatkort") or {}

    tal_seg = media.get("tal") or []
    skarm_lista = media.get("skarmtext") or []
    scen_obj = (tillstand.get("scen") or {}).get("objekt") or []
    extra_obj = [o for o in scen_obj if str(o.get("id", "")).startswith(("prop_", "miljo_"))]

    andring_per_tagn: dict[str, list[str]] = {}
    globala_andringar: list[str] = []
    for a in andringar:
        p = a.get("params") or {}
        tid = p.get("tagning_id")
        if tid and tid != "alla":
            andring_per_tagn.setdefault(tid, []).append(a["beskrivning"])
        elif a.get("op") in ("byt_miljo", "ljud_musik", "objekt_lagg_till", "objekt_byt", "objekt_ta_bort"):
            globala_andringar.append(a["beskrivning"])

    scener: list[dict[str, Any]] = []
    aktiva_nr = 0
    for tg in tagningar:
        sid = tg["id"]
        if tg.get("stryk") or tg.get("ny_fran_s") is None:
            scener.append(
                {
                    "nr": tg["nr"],
                    "id": sid,
                    "stryk": True,
                    "fran": None,
                    "till": None,
                    "fran_s": None,
                    "till_s": None,
                    "langd": 0.0,
                    "langd_s": 0.0,
                    "orig_tid": f"{tg['orig_fran_s']:.2f}–{tg['orig_till_s']:.2f} s",
                    "vem": ", ".join(tg.get("personer") or []) or "ingen person",
                    "var": miljo.get("namn", "Original"),
                    "sags": None,
                    "vad_sags": None,
                    "replik_ny": tg.get("replik_ny"),
                    "kansla": tg.get("kansla"),
                    "anteckning": tg.get("anteckning"),
                    "skarmtext": [],
                    "hur": [tg.get("kamera_typ", "statisk"), f"{tg.get('lins_mm') or '–'} mm"],
                    "kamera": f"{tg.get('kamera_typ', 'statisk')} · {tg.get('lins_mm') or '–'} mm",
                    "andrat": ["STRUKEN ur sekvensen"] + andring_per_tagn.get(sid, []),
                    "instruktion": f"Tagning {sid} är struken.",
                }
            )
            continue

        aktiva_nr += 1
        a_s = float(tg["ny_fran_s"])
        b_s = float(tg["ny_till_s"])
        dur = round(b_s - a_s, 2)

        rep_i_scen = [s for s in tal_seg if min(b_s, s["till_s"]) - max(a_s, s["fran_s"]) > 0.12]
        tx_i_scen = [
            x
            for x in skarm_lista
            if (x.get("typ") != "scen" or x.get("andrad") or x.get("ny"))
            and min(b_s, x["till_s"]) - max(a_s, x["fran_s"]) > 0.12
        ]
        vad_sags = " ".join(s["text"] for s in rep_i_scen).strip() or None
        tx_rader = [
            f'"{x["text"]}" ({_stil_sammanfattning(x.get("stil"))}, {max(a_s, x["fran_s"]):.1f}–{min(b_s, x["till_s"]):.1f} s)'
            for x in tx_i_scen
        ]

        pers_lista = tg.get("personer") or []
        vem = ", ".join(pers_lista) if pers_lista else "miljö/detalj utan person"
        var_plats = miljo.get("namn", "Original")
        synl_props = [o.get("etikett") or o.get("typ") for o in extra_obj if o.get("typ") not in ("golv", "vagg")]
        if synl_props:
            var_plats += f" (rekvisita: {', '.join(synl_props[:3])})"

        hur_delar = [tg.get("kamera_typ") or "statisk"]
        if tg.get("lins_mm"):
            hur_delar.append(f"{tg['lins_mm']} mm")
        if abs(float(tg.get("tempo", 1.0)) - 1.0) > 0.02:
            hur_delar.append(f"tempo {tg['tempo']:.2f}×")
        if float(tg.get("paus_slut_s", 0.0)) > 0.05:
            hur_delar.append(f"+{tg['paus_slut_s']:.1f} s slutpaus")
        hur = " · ".join(hur_delar)

        andrat = list(andring_per_tagn.get(sid, []))
        orig_dur = round(tg["orig_till_s"] - tg["orig_fran_s"], 2)
        if abs(dur - orig_dur) > 0.08:
            andrat.append(f"Tid ändrad: {orig_dur:.2f} s → {dur:.2f} s")
        if tg.get("replik_ny"):
            andrat.append(f"Ny replik för inspelning: \"{tg['replik_ny']}\"")
        if tg.get("kansla"):
            andrat.append(f"Känsla/ton: {tg['kansla']}")
        if tg.get("anteckning"):
            andrat.append(f"Regianteckning: {tg['anteckning']}")
        for x in tx_i_scen:
            if x.get("andrad"):
                andrat.append(f"Text ändrad: \"{x.get('text_original', '')}\" → \"{x['text']}\"")
            elif x.get("ny"):
                andrat.append(f"Ny skärmtext: \"{x['text']}\"")

        replik_att_saga = tg.get("replik_ny") or vad_sags
        instr = f"Filma {vem} i {var_plats} ({hur}, {dur:.1f} s)."
        if replik_att_saga:
            instr += f' Säg: "{replik_att_saga}".'
        if tx_i_scen:
            instr += " Skärmtext: " + "; ".join(f'"{x["text"]}"' for x in tx_i_scen) + "."
        if tg.get("anteckning"):
            instr += f" OBS: {tg['anteckning']}."

        scener.append(
            {
                "nr": tg["nr"],
                "aktiv_nr": aktiva_nr,
                "id": sid,
                "stryk": False,
                "funktion": tg.get("funktion"),
                "fran": round(a_s, 2),
                "till": round(b_s, 2),
                "fran_s": round(a_s, 2),
                "till_s": round(b_s, 2),
                "langd": dur,
                "langd_s": dur,
                "orig_tid": f"{tg['orig_fran_s']:.2f}–{tg['orig_till_s']:.2f} s",
                "vem": vem,
                "var": var_plats,
                "sags": vad_sags,
                "vad_sags": vad_sags,
                "replik_ny": tg.get("replik_ny"),
                "kansla": tg.get("kansla"),
                "anteckning": tg.get("anteckning"),
                "skarmtext": tx_rader,
                "hur": hur_delar,
                "kamera": hur,
                "andrat": andrat,
                "instruktion": instr,
                "k5_bar": tg.get("k5_bar") or [],
            }
        )

    ljud_txt = {
        "original": "Original (tal + ev. musik)",
        "tal": "Endast tal (musik dämpad)",
        "tyst": "Tyst (inspelning utan ljudspår / lägg på i efterhand)",
    }.get(media.get("ljud_lage", "original"), "Original")

    huvud = {
        "klipp": klipp["id"],
        "namn": klipp["namn"],
        "kund": (kund or {}).get("konto"),
        "langd": klipp["langd_s"],
        "langd_s": klipp["langd_s"],
        "langd_orig_s": klipp["langd_orig_s"],
        "scener": aktiva_nr,
        "antal_scener_aktiva": aktiva_nr,
        "antal_scener_totalt": len(tagningar),
        "miljo": miljo.get("namn", "Original"),
        "musik": ljud_txt,
        "ljud": ljud_txt,
        "avsikt": tillstand.get("avsikt") or "",
        "karna_kort": fk.get("karna"),
        "handling_kort": fk.get("handling"),
        "karna": fk.get("karna"),
        "handling": fk.get("handling"),
        "tidal_waves": tidal_waves,
        "globala_andringar": globala_andringar,
    }

    md: list[str] = [
        f"# Inspelningsmanus (K6): {klipp['namn']}",
        "",
        f"- **Längd:** {klipp['langd_s']:.2f} s (original {klipp['langd_orig_s']:.2f} s) · **Tagningar:** {aktiva_nr}/{len(tagningar)} aktiva",
        f"- **Miljö:** {huvud['miljo']} · **Ljud:** {ljud_txt}"
        + (f" · **Kund:** @{huvud['kund']}" if huvud["kund"] else ""),
    ]
    if huvud["avsikt"]:
        md.append(f"- **Avsikt:** {huvud['avsikt']}")
    if fk.get("karna"):
        md.append(f"- **Kärna [formatkort]:** {fk['karna']}")
    if tidal_waves:
        md += ["", "## Varför & Tidal waves i sekvensen", ""]
        for tw in tidal_waves:
            md.append(f"- {tw}")
    if globala_andringar:
        md += ["", "## Övergripande ändringar", ""]
        for g in globala_andringar:
            md.append(f"- {g}")

    md += [
        "",
        "## Scenblad",
        "",
        "| # | Tid | Vem | Var | Vad sägs / Ny replik | Skärmtext | Kamera & utsnitt | Ändringar |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for sc in scener:
        if sc["stryk"]:
            md.append(f"| {sc['nr']} ({sc['id']}) | STRUKEN | {sc['vem']} | – | – | – | – | {'; '.join(sc['andrat'])} |")
            continue
        rep_vis = f"**NY:** {sc['replik_ny']}" if sc.get("replik_ny") else (sc["vad_sags"] or "–")
        tx_vis = "; ".join(sc["skarmtext"]) or "–"
        andr_vis = "; ".join(sc["andrat"]) or "–"
        md.append(
            f"| {sc['nr']} ({sc['id']}) | {sc['fran_s']:.2f}–{sc['till_s']:.2f} s ({sc['langd_s']:.1f} s) "
            f"| {sc['vem']} | {sc['var']} | {rep_vis.replace('|', '/')} | {tx_vis.replace('|', '/')} "
            f"| {sc['kamera']} | {andr_vis.replace('|', '/')} |"
        )

    md += ["", "## Att spela in, scen för scen", ""]
    for sc in scener:
        prefix = f"{sc['nr']}. [{sc['id']}]"
        if sc["stryk"]:
            md.append(f"{prefix} ~~Struken tagning~~")
        else:
            rad = f"{prefix} ({sc['fran_s']:.2f}–{sc['till_s']:.2f} s) {sc['instruktion']}"
            if sc["andrat"]:
                rad += " **[" + "; ".join(sc["andrat"]) + "]**"
            md.append(rad)

    return {
        "huvud": huvud,
        "scener": scener,
        "md": "\n".join(md) + "\n",
    }
