"""Blockout av brons steg i Blender: en stillbild per steg, 9:16.

Kör:  blender -b --factory-startup --python blockout.py -- bro_notan_gelato.json ut/blockout

Det här är en uppställning, inte en läsning: lådor och dockor på de platser bron anger.
Måtten är schabloner (disk 0,93 m hög, bord 0,75 m, docka 1,7 m). Ingenting kommer ur video.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

FARG = {'gast_a': (0.90, 0.45, 0.15, 1), 'gast_b': (0.20, 0.45, 0.85, 1), 'personal': (0.20, 0.65, 0.35, 1),
        'mobel': (0.55, 0.50, 0.45, 1), 'golv': (0.82, 0.80, 0.76, 1), 'sak': (0.95, 0.85, 0.30, 1),
        'vagg': (0.70, 0.72, 0.75, 1), 'hud': (0.85, 0.70, 0.60, 1), 'mork': (0.15, 0.15, 0.17, 1)}
MAT = {}


def mat(namn):
    if namn not in MAT:
        m = bpy.data.materials.new(namn)
        m.diffuse_color = FARG[namn]
        MAT[namn] = m
    return MAT[namn]


def lada(namn, pos, storlek, farg, rot=0.0, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.object
    o.name = namn
    o.scale = storlek
    o.rotation_euler[2] = rot
    o.data.materials.append(mat(farg))
    if parent:
        o.parent = parent
    return o


def cyl(namn, a, b, radie, farg, parent=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=radie, depth=d.length, location=(a + b) / 2, vertices=12)
    o = bpy.context.object
    o.name = namn
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    o.data.materials.append(mat(farg))
    if parent:
        o.parent = parent
    return o


def klot(namn, pos, radie, farg, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radie, location=pos, segments=16, ring_count=8)
    o = bpy.context.object
    o.name = namn
    o.data.materials.append(mat(farg))
    if parent:
        o.parent = parent
    return o


def sak(typ, lokal, parent=None, skala=1.0):
    """Föremål. lokal = position i förälderns ram (eller världen)."""
    x, y, z = lokal
    if typ == 'terminal':
        return lada('terminal', (x, y, z + 0.02), (0.09, 0.16, 0.04), 'mork', parent=parent)
    if typ == 'bricka':
        return lada('bricka', (x, y, z + 0.03), (0.45 * skala, 0.32 * skala, 0.06), 'sak', parent=parent)
    if typ == 'lada':
        return lada('lada', (x, y, z + 0.05 * skala), (0.18 * skala, 0.18 * skala, 0.10 * skala), 'sak', parent=parent)
    if typ == 'lada_stor':
        return lada('lada_stor', (x, y, z + 0.11), (0.36, 0.30, 0.22), 'sak', parent=parent)
    if typ == 'sked':
        return lada('sked', (x, y, z), (0.03, 0.10, 0.02), 'sak', parent=parent)
    if typ == 'spade':
        o = lada('spade', (x, y, z + 0.06), (0.16, 0.05, 0.22), 'sak', parent=parent)
        return o
    if typ == 'trag':
        return lada('trag', (x, y, z + 0.04), (0.42, 0.32, 0.08), 'sak', parent=parent)
    raise ValueError(typ)


def docka(p):
    """Docka i egen ram: står i origo, vänd mot +y. Roteras och flyttas sedan."""
    rot = bpy.data.objects.new('P_' + p['id'], None)
    bpy.context.collection.objects.link(rot)
    f = p['roll']
    sitter = p.get('pose') == 'sitter'
    hoft = 0.47 if sitter else 0.92
    axel = hoft + 0.52
    for s in (-1, 1):
        if sitter:
            cyl('lar', (s * 0.10, 0, hoft), (s * 0.10, 0.42, hoft), 0.07, f, rot)
            cyl('ben', (s * 0.10, 0.42, hoft), (s * 0.10, 0.42, 0.03), 0.06, f, rot)
        else:
            cyl('ben', (s * 0.10, 0, hoft), (s * 0.10, 0, 0.03), 0.07, f, rot)
    cyl('bal', (0, 0, hoft), (0, 0, axel), 0.16, f, rot)
    klot('huvud', (0, 0, axel + 0.20), 0.12, 'hud', rot)
    lada('nasa', (0, 0.13, axel + 0.19), (0.04, 0.06, 0.04), 'mork', parent=rot)   # visar blickriktningen
    arm = p.get('arm')
    hand = None
    for s in (-1, 1):
        ax = (s * 0.20, 0, axel - 0.04)
        if s == 1 and arm == 'fram':
            hand = (s * 0.18, 0.55, axel - 0.12)
            cyl('arm', ax, hand, 0.05, f, rot)
        elif s == 1 and arm == 'mun':
            arb = (s * 0.26, 0.22, axel - 0.26)
            hand = (s * 0.06, 0.20, axel + 0.10)
            cyl('overarm', ax, arb, 0.05, f, rot)
            cyl('underarm', arb, hand, 0.045, f, rot)
        else:
            cyl('arm', ax, (s * 0.24, 0.03, hoft - (0.0 if sitter else 0.05) + (0.12 if sitter else 0)), 0.05, f, rot)
    if p.get('haller'):
        h = hand or (0.24, 0.12, hoft + 0.10)
        if p['haller'] == 'lada_stor' and not hand:
            cyl('arm2', (0.20, 0, axel - 0.04), (0.16, 0.30, hoft + 0.18), 0.05, f, rot)
            cyl('arm3', (-0.20, 0, axel - 0.04), (-0.16, 0.30, hoft + 0.18), 0.05, f, rot)
            h = (0, 0.36, hoft + 0.08)
        sak(p['haller'], (h[0], h[1] + 0.06, h[2]), parent=rot, skala=p.get('haller_skala', 1.0))
    if sitter:
        lada('stol', (0, -0.02, 0.22), (0.42, 0.42, 0.44), 'mobel', parent=rot)
    rot.location = (p['pos'][0], p['pos'][1], 0)
    rot.rotation_euler[2] = math.radians(p.get('vand', 0))
    return rot


def bygg(scen):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    lada('golv', (0, 0, -0.025), (7, 7, 0.05), 'golv')
    lada('vagg', (0, 2.4, 1.4), (7, 0.1, 2.8), 'vagg')
    for s in scen.get('saker', []):
        if s['typ'] == 'disk':
            lada('disk', (0, 0.05, 0.465), (2.6, 0.6, 0.93), 'mobel')
        elif s['typ'] == 'dorr':      # fasad med dörr: personen står utanför
            lada('fasad_v', (-1.6, 1.2, 1.4), (2.2, 0.15, 2.8), 'vagg')
            lada('fasad_h', (1.6, 1.2, 1.4), (2.2, 0.15, 2.8), 'vagg')
            lada('fasad_o', (0, 1.2, 2.5), (1.0, 0.15, 0.6), 'vagg')
            lada('dorr', (0, 1.25, 1.1), (1.0, 0.05, 2.2), 'mork')
        elif s['typ'] == 'hylla':     # barhylla bakom disken
            lada('hylla', (0, 1.9, 1.5), (2.6, 0.3, 1.6), 'mork')
            for i in range(7):
                lada('flaska', (-1.05 + i * 0.35, 1.72, 1.55), (0.08, 0.08, 0.3), 'sak')
        elif s['typ'] == 'spis':      # köksbänk bakom
            lada('spis', (0, 1.9, 0.45), (2.6, 0.6, 0.9), 'mork')
        elif s['typ'] == 'bord':
            lada('bord', (s['pos'][0], s['pos'][1], 0.73), (0.75, 0.75, 0.05), 'mobel')
            cyl('bordsben', (s['pos'][0], s['pos'][1], 0), (s['pos'][0], s['pos'][1], 0.72), 0.05, 'mobel')
        else:
            sak(s['typ'], (s['pos'][0], s['pos'][1], s.get('z', 0)), skala=s.get('skala', 1.0))
    for p in scen['personer']:
        docka(p)
    kam = {'vid': ((0.0, -4.3, 1.55), (0, 0.2, 0.95), 30), 'sned': ((2.5, -3.3, 1.75), (-0.05, -0.15, 1.0), 32),
           'rak': ((0.0, -2.6, 1.45), (0, 0.4, 1.15), 32), 'ko': ((1.9, -4.6, 1.75), (-0.55, -0.6, 1.0), 34),
           'bordet': ((0.0, -2.9, 1.5), (0, 0.3, 0.95), 32), 'ute': ((0.0, -3.6, 1.5), (0, 0.3, 1.0), 30)}[scen.get('kamera', 'sned')]
    z = scen.get('zoom') or 1.0      # under 1 = tätare bild, över 1 = vidare
    if z != 1.0:
        kam = (tuple(Vector(kam[1]) + (Vector(kam[0]) - Vector(kam[1])) * z), kam[1], kam[2])
    bpy.ops.object.camera_add(location=kam[0])
    c = bpy.context.object
    c.data.lens = kam[2]
    c.rotation_mode = 'QUATERNION'
    c.rotation_quaternion = (Vector(kam[1]) - Vector(kam[0])).to_track_quat('-Z', 'Y')
    bpy.context.scene.camera = c


def main():
    arg = sys.argv[sys.argv.index('--') + 1:]
    bro = json.loads(Path(arg[0]).resolve().read_text(encoding='utf-8'))
    ut = Path(arg[1]).resolve()
    ut.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'MATERIAL'
    sc.display.shading.show_shadows = True
    sc.display.shading.show_cavity = True
    sc.render.resolution_x, sc.render.resolution_y = 540, 960
    sc.render.film_transparent = False
    prefix = arg[2] if len(arg) > 2 else 'steg'
    for i, steg in enumerate(bro['steg']):
        MAT.clear()
        bygg(steg['scen'])
        sc.render.filepath = str(ut / f'{prefix}_{i:02d}.png')
        bpy.ops.render.render(write_still=True)
        print('renderad', i, steg['t'])


if __name__ == '__main__':
    main()
