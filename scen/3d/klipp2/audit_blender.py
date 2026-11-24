"""Reopen saved deliverable and verify the evaluated channels, not builder inputs."""
import bpy,json,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
start=time.perf_counter();s=bpy.context.scene;r=bpy.data.objects['PerformerRig'];d=bpy.data.objects['MocapRotations'];mesh=bpy.data.objects['PerformerMesh'];a=json.loads((HERE/'animation.json').read_text());p='mixamorig:'
face_error=0;angles=[];hands=[];camera_error=0
for i in range(369):
    s.frame_set(i);bpy.context.view_layer.update();rr=r.evaluated_get(bpy.context.evaluated_depsgraph_get());aa=[];hh=[]
    for side in ['Left','Right']:
        q=[np.array(rr.matrix_world@rr.pose.bones[p+side+n].head) for n in ['UpLeg','Leg','Foot']];x=q[0]-q[1];y=q[2]-q[1];aa.append(float(np.degrees(np.arccos(np.clip(x@y/(np.linalg.norm(x)*np.linalg.norm(y)),-1,1)))));hh.append(list(rr.pose.bones[p+side+'Hand'].matrix.to_quaternion()))
    angles.append(aa);hands.append(hh)
    for name,values in a['face'].items():
        key=mesh.data.shape_keys.key_blocks.get(name)
        if key:face_error=max(face_error,abs(key.value-values[i]))
    camera_error=max(camera_error,float(np.abs(np.array(s.camera.matrix_world)-np.array(a['camera'][i])).max()))
angles=np.array(angles);changes=np.abs(np.diff(angles,axis=0));hands=np.array(hands);dots=np.clip(np.abs(np.sum(hands[1:]*hands[:-1],axis=-1)),0,1);steps=np.degrees(2*np.arccos(dots))
report=dict(frames=369,face_channels=51,face_max_absolute_error=face_error,camera_matrix_max_error=camera_error,copy_rotation_constraints=sum(c.type=='COPY_ROTATION' for b in r.pose.bones for c in b.constraints),ik_constraints=sum(c.type=='IK' for o in [r,d] for b in o.pose.bones for c in b.constraints),nla_tracks=dict(body=len(d.animation_data.nla_tracks),root=len(r.animation_data.nla_tracks),face=len(mesh.data.shape_keys.animation_data.nla_tracks)),max_knee_angle_step_degrees=float(changes.max()),knee_steps_over_15_degrees=int((changes>15).sum()),max_hand_orientation_step_degrees=float(steps.max()),hand_steps_over_30_degrees=int((steps>30).sum()),face_faithful_to_detector=face_error<1e-5,seconds=time.perf_counter()-start)
(HERE/'blender-audit.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
