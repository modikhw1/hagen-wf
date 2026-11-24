"""0023: försöken mot en generering som följer originalet. Luma Ray 3.2 video-till-video på fal, 540p, 5 s (0,15 USD).

  scen/.venv/Scripts/python.exe scen/3d/gennedbrytning/d2_video.py <variant>
Varje variant ändrar en sak mot den förra. Prompt och indata sparas i d_video/<variant>/. Kör aldrig om en variant (falapi spärrar).
k2  = källa kamerafri_k2/k2.mp4 (kamerafri, originalets pixlar kvar, kundens hand grå), startbild kamerafri_k2/nyckel/kf_000.png,
      prompten P_ANTAGEN (borttagning + antagandet + rörelsen i tid).
k2s = som k2 med P_FOREMAL (0024: skeden stannar i handen). k2sn = som k2s med nyckelbilder vid 0, 55, 94, 136.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'fal'))
import falapi

HIT = Path(__file__).resolve().parent; K2 = HIT / 'kamerafri_k2'

P_ANTAGEN = (
    "Remove the ice-cream display counter, the glass, the ice-cream tubs, the shop interior, the on-screen text and the customer's hand. "
    "Keep only the woman, with exactly the same movements and timing as in the source, frame by frame. "
    "She stands on a plain light-grey floor in front of a plain light-grey background, and her whole body from head to feet is visible in every frame. "
    "She stands in the same spot the whole time: her feet stay still and her legs stay straight. When she leans forward she bends at the hips. "
    "Her hands are empty and there is nothing in front of her. The camera is locked and never moves, zooms or tilts. "
    "Timing: 0.0-0.8 s she stands upright and looks down. 0.8-1.5 s she bends forward at the hips and reaches down low in front of her with her right arm. "
    "1.5-2.4 s she stays bent forward, right arm stretched down. 2.4-3.1 s she straightens up and brings her right hand to her chest. "
    "3.1-3.8 s she stretches her right arm straight forward towards the camera, palm up. 3.8-4.9 s she keeps the arm stretched towards the camera and smiles."
)

# 0024 punkt 1: lager 2 är kvinnan med det hon håller. Inga "tomma händer". Kundens hand och disken ska fortfarande bort.
P_FOREMAL = (
    "Remove the ice-cream display counter, the glass, the ice-cream tubs, the shop interior, the on-screen text and the customer's hand. "
    "Keep the woman and the small tasting spoon she holds in her right hand, with exactly the same movements and timing as in the source, frame by frame. "
    "She stands on a plain light-grey floor in front of a plain light-grey background, and her whole body from head to feet is visible in every frame. "
    "She stands in the same spot the whole time: her feet stay still and her legs stay straight. When she leans forward she bends at the hips. "
    "The only thing in her hands is the small spoon; there is nothing in front of her. The camera is locked and never moves, zooms or tilts. "
    "Timing: 0.0-0.8 s she stands upright, looks down and holds the small spoon in her right hand, low in front of her. "
    "0.8-1.5 s she bends forward at the hips and lowers the spoon with her right arm. "
    "1.5-2.4 s she stays bent forward and scoops a small taste of ice cream onto the spoon. "
    "2.4-3.1 s she straightens up and lifts the spoon with the taste to her chest. "
    "3.1-3.8 s she stretches her right arm straight forward towards the camera, offering the spoon with the taste. "
    "3.8-4.9 s she keeps the arm stretched towards the camera, holding out the spoon, and smiles."
)


def variant(v):
    if v == 'k2':
        return dict(video_url=falapi.ladda_upp(K2 / 'k2.mp4'), start_image_url=falapi.ladda_upp(K2 / 'nyckel/kf_000.png'),
                    prompt=P_ANTAGEN, resolution='540p', duration='5s'), 'kamerafri källa med originalets pixlar, startbild kf_000, prompt med antagandet'
    if v == 'k2s':   # 0024 punkt 1, en ändring mot k2: prompten. Skeden och smakprovet stannar i handen ("tomma händer" struket)
        return dict(video_url=falapi.ladda_upp(K2 / 'k2.mp4'), start_image_url=falapi.ladda_upp(K2 / 'nyckel/kf_000.png'),
                    prompt=P_FOREMAL, resolution='540p', duration='5s'), 'som k2, prompten P_FOREMAL: skeden och smakprovet stannar i hennes hand'
    if v == 'k2sn':  # en ändring mot k2s: nyckelbilder i stället för startbild. Ruta 0 och 55 saknar skeden tills ägarens GPT-bilder finns (NASTA-BILDER.md)
        R = [0, 55, 94, 136]; nk = lambda r: K2 / f'nyckel/kf_{r:03d}_sked.png' if (K2 / f'nyckel/kf_{r:03d}_sked.png').exists() else K2 / f'nyckel/kf_{r:03d}.png'
        return dict(video_url=falapi.ladda_upp(K2 / 'k2.mp4'), keyframes=[falapi.ladda_upp(nk(r)) for r in R],
                    keyframe_indexes=R, prompt=P_FOREMAL, resolution='540p', duration='5s'), 'som k2s, nyckelbilder vid rutorna 0, 55, 94, 136'
    raise ValueError(v)


def main():
    v = sys.argv[1]; ut = HIT / 'd_video' / v; ut.mkdir(parents=True, exist_ok=True)
    ind, vad = variant(v)
    (ut / 'prompt.txt').write_text(ind['prompt'], encoding='utf-8')
    (ut / 'variant.json').write_text(json.dumps(dict(variant=v, andring=vad, indata={k: x for k, x in ind.items() if k != 'prompt'}), ensure_ascii=False, indent=1), encoding='utf-8')
    s = falapi.kor('luma/agent/ray/v3.2/video-to-video', ind, ut / 'anrop', f'0023 video {v}', 0.15, '0.03 USD/s x 5 s, 540p')
    url = (s.get('video') or {}).get('url') or s['videos'][0]['url']
    falapi.hamta(url, ut / 'isolerad.mp4'); print(ut / 'isolerad.mp4', falapi.summa().get('summa_fal_usd'))


if __name__ == '__main__': main()
