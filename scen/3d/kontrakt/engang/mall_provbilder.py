"""Egna bakgrunds-Blender: två provrutor per scen ur en byggd mallfilm.

Skriver bara till byggmappens provbilder/. Rör aldrig en GUI-session.
"""
import json
import sys
from pathlib import Path
import bpy

a=sys.argv[sys.argv.index('--')+1:];d=Path(a[0]).resolve();p=json.loads((d/'plan.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(d/'scen.blend'));sc=bpy.context.scene
(d/'provbilder').mkdir(exist_ok=True)
for s in p['scener']:
    x,y=s['ut']
    for j,f in enumerate([x+(y-x)//3,x+2*(y-x)//3],1):
        sc.frame_set(f);sc.render.filepath=str(d/'provbilder'/f'{s["id"]}_{j}.png');bpy.ops.render.render(write_still=True)
