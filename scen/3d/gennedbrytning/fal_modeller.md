# fal.ai: kandidater för generativ nedbrytning (uppdrag 0017)

Hämtat 12 nov 2026 ur fal:s plattforms-API (`api.fal.ai/v1/models` med OpenAPI-schema och `/v1/models/pricing`), inte ur minnet. Råsvaren finns i `fal/modeller_schema.json` och `fal/pris_rad.json`. Status är fal:s egen flagga (active/deprecated). Längd och fps står bara där schemat anger dem.

| Modell | Slag | Indata som styr | Pris | Längd | fps ut | Status |
|---|---|---|---|---|---|---|
| `fal-ai/object-removal/mask` | bild: maskad borttagning | image_url, mask_url | 0.006 USD/images | ej angivet | ej angivet | active |
| `fal-ai/qwen-image-edit/inpaint` | bild: maskad inpainting | image_url, mask_url | 0.03 USD/megapixels | ej angivet | ej angivet | active |
| `fal-ai/flux-kontext-lora/inpaint` | bild: maskad inpainting + referens | image_url, mask_url, reference_image_url | 0.035 USD/megapixels | ej angivet | ej angivet | active |
| `openai/gpt-image-2/edit` | bild: instruktion, flera bilder, valfri mask | image_urls, mask_url | 1 USD/units (enheten anges inte i API:t) | ej angivet | ej angivet | active |
| `google/nano-banana-2.1/edit` | bild: instruktion, flera bilder | image_urls, video_url | 1 USD/units (enheten anges inte i API:t) | ej angivet | ej angivet | active |
| `fal-ai/nano-banana-pro/edit` | bild: instruktion, flera bilder | image_urls | 0.15 USD/images | ej angivet | ej angivet | active |
| `bytedance/seedream/v5.5/edit` | bild: instruktion, flera bilder | image_urls | 0.03 USD/units (enheten anges inte i API:t) | ej angivet | ej angivet | active |
| `luma/agent/uni-1/v1/edit` | bild: instruktion + referensbilder | image_url, reference_image_urls | 0.003 USD/images | ej angivet | ej angivet | active |
| `luma/agent/ray/v3.2/video-to-video` | video→video: startbild eller upp till 64 nyckelbilder | video_url, start_image_url, keyframes, keyframe_indexes, edit_strength, controls | 0.03 USD/seconds | ['5s', '10s'] | ej angivet | active |
| `kling/v4/video-to-video/edit` | video→video: start-, mitt-, slutbild | image_urls, video_url, video_urls, start_image_url, middle_image_urls, end_image_url | 0.157 USD/seconds | ej angivet | ej angivet | active |
| `fal-ai/kling-video/o3/standard/video-to-video/edit` | video→video: referensbilder | image_urls, video_url | 0.14 USD/seconds | ej angivet | ej angivet | active |
| `fal-ai/kling-video/o1/video-to-video/edit` | video→video: referensbilder | image_urls, video_url | 0.168 USD/seconds | ej angivet | ej angivet | active |
| `fal-ai/wan/v2.7/edit-video` | video→video: referensbild | reference_image_url, video_url | 0.1 USD/seconds | [0, 2, 3, 4, 5, 6, 7, 8, 9, 10] | ej angivet | active |
| `blackforestlabs/flux-3/edit-video` | video→video: bara prompt | video_url | 0.03 USD/seconds | ej angivet | ej angivet | active |
| `fal-ai/bytedance/dreamactor/v2` | rörelseöverföring: bild + video | image_url, video_url | 0.05 USD/seconds | ej angivet | ej angivet | active |
| `fal-ai/kling-video/v3/standard/motion-control` | rörelseöverföring: bild + video | image_url, video_url | 0.126 USD/seconds | ej angivet | ej angivet | active |
| `fal-ai/wan-vace-14b/inpainting` | maskstyrd video: maskvideo, första/sista ruta, referenser | video_url, first_frame_url, last_frame_url, mask_video_url, mask_image_url, ref_image_urls | 0.08 USD/seconds | num_frames max 241 | standard 16 | active |
| `fal-ai/wan-22-vace-fun-a14b/inpainting` | maskstyrd video: maskvideo, första/sista ruta | video_url, first_frame_url, last_frame_url, mask_video_url, mask_image_url, ref_image_urls | 0.1 USD/seconds | num_frames max 241 | standard 16 | active |
| `fal-ai/ltx-2.3-quality/inpaint` | maskstyrd video: maskvideo | video_url, mask_video_url | 0.0024075 USD/megapixels | num_frames max 481 | standard 24 | active |
| `fal-ai/void-video-inpainting` | maskstyrd video: mask eller maskprompt | video_url, quad_mask_video_url, mask_prompt | 0.05 USD/units (enheten anges inte i API:t) | num_frames max 197 | ej angivet | active |

Ingen av kandidaterna är flaggad för borttagning. Den äldre `fal-ai/wan-vace` är `deprecated` och ersätts av `fal-ai/wan-vace-14b`.

**Val för provet** (pris kontrollerat före körning):
- B: maskad `fal-ai/object-removal/mask` (0,006 USD per bild) och promptad `luma/agent/uni-1/v1/edit` (0,003 USD per bild).
- C: `luma/agent/uni-1/v1/edit` med originalet och den tomma scenen som referenser.
- D: `luma/agent/ray/v3.2/video-to-video` i 540p (0,03 USD per sekund, alltså 0,15 USD för 5 s), med `start_image_url` eller `keyframes`/`keyframe_indexes`.

Ägarens Luma-recept (Ray 3.2 Modify med första rutan låst) finns alltså på fal, och där går det dessutom att låsa fler nyckelbilder.
