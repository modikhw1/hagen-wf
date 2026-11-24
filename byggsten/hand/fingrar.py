"""Fingrarna: axlar för scenändring, härledda ur metadata som lästes för ett annat ändamål.

Två sorter hålls isär (dialogens punkt om "vad" och "känsla"):
  yta    : iakttagelser ur L3 (de 43 ytlagren). Varje yt-finger äger en kanal i 3D-scenen.
  mening : tolkningar ur L4 (formatkortet): var poängen bor och hur den läses.

Varje finger ger ett värde 0..1 per klipp, eller None när underlaget saknas.
"""

KARNORD = {'lite': 0.0, 'en_del': 0.5, 'mycket': 1.0}


def _beats(l4, bar=None):
    b = l4.get('beats') or []
    return [x for x in b if bar is None or x.get('bar') == bar]


def _andel(xs, test):
    xs = list(xs)
    return sum(1 for x in xs if test(x)) / len(xs) if xs else None


def _platstyper(l4):
    return {p.get('typ') for p in (l4.get('platser') or [])}


# --- yt-fingrar (L3) -------------------------------------------------------

def ensemble(r):
    return r['l3']['personer'] / 3


def samspel(r):
    l = r['l3']
    return (l['dialog'] + l['roll'] + (not l['tilltal'])) / 3


def ord_(r):
    return {'inget': 0.0, 'voiceover': 0.5, 'repliker': 1.0, 'bada': 1.0}[r['l3']['tal']]


def text(r):
    l = r['l3']
    return (l['skarmtext'] / 3 + l['text_poang']) / 2


def klippning(r):
    l = r['l3']
    return (l['klipp'] / 3 + l['montage']) / 2


def produkt(r):
    l = r['l3']
    return (l['mat_andel'] / 4 + l['tillagning']) / 2


def rum(r):
    return r['l3']['lokal'] / 3


def ansikte(r):
    return float(r['l3']['narbild_ansikte'])


def lanat_ljud(r):
    l = r['l3']
    return (l['trendljud'] + l['mimar']) / 2


# --- meningsfingrar (L4) ---------------------------------------------------

def poang_i_ord(r):
    """Poängen ligger i en replik eller en text som går att byta ut."""
    t = _platstyper(r['l4'])
    return (('replik' in t) + ('text' in t)) / 2


def poang_i_sak(r):
    """Poängen ligger i ett föremål eller i produkten."""
    l4 = r['l4']
    a = _andel(_beats(l4, 'karna'), lambda b: b.get('bunden') == 'produkt')
    if a is None:
        return None
    return (a + ('rekvisita' in _platstyper(l4))) / 2


def poang_i_klipp(r):
    """Poängen ligger i redigeringen: klipp, vidbild, musikbyte, text som slås på."""
    l4 = r['l4']
    a = _andel(_beats(l4), lambda b: b.get('bunden') == 'redigering')
    k = KARNORD.get((l4.get('sprak') or {}).get('klippberoende'))
    if a is None or k is None:
        return None
    return (min(1.0, a * 3) + k) / 2


def poang_i_person(r):
    """Poängen bärs av just den här personen (karisma, frontfigur)."""
    l4 = r['l4']
    a = _andel(_beats(l4, 'karna'), lambda b: b.get('bunden') == 'person')
    if a is None:
        return None
    return (a + ((l4.get('grundvarde') or {}).get('bars_av') == 'karisma')) / 2


def vandning(r):
    l4 = r['l4']
    f = {b.get('funktion') for b in _beats(l4)}
    return (bool((l4.get('grundvarde') or {}).get('vandning')) + ('punchline' in f) + ('vandning' in f)) / 3


FINGRAR = {
    # namn: (sort, lager, funktion, kanal i 3D-scenen, pol 0, pol 1)
    'ensemble':   ('yta', 'l3', ensemble, 'kroppar: antal', 'ingen person', 'tre eller fler'),
    'samspel':    ('yta', 'l3', samspel, 'kroppar: blick och riktning', 'talar till kameran', 'spelad scen mellan roller'),
    'ord':        ('yta', 'l3', ord_, 'replikspår', 'inget tal', 'repliker'),
    'text':       ('yta', 'l3', text, 'textlager', 'ingen skärmtext', 'texten bär poängen'),
    'klippning':  ('yta', 'l3', klippning, 'tidslinje: tagningar', 'en tagning', 'montage'),
    'produkt':    ('yta', 'l3', produkt, 'föremål: mat och dryck', 'ingen mat i fokus', 'mat och tillagning hela tiden'),
    'rum':        ('yta', 'l3', rum, 'rum: hur mycket som byggs', 'ingen lokal syns', 'mycket av lokalen syns'),
    'ansikte':    ('yta', 'l3', ansikte, 'mimik (saknas i förvärlden)', 'inget uttryck bär', 'närbild där uttrycket bär'),
    'lanat_ljud': ('yta', 'l3', lanat_ljud, 'ljudspår (saknas i förvärlden)', 'eget ljud', 'trendljud som mimas'),
    'poang_i_ord':    ('mening', 'l4', poang_i_ord, 'replikspår, textlager', 'poängen är inte en mening', 'poängen är en utbytbar replik eller text'),
    'poang_i_sak':    ('mening', 'l4', poang_i_sak, 'föremål', 'poängen ligger inte i något föremål', 'poängen ligger i föremålet eller produkten'),
    'poang_i_klipp':  ('mening', 'l4', poang_i_klipp, 'tidslinje, kamera', 'tål vilken klippning som helst', 'poängen finns i klippet'),
    'poang_i_person': ('mening', 'l4', poang_i_person, 'kroppar: vem', 'vem som helst kan göra det', 'bärs av just den personen'),
    'vandning':       ('mening', 'l4', vandning, 'tidslinje: ordning', 'ingen vändning', 'vändning och punchline'),
}

KATEGORIER = {
    # hålls som kategorier, inte som tal
    'plats': lambda r: tuple(sorted((r['l4'].get('krav') or {}).get('lokal') or [])),
    'strategi': lambda r: (r['l4'].get('sprak') or {}).get('strategi'),
    'tilltal': lambda r: (r['l4'].get('sprak') or {}).get('tilltal'),
}


def las(r):
    """Fingervärden för ett klipp. None där lagret eller fältet saknas."""
    ut = {}
    for namn, (sort, lager, f, *_ ) in FINGRAR.items():
        if lager not in r:
            ut[namn] = None
            continue
        try:
            v = f(r)
            ut[namn] = None if v is None else round(float(v), 3)
        except (KeyError, TypeError):
            ut[namn] = None
    return ut


def niva(v):
    """Tre lägen per finger. Rutten räknar hopp i lägen, inte i decimaler."""
    if v is None:
        return None
    return 0 if v < 1 / 3 else (1 if v <= 2 / 3 else 2)
