"""0017 del D / 0019 variant (a): isolerad person som video, Luma Ray 3.2 video-till-video på fal.

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/d_video.py <variant>
a  = startbild: ruta 0, ägarens GPT-isolering passad mot masken (nyckel/B_000_passad.png), STEP 2 ur luma-agaren/PROMPT.txt, 540p, 5 s,
     edit_strength lämnas åt Lumas standard. Källa: luma-agaren/1_kalla_gelato_S1.mp4 (148 rutor, 29,97 fps).
Pris före körning: 0,03 USD/s i 540p (api.fal.ai/v1/models/pricing), 5 s = 0,15 USD.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'fal'))
import falapi

HIT = Path(__file__).resolve().parent; LA = HIT / 'luma-agaren'


def main():
    v = sys.argv[1]; ut = HIT / 'd_video' / v; ut.mkdir(parents=True, exist_ok=True)
    p = (LA / 'PROMPT.txt').read_text(encoding='utf-8').split('STEP 2 — VIDEO')[1].split('\n', 1)[1].strip()
    (ut / 'prompt.txt').write_text(p, encoding='utf-8')
    if v == 'a':
        ind = dict(video_url=falapi.ladda_upp(LA / '1_kalla_gelato_S1.mp4'), start_image_url=falapi.ladda_upp(HIT / 'nyckel/B_000_passad.png'),
                   prompt=p, resolution='540p', duration='5s')
    elif v == 'k':   # 0021 punkt 3: kamerafri, förgrundsfri källa (kamerafri/kamerafri.mp4), samma startbild, kort prompt
        p = ("Keep this exact performance: the same woman, the same movements, the same timing, frame by frame. "
             "Show her whole body from head to feet in every frame, standing on a plain light-grey floor in front of a plain light-grey background. "
             "Complete every part of her that is missing in the source: hips, legs, feet, forearms and hands, at the same scale. "
             "Her hands are empty. No other person, no other hands, no objects, no text. "
             "The camera is locked on a tripod and never moves, zooms or tilts.")
        (ut / 'prompt.txt').write_text(p, encoding='utf-8')
        ind = dict(video_url=falapi.ladda_upp(HIT / 'kamerafri/kamerafri.mp4'), start_image_url=falapi.ladda_upp(HIT / 'nyckel/B_000_passad.png'),
                   prompt=p, resolution='540p', duration='5s')
    else: raise ValueError(v)
    s = falapi.kor('luma/agent/ray/v3.2/video-to-video', ind, ut / 'anrop', f'D video variant {v}', 0.15, '0.03 USD/s x 5 s, 540p')
    url = (s.get('video') or {}).get('url') or s['videos'][0]['url']
    falapi.hamta(url, ut / 'isolerad.mp4'); print(ut / 'isolerad.mp4', falapi.summa().get('summa_fal_usd'))


if __name__ == '__main__': main()
