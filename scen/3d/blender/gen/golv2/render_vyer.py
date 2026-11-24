"""Rena bildpass från sparad ordinarie scen; inga maskändringar i samma process."""
import sys,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
if '--blender' not in sys.argv:
    for phase in ['fore','efter']:
        with (HERE/phase/'rena_vyer.log').open('wb') as f:
            r=subprocess.run([r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe','-b','--factory-startup','-t','8','--python-exit-code','1','--python',str(Path(__file__).resolve()),'--','--blender',phase],stdout=f,stderr=subprocess.STDOUT)
        print(phase,'rena vyer exit',r.returncode,flush=True)
        if r.returncode:print((HERE/phase/'rena_vyer.log').read_text(encoding='utf-8',errors='replace')[-3000:]);raise SystemExit(r.returncode)
    raise SystemExit(0)
import bpy
from mathutils import Matrix
sys.path.insert(0,str(HERE));from prova import log
phase=sys.argv[-1];out=HERE/phase
bpy.ops.wm.open_mainfile(filepath=str(out/'scen.blend'));sc=bpy.context.scene
measures=json.loads((out/'blender_matning.json').read_text(encoding='utf-8'))
sc.render.resolution_percentage=50;sc.render.image_settings.color_mode='RGBA'
orig=sc.camera;cd=orig.data.copy();cd.animation_data_clear();cam=bpy.data.objects.new('ren_flyttad_kamera',cd);sc.collection.objects.link(cam)
for r in measures:
    sid,u=r['scen'],r['ut'];sc.frame_set(u);sc.camera=orig;bpy.context.view_layer.update()
    def render(suffix):
        sc.render.filepath=str(out/f'{sid}_{u:03d}_{suffix}.png');bpy.ops.render.render(write_still=True)
    render('original')
    cam.matrix_world=Matrix(r['flyttad']['matris']);cd.lens=r['flyttad']['lins_mm'];sc.camera=cam
    render('flyttad')
    assert max(abs(cam.matrix_world[i][j]-r['flyttad']['matris'][i][j]) for i in range(4) for j in range(4))<1e-6
    if (out/f'{sid}_{u:03d}_flyttad_vid.png').exists():cd.lens/=2;render('flyttad_vid')
    sc.camera=orig
log(f'{phase}: samtliga original- och sidovyer omrenderade direkt ur sparad scen, i en process utan maskpass. Detta undviker kvarvarande synlighetsstate efter bort-/återkoppling av maskpassets animationer. Kamerans matris kontrollerad efter render. Dessa bilder är de slutliga.',"scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/analysera.py")
