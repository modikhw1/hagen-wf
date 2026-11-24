"""Blender-native COPY_ROTATION retarget and NLA; no position IK.
Run blender -b --python build_scene.py -- [--baseline] [--preview 120] [--render]
"""
import bpy,sys,json,time,math
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector,Quaternion
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent
ARGS=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
BASELINE='--baseline' in ARGS
LABEL='baseline' if BASELINE else 'render'
START=time.perf_counter()
data=json.loads((HERE/'animation.json').read_text());W=np.array(data['baseline_world' if BASELINE else 'world']);C=np.array(data['camera']);K=np.array(data['K'])
bpy.ops.wm.open_mainfile(filepath=str(HERE/'character.blend'))
scene=bpy.context.scene;scene.frame_start=0;scene.frame_end=368;scene.render.fps=30
rig=bpy.data.objects['PerformerRig'];mesh=bpy.data.objects['PerformerMesh'];P='mixamorig:'

def mat(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.7;return m
skin=mat('Skin',(.60,.36,.25));shirt=mat('Black knit top',(.018,.021,.026));trousers=mat('Charcoal trousers',(.07,.065,.06));hair=mat('Brown hair',(.055,.024,.012));white=mat('Eye white',(.8,.77,.70));iris=mat('Iris',(.08,.065,.04));mouthmat=mat('Mouth cavity',(.07,.015,.012))
for m in [skin,shirt,trousers]:mesh.data.materials.append(m)
# Evaluate morphology without topology-changing helper mask so polygon indices remain stable.
mask=next(m for m in mesh.modifiers if m.type=='MASK');mask.show_viewport=False;bpy.context.view_layer.update();evalmesh=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();verts=np.array([v.co[:] for v in evalmesh.vertices]);mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear();mask.show_viewport=True
bodygroup=mesh.vertex_groups['body'].index;bodyids=[v.index for v in mesh.data.vertices if any(g.group==bodygroup and g.weight>.5 for g in v.groups)];height=verts[bodyids,2].max()-verts[bodyids,2].min();scale=1.65/height;rig.scale=(scale,)*3
handgroups=[g.index for g in mesh.vertex_groups if 'Hand' in g.name]
for poly in mesh.data.polygons:
    xyz=verts[list(poly.vertices)].mean(0);hand=any(any(g.group in handgroups and g.weight>.3 for g in mesh.data.vertices[i].groups) for i in poly.vertices)
    poly.material_index=0 if xyz[2]>1.19 or hand else (1 if xyz[2]>.80 else 2);poly.use_smooth=True
# Native subdivision is deliberately limited for fast CPU previews.
sub=mesh.modifiers.new('Surface smoothing','SUBSURF');sub.levels=1;sub.render_levels=1

def parent_head(obj):
    # Keep neutral armature-space coordinates; bone parenting has an implicit tail offset.
    obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=P+'Head';obj.matrix_parent_inverse=(rig.data.bones[P+'Head'].matrix_local@Matrix.Translation((0,rig.data.bones[P+'Head'].length,0))).inverted()
def sphere(name,pos,scl,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=pos);o=bpy.context.object;o.name=name;o.scale=scl;o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    parent_head(o);return o
groups=json.loads((HERE/'deps/mpfb2-master/src/mpfb/data/mesh_metadata/basemesh_vertex_groups.json').read_text())
def group_center(name):
    g=mesh.vertex_groups.get(name);ids=[v.index for v in mesh.data.vertices if any(x.group==g.index and x.weight>.1 for x in v.groups)];return verts[ids].mean(0)
for side in ['l','r']:
    center=group_center('joint-'+side+'-eye');sphere('Eye '+side,center,(.0105,.0105,.0105),white);sphere('Iris '+side,center+[0,-.009,0],(.0048,.0018,.0048),iris)
# Scalp cap with open face and shoulder-length back/sides; task-authored geometry.
head=rig.data.bones[P+'Head'].head_local;top=verts[bodyids,2].max();hz=top-.065;hx=0.;hy=.008
vv=[];ff=[];nr=14;ns=48
for j in range(nr):
    u=j/(nr-1)
    for k in range(ns):
        phi=2*math.pi*k/ns;front=math.sin(phi)<-.3
        theta=u*(1.36 if front else 2.0)
        x=.098*math.sin(theta)*math.cos(phi);y=hy+.115*math.sin(theta)*math.sin(phi);z=hz+.10*math.cos(theta)
        if not front:z-=max(0,u-.7)*.55
        vv.append((x,y,z))
for j in range(nr-1):
    for k in range(ns):a=j*ns+k;b=j*ns+(k+1)%ns;ff.append((a,b,b+ns,a+ns))
hm=bpy.data.meshes.new('Hair mesh');hm.from_pydata(vv,[],ff);ho=bpy.data.objects.new('Hair',hm);scene.collection.objects.link(ho);ho.data.materials.append(hair);parent_head(ho)
for p in hm.polygons:p.use_smooth=True

rest={b.name:b.matrix_local.to_3x3().copy() for b in rig.data.bones}
donor=rig.copy();donor.data=rig.data.copy();donor.name='MocapRotations';scene.collection.objects.link(donor);donor.hide_render=True;donor.hide_set(True)
for pb in rig.pose.bones:
    con=pb.constraints.new('COPY_ROTATION');con.name='Source rotation, no IK';con.target=donor;con.subtarget=pb.name;con.target_space='POSE';con.owner_space='POSE';con.mix_mode='REPLACE'

def normalized(v,fallback=(0,0,1)):
    v=Vector(v);return v.normalized() if v.length>1e-6 else Vector(fallback)
def frame_basis(x,z):
    z=normalized(z);x=Vector(x)-z*Vector(x).dot(z);x=normalized(x,(1,0,0));y=z.cross(x).normalized();return Matrix((x,y,z)).transposed()
def swing(name,direction,bodyrot):
    r=bodyrot@rest[P+name];old=r.col[1];q=old.rotation_difference(normalized(direction));return q.to_matrix()@r
def hand_basis(points):
    y=normalized(points[9]-points[0]);x=Vector(points[5]-points[17]);x=(x-y*x.dot(y)).normalized();z=x.cross(y).normalized();return Matrix((x,y,z)).transposed()
handrest={}
for side in ['Left','Right']:
    names=['Hand','HandIndex1','HandMiddle1','HandPinky1'];q=[rig.data.bones[P+side+n].head_local for n in names];hh=np.zeros((21,3));hh[0],hh[5],hh[9],hh[17]=q;handrest[side]=hand_basis(hh)

# Stature and segment proportions are constant across all frames, preserving bone length.
segments={'LeftArm':(11,12),'LeftForeArm':(12,13),'RightArm':(14,15),'RightForeArm':(15,16),'LeftUpLeg':(4,5),'LeftLeg':(5,6),'RightUpLeg':(1,2),'RightLeg':(2,3)}
for name,(a,b) in segments.items():
    value=float(np.median(np.linalg.norm(W[:,b]-W[:,a],axis=-1)))/(rig.data.bones[P+name].length*scale)
    value=max(.65,min(1.5,value));rig.pose.bones[P+name].scale.y=value;donor.pose.bones[P+name].scale.y=value
rest_torso=((rig.data.bones[P+'LeftArm'].head_local+rig.data.bones[P+'RightArm'].head_local)/2-rig.data.bones[P+'Hips'].head_local).length*scale
torso_ratio=float(np.median(np.linalg.norm(W[:,8]-W[:,0],axis=-1)))/rest_torso
for name in ['Hips','Spine','Spine1','Spine2']:
    rig.pose.bones[P+name].scale.y=torso_ratio;donor.pose.bones[P+name].scale.y=torso_ratio
rest_width=(rig.data.bones[P+'LeftArm'].head_local-rig.data.bones[P+'RightArm'].head_local).length*scale
width_ratio=1+(float(np.median(np.linalg.norm(W[:,11]-W[:,14],axis=-1)))/rest_width-1)*1.3
for name in ['LeftShoulder','RightShoulder']:
    rig.pose.bones[P+name].scale.y=width_ratio;donor.pose.bones[P+name].scale.y=width_ratio
for ob in [rig,donor]:
    for b in ob.data.bones:b.inherit_scale='NONE'

previous={};rotations={n:[] for n in rest};absolute={n:[] for n in rest};roots=[];headref=None
for i,w in enumerate(W):
    body=frame_basis(w[11]-w[14],w[8]-w[0]);hip=frame_basis(w[4]-w[1],w[8]-w[0]);desired={}
    for pb in donor.pose.bones:
        name=pb.name[len(P):];desired[pb.name]=(hip if name=='Hips' else body)@rest[pb.name]
    for name,(a,b) in segments.items():desired[P+name]=swing(name,w[b]-w[a],body)
    for side,ankle in [('Left',6),('Right',3)]:
        desired[P+side+'Foot']=body@rest[P+side+'Foot'];desired[P+side+'ToeBase']=body@rest[P+side+'ToeBase']
    # FaceLandmarker transform already has OpenGL camera convention; preserve head motion.
    fr=Matrix(np.array(data['face_matrix'][i])[:3,:3].tolist());cameraR=Matrix(C[i,:3,:3].tolist());target_head=cameraR@fr
    # Canonical face +Z points out of the face, while the human faces -Y.
    neutral=Matrix(((1,0,0),(0,0,-1),(0,1,0)))
    desired[P+'Head']=target_head@neutral.inverted()@rest[P+'Head']
    desired[P+'Neck']=body@rest[P+'Neck']
    camcv=Matrix(C[i,:3,:3].tolist())@Matrix.Diagonal((1.,-1.,-1.))
    for side,wi in [('Left',13),('Right',16)]:
        h=np.array(data['hand_world'][side][i]);hw=np.array([camcv@Vector(p) for p in h]);delta=hand_basis(hw)@handrest[side].inverted();desired[P+side+'Hand']=delta@rest[P+side+'Hand']
        for finger,start in [('Thumb',1),('Index',5),('Middle',9),('Ring',13),('Pinky',17)]:
            for j in range(1,4):
                name=side+'Hand'+finger+str(j);a=start+j-1;b=a+1;desired[P+name]=swing(name,hw[b]-hw[a],delta)
    # Convert absolute rotations to bone local channels. The target armature gets them via Blender constraints.
    for pb in donor.pose.bones:
        absolute[pb.name].append(list(desired[pb.name].to_quaternion()))
        rr=rest[pb.name];parent=pb.parent
        if parent:
            rel=rest[parent.name].inverted()@rr;basis=rel.inverted()@desired[parent.name].inverted()@desired[pb.name]
        else:basis=rr.inverted()@desired[pb.name]
        q=basis.to_quaternion();old=previous.get(pb.name)
        if old and old.dot(q)<0:q.negate()
        previous[pb.name]=q.copy();rotations[pb.name].append(list(q))
    roots.append(w[0]-np.array(rig.data.bones[P+'Hips'].head_local)*scale)

# Robust symmetric smoothing in absolute rotation space avoids palm-estimator flips.
# Geodesic medoid removes isolated wrong orientations. Hemisphere unwrapping plus
# symmetric component filtering avoids the two-mode ambiguity of an eigenvector mean.
def robust_quats(values,radius=3):
    q=np.array(values);q/=np.linalg.norm(q,axis=1)[:,None];med=[]
    for i in range(len(q)):
        win=q[max(0,i-radius):min(len(q),i+radius+1)];dist=np.arccos(np.clip(np.abs(win@win.T),0,1));med.append(win[np.argmin(dist.sum(axis=1))])
    med=np.array(med);out=[]
    for i in range(1,len(med)):
        if med[i]@med[i-1]<0:med[i]*=-1
    for i in range(len(q)):
        ids=np.arange(max(0,i-6),min(len(q),i+7));win=med[ids];weights=np.exp(-.5*((ids-i)/3.)**2);v=np.sum(weights[:,None]*win,axis=0);out.append(v/np.linalg.norm(v))
    out=np.array(out)
    # Outlier-only speed guard, applied symmetrically; wrists and body timing are untouched.
    # This intentionally sacrifices uncertain palm roll, which is reported in the log.
    def guarded(qs):
        qs=[Quaternion(v) for v in qs]
        for i in range(1,len(qs)):
            dot=abs(qs[i-1].dot(qs[i]));angle=2*math.acos(min(1.,max(0.,dot)))
            if angle>math.radians(18):qs[i]=qs[i-1].slerp(qs[i],math.radians(18)/angle)
        return qs
    forward=guarded(out);backward=guarded(out[::-1])[::-1];result=[x.slerp(y,.5) for x,y in zip(forward,backward)]
    # Final symmetric iterations remove residual discontinuities from the paired interpolation.
    for _ in range(2):result=guarded(guarded(result)[::-1])[::-1]
    return np.array([list(v) for v in result])
if not BASELINE:
    for name in absolute:
        if 'Hand' in name:absolute[name]=robust_quats(absolute[name])
    for name in rotations:
        if 'Hand' not in name:continue
        parent=donor.pose.bones[name].parent.name;rel=rest[parent].inverted()@rest[name];qs=[]
        for i in range(369):
            desiredR=Quaternion(absolute[name][i]).to_matrix();parentR=Quaternion(absolute[parent][i]).to_matrix();q=(rel.inverted()@parentR.inverted()@desiredR).to_quaternion()
            if qs and Quaternion(qs[-1]).dot(q)<0:q.negate()
            qs.append(list(q))
        rotations[name]=qs
for name,qs in rotations.items():
    values=np.array(qs)
    pb=donor.pose.bones[name];pb.rotation_mode='QUATERNION'
    for i,q in enumerate(values):pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=i,group=name)
for i,pos in enumerate(roots):
    for ob in [donor,rig]:ob.location=pos;ob.keyframe_insert('location',frame=i)
for name,values in data['face'].items():
    key=mesh.data.shape_keys.key_blocks.get(name)
    if key is None:continue
    for i,v in enumerate(values):key.value=v;key.keyframe_insert('value',frame=i)

def nla(ob,name):
    ad=ob.animation_data
    if ad and ad.action:
        action=ad.action;action.name=name;track=ad.nla_tracks.new();track.name=name;strip=track.strips.new(name,0,action);strip.action_frame_start=0;strip.action_frame_end=368;strip.frame_start=0;strip.frame_end=368;ad.action=None
for ob,n in [(donor,'Body and fingers - 30fps'),(rig,'World trajectory'),(mesh.data.shape_keys,'Facial performance - source timing')]:nla(ob,n)

def box(name,pos,dim,color):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat(name+' material',color));return o
floor=data['ground_z'];box('Floor (assumed plane)',(0,3,floor-.05),(18,20,.1),(.26,.23,.17));box('Back wall',(0,8.5,floor+1.7),(18,.15,3.4),(.20,.12,.075))
for j,(x,y) in enumerate([(-2.0,3.5),(2.0,3.8),(3.7,6.8)]):
    box(f'Pool table {j+1} base',(x,y,floor+.5),(1.4,2.4,.7),(.09,.055,.03));box(f'Pool table {j+1} felt',(x,y,floor+.88),(1.48,2.48,.08),(.025,.40,.39))
    for xx in [-.68,.68]:box(f'Table {j+1} rail',(x+xx,y,floor+.96),(.12,2.5,.12),(.32,.19,.07))
for x in [-3,0,3]:box('Window',(x,8.39,floor+2.1),(1.8,.02,1.4),(.7,.78,.8))
camera=bpy.data.cameras.new('Tracked camera');cam=bpy.data.objects.new('Tracked camera',camera);scene.collection.objects.link(cam);scene.camera=cam;camera.sensor_width=36;camera.sensor_fit='HORIZONTAL';camera.lens=K[0,0]*36/540;camera.clip_end=100
for i,m in enumerate(C):
    cam.matrix_world=Matrix(m.tolist());cam.keyframe_insert('location',frame=i);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=cam.matrix_world.to_quaternion();cam.keyframe_insert('rotation_quaternion',frame=i)
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=540;scene.render.resolution_y=960;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.display.shading.light='STUDIO';scene.display.shading.studiolight_rotate_z=.35;scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=False;scene.display.shading.background_type='WORLD';scene.world.color=(.10,.10,.10);scene.display.render_aa='8';scene.view_settings.view_transform='Standard'
scene.render.film_transparent=False;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.sequence_editor_create();scene.sequence_editor.strips.new_sound('Original source audio',str(HERE.parent.parent/'klipp/kand-interpooluppsala-7599643065644551446.mp4'),channel=1,frame_start=0)
scene.render.use_sequencer=False
# Export evaluated rig measurements: catches errors introduced after source fitting.
measure=[];jointbones={0:'Hips',1:'RightUpLeg',2:'RightLeg',3:'RightFoot',4:'LeftUpLeg',5:'LeftLeg',6:'LeftFoot',8:'Neck',10:'Head',11:'LeftArm',12:'LeftForeArm',13:'LeftHand',14:'RightArm',15:'RightForeArm',16:'RightHand'}
for i in range(369):
    scene.frame_set(i);bpy.context.view_layer.update();rr=rig.evaluated_get(bpy.context.evaluated_depsgraph_get());xyz={str(j):list(rr.matrix_world@rr.pose.bones[P+n].head) for j,n in jointbones.items()};proj={j:list(world_to_camera_view(scene,cam,Vector(v)))[:2] for j,v in xyz.items()};measure.append(dict(frame=i,world=xyz,uv={j:[q[0]*540,(1-q[1])*960] for j,q in proj.items()}))
(HERE/f'{LABEL}-rig-measurements.json').write_text(json.dumps(measure,separators=(',',':')))
scene.frame_set(120);scene['camera_provenance']=data['camera_file'];scene['floor_and_tables']='Floor alignment and table positions are approximate; no verified tracked table anchors';scene['retarget']='Native COPY_ROTATION constraints driven by fitted skeleton rotations; NLA. No IK.'
scene['character_license']='MakeHuman base/rig CC0; Mika Suominen ARKit face units CC0; MPFB code GPL-3.0'
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/f'{LABEL}.blend'))
(HERE/f'{LABEL}-build-timing.json').write_text(json.dumps(dict(seconds=time.perf_counter()-START,frames=369,bones=len(rig.pose.bones),face_shapes=52,character_height_m=1.65,rig_scale=scale),indent=2))
print('BUILD DONE',LABEL,time.perf_counter()-START,flush=True)
out=HERE/LABEL;out.mkdir(exist_ok=True)
if '--preview' in ARGS:
    i=int(ARGS[ARGS.index('--preview')+1]);scene.frame_set(i);scene.render.filepath=str(out/f'{i:04d}.png');bpy.ops.render.render(write_still=True)
if '--render' in ARGS:
    scene.render.filepath=str(out)+ '/';bpy.ops.render.render(animation=True)
