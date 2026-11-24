"""Smart Kontext-LLM för regibordet (ingen Jev): läser full klippkontext, resonerar om tidal waves & K5, och kör säkra operationer."""
from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from .k7_vakt import K7StoppError, kontrollera_cm_text, kontrollera_operation, logga_k7
from .operationer import pop_undo, push_undo, utfor_operation
from .schema import ENV_LOCAL, MILJO_TEMAN, UT_DIR, kompilera_tillstand

_PARAMS_PROPS: dict[str, Any] = {
    "tema": {"type": "string"},
    "tagningar": {"type": "array", "items": {"type": "string"}},
    "tagning_id": {"type": "string"},
    "zoom": {"type": "number"},
    "pan_deg": {"type": "number"},
    "tilt_deg": {"type": "number"},
    "stabilisera": {"type": "boolean"},
    "handhallen_energi": {"type": "number"},
    "typ": {"type": "string"},
    "etikett": {"type": "string"},
    "farg": {"type": "string"},
    "pos": {"type": "array", "items": {"type": "number"}},
    "matt": {"type": "array", "items": {"type": "number"}},
    "nara": {"type": "string"},
    "id": {"type": "string"},
    "dx": {"type": "number"},
    "dy": {"type": "number"},
    "dz": {"type": "number"},
    "vrid_deg": {"type": "number"},
    "person_id": {"type": "string"},
    "flytta_med_kamera": {"type": "boolean"},
    "fran_s": {"type": "number"},
    "till_s": {"type": "number"},
    "ny_langd_s": {"type": "number"},
    "aterstall": {"type": "boolean"},
    "tempo": {"type": "number"},
    "sekunder": {"type": "number"},
    "text": {"type": "string"},
    "position": {"type": "string"},
    "lage": {"type": "string"},
    "replik_ny": {"type": "string"},
    "kansla": {"type": "string"},
}

BEACON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "tolkning",
        "tidal_waves",
        "arver_1till1",
        "k5_varning",
        "kropp_behov",
        "operationer",
        "svar_till_cm",
    ],
    "properties": {
        "tolkning": {"type": "string"},
        "tidal_waves": {"type": "array", "items": {"type": "string"}},
        "arver_1till1": {"type": "array", "items": {"type": "string"}},
        "k5_varning": {
            "type": "object",
            "required": ["niva", "text"],
            "properties": {
                "niva": {"type": "string", "enum": ["ingen", "info", "varning", "stopp"]},
                "text": {"type": "string"},
            },
        },
        "kropp_behov": {"type": "string"},
        "operationer": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["op", "params"],
                "properties": {
                    "op": {"type": "string"},
                    "params": {"type": "object", "properties": _PARAMS_PROPS},
                },
            },
        },
        "svar_till_cm": {"type": "string"},
    },
}

CODEX_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "tolkning",
        "tidal_waves",
        "arver_1till1",
        "k5_varning",
        "kropp_behov",
        "operationer",
        "svar_till_cm",
    ],
    "properties": {
        "tolkning": {"type": "string"},
        "tidal_waves": {"type": "array", "items": {"type": "string"}},
        "arver_1till1": {"type": "array", "items": {"type": "string"}},
        "k5_varning": {
            "type": "object",
            "additionalProperties": False,
            "required": ["niva", "text"],
            "properties": {
                "niva": {"type": "string", "enum": ["ingen", "info", "varning", "stopp"]},
                "text": {"type": "string"},
            },
        },
        "kropp_behov": {"type": "string"},
        "operationer": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["op", "params_json"],
                "properties": {
                    "op": {"type": "string"},
                    "params_json": {"type": "string"},
                },
            },
        },
        "svar_till_cm": {"type": "string"},
    },
}

SYSTEM_INSTRUKTION = """Du är Smart Kontext-LLM i ett regibord för en restaurang- och kafébyrå.
CM laddar in ett referensklipp (med 1:1-bevarad kamera, kamerarörelse, klipprytm, kroppsrörelse/hållning och ljudsynk) och ger regi i naturligt språk för att forma om scenen åt en kund.

Dina regler:
1. ÄRV 1:1: Kamera, kamerarörelse, klipprytm, kroppshållning och ljudsynk ärvs som grund. Byt fyllningen (miljötema, 3D-rekvisita/block, skärmtext, ljus, subtil kamerajustering, ljudläge, pacing/tidslinje, manusanteckningar/repliker).
2. K7-SPÄRR (OBRYTBAR): Noll generativ bild/video/röst och noll spegling (`byt_hand`). Om CM ber om det: lämna `operationer` tom, sätt `k5_varning.niva="stopp"` och förklara K7-spärren.
3. TIDAL WAVES: Tänk på följdverkningar över hela sekvensen! Om du t.ex. flyttar scenen till ett kafé eller en kunds pizzeria:
   - byt miljötema (`byt_miljo`) OCH anpassa skärmtext (`skarmtext_byt`) eller lägg till skylt/prop (`objekt_lagg_till`) och/eller manusanteckning (`manus_anteckning`) där följdverkningar uppstår.
4. K5-KONTROLL: Kontrollera om en ändring skadar någon bärande post (`roll="bar"`) i K5-bärlistan. Varna ärligt i `k5_varning` om bärande tagning/text/ljud påverkas.
5. KROPPSBEHOV: Ange kort i `kropp_behov` om skådespelaren behöver någon ny hantering/rörelse vid inspelning (t.ex. "behåller exakt sittande hållning men tar emot espressokopp" eller "inga nya kroppskrav").
6. Håll antalet operationer koncist och träffsäkert (vanligen 1–5 operationer). Använd ENDAST tillåtna operationsnamn nedan och inkludera ENDAST parametrarna som operationen använder (utelämna oanvända fält som `zoom`/`vrid_deg`).
7. VIKTIGT för `objekt_lagg_till` med `typ="skylt"` eller rekvisita: sätt alltid `etikett` till den korta texten som ska synas på 3D-skylten/rekvisitan (t.ex. `etikett: "KAPPABAR KÖK"`).

Tillåtna operationer (op + params):
- `byt_miljo`: {tema: "original"|"kok"|"bar"|"uteservering"|"kafe"|"foodtruck"|"matsal", tagningar?: [tagnings_id]}
- `kamera_justera`: {tagning_id: "s1"|"alla", zoom?: nummer (>1 tätare, t.ex. 1.15), pan_deg?: nummer, tilt_deg?: nummer, stabilisera?: bool, handhallen_energi?: 0.0-1.0}
- `objekt_lagg_till`: {typ: "kaffemaskin"|"spis"|"disk"|"bank"|"skylt"|"hylla"|"parasoll"|"lampa"|"prop", etikett: str (obligatorisk för skylt!), farg?: "#hex", nara?: person_id|objekt_id, tagningar?: [tagnings_id]}
- `objekt_byt`: {id: objekt_id, typ?: str, etikett?: str, farg?: "#hex"}
- `objekt_ta_bort`: {id: objekt_id}
- `objekt_flytta`: {id: objekt_id, dx: meter, dy: meter, dz: meter, vrid_deg?: grader}
- `person_placering`: {person_id: "A"|"B"|..., tagning_id?: id|"alla", dx: meter, dy: meter, dz: meter, vrid_deg?: grader, flytta_med_kamera?: bool}
- `tidslinje_korta`: {tagning_id: id, fran_s?: nummer, till_s?: nummer, ny_langd_s?: nummer}
- `tidslinje_stryk`: {tagning_id: id, aterstall?: bool}
- `tidslinje_tempo`: {tagning_id: id|"alla", tempo: nummer (0.5-2.0)}
- `tidslinje_paus`: {tagning_id: id, sekunder: nummer (0.0-3.0)}
- `skarmtext_byt`: {id: skarmtext_id, text: str}
- `skarmtext_lagg_till`: {text: str, tagning_id?: id, fran_s?: nummer, till_s?: nummer, position?: "ovre"|"mitt"|"nedre"}
- `skarmtext_ta_bort`: {id: skarmtext_id}
- `ljud_musik`: {lage: "original"|"tal"|"tyst"}
- `manus_anteckning`: {tagning_id: id|"alla", text: str, replik_ny?: str, kansla?: str}
- `aterstall`: {}

Svara ENDAST med giltig JSON enligt schemat. Skriv på svenska."""


def _las_env() -> dict[str, str]:
    if not ENV_LOCAL.exists():
        return {}
    ut: dict[str, str] = {}
    for rad in ENV_LOCAL.read_text(encoding="utf-8").splitlines():
        s = rad.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        ut[k.strip()] = v.strip().strip('"').strip("'")
    return ut


def bygg_kontext_prompt(tillstand: dict[str, Any], cm_text: str, avsikt: str | None = None) -> str:
    """Bygger hela klippets rika kontext för Smart Kontext-LLM."""
    klipp = tillstand["klipp"]
    fk = tillstand.get("formatkort") or {}
    kund = tillstand.get("kund")
    miljo = tillstand.get("miljo_tema") or {}
    media = tillstand["media"]
    scen = tillstand.get("scen") or {}
    k5 = tillstand.get("k5") or {}

    delar = [SYSTEM_INSTRUKTION, ""]
    delar.append(
        f"KLIPP: {klipp['namn']} (id={klipp['id']}, har_3d={klipp['har_3d']}, "
        f"längd={klipp['langd_s']} s, original={klipp['langd_orig_s']} s, "
        f"{klipp['bredd']}x{klipp['hojd']}, {klipp['fps']} fps)"
    )
    delar.append(
        f"NUVARANDE LÄGE: miljötema={miljo.get('id', 'original')} ({miljo.get('namn', 'Original')}), "
        f"ljud={media.get('ljud_lage', 'original')}, musik_finns={bool((media.get('musik') or {}).get('finns'))}, "
        f"separerat_tal={bool(media.get('tal_url'))}"
    )

    if fk:
        beats_str = " | ".join(f"{b.get('funktion')}: {b.get('vad')}" for b in (fk.get("beats") or []))
        delar.append(f"FORMATKORT ({fk.get('typ')}): Kärna: {fk.get('karna')}. Handling: {fk.get('handling')}")
        if beats_str:
            delar.append(f"TAKTER: {beats_str}")

    if kund:
        delar.append(
            f"KUNDPROFIL @{kund['konto']}: {kund.get('antal_klipp', 0)} klipp, "
            f"vanliga rum={', '.join(kund.get('rum') or []) or '–'}, "
            f"produkter={', '.join((kund.get('produkter') or [])[:6]) or '–'}"
        )

    eff_avsikt = (avsikt if avsikt is not None else tillstand.get("avsikt")) or ""
    delar.append(f"CM:S AVSIKT MED PASSET: {eff_avsikt or '(ej angiven)'}")

    delar.append("\nTAGNINGAR:")
    for t in tillstand.get("tagningar", []):
        tid_str = "STRUKEN" if t.get("stryk") else f"{t['ny_fran_s']:.2f}–{t['ny_till_s']:.2f} s"
        rep_str = " / ".join(t.get("repliker") or []) or "(inget tal)"
        k5_str = ", ".join(t.get("k5_bar") or []) or "–"
        delar.append(
            f"- {t['id']} [{tid_str}, orig {t['orig_fran_s']:.2f}–{t['orig_till_s']:.2f} s, "
            f"tempo={t['tempo']}x, paus={t['paus_slut_s']} s, kamera={t['kamera_typ']} {t.get('lins_mm') or ''}mm, "
            f"personer={t.get('personer')}, funktion={t.get('funktion') or '–'}]: "
            f"tal=\"{rep_str}\" | K5_bär=[{k5_str}]"
        )

    delar.append("\nSKÄRMTEXTER:")
    skarm = [x for x in media.get("skarmtext", []) if x.get("typ") != "scen" or x.get("andrad") or x.get("ny")]
    if skarm:
        for x in skarm[:24]:
            delar.append(
                f"- id={x['id']} [{x['fran_s']:.2f}–{x['till_s']:.2f} s, pos={(x.get('stil') or {}).get('position', 'mitt')}]: \"{x['text']}\""
            )
    else:
        delar.append("- (inga)")

    if scen.get("objekt"):
        delar.append("\n3D-OBJEKT:")
        for o in scen["objekt"]:
            if o.get("typ") in ("golv", "vagg"):
                continue
            delar.append(
                f"- id={o['id']} typ={o['typ']} etikett=\"{o.get('etikett') or o['id']}\" "
                f"pos={o['pos']} matt={o['matt']} farg={o['farg']}"
            )

    bar_poster = [p for p in k5.get("poster", []) if p.get("roll") == "bar"]
    if bar_poster:
        delar.append("\nK5-BÄRLISTA (detta bär klippets mening):")
        for p in bar_poster[:18]:
            delar.append(
                f"- {p['namn']} ({p['typ']}, tagn={p.get('tagningar')}, medie={p.get('medie')}): {p.get('varfor') or ''}"
            )

    if tillstand.get("andringar"):
        delar.append("\nREDAN UTFÖRDA ÄNDRINGAR:")
        for a in tillstand["andringar"][-8:]:
            delar.append(f"- #{a['nr']} {a['op']}: {a['beskrivning']}")

    delar.append(f"\nCM SKRIVER NU:\n\"{cm_text}\"")
    return "\n".join(delar)


def _anropa_beacon(prompt: str, modell: str, env: dict[str, str]) -> tuple[dict[str, Any], int, str]:
    nyckel = env.get("BEACON_NYCKEL") or os.environ.get("BEACON_NYCKEL")
    if not nyckel:
        raise RuntimeError("BEACON_NYCKEL saknas i video/.env.local")
    url = env.get("BEACON_URL") or "https://token-budget-beacon.lovable.app/api/public/v1/generate"
    body = {
        "model": modell,
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseJsonSchema": BEACON_SCHEMA,
            "thinkingConfig": {"thinkingLevel": "low"},
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "authorization": f"Bearer {nyckel}",
            "content-type": "application/json",
        },
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=25) as resp:
        j = json.loads(resp.read().decode("utf-8"))
    ms = round((time.perf_counter() - t0) * 1000)
    parts = j["candidates"][0]["content"]["parts"]
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    return json.loads(text), ms, "beacon"


def _anropa_gemini(prompt: str, modell: str, env: dict[str, str]) -> tuple[dict[str, Any], int, str]:
    nyckel = (
        env.get("GEMINI_API_KEY_GRATIS")
        or env.get("GEMINI_API_KEY")
        or os.environ.get("GEMINI_API_KEY_GRATIS")
        or os.environ.get("GEMINI_API_KEY")
    )
    if not nyckel:
        raise RuntimeError("GEMINI_API_KEY_GRATIS / GEMINI_API_KEY saknas")
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseSchema": BEACON_SCHEMA,
            "thinkingConfig": {"thinkingLevel": "minimal"},
        },
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{modell}:generateContent",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": nyckel},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=20) as resp:
        j = json.loads(resp.read().decode("utf-8"))
    ms = round((time.perf_counter() - t0) * 1000)
    parts = j["candidates"][0]["content"]["parts"]
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    return json.loads(text), ms, "gemini"


def _anropa_codex(prompt: str) -> tuple[dict[str, Any], int, str]:
    exe = shutil.which("codex")
    if not exe:
        raise RuntimeError("codex CLI finns inte i PATH")
    log_dir = UT_DIR / "codex_tmp"
    tom = log_dir / "tom"
    tom.mkdir(parents=True, exist_ok=True)
    schema_fil = log_dir / "schema.json"
    schema_fil.write_text(json.dumps(CODEX_SCHEMA), encoding="utf-8")
    ut_fil = log_dir / f"svar_{uuid.uuid4().hex[:8]}.txt"
    t0 = time.perf_counter()
    p = subprocess.run(
        [
            exe,
            "exec",
            "-m",
            "gpt-5.6-sol",
            "-c",
            "model_reasoning_effort=low",
            "-s",
            "read-only",
            "--skip-git-repo-check",
            "--ephemeral",
            "-C",
            str(tom),
            "--output-schema",
            str(schema_fil),
            "-o",
            str(ut_fil),
            "-",
        ],
        input=prompt.encode("utf-8"),
        capture_output=True,
        timeout=120,
    )
    ms = round((time.perf_counter() - t0) * 1000)
    raw = ut_fil.read_text(encoding="utf-8") if ut_fil.exists() else ""
    if ut_fil.exists():
        ut_fil.unlink()
    if not raw.strip():
        raise RuntimeError("Codex svarade tomt: " + p.stderr.decode("utf-8", "replace")[-240:])
    svar, _ = json.JSONDecoder().raw_decode(raw[raw.index("{") :])
    # Konvertera params_json -> params
    ops = []
    for item in svar.get("operationer") or []:
        pj = item.get("params_json") or "{}"
        try:
            params = json.loads(pj)
        except Exception:
            params = {}
        ops.append({"op": item.get("op"), "params": params})
    svar["operationer"] = ops
    return svar, ms, "codex"


def _fraga_modell(prompt: str, modell_val: str) -> tuple[dict[str, Any], int, str, str]:
    """Returnerar (svar_dict, ms, via, faktisk_modell)."""
    env = _las_env()
    m = (modell_val or "gemini-3.5-flash").strip()
    fel: list[str] = []

    if m == "codex":
        svar, ms, via = _anropa_codex(prompt)
        return svar, ms, via, "gpt-5.6-sol"

    if m == "gemini-3-flash-preview":
        for fn, mod_namn in (
            (lambda: _anropa_gemini(prompt, "gemini-3-flash-preview", env), "gemini-3-flash-preview"),
            (lambda: _anropa_beacon(prompt, "gemini-3-flash-preview", env), "gemini-3-flash-preview"),
            (lambda: _anropa_beacon(prompt, "gemini-3.5-flash", env), "gemini-3.5-flash"),
        ):
            try:
                svar, ms, via = fn()
                return svar, ms, via, mod_namn
            except Exception as e:
                fel.append(f"{mod_namn}: {e}")
    else:
        for fn, mod_namn in (
            (lambda: _anropa_beacon(prompt, m, env), m),
            (lambda: _anropa_gemini(prompt, "gemini-3-flash-preview", env), "gemini-3-flash-preview"),
        ):
            try:
                svar, ms, via = fn()
                return svar, ms, via, mod_namn
            except Exception as e:
                fel.append(f"{mod_namn}: {e}")

    try:
        svar, ms, via = _anropa_codex(prompt)
        return svar, ms, via, "gpt-5.6-sol (fallback)"
    except Exception as e:
        fel.append(f"codex: {e}")

    raise RuntimeError("Alla LLM-vägar misslyckades: " + " | ".join(fel))


def regissera(
    session: dict[str, Any],
    text: str,
    avsikt: str | None = None,
    modell: str | None = None,
) -> dict[str, Any]:
    """Kör Smart Kontext-LLM, validerar K7, utför operationer i följd och loggar diff + feedback_id."""
    if avsikt is not None:
        session["avsikt"] = avsikt.strip()

    tillstand_fore = kompilera_tillstand(session)
    feedback_id = uuid.uuid4().hex[:10]
    klipp_id = session["klipp"]["id"]
    sid = session["session_id"]

    # 1. Hård K7-förkontroll på CM-texten
    k7_stopp = kontrollera_cm_text(text)
    if k7_stopp:
        logga_k7("blockerad_regi", sid, klipp_id, "regi_text", {"text": text}, ok=False, detalj=k7_stopp)
        llm_svar = {
            "tolkning": text,
            "tidal_waves": [],
            "arver_1till1": ["Kamera, rörelse, klipprytm, kropp och ljudsynk är orörda 1:1."],
            "k5_varning": {"niva": "stopp", "text": k7_stopp},
            "kropp_behov": "Inga generativa eller speglade kroppsändringar tillåts.",
            "operationer": [],
            "svar_till_cm": k7_stopp,
            "modell": "k7_vakt",
            "via": "k7_sparr",
            "ms": 0,
        }
        return {"tillstand": tillstand_fore, "llm_svar": llm_svar, "feedback_id": feedback_id}

    prompt = bygg_kontext_prompt(tillstand_fore, text, session.get("avsikt"))
    svar_raw, ms, via, faktisk_modell = _fraga_modell(prompt, modell or "gemini-3.5-flash")

    planerade = list(svar_raw.get("operationer") or [])
    utforda_logg: list[dict[str, Any]] = []
    nagot_andrat = False

    if planerade:
        push_undo(session)
        for item in planerade:
            op_namn = str(item.get("op") or "").strip()
            op_params = item.get("params") if isinstance(item.get("params"), dict) else {}
            # Filtrera bort ev. None-värden eller irrelevanta nollor från schemat
            op_params = {k: v for k, v in op_params.items() if v is not None}
            if op_namn != "kamera_justera":
                if op_params.get("zoom") == 1.0:
                    op_params.pop("zoom", None)
                if op_params.get("pan_deg") == 0.0:
                    op_params.pop("pan_deg", None)
                if op_params.get("tilt_deg") == 0.0:
                    op_params.pop("tilt_deg", None)
            if op_namn not in ("objekt_flytta", "person_placering") and op_params.get("vrid_deg") == 0.0:
                op_params.pop("vrid_deg", None)
            try:
                kontrollera_operation(op_namn, op_params)
                _, res = utfor_operation(
                    session,
                    op_namn,
                    op_params,
                    kalla="llm",
                    push_undo_snap=False,
                )
                utforda_logg.append(
                    {
                        "op": op_namn,
                        "params": op_params,
                        "ok": True,
                        "beskrivning": res["beskrivning"],
                    }
                )
                nagot_andrat = True
            except K7StoppError as exc:
                logga_k7("blockerad_llm_op", sid, klipp_id, op_namn, op_params, ok=False, detalj=str(exc))
                utforda_logg.append(
                    {
                        "op": op_namn,
                        "params": op_params,
                        "ok": False,
                        "beskrivning": "",
                        "fel": str(exc),
                    }
                )
            except Exception as exc:
                utforda_logg.append(
                    {
                        "op": op_namn,
                        "params": op_params,
                        "ok": False,
                        "beskrivning": "",
                        "fel": str(exc),
                    }
                )
        if not nagot_andrat:
            pop_undo(session)

    tidal_waves = [str(x) for x in (svar_raw.get("tidal_waves") or []) if str(x).strip()]
    if tidal_waves:
        session["tidal_waves"] = tidal_waves

    tillstand_efter = kompilera_tillstand(session)
    k5_v = svar_raw.get("k5_varning") or {"niva": "ingen", "text": ""}
    if not isinstance(k5_v, dict):
        k5_v = {"niva": "info", "text": str(k5_v)}

    llm_svar = {
        "tolkning": svar_raw.get("tolkning") or "",
        "tidal_waves": tidal_waves,
        "arver_1till1": list(svar_raw.get("arver_1till1") or []),
        "k5_varning": {
            "niva": k5_v.get("niva") or "ingen",
            "text": k5_v.get("text") or "",
        },
        "kropp_behov": svar_raw.get("kropp_behov") or "",
        "operationer": utforda_logg,
        "svar_till_cm": svar_raw.get("svar_till_cm") or "",
        "modell": faktisk_modell,
        "via": via,
        "ms": ms,
    }

    session.setdefault("feedback_history", {})[feedback_id] = {
        "tid": datetime.datetime.now().isoformat(timespec="seconds"),
        "cm_text": text,
        "avsikt": session.get("avsikt", ""),
        "llm_svar": llm_svar,
    }
    logga_k7(
        "llm_regi",
        sid,
        klipp_id,
        "regi",
        {"text": text, "modell": faktisk_modell, "via": via},
        ok=True,
        detalj=llm_svar["svar_till_cm"][:200],
        extra={"ms": ms, "antal_ops": len(utforda_logg), "feedback_id": feedback_id},
    )
    return {
        "tillstand": tillstand_efter,
        "llm_svar": llm_svar,
        "feedback_id": feedback_id,
    }
