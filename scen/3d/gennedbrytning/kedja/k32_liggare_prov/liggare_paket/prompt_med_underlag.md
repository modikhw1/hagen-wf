

You write the LEDGER (liggare) for a short vertical video clip that has been decomposed into an editable 3D "pre-world". A content manager (CM) will later change the clip with one sentence ("let her give the sample with the other hand", "make it two samples"). A fast, shallow selector picks among the edits you list here, so everything that requires understanding must be done by you, now.

GIVEN (facts from measurement and earlier steps; do not contradict them, refer to their ids):
{
 "klipp": "kennysgelato2.0-7596403003901381910",
 "tidsbas": {
  "fps_taljare": 2997,
  "fps_namnare": 100,
  "antal_rutor": 252,
  "langd_s": 8.4084,
  "regel": "Tid i sekunder på källklockan: tid_s = ruta / fps. Ruta 0 = 0,0 s. Intervall är halvöppna [start, slut)."
 },
 "personer": [
  {
   "id": "A",
   "roll": "gelato server",
   "beskrivning": "Ung kvinna med blont hår i knut, iförd svart topp och namnbricka.",
   "roll_kalla": "modellbedomd",
   "ursprung": {
    "typ": "modellbedomd",
    "modell": "gemini-3.5-flash",
    "prompt_version": "semantik-prompt/1",
    "konfidens": "hog"
   }
  }
 ],
 "scener": [
  {
   "id": "s1",
   "start_s": 0.0,
   "slut_s": 5.2052,
   "funktion": "krok",
   "syfte": "Expediten skopar upp ett ytterst litet smakprov och räcker till kunden.",
   "personer": [
    "A"
   ]
  },
  {
   "id": "s2",
   "start_s": 5.2052,
   "slut_s": 8.4084,
   "funktion": "punchline",
   "syfte": "Expediten tar en gigantisk skopa gelato till sig själv och stoppar i munnen.",
   "personer": [
    "A"
   ]
  }
 ],
 "props": [
  {
   "id": "provsked",
   "typ": "provsked",
   "etikett": "provsked",
   "stod": null,
   "deklaration": {
    "foremal": "provsked",
    "former": [
     "A:hand:provsked"
    ],
    "scener": [
     "s1"
    ],
    "pa": null,
    "i_hand": [
     {
      "scen": "s1",
      "person": "A",
      "sida": "h"
     }
    ],
    "storlek_m": [
     0.04,
     0.01,
     0.08
    ]
   }
  },
  {
   "id": "disk_A",
   "typ": "glassdisk",
   "etikett": "Glassdisk",
   "stod": null,
   "deklaration": null
  }
 ],
 "skarmtext": [
  {
   "id": "st1",
   "scen": "s1",
   "text": "Smakproverna vi ger\nkunder",
   "start_s": 0.0,
   "slut_s": 4.2042042042042045
  },
  {
   "id": "st2",
   "scen": "s1",
   "text": "Vs",
   "start_s": 3.4367701034367704,
   "slut_s": 5.205205205205205
  },
  {
   "id": "st3",
   "scen": "s2",
   "text": "Smakproverna vi ger oss\nsjälv 😅",
   "start_s": 5.505505505505505,
   "slut_s": 8.375041708375042
  }
 ],
 "handlingsspar": [
  {
   "scen": "s1",
   "segment": [
    {
     "id": "h1",
     "vem": "A",
     "rutor": [
      7,
      15
     ],
     "tid_s": [
      0.2336,
      0.5005
     ],
     "hallning": "lutar_sig",
     "handling": "luta_sig",
     "kroppsdel": "overkroppen",
     "foremal": "A:hand:provsked",
     "i_handen": null,
     "mal": "disk_A",
     "blick": null,
     "kontakt": null,
     "beskrivning": "Person A leans over the display counter."
    },
    {
     "id": "h2",
     "vem": "A",
     "rutor": [
      15,
      28
     ],
     "tid_s": [
      0.5005,
      0.9343
     ],
     "hallning": "lutar_sig",
     "handling": "luta_sig",
     "kroppsdel": "overkroppen",
     "foremal": "A:hand:provsked",
     "i_handen": null,
     "mal": "disk_A",
     "blick": null,
     "kontakt": null,
     "beskrivning": "Person A leans over the counter with a spoon in her hand."
    },
    {
     "id": "h3",
     "vem": "A",
     "rutor": [
      28,
      66
     ],
     "tid_s": [
      0.9343,
      2.2022
     ],
     "hallning": "lutar_sig",
     "handling": "ta",
     "kroppsdel": "hogra_armen",
     "foremal": "A:hand:provsked",
     "i_handen": null,
     "mal": "disk_A",
     "blick": null,
     "kontakt": "A:hand:provsked>disk_A",
     "beskrivning": "Person A scoops ice cream from the display counter with a spoon."
    },
    {
     "id": "h4",
     "vem": "A",
     "rutor": [
      66,
      84
     ],
     "tid_s": [
      2.2022,
      2.8028
     ],
     "hallning": "rater_pa_sig",
     "handling": "rata_pa_sig",
     "kroppsdel": "hela_kroppen",
     "foremal": "A:hand:provsked",
     "i_handen": null,
     "mal": null,
     "blick": null,
     "kontakt": null,
     "beskrivning": "Person A straightens up while holding a spoon with ice cream."
    },
    {
     "id": "h5",
     "vem": "A",
     "rutor": [
      84,
      90
     ],
     "tid_s": [
      2.8028,
      3.003
     ],
     "hallning": "upprat",
     "handling": "sta",
     "kroppsdel": "hela_kroppen",
     "foremal": "A:hand:provsked",
     "i_handen": null,
     "mal": "kamera",
     "blick": null,
     "kontakt": null,
     "beskrivning": "Person A stands upright, holding a spoon with ice cream and looking towards the camera."
    },
    {
     "id": "h6",
     "vem": "A",
     "rutor": [
      90,
      102
     ],
     "tid_s": [
      3.003,
      3.4034
     ],
     "hallning": "upprat",
     "handling": "racka",
     "kroppsdel": "hogra_armen",
     "foremal": "A:hand:provsked",
     "i_handen": null,
     "mal": "kund",
     "blick": null,
     "kontakt": null,
     "beskrivning": "Person A extends her arm, offering a spoon with ice cream."
    },
    {
     "id": "h7",
     "vem": "A",
     "rutor": [
      102,
      116
     ],
     "tid_s": [
      3.4034,
      3.8705
     ],
     "hallning": "upprat",
     "handling": "halla",
     "kroppsdel": "hogra_armen",
     "foremal": "A:hand:provsked",
     "i_handen": null,
     "mal": "kund",
     "blick": null,
     "kontakt": null,
     "beskrivning": "Person A holds out a spoon with ice cream."
    },
    {
     "id": "h8",
     "vem": "A",
     "rutor": [
      116,
      146
     ],
     "tid_s": [
      3.8705,
      4.8715
     ],
     "hallning": "upprat",
     "handling": "racka",
     "kroppsdel": "hogra_armen",
     "foremal": "A:hand:provsked",
     "i_handen": null,
     "mal": "kund",
     "blick": null,
     "kontakt": "kund:hand>A:hand:provsked",
     "beskrivning": "Person A offers the spoon with ice cream, and a customer's hand takes it."
    },
    {
     "id": "h9",
     "vem": "A",
     "rutor": [
      146,
      155
     ],
     "tid_s": [
      4.8715,
      5.1718
     ],
     "hallning": "lutar_sig",
     "handling": "luta_sig",
     "kroppsdel": "hela_kroppen",
     "foremal": "A:hand:provsked",
     "i_handen": null,
     "mal": "kund",
     "blick": null,
     "kontakt": null,
     "beskrivning": "Person A stands upright, her hand no longer holding the spoon."
    }
   ]
  }
 ],
 "relevans": {
  "mening": "Klippet visar den humoristiska kontrasten mellan den minimala glassprovportionen personalen ger kunder och den enorma, ogenerade portionen de tar till sig själva.",
  "modell": "google/gemini-2.5-flash",
  "kalla": "../../scen/3d/gennedbrytning/relevans/kand-kennysgelato-tagningar/relevans.json",
  "poster": [
   {
    "id": "A",
    "namn": "Person A",
    "typ": "person",
    "roll": "bar",
    "behandling": "eget_lager",
    "varfor": "Utför handlingarna som skapar kontrasten mellan kund- och personalportion och är central för skämtet.",
    "tagningar": [
     "S1",
     "S2"
    ],
    "samspel": [
     "hand_A",
     "provsked_liten",
     "skopa_stor",
     "glassdisk",
     "st1",
     "st2",
     "st3"
    ],
    "kalla": "matt",
    "ref": "A"
   },
   {
    "id": "hand_A",
    "namn": "Hand (Person A)",
    "typ": "kroppsdel",
    "roll": "bar",
    "behandling": "bakas_in_i_personen",
    "varfor": "Håller i och hanterar både den lilla provskeden och den stora glasskopan, vilket är avgörande för skämtet.",
    "tagningar": [
     "S1",
     "S2"
    ],
    "samspel": [
     "A",
     "provsked_liten",
     "skopa_stor",
     "glassdisk"
    ],
    "kalla": "last",
    "ref": null
   },
   {
    "id": "provsked_liten",
    "namn": "Liten provsked",
    "typ": "foremal_i_hand",
    "roll": "bar",
    "behandling": "bakas_in_i_personen",
    "varfor": "Representerar den lilla smakportionen som ges till kunden, vilket är den första delen av kontrasten.",
    "tagningar": [
     "S1"
    ],
    "samspel": [
     "A",
     "hand_A",
     "glassdisk",
     "st1"
    ],
    "kalla": "last",
    "ref": "A:hand:provsked"
   },
   {
    "id": "skopa_stor",
    "namn": "Stor glasskopa",
    "typ": "foremal_i_hand",
    "roll": "bar",
    "behandling": "bakas_in_i_personen",
    "varfor": "Representerar den gigantiska portionen som personalen tar till sig själv, vilket är punchlinen.",
    "tagningar": [
     "S2"
    ],
    "samspel": [
     "A",
     "hand_A",
     "glassdisk",
     "st3"
    ],
    "kalla": "last",
    "ref": null
   },
   {
    "id": "glassdisk",
    "namn": "Glassdisk",
    "typ": "mobel",
    "roll": "ramar",
    "behandling": "eget_lager",
    "varfor": "Definierar arbetsplatsen där smakprover och skopor hanteras och ger trovärdighet åt scenariot.",
    "tagningar": [
     "S1",
     "S2"
    ],
    "samspel": [
     "A",
     "provsked_liten",
     "skopa_stor",
     "bakgrund"
    ],
    "kalla": "matt",
    "ref": "disk_A"
   },
   {
    "id": "bakgrund",
    "namn": "Butiksinredning",
    "typ": "bakgrund",
    "roll": "ramar",
    "behandling": "forenklad_form",
    "varfor": "Ger en trovärdig kontext av en glassbutik utan att vara central för skämtet i sig.",
    "tagningar": [
     "S1",
     "S2"
    ],
    "samspel": [
     "glassdisk",
     "A"
    ],
    "kalla": "last",
    "ref": "vagg_bak"
   },
   {
    "id": "st1",
    "namn": "Text kundprover",
    "typ": "text",
    "roll": "bar",
    "behandling": "eget_lager",
    "varfor": "Förklarar visuellt att den lilla portionen är för kunder, vilket är den första delen av skämtet.",
    "tagningar": [
     "S1"
    ],
    "samspel": [
     "provsked_liten",
     "A"
    ],
    "kalla": "last",
    "ref": "st1"
   },
   {
    "id": "st2",
    "namn": "Text vs",
    "typ": "text",
    "roll": "bar",
    "behandling": "eget_lager",
    "varfor": "Markerar tydligt övergången och jämförelsen mellan de två portionerna, avgörande för förståelsen av skämtet.",
    "tagningar": [
     "S2"
    ],
    "samspel": [
     "provsked_liten",
     "skopa_stor"
    ],
    "kalla": "antagen",
    "ref": "st2"
   },
   {
    "id": "st3",
    "namn": "Text personalprover",
    "typ": "text",
    "roll": "bar",
    "behandling": "eget_lager",
    "varfor": "Förklarar visuellt att den stora portionen är för personalen, vilket är upplösningen av skämtet.",
    "tagningar": [
     "S2"
    ],
    "samspel": [
     "skopa_stor",
     "A"
    ],
    "kalla": "antagen",
    "ref": "st3"
   },
   {
    "id": "kamera",
    "namn": "Kamera",
    "typ": "kamera",
    "roll": "ramar",
    "behandling": "utelamnas",
    "varfor": "Fångar händelseförloppet men dess specifika rörelser är inte avgörande för skämtets betydelse i 3D-återskapandet.",
    "tagningar": [
     "S1",
     "S2"
    ],
    "samspel": [],
    "kalla": "matt",
    "ref": null
   },
   {
    "id": "kund_hand",
    "namn": "Kundens hand",
    "typ": "kroppsdel",
    "roll": "bar",
    "behandling": "forenklad_form",
    "varfor": "Tar emot smakprovet i h8; utan mottagaren finns inget smakprov att ge, och kontrasten mot personalens egen portion faller. Missades i 0025.",
    "tagningar": [
     "S1"
    ],
    "samspel": [
     "A",
     "provsked_liten"
    ],
    "kalla": "matt",
    "ref": "kund"
   }
  ]
 },
 "scenbygge": [
  {
   "scen": "s1",
   "objekt": [
    "disk_A",
    "disk_A:fram",
    "disk_A:bak",
    "disk_A:v",
    "disk_A:h",
    "disk_A:trag",
    "bank_bak",
    "kund:kropp",
    "kund:ben",
    "kund:huvud",
    "kund:arm"
   ]
  }
 ],
 "rutor_regel": "frames are source frames [first, last+1) at the clip fps; scene s<n> spans its start_s..slut_s"
}

WRITE, as JSON following the schema below:
1. entiteter: every person, body part that can carry or act (each hand separately), object, CONTENT (what is carried: the food on a spoon is its own entity, not a property of the spoon), furniture, PLACE (where things are taken from or given to), and on-screen text. Link each to the source id (kalla_ref) or null. List its affordances (kan_bara, kan_halla, kan_tas_med_sked, kan_ta_emot, kan_talas_om, ...). kalla: matt if it is in the measured source, last if you read it from the images, antagen if inferred.
2. starttillstand: short predicates true at the first frame: i_hand(hand, object), pa(content, object), i(content, place), vid(person, place), vand_mot(person, x), tittar_pa(person, x), tom(object), har(person, x).
3. handelser: one per action, covering the action-track segments in order (an event may span several segments). ram is one verb from: ta, ge, ta_emot, skopa, lyfta, rakna_fram, halla, luta_sig, rata_pa_sig, sta, ga, sitta, tala, titta, gissa, vaga, ata, peka, scenbyte. roller from: agent, sak, mottagare, verktyg, kalla, kroppsdel, mal. forvillkor must be true in the state before the event; effekt adds and removes facts. Every object that appears in a hand must have been taken (or be in the start state); every content must come from somewhere. Use scenbyte when a new shot resets the world.
4. forlopp: events that belong together under one purpose (e.g. "serve a sample" = take, scoop, lift, hold out, give). This is the unit a CM usually means.
5. mening: the point in one sentence (poang); which roles or facts carry it (bar, written as event.role=entity or as a fact); which are incidental (tillfalligt, e.g. which hand, the tempo); which only frame it (ramar).
6. frihetsgrader: the legal edits. For each: which event, process or entity it applies to (galler), the parameter, the current value, the domain of legal values, the execution level (3d = mirror, IK, retime, remove, repeat in the existing 3D; redigering = needs a motion-editing model; generering = needs a new generation), whether it touches what carries the point (bar_meningen), the propagation (which other events and facts must change with it, and which attachments move), one line of text for the selector with {varde} for the value, and a regi template using ONLY these operations (null if none exists):
- ta_bort_handling {scen, segment}: remove an action-track segment (crossfade over it)
- tempo_handling {scen, segment, faktor}: play a segment slower (>1) or faster (<1)
- upprepa_handling {scen, fran, till, antal}: play a run of segments again
- satt_frihetsgrad {scen, frihetsgrad, parameter, varde, rutor, mal}: execute a degree of freedom in 3D (today: parameter kroppsdel = mirror the arm and IK to the same targets)
- byt_prop {scen, prop, ny_typ}: swap a prop (a held object becomes a placeholder of the new type)
- ta_bort_prop {scen, prop}: remove a prop or piece of furniture
- renderkamera {scen, kamera_id, lage: stativ}: a still camera
- trimma_scen {scen, slut_s, lage: hall_sista}: extend the end by holding the last frame
- flytta_scen {scen, efter}: move a shot (efter null = first)
- ta_bort_scen {scen}: remove a shot
- byt_miljo {scen, rum}: swap the room for a template in the bank (only templates that exist)
   Include edits that are legal but not yet executable (regi null) when a CM is likely to ask for them (another hand for the other person, a facial expression, another place), so the selector can say "this is the one, but it cannot be done yet" instead of guessing something else.
   Do not list an edit that would break the point unless it is a plain removal the CM may ask for; mark those bar_meningen true.

Rules: small general vocabulary; nothing specific to this clip in the vocabulary itself; ids from the source wherever they exist; no invented measurements. Answer with JSON only.

SCHEMA:
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "liggare.schema.json",
  "title": "liggare",
  "description": "0031: vad handlingarna i ett klipp betyder och vad som får ändras. Skrivs vid ingest av en stark modell ur källan, handlingsspåret och relevanslistan. Fakta är korta predikat, pred(arg, arg, ...), med entiteternas id som argument. Jev läser bara ytan (jev_yta), aldrig hela liggaren.",
  "type": "object",
  "properties": {
    "schema_version": {"description": "Kontraktsversion.", "const": "liggare/1"},
    "klipp": {"description": "Klippets id, som i källan.", "type": "string"},
    "kalla": {"description": "Källan liggaren skrevs mot.", "type": "object", "properties": {
      "fil": {"description": "Källans sökväg, relativ till liggaren.", "type": "string"},
      "revision": {"description": "Källans revision.", "type": "integer"}}, "required": ["fil", "revision"], "additionalProperties": false},
    "skriven_av": {"description": "Vem eller vad som skrev liggaren, och med vilken prompt.", "type": "object", "properties": {
      "modell": {"description": "Modellen (eller uppdragstagaren som stark modell).", "type": "string"},
      "prompt": {"description": "Promptens fil.", "type": "string"},
      "tid": {"description": "ISO 8601.", "type": ["string", "null"]}}, "required": ["modell", "prompt"], "additionalProperties": false},
    "entiteter": {"description": "Allt som kan vara argument i ett faktum.", "type": "array", "items": {"$ref": "#/$defs/entitet"}},
    "starttillstand": {"description": "Fakta som är sanna i klippets första ruta.", "type": "array", "items": {"$ref": "#/$defs/faktum"}},
    "handelser": {"description": "Händelser i tidsordning, över handlingsspårets segment.", "type": "array", "items": {"$ref": "#/$defs/handelse"}},
    "forlopp": {"description": "Händelser som hör ihop under ett syfte; den enhet CM oftast menar.", "type": "array", "items": {"$ref": "#/$defs/forlopp"}},
    "mening": {"description": "Vad som bär poängen, vad som är tillfälligt och vad som ramar.", "type": "object", "properties": {
      "poang": {"description": "Poängen i en mening.", "type": "string"},
      "bar": {"description": "Roller eller fakta som bär poängen (till exempel ge.mottagare=kund).", "type": "array", "items": {"type": "string"}},
      "tillfalligt": {"description": "Det som kan ändras utan att poängen faller (till exempel ge.kroppsdel).", "type": "array", "items": {"type": "string"}},
      "ramar": {"description": "Det som ramar men inte bär.", "type": "array", "items": {"type": "string"}}}, "required": ["poang", "bar", "tillfalligt"], "additionalProperties": false},
    "frihetsgrader": {"description": "Lagliga ändringar med värdedomän, utförandenivå, spridning och regi-mall.", "type": "array", "items": {"$ref": "#/$defs/frihetsgrad"}}
  },
  "required": ["schema_version", "klipp", "kalla", "skriven_av", "entiteter", "starttillstand", "handelser", "forlopp", "mening", "frihetsgrader"],
  "additionalProperties": false,
  "$defs": {
    "faktum": {"description": "Ett predikat, pred(arg, ...). Argumenten är entiteters id eller korta konstanter (hoger, vanster).", "type": "string", "pattern": "^[a-z_]+\\([^()]*\\)$"},
    "entitet": {"description": "En entitet med affordanser.", "type": "object", "properties": {
      "id": {"description": "Unikt id.", "type": "string", "minLength": 1},
      "typ": {"description": "person, kroppsdel, foremal, innehall, mobel, plats eller text.", "type": "string", "enum": ["person", "kroppsdel", "foremal", "innehall", "mobel", "plats", "text"]},
      "namn": {"description": "Läsbart namn.", "type": "string"},
      "agare": {"description": "För kroppsdel: personen. Annars null.", "type": ["string", "null"]},
      "kalla_ref": {"description": "Id i källan eller planen (person, objekt, handföremål, skärmtext). null = finns inte där (till exempel innehållet).", "type": ["string", "null"]},
      "affordanser": {"description": "Vad den kan göras med eller göra (kan_bara, kan_halla, kan_tas_med_sked, kan_ta_emot, ...).", "type": "array", "items": {"type": "string"}},
      "kalla": {"description": "matt, last eller antagen.", "type": "string", "enum": ["matt", "last", "antagen"]}},
      "required": ["id", "typ", "affordanser", "kalla"], "additionalProperties": false},
    "handelse": {"description": "En händelse: ram, roller, förvillkor och effekt.", "type": "object", "properties": {
      "id": {"description": "Unikt id.", "type": "string", "minLength": 1},
      "ram": {"description": "Ett verb ur ett litet förråd (ge, ta, ta_emot, skopa, lyfta, rakna_fram, halla, luta_sig, rata_pa_sig, sta, tala, titta, gissa, vaga, ...).", "type": "string"},
      "segment": {"description": "Handlingsspårets segment-id som händelsen täcker.", "type": "array", "items": {"type": "string"}},
      "rutor": {"description": "Källrutor [första, sista+1).", "type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
      "roller": {"description": "Roll -> entitet-id (agent, sak, mottagare, verktyg, kalla, kroppsdel, mal).", "type": "object", "additionalProperties": {"type": "string"}},
      "forvillkor": {"description": "Fakta som måste vara sanna före.", "type": "array", "items": {"$ref": "#/$defs/faktum"}},
      "effekt": {"description": "Fakta som läggs till och tas bort.", "type": "object", "properties": {
        "lagg_till": {"description": "Blir sanna.", "type": "array", "items": {"$ref": "#/$defs/faktum"}},
        "ta_bort": {"description": "Upphör.", "type": "array", "items": {"$ref": "#/$defs/faktum"}}}, "required": ["lagg_till", "ta_bort"], "additionalProperties": false},
      "kalla": {"description": "matt (gränser och hållning ur mätning), last (ur en modell) eller antagen.", "type": "string", "enum": ["matt", "last", "antagen"]},
      "anmarkning": {"description": "Fritt, kort.", "type": ["string", "null"]}},
      "required": ["id", "ram", "segment", "rutor", "roller", "forvillkor", "effekt", "kalla"], "additionalProperties": false},
    "forlopp": {"description": "Ett förlopp.", "type": "object", "properties": {
      "id": {"description": "Unikt id.", "type": "string", "minLength": 1},
      "syfte": {"description": "Syftet i några ord.", "type": "string"},
      "handelser": {"description": "Händelsernas id i ordning.", "type": "array", "items": {"type": "string"}},
      "rutor": {"description": "Källrutor [första, sista+1).", "type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2}},
      "required": ["id", "syfte", "handelser", "rutor"], "additionalProperties": false},
    "frihetsgrad": {"description": "En laglig ändring.", "type": "object", "properties": {
      "id": {"description": "Unikt id; Jev-ytan pekar hit.", "type": "string", "minLength": 1},
      "galler": {"description": "Händelse- eller förlopps-id, eller entitet-id för en entitets egenskap.", "type": "string"},
      "parameter": {"description": "Vad som ändras: kroppsdel, tempo, antal, sak, finns, ordning, ...", "type": "string"},
      "varde_nu": {"description": "Värdet i källan."},
      "doman": {"description": "Lagliga värden.", "type": "object", "properties": {
        "typ": {"description": "mangd eller intervall.", "type": "string", "enum": ["mangd", "intervall"]},
        "varden": {"description": "För mangd.", "type": "array"},
        "min": {"description": "För intervall.", "type": "number"},
        "max": {"description": "För intervall.", "type": "number"}}, "required": ["typ"], "additionalProperties": false},
      "niva": {"description": "Utförandenivå: 3d (direkt), redigering (rörelseredigeringsmodell) eller generering (ny generering).", "type": "string", "enum": ["3d", "redigering", "generering"]},
      "bar_meningen": {"description": "Sant om ändringen rör något som bär poängen (kompilatorn varnar).", "type": "boolean"},
      "spridning": {"description": "Det som måste följa med.", "type": "object", "properties": {
        "handelser": {"description": "Händelser som ändras.", "type": "array", "items": {"type": "string"}},
        "fakta": {"description": "Fakta som ändras, som 'gammalt -> nytt'.", "type": "array", "items": {"type": "string"}},
        "foremal": {"description": "Fästen eller föremål som flyttas.", "type": "array", "items": {"type": "string"}}}, "required": ["handelser", "fakta"], "additionalProperties": false},
      "text": {"description": "En rad till Jev, med {varde} för värdet.", "type": "string"},
      "regi": {"description": "Regi-mall: edits med {varde} som platshållare; null = ingen operation finns (nivån saknas).", "type": ["array", "null"], "items": {"type": "object"}}},
      "required": ["id", "galler", "parameter", "doman", "niva", "spridning", "text", "regi"], "additionalProperties": false}
  }
}



IMAGES: C:\Users\praiseworthy\Desktop\hagen-wf\scen\3d\ingest\ut\kand-kennysgelato-tagningar\brief\kontakt_S1.jpg, C:\Users\praiseworthy\Desktop\hagen-wf\scen\3d\ingest\ut\kand-kennysgelato-tagningar\brief\kontakt_S2.jpg