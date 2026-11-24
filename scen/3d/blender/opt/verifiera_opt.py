"""Independent evaluated Blender verification, every frame, native masks.

blender -b --python opt/verifiera_opt.py -- [--variant before|after]
Default collects both and invokes CPU metric/report generation. Failures exit 1.
"""
import sys, json, math, hashlib, argparse, subprocess, traceback, os
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
CONV=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
BODY=['nose','LeftArm','RightArm','LeftForeArm','RightForeArm','LeftHand','RightHand']
FEATURES=BODY+[f'{s}Hand{f}{i}' for s in ['Left','Right'] for f in ['Thumb','Index','Middle','Ring','Pinky'] for i in range(1,5)]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def collect(variant,quick=False):
    bakepath=HERE.parent/'bake.json' if variant=='before' else HERE/'bake-opt.json'
    blendpath=HERE.parent/'scen.blend' if variant=='before' else HERE/'scen-opt.blend'
    bake=read(bakepath);spec=read(ROOT/'scen3d.json');assets=read(HERE.parent/'bake-assets.json')
    bpy.ops.wm.open_mainfile(filepath=str(blendpath))
    scene=bpy.context.scene
    scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage=576,1024,100
    scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading
    sh.light,sh.color_type='FLAT','OBJECT'
    sh.show_shadows=sh.show_cavity=sh.show_specular_highlight=sh.show_object_outline=False
    sh.background_type,sh.background_color='WORLD',(0,0,0)
    scene.world.color=(0,0,0);scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    scene.view_settings.exposure,scene.view_settings.gamma=0,1;scene.render.film_transparent=False
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.display.render_aa='8'
    scene.render.use_sequencer=False;scene.use_nodes=False
    if hasattr(scene,'compositing_node_group'):scene.compositing_node_group=None
    out=HERE/'verification'/f'{variant}-{sha(bakepath)[:12]}';out.mkdir(parents=True,exist_ok=True)
    frames=[];timing_equal=True;face_equal=True;camera_error=0;parts_max_error=0;mouthOpen_error=0
    for f in bake['frames']:
        i=f['i'];aid=f['mainActor'];scene.frame_set(i)
        if quick:
            ids=[fr['i'] for fr in bake['frames'] if fr['shot']==f['shot']]
            if i not in [ids[0]+2,ids[len(ids)//2],ids[-1]-2]:continue
        shot=next(s for s in spec['shots'] if s['id']==f['shot']);source=shot['source']['camera']
        camera=bpy.data.objects['kam:'+f['shot']];scene.camera=camera
        # Assert the scene builder's camera is still the immutable source camera.
        pos=np.array(source['pos']);z=pos-np.array(source['target']);z/=np.linalg.norm(z)
        x=np.cross(source['up'],z);x/=np.linalg.norm(x);y=np.cross(z,x)
        expected=np.eye(4);expected[:3,:3]=np.stack([x,y,z],axis=1);expected[:3,3]=pos
        actual=np.array(CONV.inverted()@camera.matrix_world)
        camera_error=max(camera_error,float(np.max(abs(actual-expected))))
        assert abs(camera.data.angle-math.radians(source['fov']))<1e-5,'Source camera FOV changed'
        assert camera_error<1e-5,'Source camera transform changed'
        for o in bpy.data.objects:o.color=(1,1,1,1) if o.name.startswith('actor:'+aid+':') else (0,0,0,1)
        graph=bpy.context.evaluated_depsgraph_get();rig=bpy.data.objects['actor:'+aid+':rig'].evaluated_get(graph)
        bones={b.name.removeprefix('mixamorig').lstrip(':'):b for b in rig.pose.bones}
        face=bpy.data.objects['actor:'+aid+':face'].evaluated_get(graph)
        xyz=[];uv=[]
        for n in FEATURES:
            p=face.matrix_world@Vector(assets['actors'][aid]['faceLandmarks']['nose']) if n=='nose' else rig.matrix_world@bones[n].head
            xyz.append(list(CONV.inverted()@p));q=world_to_camera_view(scene,camera,p);uv.append([q.x*576,(1-q.y)*1024])
        # Anatomical pelvis centre is the midpoint of the hip joints. The rig's
        # Hips controller is several centimetres higher and is not that landmark.
        hips=list(CONV.inverted()@(rig.matrix_world@((bones['LeftUpLeg'].head+bones['RightUpLeg'].head)/2)))
        toes=[list(CONV.inverted()@(rig.matrix_world@bones[n].head)) for n in ['LeftToeBase','RightToeBase']]
        props={}
        for p in spec['props']:
            obj=bpy.data.objects[p['id']].evaluated_get(graph)
            props[p['id']]=dict(matrix=np.array(CONV.inverted()@obj.matrix_world@CONV).T.reshape(-1).tolist(),visible=not obj.hide_render)
        # Local expression channel is unchanged even when the head is repositioned.
        mouth=bpy.data.objects['actor:'+aid+':mouth'].evaluated_get(graph)
        expected_mouth=f['actors'][aid]['face']['parts']['mouth']['scale']
        local_mouth_error=max(abs(mouth.scale[k]-expected_mouth[k]) for k in range(3))
        face_equal &= local_mouth_error<1e-7
        for name,part in f['actors'][aid]['face']['parts'].items():
            from mathutils import Quaternion
            x,y,z,w=part['quaternion']
            wanted=Matrix.LocRotScale(Vector(part['position']),Quaternion((w,x,y,z)),Vector(part['scale']))
            obj=bpy.data.objects['actor:'+aid+':'+name].evaluated_get(graph)
            parts_max_error=max(parts_max_error,float(np.max(abs(np.array(obj.matrix_basis)-np.array(wanted)))))
        mouthOpen_error=max(mouthOpen_error,abs(bpy.data.objects['actor:'+aid]['mouthOpen']-f['actors'][aid]['mouthOpen']))
        mask=out/f'{i:04d}.png'
        if not mask.exists():scene.render.filepath=str(mask);bpy.ops.render.render(write_still=True)
        frames.append(dict(i=i,shot=f['shot'],uv=uv,xyz=xyz,hips=hips,toes=toes,props=props,mask=str(mask.relative_to(HERE)),mouth_local_scale_error=local_mouth_error))
        if i%60==0:print(f'{variant}: verified {i+1}/{bake["N"]}',flush=True)
    result=dict(variant=variant,bake_sha256=sha(bakepath),blend_sha256=sha(blendpath),blender=bpy.app.version_string,features=FEATURES,frames=frames,camera_max_matrix_error=camera_error,mouth_local_scale_pass=bool(face_equal),all_face_parts_local_matrix_max_error=parts_max_error,mouthOpen_max_error=mouthOpen_error)
    (HERE/f'evaluated-{variant}{"-quick" if quick else ""}.json').write_text(json.dumps(result,separators=(',',':')),encoding='utf-8')
    return result
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--variant',choices=['before','after']);ap.add_argument('--quick',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    for v in [a.variant] if a.variant else ['before','after']:collect(v,a.quick)
    if not a.variant:subprocess.run([str(ROOT.parent/'.venv/Scripts/python.exe'),str(HERE/'metrics.py')],check=True)
if __name__=='__main__':
    try:main()
    except Exception:traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
