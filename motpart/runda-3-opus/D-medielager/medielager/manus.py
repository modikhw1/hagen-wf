# -*- coding: utf-8 -*-
"""Manus per scen (K6): vem, var, vad som sägs, hur och hur länge. Ur medielagren plus befintlig ryggrad.

En scen = en tagning i tidslinjen. Källorna är märkta i manuset:
  [mätt]   tagningar, utsnitt, kamerarörelse, personer (YOLO), plats (CLIP-gissning), tal (KB-whisper), text (OCR)
  [kort]   formatkortets handling, kärna och takter (Gemini, ur byggsten/hand/ut/klipp.jsonl, otidsatta)
  [ändrat] det CM:s ändring har gjort (byt_text, ta_bort_musik, byt_matbild, korta_montage ...)
Ingen modell skriver manuset; det är mallar över lagren. Repliker skrivs inte om (det gör kunden eller CM).

    from medielager.manus import manus
    m = manus(tidslinje)          # dict med scener
    md = manus_md(m)              # text att läsa
"""
import json

KLASS = {"mat": "matbild utan person", "person_med_mat": "person med mat i bild", "person": "person",
         "miljo": "miljö utan person", "text": "textplatta eller skärmbild"}
POS = {"ovre": "överst", "mitt": "i mitten", "nedre": "nederst"}


def _stiltext(st):
    st = st or {}
    farg = st.get("glyffarg") or "?"
    delar = [("ljus" if st.get("ljus_text") else "mörk") + f" text ({farg})"]
    if st.get("platta"):
        delar.append(f"på platta ({st.get('bakgrund')})")
    elif st.get("kontur"):
        delar.append("med kontur")
    if st.get("versaler"):
        delar.append("versaler")
    delar.append(POS.get(st.get("position"), ""))
    return ", ".join(d for d in delar if d)


def manus(tl):
    an = tl.get("andring") or {}
    kort = (tl.get("andra_lasare") or {}).get("l4") or {}
    l2 = (tl.get("andra_lasare") or {}).get("l2") or {}
    tal = tl.get("tal", {}).get("segment", [])
    text = {x["id"]: x for x in tl.get("skarmtext", [])}
    musik = tl.get("musik") or {}
    scener = []
    for i, tg in enumerate(tl["tagningar"], 1):
        a, b = tg["fran"], tg["till"]
        oa = (tg.get("fran_original") or [a, b])[0]
        ob = (tg.get("fran_original") or [a, b])[1]
        rep = [s for s in tal if min(ob, s["till"]) - max(oa, s["fran"]) > 0.2]
        tx = [x for x in tl.get("skarmtext", []) if x.get("typ") == "overlag"
              and min(ob, x["till"]) - max(oa, x["fran"]) > 0.2]
        pers = tg.get("personer") or {}
        n = pers.get("antal", 0)
        vem = "ingen person" if n == 0 else (f"{n} person" + ("er" if n > 1 else ""))
        if tg.get("klass") in ("mat", "person_med_mat"):
            vem += ", maten i fokus"
        var = (tg.get("plats") or {}).get("gissning")
        hur = []
        if tg.get("utsnitt"):
            hur.append(tg["utsnitt"])
        elif tg.get("klass") == "mat":
            hur.append("närbild på maten")
        hur.append("stilla kamera" if tg.get("still") else "rörlig kamera eller mycket rörelse i bild")
        hur.append(KLASS.get(tg.get("klass"), tg.get("klass") or "?"))
        andrat = []
        if an.get("op") == "byt_matbild" and tg.get("utbytt"):
            u = tg["utbytt"]
            andrat.append(f"BILDEN BYTS: använd kundens egen tagning ({u['klipp']}, {u['tagning']}) i stället")
        for x in tx:
            if x.get("andrad"):
                andrat.append(f"NY TEXT: \"{x['text']}\" (i stället för \"{x.get('text_original')}\")")
        if an.get("op") == "korta_montage" and tg.get("fran_original"):
            fo = tg["fran_original"]
            if abs((fo[1] - fo[0]) - (b - a)) > 0.05:
                andrat.append(f"KORTAD: {fo[1] - fo[0]:.1f} s → {b - a:.1f} s")
        sagt = " ".join(s["text"] for s in rep).strip()
        textrader = [f"\"{x['text']}\" ({_stiltext(x.get('stil'))}, {max(oa, x['fran']) - oa:.1f}–{min(ob, x['till']) - oa:.1f} s in i scenen)"
                     for x in tx]
        instr = f"Filma {hur[0] if tg.get('utsnitt') or tg.get('klass') == 'mat' else 'bild'} av {vem}"
        if var:
            instr += f" i/vid {var}"
        instr += f", {hur[1]}. Cirka {b - a:.1f} s."
        if sagt:
            instr += f" Säg: \"{sagt}\"."
        if textrader:
            instr += " Text på skärmen: " + "; ".join(f"\"{x['text']}\"" for x in tx) + "."
        scener.append(dict(nr=i, id=tg["id"], fran=round(a, 2), till=round(b, 2), langd=round(b - a, 2),
                           vem=vem, var=var, var_p=(tg.get("plats") or {}).get("p"),
                           sags=sagt or None, skarmtext=textrader, hur=hur, andrat=andrat, instruktion=instr,
                           nyckelruta=tg.get("nyckelruta")))
    huvud = dict(
        klipp=tl["klipp"], langd=round(tl["kalla"]["langd"], 1), scener=len(scener),
        typ=l2.get("typ"), innehall_kort=l2.get("innehall"), handling_kort=kort.get("handling"),
        karna_kort=kort.get("karna"),
        takter_kort=[f"{t.get('funktion')}: {t.get('vad')}" for t in kort.get("beats") or []],
        musik=("ingen (borttagen)" if (tl.get("musik") or {}).get("borttagen") else
               ("musik under" if musik.get("finns") else "ingen musik hittad")),
        sprak=tl.get("tal", {}).get("sprak"), andring=an.get("op"), andring_param=an.get("parametrar"))
    return dict(huvud=huvud, scener=scener)


def manus_md(m, utan_scen=None):
    h = m["huvud"]
    L = [f"# Manus: {h['klipp']}" + (f" (ändring: {h['andring']})" if h.get("andring") else ""), "",
         f"Längd {h['langd']} s, {h['scener']} scener. Ljud: {h['musik']}. Språk i tal: {h['sprak']}.", ""]
    if h.get("handling_kort") or h.get("innehall_kort"):
        L += [f"**Idén [kort]:** {h.get('karna_kort') or h.get('innehall_kort')}", ""]
    if h.get("takter_kort"):
        L += ["**Takter [kort, otidsatta]:** " + " · ".join(h["takter_kort"]), ""]
    L += ["| # | tid | vem [mätt] | var [mätt, gissning] | vad sägs [mätt] | text på skärmen [mätt] | hur [mätt] | ändrat |",
          "|---|---|---|---|---|---|---|---|"]
    for s in m["scener"]:
        if utan_scen and s["nr"] == utan_scen:
            L.append(f"| {s['nr']} | {s['fran']}–{s['till']} s |  |  |  |  |  |  |")
            continue
        L.append(f"| {s['nr']} | {s['fran']}–{s['till']} s ({s['langd']} s) | {s['vem']} | {s['var'] or '–'} | "
                 f"{(s['sags'] or '–')[:220]} | {'; '.join(s['skarmtext']) or '–'} | {', '.join(s['hur'])} | "
                 f"{'; '.join(s['andrat']) or '–'} |")
    L += ["", "## Att spela in, scen för scen", ""]
    for s in m["scener"]:
        if utan_scen and s["nr"] == utan_scen:
            L.append(f"{s['nr']}. ")
            continue
        L.append(f"{s['nr']}. {s['instruktion']}" + (" **" + "; ".join(s["andrat"]) + "**" if s["andrat"] else ""))
    return "\n".join(L) + "\n"


FRAGOR = ["Vem syns i scenen?", "Var spelas scenen in?", "Vad sägs, eller vad står det på skärmen?",
          "Hur filmas scenen (avstånd, stilla eller rörlig kamera)?", "Hur länge är scenen (sekunder)?"]


def provformular(poster, ut_html, nyckel_fil):
    """poster: [{etikett, manus_md, manus(dict), forhandsvisning (relativ sökväg från html), larm_scen}]"""
    data = [dict(etikett=p["etikett"], manus_md=p["manus_md"], video=p.get("video"),
                 scener=[dict(nr=s["nr"], tid=f"{s['fran']}–{s['till']} s") for s in p["manus"]["scener"]])
            for p in poster]
    nyckel = [dict(etikett=p["etikett"], klipp=p["manus"]["huvud"]["klipp"], andring=p["manus"]["huvud"].get("andring"),
                   larm_scen=p.get("larm_scen")) for p in poster]
    nyckel_fil.write_text(json.dumps(nyckel, ensure_ascii=False, indent=1), encoding="utf-8")
    html = PROV_HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace(
        "__FRAGOR__", json.dumps(FRAGOR, ensure_ascii=False))
    ut_html.write_text(html, encoding="utf-8")


PROV_HTML = r"""<!doctype html>
<html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Manusprov K6</title>
<style>
:root{--bg:#fafaf8;--fg:#1d1d1b;--mut:#6b6b66;--kant:#d9d8d2;--acc:#2f5d8a}
@media (prefers-color-scheme:dark){:root{--bg:#1b1b1a;--fg:#ecebe6;--mut:#a3a29c;--kant:#3a3a37;--acc:#8db4dc}}
body{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;margin:0;padding:16px;max-width:1100px}
h1{font-size:20px}h2{font-size:17px;margin-top:28px;border-top:1px solid var(--kant);padding-top:14px}
pre{white-space:pre-wrap;background:transparent;border:1px solid var(--kant);padding:10px;font-size:13px;overflow-x:auto}
table{border-collapse:collapse;width:100%}td,th{border:1px solid var(--kant);padding:4px;vertical-align:top;font-size:13px}
textarea{width:100%;min-height:34px;font:inherit;background:transparent;color:inherit;border:1px solid var(--kant)}
.facit{display:none}.agare .facit{display:table-cell}.mut{color:var(--mut)}button{font:inherit;padding:6px 12px}
video{max-width:280px;width:100%}
</style></head><body>
<h1>Manusprov (K6)</h1>
<p class="mut">För en person som inte har sett originalet. Läs manuset, titta på förhandsvisningen och svara på fem frågor per scen.
Ägaren fyller i facit i ägarläget och markerar rätt eller fel. Svaren sparas bara när du trycker <b>Ladda ner svar</b>.</p>
<label><input type="checkbox" id="agare"> Ägarläge (visar facit och rätt/fel)</label>
<label style="margin-left:16px">Ditt namn: <input id="namn"></label>
<div id="rot"></div>
<p><button id="ladda">Ladda ner svar</button></p>
<script>
const DATA=__DATA__, FR=__FRAGOR__;
const rot=document.getElementById('rot');
DATA.forEach((p,pi)=>{
  const s=document.createElement('section');
  let h=`<h2>${p.etikett}</h2>`;
  if(p.video) h+=`<p><video controls preload="none" src="${p.video}"></video></p>`;
  h+=`<details><summary>Manus</summary><pre>${p.manus_md.replace(/</g,'&lt;')}</pre></details>`;
  h+='<table><tr><th>scen</th><th>fråga</th><th>svar</th><th class="facit">facit (ägaren)</th><th class="facit">rätt?</th></tr>';
  p.scener.forEach(sc=>FR.forEach((f,fi)=>{
    const k=`${pi}|${sc.nr}|${fi}`;
    h+=`<tr><td>${fi?'':sc.nr+' ('+sc.tid+')'}</td><td>${f}</td><td><textarea data-k="s|${k}"></textarea></td>`+
       `<td class="facit"><textarea data-k="f|${k}"></textarea></td><td class="facit"><select data-k="r|${k}"><option></option><option>rätt</option><option>fel</option></select></td></tr>`;
  }));
  s.innerHTML=h+'</table>'; rot.appendChild(s);
});
document.getElementById('agare').onchange=e=>document.body.classList.toggle('agare',e.target.checked);
document.getElementById('ladda').onclick=()=>{
  const ut={namn:document.getElementById('namn').value,tid:new Date().toISOString(),svar:{}};
  document.querySelectorAll('[data-k]').forEach(el=>{if(el.value)ut.svar[el.dataset.k]=el.value});
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(ut,null,1)],{type:'application/json'}));
  a.download='k6-svar.json';a.click();
};
</script></body></html>
"""
