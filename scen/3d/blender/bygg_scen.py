"""Scen3D -> Blender (förvisualisering). JSON in, Blender-scen ut.

Bygger rum (set), rekvisita, en kamera per tagning med klipp på exakt samma bildrutor som three.js-spelaren,
originalljudet mappat per tagning (som mvp_render.py), och en tagningslista för prompten.
Rörelsen (X Bot-dockorna) bakas av Codex i bake.json och läses in av importera_bake.py om den finns.

Kör (bakgrund): blender -b --factory-startup --python scen/3d/blender/bygg_scen.py -- [--scen scen3d.json] [--spara ut.blend]
Kör (live via MCP): exec(open(r'...\\bygg_scen.py', encoding='utf-8').read(), {'__name__': '__main__', 'ARGV': []})
"""
import json, math, sys, subprocess, importlib.util
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

HIT = Path(__file__).resolve().parent if '__file__' in globals() else Path(r'C:\Users\praiseworthy\Desktop\hagen-wf\scen\3d\blender')
ROOT = HIT.parent
FPS = 30
C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))          # three (Y upp) -> Blender (Z upp)


def bl(v):
    """three-punkt -> Blender-punkt."""
    return Vector((v[0], -v[2], v[1]))


def args():
    a = globals().get('ARGV') or (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    g = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    return dict(scen=ROOT / g('--scen', 'scen3d.json'), spara=g('--spara'), ljud='--utan-ljud' not in a,
                bake=g('--bake'), arbetsut=g('--arbetsut'))


# ---------- material ----------
_mat = {}
def mat(hexfarg, namn=None):
    hexfarg = (hexfarg or '#808080').lstrip('#')
    if hexfarg in _mat: return _mat[hexfarg]
    rgb = [int(hexfarg[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
    m = bpy.data.materials.new(namn or f'farg_{hexfarg}')
    m.diffuse_color = (*lin, 1)                       # Workbench/klot
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (*lin, 1)
    bsdf.inputs['Roughness'].default_value = .8
    _mat[hexfarg] = m
    return m


# ---------- geometri (lågpoly kit; samma mått och ankare som meshes.js makeObject) ----------
def kloss(namn, farg, centrum, storlek, parent):
    """Låda i förälderns lokala three-ram (centrum, storlek = [w,h,d])."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object; o.name = namn
    o.scale = (storlek[0], storlek[2], storlek[1]); o.location = bl(centrum)
    o.data.materials.append(mat(farg)); o.parent = parent
    return o

def cylinder(namn, farg, centrum, r1, r2, h, parent, sidor=12):
    bpy.ops.mesh.primitive_cone_add(vertices=sidor, radius1=r2, radius2=r1, depth=h)
    o = bpy.context.active_object; o.name = namn; o.location = bl(centrum)
    o.data.materials.append(mat(farg)); o.parent = parent
    return o

def objekt(o, samling):
    """En set-/rekvisitapost -> tom förälder (id, semantik) med enkla barn."""
    rot = bpy.data.objects.new(o['id'], None); samling.objects.link(rot)
    rot.empty_display_size = .05
    rot['semantik'] = json.dumps({k: o.get(k) for k in ('id', 'type', 'label', 'support', 'semantic') if k in o}, ensure_ascii=False)
    w, h, d = o['dims']; c = o.get('color') or '#25282b'; t = o['type']; n = o['id']
    if t == 'table':
        kloss(n + '/skiva', c, [0, h / 2 - .025, 0], [w, .05, d], rot)
        cylinder(n + '/fot', '#31363a', [0, -.02, 0], .035, .045, h - .07, rot)
        kloss(n + '/bas', c, [0, -h / 2 + .025, 0], [min(w, .48), .045, min(d, .48)], rot)
    elif t == 'chair':
        kloss(n + '/sits', c, [0, h / 2, 0], [w, .055, d], rot)
        kloss(n + '/rygg', c, [0, h / 2 + .23, -d * .43], [w, .42, .045], rot)
        for x in (-1, 1):
            for z in (-1, 1):
                cylinder(n + '/ben', '#33383b', [x * w * .38, -.01, z * d * .38], .015, .015, h, rot, 6)
    elif t == 'window_wall':
        kloss(n + '/glas', '#a6bdc1', [0, .15, 0], [w, h - .3, .025], rot)
        x = -w / 2
        while x <= w / 2:
            kloss(n + '/post', c, [x, 0, -.035], [.055, h, .09], rot); x += .8
        for y in (-h / 2 + .12, .15, h / 2):
            kloss(n + '/regel', c, [0, y, -.04], [w, .055, .1], rot)
        x = -w / 2 + .2
        while x < w / 2:
            kloss(n + '/ute', '#81928b', [x, -.3, .5], [.5, 1.6, .3], rot); x += .75
    elif t == 'pendant':
        cylinder(n + '/sladd', '#282d32', [0, .18, 0], .008, .008, .36, rot, 6)
        cylinder(n + '/skarm', c, [0, -.03, 0], w * .25, w / 2, h * .45, rot)
    elif t == 'counter':
        kloss(n + '/kropp', c, [0, 0, 0], [w, h, d], rot)
        kloss(n + '/topp', '#ba9d75', [0, h / 2, 0], [w + .04, .045, d + .05], rot)
    elif t in ('paper_cup', 'drink_can', 'sauce_cup', 'fry'):
        farg = {'paper_cup': '#e8ddbd', 'drink_can': '#a5bed0', 'sauce_cup': '#e9e2d0', 'fry': '#e3b85b'}[t]
        cylinder(n + '/kropp', farg, [0, 0, 0], w / 2, w * (.37 if t == 'paper_cup' else .5), h, rot, 10)
    elif t == 'burger':
        cylinder(n + '/brod', '#c98d4a', [0, h * .2, 0], w * .45, w / 2, h * .45, rot, 10)
        cylinder(n + '/kott', '#5a3a27', [0, -h * .1, 0], w / 2, w / 2, h * .2, rot, 10)
        cylinder(n + '/botten', '#d39a55', [0, -h * .35, 0], w / 2, w * .47, h * .3, rot, 10)
    else:   # tray, fries_box, food_box, paper_wrap, card_terminal, floor, wall, ceiling …
        farg = {'tray': '#8a5a3c', 'fries_box': '#c8322b', 'food_box': '#e6dcc8', 'paper_wrap': '#e9e1d2', 'card_terminal': '#2b2e33'}.get(t, c)
        kloss(n + '/kropp', farg, [0, 0, 0], [w, h, d], rot)
    rot.location = bl(o['transform']['position'])
    rot.rotation_euler = (0, 0, math.radians(o['transform'].get('yaw') or 0))
    rot.hide_viewport = rot.hide_render = o.get('visible') is False
    for b in rot.children: b.hide_render = b.hide_viewport = rot.hide_render
    return rot


# ---------- tid: samma regler som player.js shotAt ----------
def tagningar(S):
    """[(shot, start_s, första_bildruta, sista_bildruta)] – bildruta i hör till tagningen där i/30 < start+duration."""
    ut, start, N = [], 0.0, round(sum(s['duration'] for s in S['shots']) * FPS)
    for s in S['shots']:
        slut = start + s['duration']
        f0 = next(i for i in range(N + 1) if i / FPS >= start - 1e-7)
        f1 = max(i for i in range(N) if i / FPS < slut - 1e-7) if s is not S['shots'][-1] else N - 1
        ut.append((s, start, f0, f1)); start = slut
    return ut, N


def kamerastate(shot, lokal):
    """Port av scene_runtime.cameraState (nyckelbilder + orbit)."""
    k = shot['camera']['keyframes']; a = b = k[0]
    for x in k:
        if x['t'] <= lokal: a = x
        if x['t'] > lokal: b = x; break
        b = a
    f = 0 if a is b else min(1, max(0, (lokal - a['t']) / (b['t'] - a['t'])))
    lerp = lambda p, q: Vector(p).lerp(Vector(q), f)
    pos, mal, upp = lerp(a['pos'], b['pos']), lerp(a['target'], b['target']), lerp(a.get('up', [0, 1, 0]), b.get('up', [0, 1, 0]))
    o = shot['camera'].get('orbit')
    if o:
        tt = min(1, max(0, (lokal - o['start']) / (o['end'] - o['start'])))
        pos = (Vector(o['startPos']) - Vector(o['pivot'])); pos.rotate(Matrix.Rotation(math.radians(o['degrees']) * tt, 3, 'Y')); pos += Vector(o['pivot'])
    return pos, mal, upp, a['fov'] + f * (b['fov'] - a['fov'])


def kameramatris(pos, mal, upp):
    """three lookAt (kameran tittar längs -Z, upp +Y) -> Blender-världsmatris."""
    z = (pos - mal).normalized(); x = upp.cross(z).normalized(); y = z.cross(x)
    R = C @ Matrix((x, y, z)).transposed()
    M = R.to_4x4(); M.translation = bl(pos)
    return M


def kameror(S, scen, samling):
    T, N = tagningar(S)
    for s, start, f0, f1 in T:
        cd = bpy.data.cameras.new('kam:' + s['id']); cd.sensor_fit = 'VERTICAL'; cd.clip_start = .025; cd.clip_end = 80
        kam = bpy.data.objects.new('kam:' + s['id'], cd); samling.objects.link(kam)
        kam['tagning'] = s['id']
        statisk = len(s['camera']['keyframes']) == 1 and not s['camera'].get('orbit')
        for i in ([f0] if statisk else range(f0, f1 + 1)):
            pos, mal, upp, fov = kamerastate(s, i / FPS - start)
            kam.matrix_world = kameramatris(pos, mal, upp); cd.angle = math.radians(fov)
            if not statisk:
                kam.keyframe_insert('location', frame=i); kam.keyframe_insert('rotation_euler', frame=i); cd.keyframe_insert('lens', frame=i)
        m = scen.timeline_markers.new(s['id'], frame=f0); m.camera = kam
    scen.camera = bpy.data.objects['kam:' + T[0][0]['id']]
    return T, N


def rekvisita_per_tagning(S, T):
    """propOverrides: synlighet/position per tagning, nycklat på tagningens första bildruta (konstant interpolation)."""
    for p in S['props']:
        o = bpy.data.objects.get(p['id'])
        if not o: continue
        for s, start, f0, f1 in T:
            ov = {**p, **(s.get('propOverrides', {}).get(p['id']) or {})}
            dold = ov.get('visible') is False or bool(ov.get('attach'))   # handfästa föremål tas över av bakningen
            o.location = bl(ov['transform']['position']); o.rotation_euler = (0, 0, math.radians(ov['transform'].get('yaw') or 0))
            o.hide_render = o.hide_viewport = dold
            for k in ('location', 'rotation_euler', 'hide_render', 'hide_viewport'): o.keyframe_insert(k, frame=f0)
            for b in o.children:
                b.hide_render = b.hide_viewport = dold
                b.keyframe_insert('hide_render', frame=f0); b.keyframe_insert('hide_viewport', frame=f0)
        for ob in [o, *o.children]:
            if ob.animation_data and ob.animation_data.action:
                for kp in _kurvor(ob.animation_data.action): kp.interpolation = 'CONSTANT'


def rekvisita_fran_bake(bake):
    """Rekvisita bildruta för bildruta ur bakningen (även föremål i händerna). Nyckel bara där något ändras."""
    C4 = C.to_4x4(); Ci = C4.inverted()
    forra = {}
    for fr in bake['frames']:
        i = fr['i']
        for pid, p in (fr.get('props') or {}).items():
            o = bpy.data.objects.get(pid)
            if not o: continue
            m = p['matrix']; M = Matrix([m[0:4], m[4:8], m[8:12], m[12:16]]).transposed()
            Mb = C4 @ M @ Ci
            nyckel = (tuple(round(x, 5) for r in Mb for x in r), bool(p.get('visible')))
            if forra.get(pid) == nyckel: continue
            forra[pid] = nyckel
            o.matrix_world = Mb; o.keyframe_insert('location', frame=i); o.keyframe_insert('rotation_euler', frame=i); o.keyframe_insert('scale', frame=i)
            for ob in (o, *o.children):
                ob.hide_render = ob.hide_viewport = not p.get('visible')
                ob.keyframe_insert('hide_render', frame=i); ob.keyframe_insert('hide_viewport', frame=i)
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action and not o.name.startswith(('actor:', 'kam:')):
            for kp in _kurvor(o.animation_data.action): kp.interpolation = 'CONSTANT'


def _kurvor(action):
    """Nyckelpunkter oberoende av API-version (Blender 5: kanalbuntar i lager)."""
    fc = list(getattr(action, 'fcurves', []) or [])
    if not fc:
        for lager in getattr(action, 'layers', []):
            for strip in lager.strips:
                for cb in strip.channelbags: fc += list(cb.fcurves)
    return [kp for f in fc for kp in f.keyframe_points]


def ljud(S, T, scen):
    """Originalljudet i scentid, exakt som mvp_render.py (atrim per tagning, atempo om tidskarta)."""
    ut = HIT / 'ljud-original.wav'; filt, delar = [], []
    for i, (s, *_r) in enumerate(T):
        a, b = s['source']['inSec'], s['source']['outSec']; d = s['duration']
        if s.get('tyst'):
            filt.append(f'anullsrc=r=48000:cl=mono,atrim=0:{d:.4f}[s{i}]')
        else:
            tempo = (b - a) / d
            filt.append(f'[0:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=mono' + (f',atempo={tempo:.4f}' if abs(tempo - 1) > .01 else '') + f'[s{i}]')
        delar.append(f'[s{i}]')
    filt.append(''.join(delar) + f'concat=n={len(delar)}:v=0:a=1[a]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(ROOT / S['audio']), '-filter_complex', ';'.join(filt), '-map', '[a]', str(ut)], check=True)
    if not scen.sequence_editor: scen.sequence_editor_create()
    se = scen.sequence_editor
    strips = se.strips if hasattr(se, 'strips') else se.sequences
    for x in list(strips): strips.remove(x)
    strips.new_sound('original', str(ut), 1, 0)
    return ut


def tagningslista(S, T, N):
    """Tagningslista för prompten: exakta tider, kamera, vem/vad i bild och repliker med ordtider (lokal tid i tagningen)."""
    akt = {a['id']: a for a in S['actors']}
    rader = []
    for s, start, f0, f1 in T:
        ing = s.get('ingest', {}); a0, a1 = s['source']['inSec'], s['source']['outSec']
        repl = []
        for d in S['dialogue']:
            if d['end'] > a0 and d['start'] < a1:
                repl.append(dict(talare=d['speaker'], text=d['text'],
                                 ord=[dict(w=w['w'], start=round(max(0, w['start'] - a0) + start, 3), slut=round(min(a1, w['end']) - a0 + start, 3)) for w in d.get('words', []) if w['end'] > a0 and w['start'] < a1]))
        synliga = [p['id'] for p in S['props'] if ({**p, **(s.get('propOverrides', {}).get(p['id']) or {})}).get('visible') is not False]
        rader.append(dict(
            id=s['id'], beat=s.get('beat'), start_s=round(start, 4), slut_s=round(start + s['duration'], 4), langd_s=round(s['duration'], 4),
            bildrutor=[f0, f1], kalla_s=[a0, a1],
            kamera=dict(utsnitt=ing.get('utsnitt'), rorelse=ing.get('rorelse'), objektiv_mm=ing.get('objektiv_mm_ekv'), fov=ing.get('fov_grader'),
                        avstand_m=ing.get('avstand_m'), hojd_mot_ogon_m=ing.get('kamerahojd_mot_ogon_m'), lutning=ing.get('lutning_grader')),
            i_bild=[dict(id=e['id'], roll=akt[e['id']].get('role'), sitter=akt[e['id']].get('seated')) for e in s['actors']],
            talare_utanfor_bild=ing.get('talare_utanfor_bild'), rekvisita_i_scen=synliga, repliker=repl))
    lista = dict(klipp=S['source']['clip'], fps=FPS, bildrutor=N, langd_s=round(N / FPS, 4), ljud='blender/ljud-original.wav', tagningar=rader)
    (HIT / 'tagningslista.json').write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding='utf-8')
    return lista


def bygg(scenfil=None, med_ljud=True, spara=None, bake_path=None, arbetsut=None):
    # Optional output root keeps the established chain's audio/list untouched.
    global HIT
    original_hit = HIT
    if arbetsut:
        HIT = Path(arbetsut).resolve(); HIT.mkdir(parents=True, exist_ok=True)
    S = json.loads(Path(scenfil or ROOT / 'scen3d.json').read_text(encoding='utf-8'))
    # töm scenen utan read_factory_settings (den skulle stänga av MCP-tillägget i en live-session)
    if bpy.context.object and bpy.context.object.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    for samling in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.actions, bpy.data.armatures, bpy.data.collections, bpy.data.sounds):
        for x in list(samling): samling.remove(x)
    bpy.context.scene.timeline_markers.clear()
    _mat.clear()
    scen = bpy.context.scene; scen.name = 'scen3d'
    scen.render.fps = FPS; scen.render.resolution_x = S['source'].get('width', 576); scen.render.resolution_y = S['source'].get('height', 1024)
    scen.unit_settings.system = 'METRIC'
    rum = bpy.data.collections.new('rum'); rek = bpy.data.collections.new('rekvisita'); kam = bpy.data.collections.new('kameror')
    for c in (rum, rek, kam): scen.collection.children.link(c)
    for o in S['set']:
        r = objekt(o, rum)
        for b in r.children: rum.objects.link(b) if b.name not in rum.objects else None
    for p in S['props']:
        r = objekt(p, rek)
        for b in r.children: rek.objects.link(b) if b.name not in rek.objects else None
    for o in list(scen.collection.objects): scen.collection.objects.unlink(o)   # primitiva lades i scenens rot
    T, N = kameror(S, scen, kam)
    scen.frame_start, scen.frame_end = 0, N - 1
    rekvisita_per_tagning(S, T)
    # ljus: enkel tre-punkt som spelaren (riktning i three-ram)
    for namn, riktning, styrka in (('sol', (-2, 5, 1), 3), ('fyll', (3, 3, 4), 1)):
        ld = bpy.data.lights.new(namn, 'SUN'); ld.energy = styrka
        lo = bpy.data.objects.new(namn, ld); kam.objects.link(lo)
        lo.rotation_euler = bl(riktning).to_track_quat('Z', 'Y').to_euler()
    scen.world = scen.world or bpy.data.worlds.new('varld'); scen.world.color = (.55, .6, .61)
    if med_ljud: ljud(S, T, scen)
    lista = tagningslista(S, T, N)
    bake = Path(bake_path).resolve() if bake_path else original_hit / 'bake.json'
    if bake_path and not bake.exists():
        raise FileNotFoundError(bake)
    if bake.exists() and (original_hit / 'importera_bake.py').exists():
        spec = importlib.util.spec_from_file_location('importera_bake', original_hit / 'importera_bake.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        m.importera(str(bake), str(scenfil or ROOT / 'scen3d.json'))
        for o in bpy.data.objects:      # bakningen ersätter propOverrides-nycklarna
            if o.animation_data and not o.name.startswith(('actor:', 'kam:')): o.animation_data_clear()
        rekvisita_fran_bake(json.loads(bake.read_text(encoding='utf-8')))
    scen.frame_set(0)
    if spara: bpy.ops.wm.save_as_mainfile(filepath=str(Path(spara).resolve()))
    print(f'bygg_scen: {len(S["set"])} set, {len(S["props"])} rekvisita, {len(T)} tagningar, {N} bildrutor ({N / FPS:.3f} s)',
          '| bake:', 'ja' if bake.exists() else 'nej (väntar på Codex)')
    HIT = original_hit
    return lista


if __name__ == '__main__':
    a = args()
    bygg(a['scen'], a['ljud'], a['spara'], a['bake'], a['arbetsut'])
