"""Fast edit/render path: run inside an already loaded render.blend.

--frames 60,120,... or --all; --move-table dx; --camera-x dx.
Report operation time separately from fresh Blender process startup and image rendering.
"""
import bpy,sys,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
scene=bpy.context.scene;start=time.perf_counter();edits={}
if '--move-table' in args:
    delta=float(args[args.index('--move-table')+1])
    for ob in bpy.data.objects:
        if ob.name.startswith('Pool table 1 ') or ob.name.startswith('Table 1 rail'):ob.location.x+=delta
    edits['table_x_delta']=delta
if '--camera-x' in args:
    delta=float(args[args.index('--camera-x')+1]);cam=scene.camera;ad=cam.animation_data
    # Modify a parent offset, keeping every source camera key intact.
    off=bpy.data.objects.new('Camera edit offset',None);scene.collection.objects.link(off);cam.parent=off;off.location.x=delta;edits['camera_x_delta']=delta
if '--swap-look' in args:
    c=bpy.data.materials['Black knit top'];c.diffuse_color=(.04,.08,.14,1);edits['shirt']='blue'
if '--swap-character' in args:
    asset=Path(args[args.index('--swap-character')+1]).resolve();old=bpy.data.objects['PerformerRig'];oldmesh=bpy.data.objects['PerformerMesh'];donor=bpy.data.objects['MocapRotations']
    with bpy.data.libraries.load(str(asset),link=False) as (src,dst):dst.objects=[n for n in src.objects if n in ['PerformerRig','PerformerMesh']]
    for ob in dst.objects:scene.collection.objects.link(ob)
    new=next(o for o in dst.objects if o.type=='ARMATURE');newmesh=next(o for o in dst.objects if o.type=='MESH')
    if set(old.pose.bones.keys())!=set(new.pose.bones.keys()):raise ValueError('Cached swap needs matching named rig; new rig types require one-time retarget setup')
    def copy_nla(src,dst):
        ad=dst.animation_data_create()
        for track in src.animation_data.nla_tracks:
            nt=ad.nla_tracks.new();nt.name=track.name
            for st in track.strips:
                ns=nt.strips.new(st.name,int(st.frame_start),st.action);ns.action_frame_start=st.action_frame_start;ns.action_frame_end=st.action_frame_end;ns.frame_start=st.frame_start;ns.frame_end=st.frame_end
    copy_nla(old,new);copy_nla(oldmesh.data.shape_keys,newmesh.data.shape_keys);new.scale=old.scale
    for pb in new.pose.bones:
        pb.scale=old.pose.bones[pb.name].scale;new.data.bones[pb.name].inherit_scale='NONE';con=pb.constraints.new('COPY_ROTATION');con.target=donor;con.subtarget=pb.name;con.owner_space='POSE';con.target_space='POSE'
    for ob in list(old.children)+[old]:ob.hide_render=True;ob.hide_set(True)
    edits['character_asset']=str(asset);edits['character_swap_scope']='prebuilt compatible named rig; new topology/rig setup is ingest'
bpy.context.view_layer.update();edit_s=time.perf_counter()-start
folder=HERE/('baseline' if Path(bpy.data.filepath).stem=='baseline' else 'render');folder.mkdir(exist_ok=True)
frames=range(369) if '--all' in args else [int(x) for x in args[args.index('--frames')+1].split(',')] if '--frames' in args else []
for i in frames:
    scene.frame_set(i);scene.render.filepath=str(folder/f'{i:04d}.png');bpy.ops.render.render(write_still=True)
report=dict(edit_seconds=edit_s,total_seconds=time.perf_counter()-start,frames=len(frames),edits=edits)
name='edit-timing.json' if edits else ('baseline-render-timing.json' if folder.name=='baseline' else 'render-timing.json')
(HERE/name).write_text(json.dumps(report,indent=2));print(report,flush=True)
