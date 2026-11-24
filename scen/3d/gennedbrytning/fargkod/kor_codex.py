"""0025 del B: färgkodade föremålslager genom Codex (codex_bild.py, ny session per bild, rått läge), i tur och ordning.

  CODEX_RAA=1 scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/fargkod/kor_codex.py [--max 18] [--lista]
codex_bild.py tar den nyaste genererade bilden och den nyaste sessionsfilen, så två samtidiga körningar kan byta resultat med varandra.
Därför körs jobben i tur och ordning, viktigast först. Ett jobb som redan har en bild hoppas över. Kvoten läses före varje jobb, och
körningen stannar när femtimmarsfönstret passerar STOPP_PROCENT (minst en tredjedel ska lämnas).
Föremålen kommer ur relevanslistan (del A, roll bar eller ramar). Skärmtext och kamera färgas inte: de är inte föremål i rummet.
Fast palett per id, samma i alla rutor. Prompten för varje jobb sparas som fargkod/prompter/<jobb>.txt.
"""
import argparse, json, sys
from pathlib import Path

HIT = Path(__file__).resolve().parent; GEN = HIT.parent; sys.path.insert(0, str(GEN))
import codex_bild

STOPP_PROCENT = 62
PALETT = {
    'gelato': [('disk_A', 'the ice-cream display counter: its glass, metal frame, the ice-cream tubs and the front panel', 'pure green #00C853'),
               ('bakgrund', 'the background behind her: back wall, shelves, back counter, machines and ceiling', 'pure blue #2962FF'),
               ('A:hand:provsked', 'the small tasting spoon in her hand, only if it is visible', 'pure yellow #FFD600')],
    'guac': [('bardisk', 'the bar counter: the wooden countertop and the white front below it', 'pure green #00C853'),
             ('stol_A', 'the bar stool he sits on, only if it is visible', 'pure orange #FF6D00'),
             ('vagg_bak', 'the wall behind him with the colourful mural', 'pure blue #2962FF'),
             ('foremal_i_hand_A', 'the object he holds in his hands', 'pure yellow #FFD600')]}
PERSON = 'pure magenta #D500F9'
VEM = dict(gelato='the woman', guac='the man')


def lista(klipp, utan=()):
    return '\n'.join(f'- {b}: {f}' for i, b, f in PALETT[klipp] if i not in utan)


def v1(k):
    return (f"Recolour only these things in this photo, each with one flat, saturated, uniform colour over its whole visible surface, with no texture, shading or highlights, keeping its exact outline:\n{lista(k)}\n"
            f"Everything else stays exactly as it is, pixel for pixel: {VEM[k]}, the rest of the room, the lighting, the on-screen text, the camera and the framing. "
            "Do not move, resize, redraw, add or remove anything. Same size and 9:16 framing.")


def v2(k):
    return (f"Turn this photo into a flat colour map with no texture, shading, light or detail. Each of these things becomes one uniform flat colour region with its exact outline from the photo:\n{lista(k)}\n"
            f"- {VEM[k]}, including hair, clothes and hands: {PERSON}\n"
            "Everything else, including the on-screen text, becomes flat neutral grey #808080. Keep every outline exactly where it is in the photo: do not move, resize or redraw any shape. Same size and 9:16 framing.")


def v4(k):
    return (f"This photo shows a room with nobody in it. Recolour only these things, each with one flat, saturated, uniform colour over its whole surface, with no texture, shading or highlights, keeping its exact outline:\n"
            f"{lista(k, utan=('A:hand:provsked', 'foremal_i_hand_A'))}\n"
            "Everything else stays exactly as it is, pixel for pixel. Do not move, resize, redraw, add or remove anything. Same size and 9:16 framing.")


V3_DISK = ("Remove everything from this photo except the ice-cream display counter (its glass, metal frame, ice-cream tubs, labels and front panel). "
           "Remove the woman, the back wall, the shelves, the back counter, the machines, the ceiling, the customer's hand and the on-screen text, and replace all of it with flat light grey. "
           "Where the woman or her arm hid parts of the counter, complete the counter as it continues. The counter stays exactly where it is, same size and perspective, pixel for pixel: do not move, redraw or tidy it. Same 9:16 framing.")
V3_RUM = ("Remove the ice-cream display counter from this photo: the glass, the metal frame, the tubs, the labels and the front panel. "
          "Fill the area where it stood with what is behind it: the floor continuing to the back counter, and the lower part of the back counter and its cabinets, at the same perspective and lighting. "
          "Keep everything else exactly as it is, pixel for pixel: the wall, the shelves, the machines, the ceiling, the camera and the framing. Same 9:16. Do not restyle, tidy or move anything.")
V3_BAR = ("Remove everything from this photo except the bar counter (the wooden countertop and the white front below it). "
          "Remove the man, the stool, the hanging glasses, the walls, the mural, the payment terminal, the cups, the objects on the counter and the on-screen text, and replace all of it with flat light grey. "
          "Where the man, his arms or the objects hid parts of the counter, complete the counter as it continues. The counter stays exactly where it is, same size and perspective: do not move or redraw it. Same 9:16 framing.")
A_GUAC = ("Remove the man from this photo, together with the object he holds. Nothing else changes. Fill the area where he was with what is behind him: the wall with the mural, the bar and the stool, continued naturally from what is visible around him. "
          "Also remove the white on-screen text and fill it in the same way. Keep everything else exactly as it is, pixel for pixel: the counter, the glasses, the payment terminal, the lighting, the camera and the framing. Same 9:16, same size. Do not restyle or move anything.")

R = HIT / 'rutor'
JOBB = [  # (jobb, prompt, bilder), viktigast först
    ('V1_gelato_000', v1('gelato'), [R / 'gelato_000.png']), ('V2_gelato_000', v2('gelato'), [R / 'gelato_000.png']),
    ('V3disk_gelato_000', V3_DISK, [R / 'gelato_000.png']), ('V4_gelato_000', v4('gelato'), [R / 'gelato_000_A.png']),
    ('V1_guac_000', v1('guac'), [R / 'guac_000.png']), ('V2_guac_000', v2('guac'), [R / 'guac_000.png']),
    ('V3bar_guac_000', V3_BAR, [R / 'guac_000.png']), ('A_guac_000', A_GUAC, [R / 'guac_000.png']),
    ('V4_guac_000', v4('guac'), [HIT / 'codex/A_guac_000.png']),
    ('V1_gelato_055', v1('gelato'), [R / 'gelato_055.png']), ('V1_gelato_112', v1('gelato'), [R / 'gelato_112.png']),
    ('V2_gelato_055', v2('gelato'), [R / 'gelato_055.png']), ('V2_gelato_112', v2('gelato'), [R / 'gelato_112.png']),
    ('V4_gelato_055', v4('gelato'), [R / 'gelato_055_A.png']), ('V4_gelato_112', v4('gelato'), [R / 'gelato_112_A.png']),
    ('V3disk_gelato_055', V3_DISK, [R / 'gelato_055.png']), ('V3disk_gelato_112', V3_DISK, [R / 'gelato_112.png']),
    ('V3rum_gelato_000', V3_RUM, [R / 'gelato_000_A.png'])]


def main():
    a = argparse.ArgumentParser(); a.add_argument('--max', type=int, default=18); a.add_argument('--lista', action='store_true'); x = a.parse_args()
    (HIT / 'prompter').mkdir(exist_ok=True); (HIT / 'codex').mkdir(exist_ok=True)
    for j, p, _ in JOBB: (HIT / 'prompter' / f'{j}.txt').write_text(p, encoding='utf-8')
    (HIT / 'palett.json').write_text(json.dumps(dict(PALETT, person=PERSON), ensure_ascii=False, indent=1), encoding='utf-8')
    if x.lista: print('\n'.join(j for j, _, _ in JOBB)); return
    gjorda = 0
    for j, p, bilder in JOBB:
        ut = HIT / 'codex' / f'{j}.png'
        if ut.exists(): continue
        if gjorda >= x.max: break
        if not all(Path(b).exists() for b in bilder): print('HOPPAR', j, 'saknar indata', flush=True); continue
        kv = codex_bild.kvot(); pr = (kv.get('primar') or {}).get('used_percent')
        if pr is not None and pr >= STOPP_PROCENT and kv.get('primar', {}).get('resets_at', 0) > __import__('time').time():
            print('STOPP kvot', pr, flush=True); break
        r = codex_bild.generera(ut, p, [str(b) for b in bilder]); gjorda += 1
        print('JOBB', j, 'bild' if ut.exists() else 'INGEN BILD', 'hel' if r.get('prompt_fram', {}).get('hel') else 'PROMPT EJ HEL', r['sekunder'], 's',
              'kvot', (r['kvot_efter'].get('primar') or {}).get('used_percent'), flush=True)
    print('KLAR', gjorda, flush=True)


if __name__ == '__main__': main()
