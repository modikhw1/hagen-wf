// scenlasning/0: vad ingesten ska ge för att ryggraden, regin och blockouten ska stå på läsning i stället för schabloner.
// Två pass. Pass 1 är ett protokoll (bara det som syns och hörs). Pass 2 tolkar, med protokollet framför sig.
const s = (description, e) => ({ type: 'string', description, ...(e ? { enum: e } : {}) })
const n = (description, min, max) => ({ type: 'number', description, ...(min !== undefined ? { minimum: min } : {}), ...(max !== undefined ? { maximum: max } : {}) })
const b = description => ({ type: 'boolean', description })
const obj = properties => ({ type: 'object', properties, required: Object.keys(properties), additionalProperties: false })
const arr = (items, description) => ({ type: 'array', items, ...(description ? { description } : {}) })

export const STALLEN = ['utanfor', 'bar', 'disk', 'bakom_disk', 'kok', 'bord', 'uteservering', 'lokalen', 'lager', 'bil', 'annat']
export const FUNKTION = ['krok', 'uppbyggnad', 'visning', 'vandning', 'punchline', 'tilltal', 'avslut']
export const KANAL = ['replik', 'text', 'sak', 'storlek', 'klipp', 'ljud', 'min', 'handling']
const BELAGG = ['sett', 'hort', 'antaget']

export const protokoll = obj({
  langd_s: n('Clip length in seconds.'),
  klipp: arr(n('Timestamp in seconds of a hard cut.'), 'Every hard cut, in order.'),
  personer_samtidigt: n('Most people visible in one frame.', 0),
  personer_totalt: n('Distinct people who appear at all.', 0),
  handelser: arr(obj({
    t: n('Second it starts.'), vem: s('Short neutral label for the person, e.g. "woman in black apron".'),
    syns: s('What is visible, one sentence, no interpretation.'), hors: s('What is heard, verbatim if speech, else "".'),
  })),
  tal: arr(obj({ in_s: n('Start.'), ut_s: n('End.'), vem: s('Speaker label or "unknown".'), text: s('Verbatim.'),
    kalla: s('How the speech exists.', ['live_i_bild', 'berattarrost', 'lanat_ljud', 'oklart']) })),
  text: arr(obj({ in_s: n('Start.'), ut_s: n('End.'), text: s('Verbatim on-screen text.') })),
  ljud: obj({ musik: b('Is there music?'), byte_s: arr(n('Second where the music or sound changes clearly.')), trendljud: b('Is the sound a known reused clip or song?') }),
})

const person = obj({
  roll: s('Role.', ['personal', 'gast', 'chef', 'forbipasserande', 'kreator', 'okand']),
  plats_i_bild: s('Position in frame.', ['vanster', 'mitten', 'hoger', 'utanfor']),
  vand_mot: s('What the person faces.', ['kamera', 'motspelare', 'produkt', 'bort']),
  hallning: s('Posture.', ['star', 'sitter', 'gar', 'ligger', 'bojd']),
  hander: arr(s('What the hands do.', ['haller_upp', 'racker', 'tar_emot', 'ater', 'tillagar', 'betalar', 'pekar', 'gestikulerar', 'vilar'])),
  utsnitt: s('How much of the person is in frame.', ['narbild', 'halvbild', 'helbild']),
})

export const tolkning = obj({
  strategi: s('What kind of content this is.', ['tilltal', 'sketchvarld', 'visning', 'kampanj', 'trend', 'premium_stamning']),
  tilltal: s('How the viewer is addressed.', ['till_kamera', 'spelad_scen', 'berattarrost', 'inget']),
  karna: s('The idea in one sentence, transferable to another business.'),
  mall: s('The transferable template with [slots] in square brackets.'),
  platser: arr(obj({ plats: s('Slot name as in the template.'), har: s('What fills it here.'),
    typ: s('Kind of slot.', ['produkt', 'rekvisita', 'replik', 'text', 'lokal', 'person', 'situation']) })),
  takter: arr(obj({
    in_s: n('Start.'), ut_s: n('End.'), vad: s('What happens, one sentence.'),
    funktion: s('Function in the clip.', FUNKTION),
    bar: s('Removal test: ryggrad, stod or fri.', ['ryggrad', 'stod', 'fri']),
    bunden: s('What the beat depends on.', ['ingen', 'produkt', 'lokal', 'person', 'redigering', 'trend']),
    stalle: s('Where it takes place.', STALLEN), stalle_annat: s('Five words if stalle is annat, else "".'),
    personer: arr(person),
    motpart_i_bild: s('The customer or counterpart.', ['i_bild', 'kant', 'utanfor', 'ingen_motpart']),
    spelas_mot: s('Who the performance is aimed at.', ['kamera', 'motspelare', 'ingen']),
    belagg: s('Seen, heard or assumed.', BELAGG),
  })),
  poang: obj({ kanal: s('The one channel that carries the point.', KANAL), sek: n('Second it lands.'), vad: s('What exactly, in ten words.'),
    belagg: s('Seen, heard or assumed.', BELAGG) }),
  text_roller: arr(obj({ text: s('The on-screen text.'), roll: s('What the text does.', ['undertext', 'premiss', 'punchline', 'info']) })),
  kontrast: obj({ finns: b('Does the clip set two things against each other?'), liten: s('The small side, or "".'), stor: s('The large side, or "".'),
    overdrift: n('1 barely noticeable, 5 absurd. 0 if no contrast.', 0, 5) }),
  spel: obj({
    mekanik: s('Kind of joke, or ingen.', ['kontrast', 'avslojande', 'bokstavligt', 'eskalering', 'fasad', 'overdrift', 'satt_pa_plats', 'missforstand', 'igenkanning', 'ingen']),
    relation: s('Who acts on whom.', ['personal_mot_gast', 'gast_mot_personal', 'personal_sinsemellan', 'chef_och_personal', 'gaster_sinsemellan', 'personal_ensam', 'annan']),
    offer: s('At whose expense.', ['personal', 'gast', 'chef', 'ingen']),
    insats: s('What is at stake.', ['betalning', 'service', 'mat', 'uppmarksamhet', 'vila', 'regler', 'ingen']),
    byte_andrar: b('Swap test: would the clip mean something else if the two parties traded places?'),
    belagg: s('Seen, heard or assumed.', BELAGG),
  }),
  tilltalet: obj({
    grepp: s('What the speaker does with attention, or inget.', ['svarar_pa_fraga', 'provsmakar', 'visar_tillagning', 'guidar', 'utmanar_publiken', 'annonserar', 'bakom_kulisserna', 'tycker_till', 'krok_som_vander', 'inget']),
    motpart: s('Who is addressed.', ['tittaren', 'kollega', 'gast_eller_forbipasserande', 'kommentar', 'ingen']),
    last: s('What carries interest.', ['produkten', 'manniskan', 'iden', 'erbjudandet']),
  }),
  osakert: arr(s('Anything you could not determine from the clip, one line each.')),
})
