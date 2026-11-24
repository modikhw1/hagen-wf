"""0017 del A: skriver ../fal_modeller.md ur modeller_schema.json och pris_rad.json (hämtade ur fal:s plattforms-API)."""
import json
u = json.load(open('modeller_schema.json', encoding='utf-8')); P = {p['endpoint_id']: p for p in json.load(open('pris_rad.json'))['prices']}
slag = {'fal-ai/object-removal/mask': 'bild: maskad borttagning', 'fal-ai/qwen-image-edit/inpaint': 'bild: maskad inpainting', 'fal-ai/flux-kontext-lora/inpaint': 'bild: maskad inpainting + referens',
        'openai/gpt-image-2/edit': 'bild: instruktion, flera bilder, valfri mask', 'google/nano-banana-2.1/edit': 'bild: instruktion, flera bilder', 'fal-ai/nano-banana-pro/edit': 'bild: instruktion, flera bilder',
        'bytedance/seedream/v5.5/edit': 'bild: instruktion, flera bilder', 'luma/agent/uni-1/v1/edit': 'bild: instruktion + referensbilder',
        'luma/agent/ray/v3.2/video-to-video': 'video→video: startbild eller upp till 64 nyckelbilder', 'kling/v4/video-to-video/edit': 'video→video: start-, mitt-, slutbild',
        'fal-ai/kling-video/o3/standard/video-to-video/edit': 'video→video: referensbilder', 'fal-ai/kling-video/o1/video-to-video/edit': 'video→video: referensbilder',
        'fal-ai/wan/v2.7/edit-video': 'video→video: referensbild', 'blackforestlabs/flux-3/edit-video': 'video→video: bara prompt',
        'fal-ai/bytedance/dreamactor/v2': 'rörelseöverföring: bild + video', 'fal-ai/kling-video/v3/standard/motion-control': 'rörelseöverföring: bild + video',
        'fal-ai/wan-vace-14b/inpainting': 'maskstyrd video: maskvideo, första/sista ruta, referenser', 'fal-ai/wan-22-vace-fun-a14b/inpainting': 'maskstyrd video: maskvideo, första/sista ruta',
        'fal-ai/ltx-2.3-quality/inpaint': 'maskstyrd video: maskvideo', 'fal-ai/void-video-inpainting': 'maskstyrd video: mask eller maskprompt'}
rel = ('image_url', 'image_urls', 'mask_url', 'reference_image_url', 'reference_image_urls', 'video_url', 'video_urls', 'start_image_url', 'middle_image_urls', 'end_image_url', 'keyframes',
       'keyframe_indexes', 'first_frame_url', 'last_frame_url', 'mask_video_url', 'mask_image_url', 'ref_image_urls', 'quad_mask_video_url', 'mask_prompt', 'edit_strength', 'controls')
rad = ['# fal.ai: kandidater för generativ nedbrytning (uppdrag 0017)', '',
       'Hämtat 12 nov 2026 ur fal:s plattforms-API (`api.fal.ai/v1/models` med OpenAPI-schema och `/v1/models/pricing`), inte ur minnet. Råsvaren finns i `fal/modeller_schema.json` och `fal/pris_rad.json`. Status är fal:s egen flagga (active/deprecated). Längd och fps står bara där schemat anger dem.', '',
       '| Modell | Slag | Indata som styr | Pris | Längd | fps ut | Status |', '|---|---|---|---|---|---|---|']
for e, s in slag.items():
    f = u[e]['falt']; inn = ', '.join(k for k in rel if k in f)
    p = P.get(e); pris = f"{p['unit_price']} USD/{p['unit']}" if p else '?'
    if p and p['unit'] == 'units': pris += ' (enheten anges inte i API:t)'
    langd = f.get('duration', {}).get('enum') or (f"num_frames max {f['num_frames'].get('maximum')}" if 'num_frames' in f and f['num_frames'].get('maximum') else 'ej angivet')
    fps = f"standard {f['frames_per_second'].get('default')}" if 'frames_per_second' in f else ('kan matcha källan' if 'match_input_frames_per_second' in f else 'ej angivet')
    rad.append(f"| `{e}` | {s} | {inn} | {pris} | {langd} | {fps} | {u[e]['meta']['status']} |")
rad += ['', 'Ingen av kandidaterna är flaggad för borttagning. Den äldre `fal-ai/wan-vace` är `deprecated` och ersätts av `fal-ai/wan-vace-14b`.',
        '', '**Val för provet** (pris kontrollerat före körning):',
        '- B: maskad `fal-ai/object-removal/mask` (0,006 USD per bild) och promptad `luma/agent/uni-1/v1/edit` (0,003 USD per bild).',
        '- C: `luma/agent/uni-1/v1/edit` med originalet och den tomma scenen som referenser.',
        '- D: `luma/agent/ray/v3.2/video-to-video` i 540p (0,03 USD per sekund, alltså 0,15 USD för 5 s), med `start_image_url` eller `keyframes`/`keyframe_indexes`.',
        '', 'Ägarens Luma-recept (Ray 3.2 Modify med första rutan låst) finns alltså på fal, och där går det dessutom att låsa fler nyckelbilder.']
open('../fal_modeller.md', 'w', encoding='utf-8').write('\n'.join(rad) + '\n'); print(len(rad))
