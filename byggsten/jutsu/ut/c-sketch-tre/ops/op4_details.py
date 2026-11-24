"""Editable, explicitly assumed restaurant fittings and hand-driven prop animation."""
import bpy
import math
from mathutils import Vector

s = bpy.context.scene
kol = bpy.data.collections.new('PRP_restaurant_details')
s.collection.children.link(kol)
table = bpy.data.objects['PRP_bord_huvud']
floor = bpy.data.objects['ENV_golv'].location.z + .06
yaw = table.rotation_euler.z
forward = Vector((math.cos(yaw), math.sin(yaw), 0))
side = Vector((-math.sin(yaw), math.cos(yaw), 0))
origin = table.location.copy()


def material(name, color):
    m = bpy.data.materials.new('M_'+name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = .7
    return m


wood = material('oak', (.28,.15,.065))
metal = material('charcoal', (.035,.042,.045))
blue = material('blue_bag', (.025,.24,.5))
ceramic = material('tray', (.8,.78,.66))
food = material('food', (.62,.38,.045))
screen = material('screen', (.07,.27,.34))


def box(name, position, dimensions, mat, angle=yaw, parent=None):
    # Copy a unit mesh; geometry dimensions remain editable per semantic object.
    mesh = table.data.copy()
    mesh.materials.clear(); mesh.materials.append(mat)
    ob = bpy.data.objects.new(name, mesh); kol.objects.link(ob)
    ob.parent = parent; ob.location = position; ob.scale = dimensions
    ob.rotation_euler.z = angle
    ob['provenance'] = 'assumed dimensions and hidden geometry, visually guided by source'
    return ob


def empty(name):
    ob = bpy.data.objects.new(name, None); kol.objects.link(ob)
    return ob


def point(pid, joint):
    return bpy.data.objects[f'RIG_{pid}_full_{joint}'].matrix_world.translation.copy()


def visibility(ob, intervals):
    previous = bpy.context.preferences.edit.keyframe_new_interpolation_type
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'CONSTANT'
    for frame, hidden in intervals:
        ob.hide_render = hidden; ob.hide_viewport = hidden
        ob.keyframe_insert('hide_render',frame=frame)
        ob.keyframe_insert('hide_viewport',frame=frame)
    bpy.context.preferences.edit.keyframe_new_interpolation_type = previous


# Give the existing chairs physical supports; add the chair opposite the customer.
chair_pos = origin + forward * .68
chair_pos.z = floor + .45
box('PRP_stol_huvud', chair_pos, (.43,.45,.08), wood)
chair_back = chair_pos + forward * .21; chair_back.z = floor + .73
box('PRP_stolrygg_huvud', chair_back, (.07,.45,.58), wood)
for chair in [o for o in bpy.data.objects if o.name.startswith('PRP_stol_')]:
    for a in (-.16,.16):
        for b in (-.16,.16):
            p = chair.location + forward*a + side*b; p.z = floor+.22
            box(chair.name+f'_leg_{a}_{b}', p, (.035,.035,.44), metal)

# The blue bag is a source landmark on the bench, not a measured mesh.
bench = bpy.data.objects['PRP_bank_sits']
bag_pos = bench.location + side * .85 + forward * .09
bag_pos.z = bench.location.z + .28
box('PRP_blue_bag', bag_pos, (.15,.32,.4), blue)
for b in (-.11,.11):
    p=bag_pos+side*b; p.z+=.25
    box('PRP_bag_handle_'+str(b),p,(.025,.025,.16),blue)

# Restaurant depth and ceiling structure, all declared assumptions.
back = origin + side*4.3
back.z = floor+1.4
box('ENV_back_wall',back,(4.5,.10,2.8),material('back_wall',(.22,.18,.12)))
for distance in (-1.8,-.8,.2,1.2,2.2,3.2,4.2):
    p=origin+side*distance; p.z=floor+2.65
    box('ENV_ceiling_beam_'+str(distance),p,(3.8,.09,.12),wood)
for i in range(3):
    p=back+forward*(i*.57-.57)-side*.075; p.z=floor+2.0
    box('PRP_menu_panel_'+str(i),p,(.5,.03,.48),screen)
    for row in range(3):
        q=p-side*.02; q.z+=.13-row*.12
        box(f'PRP_menu_line_{i}_{row}',q,(.37,.015,.022),ceramic)

# Tray with independent editable rim and food shapes.
tray = empty('RIG_tray')
tray['provenance']='authored prop path: waiter hand -> main table -> carrier hands -> rear table; source timing reviewed'
tray_parts=[box('PRP_tray_base',(0,0,0),(.39,.28,.018),ceramic,0,tray)]
for x in (-.19,.19): tray_parts.append(box('PRP_tray_rim_x_'+str(x),(x,0,.019),(.012,.28,.035),ceramic,0,tray))
for y in (-.135,.135): tray_parts.append(box('PRP_tray_rim_y_'+str(y),(0,y,.019),(.39,.012,.035),ceramic,0,tray))
for i in range(9):
    tray_parts.append(box('PRP_food_'+str(i),((i%3-1)*.09,(i//3-1)*.07,.037),(.075,.055,.04),food,.2*(i%2),tray))

devices=[]
for pid, name in [('1','customer_phone'),('2','payment_terminal')]:
    rig=empty('RIG_'+name)
    body=box('PRP_'+name,(0,0,0),(.075,.022,.14),metal,0,rig)
    glass=box('PRP_'+name+'_screen',(0,-.013,.01),(.063,.004,.105),screen,0,rig)
    devices.append((pid,rig,[body,glass]))

tabletop=origin.copy(); tabletop.z += .055/2+.009
tabletop += side*.02
rear=origin+side*3.3
rear.z=tabletop.z
frames=sorted(set(range(0,819,3))|{50,100,115,450,510,549,550,560,570,580,590,600,630,680,740,760,780,818})
bpy.context.preferences.edit.keyframe_new_interpolation_type='LINEAR'
previous_hand_angle=yaw
previous_device_rotation={}
for frame in frames:
    s.frame_set(frame); bpy.context.view_layer.update()
    if frame < 115:
        hand=point('2','l_wrist')-forward*.14; hand.z-=.035
        t=max(0,min(1,(frame-80)/35)); t=t*t*(3-2*t)
        pos=hand.lerp(tabletop,t); angle=yaw
    elif frame < 560:
        pos=tabletop; angle=yaw
    else:
        l=point('3','l_wrist'); r=point('3','r_wrist')
        hand=(l+r)/2; hand.z-=.02
        t=max(0,min(1,(frame-560)/25)); t=t*t*(3-2*t)
        pos=tabletop.lerp(hand,t)
        hand_angle=math.atan2((r-l).y,(r-l).x)
        hand_angle=previous_hand_angle+(hand_angle-previous_hand_angle+math.pi/2)%math.pi-math.pi/2
        previous_hand_angle=hand_angle
        angle=yaw*(1-t)+hand_angle*t
        if frame>=740:
            t=max(0,min(1,(frame-740)/40)); t=t*t*(3-2*t)
            target_yaw=hand_angle+(yaw-hand_angle+math.pi/2)%math.pi-math.pi/2
            pos=hand.lerp(rear,t); angle=hand_angle*(1-t)+target_yaw*t
    tray.location=pos; tray.rotation_euler.z=angle
    tray.keyframe_insert('location',frame=frame); tray.keyframe_insert('rotation_euler',frame=frame)
    for pid,rig,parts in devices:
        wrist=point(pid,'r_wrist'); elbow=point(pid,'r_lowarm')
        direction=(wrist-elbow).normalized()
        rig.location=wrist+direction*.065
        rig.rotation_mode='QUATERNION'
        rotation=direction.to_track_quat('Z','Y')
        if pid in previous_device_rotation and rotation.dot(previous_device_rotation[pid]) < 0:
            rotation.negate()
        previous_device_rotation[pid]=rotation.copy()
        rig.rotation_quaternion=rotation
        rig.keyframe_insert('location',frame=frame); rig.keyframe_insert('rotation_quaternion',frame=frame)
for part in tray_parts: visibility(part,[(0,True),(50,False)])
for pid,rig,parts in devices:
    for part in parts:
        visibility(part,[(0,False)] if pid=='1' else [(0,True),(115,False),(550,True)])

# A motivated broad front fill makes the measured poses readable in EEVEE.
key=bpy.data.objects['LGT_key']; key.data.energy=2.0
fill=bpy.data.objects['LGT_fill']; fill.location=origin-side*2+Vector((0,0,2.3)); fill.data.energy=450
fill.data.color=(1.0,.84,.68); fill.data.shadow_soft_size=2.0
s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
s['reconstruction_limitations']='Body estimates at 10 fps; occlusion staging and props authored; room dimensions assumed. Not a metrically verified reconstruction.'
s.frame_set(200)
s.render.engine='BLENDER_EEVEE'
s.render.resolution_percentage=50
s.render.image_settings.media_type='IMAGE'; s.render.image_settings.file_format='PNG'
target=artifacts.file(name='scene_lit_f200.png',media_type='image/png')
s.render.filepath=str(target.path); bpy.ops.render.render(write_still=True); target.publish()
s.render.resolution_percentage=100
result={'detail_objects':len(kol.objects),'frames':[s.frame_start,s.frame_end],'props':['tray','customer_phone','payment_terminal'],'assumed_geometry':True}

"""Blender-side delivery gate. Embed this file in Jutsu operations; no local imports."""
import bpy
import math
from mathutils import Vector


def object_curves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    action = ad.action
    if hasattr(action, 'fcurves'):
        for curve in action.fcurves:
            yield action.fcurves, curve
    else:
        slot = getattr(getattr(ad, 'action_slot', None), 'handle', None)
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    if slot is None or bag.slot_handle == slot:
                        for curve in bag.fcurves:
                            yield bag.fcurves, curve


def merge_scene_animation(scene):
    """One multi-slot Action preserves simultaneous motion with default GLB export."""
    owners=[]
    for obj in scene.objects:
        for owner in (obj, obj.data):
            if owner is not None and getattr(owner,'animation_data',None) and owner.animation_data.action and owner not in owners:
                owners.append(owner)
    # Retain original datablocks until save; revision history and .blend1 preserve the source.
    merged=bpy.data.actions.new('PIPE_scene_timeline')
    layer=merged.layers.new('Scene timeline')
    strip=layer.strips.new(type='KEYFRAME')
    assignments=[]
    for owner in owners:
        slot=merged.slots.new(id_type=owner.id_type,name=owner.name)
        bag=strip.channelbags.new(slot)
        for _,source in list(object_curves(owner)):
            if source.modifiers:
                raise RuntimeError('EXPORT BLOCKED: unsupported curve modifier on '+owner.name)
            curve=bag.fcurves.new(source.data_path,index=source.array_index)
            curve.extrapolation=source.extrapolation
            curve.keyframe_points.add(len(source.keyframe_points))
            for a,b in zip(source.keyframe_points,curve.keyframe_points):
                b.co=a.co; b.interpolation=a.interpolation; b.easing=a.easing
                b.handle_left_type=a.handle_left_type; b.handle_right_type=a.handle_right_type
                b.handle_left=a.handle_left; b.handle_right=a.handle_right
            curve.update()
        assignments.append((owner,slot))
    for owner,slot in assignments:
        owner.animation_data.action=merged
        owner.animation_data.action_slot=slot
    return len(assignments)


def prepare_export_scene():
    scene = bpy.context.scene
    saved_frame = scene.frame_current
    candidates = [o for o in scene.objects if o.type == 'MESH']
    forbidden = [o.name for o in candidates if '_beat_' in o.name or any(c.hide_render or c.hide_viewport for c in o.users_collection)]
    if forbidden:
        raise RuntimeError('EXPORT BLOCKED: hidden/alternative meshes remain: '+', '.join(forbidden[:8]))
    prepared = []
    previous = bpy.context.preferences.edit.keyframe_new_interpolation_type
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = 'CONSTANT'
        for obj in candidates:
            curves = list(object_curves(obj))
            hide = next((c for _,c in curves if c.data_path == 'hide_render'), None)
            if hide is None:
                if obj.hide_render or obj.hide_viewport:
                    raise RuntimeError('EXPORT BLOCKED: static hidden mesh '+obj.name)
                continue
            scale_curves = [c for _,c in curves if c.data_path == 'scale']
            if scale_curves and 'pipe_base_scale' not in obj:
                raise RuntimeError('EXPORT BLOCKED: authored scale needs explicit visibility carrier: '+obj.name)
            base = list(obj.get('pipe_base_scale', obj.scale))
            obj['pipe_base_scale'] = base
            # Disabling viewport evaluation leaves constraint-driven geometry at identity.
            for owner,curve in curves:
                if curve.data_path == 'hide_viewport':
                    owner.remove(curve)
            obj.hide_viewport = False
            frames = sorted({scene.frame_start, scene.frame_end} | {int(k.co.x) for k in hide.keyframe_points})
            states = [hide.evaluate(frame) >= .5 for frame in frames]
            for frame in frames:
                hidden = hide.evaluate(frame) >= .5
                obj.scale = (0,0,0) if hidden else base
                obj.keyframe_insert('scale',frame=frame)
            # Preferences do not reliably override existing/action-created key interpolation.
            for _,curve in object_curves(obj):
                if curve.data_path == 'scale':
                    for key in curve.keyframe_points:
                        key.interpolation = 'CONSTANT'
            obj['pipe_visibility'] = 'scale-zero-constant-v1'
            obj['pipe_visibility_animated'] = len(set(states)) > 1
            prepared.append(obj.name)
        # Verify the switch itself, not merely the existence of a scale channel.
        probes={scene.frame_start,scene.frame_end,saved_frame}
        for name in prepared:
            for _,curve in object_curves(bpy.data.objects[name]):
                if curve.data_path=='hide_render':
                    for key in curve.keyframe_points:
                        probes.update(int(key.co.x)+offset for offset in (-1,0,1) if scene.frame_start<=int(key.co.x)+offset<=scene.frame_end)
        for frame in sorted(probes):
            scene.frame_set(frame)
            for name in prepared:
                obj=bpy.data.objects[name]
                expected=(0,0,0) if obj.hide_render else obj['pipe_base_scale']
                if max(abs(a-b) for a,b in zip(obj.scale,expected))>1e-6:
                    raise RuntimeError(f'EXPORT BLOCKED: visibility fade {name} frame {frame}')
        scene.frame_set(saved_frame)
        bpy.context.view_layer.update()
        failures=[]
        for obj in candidates:
            points=[obj.matrix_world @ Vector(v) for v in obj.bound_box]
            if not all(math.isfinite(x) for point in points for x in point):
                failures.append(obj.name+': nonfinite bounds')
            dimensions=[max(p[k] for p in points)-min(p[k] for p in points) for k in range(3)]
            if obj.name.startswith('RIG_') and obj.name.endswith('_huvud') and max(dimensions)>.4:
                failures.append(obj.name+': oversized head '+str(dimensions))
        if failures:
            raise RuntimeError('EXPORT BLOCKED: '+'; '.join(failures[:8]))
        slots=merge_scene_animation(scene)
        scene.frame_set(saved_frame); bpy.context.view_layer.update()
        scene['pipe_export_gate']='v2: no hidden alternatives, portable step visibility, bounded heads, shared timeline; GLB audit still required'
        return {'mesh_count':len(candidates),'portable_visibility_objects':len(prepared),'hidden_alternatives':0,'timeline_slots':slots,'glb_audit_required':True}
    finally:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = previous


result = prepare_export_scene()
