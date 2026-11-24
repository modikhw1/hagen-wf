"""Översiktsbild av platsen: alla roller på sina ankare och varje tagnings kameraläge som markör.
Körs headless på en redan byggd scen.blend (mhr_rig.py --plan ...):
  blender -b --factory-startup --python scen/3d/ingest/plats_oversikt.py -- <byggmapp med scen.blend> <plan.json> <utbild-prefix>
Skriver <prefix>_ovan.png (ortografisk, rakt uppifrån) och <prefix>_sned.png (perspektiv snett uppifrån).
Personerna fryses i varsin tagning (den där rollen syns i flest rutor, mittrutan) och de animerade kropparna tas bort,
så att alla syns samtidigt. Ändrar inte scen.blend på disk.
"""
import json
import math
import os
import re
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

FARG = ['#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4', '#008080', '#9a6324', '#800000']


def mat(hexf, emissive=False):
    h = hexf.lstrip('#'); rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    m = bpy.data.materials.new('o_' + h); m.diffuse_color = (*rgb, 1)
    return m


def lada(namn, pos, matt, farg, yaw=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos); o = bpy.context.active_object; o.name = namn
    o.dimensions = matt; o.rotation_euler[2] = yaw; o.data.materials.append(mat(farg)); return o


def text(namn, s, pos, mot, storlek=.18, farg='#000000'):
    c = bpy.data.curves.new(namn, 'FONT'); c.body = s; c.size = storlek; c.align_x = 'CENTER'
    o = bpy.data.objects.new(namn, c); bpy.context.collection.objects.link(o); o.location = pos
    t = o.constraints.new('TRACK_TO'); t.target = mot; t.track_axis = 'TRACK_Z'; t.up_axis = 'UP_Y'
    o.data.materials.append(mat(farg)); return o


def main():
    a = sys.argv[sys.argv.index('--') + 1:]; bygg, planfil, prefix = a[0], a[1], a[2]
    plan = json.load(open(planfil, encoding='utf-8'))
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(os.path.join(bygg, 'scen.blend')))
    sc = bpy.context.scene
    # 1. frys en kropp per roll
    armaturer = sorted([o for o in bpy.data.objects if o.type == 'ARMATURE'], key=lambda o: (re.sub(r'\.\d+$', '', o.name), int(o.name.rsplit('.', 1)[1]) if re.search(r'\.\d+$', o.name) else 0))
    kand = {}   # roll -> [(scen, personindex i planen)]
    for d in plan['scener']:
        for pm in d['personer']: kand.setdefault(pm['id'], []).append(d)
    antal = {}
    val = {}   # roll -> (armatur, ruta)
    for arm in armaturer:
        roll = re.sub(r'\.\d+$', '', arm.name)[len('person:'):]
        i = antal.get(roll, 0); antal[roll] = i + 1
        d = kand[roll][i]; a0, b0 = d['ut']
        rutor = b0 - a0
        if roll not in val or rutor > val[roll][2]: val[roll] = (arm, (a0 + b0) // 2, rutor)
    frysta = []
    dg = bpy.context.evaluated_depsgraph_get()
    for roll, (arm, f, _) in sorted(val.items()):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        for ch in arm.children:
            if ch.type != 'MESH': continue
            ev = ch.evaluated_get(dg); me = bpy.data.meshes.new_from_object(ev)
            ny = bpy.data.objects.new(f'fryst:{roll}', me); bpy.context.collection.objects.link(ny); ny.matrix_world = ch.matrix_world.copy()
            for m in ch.data.materials: ny.data.materials.append(m)
            frysta.append((roll, ny))
    for arm in armaturer:
        for ch in list(arm.children): bpy.data.objects.remove(ch, do_unlink=True)
        bpy.data.objects.remove(arm, do_unlink=True)
    # Samma möbeldel kan ha skilda synlighetsintervall i planen. I den
    # frysta översikten visas den en gång, så ytor inte flimrar mot sig själva.
    sedda=set()
    for o in sorted(list(bpy.data.objects),key=lambda o:o.name):
        if 'room_id' not in o:continue
        key=(o['room_id'],tuple(o.location),tuple(o.rotation_euler),tuple(o.dimensions))
        if key in sedda:bpy.data.objects.remove(o,do_unlink=True)
        else:sedda.add(key)
    for o in bpy.data.objects:
        if o.animation_data: o.animation_data_clear()
        if o.type != 'CAMERA': o.hide_render = o.hide_viewport = False
    sc.frame_set(0)
    # 2. platsens ankare och kameramarkörer
    pl = plan['plats'][0]
    centrum = np.zeros(3); allaxy = []
    for k in pl['ankare']:
        x, y, z = k['pos_m']; allaxy.append((x, y))
        if k['typ'] in ('sate', 'staplats'):
            bpy.ops.mesh.primitive_cylinder_add(radius=.28, depth=.03, location=(x, y, z + .02)); c = bpy.context.active_object; c.name = 'ankare:' + k['id']; c.data.materials.append(mat('#ffd800'))
            bpy.ops.mesh.primitive_cone_add(radius1=.07, depth=.2, location=(x + .28 * math.cos(k['riktning_rad']), y + .28 * math.sin(k['riktning_rad']), z + .05))
            p = bpy.context.active_object; p.rotation_euler = (0, math.pi / 2, k['riktning_rad']); p.data.materials.append(mat('#ff6a00')); p.name = 'riktning:' + k['id']
    kam = []
    for i, d in enumerate(plan['scener']):
        M = np.array(plan['renderkamera']['nycklar'][d['ut'][0]]['matris']); kam.append((d['id'], M)); allaxy.append((M[0, 3], M[1, 3]))
        col = FARG[i % len(FARG)]
        v = [(0, 0, 0), (-.16, -.28, -.45), (.16, -.28, -.45), (.16, .28, -.45), (-.16, .28, -.45)]
        me = bpy.data.meshes.new('kam_' + d['id']); me.from_pydata(v, [], [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1), (1, 2, 3, 4)]); me.update()
        o = bpy.data.objects.new('kam:' + d['id'], me); bpy.context.collection.objects.link(o); o.matrix_world = Matrix(M.tolist()); o.data.materials.append(mat(col))
    xy = np.array(allaxy); mitt = np.array([(xy[:, 0].min() + xy[:, 0].max()) / 2, (xy[:, 1].min() + xy[:, 1].max()) / 2, .6]); spann = max(np.ptp(xy[:, 0]), np.ptp(xy[:, 1])) + 2.2
    # 3. kameror för översikten och etiketter
    bpy.ops.object.empty_add(location=mitt.tolist()); mal = bpy.context.active_object; mal.name = 'mal'
    cd = bpy.data.cameras.new('oversikt'); co = bpy.data.objects.new('oversikt', cd); bpy.context.collection.objects.link(co)
    for i, (sid, M) in enumerate(kam): text('etikett:' + sid, sid.upper(), (M[0, 3], M[1, 3], M[2, 3] + .25 + .12 * (i % 3)), co, .16, FARG[i % len(FARG)])
    for k in pl['ankare']:
        if k['typ'] in ('sate', 'staplats'): text('etikett:' + k['id'], k['id'], (k['pos_m'][0], k['pos_m'][1], k['pos_m'][2] + 1.95), co, .16, '#000000')
    for roll, ny in frysta: pass
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x, sc.render.resolution_y = 1400, 1000; sc.render.film_transparent = False
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_shadows = False
    sc.world = bpy.data.worlds.new('b'); sc.world.color = (.86, .87, .89); sc.render.image_settings.file_format = 'PNG'
    sc.camera = co
    # ovan
    cd.type = 'ORTHO'; cd.ortho_scale = spann * 1.15; co.location = (mitt[0], mitt[1], 20); co.rotation_euler = (0, 0, 0)
    for o in bpy.data.objects:
        if o.type == 'FONT': o.constraints.clear(); o.rotation_euler = (0, 0, 0)
    sc.render.filepath = os.path.abspath(prefix + '_ovan.png'); bpy.ops.render.render(write_still=True)
    # snett
    cd.type = 'PERSP'; cd.lens = 30; cd.clip_end = 200
    # Se in från mallens öppna sida även när lokalen roterats vid ett byte.
    # Samma antagna översiktsavstånd som tidigare; rummets yaw styr bara sidan.
    golv = next((d for d in pl.get('rumsmall',{}).get('delar',[]) if d['typ']=='golv'),None)
    yaw = golv['yaw_rad'] if golv else 0.; c,s = math.cos(yaw),math.sin(yaw)
    dx,dy = -spann*.9,-spann*1.1
    co.location = (mitt[0]+c*dx-s*dy,mitt[1]+s*dx+c*dy,4.0+spann*.5)
    d = Vector(mitt.tolist()) - co.location; co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    for o in bpy.data.objects:
        if o.type == 'FONT':
            t = o.constraints.new('TRACK_TO'); t.target = co; t.track_axis = 'TRACK_Z'; t.up_axis = 'UP_Y'
    sc.render.filepath = os.path.abspath(prefix + '_sned.png'); bpy.ops.render.render(write_still=True)
    print('oversikt klar', prefix, flush=True)


main()
