"""Läs MHR:s hela hud (hörn, trianglar, benvikter) ur lod1.fbx i en egen Blender-bakgrundsprocess. Ingen GUI.

Körs bara när tro_hud.npz ska göras om:
  blender -b --factory-startup --python scen/3d/kontrakt/tro_export_hud.py
lod1 har samma 18 439 hörn och ordning som kroppsmodellens egen modellutdata; det kontrolleras i kroppmatt.py (kontrollera_hud).
Renderingen använder lod3 (färre hörn, samma kropp). Vikterna sparas som de åtta tyngsta per hörn.
"""
import json
from pathlib import Path
import bpy
import numpy as np

HIT = Path(__file__).resolve().parent
namn = json.loads((HIT.parent / 'ingest/mhr_ledernamn.json').read_text(encoding='utf-8'))
bpy.ops.import_scene.fbx(filepath=str(HIT.parent / 'klipp2/sam3db/mhr/assets/lod1.fbx'))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
verts = []; faces = []; wi = []; ww = []; off = 0
for mesh in meshes:
    groups = {g.index: namn.index(g.name) for g in mesh.vertex_groups if g.name in namn}
    for v in mesh.data.vertices:
        verts.append(np.array(mesh.matrix_world @ v.co))
        g = sorted([(x.weight, groups[x.group]) for x in v.groups if x.group in groups], reverse=True)[:8]
        s = sum(x[0] for x in g) or 1.0
        wi.append([x[1] for x in g] + [0] * (8 - len(g))); ww.append([x[0] / s for x in g] + [0.] * (8 - len(g)))
    for p in mesh.data.polygons:
        ix = [off + i for i in p.vertices]
        for k in range(1, len(ix) - 1): faces.append([ix[0], ix[k], ix[k + 1]])
    off += len(mesh.data.vertices)
np.savez_compressed(HIT / 'tro_hud.npz', verts_fbx=np.array(verts, np.float32), faces=np.array(faces, np.int32),
                    vikt_led=np.array(wi, np.int16), vikt=np.array(ww, np.float32))
print('Exporterade hud', len(verts), 'hörn', len(faces), 'trianglar')
