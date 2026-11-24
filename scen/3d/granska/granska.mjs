// Gemini as an artifact critic for the Blender pre-render.
// Sends the source clip, the render alone, and the 3-panel comparison (source | overlay | render)
// and asks for a structured, time-stamped list of every artifact that blocks a faithful 1:1 pre-render.
//
//   node scen/3d/granska/granska.mjs <ut-dir> <source.mp4> [--modell gemini-3.1-pro-preview] [--fps 10] [--nyckel GEMINI_API_KEY_GRATIS] [--tag a]
//
// Output: <ut-dir>/granska/fynd_<modell>_<tag>.json (+ raw response). Keys are never printed or written.
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (n, d) => { const i = args.indexOf('--' + n); return i >= 0 ? args[i + 1] : d; };
const [utDir, source] = args.filter((a, i) => !a.startsWith('--') && !(i > 0 && args[i - 1].startsWith('--')));
if (!utDir || !source) throw Error('usage: granska.mjs <ut-dir> <source.mp4> [--modell m] [--fps n]');
const model = opt('modell', 'gemini-3.1-pro-preview');
const fps = Number(opt('fps', '10'));
const keyName = opt('nyckel', 'GEMINI_API_KEY_GRATIS');
const tag = opt('tag', 'a');

const envText = fs.readFileSync(path.resolve(here, '../../../video/.env.local'), 'utf8');
const line = envText.split(/\r?\n/).find(s => s.startsWith(keyName + '='));
if (!line) throw Error('credential unavailable: ' + keyName);
const key = line.slice(line.indexOf('=') + 1).trim().replace(/^['"]|['"]$/g, '');

const outDir = path.join(utDir, 'granska');
fs.mkdirSync(outDir, {recursive: true});

// Render-only video from the PNG frames, with the source audio so both videos share a clock.
const meta = JSON.parse(fs.readFileSync(path.join(utDir, 'meta.json'), 'utf8'));
const renderMp4 = path.join(outDir, 'render.mp4');
if (!fs.existsSync(renderMp4)) {
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(meta.fps), '-i', path.join(utDir, 'render', 'f%04d.png'),
    '-i', source, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-shortest', renderMp4]);
}
const jamfor = path.join(utDir, 'jamforelse.mp4');
const tider = fs.existsSync(path.join(utDir, 'tider.json')) ? fs.readFileSync(path.join(utDir, 'tider.json'), 'utf8') : '{}';

const pipeline = `
PIPELINE THAT PRODUCED THE RENDER (each stage is cached; attribute each artifact to the most likely stage):
- personer: YOLO11-seg person masks + BoT-SORT tracking with ReID, track fragments merged into stable person IDs.
- kamera: COLMAP structure-from-motion on every 3rd frame with persons masked out; SIMPLE_RADIAL intrinsics; poses slerped between registered frames. Focal length is weakly constrained under low parallax (known run-to-run variance 1658 vs 2154 px).
- kropp: SAM 3D Body (ViT-H, Meta) per frame per person, output = MHR body model params (127 joints, 45 shape, 72 expression, 108 hand params) in the camera frame.
- sekvens: identity (shape) locked to the median; root rotation unwrapped; Hampel filter (+-4 frames, 3*MAD) replaces broken frames (e.g. upside-down fits); occluded legs (knee not visible / inside another mask) held from nearest visible frame or set to neutral standing; zero-phase Butterworth 6 Hz body, 8 Hz hands/face.
- varld: camera path x person-in-camera -> metric world; scale k chosen to minimise root-trajectory roughness; gravity from spine directions.
- golv: each person slid along the camera ray until the lowest foot touches the floor; floor from visible feet, else assumed camera height 1.45 m; scale smoothed at 1.5 Hz.
- rum: (not built yet) no room geometry, no furniture, no props. Only a flat floor exists.
- blender: MHR lod3.fbx rig keyed directly (no retargeting), keyed camera from COLMAP, Workbench flat render, no facial expression applied yet, no clothes/hair.
- jamfor: ffmpeg 3-panel composite.
Stage metrics from this run (tider.json): ${tider.replace(/\s+/g, ' ')}
`;

const prompt = `You are a senior motion-capture cleanup artist and 3D layout supervisor reviewing a pre-visualisation.
GOAL: the Blender pre-render must reproduce the SOURCE clip 1:1 (camera, body placement, body motion, weight, contacts, scene objects), because it is used as the motion/layout reference for a video model. Stylisation is NOT the goal; fidelity and natural, weighted, smooth motion are.

You get three videos with the same clock (${meta.fps} fps source, ${meta.N} frames):
  VIDEO 1 = SOURCE (real footage).
  VIDEO 2 = RENDER (grey MHR mannequins, flat floor, keyed camera).
  VIDEO 3 = COMPARISON: left = source, middle = render overlaid on source, right = render.
${pipeline}
TASK: List EVERY visible artifact that makes the render diverge from the source or look physically wrong. Be extremely specific and technical. For each:
- exact time window in seconds (start_s, end_s, 0.1 s precision) and the frame range at ${meta.fps} fps;
- which person (describe by position/clothing in the SOURCE, e.g. "woman in black jacket, left") and which body part / joint chain (e.g. "right forearm + wrist", "pelvis root", "left foot", "head yaw");
- category from the enum;
- what the SOURCE shows vs what the RENDER shows, in measurable terms where possible (approx degrees, cm, px in the 3-panel, frames of lag, direction of error);
- the most likely pipeline stage at fault and a concrete technical hypothesis (e.g. "Hampel window too short so a 3-frame flip survives", "Butterworth 6 Hz over-smooths a 0.2 s clap peak", "COLMAP pose interpolation drift between registered frames", "root depth from monocular fit oscillates, scale k amplifies it", "occluded legs held -> foot skate");
- a concrete fix (parameter change, constraint, extra signal, or tool);
- severity 1-5 (5 = blocks using the render as a reference), and your confidence 0-1.
Also judge holistically: does the motion have weight (pelvis/COM follows foot plants, ground contact, anticipation/follow-through), or does it float, slide, snap, or jitter? Does the camera move identically to the source (pan/tilt/dolly/handheld shake magnitude and timing)? Do body scale and depth relative to the camera look right? Are there missing scene objects the bodies interact with or are occluded by?
Mark findings that only follow from a known, deliberate limitation (no room/props yet, no facial expressions, no hair/clothes) with known_limitation=true, but still report them if they affect occlusion, contact or weight.
Do not invent artifacts: if a body part matches, say nothing about it. Prefer many precise findings over vague ones. Write in English.`;

const S = (description) => ({type: 'STRING', description});
const schema = {
  type: 'OBJECT',
  properties: {
    overall: {
      type: 'OBJECT',
      properties: {
        verdict: S('2-4 sentences: how usable the render is as a 1:1 reference and the single biggest blocker'),
        weight_and_physics: S('does the motion carry weight; specifics'),
        smoothness: S('jitter / snapping / flips / over-smoothing; specifics'),
        camera_match: S('camera motion vs source; specifics'),
        scale_depth_placement: S('body size, depth, floor contact vs source'),
        scene_objects_missing: {type: 'ARRAY', items: S('object the bodies interact with or are occluded by')},
      },
      required: ['verdict', 'weight_and_physics', 'smoothness', 'camera_match', 'scale_depth_placement', 'scene_objects_missing'],
    },
    findings: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        properties: {
          start_s: {type: 'NUMBER'}, end_s: {type: 'NUMBER'},
          start_frame: {type: 'INTEGER'}, end_frame: {type: 'INTEGER'},
          person: S('who, as seen in the source'),
          body_part: S('joint chain or object'),
          category: {type: 'STRING', enum: ['jitter', 'flip_or_snap', 'foot_skate', 'floating_or_sinking', 'no_weight', 'over_smoothed', 'pose_mismatch', 'hand_or_finger', 'head_or_gaze', 'timing_lag', 'depth_or_scale', 'placement_drift', 'interpenetration', 'occlusion_wrong', 'missing_object', 'camera_mismatch', 'identity_or_swap', 'face_expression', 'other']},
          source_shows: S('what the source shows'),
          render_shows: S('what the render shows, measurable where possible'),
          stage: {type: 'STRING', enum: ['personer', 'kamera', 'kropp', 'sekvens', 'varld', 'golv', 'rum', 'blender', 'unknown']},
          hypothesis: S('technical cause'),
          fix: S('concrete fix'),
          severity: {type: 'INTEGER'}, confidence: {type: 'NUMBER'},
          known_limitation: {type: 'BOOLEAN'},
        },
        required: ['start_s', 'end_s', 'start_frame', 'end_frame', 'person', 'body_part', 'category', 'source_shows', 'render_shows', 'stage', 'hypothesis', 'fix', 'severity', 'confidence', 'known_limitation'],
      },
    },
    priorities: {type: 'ARRAY', items: S('ordered list: what to fix first and why (reference finding indices)')},
  },
  required: ['overall', 'findings', 'priorities'],
};

const vid = (file) => ({inline_data: {mime_type: 'video/mp4', data: fs.readFileSync(file).toString('base64')}, video_metadata: {fps}});
const body = {
  contents: [{role: 'user', parts: [
    {text: 'VIDEO 1 = SOURCE'}, vid(source),
    {text: 'VIDEO 2 = RENDER'}, vid(renderMp4),
    {text: 'VIDEO 3 = COMPARISON (source | overlay | render)'}, vid(jamfor),
    {text: prompt},
  ]}],
  generationConfig: {responseMimeType: 'application/json', responseSchema: schema, temperature: 0.2, maxOutputTokens: 32000},
};
const t0 = performance.now();
let res, raw;
for (let forsok = 1; ; forsok++) {
  res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
    method: 'POST', headers: {'content-type': 'application/json', 'x-goog-api-key': key},
    body: JSON.stringify(body), signal: AbortSignal.timeout(600000),
  });
  raw = await res.text();
  // 503 = overloaded, retry; 429 with limit 0 = model not in this tier, give up.
  if (res.status !== 503 || forsok >= 8) break;
  console.error(`503, retry ${forsok} in ${15 * forsok}s`);
  await new Promise(r => setTimeout(r, 15000 * forsok));
}
const stem = `fynd_${model}_${tag}`;
fs.writeFileSync(path.join(outDir, stem + '.raw.json'), raw);
if (!res.ok) { console.error('HTTP', res.status, raw.slice(0, 600)); process.exit(1); }
const j = JSON.parse(raw);
const text = (j.candidates?.[0]?.content?.parts || []).filter(p => !p.thought).map(p => p.text || '').join('');
const data = JSON.parse(text);
data.findings.sort((a, b) => b.severity - a.severity || a.start_s - b.start_s);
const out = {model, fps, sek: Math.round((performance.now() - t0) / 100) / 10, usage: j.usageMetadata, source: path.basename(source), ...data};
fs.writeFileSync(path.join(outDir, stem + '.json'), JSON.stringify(out, null, 2));
console.log(`${path.basename(utDir)} ${model}: ${data.findings.length} findings in ${out.sek}s, tokens in ${j.usageMetadata?.promptTokenCount} out ${j.usageMetadata?.candidatesTokenCount}`);
console.log(data.overall.verdict);
