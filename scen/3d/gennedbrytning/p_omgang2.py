"""0026 punkt 5: Dreamina omgång 2 för gelato S1. Indata, en prompt per körning och LAS-MIG.md i d_video/dreamina-paket/omgang2/.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/p_omgang2.py
Promptens tider kommer ur handlingsspårets mätta segment (handling/S1/handling.json), skalade till körningens längd, så att tiderna är
källans och tidspassningen (t_tid.py) blir nära linjär. Lärdomar ur utfall 1 (svar 0026): huvudet ärvde källans bildkant, kameran tippade
från cirka 5 s, och handen gick ned till fötterna.
"""
import json, shutil, subprocess
from pathlib import Path

HIT = Path(__file__).resolve().parent; UT = HIT / 'd_video/dreamina-paket/omgang2'; K2 = HIT / 'kamerafri_k2'
SEG = json.loads((HIT / 'handling/S1/handling.json').read_text(encoding='utf-8'))['segment']; KALLA_S = 148 / 29.97

VAD = {  # vad hon gör per segment, i ordning; samma ord som handlingsspåret, skrivet för en videomodell
    'h1': 'stands upright behind where the counter was, looks down, holding the small spoon in her right hand low in front of her',
    'h2': 'starts to bend forward at the hips and lowers the spoon',
    'h3': 'stays bent forward and scoops a small taste of ice cream with the spoon; her hand goes down only to about knee height',
    'h4': 'straightens up and lifts the spoon with the taste',
    'h5': 'stands upright holding the spoon at chest height',
    'h6': 'starts to stretch her right arm forward towards the camera with the spoon',
    'h7': 'holds the spoon out towards the camera, arm stretched',
    'h8': 'keeps the arm stretched and offers the spoon towards the camera, as if a customer takes it',
    'h9': 'keeps standing with her arm forward and smiles'}

BAS = ("Remove the ice-cream display counter, the glass, the ice-cream tubs, the shop interior, the on-screen text and the customer's hand. "
       "Keep the woman and the small tasting spoon she holds in her right hand, with the same movements as in the source video. "
       "She stands on a plain light-grey floor in front of a plain light-grey background, and her whole body from head to feet is visible in every frame. "
       "Her head is always fully visible: where her head leaves the top of the source frame while she bends forward, show her whole head as in the bent reference image; never cut her head off with a straight edge. "
       "She stands in the same spot the whole time: her feet stay still and her legs stay straight. When she leans forward she bends at the hips. "
       "The only thing in her hands is the small spoon; there is nothing in front of her. "
       "The camera is locked on a tripod at chest height and never moves, tilts or zooms: her feet stay on the same place in the frame and her size in the frame is the same from the first frame to the last.")
MARK = " The thin dark line across the floor in the source is a guide for where her feet stand: keep her feet on it, and do not draw the line."


def tider(langd):
    f = langd / KALLA_S
    return ' '.join(f"{s['tid_s'][0] * f:.1f}-{s['tid_s'][1] * f:.1f} s: she {VAD[s['id']]}." for s in SEG)


def koda(src, dst, extra=''):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(src)] + (['-vf', extra] if extra else []) + ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-an', str(dst)], check=True)


def main():
    UT.mkdir(parents=True, exist_ok=True); (UT / 'svar').mkdir(exist_ok=True)
    koda(K2 / 'k2.mp4', UT / '1_kalla_k2_h264.mp4')
    koda(K2 / 'k2.mp4', UT / '2_kalla_k2_8s_h264.mp4', f'setpts=PTS*{8 / KALLA_S:.5f},fps=29.97')
    # fast markering: en tunn mörk linje där fötterna står i nyckelbilden för ruta 0 (fotlinjen 1688 px i den kamerafria ramen)
    koda(K2 / 'k2.mp4', UT / '3_kalla_k2_markering_h264.mp4', 'drawbox=x=0:y=1686:w=iw:h=6:color=0x303030@1:t=fill')
    for i, r in enumerate([0, 55, 94, 136], 4): shutil.copy(K2 / f'nyckel/kf_{r:03d}.png', UT / f'{i}_nyckel_kallruta{r:03d}.png')
    K = {1: ('1_5s_universell', BAS + ' Timing: ' + tider(5.0)),
         2: ('2_5s_markering', BAS + MARK + ' Timing: ' + tider(5.0)),
         3: ('3_8s_nedsaktad', BAS + ' Timing: ' + tider(8.0)),
         4: ('4_flera_bildrutor', None)}
    for n, (namn, p) in K.items():
        if p: (UT / f'prompt_{namn}.txt').write_text(p, encoding='utf-8')
    # flera bildrutor: en text per övergång mellan nyckelbilderna (tider ur källan, 5 s)
    t = [0, 55 / 29.97, 94 / 29.97, 136 / 29.97, KALLA_S]
    over = ["She bends forward at the hips and lowers the small spoon in her right hand to about knee height, as if scooping. Whole body visible, head never cut, camera locked.",
            "She scoops a taste with the spoon, straightens up and lifts the spoon to her chest. Whole body visible, camera locked, feet still.",
            "She stretches her right arm straight forward towards the camera, offering the spoon with the taste. Camera locked, feet still.",
            "She keeps the arm stretched towards the camera, holding out the spoon, and smiles. Camera locked."]
    (UT / 'prompt_4_flera_bildrutor.txt').write_text('\n'.join(f"Bildruta {i + 4} -> {i + 5} ({t[i + 1] - t[i]:.1f} s): {o}" for i, o in enumerate(over[:3])) + f"\nEfter sista bildrutan ({t[4] - t[3]:.1f} s): {over[3]}\n", encoding='utf-8')
    print('klart', sorted(p.name for p in UT.iterdir()))


if __name__ == '__main__': main()
