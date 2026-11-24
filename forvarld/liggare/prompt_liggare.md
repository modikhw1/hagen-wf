# Prompt: liggaren för ett klipp (0031)

Körs vid ingest av en stark modell: uppdragstagaren i 0031, eller via API (`forvarld/liggare/kor_liggare.py --modell ...`).
- **Underlaget** fylls i av skriptet och skickas med: källans semantik, handlingsspåret, relevanslistan, kontaktbladen och regi-operationerna.
- **Svaret** är en JSON enligt `scen/3d/kontrakt/liggare.schema.json`.

---

You write the LEDGER (liggare) for a short vertical video clip that has been decomposed into an editable 3D "pre-world". A content manager (CM) will later change the clip with one sentence ("let her give the sample with the other hand", "make it two samples"). A fast, shallow selector picks among the edits you list here, so everything that requires understanding must be done by you, now.

GIVEN (facts from measurement and earlier steps; do not contradict them, refer to their ids):
{underlag}

WRITE, as JSON following the schema below:
1. entiteter: every person, body part that can carry or act (each hand separately), object, CONTENT (what is carried: the food on a spoon is its own entity, not a property of the spoon), furniture, PLACE (where things are taken from or given to), and on-screen text. Link each to the source id (kalla_ref) or null. List its affordances (kan_bara, kan_halla, kan_tas_med_sked, kan_ta_emot, kan_talas_om, ...). kalla: matt if it is in the measured source, last if you read it from the images, antagen if inferred.
2. starttillstand: short predicates true at the first frame: i_hand(hand, object), pa(content, object), i(content, place), vid(person, place), vand_mot(person, x), tittar_pa(person, x), tom(object), har(person, x).
3. handelser: one per action, covering the action-track segments in order (an event may span several segments). ram is one verb from: ta, ge, ta_emot, skopa, lyfta, rakna_fram, halla, luta_sig, rata_pa_sig, sta, ga, sitta, tala, titta, gissa, vaga, ata, peka, scenbyte. roller from: agent, sak, mottagare, verktyg, kalla, kroppsdel, mal. forvillkor must be true in the state before the event; effekt adds and removes facts. Every object that appears in a hand must have been taken (or be in the start state); every content must come from somewhere. Use scenbyte when a new shot resets the world.
4. forlopp: events that belong together under one purpose (e.g. "serve a sample" = take, scoop, lift, hold out, give). This is the unit a CM usually means.
5. mening: the point in one sentence (poang); which roles or facts carry it (bar, written as event.role=entity or as a fact); which are incidental (tillfalligt, e.g. which hand, the tempo); which only frame it (ramar).
6. frihetsgrader: the legal edits. For each: which event, process or entity it applies to (galler), the parameter, the current value, the domain of legal values, the execution level (3d = mirror, IK, retime, remove, repeat in the existing 3D; redigering = needs a motion-editing model; generering = needs a new generation), whether it touches what carries the point (bar_meningen), the propagation (which other events and facts must change with it, and which attachments move), one line of text for the selector with {varde} for the value, and a regi template using ONLY these operations (null if none exists):
{operationer}
   Include edits that are legal but not yet executable (regi null) when a CM is likely to ask for them (another hand for the other person, a facial expression, another place), so the selector can say "this is the one, but it cannot be done yet" instead of guessing something else.
   Do not list an edit that would break the point unless it is a plain removal the CM may ask for; mark those bar_meningen true.

Rules: small general vocabulary; nothing specific to this clip in the vocabulary itself; ids from the source wherever they exist; no invented measurements. Answer with JSON only.

SCHEMA:
{schema}
