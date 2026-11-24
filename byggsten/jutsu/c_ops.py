"""Reuse the proven Jutsu operation templates for C's measured ingest.

No changes to the Notan experiment. Run after C's ingest through varld/golv.
"""
import ast
import json
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'ut/c-sketch-tre'
sys.path.insert(0, str(ROOT / 'scen/3d/kontrakt'))
import trohet
from mathutils_lite import mat_till_quat


def export_frames(seq, track, max_gap=6, edge_hold=5):
    """Short tracking gaps are inferred; identity transitions remain hidden."""
    visible = np.zeros(len(seq['inom']), dtype=bool)
    visible[[int(f) for f in track]] = True
    support = np.asarray(seq['inom'], dtype=bool).copy()
    known = np.flatnonzero(support)
    if not len(known):
        return np.array([], dtype=int)
    support[max(0, known[0]-edge_hold):known[0]] = True
    support[known[-1]+1:known[-1]+edge_hold+1] = True
    frames = np.flatnonzero(support & visible)
    result = support & visible
    for a, b in zip(frames[:-1], frames[1:]):
        if 1 < b-a <= max_gap+1 and support[a:b+1].all():
            result[a:b+1] = True
    return np.flatnonzero(result)


def main():
    src = OUT / 'ingest'
    required = ['varld.npz', 'sekvens_1.npz', 'sekvens_2.npz', 'sekvens_3.npz']
    missing = [name for name in required if not (src / name).exists()]
    if missing:
        raise SystemExit('Ingest incomplete; missing: ' + ', '.join(missing))
    tracks = json.loads((src / 'personer.json').read_text(encoding='utf-8'))
    meta = json.loads((src / 'meta.json').read_text())
    world = dict(np.load(src / 'varld.npz'))
    G = trohet.gravitation(world)
    names = ['c_spine0','c_spine2','c_neck','c_head','l_uparm','l_lowarm','l_wrist',
             'r_uparm','r_lowarm','r_wrist','l_upleg','l_lowleg','l_foot','r_upleg',
             'r_lowleg','r_foot','l_ball','r_ball']
    # trohet.NAMN includes the world root, matching the pose array.
    indices = [trohet.IX[n] for n in names]
    persons, data, intervals = {}, {}, []
    colours = ['#a8ced3','#414858','#a68160']
    for num, path in enumerate(sorted(src.glob('sekvens_*.npz'))):
        pid = path.stem[8:]
        seq = trohet.las_sekvens(path)
        roles={'1':('kund','#a8ced3'),'2':('servitor','#414858'),'3':('matbarare','#a68160')}
        role,colour=roles.get(pid,('source_track_'+pid,colours[num % 3]))
        persons[pid] = dict(roll=role, farg=colour)
        frames = export_frames(seq, tracks[pid])
        persons[pid]['inferred_visibility_frames'] = [int(f) for f in frames if not seq['inom'][f] or str(f) not in tracks[pid]]
        # Reviewed source_handoff.jpg: separate actors remain visible during occlusion.
        # These are authored/interpolated continuations, never additional body measurements.
        inferred = {'2': (451, 550), '3': (413, 480)}.get(pid)
        if inferred:
            frames = np.union1d(frames, np.arange(*inferred))
            persons[pid]['authored_occlusion_interval'] = list(inferred)
            persons[pid]['authored_occlusion_method'] = ('hold last pose and exit screen-right' if pid == '2' else 'interpolate between same-identity endpoint poses')
        if pid == '3':
            persons[pid]['assumed_seated_support'] = {'frames':[780,819], 'reason':'source shows sitting; hidden lower legs fold upward in monocular estimate; blend to bent knees and floor-supported feet'}
        groups = np.split(frames, np.where(np.diff(frames) > 1)[0] + 1)
        data[pid] = []
        for group in groups:
            if not len(group): continue
            a, b = int(group[0]), int(group[-1]) + 1
            rows = []
            for f in sorted(set(range(a, b, 3)) | {b-1}):
                Q = G @ world['kam_R'][f] @ trohet.F
                T = G @ (world['kam_C'][f] + world['kam_R'][f] @ seq['cam_t'][f])
                xyz = seq['pose'][f, indices, :3] / 100 @ Q.T + T
                if pid == '2' and f > 450:
                    # Source: waiter still partly visible at 510, fully outside after 549.
                    shift = np.interp(f, [450, 510, 549], [0., .13, 1.05])
                    xyz += (G @ world['kam_R'][f][:, 0]) * shift
                if pid == '3' and f >= 780:
                    t=min(1.,(f-780)/30); t=t*t*(3-2*t)
                    # Source-guided seated support, kept separate from measured ingest.
                    direction=np.array([.72,-.69,0.]); direction/=np.linalg.norm(direction)
                    for side_name in ('l','r'):
                        hip=xyz[names.index(side_name+'_upleg')]
                        knee=hip+direction*.40; knee[2]-=.035
                        foot=knee.copy(); foot[2]=float(world['golv_h'])+.07
                        toe=foot+direction*.13; toe[2]-=.035
                        for joint,target in [('lowleg',knee),('foot',foot),('ball',toe)]:
                            index=names.index(side_name+'_'+joint)
                            xyz[index]=(1-t)*xyz[index]+t*target
                rows.append([f] + np.rint(xyz.ravel()*1000).astype(int).tolist())
            data[pid].append(dict(scen='S1',ut=[a,b],rutor=rows))
    first = trohet.las_sekvens(next(src.glob('sekvens_*.npz')))
    focal = float(first['fokal'])
    cam = []
    for f in sorted(set(range(0,meta['N'],3)) | {meta['N']-1}):
        loc = G @ world['kam_C'][f]
        rot = G @ world['kam_R'][f] @ trohet.F
        cam.append([f]+loc.round(5).tolist()+list(mat_till_quat(rot))+[36*focal/meta['bredd']])
    room_path=OUT/'room.json'
    if not room_path.exists():
        def center(pid, joint, start, end):
            samples=[np.array(row[1:]).reshape(-1,3)[names.index(joint)]/1000
                     for seg in data[pid] for row in seg['rutor'] if start<=row[0]<=end]
            return np.median(samples,axis=0)
        customer=center('1','c_spine0',150,360)
        server=center('2','c_spine0',150,360)
        forward=server-customer;forward[2]=0;forward/=np.linalg.norm(forward)
        side=np.array([-forward[1],forward[0],0])
        yaw=float(np.arctan2(forward[1],forward[0]))
        floor=float(world.get('golv_h',min(center('2','l_foot',150,360)[2],center('2','r_foot',150,360)[2])))
        table=customer+forward*.58;table[2]=floor+.74
        room=[]
        def box(id,p,m,colour,yaw=yaw):
            room.append(dict(id=id,p=np.asarray(p).round(4).tolist(),m=m,rz=yaw,f=colour,s=[0,meta['N']]))
        box('golv', [*customer[:2],floor-.06],[7,10,.12],'#8e7662')
        box('bord_huvud',table,[.8,.8,.055],'#4b352a')
        base=table.copy();base[2]=floor+.36;box('bordsben',base,[.08,.08,.72],'#282b2d')
        bench=customer-forward*.15;bench[2]=floor+.44;box('bank_sits',bench,[.55,5,.14],'#796b67')
        back=bench-forward*.3;back[2]=floor+.95;box('bank_rygg',back,[.14,5,1.1],'#796b67')
        wall=back-forward*.15;wall[2]=floor+1.5;box('vagg',wall,[.12,8,3],'#d9c5a3')
        for offset in [-1.65,1.65,3.3]:
            t=table+side*offset;box('bord_'+str(offset),t,[.8,.8,.055],'#785a36')
            leg=t.copy();leg[2]=floor+.36;box('ben_'+str(offset),leg,[.08,.08,.72],'#282b2d')
            chair=t+forward*.68;chair[2]=floor+.45;box('stol_'+str(offset),chair,[.43,.45,.08],'#5c4538')
            chair+=forward*.21;chair[2]=floor+.73;box('stolrygg_'+str(offset),chair,[.07,.45,.58],'#5c4538')
        room_path.write_text(json.dumps(room,indent=2),encoding='utf-8')
        (OUT/'room_provenance.json').write_text(json.dumps(dict(status='assumed_geometry',
            anchors='median measured pelvis positions; measured/estimated ingest floor',
            dimensions='assumed table height .74m, bench .44m; simple restaurant layout from source contact sheet',
            customer=customer.tolist(),server=server.tolist(),floor=floor,table=table.tolist()),indent=2),encoding='utf-8')
    room = json.loads(room_path.read_text(encoding='utf-8'))
    (OUT/'motion.json').write_text(json.dumps(dict(joints=names,persons=persons,motion=data),ensure_ascii=False),encoding='utf-8')
    templates = {n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse((HERE/'notan_ops.py').read_text(encoding='utf-8')).body
                 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('OP1','OP2','OP3')}
    j = lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':'))
    replace = {'__META__':j(dict(fps=meta['fps'],n=meta['N'],w=meta['bredd'],h=meta['hojd'],sensor=36)),
               '__RUM__':j(room),'__KAM__':j(cam),'__SC__':j([dict(id='S1',ut=[0,meta['N']],personer=list(persons),ankare=[])]),
               '__REP__':'[]','__PERS__':j(persons),'__LEDER__':j(names),'__PDATA__':j(data),
               '__NYCKEL__':j({'S1':[0,90,450,600,818]}),'__N__':str(meta['N'])}
    ops = OUT / 'ops'; ops.mkdir(exist_ok=True)
    (ops/'op4_details.py').write_text((HERE/'c_detail.py').read_text(encoding='utf-8')+'\n'+(HERE/'export_gate.py').read_text(encoding='utf-8'),encoding='utf-8')
    for name, template in templates.items():
        for old,new in replace.items(): template=template.replace(old,new)
        if name=='OP3':
            for a in range(0,meta['N'],150):
                b=min(a+149,meta['N']-1)
                (ops/f'render_{a}_{b}.py').write_text(template.replace('__A__',str(a)).replace('__B__',str(b)),encoding='utf-8')
        else:
            template=template.replace('(36,140,200,360)', '(0,90,414,480,600,818)')
            if name == 'OP2':
                template=template.replace('def synlighet(ob,intervall):', 'def synlighet(ob,intervall):\n    previous=bpy.context.preferences.edit.keyframe_new_interpolation_type\n    bpy.context.preferences.edit.keyframe_new_interpolation_type="CONSTANT"')
                template=template.replace('\ndef bygg(pid,niva,interp):', '\n    bpy.context.preferences.edit.keyframe_new_interpolation_type=previous\n\ndef bygg(pid,niva,interp):')
                template += '\n' + (HERE/'export_gate.py').read_text(encoding='utf-8')
            (ops/f'{name.lower()}.py').write_text(template,encoding='utf-8')
    (OUT/'export_summary.json').write_text(j(dict(persons=persons,frames=meta['N'],camera_samples=len(cam),
        visibility='Reviewed tracks; gaps up to 6 frames interpolated, edges held up to 5 frames. Reviewed occlusions authored separately: waiter 451-549, food-carrier 413-479. Inferred intervals listed per person.',
        motion='SAM 3D Body estimates, stabilized and interpolated at 10 fps; not direct measurements at every frame',
        provenance='Estimated ingest motion and camera; assumed geometry in room_provenance.json')),encoding='utf-8')


if __name__ == '__main__':
    main()
