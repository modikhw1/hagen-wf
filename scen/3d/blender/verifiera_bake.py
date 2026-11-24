"""End-to-end acceptance: blender -b --python scen/3d/blender/verifiera_bake.py

Uses the real evaluated/keyframed Blender objects, all 383 frames for joints,
mouth/face and visibility, and three native Workbench renders per shot.
Verification-only occluders reproduce the player's mask's depth test.
"""
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from importera_bake import CONV, importera, mat, mesh_object, trs

OUT = HERE / 'verifiering'
JOINTS = {'LeftArm': 11, 'RightArm': 12, 'LeftForeArm': 13, 'RightForeArm': 14,
          'LeftHand': 15, 'RightHand': 16, 'LeftUpLeg': 23, 'RightUpLeg': 24, 'Head': None}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def src_at(shot, local):
    knots = shot['source'].get('knots')
    if not knots:
        source = shot['source']
        return source['inSec'] + local / shot['duration'] * (source['outSec'] - source['inSec'])
    if local <= knots[0][0]:
        return knots[0][1]
    for (l0, s0), (l1, s1) in zip(knots, knots[1:]):
        if local <= l1:
            return s0 + (local - l0) / max(1e-6, l1 - l0) * (s1 - s0)
    return knots[-1][1]


def timeline_checks(bake, spec):
    duration = sum(s['duration'] for s in spec['shots'])
    expected_n = math.floor(duration * 30 + .5)
    assert bake['fps'] == 30 and bake['N'] == expected_n
    assert [f['i'] for f in bake['frames']] == list(range(expected_n))
    assert all(f['t'] == f['i'] / 30 for f in bake['frames'])
    assert all(f['audioMode'] == 'original' for f in bake['frames'])
    assert all(r['pass'] for r in bake['regression']) and not bake['errors'] and not bake['externalRequests']
    assert all(sha(ROOT / p) == h for p, h in bake['fingerprints'].items()), 'Inputs changed; rerun baka.mjs'
    assert sha(HERE / bake['assets']) == bake['assetsSha256'], 'Geometry changed; rerun baka.mjs'
    def at(t):
        start = 0
        for s in spec['shots']:
            if t < start + s['duration'] - 1e-7:
                return s, start
            start += s['duration']
        return spec['shots'][-1], start - spec['shots'][-1]['duration']
    for probe in bake['shotAt']:
        s, start = at(probe['t'])
        assert probe['shot'] == s['id'] and abs(start - probe['start']) < 1e-12
    audio_errors, source_errors, mvp_errors, boundaries = [], [], [], []
    for f in bake['frames']:
        s, start = at(f['t'])
        assert s['id'] == f['shot'] == bake['shotAt'][f['i']]['shot']
        local = f['t'] - start
        source = src_at(s, local)
        audio = source if s['source'].get('knots') else s['audioRange'][0] + local / s['duration'] * (s['audioRange'][1] - s['audioRange'][0])
        source_errors.append(abs(source - f['sourceT']))
        audio_errors.append(abs(audio - f['audioTime']))
        # Exactly the linear source interval used by mvp_render.py --original.
        mvp = s['source']['inSec'] + local / s['duration'] * (s['source']['outSec'] - s['source']['inSec'])
        mvp_errors.append(abs(audio - mvp) if not s.get('tyst') else 0)
    for shot in spec['shots']:
        frames = [f for f in bake['frames'] if f['shot'] == shot['id']]
        first, last = frames[0], frames[-1]
        boundaries.append(dict(shot=shot['id'], first=first['i'], last=last['i'], count=len(frames),
                               first_source_s=first['sourceT'], last_source_s=last['sourceT'],
                               first_shotAt=bake['shotAt'][first['i']]['shot'], last_shotAt=bake['shotAt'][last['i']]['shot']))
    audio_info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(ROOT / spec['audio'])], text=True))
    result = dict(N=expected_n, contiguous=True, fps=30, scene_duration_s=duration, baked_duration_s=expected_n / 30,
                  duration_error_s=abs(expected_n / 30 - duration), mvp_frame_count=int(duration * 30),
                  audio_file=spec['audio'], audio_file_duration_s=float(audio_info['format']['duration']),
                  audio_mapping_max_error_s=max(audio_errors), source_mapping_max_error_s=max(source_errors),
                  mvp_linear_mapping_max_error_s=max(mvp_errors), cuts=boundaries,
                  note='mvp_render.py uses linear source intervals, not piecewise source.knots; mismatch is a failure if present.')
    result['source_audio_tail_shortfall_s'] = max(0, max(s['audioRange'][1] for s in spec['shots']) - result['audio_file_duration_s'])
    result['last_sample_audio_s'] = bake['frames'][-1]['audioTime']
    result['audio_tail_note'] = 'The existing M4A is shorter than the mapped interval by less than one frame; every sampled audioTime is inside the source. No retiming was introduced.'
    result['pass'] = (max(audio_errors + source_errors + mvp_errors) < 1e-7 and
                      result['duration_error_s'] <= .5 / 30 and result['mvp_frame_count'] == expected_n and
                      max(s['audioRange'][1] for s in spec['shots']) <= result['audio_file_duration_s'] + 1 / 30)
    return result


def camera_for(scene, frame):
    camera = scene.camera
    camera.matrix_world = CONV @ mat(frame['camera']['matrix'])
    camera.data.sensor_fit = 'VERTICAL'
    camera.data.sensor_height = 32
    camera.data.lens = 16 / math.tan(math.radians(frame['camera']['fov']) / 2)
    camera.data.clip_start = frame['camera']['near']
    camera.data.clip_end = frame['camera']['far']
    bpy.context.view_layer.update()


def main():
    began = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    if not (HERE / 'bake.json').exists():
        subprocess.run(['node', str(HERE / 'baka.mjs')], check=True, cwd=ROOT)
    bake = json.loads((HERE / 'bake.json').read_text(encoding='utf-8'))
    spec = json.loads((ROOT / 'scen3d.json').read_text(encoding='utf-8'))
    assets = json.loads((HERE / bake['assets']).read_text(encoding='utf-8'))
    timeline = timeline_checks(bake, spec)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    actors = importera(HERE / 'bake.json', ROOT / 'scen3d.json')
    scene = bpy.context.scene
    assert scene.frame_start == 0 and scene.frame_end == bake['N'] - 1
    # Save the actor-only integration artifact before adding verification cameras/occluders.
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'bake.blend'))
    cam = bpy.data.objects.new('verification:camera', bpy.data.cameras.new('verification:camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = bake['width'], bake['height']
    scene.render.resolution_percentage = 100
    frame_results = []
    for f in bake['frames']:
        scene.frame_set(f['i'])
        camera_for(scene, f)
        graph = bpy.context.evaluated_depsgraph_get()
        joint_errors, bone_errors, mouth_errors, face_errors, projected_errors = [], [], [], [], []
        mouth_scales, mouth_apertures, mouth_values = [], [], []
        visibility_errors = []
        for aid, value in f['actors'].items():
            actor = actors[aid]
            for obj in actor['objects']:
                expected = value['visible']
                if expected and (obj == actor['face'] or obj in actor['parts'].values()):
                    expected = value['face']['visible']
                if expected and obj in actor['parts'].values():
                    name = next(n for n, o in actor['parts'].items() if o == obj)
                    expected = value['face']['parts'][name]['visible']
                if obj.hide_render != (not expected) or obj.hide_viewport != (not expected):
                    visibility_errors.append(obj.name)
            if not value['visible']:
                continue
            rig = actor['armature'].evaluated_get(graph)
            for name, bone in actor['bones'].items():
                evaluated = rig.pose.bones[bone.name]
                actual = rig.matrix_world @ evaluated.head
                expected = CONV @ mat(value['bones'][name]['world']).translation
                error = (actual - expected).length
                bone_errors.append(error)
                if name in JOINTS:
                    joint_errors.append(error)
                    j = JOINTS[name]
                    if aid == f['mainActor'] and j is not None:
                        uv = world_to_camera_view(scene, cam, actual)
                        projected_errors.append(float(np.linalg.norm(np.array((uv.x * bake['width'], (1 - uv.y) * bake['height'])) - np.array(f['joints'][j][:2]))))
            head_gl = mat(value['bones']['Head']['world'])
            for name, obj in actor['parts'].items():
                actual = obj.evaluated_get(graph)
                expected = value['face']['parts'][name]
                local_error = float(np.max(np.abs(np.asarray(actual.matrix_basis) - np.asarray(trs(expected)))))
                world_expected = CONV @ head_gl @ trs(value['face']) @ trs(expected)
                world_error = float(np.max(np.abs(np.asarray(actual.matrix_world) - np.asarray(world_expected))))
                face_errors.append(max(local_error, world_error))
                if name == 'mouth':
                    mouth_scales.append(max(abs(actual.scale[k] - expected['scale'][k]) for k in range(3)))
                    mouth_apertures.append(abs(2 * actual.scale.y - 2 * expected['scale'][1]))
                    mouth_values.append(abs(actor['root']['mouthOpen'] - value['mouthOpen']))
                    mouth_errors.extend([max(abs(actual.scale[k] - expected['scale'][k]) for k in range(3)),
                                         abs(actor['root']['mouthOpen'] - value['mouthOpen']), world_error])
            if aid == f['mainActor']:
                nose = actor['face'].evaluated_get(graph).matrix_world @ Vector(assets['actors'][aid]['faceLandmarks']['nose'])
                uv = world_to_camera_view(scene, cam, nose)
                projected_errors.append(float(np.linalg.norm(np.array((uv.x * bake['width'], (1 - uv.y) * bake['height'])) - np.array(f['joints'][0][:2]))))
        frame_results.append(dict(i=f['i'], shot=f['shot'], joint_errors_m=joint_errors,
                                  bone_max_m=max(bone_errors), mouth_max_error=max(mouth_errors), face_max_error=max(face_errors),
                                  mouth_scale_max_error=max(mouth_scales), mouth_aperture_max_error_m=max(mouth_apertures), mouthOpen_max_error=max(mouth_values),
                                  projected_max_px=max(projected_errors), visibility_errors=visibility_errors))
        if f['i'] % 90 == 0:
            print(f'Checked frame {f["i"]}: joint {max(joint_errors)*1000:.6f} mm; mouth {max(mouth_errors):.3g}', flush=True)
    # These exact, black meshes exist only for verification. They retain normal
    # depth testing because #mode=mask blacks out occluders rather than hiding them.
    collection = bpy.data.collections.new('verification:occluders')
    scene.collection.children.link(collection)
    occluders = {}
    for oid, data in assets['occluders'].items():
        objects = []
        for index, mesh in enumerate(data['meshes']):
            obj = mesh_object(f'verification:{oid}:{index}', mesh, collection)
            obj.color = (0, 0, 0, 1)
            objects.append((obj, mat(mesh['matrix'])))
        occluders[oid] = objects
    scene.render.engine = 'BLENDER_WORKBENCH'
    shading = scene.display.shading
    shading.light, shading.color_type = 'FLAT', 'OBJECT'
    shading.show_shadows = shading.show_cavity = shading.show_specular_highlight = shading.show_object_outline = False
    shading.background_type, shading.background_color = 'WORLD', (0, 0, 0)
    scene.world = bpy.data.worlds.new('verification:black')
    scene.world.color = (0, 0, 0)
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure, scene.view_settings.gamma = 0, 1
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.display.render_aa = '8'
    for sample in bake['samples']:
        f = bake['frames'][sample['i']]
        scene.frame_set(f['i'])
        camera_for(scene, f)
        for aid, actor in actors.items():
            for obj in actor['objects']:
                obj.color = (1, 1, 1, 1) if aid == f['mainActor'] else (0, 0, 0, 1)
        for oid, objects in occluders.items():
            value = f['props'].get(oid, assets['occluders'][oid])
            for obj, local in objects:
                obj.matrix_world = CONV @ mat(value['matrix']) @ local
                obj.hide_render = obj.hide_viewport = not value['visible']
        scene.render.filepath = str(OUT / f'{f["shot"]}-{f["i"]:03d}-blender-mask.png')
        bpy.ops.render.render(write_still=True)
        print(f'Rendered {f["shot"]} frame {f["i"]}', flush=True)
    python = ROOT.parent / '.venv/Scripts/python.exe'
    subprocess.run([str(python), str(HERE / 'compare_masks.py')], check=True)
    masks = json.loads((OUT / 'mask-results.json').read_text(encoding='utf-8'))
    shots = []
    for shot in bake['shots']:
        fs = [f for f in frame_results if f['shot'] == shot['id']]
        errors = [e * 1000 for f in fs for e in f['joint_errors_m']]
        mask_results = [r for r in masks if r['shot'] == shot['id']]
        row = dict(shot=shot['id'], frames_checked=len(fs), joints_median_mm=float(np.median(errors)), joints_max_mm=max(errors),
                   all_bones_max_mm=max(f['bone_max_m'] for f in fs) * 1000,
                   mouth_max_error=max(f['mouth_max_error'] for f in fs), face_max_error=max(f['face_max_error'] for f in fs),
                   mouth_scale_max_error=max(f['mouth_scale_max_error'] for f in fs),
                   mouth_aperture_max_error_m=max(f['mouth_aperture_max_error_m'] for f in fs),
                   mouthOpen_max_error=max(f['mouthOpen_max_error'] for f in fs),
                   projected_max_px=max(f['projected_max_px'] for f in fs),
                   visibility_errors=sum(len(f['visibility_errors']) for f in fs),
                   iou_min=min(m['iou'] for m in mask_results), iou_mean=float(np.mean([m['iou'] for m in mask_results])),
                   mask_frames=[m['i'] for m in mask_results], image=f'verifiering/{shot["id"]}-comparison.png')
        row['pass'] = (row['joints_max_mm'] <= 5 and row['iou_min'] >= .9 and row['mouth_max_error'] < 1e-5 and
                       row['face_max_error'] < 1e-5 and row['visibility_errors'] == 0)
        shots.append(row)
    report = dict(schema='scen3d-bake-verification/1', passed=all(s['pass'] for s in shots) and timeline['pass'],
                  blender=bpy.app.version_string, timeline=timeline, shots=shots, masks=masks,
                  player_regression=dict(images=len(bake['regression']) * 2, pixel_identical=all(r['pass'] for r in bake['regression'])),
                  comparison='Evaluated Blender bone heads and bone-parented ellipsoids vs three.js world transforms; native Workbench vs original player mask including exact black depth occluders.',
                  uncertainties=['Validates faithful transfer of the player, not anatomical accuracy of the measured retarget.',
                                 'Guest motion is the player\'s static untracked background guest.',
                                 'Original M4A ends 20.658 ms before the mapped scene end, after the final sampled frame; the bake preserves the existing timing.',
                                 'mvp_render.py only supports linear audio intervals; edited source.knots are explicitly checked for mismatch.'],
                  bake_sha256=sha(HERE / 'bake.json'), seconds=time.perf_counter() - began, frames=frame_results)
    (HERE / 'verifiering-bake.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    for row in shots:
        print(f'{row["shot"]}: joints median/max {row["joints_median_mm"]:.6f}/{row["joints_max_mm"]:.6f} mm; IoU min/mean {row["iou_min"]:.5f}/{row["iou_mean"]:.5f}; mouth {row["mouth_max_error"]:.3g}; {"PASS" if row["pass"] else "FAIL"}', flush=True)
    print('ACCEPTANCE', 'PASS' if report['passed'] else 'FAIL', flush=True)
    if not report['passed']:
        raise AssertionError('Bake acceptance failed; see verifiering-bake.json')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)  # Blender otherwise reports exit 0 for an unhandled Python error.
