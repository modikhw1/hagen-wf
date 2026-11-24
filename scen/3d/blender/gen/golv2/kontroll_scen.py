import sys,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];P=ROOT/'scen/3d'
if '--blender' not in sys.argv:
    with (HERE/'kontroll_scen.log').open('wb') as f:
        r=subprocess.run([r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe','-b','--factory-startup','-t','8','--python-exit-code','1','--python',str(Path(__file__).resolve()),'--','--blender'],stdout=f,stderr=subprocess.STDOUT)
    print('kontroll exit',r.returncode)
    if r.returncode:print((HERE/'kontroll_scen.log').read_text(encoding='utf-8',errors='replace')[-4000:])
    raise SystemExit(r.returncode)
import bpy,numpy as np
from mathutils import Matrix,Vector
sys.path[:0]=[str(HERE),str(P/'kontrakt')]
from prova import save,log
from trohet import IX
facts={};contacts=[]
for phase in ['fore','efter']:
    plan=json.loads((HERE/phase/'plan.json').read_text(encoding='utf-8'))
    bpy.ops.wm.open_mainfile(filepath=str(HERE/phase/'scen.blend'));sc=bpy.context.scene
    measures=json.loads((HERE/phase/'blender_matning.json').read_text(encoding='utf-8'))
    fact=[]
    for row in measures:
        u=row['ut'];sc.frame_set(u);bpy.context.view_layer.update();sid=row['scen'];s=next(s for s in plan['scener'] if s['id']==sid)
        active=[o for o in sc.objects if o.type=='MESH' and not o.hide_render]
        props=[dict(namn=o.name,position=list(o.matrix_world.translation)) for o in active if o.name.startswith('prop:')]
        fact.append(dict(scen=sid,ut=u,synliga_meshar=len(active),synliga_props=props))
        for pr in row['personer']:
            pm=next(p for p in s['personer'] if p['id']==pr['person']);anchor=pm['stod'];hip=np.array(pr['backen_m']);wr=np.array(pr['handleder_m'])
            objs=[o for o in plan['objekt'] if o['synlig_ut'][0]<=u<o['synlig_ut'][1]]
            seats=[o for o in objs if o['id'].startswith(anchor['id']+':') and o['matt_m'][2]<.12]
            tables=[o for o in objs if o['id'].startswith('bord') and o['matt_m'][2]<.12]
            nearest=lambda os:min(os,key=lambda o:np.linalg.norm(np.array(o['pos_m'])[:2]-hip[:2])) if os else None
            seat=nearest(seats);table=nearest(tables)
            r=dict(fas=phase,scen=sid,ut=u,person=pr['person'],sula_m=pr['sula_over_golv_m'])
            if seat:
                pos=np.array(seat['pos_m']);dim=np.array(seat['matt_m']);r['sits']=dict(id=seat['id'],topp_m=pos[2]+dim[2]/2,backen_over_sits_m=hip[2]-pos[2]-dim[2]/2,backen_xy_avstand_m=float(np.linalg.norm(hip[:2]-pos[:2])),matt_m=dim.tolist())
            if table:
                pos=np.array(table['pos_m']);dim=np.array(table['matt_m']);yaw=table['rotation_rad'][2];c,si=np.cos(yaw),np.sin(yaw);R=np.array([[c,-si],[si,c]])
                xy=(wr[:,:2]-pos[:2])@R
                r['bord']=dict(id=table['id'],topp_m=pos[2]+dim[2]/2,handled_over_bord_m=(wr[:,2]-pos[2]-dim[2]/2).tolist(),handled_utanfor_xy_m=np.linalg.norm(np.maximum(np.abs(xy)-dim[:2]/2,0),axis=1).tolist(),matt_m=dim.tolist())
            contacts.append(r)
    facts[phase]=fact
    # Kontroll av vid S4, direkt efter återöppning: inga maskpass har påverkat scenen.
    bpy.ops.wm.open_mainfile(filepath=str(HERE/phase/'scen.blend'));sc=bpy.context.scene;sc.frame_set(213)
    row=next(r for r in measures if r['ut']==213);m=row['flyttad']['matris']
    cd=sc.camera.data.copy();cd.animation_data_clear();cam=bpy.data.objects.new('isolerad_kontrollkamera',cd);sc.collection.objects.link(cam)
    cam.matrix_world=Matrix(m);cd.lens=row['flyttad']['lins_mm']/2;sc.camera=cam
    sc.render.resolution_percentage=50;sc.render.filepath=str(HERE/phase/'kontroll_s4_vid.png');bpy.ops.render.render(write_still=True)
save(HERE/'scenkontroll.json',facts);save(HERE/'mobelkontakter.json',contacts)
print('S4 props',[(p,[r for r in v if r['ut']==213][0]['synliga_props']) for p,v in facts.items()])
print('Mid contacts',[(r['fas'],r['scen'],r.get('sits'),r.get('bord')) for r in contacts if r['ut'] in [36,93,142,213,268,309,360]])
log('Scenen återöppnad separat för oberoende kontroll av faktiska möbler/synlighet och S4:s vidare vy. Inga maskpass föregår denna render. Höft/sits och handled/bord uppmätta i planens/Blenders meter; rotleden är inte en fysisk sittyta.',"scen/.venv/Scripts/python.exe scen/3d/blender/gen/golv2/slutrapport.py")
