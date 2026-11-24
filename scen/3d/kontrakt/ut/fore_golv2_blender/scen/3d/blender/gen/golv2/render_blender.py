"""Körs i egen headless Blender. Ordinarie byggare, utvalda stillbilder och mätpass."""
import sys,json,importlib.util,time
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];P=ROOT/'scen/3d'
sys.dont_write_bytecode=True
sys.path[:0]=[str(P/'ingest'),str(P/'kontrakt'),str(HERE)]
from prova import save,log
from trohet import NAMN,IX,ruta,projicera
phase=sys.argv[sys.argv.index('--')+1];out=HERE/phase
plan=json.loads((out/'plan.json').read_text(encoding='utf-8'))
file=P/'ingest/mhr_rig.py' if phase=='efter' else P/'kontrakt/ut/fore_golv2/scen/3d/ingest/mhr_rig.py'
spec=importlib.util.spec_from_file_location('prov_rigg',file);rig=importlib.util.module_from_spec(spec);spec.loader.exec_module(rig)
rig.FBX=str(P/'klipp2/sam3db/mhr/assets/lod3.fbx')
start=time.perf_counter()
rig.bygg(str(P/'ingest/ut/notan-tagningar/S1'),str(ROOT/'scen/klipp/d-dialog-notan.mp4'),planfil=str(out/'plan.json'),byggut=str(out))
sc=bpy.context.scene;sc.render.resolution_percentage=50
sc.render.image_settings.color_mode='RGBA';sc.render.use_file_extension=True
sc.render.threads_mode='FIXED';sc.render.threads=8
cam=sc.camera;rows=[];counts={};arms={}
for s in plan['scener']:
    for pm in s['personer']:
        pid=pm['id'];i=counts.get(pid,0);counts[pid]=i+1
        arms[s['id'],pid]=bpy.data.objects['person:'+pid+('' if i==0 else f'.{i:03d}')]
def render(name):
    sc.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True)
for s in plan['scener']:
    a,b=s['ut'];frames=[a+2,(a+b)//2,b-3]
    for u in frames:
        sc.frame_set(u);bpy.context.view_layer.update();f=s['lokal_start']+u-a
        original=cam.matrix_world.copy();lens=cam.data.lens
        key=plan['renderkamera']['nycklar'][u]
        item=dict(scen=s['id'],ut=u,lokal=f,kallruta=plan['kallrutor'][u],personer=[])
        dg=bpy.context.evaluated_depsgraph_get()
        for pm in s['personer']:
            arm=arms[s['id'],pm['id']];x=np.zeros((len(NAMN),3))
            for j in range(1,len(NAMN)):x[j]=arm.matrix_world@arm.pose.bones[NAMN[j]].head
            uv=[]
            for pt in x:
                v=world_to_camera_view(sc,cam,Vector(pt));uv.append([v.x*plan['kallbild_bredd'],(1-v.y)*plan['kallbild_hojd']])
            mesh=next(ch for ch in arm.children if ch.type=='MESH');ev=mesh.evaluated_get(dg)
            verts=np.array([ev.matrix_world@v.co for v in ev.data.vertices]);zmin=float(verts[:,2].min())
            floor=next((float(p['golv_hojd_m']) for p in plan.get('plats',[]) if p['id']==s.get('plats_id')),0.)
            pr=dict(person=pm['id'],ingest_id=pm.get('ingest_id','1'),leder_m=x.tolist(),leder_px=uv,
                mesh_min_z_m=zmin,golv_m=floor,sula_over_golv_m=zmin-floor,
                backen_m=x[IX['root']].tolist(),handleder_m=x[[IX['l_wrist'],IX['r_wrist']]].tolist())
            if phase=='efter':
                expected=ruta(s,pm,f)
                pr['blender_numpy_max_m']=float(np.linalg.norm(x[1:]-expected[1:],axis=1).max())
                pr['blender_numpy_max_px']=float(np.linalg.norm(np.array(uv)[1:]-projicera(expected[1:],key,plan['kallbild_bredd'],plan['kallbild_hojd']),axis=1).max())
            item['personer'].append(pr)
        render(f'{s["id"]}_{u:03d}_original')
        # Silhuett från samma evaluerade Blenderhud, med möbler undanlagda.
        hidden={o:o.hide_render for o in sc.objects}
        shading=sc.display.shading
        old=(shading.light,shading.color_type,shading.show_shadows,sc.render.film_transparent)
        for o in sc.objects:
            if o.type=='MESH' and not o.name.startswith('person:'):o.hide_render=True
        shading.light='FLAT';shading.color_type='SINGLE';shading.single_color=(1,1,1);shading.show_shadows=False
        sc.render.film_transparent=True
        render(f'{s["id"]}_{u:03d}_mask')
        for o,h in hidden.items():o.hide_render=h
        shading.light,shading.color_type,shading.show_shadows,sc.render.film_transparent=old
        torso=np.array(item['personer'][0]['leder_m'][IX['c_spine2']]);m=np.array(original)
        distance=float((torso-m[:3,3])@(-m[:3,2]));target=m[:3,3]-m[:3,2]*distance
        pos=m[:3,3]+.5*m[:3,0]+np.array([0,0,.3])
        q=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y')
        cam.matrix_world=Matrix.Translation(Vector(pos))@q.to_matrix().to_4x4()
        item['flyttad']=dict(position_m=pos.tolist(),mal_m=target.tolist(),lins_mm=lens,matris=[list(r) for r in cam.matrix_world])
        render(f'{s["id"]}_{u:03d}_flyttad')
        if u==frames[1]:
            cam.data.lens=lens/2
            render(f'{s["id"]}_{u:03d}_flyttad_vid')
        cam.matrix_world=original;cam.data.lens=lens;rows.append(item)
        save(out/'blender_matning.json',rows)
        print('GOLV2_RUTA',phase,s['id'],u,flush=True)
    log(f'Blender {phase}: {s["id"]} renderad början/mitt/slut, originalkamera, silhuett och flyttad kamera. Mitt även vidare utsnitt med halverad lins. Faktiska Blenderleder och hudgolv sparade.',f'scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/kor_render.py {"fore" if phase=="efter" else "analys"}')
save(out/'render_info.json',dict(kod=str(file),blender=bpy.app.version_string,bygg_och_render_s=time.perf_counter()-start,rutor=len(rows),upplosning=[288,512],fbx=rig.FBX))
