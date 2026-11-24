"""VLM-läsning per tagning: det som djup och kropp inte ger.

Läser ljusets riktning, fönster, dörrar, rumsnycklar (vägg, golv, tak) och distinkta föremål
på bord. Ett anrop per tagning med hela tagningens video, strukturerad JSON och cache på disk.
Svaret är en observation med brus, inte en dom. Hjärnan väger den mot resten.

    scen/.venv/Scripts/python.exe byggsten/rumshypotes/las_vlm.py scen/3d/ingest/ut/notan-tagningar --ut byggsten/rumshypotes/ut/notan/vlm

Anropet går via ägarens proxy (rum_video.anropa_beacon, nyckeln i video/.env.local). Kostnaden loggas.
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import sys

ROT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "scen" / "3d" / "ingest"))

SCHEMA = {
    "type": "object",
    "properties": {
        "ljus_fran": {"type": "string",
                      "enum": ["vanster", "hoger", "bakom_kameran", "framfor_i_bild", "oklart"]},
        "ljus_x_andel": {"type": "number"},
        "fonster_x_andel": {"type": "array", "items": {"type": "number"}},
        "dorrar_x_andel": {"type": "array", "items": {"type": "number"}},
        "vagg": {"type": "string", "enum": ["vit", "beige", "gra", "mork", "tra", "tegel", "glas", "annat"]},
        "golv": {"type": "string", "enum": ["tra", "sten", "betong", "matta", "kakel", "annat", "syns_ej"]},
        "tak": {"type": "string", "enum": ["ror_och_kanaler", "slatt", "annat", "syns_ej"]},
        "foremal": {"type": "array", "items": {"type": "object", "properties": {
            "nyckel": {"type": "string"},
            "x_andel": {"type": "number"},
            "y_andel": {"type": "number"},
            "pa_bord": {"type": "boolean"},
            "distinkt": {"type": "boolean"}},
            "required": ["nyckel", "x_andel", "y_andel", "pa_bord", "distinkt"]}},
    },
    "required": ["ljus_fran", "ljus_x_andel", "fonster_x_andel", "dorrar_x_andel", "vagg", "golv", "tak", "foremal"],
}

FRAGA = """Du ser en kort tagning (stående video) inomhus. Beskriv rummet i tagningens mittersta bildruta.
Positioner anges som andel av bildens bredd (x_andel, 0 = vänster kant, 1 = höger kant) och höjd (y_andel, 0 = överkant).

- ljus_fran: varifrån huvudljuset (dagsljus eller fönster) kommer, sett från kameran.
  vanster/hoger = från kamerans vänstra/högra sida, bakom_kameran = ansikten och föremål lyses upp rakt framifrån,
  framfor_i_bild = ljuskällan syns i bild eller motljus. Säg oklart om det inte går att avgöra.
- ljus_x_andel: x_andel för ljuskällan (fönstret) om den syns i bild, annars -1.
- fonster_x_andel: x_andel för varje synligt fönster. Tom lista om inga syns.
- dorrar_x_andel: x_andel för varje synlig dörr. Tom lista om inga syns.
- vagg: färgen på de väggar som syns mest.
- golv: golvets material, eller syns_ej.
- tak: takets typ (ror_och_kanaler = synliga rör, ventilationskanaler eller installationer), eller syns_ej.
- foremal: små föremål som står på bord (burkar, muggar, flaskor, brickor). Ange mitten av föremålet.
  nyckel = märke_typ_färg med små bokstäver utan å/ä/ö, till exempel bonaqua_burk_gul eller cocacola_mugg_vit.
  distinkt = true om märke eller färg gör föremålet lätt att känna igen i en annan tagning.
  Ta inte med mat (hamburgare, pommes) eller servetter.
Svara bara med JSON enligt schemat."""


def las(ingest: pathlib.Path, ut: pathlib.Path, modell: str = "google/gemini-3.5-flash") -> dict:
    from rum_video import anropa_beacon
    ut.mkdir(parents=True, exist_ok=True)
    svar, kostnad = {}, 0.0
    for video in sorted((ingest / "klipp").glob("S*.mp4")):
        S = video.stem
        cache = ut / f"{S}.json"
        if cache.exists():
            svar[S] = json.loads(cache.read_text(encoding="utf-8"))
            continue
        v = base64.b64encode(video.read_bytes()).decode()
        body = dict(model=modell, max_tokens=4000, messages=[dict(role="user", content=[
            dict(type="text", text=FRAGA),
            dict(type="file", file=dict(file_data="data:video/mp4;base64," + v, filename=video.name))])],
            response_format=dict(type="json_schema", json_schema=dict(name="rumsvlm", strict=True, schema=SCHEMA)))
        d = anropa_beacon(body, 0.1)
        text = d["choices"][0]["message"]["content"]
        j = json.loads(text[text.find("{"):text.rfind("}") + 1])
        j["_anvandning"] = d.get("usage")
        j["_modell"] = modell
        cache.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        kostnad += float((d.get("usage") or {}).get("cost") or 0.0)
        svar[S] = j
        print(S, j["ljus_fran"], j["vagg"], j["tak"], [f["nyckel"] for f in j["foremal"]])
    print(f"kostnad denna körning: {kostnad:.4f} USD")
    return svar


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ingest")
    ap.add_argument("--ut", required=True)
    ap.add_argument("--modell", default="google/gemini-3.5-flash")
    a = ap.parse_args()
    las(pathlib.Path(a.ingest), pathlib.Path(a.ut), a.modell)
