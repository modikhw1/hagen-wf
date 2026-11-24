"""Package measured results and the explicit visual review; never edits artwork."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
shots = json.loads((HERE.parent/'tagningslista.json').read_text(encoding='utf-8'))['tagningar']
metrics = json.loads((HERE/'mask_metrics.json').read_text(encoding='utf-8'))
roles = dict(S1='A', S2='B', S3='A', S4='C', S5='B', S6='A', S7='B')
revisions = dict(S1=1, S2=1, S3=2, S4=1, S5=2, S6=1, S7=1)
visual = {
 'S1': dict(objects='Can left, cup left-center, fries behind, kraft bag rear-right, burger carton front-right, sauce right and tray retained. Bag corrected for continuity with S3/S6.', caveats=['Elbows and hair extend farther sideways than the mannequin; hair and fabric fill the mannequin waist gaps.', 'Fries extend above their blockout box; packaging outlines and sauce position are approximate.']),
 'S2': dict(objects='Cup left, burger center-left, sauce front-center, fries right; fry and gripping hand at right edge after correction.', caveats=['Sweater torso is straighter and forearm thicker than the mannequin.', 'Cup/carton/fries boundaries differ by several pixels; carton is open to expose food.']),
 'S3': dict(objects='Can, cup, fries, rear paper bag, front burger carton, sauce and tray retain relative locations. Added background person removed.', caveats=['Shoulders intentionally broadened to approach mannequin silhouette, so build is bulkier than neutral template.', 'Rear wrapping becomes a kraft bag; carton lid and sauce placement remain approximate.']),
 'S4': dict(objects='Staff stands looking right with terminal in upturned hand; generic seated guest at left and furniture retained. Added background food removed.', caveats=['Terminal is larger and rotated relative to the thin blockout slab.', 'Staff arm/leg widths and background guest pose differ from mannequin. YOLO instance count is not a reliable physical-person count.']),
 'S5': dict(objects='Cup left, sauce low-center, fries right and held burger carton upper-right retained. Added can removed; blockout props retextured.', caveats=['Held carton lid extends above blockout footprint and hand is simplified.', 'Forearm/torso outlines drift; IoU is only slightly above threshold.']),
 'S6': dict(objects='Can left, cup left-center, fries center, bag rear-right, burger front-right, sauce at right and tray retained. Extra tabletop hand removed.', caveats=['Head tilt and neck/shoulder proportions differ slightly.', 'Table edge and foreground package height drift; window remains opaque blue-grey unlike detailed backgrounds in S1/S3.']),
 'S7': dict(objects='Distant seated B, small food group, chair/table arrangement and large cropped can at bottom-right retained. Added raised fry gesture removed.', caveats=['Legs are straighter and slimmer than mannequin; small head/arm outlines differ.', 'Can is wider and starts slightly lower than blockout; small prop spacing differs. IoU is close to threshold.'])
}

# Exact input references in the order submitted to the built-in generator.
refs = {'A': [], 'B':['mallar/A.png'], 'C':['mallar/A.png'],
        'miljo':['../ut/forsta_S4.png','referenser/kalla_S4.png','mallar/A.png']}
for sid, role in roles.items():
    refs[sid] = [f'mallar/{role}.png', f'../ut/forsta_{sid}.png', f'referenser/kalla_{sid}.png']
refs.update({
 'S1_r1':['forsok/S1_v0.png','forsok/S6_r1.png'],
 'S2_r1':['../ut/forsta_S2.png','mallar/B.png','forsok/S2_v0.png'],
 'S3_r1':['forsok/S3_v0.png'],
 'S3_r2':['forsok/S3_r1.png','../ut/forsta_S3.png','masker/blockout_S3.png'],
 'S4_r1':['forsok/S4_v0.png'],
 'S5_r1':['../ut/forsta_S5.png','mallar/B.png','masker/blockout_S5.png'],
 'S5_r2':['forsok/S5_r1.png'],
 'S6_r1':['../ut/forsta_S6.png','mallar/A.png','masker/blockout_S6.png','forsok/S6_v0.png'],
 'S7_r1':['forsok/S7_v0.png','../ut/forsta_S7.png','masker/blockout_S7.png'],
})
manifest = []
for name, inputs in refs.items():
    prompt_path = HERE/'prompter'/f'{name}.txt'
    assert prompt_path.is_file()
    for inp in inputs: assert (HERE/inp).is_file(), inp
    manifest.append(dict(id=name,tool='image_gen.imagegen',transparent_background=False,
                         prompt_file=f'prompter/{name}.txt',prompt_sha256=sha(prompt_path),
                         referenced_image_paths=inputs))
(HERE/'generation_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

artifact_files = [HERE/'mallar'/f'{role}.png' for role in 'ABC'] + [HERE/'miljo.png'] + [HERE/f'forsta_S{i}.png' for i in range(1,8)]
artifacts = []
for p in artifact_files:
    with Image.open(p) as im:
        im.verify()
    with Image.open(p) as im:
        size = list(im.size)
    if p.parent != HERE/'mallar': assert size == [576,1024], (p,size)
    artifacts.append(dict(path=p.relative_to(HERE).as_posix(),dimensions=size,sha256=sha(p)))

for row, shot in zip(metrics['shots'], shots):
    sid = row['shot']
    assert sid == shot['id']
    assert row['image_sha256'] == sha(HERE/f'forsta_{sid}.png'), f'Stale metric: {sid}'
    assert round(shot['kalla_s'][0]*30) == shot['bildrutor'][0], 'Existing extracted frame no longer matches source time'
    assert revisions[sid] <= 3
    for p in [f'kontroll_{sid}.jpg',f'masker/blockout_{sid}.png',f'masker/ps2_{sid}.png',f'masker/overlap_{sid}.png']:
        with Image.open(HERE/p) as im: im.verify()
    row.update(role=roles[sid],source_time_s=shot['kalla_s'][0],source_frame=round(shot['kalla_s'][0]*30),
               image=f'forsta_{sid}.png',triptych=f'kontroll_{sid}.jpg',regenerations=revisions[sid],
               final_prompt=f'prompter/{sid}_r{revisions[sid]}.txt',
               object_position_review=visual[sid]['objects'],remaining_deviations=visual[sid]['caveats'],
               exact_layout=False,template_consistency='Same invented face/hair/outfit visually retained; pose-related body proportion drift remains.',
               likeness_review='Visual review: no obvious source-person identity reproduced; generic faces designed independently in templates.',
               logos_or_text_observed=False,style_review='Consistent low-poly PS2 characters, painted textures and game props.')

result = dict(created_at=datetime.now().astimezone().isoformat(),generator='Built-in image_gen.imagegen only; no API/CLI generation.',
    normalization='Generated portrait PNGs normalized to 576x1024 by ffmpeg scale. No crop, perspective warp or manual retouching.',
    acceptance=dict(templates_3=True,environment_1=True,keyframes_7=True,triptychs_7=True,
                    all_person_iou_at_least_0_7=all(r['pass_iou'] for r in metrics['shots']),
                    consistent_ps2_style_visual_review=True,no_obvious_real_likeness_visual_review=True,
                    no_logos_or_text_in_generated_assets_visual_review=True,max_three_regenerations_per_shot=True,
                    exact_composition_and_objects=False),
    overall='Deliverables and numeric/visual acceptance checks complete; exact pixel-level composition is not achieved. Residual deviations disclosed per shot.',
    method=metrics,artifacts=artifacts,
    environment_review='S4 low-angle direction, dark tables, white walls, left window wall, pendant lamp and rear counter are present. Empty-room layout and added ceiling ducts are interpreted, not a calibrated Blender-camera render.',
    limitations=['YOLO is a proxy segmenter trained on photographs; stylized clothing, table occlusion and duplicate/partial instances affect masks. Raw union of all class-0 masks is used, with no hand corrections.',
                 'S5 and S7 clear 0.70 narrowly. Passing IoU does not establish exact hands, object edges, face expression or environment geometry.',
                 'Generic faces pass visual comparison only; this is not a biometric proof of absence of likeness.',
                 'Original source frames and source panels intentionally retain real people, source branding and subtitles for QA. They are diagnostic references, not generated deliverables.',
                 'S1/S3 have detailed views through glazing whereas S6 has opaque blue-grey glazing. Same PS2 art treatment, imperfect environment continuity.'])
(HERE/'kontroll.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')

template_readme = ['# PS2 character templates','',
 'Built-in `image_gen.imagegen`; three views (front, three-quarter, side), neutral pose, plain background. A was generated without images; B and C used A solely as the rendering-style reference. No source portraits were supplied for template creation. C has a blank red fabric patch, without branding.', '',
 'Use the appropriate sheet as **IMAGE 1 = MAIN CHARACTER REFERENCE**. These are independently invented characters. Exact prompts follow; the original text files are also in `../prompter/`.', '']
for role in 'ABC':
    template_readme += [f'## {role} — `{role}.png`','', '```text', (HERE/'prompter'/f'{role}.txt').read_text(encoding='utf-8').strip(), '```','']
(HERE/'mallar/README.md').write_text('\n'.join(template_readme),encoding='utf-8')

report = ['# PS2-mallar — report','',
 'Created with the built-in image generator: **3 character sheets, 1 environment frame and 7 keyframes**. All keyframes/environment are 576×1024; sheets are 1536×1024. All seven final person-mask IoUs meet 0.70. Visual review found a consistent PS2 treatment and no obvious source likeness, real logos or text in the generated assets. Exact composition still has the deviations below.', '',
 '| Shot | IoU | Regenerations | Remaining layout/prop deviations |','|---|---:|---:|---|']
for row in metrics['shots']:
    report.append(f"| {row['shot']} | {row['iou']:.6f} | {row['regenerations']} | {' '.join(row['remaining_deviations'])} |")
report += ['', '**Prompts:** exact character prompts in [mallar/README.md](mallar/README.md); every initial and revision prompt in [prompter/](prompter/), with ordered input references in [generation_manifest.json](generation_manifest.json). 20 image-generation calls total; no shot exceeded two regenerations.', '',
 '**Paths:** `mallar/A.png`, `B.png`, `C.png`; `miljo.png`; `forsta_S1.png`–`forsta_S7.png`; [kontroll.json](kontroll.json); `kontroll_S1.jpg`–`kontroll_S7.jpg` (source | blockout | PS2); `masker/` contains both masks and overlap images.', '',
 '**Verification:** Blender 5.2 Workbench renders the visible `bakade_aktorer` collection white, with set/prop occluders black, using each shot camera and first frame from `scen.blend`. YOLO `yolo11n-seg.pt`, person class 0, confidence 0.25, image size 1024, retina masks; union IoU, no alignment/dilation/manual correction. Model and image SHA-256 hashes, mask areas and raw detections are recorded. The mapped source frames are 0, 73, 114, 171, 256, 281 and 337, matching `kalla_s` at 30 fps.', '',
 '**Remaining failures/limits:** exact silhouette/pose/prop geometry is not achieved; the table lists drift. S5/S7 pass narrowly. The environment frame interprets the empty S4 room; S6 glazing differs from S1/S3. Generic identity and absence of branding were checked visually, not biometrically. Raw YOLO detections can overlap or split a visible person. Source-reference files and source panels retain original people, logos and captions for comparison only.', '',
 '**Reproduce checks from repo root:**', '```powershell',
 "& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -b scen/3d/blender/scen.blend --python scen/3d/blender/ps2/render_masks.py",
 'scen/.venv/Scripts/python.exe scen/3d/blender/ps2/check_masks.py',
 'scen/.venv/Scripts/python.exe scen/3d/blender/ps2/finalize.py', '```','']
(HERE/'RAPPORT.md').write_text('\n'.join(report),encoding='utf-8')
print(json.dumps(dict(artifacts=len(artifacts),shots=len(metrics['shots']),minimum_iou=min(r['iou'] for r in metrics['shots']),all_iou_pass=result['acceptance']['all_person_iou_at_least_0_7'],generation_calls=len(manifest),max_regenerations=max(revisions.values())),indent=2))
